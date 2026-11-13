# Problem Discovery

## Executive Summary

Elite football clubs need faster, trusted decisions across sporting and business operations. A Head of Football Operations wants to know whether players are ready for training or matchday. A Commercial Director wants to understand ticket and merchandise demand. A Fan Engagement Manager wants trusted fan segments. A Data Platform Lead wants reliable, reusable data products rather than one-off reports.

This project is forward-deployed because it starts with daily stakeholder workflows, not just tables. It delivers pipelines, marts, APIs, dashboards, AI assistance, monitoring, and adoption metrics.

## Stakeholder Personas

| Persona | Business Goal | Pain Points | Current Manual Workflow | Data Needed | Success Metric | Daily Change |
|---|---|---|---|---|---|---|
| Head of Football Operations | Improve readiness and reduce preventable availability risk | GPS, wellness, and availability data are reviewed separately | Export GPS, copy wellness scores, ask medical staff for availability, build a slide | Players, sessions, GPS, wellness, availability, fixtures | Fewer manual prep hours and more managed-load decisions documented | Opens Football Operations page before staff meeting |
| Commercial Director | Grow matchday revenue and plan demand | Ticketing, retail, and campaign views do not reconcile | Pull CSVs from ticketing and ecommerce, manually summarize by fixture | Fixtures, ticket sales, merch orders, campaigns | Revenue visibility before matchday and faster channel decisions | Uses Matchday Revenue page for pricing and staffing decisions |
| Fan Engagement Manager | Activate trusted segments and measure campaigns | Fan lists are static and campaign reporting is delayed | Build spreadsheets from email, app, ticketing, and retail exports | Fan events, campaigns, ticketing, merchandise | Campaigns using governed segments and lower cost per engagement | Selects segments from Gold data products |
| Data Platform Lead | Build governed, reusable, observable data products | Ad hoc pipelines create trust and support issues | Manually rerun jobs, inspect logs, answer repeated metric questions | Run logs, quality results, freshness, adoption events | Fewer incidents, higher dashboard adoption, reusable marts | Uses monitoring to triage quality and adoption |

## High-Value Use Cases

| Use Case | Input Data | Output Data Product | Business Impact | Technical Components | Acceptance Criteria |
|---|---|---|---|---|---|
| Training workload and player readiness | GPS, sessions, wellness, availability | `fact_player_readiness_daily`, Football Operations dashboard | Faster staff decisions and managed load visibility | Bronze/Silver/Gold, quality checks, FastAPI | Readiness is reproducible, traceable, and refreshed daily |
| Matchday operations dashboard | Fixtures, ticket sales, merch orders | `fact_matchday_revenue`, dashboard and API | Better channel decisions and matchday staffing | Gold mart, API, dashboard filters | Revenue filterable by fixture, channel, and revenue type |
| Fan engagement segmentation | Fan events, tickets, merch | `dim_fan_segment`, `fact_fan_engagement_daily` | Campaigns use governed segments | Silver fan events, segment rules, dashboard | Segment counts and revenue are explainable |
| Ticket and merchandise forecasting | Revenue history, fixtures | `fact_demand_forecast`, MLflow run | Better inventory and staffing planning | Gold fact, baseline model, MLflow | Forecast and validation MAE are logged |
| ClubOps Copilot | Semantic layer, Silver/Gold data | Guarded natural-language answers | Faster operational Q&A with governance | Prompt template, SQL validator, logs | Unsupported or sensitive questions are refused |

