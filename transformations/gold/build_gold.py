"""Build Gold star-schema facts and dimensions."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from lakehouse.io import read_table, to_float, to_int, write_table
from monitoring.pipeline_run_logger import log_event
from transformations.common import iso_date_from_ts, parse_date, readiness_band, rolling_average_by_player, safe_divide


def build_gold(lakehouse_path: str | Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    counts["dim_player"] = _build_dim_player(lakehouse_path)
    counts["dim_team"] = _copy_table(lakehouse_path, "teams", "dim_team")
    counts["dim_fixture"] = _copy_table(lakehouse_path, "fixtures", "dim_fixture")
    counts["fact_player_workload_daily"] = _build_workload_fact(lakehouse_path)
    counts["fact_player_readiness_daily"] = _build_readiness_fact(lakehouse_path)
    counts["fact_matchday_revenue"] = _build_matchday_revenue(lakehouse_path)
    counts["fact_fan_engagement_daily"] = _copy_table(lakehouse_path, "fan_engagement_daily", "fact_fan_engagement_daily")
    counts["dim_fan_segment"] = _build_fan_segments(lakehouse_path)
    counts["fact_campaign_performance"] = _build_campaign_performance(lakehouse_path)
    counts["fact_product_adoption"] = _build_product_adoption(lakehouse_path)
    counts["dim_date"] = _build_dim_date(lakehouse_path)
    log_event("gold_transformations", "success", {"table_counts": counts})
    return counts


def _copy_table(lakehouse_path: str | Path, silver_table: str, gold_table: str) -> int:
    rows = read_table(lakehouse_path, "silver", silver_table)
    write_table(lakehouse_path, "gold", gold_table, rows)
    return len(rows)


def _build_dim_player(lakehouse_path: str | Path) -> int:
    rows = []
    for row in read_table(lakehouse_path, "silver", "players"):
        effective_to = row.get("effective_to") or "9999-12-31"
        rows.append(
            {
                "player_key": f"{row.get('player_id')}|{row.get('effective_from')}",
                "player_id": row.get("player_id", ""),
                "team_id": row.get("team_id", ""),
                "name": row.get("name", ""),
                "position": row.get("position", ""),
                "birth_date": row.get("birth_date", ""),
                "nationality": row.get("nationality", ""),
                "dominant_foot": row.get("dominant_foot", ""),
                "squad_status": row.get("squad_status", ""),
                "effective_from": row.get("effective_from", ""),
                "effective_to": effective_to,
                "is_current": "true" if effective_to == "9999-12-31" else "false",
            }
        )
    write_table(lakehouse_path, "gold", "dim_player", rows)
    return len(rows)


def _build_workload_fact(lakehouse_path: str | Path) -> int:
    rows = read_table(lakehouse_path, "silver", "player_workload_daily")
    seven_day = rolling_average_by_player(rows, "total_distance_m", 7)
    twenty_eight_day = rolling_average_by_player(rows, "total_distance_m", 28)
    output = []
    for row in rows:
        key = (str(row.get("player_id", "")), str(row.get("metric_date", "")))
        acute = seven_day.get(key, to_float(row.get("total_distance_m")))
        chronic = twenty_eight_day.get(key, acute)
        output.append(
            {
                **row,
                "acute_load_7d": acute,
                "chronic_load_28d": chronic,
                "acute_chronic_load_ratio": round(acute / chronic, 3) if chronic else 0.0,
            }
        )
    write_table(lakehouse_path, "gold", "fact_player_workload_daily", output)
    return len(output)


def _build_readiness_fact(lakehouse_path: str | Path) -> int:
    workloads = read_table(lakehouse_path, "gold", "fact_player_workload_daily")
    wellness = {
        (row.get("player_id", ""), row.get("metric_date", "")): row
        for row in read_table(lakehouse_path, "silver", "wellness_daily")
    }
    availability = {
        (row.get("player_id", ""), row.get("metric_date", "")): row
        for row in read_table(lakehouse_path, "silver", "player_availability_daily")
    }
    output = []
    for row in workloads:
        key = (row.get("player_id", ""), row.get("metric_date", ""))
        wellness_row = wellness.get(key, {})
        availability_row = availability.get(key, {"availability_status": "available"})
        fatigue = to_float(wellness_row.get("fatigue"), 3.0)
        soreness = to_float(wellness_row.get("soreness"), 3.0)
        stress = to_float(wellness_row.get("stress"), 3.0)
        acwr = to_float(row.get("acute_chronic_load_ratio"), 1.0)
        status = str(availability_row.get("availability_status", "available"))
        readiness_score = 100.0
        readiness_score -= min(35.0, abs(acwr - 1.0) * 45.0)
        readiness_score -= min(25.0, fatigue * 4.0 + soreness * 2.0 + stress * 1.5)
        if status == "managed_load":
            readiness_score -= 10.0
        elif status == "doubtful":
            readiness_score -= 25.0
        elif status == "unavailable":
            readiness_score -= 50.0
        score = round(max(0.0, min(100.0, readiness_score)), 2)
        output.append(
            {
                "player_id": row.get("player_id", ""),
                "metric_date": row.get("metric_date", ""),
                "readiness_score": score,
                "readiness_band": readiness_band(score),
                "availability_status": status,
                "acute_chronic_load_ratio": row.get("acute_chronic_load_ratio", ""),
                "fatigue": fatigue,
                "soreness": soreness,
                "stress": stress,
                "recommended_action": _recommendation(score, status),
            }
        )
    write_table(lakehouse_path, "gold", "fact_player_readiness_daily", output)
    return len(output)


def _recommendation(score: float, status: str) -> str:
    if status == "unavailable":
        return "medical_review"
    if score < 50:
        return "reduce_load_and_review"
    if score < 65:
        return "managed_training"
    if score < 80:
        return "monitor"
    return "normal_training"


def _build_matchday_revenue(lakehouse_path: str | Path) -> int:
    fixtures = read_table(lakehouse_path, "silver", "fixtures")
    fixture_by_date = {iso_date_from_ts(row.get("kickoff_ts")): row for row in fixtures if row.get("venue") == "home"}
    rows: dict[tuple[str, str, str], dict[str, object]] = {}
    for ticket in read_table(lakehouse_path, "silver", "ticket_sales"):
        key = (str(ticket.get("fixture_id", "")), str(ticket.get("channel", "")), "ticket")
        rows.setdefault(
            key,
            {
                "fixture_id": key[0],
                "channel": key[1],
                "revenue_type": key[2],
                "net_revenue": 0.0,
                "order_count": 0,
                "unit_count": 0,
            },
        )
        rows[key]["net_revenue"] = to_float(rows[key]["net_revenue"]) + to_float(ticket.get("price_paid"))
        rows[key]["order_count"] = to_int(rows[key]["order_count"]) + 1
        rows[key]["unit_count"] = to_int(rows[key]["unit_count"]) + to_int(ticket.get("quantity"))

    for merch in read_table(lakehouse_path, "silver", "merchandise_orders"):
        fixture = fixture_by_date.get(iso_date_from_ts(merch.get("order_ts")))
        if not fixture:
            continue
        key = (str(fixture.get("fixture_id", "")), str(merch.get("channel", "")), "merchandise")
        rows.setdefault(
            key,
            {
                "fixture_id": key[0],
                "channel": key[1],
                "revenue_type": key[2],
                "net_revenue": 0.0,
                "order_count": 0,
                "unit_count": 0,
            },
        )
        rows[key]["net_revenue"] = to_float(rows[key]["net_revenue"]) + to_float(merch.get("net_revenue"))
        rows[key]["order_count"] = to_int(rows[key]["order_count"]) + 1
        rows[key]["unit_count"] = to_int(rows[key]["unit_count"]) + to_int(merch.get("quantity"))

    output = []
    for row in rows.values():
        row["net_revenue"] = round(to_float(row["net_revenue"]), 2)
        row["average_order_value"] = round(to_float(row["net_revenue"]) / max(to_int(row["order_count"]), 1), 2)
        output.append(row)
    write_table(lakehouse_path, "gold", "fact_matchday_revenue", output)
    return len(output)


def _build_fan_segments(lakehouse_path: str | Path) -> int:
    fan_metrics: dict[str, dict[str, float]] = defaultdict(lambda: {"ticket_revenue": 0.0, "ticket_units": 0.0, "merch_revenue": 0.0, "engagements": 0.0})
    for row in read_table(lakehouse_path, "silver", "ticket_sales"):
        fan_metrics[str(row.get("fan_id", ""))]["ticket_revenue"] += to_float(row.get("price_paid"))
        fan_metrics[str(row.get("fan_id", ""))]["ticket_units"] += to_float(row.get("quantity"))
    for row in read_table(lakehouse_path, "silver", "merchandise_orders"):
        fan_metrics[str(row.get("fan_id", ""))]["merch_revenue"] += to_float(row.get("net_revenue"))
    for row in read_table(lakehouse_path, "silver", "fan_engagement_events"):
        fan_metrics[str(row.get("fan_id", ""))]["engagements"] += 1

    rows = []
    for fan_id, metrics in fan_metrics.items():
        total_revenue = metrics["ticket_revenue"] + metrics["merch_revenue"]
        if total_revenue >= 500:
            segment = "high_value"
        elif metrics["ticket_units"] >= 6:
            segment = "frequent_matchgoer"
        elif metrics["engagements"] >= 8:
            segment = "digitally_engaged"
        elif total_revenue == 0 and metrics["engagements"] <= 1:
            segment = "lapsed_or_low_touch"
        else:
            segment = "general_supporter"
        rows.append(
            {
                "fan_id": fan_id,
                "fan_segment": segment,
                "ticket_revenue": round(metrics["ticket_revenue"], 2),
                "merch_revenue": round(metrics["merch_revenue"], 2),
                "engagement_count": int(metrics["engagements"]),
                "ticket_units": int(metrics["ticket_units"]),
            }
        )
    write_table(lakehouse_path, "gold", "dim_fan_segment", rows)
    return len(rows)


def _build_campaign_performance(lakehouse_path: str | Path) -> int:
    campaigns = {row["campaign_id"]: row for row in read_table(lakehouse_path, "silver", "marketing_campaigns")}
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for event in read_table(lakehouse_path, "silver", "fan_engagement_events"):
        campaign_id = str(event.get("campaign_id", ""))
        if not campaign_id or campaign_id not in campaigns:
            continue
        metric_date = iso_date_from_ts(event.get("event_ts"))
        key = (campaign_id, metric_date)
        grouped.setdefault(
            key,
            {
                "campaign_id": campaign_id,
                "metric_date": metric_date,
                "channel": campaigns[campaign_id].get("channel", ""),
                "target_segment": campaigns[campaign_id].get("target_segment", ""),
                "engagement_count": 0,
                "click_count": 0,
                "estimated_spend": 0.0,
            },
        )
        grouped[key]["engagement_count"] = to_int(grouped[key]["engagement_count"]) + 1
        if event.get("event_type") == "click":
            grouped[key]["click_count"] = to_int(grouped[key]["click_count"]) + 1

    for key, row in grouped.items():
        campaign = campaigns[key[0]]
        start = parse_date(campaign.get("start_date"))
        end = parse_date(campaign.get("end_date"))
        campaign_days = max(((end - start).days + 1) if start and end else 1, 1)
        row["estimated_spend"] = round(to_float(campaign.get("spend")) / campaign_days, 2)
        row["click_through_rate"] = safe_divide(to_float(row["click_count"]), to_float(row["engagement_count"]))
        row["cost_per_engagement"] = round(to_float(row["estimated_spend"]) / max(to_int(row["engagement_count"]), 1), 2)

    output = list(grouped.values())
    write_table(lakehouse_path, "gold", "fact_campaign_performance", output)
    return len(output)


def _build_product_adoption(lakehouse_path: str | Path) -> int:
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for event in read_table(lakehouse_path, "silver", "product_adoption_events"):
        metric_date = iso_date_from_ts(event.get("event_ts"))
        key = (str(event.get("persona", "")), str(event.get("product_area", "")), metric_date)
        grouped.setdefault(
            key,
            {
                "persona": key[0],
                "product_area": key[1],
                "metric_date": key[2],
                "event_count": 0,
                "active_users": set(),
                "sessions": set(),
                "copilot_queries": 0,
            },
        )
        grouped[key]["event_count"] = to_int(grouped[key]["event_count"]) + 1
        grouped[key]["active_users"].add(str(event.get("user_id", "")))  # type: ignore[attr-defined]
        grouped[key]["sessions"].add(str(event.get("session_id", "")))  # type: ignore[attr-defined]
        if event.get("action") == "copilot_query":
            grouped[key]["copilot_queries"] = to_int(grouped[key]["copilot_queries"]) + 1

    workflow_minutes: dict[str, float] = defaultdict(float)
    for workflow in read_table(lakehouse_path, "silver", "staff_workflow_events"):
        workflow_minutes[iso_date_from_ts(workflow.get("event_ts"))] += to_float(workflow.get("minutes_saved_estimate"))

    output = []
    for row in grouped.values():
        metric_date = str(row["metric_date"])
        output.append(
            {
                "persona": row["persona"],
                "product_area": row["product_area"],
                "metric_date": metric_date,
                "event_count": row["event_count"],
                "active_users": len(row["active_users"]),  # type: ignore[arg-type]
                "session_count": len(row["sessions"]),  # type: ignore[arg-type]
                "copilot_queries": row["copilot_queries"],
                "estimated_minutes_saved": round(workflow_minutes.get(metric_date, 0.0), 2),
            }
        )
    write_table(lakehouse_path, "gold", "fact_product_adoption", output)
    return len(output)


def _build_dim_date(lakehouse_path: str | Path) -> int:
    observed_dates: set[date] = set()
    for layer, table, column in (
        ("gold", "fact_player_workload_daily", "metric_date"),
        ("gold", "fact_player_readiness_daily", "metric_date"),
        ("gold", "fact_fan_engagement_daily", "metric_date"),
        ("gold", "fact_campaign_performance", "metric_date"),
        ("gold", "fact_product_adoption", "metric_date"),
        ("silver", "fixtures", "kickoff_ts"),
    ):
        for row in read_table(lakehouse_path, layer, table):
            parsed = parse_date(row.get(column))
            if parsed:
                observed_dates.add(parsed)
    if not observed_dates:
        write_table(lakehouse_path, "gold", "dim_date", [])
        return 0
    start = min(observed_dates)
    end = max(observed_dates)
    rows = []
    current = start
    while current <= end:
        rows.append(
            {
                "date_key": current.strftime("%Y%m%d"),
                "date": current.isoformat(),
                "year": current.year,
                "month": current.month,
                "day": current.day,
                "week": current.isocalendar().week,
                "day_of_week": current.strftime("%A"),
                "is_weekend": str(current.weekday() >= 5).lower(),
            }
        )
        current += timedelta(days=1)
    write_table(lakehouse_path, "gold", "dim_date", rows)
    return len(rows)

