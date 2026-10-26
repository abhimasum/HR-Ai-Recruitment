terraform {
  required_version = ">= 1.6"
  backend "gcs" {}
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.44" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com"
  ])
  service = each.key
}

resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = var.artifact_registry_repository
  description   = "Docker images for the AI HR recruitment app"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# Dedicated Service Account for Cloud Run Backend
resource "google_service_account" "backend" {
  account_id   = "hr-backend-sa"
  display_name = "HR Recruitment Backend Service Account"
}

# Grant Vertex AI user role so Cloud Run backend can invoke Gemini and Embeddings
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Grant Cloud SQL client role to connect to Cloud SQL instance
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# ---- Cloud SQL for PostgreSQL 16 (pgvector available as an extension) ----
resource "google_sql_database_instance" "db" {
  name             = "hr-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  deletion_protection = var.deletion_protection
  depends_on       = [google_project_service.apis]

  settings {
    tier = var.database_tier
    ip_configuration {
      ipv4_enabled = true
    }
  }
}

resource "google_sql_database" "hr" {
  name     = "hr"
  instance = google_sql_database_instance.db.name
}

resource "google_sql_user" "hr" {
  name     = "hr"
  instance = google_sql_database_instance.db.name
  password = var.db_password
}

# ---- Cloud Run backend ----
resource "google_cloud_run_v2_service" "backend" {
  name       = "hr-backend"
  location   = var.region
  depends_on = [
    google_project_service.apis,
    google_project_iam_member.vertex_ai_user,
    google_project_iam_member.cloudsql_client,
  ]

  template {
    service_account = google_service_account.backend.email
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.db.connection_name]
      }
    }
    containers {
      image = var.backend_image
      ports {
        container_port = 8000
      }
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://hr:${urlencode(var.db_password)}@/hr?host=/cloudsql/${google_sql_database_instance.db.connection_name}"
      }
      env {
        name  = "DATABASE_ADMIN_URL"
        value = "postgresql+asyncpg://postgres:${urlencode(var.db_admin_password)}@/hr?host=/cloudsql/${google_sql_database_instance.db.connection_name}"
      }
      env {
        name  = "LLM_PROVIDER"
        value = var.llm_provider
      }
      env {
        name  = "LLM_MODEL"
        value = var.llm_model
      }
      env {
        name  = "EMBEDDING_PROVIDER"
        value = var.embedding_provider
      }
      env {
        name  = "EMBEDDING_MODEL"
        value = var.embedding_model
      }
      env {
        name  = "EMBEDDING_DIM"
        value = tostring(var.embedding_dim)
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.vertex_ai_location
      }
      env {
        name  = "GCP_EMBEDDING_LOCATION"
        value = var.vertex_ai_embedding_location
      }
      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
      env {
        name  = "CORS_ORIGINS"
        value = var.cors_origins
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service" "frontend" {
  name       = "hr-frontend"
  location   = var.region
  depends_on = [google_cloud_run_v2_service.backend]

  template {
    containers {
      image = var.frontend_image
      ports {
        container_port = 80
      }
      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
