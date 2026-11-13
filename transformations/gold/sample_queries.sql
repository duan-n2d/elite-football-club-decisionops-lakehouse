-- Top readiness risks before the next fixture
select
  p.name,
  p.position,
  r.metric_date,
  r.readiness_score,
  r.readiness_band,
  r.recommended_action
from gold.fact_player_readiness_daily r
join gold.dim_player p on r.player_id = p.player_id and p.is_current = 'true'
order by r.metric_date desc, r.readiness_score asc
limit 10;

-- Matchday revenue by channel and opponent
select
  f.opponent,
  f.competition,
  r.channel,
  r.revenue_type,
  sum(r.net_revenue) as net_revenue
from gold.fact_matchday_revenue r
join gold.dim_fixture f on r.fixture_id = f.fixture_id
group by f.opponent, f.competition, r.channel, r.revenue_type
order by net_revenue desc;

-- Campaign ROI proxy by segment
select
  campaign_id,
  target_segment,
  channel,
  sum(engagement_count) as engagements,
  avg(cost_per_engagement) as avg_cost_per_engagement
from gold.fact_campaign_performance
group by campaign_id, target_segment, channel
order by avg_cost_per_engagement asc;

-- Dashboard adoption by persona
select
  persona,
  product_area,
  sum(event_count) as events,
  sum(active_users) as active_users,
  sum(estimated_minutes_saved) as estimated_minutes_saved
from gold.fact_product_adoption
group by persona, product_area
order by events desc;

-- Data freshness and quality score
select *
from monitoring.data_freshness
order by layer, table_name;

