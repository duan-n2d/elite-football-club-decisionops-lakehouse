create catalog if not exists club_ops;

create schema if not exists club_ops.bronze comment 'Raw append-only football club source data';
create schema if not exists club_ops.silver comment 'Cleaned and validated club operational data';
create schema if not exists club_ops.gold comment 'Trusted data products for stakeholders';
create schema if not exists club_ops.monitoring comment 'Pipeline, quality, adoption, and AI usage telemetry';

grant use catalog on catalog club_ops to `data_engineers`;
grant use schema on schema club_ops.gold to `football_ops`, `commercial`, `fan_engagement`, `executives`;
grant select on all tables in schema club_ops.gold to `football_ops`, `commercial`, `fan_engagement`, `executives`;
grant select on all tables in schema club_ops.silver to `data_engineers`;
grant modify on schema club_ops.bronze to `data_engineers`;
grant modify on schema club_ops.silver to `data_engineers`;
grant modify on schema club_ops.gold to `data_engineers`;

alter schema club_ops.gold set tags ('classification' = 'trusted_business_metrics', 'owner' = 'data_platform');
alter schema club_ops.silver set tags ('classification' = 'validated_operational_data', 'owner' = 'data_platform');
alter schema club_ops.monitoring set tags ('classification' = 'operational_telemetry', 'owner' = 'data_platform');

