variable "environment" {
  type        = string
  description = "Deployment environment."
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Azure region."
  default     = "eastus"
}

variable "tenant_id" {
  type        = string
  description = "Azure tenant ID for Key Vault."
}

variable "storage_account_name" {
  type        = string
  description = "Globally unique ADLS Gen2 storage account name."
}

variable "key_vault_name" {
  type        = string
  description = "Globally unique Key Vault name."
}

