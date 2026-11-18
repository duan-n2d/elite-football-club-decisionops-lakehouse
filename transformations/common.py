"""Shared transformation helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import date, timedelta
from typing import Any

from lakehouse.io import Row, to_float


def dedupe_by_key(rows: Iterable[Row], key: str) -> list[Row]:
    seen: dict[str, Row] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if value and value not in seen:
            seen[value] = row
    return list(seen.values())


def quarantine(row: Row, table_name: str, rule_id: str, reason: str) -> Row:
    return {
        "table_name": table_name,
        "rule_id": rule_id,
        "reason": reason,
        "source_file": row.get("_source_file", ""),
        "ingestion_run_id": row.get("_ingestion_run_id", ""),
        "record_hash": row.get("_record_hash", ""),
        "source_payload": row.get("_source_payload", ""),
    }


def split_valid_invalid(
    rows: Iterable[Row],
    table_name: str,
    validator: Callable[[Row], tuple[bool, str, str]],
) -> tuple[list[Row], list[Row]]:
    valid: list[Row] = []
    invalid: list[Row] = []
    for row in rows:
        is_valid, rule_id, reason = validator(row)
        if is_valid:
            valid.append(row)
        else:
            invalid.append(quarantine(row, table_name, rule_id, reason))
    return valid, invalid


def group_sum(rows: Iterable[Row], keys: tuple[str, ...], measures: tuple[str, ...]) -> list[Row]:
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        group_key = tuple(str(row.get(key, "")) for key in keys)
        if group_key not in grouped:
            grouped[group_key] = {key: row.get(key, "") for key in keys}
            for measure in measures:
                grouped[group_key][measure] = 0.0
            grouped[group_key]["record_count"] = 0
        for measure in measures:
            grouped[group_key][measure] += to_float(row.get(measure), 0.0)
        grouped[group_key]["record_count"] += 1
    return list(grouped.values())


def distinct_count(values: Iterable[str]) -> int:
    return len({value for value in values if value})


def parse_date(value: Any) -> date | None:
    text = str(value or "")
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def rolling_average_by_player(rows: list[Row], measure: str, window_days: int) -> dict[tuple[str, str], float]:
    by_player: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for row in rows:
        metric_date = parse_date(row.get("metric_date"))
        if metric_date is not None:
            by_player[str(row.get("player_id", ""))].append((metric_date, to_float(row.get(measure), 0.0)))

    result: dict[tuple[str, str], float] = {}
    for player_id, values in by_player.items():
        ordered = sorted(values, key=lambda item: item[0])
        for metric_date, _ in ordered:
            start_date = metric_date - timedelta(days=window_days - 1)
            in_window = [value for current_date, value in ordered if start_date <= current_date <= metric_date]
            result[(player_id, metric_date.isoformat())] = round(sum(in_window) / max(len(in_window), 1), 2)
    return result


def readiness_band(score: float) -> str:
    if score >= 80:
        return "ready"
    if score >= 65:
        return "monitor"
    if score >= 50:
        return "managed"
    return "high_risk"


def iso_date_from_ts(value: Any) -> str:
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else ""


def safe_divide(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0
