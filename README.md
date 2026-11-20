# Elite Football Club DecisionOps Lakehouse

Portfolio data engineering project for a fictional global football club. It combines stakeholder discovery, synthetic data, a Bronze/Silver/Gold pipeline, Gold data products, APIs, dashboards, AI guardrails, observability, CI/CD, and adoption measurement.

No private club data, trademarks, or assets are used.

## What Actually Runs

The runnable pipeline is **plain Python over synthetic data**: each step reads CSV files into lists of dicts, transforms them in Python, and writes CSV files under `lakehouse_local/<layer>/`. Specifically:

- **No Spark, Databricks, or Delta at runtime.** `lakehouse/spark.py` defines `get_spark()`, but nothing calls it. The `transformations/**/*.sql` files are reference SQL and are never executed; the real Silver/Gold logic is in `build_silver.py` and `build_gold.py`. The Databricks/Terraform files under `infra/` and `orchestration/databricks_job.yml` are an untested deployment skeleton.
- **Quality checks are hand-written Python** in `quality/run_checks.py` (see [Data Quality Examples](#data-quality-examples)). The Great Expectations-style YAML suites in `quality/checks/` are examples only and are not read by any code.
- **MLflow forecast** is a moving average of the last 5 values per revenue type. Its `validation_mae` is computed on those same 5 values (in-sample), so it is not a real validation metric. Logging to MLflow is skipped silently if `mlflow` is not importable.
- **ClubOps Copilot is a rule-based keyword router.** It matches keywords in the question, picks a canned SQL string, validates it with `sql_validator.py`, and returns it as `generated_sql`, but **that SQL is not executed**. The answer comes from the same Python repository functions the API uses.
- **MinIO** is started by `docker-compose.yml` but nothing reads from or writes to it.
- **`--from-date`** does not filter data. It only makes Bronze ingestion reprocess every landing file (instead of skipping already-seen files) and records the date in the run log.

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
  lakehouse/                     # Config, CSV IO, unused Spark/Delta session helper
  monitoring/                    # Pipeline logging, freshness, alert design
  orchestration/                 # Local runner, Airflow fallback, Databricks job YAML
  quality/                       # Local Python quality checks; GE-style YAML examples (not executed)
  transformations/               # Silver/Gold Python transforms; SQL files are reference only
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

Target architecture. Locally, only the CSV path is implemented; see [What Actually Runs](#what-actually-runs).

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
- Local CSV tables (the only storage path that runs today)
- Azure Databricks and Delta Lake deployment path (skeleton, not run)
- ADLS Gen2 or MinIO landing zone (planned; MinIO container is started but unused)
- Databricks Lakeflow Jobs target, Airflow fallback (config only)
- Unity Catalog-style governance SQL (not run)
- Python quality checks; Great Expectations-style YAML suites as examples
- Moving-average demand forecast with optional MLflow logging
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

## Data Quality Examples

```bash
python -m quality.run_checks --fail-on-error
```

Checks implemented in `quality/run_checks.py`:

- `silver.players`: `player_id` is unique and not null.
- `silver.training_sessions`: table is not empty.
- `silver.gps_tracking_aggregates`: `max_speed_kmh` is between 0 and 45.
- `silver.ticket_sales`: `price_paid` is non-negative.
- `silver.merchandise_orders`: `net_revenue` is non-negative.
- `gold.fact_player_readiness_daily`: `readiness_score` is between 0 and 100.
- `gold.fact_matchday_revenue`: `net_revenue` is non-negative.
- `gold.fact_product_adoption`: table is not empty.
- `silver.quarantine_failed_records`: simulated bad records were captured.

Results are written to `lakehouse_local/quality/quality_results.csv`.

## AI Assistant Examples

The Copilot is rule-based: keyword matching picks one of a few fixed queries. The returned `generated_sql` is validated but not executed.

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

Not tested. These steps describe the intended path; the jobs in `orchestration/databricks_job.yml` point at the same Python/CSV entrypoints used locally.

1. Provision infrastructure from `infra/terraform`.
2. Create Unity Catalog objects with `infra/databricks/unity_catalog.sql`.
3. Configure secrets in Azure Key Vault and Databricks secrets.
4. Upload or sync the repo to Databricks.
5. Deploy job config from `orchestration/databricks_job.yml` or `infra/databricks/asset_bundle.yml`.
6. Switch table IO from local CSV to Spark/Delta by using `lakehouse/spark.py` in job entrypoints. (Not done yet: every job entrypoint currently uses the CSV IO in `lakehouse/io.py`.)
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
- [x] Implement incremental Bronze ingestion (file-hash based).
- [x] Implement Silver cleaning, validation, dedupe, quarantine.
- [x] Implement Gold facts, dimensions (Python), and SQL examples (reference only, not executed).
- [x] Add local quality runner (Python checks).
- [ ] Run the Great Expectations YAML suites (currently examples only).
- [x] Add run logging, freshness checks, and monitoring tables.
- [x] Add FastAPI endpoints.
- [x] Add Streamlit dashboard pages.
- [x] Add moving-average demand forecast baseline with optional MLflow logging.
- [ ] Hold-out validation for the forecast (current `validation_mae` is in-sample).
- [x] Add ClubOps Copilot guardrails, eval set, and logs (rule-based; generated SQL not executed).
- [x] Add Docker Compose, Makefile, GitHub Actions, and `.env.example`.
- [x] Add Terraform-style Azure and Databricks deployment skeleton (not deployed).
- [ ] Run transformations on Spark/Delta via `lakehouse/spark.py`.
- [ ] Use MinIO as the landing zone.
- [ ] Make `--from-date` actually filter backfills.
- [x] Add documentation and interview guide.
- [x] Add local smoke tests.

## Limitations

- Synthetic data does not represent real club operations.
- Local CSV tables are the only implemented storage; there is no Delta Lake path that runs.
- Copilot is a guarded rule-based stub; its generated SQL is not executed. Production should use a governed LLM deployment.
- Forecasting is a baseline demonstration with an in-sample error metric, not a production demand model.

## Future Improvements

See `docs/09_future_improvements.md`.

