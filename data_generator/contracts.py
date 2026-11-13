"""Dataset contracts for the synthetic club data sources."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetContract:
    name: str
    primary_key: str
    columns: tuple[str, ...]
    volume_assumption: str
    quality_issues: tuple[str, ...]
    relationships: tuple[str, ...]


DATASET_CONTRACTS: dict[str, DatasetContract] = {
    "players": DatasetContract(
        name="players",
        primary_key="player_id",
        columns=(
            "player_id",
            "team_id",
            "name",
            "position",
            "birth_date",
            "nationality",
            "dominant_foot",
            "squad_status",
            "effective_from",
            "effective_to",
        ),
        volume_assumption="30-80 active squad records locally; hundreds across academy and senior teams.",
        quality_issues=("duplicate player rows", "invalid position enum", "missing team_id"),
        relationships=("team_id -> teams.team_id",),
    ),
    "teams": DatasetContract(
        name="teams",
        primary_key="team_id",
        columns=("team_id", "team_name", "age_group", "league"),
        volume_assumption="3-8 teams locally; dozens across a multi-club group.",
        quality_issues=("duplicate team names",),
        relationships=(),
    ),
    "training_sessions": DatasetContract(
        name="training_sessions",
        primary_key="session_id",
        columns=("session_id", "team_id", "session_date", "session_type", "planned_load", "duration_min"),
        volume_assumption="1-3 sessions per team per day.",
        quality_issues=("negative duration", "late arriving session records"),
        relationships=("team_id -> teams.team_id",),
    ),
    "gps_tracking_aggregates": DatasetContract(
        name="gps_tracking_aggregates",
        primary_key="event_id",
        columns=(
            "event_id",
            "player_id",
            "session_id",
            "total_distance_m",
            "high_speed_distance_m",
            "sprint_count",
            "accel_count",
            "decel_count",
            "max_speed_kmh",
        ),
        volume_assumption="Squad size multiplied by training sessions; millions per season at production scale.",
        quality_issues=("out-of-range max speed", "missing player_id", "duplicate event_id"),
        relationships=("player_id -> players.player_id", "session_id -> training_sessions.session_id"),
    ),
    "wellness_surveys": DatasetContract(
        name="wellness_surveys",
        primary_key="survey_id",
        columns=("survey_id", "player_id", "survey_date", "sleep_quality", "soreness", "fatigue", "mood", "stress"),
        volume_assumption="One record per player per training day.",
        quality_issues=("out-of-range 1-5 scores", "missing surveys"),
        relationships=("player_id -> players.player_id",),
    ),
    "injuries_availability": DatasetContract(
        name="injuries_availability",
        primary_key="record_id",
        columns=("record_id", "player_id", "status_date", "availability_status", "injury_type", "expected_return_date"),
        volume_assumption="Daily availability status per unavailable player, sparse for healthy players.",
        quality_issues=("unsupported availability status", "expected return before status date"),
        relationships=("player_id -> players.player_id",),
    ),
    "fixtures": DatasetContract(
        name="fixtures",
        primary_key="fixture_id",
        columns=("fixture_id", "team_id", "opponent", "competition", "kickoff_ts", "venue", "importance_score"),
        volume_assumption="50-70 fixtures per senior team per season.",
        quality_issues=("duplicate fixture_id", "invalid importance score"),
        relationships=("team_id -> teams.team_id",),
    ),
    "match_events": DatasetContract(
        name="match_events",
        primary_key="event_id",
        columns=("event_id", "fixture_id", "team_id", "player_id", "event_ts", "event_type", "x", "y", "outcome"),
        volume_assumption="1,500-3,000 events per match from an event provider.",
        quality_issues=("orphan fixture_id", "coordinates outside pitch bounds"),
        relationships=("fixture_id -> fixtures.fixture_id", "player_id -> players.player_id"),
    ),
    "ticket_sales": DatasetContract(
        name="ticket_sales",
        primary_key="order_id",
        columns=("order_id", "fixture_id", "fan_id", "sale_ts", "stand", "price_paid", "channel", "quantity"),
        volume_assumption="Hundreds locally; tens of thousands per fixture in production.",
        quality_issues=("negative price", "duplicate order_id", "orphan fixture_id"),
        relationships=("fixture_id -> fixtures.fixture_id",),
    ),
    "merchandise_orders": DatasetContract(
        name="merchandise_orders",
        primary_key="order_id",
        columns=("order_id", "fan_id", "order_ts", "sku", "category", "quantity", "net_revenue", "channel"),
        volume_assumption="Hundreds locally; millions per season across ecommerce and stadium retail.",
        quality_issues=("negative revenue", "zero quantity"),
        relationships=("fan_id joins to synthetic fan identifiers used in ticket and engagement events",),
    ),
    "fan_engagement_events": DatasetContract(
        name="fan_engagement_events",
        primary_key="event_id",
        columns=("event_id", "fan_id", "event_ts", "channel", "event_type", "campaign_id"),
        volume_assumption="Thousands locally; hundreds of millions per season in production.",
        quality_issues=("missing campaign_id", "invalid channel enum"),
        relationships=("campaign_id -> marketing_campaigns.campaign_id",),
    ),
    "marketing_campaigns": DatasetContract(
        name="marketing_campaigns",
        primary_key="campaign_id",
        columns=("campaign_id", "name", "start_date", "end_date", "target_segment", "spend", "channel"),
        volume_assumption="5-20 campaigns per month.",
        quality_issues=("end_date before start_date", "negative spend"),
        relationships=(),
    ),
    "staff_workflow_events": DatasetContract(
        name="staff_workflow_events",
        primary_key="event_id",
        columns=("event_id", "staff_role", "workflow_name", "event_ts", "status", "minutes_saved_estimate"),
        volume_assumption="Hundreds locally; thousands weekly when workflow telemetry is mature.",
        quality_issues=("unsupported status", "negative minutes saved"),
        relationships=(),
    ),
    "product_adoption_events": DatasetContract(
        name="product_adoption_events",
        primary_key="event_id",
        columns=("event_id", "user_id", "persona", "product_area", "event_ts", "action", "session_id"),
        volume_assumption="Hundreds locally; high-cardinality event stream in production.",
        quality_issues=("missing user_id", "unknown persona", "duplicate session events"),
        relationships=(),
    ),
}


SOURCE_NAMES: tuple[str, ...] = tuple(DATASET_CONTRACTS.keys())

