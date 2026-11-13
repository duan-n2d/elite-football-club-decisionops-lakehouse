"""Run Silver and Gold transformations."""

from __future__ import annotations

import argparse

from lakehouse.config import load_config
from monitoring.pipeline_run_logger import build_observability_tables, logged_step
from transformations.gold.demand_forecast import build_demand_forecast
from transformations.gold.build_gold import build_gold
from transformations.silver.build_silver import build_silver


def run_transformations(lakehouse_path: str) -> dict[str, dict[str, int]]:
    with logged_step("silver_transformations"):
        silver_counts = build_silver(lakehouse_path)
    with logged_step("gold_transformations"):
        gold_counts = build_gold(lakehouse_path)
    with logged_step("demand_forecast"):
        gold_counts["fact_demand_forecast"] = build_demand_forecast(lakehouse_path)
    with logged_step("observability_tables"):
        monitoring_counts = build_observability_tables(lakehouse_path)
    return {"silver": silver_counts, "gold": gold_counts, "monitoring": monitoring_counts}


def _parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser(description="Run local lakehouse transformations.")
    parser.add_argument("--lakehouse-path", default=str(config.lakehouse_path))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = run_transformations(args.lakehouse_path)
    for layer, counts in results.items():
        print(f"[{layer}]")
        for table_name, count in sorted(counts.items()):
            print(f"  {table_name}: {count}")


if __name__ == "__main__":
    main()
