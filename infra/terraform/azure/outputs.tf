output "api_url" { value = "https://${azurerm_linux_web_app.backend.default_hostname}" }
output "db_fqdn" { value = azurerm_postgresql_flexible_server.db.fqdn }
