"""Airflow fallback DAG for local or managed-Airflow orchestration.

Databricks Lakeflow Jobs is the target orchestration option. This DAG exists to
show how the same modular Python entrypoints can be reused when a club already
standardizes on Airflow.
"""

from __future__ import annotations

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
except ImportError:  # pragma: no cover - documentation scaffold
    DAG = None
    BashOperator = None


if DAG is not None:
    with DAG(
        dag_id="elite_football_club_decisionops_lakehouse",
        start_date=datetime(2026, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["football", "lakehouse", "decisionops"],
    ) as dag:
        generate = BashOperator(task_id="generate_synthetic_data", bash_command="python -m data_generator.generate")
        bronze = BashOperator(task_id="load_bronze", bash_command="python -m ingestion.load_bronze")
        transform = BashOperator(task_id="transform_silver_gold", bash_command="python -m transformations.run_transformations")
        quality = BashOperator(task_id="quality_checks", bash_command="python -m quality.run_checks --fail-on-error")

        generate >> bronze >> transform >> quality

