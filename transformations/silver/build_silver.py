"""Build cleaned Silver tables and quarantine invalid source records."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from data_generator.contracts import DATASET_CONTRACTS
from lakehouse.io import read_table, to_float, to_int, write_table
from monitoring.pipeline_run_logger import log_event
from transformations.common import dedupe_by_key, iso_date_from_ts, split_valid_invalid


POSITIONS = {"GK", "CB", "FB", "DM", "CM", "AM", "WG", "ST"}
AVAILABILITY = {"available", "managed_load", "doubtful", "unavailable"}
FAN_CHANNELS = {"email", "app", "web", "paid_social", "stadium"}
SALES_CHANNELS = {"web", "app", "box_office", "partner", "stadium_store"}
WORKFLOW_STATUSES = {"started", "completed", "automated", "failed"}
PERSONAS = {
    "Head of Football Operations",
    "Commercial Director",
    "Fan Engagement Manager",
    "Data Platform Lead",
}


def _required(row: dict[str, str], *columns: str) -> bool:
    return all(str(row.get(column, "")).strip() for column in columns)


def _score_between(row: dict[str, str], *columns: str) -> bool:
    return all(1 <= to_int(row.get(column), -1) <= 5 for column in columns)


def _validators() -> dict[str, object]:
    return {
        "teams": lambda r: (
            _required(r, "team_id", "team_name"),
            "TEAM_REQUIRED",
            "team_id and team_name are required",
        ),
        "players": lambda r: (
            _required(r, "player_id", "team_id") and r.get("position") in POSITIONS,
            "PLAYER_VALIDATION",
            "player_id/team_id required and position must be supported",
        ),
        "training_sessions": lambda r: (
            _required(r, "session_id", "team_id", "session_date") and to_int(r.get("duration_min"), -1) > 0,
            "SESSION_VALIDATION",
            "session_id/team_id/date required and duration must be positive",
        ),
        "gps_tracking_aggregates": lambda r: (
            _required(r, "event_id", "player_id", "session_id")
            and 0 <= to_float(r.get("total_distance_m"), -1) <= 20000
            and 0 <= to_float(r.get("max_speed_kmh"), -1) <= 45,
            "GPS_RANGE",
            "GPS event requires IDs and physical values in expected ranges",
        ),
        "wellness_surveys": lambda r: (
            _required(r, "survey_id", "player_id", "survey_date")
            and _score_between(r, "sleep_quality", "soreness", "fatigue", "mood", "stress"),
            "WELLNESS_RANGE",
            "wellness scores must be between 1 and 5",
        ),
        "injuries_availability": lambda r: (
            _required(r, "record_id", "player_id", "status_date")
            and r.get("availability_status") in AVAILABILITY,
            "AVAILABILITY_STATUS",
            "availability status is unsupported",
        ),
        "fixtures": lambda r: (
            _required(r, "fixture_id", "team_id", "kickoff_ts")
            and 1 <= to_int(r.get("importance_score"), -1) <= 5,
            "FIXTURE_VALIDATION",
            "fixture IDs required and importance score must be 1-5",
        ),
        "match_events": lambda r: (
            _required(r, "event_id", "fixture_id", "player_id")
            and 0 <= to_float(r.get("x"), -1) <= 100
            and 0 <= to_float(r.get("y"), -1) <= 100,
            "MATCH_EVENT_RANGE",
            "match event requires IDs and pitch coordinates between 0 and 100",
        ),
        "ticket_sales": lambda r: (
            _required(r, "order_id", "fixture_id", "fan_id")
            and to_float(r.get("price_paid"), -1) >= 0
            and to_int(r.get("quantity"), 0) > 0
            and r.get("channel") in SALES_CHANNELS,
            "TICKET_VALIDATION",
            "ticket order must have IDs, non-negative price, positive quantity, valid channel",
        ),
        "merchandise_orders": lambda r: (
            _required(r, "order_id", "fan_id")
            and to_float(r.get("net_revenue"), -1) >= 0
            and to_int(r.get("quantity"), 0) > 0
            and r.get("channel") in SALES_CHANNELS,
            "MERCH_VALIDATION",
            "merchandise order must have fan, positive quantity, non-negative revenue, valid channel",
        ),
        "fan_engagement_events": lambda r: (
            _required(r, "event_id", "fan_id", "event_ts") and r.get("channel") in FAN_CHANNELS,
            "FAN_EVENT_CHANNEL",
            "fan engagement event requires IDs and valid channel",
        ),
        "marketing_campaigns": lambda r: (
            _required(r, "campaign_id", "name", "start_date", "end_date")
            and to_float(r.get("spend"), -1) >= 0,
            "CAMPAIGN_VALIDATION",
            "campaign requires dates and non-negative spend",
        ),
        "staff_workflow_events": lambda r: (
            _required(r, "event_id", "workflow_name", "event_ts")
            and r.get("status") in WORKFLOW_STATUSES
            and to_float(r.get("minutes_saved_estimate"), -1) >= 0,
            "WORKFLOW_VALIDATION",
            "workflow events require valid status and non-negative minutes saved",
        ),
        "product_adoption_events": lambda r: (
            _required(r, "event_id", "user_id", "session_id")
            and r.get("persona") in PERSONAS,
            "ADOPTION_PERSONA",
            "product adoption event requires user/session and known persona",
        ),
    }


def build_silver(lakehouse_path: str | Path) -> dict[str, int]:
    validators = _validators()
    quarantine_rows: list[dict[str, str]] = []
    counts: dict[str, int] = {}

    for source_name, contract in DATASET_CONTRACTS.items():
        bronze_rows = read_table(lakehouse_path, "bronze", f"raw_{source_name}")
        validator = validators[source_name]
        valid_rows, invalid_rows = split_valid_invalid(bronze_rows, source_name, validator)  # type: ignore[arg-type]
        deduped = dedupe_by_key(valid_rows, contract.primary_key)
        write_table(lakehouse_path, "silver", source_name, deduped)
        counts[source_name] = len(deduped)
        quarantine_rows.extend(invalid_rows)

    write_table(
        lakehouse_path,
        "silver",
        "quarantine_failed_records",
        quarantine_rows,
        columns=(
            "table_name",
            "rule_id",
            "reason",
            "source_file",
            "ingestion_run_id",
            "record_hash",
            "source_payload",
        ),
    )
    _build_operational_silver(lakehouse_path)
    log_event("silver_transformations", "success", {"table_counts": counts, "quarantine_rows": len(quarantine_rows)})
    return counts


def _build_operational_silver(lakehouse_path: str | Path) -> None:
    sessions = {row["session_id"]: row for row in read_table(lakehouse_path, "silver", "training_sessions")}
    gps_rows = read_table(lakehouse_path, "silver", "gps_tracking_aggregates")
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in gps_rows:
        session = sessions.get(str(row.get("session_id", "")))
        if not session:
            continue
        key = (str(row.get("player_id", "")), str(session.get("session_date", "")))
        grouped.setdefault(
            key,
            {
                "player_id": key[0],
                "metric_date": key[1],
                "total_distance_m": 0.0,
                "high_speed_distance_m": 0.0,
                "sprint_count": 0.0,
                "accel_count": 0.0,
                "decel_count": 0.0,
                "session_count": 0,
            },
        )
        grouped[key]["total_distance_m"] = to_float(grouped[key]["total_distance_m"]) + to_float(row.get("total_distance_m"))
        grouped[key]["high_speed_distance_m"] = to_float(grouped[key]["high_speed_distance_m"]) + to_float(
            row.get("high_speed_distance_m")
        )
        grouped[key]["sprint_count"] = to_float(grouped[key]["sprint_count"]) + to_float(row.get("sprint_count"))
        grouped[key]["accel_count"] = to_float(grouped[key]["accel_count"]) + to_float(row.get("accel_count"))
        grouped[key]["decel_count"] = to_float(grouped[key]["decel_count"]) + to_float(row.get("decel_count"))
        grouped[key]["session_count"] = to_int(grouped[key]["session_count"]) + 1
    write_table(lakehouse_path, "silver", "player_workload_daily", list(grouped.values()))

    wellness_grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in read_table(lakehouse_path, "silver", "wellness_surveys"):
        key = (str(row.get("player_id", "")), str(row.get("survey_date", "")))
        wellness_grouped.setdefault(
            key,
            {
                "player_id": key[0],
                "metric_date": key[1],
                "sleep_quality": 0.0,
                "soreness": 0.0,
                "fatigue": 0.0,
                "mood": 0.0,
                "stress": 0.0,
                "survey_count": 0,
            },
        )
        for measure in ("sleep_quality", "soreness", "fatigue", "mood", "stress"):
            wellness_grouped[key][measure] = to_float(wellness_grouped[key][measure]) + to_float(row.get(measure))
        wellness_grouped[key]["survey_count"] = to_int(wellness_grouped[key]["survey_count"]) + 1
    wellness_rows = []
    for row in wellness_grouped.values():
        survey_count = max(to_int(row.get("survey_count")), 1)
        wellness_rows.append(
            {
                **row,
                "sleep_quality": round(to_float(row.get("sleep_quality")) / survey_count, 2),
                "soreness": round(to_float(row.get("soreness")) / survey_count, 2),
                "fatigue": round(to_float(row.get("fatigue")) / survey_count, 2),
                "mood": round(to_float(row.get("mood")) / survey_count, 2),
                "stress": round(to_float(row.get("stress")) / survey_count, 2),
            }
        )
    write_table(lakehouse_path, "silver", "wellness_daily", wellness_rows)

    availability_rows = [
        {
            "player_id": row.get("player_id", ""),
            "metric_date": row.get("status_date", ""),
            "availability_status": row.get("availability_status", ""),
            "injury_type": row.get("injury_type", ""),
            "expected_return_date": row.get("expected_return_date", ""),
        }
        for row in read_table(lakehouse_path, "silver", "injuries_availability")
    ]
    write_table(lakehouse_path, "silver", "player_availability_daily", availability_rows)

    fan_daily: dict[tuple[str, str, str], dict[str, object]] = defaultdict(
        lambda: {"event_count": 0, "click_count": 0, "campaign_touch_count": 0}
    )
    for row in read_table(lakehouse_path, "silver", "fan_engagement_events"):
        key = (str(row.get("fan_id", "")), iso_date_from_ts(row.get("event_ts")), str(row.get("channel", "")))
        fan_daily[key].update({"fan_id": key[0], "metric_date": key[1], "channel": key[2]})
        fan_daily[key]["event_count"] = to_int(fan_daily[key]["event_count"]) + 1
        if row.get("event_type") == "click":
            fan_daily[key]["click_count"] = to_int(fan_daily[key]["click_count"]) + 1
        if row.get("campaign_id"):
            fan_daily[key]["campaign_touch_count"] = to_int(fan_daily[key]["campaign_touch_count"]) + 1
    write_table(lakehouse_path, "silver", "fan_engagement_daily", list(fan_daily.values()))

