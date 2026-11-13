"""Stakeholder dashboard for the DecisionOps lakehouse."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from api import repository
from ai_assistant.copilot import answer_question


st.set_page_config(page_title="Elite FC DecisionOps", page_icon="FC", layout="wide")


PAGES = [
    "Executive Overview",
    "Football Operations",
    "Matchday Revenue",
    "Fan Engagement",
    "Campaign Performance",
    "Data Quality & Pipeline Monitoring",
    "Product Adoption",
    "ClubOps Copilot",
]


def _df(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _metric_row(metrics: list[tuple[str, object, str | None]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics, strict=False):
        col.metric(label, value, delta)


def executive_overview() -> None:
    readiness = _df(repository.player_readiness(limit=100))
    revenue = _df(repository.matchday_revenue())
    adoption = _df(repository.adoption_metrics())
    quality = repository.quality_status()

    avg_readiness = round(readiness["readiness_score"].astype(float).mean(), 1) if not readiness.empty else 0
    total_revenue = round(revenue["net_revenue"].astype(float).sum(), 2) if not revenue.empty else 0
    active_users = int(adoption["active_users"].astype(int).sum()) if not adoption.empty else 0
    _metric_row(
        [
            ("Avg readiness", avg_readiness, "Football operations"),
            ("Visible revenue", f"${total_revenue:,.0f}", "Ticket + merch"),
            ("Adoption users", active_users, "Recent usage"),
            ("Quality score", f"{quality['quality_score_pct']}%", "Trusted data"),
        ]
    )
    st.subheader("Executive questions answered")
    st.write("- Are players ready for the next match?")
    st.write("- Which commercial channels are performing?")
    st.write("- Are stakeholders adopting the product?")
    st.write("- Can executives trust the data today?")


def football_operations() -> None:
    df = _df(repository.player_readiness(limit=100))
    if df.empty:
        st.info("Run `make pipeline` to populate readiness data.")
        return
    band = st.multiselect("Readiness band", sorted(df["readiness_band"].unique()), default=sorted(df["readiness_band"].unique()))
    filtered = df[df["readiness_band"].isin(band)]
    _metric_row(
        [
            ("Players monitored", len(filtered), None),
            ("High-risk players", int((filtered["readiness_band"] == "high_risk").sum()), None),
            ("Managed players", int((filtered["readiness_band"] == "managed").sum()), None),
        ]
    )
    st.plotly_chart(px.bar(filtered, x="player_name", y="readiness_score", color="readiness_band"), use_container_width=True)
    st.dataframe(filtered, use_container_width=True)
    st.caption("Adoption metric: weekly coaching staff views and alert acknowledgements.")


def matchday_revenue() -> None:
    df = _df(repository.matchday_revenue())
    if df.empty:
        st.info("Run `make pipeline` to populate matchday revenue.")
        return
    channel = st.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
    filtered = df[df["channel"].isin(channel)]
    _metric_row(
        [
            ("Net revenue", f"${filtered['net_revenue'].astype(float).sum():,.0f}", None),
            ("Orders", int(filtered["order_count"].astype(int).sum()), None),
            ("Units", int(filtered["unit_count"].astype(int).sum()), None),
        ]
    )
    st.plotly_chart(px.bar(filtered, x="channel", y="net_revenue", color="revenue_type"), use_container_width=True)
    st.dataframe(filtered, use_container_width=True)
    st.caption("Stakeholder question: Which channel should receive matchday staffing or campaign attention?")


def fan_engagement() -> None:
    df = _df(repository.fan_segments())
    if df.empty:
        st.info("Run `make pipeline` to populate fan segments.")
        return
    _metric_row(
        [
            ("Segments", df["fan_segment"].nunique(), None),
            ("Fans represented", int(df["fan_count"].astype(int).sum()), None),
            ("Engagements", int(df["engagement_count"].astype(int).sum()), None),
        ]
    )
    st.plotly_chart(px.pie(df, names="fan_segment", values="fan_count"), use_container_width=True)
    st.dataframe(df, use_container_width=True)
    st.caption("Adoption metric: number of campaigns using governed fan segments.")


def campaign_performance() -> None:
    df = _df(repository.campaign_performance())
    if df.empty:
        st.info("Run `make pipeline` to populate campaign performance.")
        return
    campaign = st.selectbox("Campaign", sorted(df["campaign_id"].unique()))
    filtered = df[df["campaign_id"] == campaign]
    _metric_row(
        [
            ("Engagements", int(filtered["engagement_count"].astype(int).sum()), None),
            ("Clicks", int(filtered["click_count"].astype(int).sum()), None),
            ("Avg cost / engagement", round(filtered["cost_per_engagement"].astype(float).mean(), 2), None),
        ]
    )
    st.plotly_chart(px.line(filtered, x="metric_date", y="engagement_count", color="channel"), use_container_width=True)
    st.dataframe(filtered, use_container_width=True)
    st.caption("Stakeholder question: Which channels should be scaled or paused?")


def quality_monitoring() -> None:
    quality = repository.quality_status()
    checks = _df(quality["checks"])
    freshness = _df(quality["freshness"])
    _metric_row(
        [
            ("Quality score", f"{quality['quality_score_pct']}%", None),
            ("Failed checks", quality["failed_checks"], None),
            ("Tables monitored", len(freshness), None),
        ]
    )
    if not checks.empty:
        st.plotly_chart(px.histogram(checks, x="status", color="status"), use_container_width=True)
        st.dataframe(checks, use_container_width=True)
    if not freshness.empty:
        st.subheader("Freshness")
        st.dataframe(freshness, use_container_width=True)
    st.caption("Adoption metric: reduction in manual data quality triage and faster incident response.")


def product_adoption() -> None:
    df = _df(repository.adoption_metrics())
    if df.empty:
        st.info("Run `make pipeline` to populate product adoption.")
        return
    persona = st.multiselect("Persona", sorted(df["persona"].unique()), default=sorted(df["persona"].unique()))
    filtered = df[df["persona"].isin(persona)]
    _metric_row(
        [
            ("Events", int(filtered["event_count"].astype(int).sum()), None),
            ("Sessions", int(filtered["session_count"].astype(int).sum()), None),
            ("Minutes saved", int(filtered["estimated_minutes_saved"].astype(float).sum()), None),
        ]
    )
    st.plotly_chart(px.bar(filtered, x="product_area", y="event_count", color="persona"), use_container_width=True)
    st.dataframe(filtered, use_container_width=True)
    st.caption("Stakeholder question: Which workflows are becoming self-serve and which still need enablement?")


def copilot_page() -> None:
    question = st.text_input("Ask ClubOps Copilot", "Which players have the lowest readiness this week?")
    persona = st.selectbox(
        "Persona",
        ["Head of Football Operations", "Commercial Director", "Fan Engagement Manager", "Data Platform Lead"],
    )
    if st.button("Ask"):
        response = answer_question(question, user_persona=persona, execute=True)
        st.write(response["answer"])
        if response.get("generated_sql"):
            st.code(response["generated_sql"], language="sql")
        st.write("Source tables:", ", ".join(response.get("source_tables", [])) or "None")
        st.write("Estimated cost USD:", response["estimated_cost_usd"])


def main() -> None:
    st.title("Elite Football Club DecisionOps Lakehouse")
    page = st.sidebar.radio("Page", PAGES)
    if page == "Executive Overview":
        executive_overview()
    elif page == "Football Operations":
        football_operations()
    elif page == "Matchday Revenue":
        matchday_revenue()
    elif page == "Fan Engagement":
        fan_engagement()
    elif page == "Campaign Performance":
        campaign_performance()
    elif page == "Data Quality & Pipeline Monitoring":
        quality_monitoring()
    elif page == "Product Adoption":
        product_adoption()
    else:
        copilot_page()


if __name__ == "__main__":
    main()

