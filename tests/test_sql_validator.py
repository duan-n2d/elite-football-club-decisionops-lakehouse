from __future__ import annotations

from ai_assistant.sql_validator import validate_sql


def test_validator_allows_limited_select() -> None:
    result = validate_sql("select player_id, readiness_score from gold.fact_player_readiness_daily")
    assert result.is_valid
    assert "limit" in result.sql.lower()
    assert result.source_tables == ["gold.fact_player_readiness_daily"]


def test_validator_blocks_mutation() -> None:
    result = validate_sql("drop table gold.fact_player_readiness_daily")
    assert not result.is_valid


def test_validator_blocks_sensitive_unaggregated_columns() -> None:
    result = validate_sql("select fan_id from gold.dim_fan_segment")
    assert not result.is_valid
    assert "Sensitive" in str(result.reason)

