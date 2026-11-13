output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.workspace.workspace_url
}

output "storage_account_name" {
  value = azurerm_storage_account.lakehouse.name
}

output "landing_container" {
  value = azurerm_storage_container.landing.name
}

output "lakehouse_container" {
  value = azurerm_storage_container.lakehouse.name
}

