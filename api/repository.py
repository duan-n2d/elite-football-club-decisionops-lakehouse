"""Read-model helpers for API and dashboard consumers."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from lakehouse.config import load_config
from lakehouse.io import Row, read_table, to_float, to_int


def _lakehouse_path() -> Path:
    return load_config().lakehouse_path


def player_readiness(limit: int = 25) -> list[Row]:
    lakehouse_path = _lakehouse_path()
    players = {row["player_id"]: row for row in read_table(lakehouse_path, "gold", "dim_player")}
    rows = read_table(lakehouse_path, "gold", "fact_player_readiness_daily")
    latest_date = max((row.get("metric_date", "") for row in rows), default="")
    latest_rows = [row for row in rows if row.get("metric_date") == latest_date]
    latest_rows.sort(key=lambda row: to_float(row.get("readiness_score"), 999))
    output = []
    for row in latest_rows[:limit]:
        player = players.get(str(row.get("player_id", "")), {})
        output.append(
            {
                **row,
                "player_name": player.get("name", ""),
                "position": player.get("position", ""),
                "team_id": player.get("team_id", ""),
            }
        )
    return output


def readiness_for_player(player_id: str) -> list[Row]:
    rows = [
        row
        for row in read_table(_lakehouse_path(), "gold", "fact_player_readiness_daily")
        if row.get("player_id") == player_id
    ]
    rows.sort(key=lambda row: str(row.get("metric_date", "")))
    return rows


def matchday_revenue() -> list[Row]:
    lakehouse_path = _lakehouse_path()
    fixtures = {row["fixture_id"]: row for row in read_table(lakehouse_path, "gold", "dim_fixture")}
    rows = read_table(lakehouse_path, "gold", "fact_matchday_revenue")
    output = []
    for row in rows:
        fixture = fixtures.get(str(row.get("fixture_id", "")), {})
        output.append(
            {
                **row,
                "opponent": fixture.get("opponent", ""),
                "competition": fixture.get("competition", ""),
                "kickoff_ts": fixture.get("kickoff_ts", ""),
                "venue": fixture.get("venue", ""),
            }
        )
    output.sort(key=lambda row: (str(row.get("kickoff_ts", "")), str(row.get("channel", ""))))
    return output


def fan_segments() -> list[Row]:
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {"fan_segment": "", "fan_count": 0, "ticket_revenue": 0.0, "merch_revenue": 0.0, "engagement_count": 0}
    )
    for row in read_table(_lakehouse_path(), "gold", "dim_fan_segment"):
        segment = str(row.get("fan_segment", "unknown"))
        grouped[segment]["fan_segment"] = segment
        grouped[segment]["fan_count"] = to_int(grouped[segment]["fan_count"]) + 1
        grouped[segment]["ticket_revenue"] = to_float(grouped[segment]["ticket_revenue"]) + to_float(row.get("ticket_revenue"))
        grouped[segment]["merch_revenue"] = to_float(grouped[segment]["merch_revenue"]) + to_float(row.get("merch_revenue"))
        grouped[segment]["engagement_count"] = to_int(grouped[segment]["engagement_count"]) + to_int(row.get("engagement_count"))
    output = []
    for row in grouped.values():
        row["ticket_revenue"] = round(to_float(row["ticket_revenue"]), 2)
        row["merch_revenue"] = round(to_float(row["merch_revenue"]), 2)
        output.append(row)
    output.sort(key=lambda row: to_int(row.get("fan_count")), reverse=True)
    return output


def campaign_performance() -> list[Row]:
    rows = read_table(_lakehouse_path(), "gold", "fact_campaign_performance")
    rows.sort(key=lambda row: (str(row.get("campaign_id", "")), str(row.get("metric_date", ""))))
    return rows


def adoption_metrics() -> list[Row]:
    rows = read_table(_lakehouse_path(), "gold", "fact_product_adoption")
    rows.sort(key=lambda row: (str(row.get("metric_date", "")), str(row.get("persona", ""))))
    return rows


def quality_status() -> dict[str, object]:
    lakehouse_path = _lakehouse_path()
    results = read_table(lakehouse_path, "quality", "quality_results")
    freshness = read_table(lakehouse_path, "monitoring", "data_freshness")
    failed = [row for row in results if row.get("status") == "failed"]
    passed = [row for row in results if row.get("status") == "passed"]
    return {
        "quality_score_pct": round(100 * len(passed) / max(len(results), 1), 2),
        "failed_checks": len(failed),
        "checks": results,
        "freshness": freshness,
    }

