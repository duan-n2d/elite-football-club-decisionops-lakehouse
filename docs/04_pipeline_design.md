# Pipeline Design

## Repository Folders

| Folder | Purpose | Main Files | Key Functions |
|---|---|---|---|
| data_generator | Synthetic source data | `contracts.py`, `generate.py` | `generate_all` |
| ingestion | Bronze loading | `load_bronze.py` | `load_incremental`, `load_all_sources` |
| lakehouse | Runtime config and IO | `config.py`, `io.py`, `spark.py` | `read_table`, `write_table`, `get_spark` |
| transformations | Silver/Gold marts | `build_silver.py`, `build_gold.py` | `build_silver`, `build_gold` |
| quality | Data checks | `run_checks.py`, `checks/*.yml` | `run_quality_checks` |
| orchestration | Pipeline runners | `run_pipeline.py`, `airflow_dag.py`, `databricks_job.yml` | `run_pipeline` |
| api | Data product endpoints | `main.py`, `repository.py` | endpoint handlers |
| dashboard | Stakeholder UI | `app.py` | Streamlit pages |
| ai_assistant | ClubOps Copilot | `copilot.py`, `sql_validator.py` | `answer_question`, `validate_sql` |
| monitoring | Observability | `pipeline_run_logger.py` | `log_event`, `build_observability_tables` |
| infra | Deployment skeleton | Terraform, UC SQL, bundle YAML | Azure and Databricks setup |
| tests | Validation | `test_pipeline_smoke.py` | local smoke test |
| docs | Portfolio narrative | Markdown docs | stakeholder and interview artifacts |

## Example Code

```python
result = load_incremental(
    source_name="ticket_sales",
    run_id="run_demo",
    landing_path="data/landing",
    lakehouse_path="lakehouse_local",
    control_path="data/control",
)
```

```sql
select
  fixture_id,
  channel,
  revenue_type,
  sum(net_revenue) as net_revenue
from gold.fact_matchday_revenue
group by fixture_id, channel, revenue_type;
```

## Pipeline Requirements

Implemented:

- Synthetic data generation.
- Incremental ingestion using file hashes.
- Bronze raw loads with metadata.
- Silver cleaning, validation, dedupe, and quarantine.
- Gold marts and dimensions.
- Data quality checks.
- Pipeline run logging.
- Idempotent reruns.
- Backfill run metadata using `--from-date`.
- Observability tables.
- Alert design in `monitoring/alerts.yml`.

