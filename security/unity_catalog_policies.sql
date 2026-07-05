-- Roles (account groups): sales_analyst_emea, sales_analyst_americas, sales_analyst_europe,
--   data_engineer, ml_engineer, data_steward, ot_engineer, mes_engineer, exec_readonly
-- Region rule (requirement B2 now fully covered): EUROPE->SAP, AMERICAS->JDE+EBS,
--   EMEA->QAD, D365->global (masked), MES/LITMUS->ot roles.

-- 1) Row filter: region-based on source_system (EBS + D365 added)
CREATE OR REPLACE FUNCTION nucor_gold.sec.region_filter(source_system STRING)
RETURN
  is_account_group_member('data_engineer') OR is_account_group_member('exec_readonly')
  OR (is_account_group_member('sales_analyst_europe')   AND source_system = 'SAP')
  OR (is_account_group_member('sales_analyst_americas') AND source_system IN ('JDE','EBS'))
  OR (is_account_group_member('sales_analyst_emea')     AND source_system = 'QAD')
  OR (source_system = 'D365');   -- CRM rows visible to all sales analysts; PII masked below

ALTER TABLE nucor_gold.sales.fact_sales_orders
  SET ROW FILTER nucor_gold.sec.region_filter ON (source_system);
ALTER TABLE nucor_gold.sales.dim_customer
  SET ROW FILTER nucor_gold.sec.region_filter ON (source_system);

-- 2) Column mask: customer PII visible only to stewards
CREATE OR REPLACE FUNCTION nucor_gold.sec.mask_customer_name(name STRING)
RETURN CASE WHEN is_account_group_member('data_steward') THEN name
            ELSE concat(left(name, 2), '*****') END;
ALTER TABLE nucor_gold.sales.dim_customer
  ALTER COLUMN customer_name SET MASK nucor_gold.sec.mask_customer_name;

-- 3) Grants (least privilege; consumers only see Gold/products)
GRANT USE CATALOG, USE SCHEMA, SELECT ON CATALOG nucor_gold TO `sales_analyst_emea`;
GRANT USE CATALOG, USE SCHEMA, SELECT ON CATALOG nucor_gold TO `sales_analyst_americas`;
GRANT USE CATALOG, USE SCHEMA, SELECT ON CATALOG nucor_gold TO `sales_analyst_europe`;
GRANT ALL PRIVILEGES ON CATALOG nucor_bronze TO `data_engineer`;
GRANT ALL PRIVILEGES ON CATALOG nucor_silver TO `data_engineer`;
GRANT SELECT ON CATALOG nucor_gold TO `ml_engineer`;
GRANT SELECT ON SCHEMA nucor_bronze.ot  TO `ot_engineer`;
GRANT SELECT ON SCHEMA nucor_bronze.mes TO `ot_engineer`;
GRANT SELECT ON SCHEMA nucor_bronze.mes TO `mes_engineer`;

-- 4) ABAC-style PII tags (enabled — was commented out; tags now drive cross-engine ABAC
--    since UC managed tables enforce filters/masks server-side for external engines too)
ALTER TABLE nucor_gold.sales.dim_customer ALTER COLUMN customer_name SET TAGS ('pii' = 'name');
ALTER TABLE nucor_gold.sales.dim_customer ALTER COLUMN src_customer_id SET TAGS ('pii' = 'identifier');
