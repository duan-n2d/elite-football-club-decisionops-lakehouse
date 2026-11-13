from __future__ import annotations

from data_generator.contracts import DATASET_CONTRACTS


def test_all_required_sources_have_contracts() -> None:
    required = {
        "players",
        "teams",
        "training_sessions",
        "gps_tracking_aggregates",
        "wellness_surveys",
        "injuries_availability",
        "fixtures",
        "match_events",
        "ticket_sales",
        "merchandise_orders",
        "fan_engagement_events",
        "marketing_campaigns",
        "staff_workflow_events",
        "product_adoption_events",
    }
    assert required == set(DATASET_CONTRACTS)
    for contract in DATASET_CONTRACTS.values():
        assert contract.primary_key in contract.columns
        assert contract.volume_assumption
        assert contract.quality_issues

