-- Seeds cfg.layer_mappings (Silver mappings were hardcoded — gap A1) and creates fx_rates
-- (read by silver_dlt.py but never created — gap A5). Run by scripts/deploy.py step 3.

-- FX reference (Silver reads this to normalize to USD)
CREATE TABLE IF NOT EXISTS acme_silver.sales.fx_rates (
  currency_code STRING, usd_rate DOUBLE, as_of DATE);
MERGE INTO acme_silver.sales.fx_rates t
USING (VALUES ('USD',1.00,current_date()),('EUR',1.09,current_date()),
              ('GBP',1.27,current_date()),('CAD',0.73,current_date())) s(currency_code,usd_rate,as_of)
ON t.currency_code = s.currency_code WHEN NOT MATCHED THEN INSERT *;

-- Silver mappings: one row per (src_table, src_column -> tgt column expr).
-- Change = INSERT with version+1; silver_dlt.py picks max(version) per tgt_table where valid_to IS NULL.
INSERT INTO acme_bronze.cfg.layer_mappings
  (mapping_id, layer, src_table, src_column, tgt_table, tgt_column, transform_expr, dq_rule, version, valid_from, valid_to, changed_by)
VALUES
-- SAP VBAK -> sales_order_header
 (uuid(),'silver','acme_bronze.sap.vbak','VBELN','sales_order_header','src_order_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.vbak','KUNNR','sales_order_header','src_customer_id',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.vbak','NETWR','sales_order_header','order_amount',NULL,'>= 0',1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.vbak','WAERK','sales_order_header','currency_code',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.vbak','ERDAT','sales_order_header','order_date','to_date(ERDAT)',NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.vbak',NULL,'sales_order_header','source_system',"'SAP'",NULL,1,current_timestamp(),NULL,'seed'),
-- JDE F4201 -> sales_order_header (Julian date + implied decimals)
 (uuid(),'silver','acme_bronze.jde.f4201',NULL,'sales_order_header','src_order_id',"concat_ws('-', SHKCOO, SHDOCO, SHDCTO)",'NOT NULL',1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f4201','SHAN8','sales_order_header','src_customer_id',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f4201','SHOTOT','sales_order_header','order_amount','SHOTOT/100',NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f4201','SHCRCD','sales_order_header','currency_code',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f4201','SHTRDJ','sales_order_header','order_date',"date_add(to_date('1900-01-01'), cast(SHTRDJ AS INT) - 36525)",NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f4201',NULL,'sales_order_header','source_system',"'JDE'",NULL,1,current_timestamp(),NULL,'seed'),
-- QAD so_mstr -> sales_order_header
 (uuid(),'silver','acme_bronze.qad.so_mstr','so_nbr','sales_order_header','src_order_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.qad.so_mstr','so_cust','sales_order_header','src_customer_id',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.qad.so_mstr','so_t_amt','sales_order_header','order_amount',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.qad.so_mstr','so_curr','sales_order_header','currency_code',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.qad.so_mstr','so_ord_date','sales_order_header','order_date',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.qad.so_mstr',NULL,'sales_order_header','source_system',"'QAD'",NULL,1,current_timestamp(),NULL,'seed'),
-- SAP KNA1 / JDE F0101 -> customer
 (uuid(),'silver','acme_bronze.sap.kna1','KUNNR','customer','src_customer_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.kna1','NAME1','customer','customer_name',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.kna1','LAND1','customer','country',NULL,"RLIKE '^[A-Z]{2}$'",1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.sap.kna1',NULL,'customer','source_system',"'SAP'",NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f0101','ABAN8','customer','src_customer_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f0101','ABALPH','customer','customer_name',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f0101','ABCTR','customer','country',NULL,NULL,1,current_timestamp(),NULL,'seed'),
 (uuid(),'silver','acme_bronze.jde.f0101',NULL,'customer','source_system',"'JDE'",NULL,1,current_timestamp(),NULL,'seed');

-- Pipeline registry consumed by dq/quarantine_writer.py (populated by deploy.py on pipeline create)
CREATE TABLE IF NOT EXISTS acme_bronze.cfg.pipeline_registry (
  pipeline_id STRING, pipeline_name STRING, source_name STRING,
  created_at TIMESTAMP, active BOOLEAN);

