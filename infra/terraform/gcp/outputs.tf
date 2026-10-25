output "api_url" { value = google_cloud_run_v2_service.backend.uri }
output "frontend_url" { value = google_cloud_run_v2_service.frontend.uri }
output "db_connection_name" { value = google_sql_database_instance.db.connection_name }
