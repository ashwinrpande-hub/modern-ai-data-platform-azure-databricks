-- Output ports = secure views; published via Delta Sharing + Databricks Marketplace (private exchange)
CREATE CATALOG IF NOT EXISTS acme_products;
CREATE SCHEMA IF NOT EXISTS acme_products.sales;

CREATE OR REPLACE VIEW acme_products.sales.v_sales_orders AS
SELECT order_hk, customer_hk, source_system, order_date, order_amount_usd
FROM acme_gold.sales.fact_sales_orders;          -- row filters & masks carry through

COMMENT ON VIEW acme_products.sales.v_sales_orders IS
'DATA PRODUCT sales_orders_unified | owner: sales-data-team | SLA: 30-min freshness, 99.5% |
 trust score published daily to acme_products.meta.trust_scores';

-- Discoverability: UC tags drive both Marketplace listing and the custom portal search
ALTER VIEW acme_products.sales.v_sales_orders SET TAGS
  ('domain'='sales','product'='sales_orders_unified','certified'='true');

-- Share for Marketplace listing
CREATE SHARE IF NOT EXISTS acme_sales_products;
ALTER SHARE acme_sales_products ADD VIEW acme_products.sales.v_sales_orders;
-- Then: Marketplace -> provider console -> create private listing from share.

