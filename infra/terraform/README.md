# Terraform (multi-cloud)

Each cloud is a standalone root module. Run one at a time:

    cd infra/terraform/aws      # or gcp / azure
    terraform init
    terraform apply -var="db_password=..." -var="backend_image=..." [other vars]

Build and push both application images first:

    docker build -t <registry>/hr-backend backend
    docker push <registry>/hr-backend
    docker build -t <registry>/hr-frontend frontend
    docker push <registry>/hr-frontend

### Automated GCP deployment with GitHub Actions

The `Deploy HR Recruitment App to GCP` workflow in `.github/workflows/deploy-gcp.yml`
provisions Terraform resources, builds and pushes the backend and frontend images, applies the
Cloud Run deployment, then smoke tests the frontend, backend health endpoint, and database-backed
jobs API. It runs on changes to the application/GCP Terraform files on `main` or `master`, or
manually via **Actions > Deploy HR Recruitment App to GCP > Run workflow**.

Before running it:

1. From Windows PowerShell, run the one-time setup script while signed into the specified GCP
   account and GitHub CLI:

       gcloud auth login abhimasum2@gmail.com
       gh auth login
       .\infra\terraform\gcp\setup-github-actions.ps1

   The script verifies project `hr-ai-recruitment` (number `278189990066`) before making changes.
   It creates a private, versioned Terraform state bucket; a GitHub deployer service account;
   Workload Identity Federation restricted to this repository's `main`/`master` branches; scoped
   GitHub Actions variables; and random `HR_DB_PASSWORD` / `HR_DB_ADMIN_PASSWORD` secrets. It grants
   the deployer the project roles needed to provision Terraform resources. No service-account key
   file is created.
2. The script sets these GitHub repository **variables**:
   - `GCP_PROJECT_ID`
   - `GCP_REGION`
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`
   - `GCP_TERRAFORM_STATE_BUCKET`
   - `GCP_ARTIFACT_REGISTRY_REPOSITORY`
   It creates the `HR_DB_PASSWORD` and `HR_DB_ADMIN_PASSWORD` GitHub **secrets**. The workflow
   applies the admin secret to Cloud SQL's built-in `postgres` user before deploying. The app
   connects as the separate, regular `hr` database user and uses `postgres` only to install
   pgvector at startup. `HR_OPENAI_API_KEY` is only needed if you switch from the default Vertex
   AI provider to OpenAI.
3. Optionally define `HR_LLM_PROVIDER`, `HR_LLM_MODEL`, `HR_VERTEX_AI_LOCATION`,
   `HR_EMBEDDING_PROVIDER`, `HR_EMBEDDING_MODEL`, `HR_EMBEDDING_DIM`, and `HR_DATABASE_TIER`
   repository variables. Defaults are Vertex AI (`gemini-3.8-flash`, `text-embedding-004`) on its
   global endpoint, and Cloud SQL `db-f1-micro`. The global endpoint can route model processing
   outside a specific region; set `HR_VERTEX_AI_LOCATION` to a supported regional endpoint if data
   residency is required. Selecting Hugging Face installs its extra runtime dependencies during
   the backend image build.
4. Review the workflow and start it from GitHub **Actions > Deploy HR Recruitment App to GCP >
   Run workflow**. The workflow creates billable GCP resources, including Cloud SQL; check your
   billing account and quotas before starting. On success, the workflow summary contains the live
   frontend and API URLs. The smoke test exercises the frontend, health endpoint, jobs database,
   and grounded policy RAG response.

The workflow first provisions the Artifact Registry repository, then publishes immutable
commit-SHA-tagged images and applies the complete Terraform plan. Cloud SQL defaults to the
shared-core `db-f1-micro` tier for learning/demo use; override `HR_DATABASE_TIER` if needed.
Cloud Run scales to zero by default. Cloud SQL deletion protection is enabled, so an intentional
teardown requires disabling it and applying Terraform before destroying resources. Public Cloud Run
access is enabled for this demo app; it has no authentication or tenant isolation.

To run the Terraform module manually instead of Actions, initialize the GCS backend:

    cd infra/terraform/gcp
    terraform init -backend-config="bucket=YOUR_STATE_BUCKET" \
      -backend-config="prefix=hr-ai-recruitment/YOUR_PROJECT_ID"

| Cloud | Compute | Database | Registry | AI / LLM Provider |
|-------|---------|----------|----------|-------------------|
| AWS   | ECS Fargate behind an ALB | Aurora PostgreSQL 16 | ECR | OpenAI |
| GCP   | Cloud Run (frontend + backend) | Cloud SQL for PostgreSQL 16 | Artifact Registry | GCP Vertex AI (Gemini + Embeddings) or OpenAI |
| Azure | App Service for Containers | Flexible Server PostgreSQL 16 (VECTOR extension allowlisted) | ACR | OpenAI |

### GCP Deployment with Vertex AI
The GCP Terraform module sets up Cloud Run with a dedicated service account granted:
- `roles/aiplatform.user` (to call Vertex AI Gemini and text embeddings without API keys)
- `roles/cloudsql.client` (to connect via the Cloud SQL Unix socket)

To apply GCP with Vertex AI:
```bash
cd infra/terraform/gcp
terraform init
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-central1" \
  -var="backend_image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/hr-repo/hr-backend:latest" \
  -var="frontend_image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/hr-repo/hr-frontend:latest" \
  -var="db_password=YOUR_SECURE_PASSWORD" \
  -var="llm_provider=vertexai" \
  -var="llm_model=gemini-3.8-flash" \
  -var="vertex_ai_location=global" \
  -var="embedding_provider=vertexai" \
  -var="embedding_model=text-embedding-004" \
  -var="embedding_dim=768"
```

The current defaults use `gemini-3.8-flash` and `text-embedding-004` on the global Vertex AI
endpoint. Check the
[Vertex AI model lifecycle table](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions)
before changing the model variables; Google lists retirement dates there.

After applying, use `terraform output frontend_url` to open the deployed UI. The frontend's
Nginx container proxies `/api/` requests to the backend Cloud Run service.

Notes:
- AWS requires an existing VPC with public and private subnets (vpc_id, public_subnet_ids, private_subnet_ids).
- GCP connects to Cloud SQL through the Cloud Run Unix socket. The Cloud SQL instance has a public IP but no authorized networks, so only the Cloud Run connector can reach it.
- The GCP configuration makes the frontend and backend Cloud Run services publicly invokable. This is for learning/demo use only; the app has no authentication or tenant isolation and must not be used with real candidate information.
- Azure's firewall rule for 0.0.0.0 allows all Azure services. Tighten it for production.
- Secrets are passed as Terraform variables and end up in state. Move them to Secret Manager or Key Vault for production.
