"""Small local table IO layer.

The production target is Delta on Azure Databricks. For portfolio demos and CI,
this module writes deterministic CSV tables under `lakehouse_local/<layer>/`.
Keeping the IO boundary narrow makes it straightforward to replace these
functions with Spark/Delta writes in Databricks jobs.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any


Row = dict[str, Any]


def table_path(lakehouse_path: str | Path, layer: str, table_name: str) -> Path:
    return Path(lakehouse_path) / layer / f"{table_name}.csv"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: str | Path) -> list[Row]:
    source = Path(path)
    if not source.exists():
        return []
    with source.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: str | Path, rows: Iterable[Row], columns: Sequence[str] | None = None) -> int:
    target = Path(path)
    ensure_parent(target)
    materialized = list(rows)
    if columns is None:
        columns = infer_columns(materialized)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: _stringify(row.get(column, "")) for column in columns})
    return len(materialized)


def append_csv(path: str | Path, rows: Iterable[Row], columns: Sequence[str] | None = None) -> int:
    target = Path(path)
    existing = read_csv(target)
    materialized = existing + list(rows)
    return write_csv(target, materialized, columns=columns)


def read_table(lakehouse_path: str | Path, layer: str, table_name: str) -> list[Row]:
    return read_csv(table_path(lakehouse_path, layer, table_name))


def write_table(
    lakehouse_path: str | Path,
    layer: str,
    table_name: str,
    rows: Iterable[Row],
    columns: Sequence[str] | None = None,
) -> int:
    return write_csv(table_path(lakehouse_path, layer, table_name), rows, columns=columns)


def append_table(
    lakehouse_path: str | Path,
    layer: str,
    table_name: str,
    rows: Iterable[Row],
    columns: Sequence[str] | None = None,
) -> int:
    return append_csv(table_path(lakehouse_path, layer, table_name), rows, columns=columns)


def infer_columns(rows: Sequence[Row]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def record_hash(row: Row) -> str:
    payload = json.dumps(row, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def load_json(path: str | Path, default: Any) -> Any:
    source = Path(path)
    if not source.exists():
        return default
    with source.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    ensure_parent(target)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def append_jsonl(path: str | Path, payload: Row) -> None:
    target = Path(path)
    ensure_parent(target)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value == "" or value is None:
            return default
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value == "" or value is None:
            return default
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value)

