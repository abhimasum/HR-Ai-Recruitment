variable "location" { type = string, default = "eastus" }
variable "backend_image" { type = string, description = "ACR image, e.g. myacr.azurecr.io/hr-backend:latest" }
variable "db_password" { type = string, sensitive = true }
variable "openai_api_key" { type = string, sensitive = true, default = "" }
