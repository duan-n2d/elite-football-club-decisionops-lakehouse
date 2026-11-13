create or replace table gold.fact_player_readiness_daily as
select
  w.player_id,
  w.metric_date,
  greatest(
    0,
    least(
      100,
      100
        - least(35, abs(coalesce(w.acute_chronic_load_ratio, 1.0) - 1.0) * 45)
        - least(25, coalesce(ws.fatigue, 3) * 4 + coalesce(ws.soreness, 3) * 2 + coalesce(ws.stress, 3) * 1.5)
        - case
            when a.availability_status = 'managed_load' then 10
            when a.availability_status = 'doubtful' then 25
            when a.availability_status = 'unavailable' then 50
            else 0
          end
    )
  ) as readiness_score,
  a.availability_status,
  w.acute_chronic_load_ratio
from gold.fact_player_workload_daily w
left join silver.wellness_daily ws
  on w.player_id = ws.player_id and w.metric_date = ws.metric_date
left join silver.player_availability_daily a
  on w.player_id = a.player_id and w.metric_date = a.metric_date;

