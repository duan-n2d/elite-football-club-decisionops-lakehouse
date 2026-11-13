terraform {
  required_version = ">= 1.7.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "decisionops" {
  name     = "rg-elite-fc-decisionops-${var.environment}"
  location = var.location
}

resource "azurerm_storage_account" "lakehouse" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.decisionops.name
  location                 = azurerm_resource_group.decisionops.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  tags = local.tags
}

resource "azurerm_storage_container" "landing" {
  name                  = "landing"
  storage_account_name  = azurerm_storage_account.lakehouse.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "lakehouse" {
  name                  = "lakehouse"
  storage_account_name  = azurerm_storage_account.lakehouse.name
  container_access_type = "private"
}

resource "azurerm_databricks_workspace" "workspace" {
  name                        = "dbw-elite-fc-decisionops-${var.environment}"
  resource_group_name         = azurerm_resource_group.decisionops.name
  location                    = azurerm_resource_group.decisionops.location
  sku                         = "premium"
  managed_resource_group_name = "rg-elite-fc-decisionops-managed-${var.environment}"

  tags = local.tags
}

resource "azurerm_key_vault" "secrets" {
  name                       = var.key_vault_name
  location                   = azurerm_resource_group.decisionops.location
  resource_group_name        = azurerm_resource_group.decisionops.name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  tags = local.tags
}

locals {
  tags = {
    project     = "elite-football-club-decisionops"
    environment = var.environment
    owner       = "data-platform"
  }
}

