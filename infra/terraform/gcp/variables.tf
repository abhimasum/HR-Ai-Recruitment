variable "project_id" { type = string }
variable "region" { type = string, default = "us-central1" }
variable "backend_image" { type = string, description = "Artifact Registry image URI" }
variable "db_password" { type = string, sensitive = true }
variable "openai_api_key" { type = string, sensitive = true, default = "" }
variable "llm_provider" { type = string, default = "vertexai", description = "vertexai or openai" }
variable "llm_model" { type = string, default = "gemini-1.5-flash" }
variable "embedding_provider" { type = string, default = "vertexai", description = "vertexai, openai, or huggingface" }
variable "embedding_model" { type = string, default = "text-embedding-004" }
variable "embedding_dim" { type = number, default = 768 }
variable "cors_origins" { type = string, default = "*" }
variable "min_instances" { type = number, default = 1 }
variable "max_instances" { type = number, default = 5 }
