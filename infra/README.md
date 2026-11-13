# Infrastructure

This folder shows how the local demo maps to Azure and Databricks. It is intentionally a deployable skeleton rather than a live subscription-specific configuration.

- `terraform/` provisions resource groups, ADLS Gen2, Azure Databricks workspace, Key Vault, and monitoring placeholders.
- `databricks/asset_bundle.yml` maps repo entrypoints into Databricks jobs.
- `databricks/unity_catalog.sql` documents catalog, schema, grant, and tag strategy.

Production secrets should be stored in Azure Key Vault and referenced by Databricks secrets or GitHub Actions environments.

