-- Configuration & lineage tables (deployed by scripts/deploy.py)
CREATE CATALOG IF NOT EXISTS nucor_bronze;
CREATE SCHEMA IF NOT EXISTS nucor_bronze.audit;
CREATE SCHEMA IF NOT EXISTS nucor_bronze.cfg;

-- Source registry: one row per registered source (mirrors replication_sources.yaml)
CREATE TABLE IF NOT EXISTS nucor_bronze.cfg.source_registry (
  source_name STRING, system STRING, region STRING, pattern STRING,
  target_table STRING, primary_key ARRAY<STRING>, sequence_col STRING,
  schedule STRING, expectations MAP<STRING,STRING>,
  registered_by STRING, registered_at TIMESTAMP, active BOOLEAN
) ;

-- Source→target mapping AT EACH LAYER (lineage-tracked, change = insert new version)
CREATE TABLE IF NOT EXISTS nucor_bronze.cfg.layer_mappings (
  mapping_id STRING, layer STRING,                 -- bronze|silver|gold
  src_table STRING, src_column STRING,
  tgt_table STRING, tgt_column STRING,
  transform_expr STRING,                            -- SQL expression, NULL = passthrough
  dq_rule STRING, version INT, valid_from TIMESTAMP, valid_to TIMESTAMP,
  changed_by STRING
);

-- Rejected records (record-level) + batch audit
CREATE TABLE IF NOT EXISTS nucor_bronze.audit.rejected_records (
  reject_id STRING, batch_id STRING, source_name STRING, target_table STRING,
  layer STRING, failed_rule STRING, dq_dimension STRING,    -- DAMA dimension
  record_payload STRING, rejected_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS nucor_bronze.audit.batch_log (
  batch_id STRING, source_name STRING, layer STRING,
  rows_read BIGINT, rows_written BIGINT, rows_rejected BIGINT,
  started_at TIMESTAMP, finished_at TIMESTAMP, status STRING, error STRING
);
