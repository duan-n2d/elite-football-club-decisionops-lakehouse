"""Rule-based local stub for ClubOps Copilot.

In Azure, this module can swap the intent matcher for Azure OpenAI while keeping
the same semantic catalog, SQL validation, logging, and execution boundaries.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from api import repository
from lakehouse.config import load_config
from lakehouse.io import append_jsonl, to_float, to_int, utc_now
from ai_assistant.sql_validator import validate_sql


REFUSAL_TOPICS = {
    "salary",
    "contract",
    "medical diagnosis",
    "diagnose",
    "private",
    "personal email",
    "phone number",
    "address",
    "scouting target",
}


def answer_question(question: str, user_persona: str = "Data Platform Lead", execute: bool = True) -> dict[str, Any]:
    started = time.perf_counter()
    question_l = question.lower().strip()
    sql: str | None = None
    answer = ""
    refused = False
    refusal_reason: str | None = None
    rows: list[dict[str, Any]] = []

    if any(topic in question_l for topic in REFUSAL_TOPICS):
        refused = True
        refusal_reason = "The question asks for unsupported, private, or sensitive information outside the trusted data product."
        answer = refusal_reason
    elif "readiness" in question_l or "risk" in question_l or "training" in question_l:
        sql = """
        select player_id, metric_date, readiness_score, readiness_band, recommended_action
        from gold.fact_player_readiness_daily
        order by metric_date desc, readiness_score asc
        """
        rows = repository.player_readiness(limit=10) if execute else []
        answer = _summarize_readiness(rows)
    elif "revenue" in question_l or "ticket" in question_l or "merch" in question_l or "matchday" in question_l:
        sql = """
        select fixture_id, channel, revenue_type, net_revenue, order_count, unit_count
        from gold.fact_matchday_revenue
        order by net_revenue desc
        """
        rows = repository.matchday_revenue()[:10] if execute else []
        answer = _summarize_revenue(rows)
    elif "fan" in question_l or "segment" in question_l:
        sql = """
        select fan_segment, fan_count, ticket_revenue, merch_revenue, engagement_count
        from gold.dim_fan_segment
        order by fan_count desc
        """
        rows = repository.fan_segments() if execute else []
        answer = _summarize_segments(rows)
    elif "campaign" in question_l or "ctr" in question_l:
        sql = """
        select campaign_id, metric_date, channel, engagement_count, click_count, cost_per_engagement
        from gold.fact_campaign_performance
        order by metric_date desc
        """
        rows = repository.campaign_performance()[:10] if execute else []
        answer = _summarize_campaigns(rows)
    elif "adoption" in question_l or "usage" in question_l or "workflow" in question_l:
        sql = """
        select persona, product_area, metric_date, event_count, active_users, estimated_minutes_saved
        from gold.fact_product_adoption
        order by metric_date desc
        """
        rows = repository.adoption_metrics()[:10] if execute else []
        answer = _summarize_adoption(rows)
    elif "quality" in question_l or "freshness" in question_l or "pipeline" in question_l:
        sql = """
        select table_name, check_name, status, row_count
        from quality.quality_results
        order by table_name
        """
        status = repository.quality_status() if execute else {"quality_score_pct": 0, "failed_checks": 0}
        answer = f"Current data quality score is {status['quality_score_pct']}% with {status['failed_checks']} failed checks."
    else:
        refused = True
        refusal_reason = "I can only answer questions covered by trusted football operations, commercial, fan, adoption, quality, or monitoring data."
        answer = refusal_reason

    validation = validate_sql(sql or "select 1 from gold.fact_product_adoption", max_rows=load_config().copilot_max_rows)
    if not refused and not validation.is_valid:
        refused = True
        refusal_reason = validation.reason
        answer = f"I refused this query because the generated SQL failed validation: {validation.reason}"

    latency_ms = int((time.perf_counter() - started) * 1000)
    estimated_tokens = max(50, len(question.split()) * 6 + (len(sql or "") // 4))
    estimated_cost = round((estimated_tokens / 1000) * 0.002, 6)
    response = {
        "answer": answer,
        "generated_sql": validation.sql if not refused else sql,
        "source_tables": validation.source_tables if not refused else [],
        "refused": refused,
        "refusal_reason": refusal_reason,
        "latency_ms": latency_ms,
        "estimated_cost_usd": estimated_cost,
    }
    _log_interaction(question, user_persona, response)
    return response


def _summarize_readiness(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No readiness rows are available yet. Run the pipeline first."
    low = rows[0]
    return (
        f"Lowest current readiness is {low.get('player_name', low.get('player_id'))} "
        f"at {low.get('readiness_score')} ({low.get('readiness_band')}). "
        f"Recommended action: {low.get('recommended_action')}."
    )


def _summarize_revenue(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No matchday revenue rows are available yet."
    total = round(sum(to_float(row.get("net_revenue")) for row in rows), 2)
    top = max(rows, key=lambda row: to_float(row.get("net_revenue")))
    return f"Top visible revenue line is {top.get('revenue_type')} via {top.get('channel')} at {top.get('net_revenue')}. Sample total is {total}."


def _summarize_segments(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No fan segment rows are available yet."
    top = rows[0]
    return f"Largest segment is {top.get('fan_segment')} with {top.get('fan_count')} fans in the trusted demo data."


def _summarize_campaigns(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No campaign performance rows are available yet."
    best = min(rows, key=lambda row: to_float(row.get("cost_per_engagement"), 999999))
    return f"Best sample cost per engagement is campaign {best.get('campaign_id')} at {best.get('cost_per_engagement')}."


def _summarize_adoption(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No adoption rows are available yet."
    active_users = sum(to_int(row.get("active_users")) for row in rows)
    minutes = round(sum(to_float(row.get("estimated_minutes_saved")) for row in rows), 2)
    return f"Recent adoption sample shows {active_users} active user-count entries and {minutes} estimated minutes saved."


def _log_interaction(question: str, user_persona: str, response: dict[str, Any]) -> None:
    config = load_config()
    append_jsonl(
        Path(config.pipeline_log_path).parent / "copilot_interactions.jsonl",
        {
            "event_ts": utc_now(),
            "question": question,
            "user_persona": user_persona,
            "generated_sql": response.get("generated_sql"),
            "source_tables": response.get("source_tables", []),
            "latency_ms": response.get("latency_ms"),
            "estimated_cost_usd": response.get("estimated_cost_usd"),
            "refused": response.get("refused"),
            "refusal_reason": response.get("refusal_reason"),
            "feedback": None,
        },
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask ClubOps Copilot a local guarded question.")
    parser.add_argument("question")
    parser.add_argument("--persona", default="Data Platform Lead")
    parser.add_argument("--no-execute", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    response = answer_question(args.question, args.persona, execute=not args.no_execute)
    print(response["answer"])
    if response.get("generated_sql"):
        print(response["generated_sql"])


if __name__ == "__main__":
    main()

