# Data Model

## Source Datasets

| Dataset | Schema | Example Row | Volume | Quality Issues | Relationships |
|---|---|---|---|---|---|
| players | player_id, team_id, name, position, birth_date, nationality, dominant_foot, squad_status, effective_from, effective_to | player_0001, team_men_1, Alex Bennett, GK | 30-80 local | duplicate, invalid position | team_id -> teams |
| teams | team_id, team_name, age_group, league | team_men_1, Elite FC Men, Senior | 3-8 local | duplicate name | none |
| training_sessions | session_id, team_id, session_date, session_type, planned_load, duration_min | session_00001, team_men_1, 2026-01-01, tactical | daily | negative duration | team_id -> teams |
| gps_tracking_aggregates | event_id, player_id, session_id, total_distance_m, high_speed_distance_m, sprint_count, accel_count, decel_count, max_speed_kmh | gps_0000001, player_0001, session_00001, 8400 | millions production | out-of-range speed, missing player | players, sessions |
| wellness_surveys | survey_id, player_id, survey_date, sleep_quality, soreness, fatigue, mood, stress | wellness_0000001, player_0001, 2026-01-01, 4 | daily per player | score outside 1-5 | players |
| injuries_availability | record_id, player_id, status_date, availability_status, injury_type, expected_return_date | availability_0000001, player_0001, available | daily | invalid status | players |
| fixtures | fixture_id, team_id, opponent, competition, kickoff_ts, venue, importance_score | fixture_0001, team_men_1, Capital City FC | season | invalid importance | teams |
| match_events | event_id, fixture_id, team_id, player_id, event_ts, event_type, x, y, outcome | match_event_00000001, fixture_0001, pass | thousands per match | bad coordinates | fixtures, players |
| ticket_sales | order_id, fixture_id, fan_id, sale_ts, stand, price_paid, channel, quantity | ticket_00000001, fixture_0001, fan_000123 | thousands per match | negative price | fixtures |
| merchandise_orders | order_id, fan_id, order_ts, sku, category, quantity, net_revenue, channel | merch_00000001, fan_000123, HOME-KIT | millions production | negative revenue | fan IDs |
| fan_engagement_events | event_id, fan_id, event_ts, channel, event_type, campaign_id | fan_event_000000001, fan_000123, email_open | high volume | invalid channel | campaigns |
| marketing_campaigns | campaign_id, name, start_date, end_date, target_segment, spend, channel | campaign_001, Kit Launch | monthly | negative spend | fan events |
| staff_workflow_events | event_id, staff_role, workflow_name, event_ts, status, minutes_saved_estimate | workflow_00000001, commercial, completed | hundreds weekly | negative minutes | adoption |
| product_adoption_events | event_id, user_id, persona, product_area, event_ts, action, session_id | adoption_00000001, user_0001, Commercial Director | high volume | unknown persona | monitoring |

## Bronze

Bronze tables are named `bronze.raw_<source>`. They are append-only and include:

- `_ingestion_run_id`
- `_source_file`
- `_source_file_hash`
- `_ingested_at`
- `_schema_version`
- `_record_hash`
- `_source_payload`

## Silver

Silver tables are cleaned source-level tables plus operational intermediates:

- `silver.players`, `silver.training_sessions`, `silver.ticket_sales`, etc.
- `silver.player_workload_daily`
- `silver.wellness_daily`
- `silver.player_availability_daily`
- `silver.fan_engagement_daily`
- `silver.quarantine_failed_records`

Validation covers required keys, enum checks, range checks, revenue checks, and deduplication by business key.

## Gold

| Table | Grain | Primary Key | Foreign Keys | Notes |
|---|---|---|---|---|
| fact_player_workload_daily | player + date | player_id, metric_date | dim_player, dim_date | Includes ACWR |
| fact_player_readiness_daily | player + date | player_id, metric_date | dim_player, dim_date | Readiness score and band |
| fact_matchday_revenue | fixture + channel + revenue_type | fixture_id, channel, revenue_type | dim_fixture | Ticket and merch revenue |
| fact_fan_engagement_daily | fan + date + channel | fan_id, metric_date, channel | dim_date, dim_fan_segment | Aggregated fan engagement |
| fact_campaign_performance | campaign + date | campaign_id, metric_date | dim_date | CTR and cost per engagement |
| fact_product_adoption | persona + product_area + date | persona, product_area, metric_date | dim_date | Adoption and time saved |
| dim_player | SCD2 player | player_key | dim_team | `effective_from`, `effective_to`, `is_current` |
| dim_team | team | team_id | none | Standard team dimension |
| dim_fixture | fixture | fixture_id | dim_team | Match context |
| dim_fan_segment | fan | fan_id | none | Derived reusable segment |
| dim_date | date | date_key | none | Calendar attributes |

## Star Schema

```text
dim_player       dim_team        dim_fixture      dim_fan_segment      dim_date
    |               |                |                  |                 |
    +---- facts: workload, readiness, matchday revenue, fan engagement, campaigns, adoption
```

## Sample SQL

See `transformations/gold/sample_queries.sql` for readiness risk, matchday revenue, campaign performance, adoption, and freshness queries.

