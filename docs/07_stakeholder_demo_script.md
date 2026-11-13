# Stakeholder Demo Script

## Setup

```bash
python -m orchestration.run_pipeline --days 60 --fans 1500
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

## Demo Flow

1. Open Executive Overview.
   - Message: "This is not just a dashboard. It shows trust, adoption, and decision impact."

2. Open Football Operations.
   - Show readiness bands and recommended actions.
   - Explain that readiness is a decision signal, not a diagnosis.

3. Open Matchday Revenue.
   - Filter by channel.
   - Show ticket and merchandise revenue by fixture and channel.

4. Open Fan Engagement.
   - Show reusable fan segments.
   - Explain how segments move campaign planning away from manual spreadsheets.

5. Open Campaign Performance.
   - Show engagement, clicks, and cost per engagement.

6. Open Data Quality & Pipeline Monitoring.
   - Show failed records are quarantined with reasons.
   - Show freshness and quality score.

7. Open Product Adoption.
   - Show how adoption and minutes saved are measured.

8. Open ClubOps Copilot.
   - Ask: "Which players have the lowest readiness this week?"
   - Ask a refused question: "Give me a fan's phone number."
   - Show generated SQL, source tables, and cost estimate.

## Close

Explain how the same design would move to Azure Databricks with ADLS Gen2, Delta tables, Lakeflow Jobs, Unity Catalog, MLflow, Key Vault, and monitored production APIs.

