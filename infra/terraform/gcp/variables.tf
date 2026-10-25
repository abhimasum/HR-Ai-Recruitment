variable "project_id" { type = string }
variable "region" { type = string, default = "us-central1" }
variable "artifact_registry_repository" { type = string, default = "hr-repo" }
variable "backend_image" { type = string, description = "Artifact Registry image URI" }
variable "frontend_image" { type = string, description = "Artifact Registry frontend image URI" }
variable "db_password" { type = string, sensitive = true }
variable "db_admin_password" { type = string, sensitive = true }
variable "openai_api_key" { type = string, sensitive = true, default = "" }
variable "llm_provider" { type = string, default = "vertexai", description = "vertexai or openai" }
variable "llm_model" { type = string, default = "gemini-3.8-flash" }
variable "embedding_provider" { type = string, default = "vertexai", description = "vertexai, openai, or huggingface" }
variable "embedding_model" { type = string, default = "text-embedding-004" }
variable "embedding_dim" { type = number, default = 768 }
variable "cors_origins" { type = string, default = "*" }
variable "min_instances" { type = number, default = 0 }
variable "max_instances" { type = number, default = 5 }
variable "database_tier" {
  type        = string
  description = "Cloud SQL machine tier. db-f1-micro is for learning/demo use only."
  default     = "db-f1-micro"
}
variable "deletion_protection" {
  type        = bool
  description = "Protect the Cloud SQL instance from terraform destroy."
  default     = true
}
