terraform {
  required_version = ">= 1.6"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.44" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "apis" {
  for_each = toset(["run.googleapis.com", "sqladmin.googleapis.com", "artifactregistry.googleapis.com"])
  service  = each.key
}

# ---- Cloud SQL for PostgreSQL 16 (pgvector available as an extension) ----
resource "google_sql_database_instance" "db" {
  name             = "hr-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  deletion_protection = false
  depends_on       = [google_project_service.apis]

  settings {
    tier = "db-custom-1-3840"
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
  name     = "hr-backend"
  location = var.region
  depends_on = [google_project_service.apis]

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 5
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
        value = "postgresql+asyncpg://hr:${var.db_password}@/hr?host=/cloudsql/${google_sql_database_instance.db.connection_name}"
      }
      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
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
