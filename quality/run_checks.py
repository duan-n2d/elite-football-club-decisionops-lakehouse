"""Run lightweight local data quality checks.

Great Expectations YAML examples are included in `quality/checks/`. This module
implements equivalent checks without external services so CI can validate the
portfolio pipeline quickly.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from lakehouse.config import load_config
from lakehouse.io import Row, read_table, to_float, write_table
from monitoring.pipeline_run_logger import build_observability_tables, log_event


CheckFn = Callable[[list[Row]], tuple[bool, str]]


def _unique_non_null(column: str) -> CheckFn:
    def check(rows: list[Row]) -> tuple[bool, str]:
        values = [str(row.get(column, "")) for row in rows]
        non_null = [value for value in values if value]
        return len(non_null) == len(rows) and len(set(non_null)) == len(non_null), (
            f"{column} must be non-null and unique"
        )

    return check


def _between(column: str, minimum: float, maximum: float) -> CheckFn:
    def check(rows: list[Row]) -> tuple[bool, str]:
        bad = [row for row in rows if not minimum <= to_float(row.get(column), minimum - 1) <= maximum]
        return not bad, f"{column} must be between {minimum} and {maximum}; bad_rows={len(bad)}"

    return check


def _non_negative(column: str) -> CheckFn:
    def check(rows: list[Row]) -> tuple[bool, str]:
        bad = [row for row in rows if to_float(row.get(column), -1) < 0]
        return not bad, f"{column} must be non-negative; bad_rows={len(bad)}"

    return check


def _not_empty(rows: list[Row]) -> tuple[bool, str]:
    return bool(rows), "table must not be empty"


def run_quality_checks(lakehouse_path: str | Path) -> list[Row]:
    checks: list[tuple[str, str, CheckFn]] = [
        ("silver.players", "players_unique", _unique_non_null("player_id")),
        ("silver.training_sessions", "sessions_not_empty", _not_empty),
        ("silver.gps_tracking_aggregates", "gps_speed_range", _between("max_speed_kmh", 0, 45)),
        ("silver.ticket_sales", "ticket_revenue_non_negative", _non_negative("price_paid")),
        ("silver.merchandise_orders", "merch_revenue_non_negative", _non_negative("net_revenue")),
        ("gold.fact_player_readiness_daily", "readiness_score_range", _between("readiness_score", 0, 100)),
        ("gold.fact_matchday_revenue", "matchday_revenue_non_negative", _non_negative("net_revenue")),
        ("gold.fact_product_adoption", "adoption_not_empty", _not_empty),
    ]

    results: list[Row] = []
    for table_ref, check_name, check_fn in checks:
        layer, table_name = table_ref.split(".", 1)
        rows = read_table(lakehouse_path, layer, table_name)
        passed, message = check_fn(rows)
        results.append(
            {
                "table_name": table_ref,
                "check_name": check_name,
                "status": "passed" if passed else "failed",
                "message": message,
                "row_count": len(rows),
            }
        )

    quarantine_rows = read_table(lakehouse_path, "silver", "quarantine_failed_records")
    results.append(
        {
            "table_name": "silver.quarantine_failed_records",
            "check_name": "quarantine_present_for_simulated_bad_records",
            "status": "passed" if quarantine_rows else "failed",
            "message": "simulated bad records should be captured in quarantine",
            "row_count": len(quarantine_rows),
        }
    )

    write_table(
        lakehouse_path,
        "quality",
        "quality_results",
        results,
        columns=("table_name", "check_name", "status", "message", "row_count"),
    )
    failed = [result for result in results if result["status"] == "failed"]
    log_event("quality_checks", "failed" if failed else "success", {"failed_checks": len(failed), "checks": len(results)})
    build_observability_tables(lakehouse_path)
    return results


def _parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser(description="Run local data quality checks.")
    parser.add_argument("--lakehouse-path", default=str(config.lakehouse_path))
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = run_quality_checks(args.lakehouse_path)
    failed = [row for row in results if row["status"] == "failed"]
    for row in results:
        print(f"{row['status'].upper()} {row['table_name']}::{row['check_name']} - {row['message']}")
    if failed and args.fail_on_error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

