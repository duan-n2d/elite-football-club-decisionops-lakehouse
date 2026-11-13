create or replace table silver.players as
select *
from (
  select
    *,
    row_number() over (partition by player_id order by _ingested_at desc) as rn
  from bronze.raw_players
  where player_id is not null
    and team_id is not null
    and position in ('GK', 'CB', 'FB', 'DM', 'CM', 'AM', 'WG', 'ST')
)
where rn = 1;

