# Elite Football Club DecisionOps Lakehouse

Forward-deployed, portfolio-grade data engineering project for a fictional global football club. It combines stakeholder discovery, synthetic data, Azure Databricks-style lakehouse engineering, governed Gold data products, APIs, dashboards, AI guardrails, observability, CI/CD, and adoption measurement.

No private club data, trademarks, or assets are used.

## Concise Project Summary

Football clubs make high-pressure decisions across sporting, commercial, fan, and corporate teams. Those decisions often depend on disconnected spreadsheets, exported vendor files, and manual reporting. This project builds a reusable DecisionOps lakehouse that turns trusted data into daily workflows:

- Football operations monitors training workload, availability, and readiness.
- Commercial teams track matchday ticket and merchandise revenue.
- Fan engagement teams use governed segments and campaign metrics.
- Executives see adoption, data quality, business impact, and automation progress.
- ClubOps Copilot answers plain-English questions only from trusted Silver and Gold data.

This is a forward-deployed data engineering project because it starts from stakeholder workflows, delivers operational applications, measures adoption, and includes governance, deployment, monitoring, and AI controls.

## Complete Repo Tree

```text
elite-football-club-decisionops-lakehouse/
  ai_assistant/                  # ClubOps Copilot guardrails, semantic layer, eval set
  api/                           # FastAPI data product endpoints
  dashboard/                     # Streamlit stakeholder dashboard
  data_generator/                # Synthetic source contracts and generator
  ingestion/                     # Incremental Bronze loaders
  lakehouse/                     # Config, IO, optional Spark/Delta session
  monitoring/                    # Pipeline logging, freshness, alert design
  orchestration/                 # Local runner, Airflow fallback, Databricks job YAML
  quality/                       # Local quality checks and GE-style suites
  transformations/               # Silver/Gold Python transforms and SQL examples
  infra/                         # Terraform-style Azure and Databricks skeleton
  tests/                         # Unit and smoke tests
  docs/                          # Discovery, architecture, data model, demo, interviews
  .github/workflows/ci.yml
  docker-compose.yml
  Dockerfile
  Makefile
  pyproject.toml
  .env.example
```

## Architecture

```text
Synthetic Sources
(players, GPS, wellness, tickets, merch, fans, campaigns, workflows)
        |
        v
Local files / ADLS Gen2 / MinIO landing
        |
        v
Bronze CSV locally, Delta on Databricks
raw append-only + ingestion metadata
        |
        v
Silver tables
cleaning, validation, dedupe, quarantine
        |
        v
Gold star schema
facts, dimensions, forecasts, adoption marts
        |
        +--> FastAPI endpoints
        +--> Streamlit dashboard
        +--> MLflow baseline forecast
        +--> ClubOps Copilot over trusted data
        +--> Monitoring and adoption metrics
```

## Tech Stack

- Python, SQL, FastAPI, Streamlit
- Local CSV lakehouse fallback for easy demos
- Azure Databricks and Delta Lake deployment path
- ADLS Gen2 or local MinIO-compatible landing zone
- Databricks Lakeflow Jobs target, Airflow fallback
- Unity Catalog-style governance SQL
- Great Expectations-style quality suites plus local checks
- MLflow-ready baseline demand forecast
- Docker Compose, GitHub Actions, Terraform-style infra

## Dataset Description

The generator creates deterministic synthetic data for:

- players, teams, training sessions
- GPS/tracking aggregates, wellness surveys, injuries/availability
- fixtures, match events
- ticket sales, merchandise orders
- fan engagement events, marketing campaigns
- staff workflow events, product adoption events

Simulated data quality issues include duplicates, invalid enums, missing IDs, negative revenue, out-of-range GPS values, and invalid readiness inputs. These are quarantined in `silver.quarantine_failed_records`.

## How To Run Locally

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m orchestration.run_pipeline --days 60 --fans 1500
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

Or with Make:

```bash
make setup
make pipeline
make api
make dashboard
```

Docker:

```bash
docker compose up --build
```

## API Examples

```bash
curl http://localhost:8000/readiness/players
curl http://localhost:8000/matchday/revenue
curl http://localhost:8000/fans/segments
curl http://localhost:8000/campaigns/performance
curl http://localhost:8000/adoption/metrics
curl http://localhost:8000/quality/status
```

Copilot:

```bash
curl -X POST http://localhost:8000/copilot/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Which players have the lowest readiness this week?","user_persona":"Head of Football Operations"}'
```

## Dashboard Examples

Streamlit pages:

- Executive Overview
- Football Operations
- Matchday Revenue
- Fan Engagement
- Campaign Performance
- Data Quality & Pipeline Monitoring
- Product Adoption
- ClubOps Copilot

Screenshot placeholders:

- `docs/images/executive_overview.png`
- `docs/images/football_operations.png`
- `docs/images/data_quality_monitoring.png`

## Data Quality Examples

```bash
python -m quality.run_checks --fail-on-error
```

Example checks:

- Player IDs are unique and not null.
- GPS speed is within expected physical range.
- Revenue is non-negative.
- Readiness scores are between 0 and 100.
- Simulated bad records are captured in quarantine.

## AI Assistant Examples

Supported:

- "Which players have the lowest readiness this week?"
- "Which fan segment is largest?"
- "What is the current data quality score?"

Refused:

- Private fan identity requests.
- Medical diagnosis questions.
- Salary, contract, or scouting-target questions.
- Any SQL mutation request.

## 4-Week Build Plan

Week 1: scaffold repo, generate synthetic data, load Bronze, write discovery docs.

Week 2: implement Silver/Gold transformations, quality checks, quarantine, run logging, idempotency, and backfills.

Week 3: build FastAPI, Streamlit, adoption metrics, monitoring, and MLflow baseline forecast.

Week 4: add ClubOps Copilot, CI/CD, infra skeleton, demo script, interview talking points, polish, and smoke tests.

## MVP Scope

- End-to-end synthetic data generation.
- Incremental Bronze ingestion.
- Silver cleaning, dedupe, validation, quarantine.
- Gold facts and dimensions.
- Local pipeline logging and quality checks.
- FastAPI and Streamlit product surfaces.
- Guarded local Copilot stub.
- CI/CD and Docker Compose.

## Stretch Scope

- Databricks Asset Bundle deployment.
- Production Delta tables and Auto Loader.
- Azure OpenAI-backed Copilot.
- Unity Catalog grants, tags, and lineage.
- Stronger forecasting with feature engineering and MLflow registry.
- Power BI semantic model.

## Data Model

Gold tables:

- `fact_player_workload_daily`
- `fact_player_readiness_daily`
- `fact_matchday_revenue`
- `fact_fan_engagement_daily`
- `fact_campaign_performance`
- `fact_product_adoption`
- `fact_demand_forecast`
- `dim_player`
- `dim_team`
- `dim_fixture`
- `dim_fan_segment`
- `dim_date`

## Deploy To Azure Databricks

1. Provision infrastructure from `infra/terraform`.
2. Create Unity Catalog objects with `infra/databricks/unity_catalog.sql`.
3. Configure secrets in Azure Key Vault and Databricks secrets.
4. Upload or sync the repo to Databricks.
5. Deploy job config from `orchestration/databricks_job.yml` or `infra/databricks/asset_bundle.yml`.
6. Switch table IO from local CSV to Spark/Delta by using `lakehouse/spark.py` in job entrypoints.
7. Point API/dashboard to Databricks SQL warehouse or serving layer for production.

## Business Impact Summary

The project measures:

- Time saved per week.
- Reduction in manual reporting.
- Increase in trusted dashboard usage.
- Number of reusable data products.
- Number of stakeholder workflows automated.
- Forecast accuracy for ticket and merchandise demand.
- Copilot usage, refusal quality, latency, and estimated cost.

## Implementation Checklist

- [x] Create repo scaffold and config files.
- [x] Implement synthetic generator and source contracts.
- [x] Implement incremental Bronze ingestion.
- [x] Implement Silver cleaning, validation, dedupe, quarantine.
- [x] Implement Gold facts, dimensions, and SQL examples.
- [x] Add quality suites and local quality runner.
- [x] Add run logging, freshness checks, and monitoring tables.
- [x] Add FastAPI endpoints.
- [x] Add Streamlit dashboard pages.
- [x] Add MLflow-ready demand forecast baseline.
- [x] Add ClubOps Copilot guardrails, eval set, and logs.
- [x] Add Docker Compose, Makefile, GitHub Actions, and `.env.example`.
- [x] Add Terraform-style Azure and Databricks deployment skeleton.
- [x] Add documentation and interview guide.
- [x] Add local smoke tests.

## Limitations

- Synthetic data does not represent real club operations.
- Local CSV tables are a portable fallback, not a replacement for production Delta Lake.
- Copilot is a guarded rule-based stub locally; production should use a governed LLM deployment.
- Forecasting is a baseline demonstration, not a production demand model.

## Future Improvements

See `docs/09_future_improvements.md`.

