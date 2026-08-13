-- Seeds cfg.layer_mappings (Silver mappings were hardcoded - gap A1) and creates fx_rates
-- (read by silver_dlt.py but never created - gap A5). Run by scripts/deploy.py step 3.

-- FX reference (Silver reads this to normalize to USD). Lives in "ref", not "sales" -- "sales"
-- is the silver_dlt.py pipeline's own publish target, and a table of the same fully qualified
-- name there would make the pipeline's own fx_rates dataset self-referential.
CREATE SCHEMA IF NOT EXISTS acme_silver.ref;
CREATE TABLE IF NOT EXISTS acme_silver.ref.fx_rates (
  currency_code STRING, usd_rate DOUBLE, as_of DATE);
CREATE OR REPLACE TEMP VIEW fx_seed(currency_code, usd_rate, as_of) AS
VALUES ('USD',1.00,current_date()),('EUR',1.09,current_date()),
       ('GBP',1.27,current_date()),('CAD',0.73,current_date());
MERGE INTO acme_silver.ref.fx_rates t
USING fx_seed s
ON t.currency_code = s.currency_code WHEN NOT MATCHED THEN INSERT *;

-- Silver mappings: one row per (src_table, src_column -> tgt column expr).
-- Change = INSERT with version+1; silver_dlt.py picks max(version) per tgt_table where valid_to IS NULL.
-- business_definition is the column's business meaning, applied as a UC column COMMENT by
-- scripts/apply_column_comments.py (one row per source contributing to a tgt_column; the
-- script concatenates distinct definitions so multi-source nuance (e.g. JDEs Julian date,
-- SAPs doc-currency caveat) survives into the single comment UC allows per column).
-- NOTE: definitions are deliberately plain ASCII, no apostrophes and no em-dashes - this
-- workspaces databricks-connect session was observed silently dropping escaped doubled-quote
-- sequences and mangling non-ASCII characters in VALUES-clause string literals.
INSERT INTO acme_bronze.cfg.layer_mappings
  (mapping_id, layer, src_table, src_column, tgt_table, tgt_column, transform_expr, dq_rule, version, valid_from, valid_to, changed_by, business_definition)
SELECT uuid(), t.layer, t.src_table, t.src_column, t.tgt_table, t.tgt_column, t.transform_expr, t.dq_rule, t.version, t.valid_from, t.valid_to, t.changed_by, t.business_definition
FROM (VALUES
-- SAP VBAK -> sales_order_header
 (NULL,'silver','acme_bronze.sap.vbak','VBELN','sales_order_header','src_order_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','SAP: sales order document number (VBELN), the natural key for the order header.'),
 (NULL,'silver','acme_bronze.sap.vbak','KUNNR','sales_order_header','src_customer_id',NULL,NULL,1,current_timestamp(),NULL,'seed','SAP: sold-to customer number (KUNNR); joins to customer.src_customer_id within the same source_system.'),
 (NULL,'silver','acme_bronze.sap.vbak','NETWR','sales_order_header','order_amount',NULL,'>= 0',1,current_timestamp(),NULL,'seed','SAP: net order value (NETWR) in the order document currency, not yet USD; order_amount_usd is derived downstream via fx_rates.'),
 (NULL,'silver','acme_bronze.sap.vbak','WAERK','sales_order_header','currency_code',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','SAP: ISO currency code of the order amount (WAERK).'),
 (NULL,'silver','acme_bronze.sap.vbak','ERDAT','sales_order_header','order_date','to_date(ERDAT)',NULL,1,current_timestamp(),NULL,'seed','SAP: date the order was created (ERDAT), converted from the SAP YYYYMMDD date format.'),
 (NULL,'silver','acme_bronze.sap.vbak',NULL,'sales_order_header','source_system',"'SAP'",NULL,1,current_timestamp(),NULL,'seed','Which source ERP this order originated from, part of the natural key alongside src_order_id.'),
-- JDE F4201 -> sales_order_header (Julian date + implied decimals)
 (NULL,'silver','acme_bronze.jde.f4201',NULL,'sales_order_header','src_order_id',"concat_ws('-', SHKCOO, SHDOCO, SHDCTO)",'NOT NULL',1,current_timestamp(),NULL,'seed','JDE: composite order key (company, document number, document type) concatenated into one natural key, since no single JDE column uniquely identifies an order.'),
 (NULL,'silver','acme_bronze.jde.f4201','SHAN8','sales_order_header','src_customer_id',NULL,NULL,1,current_timestamp(),NULL,'seed','JDE: address book number (SHAN8) of the sold-to customer.'),
 (NULL,'silver','acme_bronze.jde.f4201','SHOTOT','sales_order_header','order_amount','SHOTOT/100',NULL,1,current_timestamp(),NULL,'seed','JDE: order amount (SHOTOT) stored as an implied-2-decimal integer, divided by 100 here to get the true decimal amount.'),
 (NULL,'silver','acme_bronze.jde.f4201','SHCRCD','sales_order_header','currency_code',NULL,NULL,1,current_timestamp(),NULL,'seed','JDE: ISO currency code of the order amount (SHCRCD).'),
 (NULL,'silver','acme_bronze.jde.f4201','SHTRDJ','sales_order_header','order_date',"date_add(to_date('1900-01-01'), cast(SHTRDJ AS INT) - 36525)",NULL,1,current_timestamp(),NULL,'seed','JDE: order date stored as a Julian date (CYYDDD, SHTRDJ), converted here to a calendar DATE.'),
 (NULL,'silver','acme_bronze.jde.f4201',NULL,'sales_order_header','source_system',"'JDE'",NULL,1,current_timestamp(),NULL,'seed','Which source ERP this order originated from, part of the natural key alongside src_order_id.'),
-- QAD so_mstr -> sales_order_header
 (NULL,'silver','acme_bronze.qad.so_mstr','so_nbr','sales_order_header','src_order_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','QAD: sales order number (so_nbr).'),
 (NULL,'silver','acme_bronze.qad.so_mstr','so_cust','sales_order_header','src_customer_id',NULL,NULL,1,current_timestamp(),NULL,'seed','QAD: customer code (so_cust) of the sold-to party.'),
 (NULL,'silver','acme_bronze.qad.so_mstr','so_t_amt','sales_order_header','order_amount',NULL,NULL,1,current_timestamp(),NULL,'seed','QAD: order total amount (so_t_amt), currency per so_curr.'),
 (NULL,'silver','acme_bronze.qad.so_mstr','so_curr','sales_order_header','currency_code',NULL,NULL,1,current_timestamp(),NULL,'seed','QAD: ISO currency code of the order amount (so_curr).'),
 (NULL,'silver','acme_bronze.qad.so_mstr','so_ord_date','sales_order_header','order_date',NULL,NULL,1,current_timestamp(),NULL,'seed','QAD: order entry date (so_ord_date).'),
 (NULL,'silver','acme_bronze.qad.so_mstr',NULL,'sales_order_header','source_system',"'QAD'",NULL,1,current_timestamp(),NULL,'seed','Which source ERP this order originated from, part of the natural key alongside src_order_id.'),
-- SAP KNA1 / JDE F0101 -> customer
 (NULL,'silver','acme_bronze.sap.kna1','KUNNR','customer','src_customer_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','SAP: customer master number (KUNNR).'),
 (NULL,'silver','acme_bronze.sap.kna1','NAME1','customer','customer_name',NULL,NULL,1,current_timestamp(),NULL,'seed','SAP: customer legal or short name (NAME1), as recorded in this source ERP, not yet resolved across sources. See dim_customer.customer_key_mdm for the cross-source entity-resolution key.'),
 (NULL,'silver','acme_bronze.sap.kna1','LAND1','customer','country',NULL,"RLIKE '^[A-Z]{2}$'",1,current_timestamp(),NULL,'seed','SAP: ISO-2 country code of the customer registered address (LAND1).'),
 (NULL,'silver','acme_bronze.sap.kna1',NULL,'customer','source_system',"'SAP'",NULL,1,current_timestamp(),NULL,'seed','Which source ERP this customer record originated from.'),
 (NULL,'silver','acme_bronze.jde.f0101','ABAN8','customer','src_customer_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','JDE: address book number (ABAN8) representing a customer.'),
 (NULL,'silver','acme_bronze.jde.f0101','ABALPH','customer','customer_name',NULL,NULL,1,current_timestamp(),NULL,'seed','JDE: alpha name (ABALPH), as recorded in this source ERP, not yet resolved across sources. See dim_customer.customer_key_mdm for the cross-source entity-resolution key.'),
 (NULL,'silver','acme_bronze.jde.f0101','ABCTR','customer','country',NULL,NULL,1,current_timestamp(),NULL,'seed','JDE: country code (ABCTR) of the customer registered address.'),
 (NULL,'silver','acme_bronze.jde.f0101',NULL,'customer','source_system',"'JDE'",NULL,1,current_timestamp(),NULL,'seed','Which source ERP this customer record originated from.'),
-- SAP LIPS (delivery item) -> shipment  [DV2.0 bridge lifecycle; SAP-only pilot -- JDE/QAD = new rows here]
 (NULL,'silver','acme_bronze.sap.lips','VBELN','shipment','src_shipment_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','SAP: delivery document number (VBELN).'),
 (NULL,'silver','acme_bronze.sap.lips','POSNR','shipment','src_shipment_line',NULL,NULL,1,current_timestamp(),NULL,'seed','SAP: delivery line item number (POSNR) within the delivery document.'),
 (NULL,'silver','acme_bronze.sap.lips','VGBEL','shipment','src_order_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','SAP: reference (VGBEL) back to the originating sales order document number.'),
 (NULL,'silver','acme_bronze.sap.lips','LFIMG','shipment','qty',NULL,'>= 0',1,current_timestamp(),NULL,'seed','SAP: delivered quantity (LFIMG) for this line, in the delivery base unit of measure.'),
 (NULL,'silver','acme_bronze.sap.lips','ERDAT','shipment','ship_date','to_date(ERDAT)',NULL,1,current_timestamp(),NULL,'seed','SAP: date the delivery document was created (ERDAT).'),
 (NULL,'silver','acme_bronze.sap.lips','WERKS','shipment','plant',NULL,NULL,1,current_timestamp(),NULL,'seed','SAP: plant or shipping location code (WERKS).'),
 (NULL,'silver','acme_bronze.sap.lips',NULL,'shipment','source_system',"'SAP'",NULL,1,current_timestamp(),NULL,'seed','Which source ERP this shipment record originated from.'),
-- SAP VBRP (billing item) -> invoice  [amount is doc-currency; VBRK header join needed before finance use]
 (NULL,'silver','acme_bronze.sap.vbrp','VBELN','invoice','src_invoice_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','SAP: billing document number (VBELN).'),
 (NULL,'silver','acme_bronze.sap.vbrp','POSNR','invoice','src_invoice_line',NULL,NULL,1,current_timestamp(),NULL,'seed','SAP: billing line item number (POSNR).'),
 (NULL,'silver','acme_bronze.sap.vbrp','AUBEL','invoice','src_order_id',NULL,'NOT NULL',1,current_timestamp(),NULL,'seed','SAP: reference (AUBEL) to the originating sales order document.'),
 (NULL,'silver','acme_bronze.sap.vbrp','VGBEL','invoice','src_shipment_id',NULL,NULL,1,current_timestamp(),NULL,'seed','SAP: reference (VGBEL) to the originating delivery document, when the invoice was created with reference to a delivery.'),
 (NULL,'silver','acme_bronze.sap.vbrp','NETWR','invoice','invoice_amount',NULL,'>= 0',1,current_timestamp(),NULL,'seed','SAP: net billed amount (NETWR) in the invoice document currency. This is doc-currency, not USD; join VBRK (not modeled here) for the header currency before any finance use.'),
 (NULL,'silver','acme_bronze.sap.vbrp','ERDAT','invoice','invoice_date','to_date(ERDAT)',NULL,1,current_timestamp(),NULL,'seed','SAP: date the billing document was created (ERDAT).'),
 (NULL,'silver','acme_bronze.sap.vbrp',NULL,'invoice','source_system',"'SAP'",NULL,1,current_timestamp(),NULL,'seed','Which source ERP this invoice record originated from.')
) AS t(mapping_id, layer, src_table, src_column, tgt_table, tgt_column, transform_expr, dq_rule, version, valid_from, valid_to, changed_by, business_definition);

-- Pipeline registry consumed by dq/quarantine_writer.py (populated by deploy.py on pipeline create)
CREATE TABLE IF NOT EXISTS acme_bronze.cfg.pipeline_registry (
  pipeline_id STRING, pipeline_name STRING, source_name STRING,
  created_at TIMESTAMP, active BOOLEAN);
