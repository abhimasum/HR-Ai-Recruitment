terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
    random  = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "hr" {
  name     = "rg-hr-recruitment"
  location = var.location
}

# ---- Azure Database for PostgreSQL Flexible Server ----
resource "azurerm_postgresql_flexible_server" "db" {
  name                   = "psql-hr-recruitment"
  resource_group_name    = azurerm_resource_group.hr.name
  location               = azurerm_resource_group.hr.location
  version                = "16"
  administrator_login    = "hr"
  administrator_password = var.db_password
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"
  zone                   = "1"
}

# Allow pgvector to be installed
resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.db.id
  value     = "VECTOR"
}

resource "azurerm_postgresql_flexible_server_database" "hr" {
  name      = "hr"
  server_id = azurerm_postgresql_flexible_server.db.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}

# Allow Azure-hosted services to reach the server. Tighten to the App Service
# outbound IPs or a VNet integration for production.
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.db.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ---- App Service (Linux container) ----
resource "azurerm_service_plan" "app" {
  name                = "asp-hr-recruitment"
  resource_group_name = azurerm_resource_group.hr.name
  location            = azurerm_resource_group.hr.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_linux_web_app" "backend" {
  name                = "app-hr-backend-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.hr.name
  location            = azurerm_resource_group.hr.location
  service_plan_id     = azurerm_service_plan.app.id

  site_config {
    health_check_path = "/health"
    application_stack {
      docker_image_name   = var.backend_image
      docker_registry_url = "https://${split("/", var.backend_image)[0]}"
    }
  }

  app_settings = {
    WEBSITES_PORT   = "8000"
    DATABASE_URL    = "postgresql+asyncpg://hr:${var.db_password}@${azurerm_postgresql_flexible_server.db.fqdn}:5432/hr?ssl=require"
    OPENAI_API_KEY  = var.openai_api_key
  }
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}
