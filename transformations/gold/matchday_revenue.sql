create or replace table gold.fact_matchday_revenue as
select
  fixture_id,
  channel,
  'ticket' as revenue_type,
  sum(price_paid) as net_revenue,
  count(*) as order_count,
  sum(quantity) as unit_count
from silver.ticket_sales
group by fixture_id, channel;

