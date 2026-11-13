# Monitoring And Product Adoption

## Technical Monitoring

Tracked locally:

- pipeline phase status
- run duration
- table row counts
- data freshness
- data quality score
- quarantine count
- Copilot latency and estimated cost

Alert design:

- failed pipeline phase
- stale Gold tables
- quality score drop below threshold
- API p95 latency above target
- Copilot budget threshold reached

## Product Adoption

Gold table `fact_product_adoption` tracks:

- persona
- product area
- date
- event count
- active users
- sessions
- Copilot queries
- estimated minutes saved

## Business Impact Metrics

- Time saved per week.
- Reduction in manual reporting.
- Increase in trusted dashboard usage.
- Number of reusable data products.
- Number of stakeholder workflows automated.
- Forecast accuracy for demand planning.
- Number of Copilot questions answered without analyst intervention.

## Adoption Narrative

The project does not stop when tables are built. It measures whether the product changes daily behavior: coaches reviewing readiness, commercial teams using matchday revenue before decisions, fan teams using governed segments, and platform leads reducing manual support.

