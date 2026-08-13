-- DQ Trust Dashboard (gap B1: requirement says "dashboard showing that metrics" for the
-- DAMA 6 dimensions, proving trust in data products). Each named query below is a dataset
-- for one Lakeview (AI/BI) dashboard widget. Import via dashboard UI or bundle resource.
-- Complements (not replaces) Databricks DQ Monitoring anomaly detection: anomaly detection
-- catches unknown-unknowns; these are the contractual DAMA thresholds per data product.
--
-- Column names below were corrected against the live schema (acme_bronze.audit.dq_results
-- is run_id/run_at/table_name/dq_dimension/check_name/passed/row_count -- no score or
-- met_threshold column exists; rejected_records is source_table/reason, not
-- target_table/failed_rule). "Score" is derived as a 0/100 pass rate from the boolean
-- passed column since dq_monitor_rca.py never wrote a numeric score.

-- widget: dq_score_by_dimension (heatmap: dimension x day, avg score)
SELECT date_trunc('day', run_at) AS day, dq_dimension, table_name,
       round(avg(CASE WHEN passed THEN 100.0 ELSE 0.0 END), 4) AS avg_score,
       min(passed) AS all_passed
FROM acme_bronze.audit.dq_results
GROUP BY 1, 2, 3;

-- widget: product_trust_scorecard (current trust per data product; joins product SLAs)
WITH latest AS (
  SELECT table_name, dq_dimension, passed,
         row_number() OVER (PARTITION BY table_name, dq_dimension ORDER BY run_at DESC) rn
  FROM acme_bronze.audit.dq_results)
SELECT table_name,
       round(avg(CASE WHEN passed THEN 100.0 ELSE 0.0 END), 2)  AS trust_score_pct,
       count_if(NOT passed)                                     AS breached_dimensions,
       collect_list(CASE WHEN NOT passed THEN dq_dimension END) AS breaches
FROM latest WHERE rn = 1
GROUP BY table_name;

-- widget: rejects_drilldown (last 7 days, by rule + DAMA dimension)
SELECT date_trunc('hour', rejected_at) AS hour, source_table, dq_dimension, reason,
       count(*) AS rejected_rows
FROM acme_bronze.audit.rejected_records
WHERE rejected_at > current_timestamp() - INTERVAL 7 DAYS
GROUP BY 1, 2, 3, 4;

-- widget: batch_health (throughput + reject rate per source — from quarantine_writer)
SELECT date_trunc('day', finished_at) AS day, source_name,
       sum(rows_written) AS rows_written, sum(rows_rejected) AS rows_rejected,
       round(sum(rows_rejected) / nullif(sum(rows_read), 0) * 100, 3) AS reject_pct
FROM acme_bronze.audit.batch_log
GROUP BY 1, 2;

-- widget/alert: freshness_slo (TIMELINESS vs product SLAs in data_products.yaml;
-- attach a Databricks SQL alert: condition minutes_since_load > sla_minutes)
SELECT source_name,
       max(finished_at) AS last_load,
       timestampdiff(MINUTE, max(finished_at), current_timestamp()) AS minutes_since_load,
       CASE source_name WHEN 'sales_orders_unified' THEN 30
                        WHEN 'customer_360' THEN 60
                        WHEN 'melt_to_margin' THEN 15 ELSE 60 END AS sla_minutes
FROM acme_bronze.audit.batch_log
GROUP BY source_name;

