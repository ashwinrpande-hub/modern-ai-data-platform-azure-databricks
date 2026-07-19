-- Bulk lineage checks across ALL orders and ALL three source systems (SAP/JDE/QAD), rather
-- than the single-order walkthrough in 02_trace_order_lineage.sql. Useful for spot-checking
-- that nothing was dropped/duplicated between layers.
--
-- Works because the hash key is deterministic and computable directly from the Bronze row:
--   hk = sha2(concat_ws('|', source_system, src_order_id), 256)   -- see pipelines/silver_dlt.py
-- so Bronze rows can be joined straight into Silver/Gold without going through the mapping
-- config at query time.

-- ============ Per-order lineage, side by side across all layers ============
WITH bronze_all AS (
  SELECT VBELN AS src_order_id, 'SAP' AS source_system, NETWR AS bronze_amount
  FROM acme_bronze.sap.vbak
  UNION ALL
  SELECT concat_ws('-', SHKCOO, SHDOCO, SHDCTO), 'JDE', CAST(SHOTOT AS STRING)
  FROM acme_bronze.jde.f4201
  UNION ALL
  SELECT so_nbr, 'QAD', CAST(so_t_amt AS STRING)
  FROM acme_bronze.qad.so_mstr
),
bronze_hk AS (
  SELECT *, sha2(concat_ws('|', source_system, src_order_id), 256) AS hk FROM bronze_all
)
SELECT b.source_system, b.src_order_id, b.bronze_amount,
       s.order_amount_usd AS silver_amount_usd,
       f.order_amount_usd AS gold_amount_usd,
       br.is_shipped, br.is_invoiced
FROM bronze_hk b
LEFT JOIN acme_silver.sales.v_sales_order_header_current s ON s.hk = b.hk
LEFT JOIN acme_gold.sales.fact_sales_orders f ON f.order_hk = b.hk
LEFT JOIN acme_gold.sales.bridge_order_fulfillment br ON br.order_hk = b.hk
ORDER BY b.source_system, b.src_order_id
LIMIT 200;

-- ============ Row-count reconciliation per source system: nothing lost between layers ============
WITH bronze_all AS (
  SELECT VBELN AS src_order_id, 'SAP' AS source_system FROM acme_bronze.sap.vbak
  UNION ALL
  SELECT concat_ws('-', SHKCOO, SHDOCO, SHDCTO), 'JDE' FROM acme_bronze.jde.f4201
  UNION ALL
  SELECT so_nbr, 'QAD' FROM acme_bronze.qad.so_mstr
),
bronze_hk AS (
  SELECT *, sha2(concat_ws('|', source_system, src_order_id), 256) AS hk FROM bronze_all
)
SELECT b.source_system,
       count(*)                    AS bronze_rows,
       count(s.hk)                 AS matched_in_silver,
       count(g.order_hk)           AS matched_in_gold
FROM bronze_hk b
LEFT JOIN acme_silver.sales.v_sales_order_header_current s ON s.hk = b.hk
LEFT JOIN acme_gold.sales.fact_sales_orders g ON g.order_hk = b.hk
GROUP BY b.source_system
ORDER BY b.source_system;

-- ============ Orphans: any Bronze order with no matching Gold fact (should be empty) ============
WITH bronze_all AS (
  SELECT VBELN AS src_order_id, 'SAP' AS source_system FROM acme_bronze.sap.vbak
  UNION ALL
  SELECT concat_ws('-', SHKCOO, SHDOCO, SHDCTO), 'JDE' FROM acme_bronze.jde.f4201
  UNION ALL
  SELECT so_nbr, 'QAD' FROM acme_bronze.qad.so_mstr
)
SELECT b.source_system, b.src_order_id
FROM bronze_all b
LEFT ANTI JOIN acme_gold.sales.fact_sales_orders g
  ON g.order_hk = sha2(concat_ws('|', b.source_system, b.src_order_id), 256)
LIMIT 50;
