-- Explore table structure and data across all four layers of the lakehouse.
-- Run in the Databricks SQL Editor (needs a SQL warehouse -- none exists yet in this
-- workspace, create a small serverless one) or a notebook attached to any cluster/serverless
-- compute. Statements are independent; run whichever section you need.

-- ============ Catalogs & schemas ============
SHOW CATALOGS LIKE 'acme_*';

SELECT catalog_name, schema_name
FROM system.information_schema.schemata
WHERE catalog_name LIKE 'acme_%'
ORDER BY catalog_name, schema_name;

-- All tables across the four layers, with row counts via DESCRIBE DETAIL
SELECT table_catalog, table_schema, table_name, table_type
FROM system.information_schema.tables
WHERE table_catalog LIKE 'acme_%'
ORDER BY table_catalog, table_schema, table_name;

-- ============ Bronze: raw source-shaped tables ============
DESCRIBE TABLE acme_bronze.sap.vbak;              -- SAP sales order header (raw column names)
SELECT * FROM acme_bronze.sap.vbak LIMIT 10;

DESCRIBE TABLE acme_bronze.cfg.layer_mappings;    -- config-driven Bronze->Silver column mappings
SELECT * FROM acme_bronze.cfg.layer_mappings WHERE tgt_table = 'sales_order_header';

SELECT * FROM acme_bronze.cfg.source_registry;    -- registered ingestion sources (from replication_sources.yaml)

-- ============ Silver: 3NF, insert-only, hash-keyed ============
DESCRIBE TABLE acme_silver.sales.sales_order_header;
SELECT * FROM acme_silver.sales.sales_order_header LIMIT 10;

-- history is append-only: multiple versions per hk are expected, "current" is a row_number() filter
SELECT hk, count(*) AS versions FROM acme_silver.sales.sales_order_header GROUP BY hk ORDER BY versions DESC LIMIT 5;

-- ============ Gold: star schema + DV2.0 query-assist tables ============
DESCRIBE TABLE acme_gold.sales.fact_sales_orders;
SELECT * FROM acme_gold.sales.fact_sales_orders LIMIT 10;

SELECT * FROM acme_gold.sales.dim_customer LIMIT 10;
SELECT * FROM acme_gold.sales.pit_customer ORDER BY snapshot_date DESC LIMIT 10;
SELECT * FROM acme_gold.sales.bridge_order_fulfillment LIMIT 10;
SELECT * FROM acme_gold.sales.agg_sales_daily ORDER BY order_date DESC LIMIT 10;

-- ============ Row counts per layer, end to end ============
SELECT 'bronze.sap.vbak' AS table_name, count(*) AS rows FROM acme_bronze.sap.vbak
UNION ALL SELECT 'silver.sales_order_header', count(*) FROM acme_silver.sales.sales_order_header
UNION ALL SELECT 'gold.fact_sales_orders', count(*) FROM acme_gold.sales.fact_sales_orders
UNION ALL SELECT 'gold.bridge_order_fulfillment', count(*) FROM acme_gold.sales.bridge_order_fulfillment
UNION ALL SELECT 'gold.agg_sales_daily', count(*) FROM acme_gold.sales.agg_sales_daily;
