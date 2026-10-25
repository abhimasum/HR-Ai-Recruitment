variable "project_id" { type = string }
variable "region" { type = string, default = "us-central1" }
variable "backend_image" { type = string, description = "Artifact Registry image URI" }
variable "db_password" { type = string, sensitive = true }
variable "openai_api_key" { type = string, sensitive = true, default = "" }
