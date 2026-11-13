"""Guardrails for generated SQL."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


ALLOWED_TABLES = {
    "silver.players",
    "silver.player_workload_daily",
    "silver.wellness_daily",
    "silver.player_availability_daily",
    "silver.ticket_sales",
    "silver.merchandise_orders",
    "silver.fan_engagement_events",
    "gold.dim_player",
    "gold.dim_team",
    "gold.dim_fixture",
    "gold.dim_fan_segment",
    "gold.dim_date",
    "gold.fact_player_workload_daily",
    "gold.fact_player_readiness_daily",
    "gold.fact_matchday_revenue",
    "gold.fact_fan_engagement_daily",
    "gold.fact_campaign_performance",
    "gold.fact_product_adoption",
    "gold.fact_demand_forecast",
    "quality.quality_results",
    "monitoring.data_freshness",
    "monitoring.product_success_metrics",
}
FORBIDDEN_KEYWORDS = {
    "alter",
    "copy",
    "create",
    "delete",
    "drop",
    "grant",
    "insert",
    "merge",
    "optimize",
    "revoke",
    "truncate",
    "update",
    "vacuum",
}
SENSITIVE_COLUMNS = {"fan_id", "birth_date"}


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    sql: str
    source_tables: list[str] = field(default_factory=list)
    reason: str | None = None


def validate_sql(sql: str, max_rows: int = 100) -> ValidationResult:
    normalized = " ".join(sql.strip().rstrip(";").split())
    lowered = normalized.lower()
    if not lowered.startswith("select"):
        return ValidationResult(False, normalized, reason="Only SELECT statements are allowed.")

    tokens = set(re.findall(r"\b[a-z_]+\b", lowered))
    forbidden = sorted(tokens & FORBIDDEN_KEYWORDS)
    if forbidden:
        return ValidationResult(False, normalized, reason=f"Forbidden keyword(s): {', '.join(forbidden)}")

    source_tables = sorted(set(re.findall(r"\b(?:from|join)\s+([a-zA-Z0-9_.]+)", normalized, flags=re.IGNORECASE)))
    unsupported = [table for table in source_tables if table not in ALLOWED_TABLES]
    if unsupported:
        return ValidationResult(False, normalized, source_tables, reason=f"Unsupported table(s): {', '.join(unsupported)}")

    selected_clause = lowered.split(" from ", 1)[0]
    sensitive = sorted(column for column in SENSITIVE_COLUMNS if re.search(rf"\b{column}\b", selected_clause))
    if sensitive and "count(" not in selected_clause and "count_distinct(" not in selected_clause:
        return ValidationResult(False, normalized, source_tables, reason=f"Sensitive column(s) require aggregation: {', '.join(sensitive)}")

    if " limit " not in lowered:
        normalized = f"{normalized} limit {max_rows}"
    return ValidationResult(True, normalized, source_tables)

