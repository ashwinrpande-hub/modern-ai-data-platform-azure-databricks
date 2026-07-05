-- DQ Trust Dashboard (gap B1: requirement says "dashboard showing that metrics" for the
-- DAMA 6 dimensions, proving trust in data products). Each named query below is a dataset
-- for one Lakeview (AI/BI) dashboard widget. Import via dashboard UI or bundle resource.
-- Complements (not replaces) Databricks DQ Monitoring anomaly detection: anomaly detection
-- catches unknown-unknowns; these are the contractual DAMA thresholds per data product.

-- widget: dq_score_by_dimension (heatmap: dimension x day, avg score)
SELECT date_trunc('day', run_at) AS day, dimension, table_name,
       round(avg(score), 4) AS avg_score, min(met_threshold) AS all_passed
FROM nucor_bronze.audit.dq_results
GROUP BY 1, 2, 3;

-- widget: product_trust_scorecard (current trust per data product; joins product SLAs)
WITH latest AS (
  SELECT table_name, dimension, score, met_threshold,
         row_number() OVER (PARTITION BY table_name, dimension ORDER BY run_at DESC) rn
  FROM nucor_bronze.audit.dq_results)
SELECT table_name,
       round(avg(score) * 100, 2)                       AS trust_score_pct,
       count_if(NOT met_threshold)                      AS breached_dimensions,
       collect_list(CASE WHEN NOT met_threshold THEN dimension END) AS breaches
FROM latest WHERE rn = 1
GROUP BY table_name;

-- widget: rejects_drilldown (last 7 days, by rule + DAMA dimension)
SELECT date_trunc('hour', rejected_at) AS hour, target_table, dq_dimension, failed_rule,
       count(*) AS rejected_rows
FROM nucor_bronze.audit.rejected_records
WHERE rejected_at > current_timestamp() - INTERVAL 7 DAYS
GROUP BY 1, 2, 3, 4;

-- widget: batch_health (throughput + reject rate per source — from quarantine_writer)
SELECT date_trunc('day', finished_at) AS day, source_name,
       sum(rows_written) AS rows_written, sum(rows_rejected) AS rows_rejected,
       round(sum(rows_rejected) / nullif(sum(rows_read), 0) * 100, 3) AS reject_pct
FROM nucor_bronze.audit.batch_log
GROUP BY 1, 2;

-- widget/alert: freshness_slo (TIMELINESS vs product SLAs in data_products.yaml;
-- attach a Databricks SQL alert: condition minutes_since_load > sla_minutes)
SELECT source_name,
       max(finished_at) AS last_load,
       timestampdiff(MINUTE, max(finished_at), current_timestamp()) AS minutes_since_load,
       CASE source_name WHEN 'sales_orders_unified' THEN 30
                        WHEN 'customer_360' THEN 60
                        WHEN 'melt_to_margin' THEN 15 ELSE 60 END AS sla_minutes
FROM nucor_bronze.audit.batch_log
GROUP BY source_name;
