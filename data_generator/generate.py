"""Generate deterministic, legally safe football club datasets.

The generator intentionally emits a small number of bad records so that the
pipeline can demonstrate data quality checks, quarantine, and stakeholder-safe
metric handling.
"""

from __future__ import annotations

import argparse
import csv
import random
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from data_generator.contracts import DATASET_CONTRACTS


FIRST_NAMES = [
    "Alex",
    "Sam",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Jamie",
    "Avery",
    "Cameron",
    "Drew",
    "Kai",
]
LAST_NAMES = [
    "Bennett",
    "Rossi",
    "Silva",
    "Okafor",
    "Nakamura",
    "Dubois",
    "Santos",
    "Khan",
    "Muller",
    "Garcia",
    "Anders",
    "Ndlovu",
]
POSITIONS = ["GK", "CB", "FB", "DM", "CM", "AM", "WG", "ST"]
NATIONALITIES = ["England", "Spain", "France", "Brazil", "Japan", "Nigeria", "Germany", "USA"]
OPPONENTS = [
    "Northbridge Athletic",
    "Capital City FC",
    "Riverside Albion",
    "Harbour United",
    "Eastport Rovers",
    "Mountain City SC",
    "Lakeside Town",
    "Metro Wanderers",
]
CAMPAIGN_NAMES = [
    "Season Ticket Renewal",
    "Derby Matchday Push",
    "New Kit Launch",
    "Family Stand Offer",
    "International Fan Week",
    "Membership Upgrade",
    "Cup Night Bundle",
    "Legends Content Series",
]


@dataclass(frozen=True)
class GeneratedData:
    output_dir: Path
    batch_id: str
    row_counts: dict[str, int]


def _iso_date(value: date) -> str:
    return value.isoformat()


def _iso_ts(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def _daterange(start: date, days: int) -> Iterable[date]:
    for offset in range(days):
        yield start + timedelta(days=offset)


def _write_source(output_dir: Path, source_name: str, batch_id: str, rows: list[dict[str, object]]) -> int:
    source_dir = output_dir / source_name
    source_dir.mkdir(parents=True, exist_ok=True)
    path = source_dir / f"{source_name}_{batch_id}.csv"
    columns = DATASET_CONTRACTS[source_name].columns
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return len(rows)


def _name(index: int) -> str:
    first = FIRST_NAMES[index % len(FIRST_NAMES)]
    last = LAST_NAMES[(index * 3) % len(LAST_NAMES)]
    return f"{first} {last}"


def _fan_id(index: int) -> str:
    return f"fan_{index:06d}"


def _build_teams() -> list[dict[str, object]]:
    return [
        {"team_id": "team_men_1", "team_name": "Elite FC Men", "age_group": "Senior", "league": "Premier Division"},
        {"team_id": "team_women_1", "team_name": "Elite FC Women", "age_group": "Senior", "league": "National League"},
        {"team_id": "team_u21", "team_name": "Elite FC U21", "age_group": "U21", "league": "Development League"},
    ]


def _build_players(rng: random.Random, squad_size: int, start: date) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    team_choices = ["team_men_1", "team_women_1", "team_u21"]
    for index in range(squad_size):
        birth_year = rng.randint(1994, 2008)
        player = {
            "player_id": f"player_{index + 1:04d}",
            "team_id": team_choices[index % len(team_choices)],
            "name": _name(index),
            "position": POSITIONS[index % len(POSITIONS)],
            "birth_date": f"{birth_year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            "nationality": rng.choice(NATIONALITIES),
            "dominant_foot": rng.choice(["left", "right", "both"]),
            "squad_status": rng.choice(["first_team", "rotation", "academy", "loan_watch"]),
            "effective_from": _iso_date(start - timedelta(days=365)),
            "effective_to": "",
        }
        rows.append(player)

    rows.append(rows[0].copy())  # duplicate for dedupe demonstration
    bad = rows[1].copy()
    bad["player_id"] = "player_bad_position"
    bad["position"] = "WIZARD"
    rows.append(bad)
    return rows


def _build_fixtures(rng: random.Random, start: date, days: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    fixture_number = 1
    for match_day in range(5, days, 7):
        fixture_date = start + timedelta(days=match_day)
        for team_id in ("team_men_1", "team_women_1"):
            kickoff = datetime.combine(fixture_date, time(hour=rng.choice([12, 15, 17, 20]), minute=0))
            rows.append(
                {
                    "fixture_id": f"fixture_{fixture_number:04d}",
                    "team_id": team_id,
                    "opponent": rng.choice(OPPONENTS),
                    "competition": rng.choice(["League", "Cup", "Continental"]),
                    "kickoff_ts": _iso_ts(kickoff),
                    "venue": rng.choice(["home", "away"]),
                    "importance_score": rng.randint(1, 5),
                }
            )
            fixture_number += 1

    if rows:
        rows.append(rows[0].copy())
        rows[-1]["importance_score"] = 9
    return rows


def _build_training_sessions(rng: random.Random, start: date, days: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    session_number = 1
    for current in _daterange(start, days):
        if current.weekday() == 6:
            continue
        for team_id in ("team_men_1", "team_women_1", "team_u21"):
            session_type = rng.choice(["recovery", "tactical", "strength", "conditioning", "match_prep"])
            duration = rng.randint(45, 110)
            rows.append(
                {
                    "session_id": f"session_{session_number:05d}",
                    "team_id": team_id,
                    "session_date": _iso_date(current),
                    "session_type": session_type,
                    "planned_load": rng.randint(30, 95),
                    "duration_min": duration,
                }
            )
            session_number += 1
    if rows:
        bad = rows[-1].copy()
        bad["session_id"] = "session_bad_duration"
        bad["duration_min"] = -15
        rows.append(bad)
    return rows


def _build_gps(
    rng: random.Random, players: list[dict[str, object]], sessions: list[dict[str, object]]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    player_team = {row["player_id"]: row["team_id"] for row in players if str(row["player_id"]).startswith("player_")}
    event_number = 1
    for session in sessions:
        if str(session["session_id"]).startswith("session_bad"):
            continue
        session_team = session["team_id"]
        for player in players:
            player_id = str(player["player_id"])
            if player_id not in player_team or player_team[player_id] != session_team or rng.random() < 0.08:
                continue
            total_distance = rng.randint(2200, 10500)
            high_speed = int(total_distance * rng.uniform(0.05, 0.22))
            rows.append(
                {
                    "event_id": f"gps_{event_number:07d}",
                    "player_id": player_id,
                    "session_id": session["session_id"],
                    "total_distance_m": total_distance,
                    "high_speed_distance_m": high_speed,
                    "sprint_count": rng.randint(0, 35),
                    "accel_count": rng.randint(5, 80),
                    "decel_count": rng.randint(5, 80),
                    "max_speed_kmh": round(rng.uniform(21.0, 36.5), 2),
                }
            )
            event_number += 1
    if rows:
        rows.append(rows[0].copy())
        bad = rows[1].copy()
        bad["event_id"] = "gps_bad_speed"
        bad["max_speed_kmh"] = 72.0
        rows.append(bad)
        bad_missing = rows[2].copy()
        bad_missing["event_id"] = "gps_missing_player"
        bad_missing["player_id"] = ""
        rows.append(bad_missing)
    return rows


def _build_wellness(
    rng: random.Random, players: list[dict[str, object]], start: date, days: int
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    survey_number = 1
    player_ids = [str(row["player_id"]) for row in players if str(row["player_id"]).startswith("player_0")]
    for current in _daterange(start, days):
        if current.weekday() == 6:
            continue
        for player_id in player_ids:
            if rng.random() < 0.1:
                continue
            rows.append(
                {
                    "survey_id": f"wellness_{survey_number:07d}",
                    "player_id": player_id,
                    "survey_date": _iso_date(current),
                    "sleep_quality": rng.randint(1, 5),
                    "soreness": rng.randint(1, 5),
                    "fatigue": rng.randint(1, 5),
                    "mood": rng.randint(1, 5),
                    "stress": rng.randint(1, 5),
                }
            )
            survey_number += 1
    if rows:
        bad = rows[0].copy()
        bad["survey_id"] = "wellness_bad_range"
        bad["fatigue"] = 9
        rows.append(bad)
    return rows


def _build_availability(
    rng: random.Random, players: list[dict[str, object]], start: date, days: int
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    statuses = ["available", "managed_load", "doubtful", "unavailable"]
    injury_types = ["", "hamstring", "ankle", "knee", "illness", "fatigue"]
    record_number = 1
    player_ids = [str(row["player_id"]) for row in players if str(row["player_id"]).startswith("player_0")]
    for current in _daterange(start, days):
        for player_id in player_ids:
            status = rng.choices(statuses, weights=[0.78, 0.12, 0.06, 0.04], k=1)[0]
            injury_type = "" if status in {"available", "managed_load"} else rng.choice(injury_types[1:])
            return_date = "" if status != "unavailable" else _iso_date(current + timedelta(days=rng.randint(3, 21)))
            rows.append(
                {
                    "record_id": f"availability_{record_number:07d}",
                    "player_id": player_id,
                    "status_date": _iso_date(current),
                    "availability_status": status,
                    "injury_type": injury_type,
                    "expected_return_date": return_date,
                }
            )
            record_number += 1
    bad = rows[0].copy()
    bad["record_id"] = "availability_bad_status"
    bad["availability_status"] = "maybe"
    rows.append(bad)
    return rows


def _build_match_events(
    rng: random.Random, fixtures: list[dict[str, object]], players: list[dict[str, object]]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_team: dict[str, list[str]] = {}
    for player in players:
        player_id = str(player["player_id"])
        if player_id.startswith("player_0"):
            by_team.setdefault(str(player["team_id"]), []).append(player_id)
    event_number = 1
    for fixture in fixtures:
        fixture_id = str(fixture["fixture_id"])
        if fixture_id in {str(row["fixture_id"]) for row in rows}:
            continue
        fixture_players = by_team.get(str(fixture["team_id"]), [])
        kickoff = datetime.fromisoformat(str(fixture["kickoff_ts"]))
        for _ in range(90):
            player_id = rng.choice(fixture_players) if fixture_players else ""
            rows.append(
                {
                    "event_id": f"match_event_{event_number:08d}",
                    "fixture_id": fixture_id,
                    "team_id": fixture["team_id"],
                    "player_id": player_id,
                    "event_ts": _iso_ts(kickoff + timedelta(minutes=rng.randint(0, 94), seconds=rng.randint(0, 59))),
                    "event_type": rng.choice(["pass", "shot", "carry", "duel", "press", "recovery"]),
                    "x": round(rng.uniform(0, 100), 2),
                    "y": round(rng.uniform(0, 100), 2),
                    "outcome": rng.choice(["successful", "unsuccessful", "neutral"]),
                }
            )
            event_number += 1
    if rows:
        bad = rows[0].copy()
        bad["event_id"] = "match_event_bad_pitch"
        bad["x"] = 140
        rows.append(bad)
    return rows


def _build_campaigns(rng: random.Random, start: date) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, name in enumerate(CAMPAIGN_NAMES, start=1):
        campaign_start = start + timedelta(days=(index - 1) * 9)
        rows.append(
            {
                "campaign_id": f"campaign_{index:03d}",
                "name": name,
                "start_date": _iso_date(campaign_start),
                "end_date": _iso_date(campaign_start + timedelta(days=rng.randint(7, 21))),
                "target_segment": rng.choice(["season_ticket_holder", "family", "international", "high_value", "lapsed"]),
                "spend": rng.randint(2500, 45000),
                "channel": rng.choice(["email", "paid_social", "app_push", "web", "stadium"]),
            }
        )
    bad = rows[0].copy()
    bad["campaign_id"] = "campaign_bad_spend"
    bad["spend"] = -500
    rows.append(bad)
    return rows


def _build_ticket_sales(
    rng: random.Random, fixtures: list[dict[str, object]], fans: int
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    order_number = 1
    for fixture in fixtures:
        if fixture["venue"] != "home" or str(fixture["fixture_id"]).endswith("0001") and int(fixture["importance_score"]) > 5:
            continue
        kickoff = datetime.fromisoformat(str(fixture["kickoff_ts"]))
        orders = rng.randint(120, 360)
        for _ in range(orders):
            quantity = rng.choices([1, 2, 3, 4], weights=[0.4, 0.35, 0.15, 0.1], k=1)[0]
            price = round(rng.uniform(22, 120) * quantity, 2)
            rows.append(
                {
                    "order_id": f"ticket_{order_number:08d}",
                    "fixture_id": fixture["fixture_id"],
                    "fan_id": _fan_id(rng.randint(1, fans)),
                    "sale_ts": _iso_ts(kickoff - timedelta(days=rng.randint(1, 35), hours=rng.randint(0, 23))),
                    "stand": rng.choice(["North", "South", "East", "West", "Hospitality"]),
                    "price_paid": price,
                    "channel": rng.choice(["web", "app", "box_office", "partner"]),
                    "quantity": quantity,
                }
            )
            order_number += 1
    if rows:
        rows.append(rows[0].copy())
        bad = rows[1].copy()
        bad["order_id"] = "ticket_bad_negative"
        bad["price_paid"] = -35.0
        rows.append(bad)
    return rows


def _build_merchandise_orders(
    rng: random.Random, start: date, days: int, fans: int
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    skus = [
        ("HOME-KIT", "shirt"),
        ("AWAY-KIT", "shirt"),
        ("SCARF-RED", "accessory"),
        ("CAP-BLK", "accessory"),
        ("TRAIN-TOP", "training"),
    ]
    for index in range(max(300, fans // 2)):
        sku, category = rng.choice(skus)
        quantity = rng.choices([1, 2, 3], weights=[0.7, 0.25, 0.05], k=1)[0]
        order_ts = datetime.combine(start + timedelta(days=rng.randint(0, days - 1)), time(hour=rng.randint(8, 22)))
        rows.append(
            {
                "order_id": f"merch_{index + 1:08d}",
                "fan_id": _fan_id(rng.randint(1, fans)),
                "order_ts": _iso_ts(order_ts),
                "sku": sku,
                "category": category,
                "quantity": quantity,
                "net_revenue": round(rng.uniform(12, 95) * quantity, 2),
                "channel": rng.choice(["web", "app", "stadium_store", "partner"]),
            }
        )
    bad = rows[0].copy()
    bad["order_id"] = "merch_bad_revenue"
    bad["net_revenue"] = -12.99
    rows.append(bad)
    return rows


def _build_fan_events(
    rng: random.Random, campaigns: list[dict[str, object]], start: date, days: int, fans: int
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    campaign_ids = [str(row["campaign_id"]) for row in campaigns if not str(row["campaign_id"]).endswith("bad_spend")]
    event_types = ["email_open", "click", "app_open", "video_view", "survey_response", "membership_view"]
    for index in range(max(1500, fans * 2)):
        event_ts = datetime.combine(start + timedelta(days=rng.randint(0, days - 1)), time(hour=rng.randint(7, 23)))
        rows.append(
            {
                "event_id": f"fan_event_{index + 1:09d}",
                "fan_id": _fan_id(rng.randint(1, fans)),
                "event_ts": _iso_ts(event_ts),
                "channel": rng.choice(["email", "app", "web", "paid_social", "stadium"]),
                "event_type": rng.choice(event_types),
                "campaign_id": rng.choice(campaign_ids + [""]),
            }
        )
    bad = rows[0].copy()
    bad["event_id"] = "fan_event_bad_channel"
    bad["channel"] = "legacy_gateway"
    rows.append(bad)
    return rows


def _build_staff_workflows(rng: random.Random, start: date, days: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    workflows = ["squad_report", "matchday_pack", "campaign_brief", "revenue_snapshot", "data_quality_triage"]
    roles = ["football_ops", "commercial", "fan_engagement", "data_platform", "executive"]
    for index in range(420):
        event_ts = datetime.combine(start + timedelta(days=rng.randint(0, days - 1)), time(hour=rng.randint(6, 20)))
        rows.append(
            {
                "event_id": f"workflow_{index + 1:08d}",
                "staff_role": rng.choice(roles),
                "workflow_name": rng.choice(workflows),
                "event_ts": _iso_ts(event_ts),
                "status": rng.choice(["started", "completed", "automated", "failed"]),
                "minutes_saved_estimate": rng.choice([0, 5, 10, 15, 30, 45]),
            }
        )
    bad = rows[0].copy()
    bad["event_id"] = "workflow_bad_minutes"
    bad["minutes_saved_estimate"] = -10
    rows.append(bad)
    return rows


def _build_product_adoption(rng: random.Random, start: date, days: int) -> list[dict[str, object]]:
    personas = ["Head of Football Operations", "Commercial Director", "Fan Engagement Manager", "Data Platform Lead"]
    product_areas = ["Executive Overview", "Football Operations", "Matchday Revenue", "Fan Engagement", "Copilot"]
    actions = ["view", "filter", "export", "copilot_query", "alert_acknowledged"]
    rows: list[dict[str, object]] = []
    for index in range(900):
        event_ts = datetime.combine(start + timedelta(days=rng.randint(0, days - 1)), time(hour=rng.randint(7, 21)))
        session_id = f"session_adopt_{rng.randint(1, 220):05d}"
        rows.append(
            {
                "event_id": f"adoption_{index + 1:08d}",
                "user_id": f"user_{rng.randint(1, 45):04d}",
                "persona": rng.choice(personas),
                "product_area": rng.choice(product_areas),
                "event_ts": _iso_ts(event_ts),
                "action": rng.choice(actions),
                "session_id": session_id,
            }
        )
    bad = rows[0].copy()
    bad["event_id"] = "adoption_bad_persona"
    bad["persona"] = "Unknown"
    rows.append(bad)
    return rows


def generate_all(
    output_dir: str | Path = "data/landing",
    days: int = 60,
    fans: int = 1500,
    squad_size: int = 36,
    seed: int = 7,
    start_date: str = "2026-01-01",
) -> GeneratedData:
    rng = random.Random(seed)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    batch_id = f"{start_date.replace('-', '')}_{seed}"
    start = date.fromisoformat(start_date)

    teams = _build_teams()
    players = _build_players(rng, squad_size=squad_size, start=start)
    sessions = _build_training_sessions(rng, start=start, days=days)
    gps = _build_gps(rng, players, sessions)
    wellness = _build_wellness(rng, players, start=start, days=days)
    availability = _build_availability(rng, players, start=start, days=days)
    fixtures = _build_fixtures(rng, start=start, days=days)
    match_events = _build_match_events(rng, fixtures, players)
    campaigns = _build_campaigns(rng, start=start)
    ticket_sales = _build_ticket_sales(rng, fixtures, fans=fans)
    merchandise = _build_merchandise_orders(rng, start=start, days=days, fans=fans)
    fan_events = _build_fan_events(rng, campaigns, start=start, days=days, fans=fans)
    workflows = _build_staff_workflows(rng, start=start, days=days)
    adoption = _build_product_adoption(rng, start=start, days=days)

    sources = {
        "teams": teams,
        "players": players,
        "training_sessions": sessions,
        "gps_tracking_aggregates": gps,
        "wellness_surveys": wellness,
        "injuries_availability": availability,
        "fixtures": fixtures,
        "match_events": match_events,
        "marketing_campaigns": campaigns,
        "ticket_sales": ticket_sales,
        "merchandise_orders": merchandise,
        "fan_engagement_events": fan_events,
        "staff_workflow_events": workflows,
        "product_adoption_events": adoption,
    }
    row_counts = {
        source_name: _write_source(output, source_name, batch_id, rows)
        for source_name, rows in sources.items()
    }
    return GeneratedData(output_dir=output, batch_id=batch_id, row_counts=row_counts)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic club source data.")
    parser.add_argument("--output", default="data/landing", help="Landing folder for generated source files.")
    parser.add_argument("--days", type=int, default=60, help="Number of synthetic days to generate.")
    parser.add_argument("--fans", type=int, default=1500, help="Number of synthetic fan IDs.")
    parser.add_argument("--squad-size", type=int, default=36, help="Synthetic player count.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic data.")
    parser.add_argument("--start-date", default="2026-01-01", help="Start date in YYYY-MM-DD format.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    generated = generate_all(
        output_dir=args.output,
        days=args.days,
        fans=args.fans,
        squad_size=args.squad_size,
        seed=args.seed,
        start_date=args.start_date,
    )
    print(f"Generated batch {generated.batch_id} in {generated.output_dir}")
    for source_name, count in sorted(generated.row_counts.items()):
        print(f"{source_name}: {count} rows")


if __name__ == "__main__":
    main()
