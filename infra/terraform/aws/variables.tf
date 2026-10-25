variable "region" { type = string, default = "us-east-1" }
variable "vpc_id" { type = string }
variable "public_subnet_ids" { type = list(string) }
variable "private_subnet_ids" { type = list(string) }
variable "backend_image" { type = string, description = "ECR image URI for the backend" }
variable "db_password" { type = string, sensitive = true }
variable "openai_api_key" { type = string, sensitive = true, default = "" }
