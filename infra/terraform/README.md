# Terraform (multi-cloud)

Each cloud is a standalone root module. Run one at a time:

    cd infra/terraform/aws      # or gcp / azure
    terraform init
    terraform apply -var="db_password=..." -var="backend_image=..." [other vars]

Push the backend image first (`docker build -t <registry>/hr-backend backend && docker push <registry>/hr-backend`).

| Cloud | Compute | Database | Registry |
|-------|---------|----------|----------|
| AWS   | ECS Fargate behind an ALB | Aurora PostgreSQL 16 | ECR |
| GCP   | Cloud Run | Cloud SQL for PostgreSQL 16 | Artifact Registry |
| Azure | App Service for Containers | Flexible Server PostgreSQL 16 (VECTOR extension allowlisted) | ACR |

Notes:
- AWS requires an existing VPC with public and private subnets (vpc_id, public_subnet_ids, private_subnet_ids).
- GCP connects to Cloud SQL through the Cloud Run Unix socket. The Cloud SQL instance has a public IP but no authorized networks, so only the Cloud Run connector can reach it.
- Azure's firewall rule for 0.0.0.0 allows all Azure services. Tighten it for production.
- Secrets are passed as Terraform variables and end up in state. Move them to Secrets Manager, Secret Manager, or Key Vault for production.
- These configurations have not been run against live accounts. Run `terraform plan` before applying.
