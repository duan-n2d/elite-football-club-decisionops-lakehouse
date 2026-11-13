create or replace table silver.ticket_sales as
select *
from bronze.raw_ticket_sales
where order_id is not null
  and fixture_id is not null
  and fan_id is not null
  and cast(price_paid as double) >= 0
  and cast(quantity as int) > 0;

create or replace table silver.merchandise_orders as
select *
from bronze.raw_merchandise_orders
where order_id is not null
  and fan_id is not null
  and cast(net_revenue as double) >= 0
  and cast(quantity as int) > 0;

