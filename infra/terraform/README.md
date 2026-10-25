# Terraform (multi-cloud)

Each cloud is a standalone root module. Run one at a time:

    cd infra/terraform/aws      # or gcp / azure
    terraform init
    terraform apply -var="db_password=..." -var="backend_image=..." [other vars]

Push the backend image first (`docker build -t <registry>/hr-backend backend && docker push <registry>/hr-backend`).

| Cloud | Compute | Database | Registry | AI / LLM Provider |
|-------|---------|----------|----------|-------------------|
| AWS   | ECS Fargate behind an ALB | Aurora PostgreSQL 16 | ECR | OpenAI |
| GCP   | Cloud Run | Cloud SQL for PostgreSQL 16 | Artifact Registry | GCP Vertex AI (Gemini + Embeddings) or OpenAI |
| Azure | App Service for Containers | Flexible Server PostgreSQL 16 (VECTOR extension allowlisted) | ACR | OpenAI |

### GCP Deployment with Vertex AI
By default, the GCP Terraform module sets up Cloud Run with a dedicated Service Account granted:
- `roles/aiplatform.user` (to call Vertex AI Gemini 1.5 and text-embedding-004 without API keys)
- `roles/cloudsql.client` (to connect via the Cloud SQL Unix socket)

To apply GCP with Vertex AI:
```bash
cd infra/terraform/gcp
terraform init
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-central1" \
  -var="backend_image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/hr-repo/hr-backend:latest" \
  -var="db_password=YOUR_SECURE_PASSWORD" \
  -var="llm_provider=vertexai" \
  -var="llm_model=gemini-1.5-flash" \
  -var="embedding_provider=vertexai" \
  -var="embedding_model=text-embedding-004" \
  -var="embedding_dim=768"
```

Notes:
- AWS requires an existing VPC with public and private subnets (vpc_id, public_subnet_ids, private_subnet_ids).
- GCP connects to Cloud SQL through the Cloud Run Unix socket. The Cloud SQL instance has a public IP but no authorized networks, so only the Cloud Run connector can reach it.
- Azure's firewall rule for 0.0.0.0 allows all Azure services. Tighten it for production.
- Secrets are passed as Terraform variables and end up in state. Move them to Secret Manager or Key Vault for production.
