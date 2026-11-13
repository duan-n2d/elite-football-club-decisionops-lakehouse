"""Baseline ticket and merchandise demand forecast with optional MLflow logging."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from lakehouse.io import read_table, to_float, write_table
from monitoring.pipeline_run_logger import log_event


def build_demand_forecast(lakehouse_path: str | Path) -> int:
    revenue_rows = read_table(lakehouse_path, "gold", "fact_matchday_revenue")
    by_type: dict[str, list[float]] = defaultdict(list)
    for row in revenue_rows:
        by_type[str(row.get("revenue_type", ""))].append(to_float(row.get("unit_count")))

    forecast_rows = []
    for revenue_type, values in by_type.items():
        if not values:
            continue
        recent = values[-5:]
        forecast_units = round(sum(recent) / len(recent), 2)
        naive_error = round(sum(abs(value - forecast_units) for value in recent) / len(recent), 2)
        forecast_rows.append(
            {
                "forecast_id": f"baseline_{revenue_type}",
                "revenue_type": revenue_type,
                "forecast_horizon": "next_home_fixture",
                "forecast_units": forecast_units,
                "model_name": "moving_average_baseline",
                "validation_mae": naive_error,
            }
        )

    write_table(lakehouse_path, "gold", "fact_demand_forecast", forecast_rows)
    _log_mlflow(forecast_rows)
    log_event("demand_forecast", "success", {"forecast_rows": len(forecast_rows)})
    return len(forecast_rows)


def _log_mlflow(forecast_rows: list[dict[str, object]]) -> None:
    try:
        import mlflow
    except ImportError:
        return

    if not forecast_rows:
        return
    try:
        mlflow.set_experiment("elite-football-club-demand-forecast")
        with mlflow.start_run(run_name="moving_average_baseline"):
            avg_mae = sum(to_float(row.get("validation_mae")) for row in forecast_rows) / len(forecast_rows)
            mlflow.log_param("model_type", "moving_average_baseline")
            mlflow.log_metric("validation_mae", round(avg_mae, 2))
            mlflow.log_metric("forecast_rows", len(forecast_rows))
    except Exception as exc:  # pragma: no cover - MLflow availability differs locally
        log_event("demand_forecast_mlflow", "failed", {"error": str(exc)})

