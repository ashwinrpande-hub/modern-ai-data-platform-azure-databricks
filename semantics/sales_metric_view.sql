-- Unity Catalog Metric View (Business Semantics — GA 2026).
-- Define revenue/orders/AOV ONCE; AI/BI Dashboards, Genie spaces, SQL, and external BI
-- (Power BI/Tableau/Sigma) all bind to the same governed definitions.
-- Replaces the old pattern of pointing Genie at agg_sales_daily: the metric view carries
-- synonyms + formats so Genie grounds NL questions deterministically (Genie Ontology-ready).
CREATE OR REPLACE VIEW acme_gold.sales.mv_sales_metrics
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.0
source: acme_gold.sales.fact_sales_orders
filter: order_amount_usd IS NOT NULL
dimensions:
  - name: order_date
    expr: order_date
    display_name: Order Date
  - name: source_system
    expr: source_system
    display_name: Source ERP
    synonyms: [erp, system, region system]
  - name: customer
    expr: customer_hk
    display_name: Customer Key
measures:
  - name: revenue_usd
    expr: SUM(order_amount_usd)
    display_name: Revenue (USD)
    format: { type: currency, currency_code: USD, decimal_places: 0 }
    synonyms: [sales, total sales, net revenue]
  - name: order_count
    expr: COUNT(DISTINCT order_hk)
    display_name: Orders
    synonyms: [number of orders, order volume]
  - name: avg_order_value
    expr: SUM(order_amount_usd) / COUNT(DISTINCT order_hk)
    display_name: Average Order Value
    synonyms: [aov, average deal size]
  - name: active_customers
    expr: COUNT(DISTINCT customer_hk)
    display_name: Active Customers
$$;

ALTER VIEW acme_gold.sales.mv_sales_metrics SET TAGS ('certified'='true','domain'='sales');
GRANT SELECT ON VIEW acme_gold.sales.mv_sales_metrics TO `sales_analyst_emea`;
GRANT SELECT ON VIEW acme_gold.sales.mv_sales_metrics TO `sales_analyst_americas`;
GRANT SELECT ON VIEW acme_gold.sales.mv_sales_metrics TO `sales_analyst_europe`;
-- Genie space + AI/BI dashboard are created ON this metric view (UI/API), inheriting
-- the row filter from fact_sales_orders — regional analysts see regional metrics only.

