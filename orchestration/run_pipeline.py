"""End-to-end local pipeline runner."""

from __future__ import annotations

import argparse
import uuid

from data_generator.generate import generate_all
from ingestion.load_bronze import load_all_sources
from lakehouse.config import load_config
from monitoring.pipeline_run_logger import build_observability_tables, logged_step, log_event
from quality.run_checks import run_quality_checks
from transformations.run_transformations import run_transformations


def run_pipeline(
    days: int = 60,
    fans: int = 1500,
    squad_size: int = 36,
    seed: int = 7,
    start_date: str = "2026-01-01",
    force: bool = False,
    from_date: str | None = None,
) -> dict[str, object]:
    config = load_config()
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    log_event("pipeline", "started", {"run_id": run_id})

    with logged_step("synthetic_generation", {"run_id": run_id}):
        generated = generate_all(
            output_dir=config.landing_path,
            days=days,
            fans=fans,
            squad_size=squad_size,
            seed=seed,
            start_date=start_date,
        )

    with logged_step("bronze_ingestion", {"run_id": run_id}):
        ingestion_results = load_all_sources(
            landing_path=config.landing_path,
            lakehouse_path=config.lakehouse_path,
            control_path=config.control_path,
            run_id=run_id,
            from_date=from_date,
            force=force,
        )

    with logged_step("transformations", {"run_id": run_id}):
        transformation_results = run_transformations(str(config.lakehouse_path))

    with logged_step("quality_checks", {"run_id": run_id}):
        quality_results = run_quality_checks(config.lakehouse_path)

    with logged_step("observability_refresh", {"run_id": run_id}):
        monitoring_results = build_observability_tables(config.lakehouse_path)

    failed_checks = [row for row in quality_results if row["status"] == "failed"]
    pipeline_status = "failed" if failed_checks else "success"
    log_event(
        "pipeline",
        pipeline_status,
        {
            "run_id": run_id,
            "generated_batch": generated.batch_id,
            "failed_quality_checks": len(failed_checks),
        },
    )
    return {
        "run_id": run_id,
        "generated": generated.row_counts,
        "ingestion": [result.__dict__ for result in ingestion_results],
        "transformations": transformation_results,
        "quality_failed": len(failed_checks),
        "monitoring": monitoring_results,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full local DecisionOps pipeline.")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--fans", type=int, default=1500)
    parser.add_argument("--squad-size", type=int, default=36)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--start-date", default="2026-01-01")
    parser.add_argument("--from-date", default=None, help="Backfill watermark documented in run metadata.")
    parser.add_argument("--force", action="store_true", help="Reload previously processed landing files.")
    parser.add_argument("--fail-on-quality", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_pipeline(
        days=args.days,
        fans=args.fans,
        squad_size=args.squad_size,
        seed=args.seed,
        start_date=args.start_date,
        force=args.force,
        from_date=args.from_date,
    )
    print(f"Pipeline run_id={result['run_id']} quality_failed={result['quality_failed']}")
    if result["quality_failed"] and args.fail_on_quality:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

