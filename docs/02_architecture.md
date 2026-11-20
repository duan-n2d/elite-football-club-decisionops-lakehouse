# Architecture

## Diagram

```text
Synthetic Sources
        |
        v
Landing Zone: local files, MinIO, or ADLS Gen2
        |
        v
Bronze: raw append-only tables with ingestion metadata
        |
        v
Silver: cleaned, typed, deduped, validated records
        |            \
        |             --> Quarantine: failed records with reasons
        v
Gold: star schema, metrics, forecasts, adoption marts
        |
        +--> FastAPI data product endpoints
        +--> Streamlit dashboard
        +--> ClubOps Copilot
        +--> Monitoring and quality dashboard
        +--> MLflow experiment tracking
```

## Data Flow

Synthetic files land under `data/landing/<source>/`. Bronze ingestion appends records with source file, file hash, run ID, schema version, ingestion timestamp, and record hash. Silver validates, deduplicates, standardizes, and quarantines failures. Gold builds stakeholder-ready facts and dimensions. APIs, dashboards, monitoring, and Copilot read only trusted outputs.

## Batch vs Near-Real-Time

The MVP is daily batch because most stakeholder decisions are daily staff meetings, matchday planning, campaign review, and executive reporting. The design can move selected feeds to near-real-time with Databricks Auto Loader, structured streaming, and Delta tables for fan events or product adoption events.

## Technology Choices

Currently implemented: local files and CSV tables, Python transforms, Python quality checks, FastAPI, Streamlit, optional MLflow logging, GitHub Actions, Docker Compose. Databricks, Delta Lake, ADLS Gen2, MinIO storage, Lakeflow, Unity Catalog, and Great Expectations execution are design targets that are not wired in yet.

- ADLS Gen2 or MinIO/local landing for cloud and local parity.
- Azure Databricks and Delta Lake for scalable lakehouse production.
- Local CSV fallback for zero-credential demos.
- Lakeflow Jobs target and Airflow fallback for orchestration.
- Unity Catalog-style schemas, grants, and tags for governance.
- Great Expectations-style checks for understandable quality rules.
- FastAPI and Streamlit for product delivery.
- MLflow for forecast experiment tracking.
- GitHub Actions and Docker Compose for engineering quality.

## Intentionally Avoided

Kafka, Kubernetes, feature stores, dbt, and real private vendor integrations are avoided in the MVP to keep the project focused on end-to-end ownership instead of tooling sprawl.

