"""Incrementally load source files into Bronze raw tables."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from data_generator.contracts import DATASET_CONTRACTS, SOURCE_NAMES
from lakehouse.config import load_config
from lakehouse.io import append_table, file_hash, load_json, read_csv, record_hash, utc_now, write_json
from monitoring.pipeline_run_logger import log_event


METADATA_COLUMNS = (
    "_ingestion_run_id",
    "_source_file",
    "_source_file_hash",
    "_ingested_at",
    "_schema_version",
    "_record_hash",
    "_source_payload",
)


@dataclass(frozen=True)
class LoadResult:
    source_name: str
    loaded_files: int
    loaded_rows: int
    skipped_files: int


def discover_source_files(landing_path: str | Path, source_name: str) -> list[Path]:
    source_dir = Path(landing_path) / source_name
    if not source_dir.exists():
        return []
    return sorted(source_dir.glob("*.csv"))


def load_incremental(
    source_name: str,
    run_id: str,
    landing_path: str | Path,
    lakehouse_path: str | Path,
    control_path: str | Path,
    from_date: str | None = None,
    force: bool = False,
) -> LoadResult:
    if source_name not in DATASET_CONTRACTS:
        raise ValueError(f"Unknown source: {source_name}")

    state_path = Path(control_path) / "ingestion_state.json"
    state = load_json(state_path, default={"processed_files": {}})
    processed_files: dict[str, str] = state.setdefault("processed_files", {})
    contract = DATASET_CONTRACTS[source_name]

    loaded_files = 0
    loaded_rows = 0
    skipped_files = 0
    all_columns = list(contract.columns) + list(METADATA_COLUMNS)

    for source_file in discover_source_files(landing_path, source_name):
        source_hash = file_hash(source_file)
        state_key = str(source_file.resolve())
        already_processed = processed_files.get(state_key) == source_hash
        if already_processed and not force and from_date is None:
            skipped_files += 1
            continue

        raw_rows = read_csv(source_file)
        ingested_at = utc_now()
        bronze_rows = []
        for row in raw_rows:
            payload = {column: row.get(column, "") for column in contract.columns}
            bronze_rows.append(
                {
                    **payload,
                    "_ingestion_run_id": run_id,
                    "_source_file": source_file.name,
                    "_source_file_hash": source_hash,
                    "_ingested_at": ingested_at,
                    "_schema_version": "1",
                    "_record_hash": record_hash(payload),
                    "_source_payload": json.dumps(payload, sort_keys=True),
                }
            )
        append_table(lakehouse_path, "bronze", f"raw_{source_name}", bronze_rows, columns=all_columns)
        processed_files[state_key] = source_hash
        loaded_files += 1
        loaded_rows += len(bronze_rows)

    write_json(state_path, state)
    result = LoadResult(
        source_name=source_name,
        loaded_files=loaded_files,
        loaded_rows=loaded_rows,
        skipped_files=skipped_files,
    )
    log_event(
        "bronze_ingestion",
        "success",
        {
            "run_id": run_id,
            "source_name": source_name,
            "loaded_files": loaded_files,
            "loaded_rows": loaded_rows,
            "skipped_files": skipped_files,
            "from_date": from_date,
        },
    )
    return result


def load_all_sources(
    landing_path: str | Path,
    lakehouse_path: str | Path,
    control_path: str | Path,
    run_id: str | None = None,
    from_date: str | None = None,
    force: bool = False,
) -> list[LoadResult]:
    current_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
    return [
        load_incremental(
            source_name=source_name,
            run_id=current_run_id,
            landing_path=landing_path,
            lakehouse_path=lakehouse_path,
            control_path=control_path,
            from_date=from_date,
            force=force,
        )
        for source_name in SOURCE_NAMES
    ]


def _parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser(description="Load generated source files into Bronze raw tables.")
    parser.add_argument("--landing-path", default=str(config.landing_path))
    parser.add_argument("--lakehouse-path", default=str(config.lakehouse_path))
    parser.add_argument("--control-path", default=str(config.control_path))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--from-date", default=None, help="Backfill watermark, documented in run metadata.")
    parser.add_argument("--force", action="store_true", help="Force reload files already present in ingestion state.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = load_all_sources(
        landing_path=args.landing_path,
        lakehouse_path=args.lakehouse_path,
        control_path=args.control_path,
        run_id=args.run_id,
        from_date=args.from_date,
        force=args.force,
    )
    for result in results:
        print(
            f"{result.source_name}: loaded_rows={result.loaded_rows} "
            f"loaded_files={result.loaded_files} skipped_files={result.skipped_files}"
        )


if __name__ == "__main__":
    main()

