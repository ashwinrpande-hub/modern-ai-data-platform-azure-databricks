# Data Model — acme Sales Lakehouse (medallion architecture)

Generated 2026-08-14 directly from the live Unity Catalog metastore on `adb-7405618665227003.3.azuredatabricks.net`. Table/column inventory comes from `system.information_schema`; Bronze→Silver lineage from the live `acme_bronze.cfg.layer_mappings` config table; Gold→Products lineage from live `SHOW CREATE TABLE` DDL on each view; remaining edges (Silver internal, Silver→Gold, Gold internal) from `pipelines/silver_dlt.py` / `pipelines/gold_dlt.py` / `ml/build_features.py` / `ai/provision_vector_search.py` / `agents/vector_content.py`, all of which are the code actually deployed to this workspace.

This file is machine-generated (do not hand-edit) — regenerate with the pipeline in the Appendix below. The interactive version of the same data, with a clickable lineage diagram, is `docs/DATA_CATALOG.html`. 500-row samples of every table below live in `data/exports/excel/{bronze,silver,gold,products}.xlsx` (one workbook per layer, one sheet per table; gitignored, regenerate locally).

## Contents

| Layer | Tables/views | Notes |
|---|---|---|
| [Bronze](#bronze-layer) | 11 (+ 9 audit/cfg platform tables) | raw, source-shaped, one row per source object |
| [Silver](#silver-layer) | 10 | 3NF, insert-only, SHA-256 hash keys |
| [Gold](#gold-layer) | 11 | star schema + Data Vault 2.0 PIT/bridge + ML features + AI/vector |
| [Products](#products-layer) | 6 | governed output ports (views), published via Delta Sharing |

**47** tables/views total, **45** lineage edges, **167,431** live rows summed across all tables.

## Bronze layer

_raw, source-shaped_

### acme_bronze.sap

#### `sap.kna1`

**Type:** MANAGED · **Live rows:** 500 · **Sampled to Excel:** 500 rows · **Source:** SAP · goldengate · EUROPE

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `KUNNR` | STRING | YES |  |
| `NAME1` | STRING | YES |  |
| `LAND1` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.customer`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'sap.kna1'`

#### `sap.lips`

**Type:** MANAGED · **Live rows:** 3,478 · **Sampled to Excel:** 500 rows · **Source:** SAP · goldengate · EUROPE

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `VBELN` | STRING | YES |  |
| `POSNR` | STRING | YES |  |
| `VGBEL` | STRING | YES |  |
| `LFIMG` | STRING | YES |  |
| `ERDAT` | STRING | YES |  |
| `WERKS` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.shipment`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'sap.lips'`

#### `sap.vbak`

**Type:** MANAGED · **Live rows:** 5,000 · **Sampled to Excel:** 500 rows · **Source:** SAP · goldengate · EUROPE

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `VBELN` | STRING | YES |  |
| `KUNNR` | STRING | YES |  |
| `NETWR` | STRING | YES |  |
| `WAERK` | STRING | YES |  |
| `ERDAT` | STRING | YES |  |
| `MATNR` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.sales_order_header`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'sap.vbak'`

#### `sap.vbrp`

**Type:** MANAGED · **Live rows:** 2,767 · **Sampled to Excel:** 500 rows · **Source:** SAP · goldengate · EUROPE

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `VBELN` | STRING | YES |  |
| `POSNR` | STRING | YES |  |
| `AUBEL` | STRING | YES |  |
| `VGBEL` | STRING | YES |  |
| `NETWR` | STRING | YES |  |
| `ERDAT` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.invoice`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'sap.vbrp'`

### acme_bronze.jde

#### `jde.f0101`

**Type:** MANAGED · **Live rows:** 501 · **Sampled to Excel:** 500 rows · **Source:** JDE · goldengate · AMERICAS

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `ABAN8` | STRING | YES |  |
| `ABALPH` | STRING | YES |  |
| `ABCTR` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.customer`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'jde.f0101'`

#### `jde.f4201`

**Type:** MANAGED · **Live rows:** 5,000 · **Sampled to Excel:** 500 rows · **Source:** JDE · goldengate · AMERICAS

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `SHKCOO` | STRING | YES |  |
| `SHDOCO` | STRING | YES |  |
| `SHDCTO` | STRING | YES |  |
| `SHAN8` | STRING | YES |  |
| `SHOTOT` | STRING | YES |  |
| `SHCRCD` | STRING | YES |  |
| `SHTRDJ` | STRING | YES |  |
| `SHLITM` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.sales_order_header`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'jde.f4201'`

### acme_bronze.qad

#### `qad.so_mstr`

**Type:** MANAGED · **Live rows:** 3,000 · **Sampled to Excel:** 500 rows · **Source:** QAD · lakeflow_sqlserver · EMEA

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `so_domain` | STRING | YES |  |
| `so_nbr` | STRING | YES |  |
| `so_cust` | STRING | YES |  |
| `so_t_amt` | STRING | YES |  |
| `so_curr` | STRING | YES |  |
| `so_ord_date` | STRING | YES |  |
| `so_part` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.sales_order_header`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'qad.so_mstr'`

### acme_bronze.d365

#### `d365.salesorders`

**Type:** MANAGED · **Live rows:** 1,500 · **Sampled to Excel:** 500 rows · **Source:** D365 · lakeflow_d365 · GLOBAL · **⚠ Gap:** landed in Bronze, not yet consumed by any downstream table

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `salesorderid` | STRING | YES |  |
| `customerid` | STRING | YES |  |
| `totalamount` | STRING | YES |  |
| `transactioncurrencyid` | STRING | YES |  |
| `productcode` | STRING | YES |  |
| `modifiedon` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'd365.salesorders'`

### acme_bronze.sfdc

#### `sfdc.opportunity`

**Type:** MANAGED · **Live rows:** 2,000 · **Sampled to Excel:** 500 rows · **Source:** SALESFORCE · autoloader_file · GLOBAL · **⚠ Gap:** landed in Bronze, not yet consumed by any downstream table

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `Id` | STRING | YES |  |
| `AccountId` | STRING | YES |  |
| `Amount` | STRING | YES |  |
| `StageName` | STRING | YES |  |
| `Product__c` | STRING | YES |  |
| `SystemModstamp` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'sfdc.opportunity'`

### acme_bronze.ot

#### `ot.furnace_telemetry`

**Type:** MANAGED · **Live rows:** 648 · **Sampled to Excel:** 500 rows · **Source:** LITMUS · litmus_eventhub · AMERICAS

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `site` | STRING | YES |  |
| `asset` | STRING | YES |  |
| `tag` | STRING | YES |  |
| `ts` | TIMESTAMP | YES |  |
| `value` | DOUBLE | YES |  |
| `quality` | STRING | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.furnace_heat_5min`  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'ot.furnace_telemetry'`

### acme_bronze.mes

#### `mes.rollmill_orders`

**Type:** MANAGED · **Live rows:** 1,500 · **Sampled to Excel:** 500 rows · **Source:** MES · litmus_eventhub · AMERICAS · **⚠ Gap:** landed in Bronze, not yet consumed by any downstream table

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `topic` | STRING | YES |  |
| `work_order_id` | STRING | YES |  |
| `event` | STRING | YES |  |
| `product` | STRING | YES |  |
| `ts` | TIMESTAMP | YES |  |
| `_source_system` | STRING | YES |  |
| `_ingest_ts` | TIMESTAMP | YES |  |
| `_batch_id` | STRING | YES |  |
| `_op_type` | STRING | YES |  |
| `_seq` | LONG | YES |  |
| `_raw` | STRING | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_bronze.xlsx → sheet 'mes.rollmill_orders'`

### ⚠ Gaps in Bronze

**Landed but not yet consumed downstream** (real tables, zero rows read by Silver/Gold today):
- `acme_bronze.d365.salesorders`
- `acme_bronze.sfdc.opportunity`
- `acme_bronze.mes.rollmill_orders`

**Registered in `cfg.source_registry` but no matching table in the metastore** (config says the source should be landing; the live metastore disagrees):
- `bronze.ebs.oe_order_headers_all` — registered as `ebs_oe_order_headers` (EBS, pattern `goldengate`)
- `bronze.ebs.ra_customer_trx_all` — registered as `ebs_ra_customer_trx` (EBS, pattern `lakeflow_query`)
- `bronze.ot.caster_history` — registered as `ot_caster_history` (LITMUS, pattern `litmus_adls`)

### Platform / governance tables (acme_bronze.audit, acme_bronze.cfg)

Not part of the medallion data flow — these carry pipeline config and run audit trail. Omitted from the lineage diagram; listed here for completeness.

| Schema | Table | Type | Live rows | Comment |
|---|---|---|---|---|
| audit | `agent_reports` | MANAGED | 32 |  |
| audit | `agent_runs` | MANAGED | 36 |  |
| audit | `batch_log` | MANAGED | 0 |  |
| audit | `dq_results` | MANAGED | 70 |  |
| audit | `rejected_records` | MANAGED | 0 |  |
| cfg | `layer_mappings` | MANAGED | 40 |  |
| cfg | `pipeline_registry` | MANAGED | 0 |  |
| cfg | `product_registry` | MANAGED | 7 |  |
| cfg | `source_registry` | MANAGED | 14 |  |

## Silver layer

_3NF, insert-only, hash-keyed_

### acme_silver.sales

#### `sales.customer`

_3NF insert-only customer; config-driven; MDM survivorship in Gold_

**Type:** STREAMING_TABLE · **Live rows:** 1,001 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `country` | STRING | YES | JDE: country code (ABCTR) of the customer registered address.  \|\|  SAP: ISO-2 country code of the customer registered address (LAND1). |
| `customer_name` | STRING | YES | JDE: alpha name (ABALPH), as recorded in this source ERP, not yet resolved across sources. See dim_customer.customer_key_mdm for the cross-source entity-resolution key.  \|\|  SAP: customer legal or short name (NAME1), as recorded in this source ERP, not yet resolved across sources. See dim_customer.customer_key_mdm for the cross-source entity-resolution key. |
| `source_system` | STRING | YES | Which source ERP this customer record originated from. |
| `src_customer_id` | STRING | YES | JDE: address book number (ABAN8) representing a customer.  \|\|  SAP: customer master number (KUNNR). |
| `hk` | STRING | YES |  |
| `record_hash` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |

**Reads from:** `acme_bronze.jde.f0101`, `acme_bronze.sap.kna1`  
**Feeds:** `acme_gold.sales.dim_customer`, `acme_gold.sales.pit_customer`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.customer'`

#### `sales.furnace_heat_5min`

_5-min OT aggregates from Litmus bronze_

**Type:** STREAMING_TABLE · **Live rows:** 639 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `window_start` | TIMESTAMP | YES |  |
| `site` | STRING | YES |  |
| `asset` | STRING | YES |  |
| `tag` | STRING | YES |  |
| `avg_value` | DOUBLE | YES |  |
| `max_value` | DOUBLE | YES |  |
| `samples` | LONG | YES |  |
| `hk` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |

**Reads from:** `acme_bronze.ot.furnace_telemetry`  
**Feeds:** `acme_gold.sales.fact_heat_quality`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.furnace_heat_5min'`

#### `sales.fx_rates`

_Reference: seeded by config/seed_layer_mappings.sql_

**Type:** MATERIALIZED_VIEW · **Live rows:** 4 · **Sampled to Excel:** 4 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `currency_code` | STRING | YES |  |
| `usd_rate` | DOUBLE | YES |  |
| `as_of` | DATE | YES |  |

**Reads from:** `acme_silver.ref.fx_rates`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.fx_rates'`

#### `sales.invoice`

_3NF insert-only billing items (SAP VBRP); amount is doc-currency — join VBRK before finance use_

**Type:** STREAMING_TABLE · **Live rows:** 2,767 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `invoice_amount` | STRING | YES | SAP: net billed amount (NETWR) in the invoice document currency. This is doc-currency, not USD; join VBRK (not modeled here) for the header currency before any finance use. |
| `invoice_date` | DATE | YES | SAP: date the billing document was created (ERDAT). |
| `source_system` | STRING | YES | Which source ERP this invoice record originated from. |
| `src_invoice_id` | STRING | YES | SAP: billing document number (VBELN). |
| `src_invoice_line` | STRING | YES | SAP: billing line item number (POSNR). |
| `src_order_id` | STRING | YES | SAP: reference (AUBEL) to the originating sales order document. |
| `src_shipment_id` | STRING | YES | SAP: reference (VGBEL) to the originating delivery document, when the invoice was created with reference to a delivery. |
| `hk` | STRING | YES |  |
| `record_hash` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |

**Reads from:** `acme_bronze.sap.vbrp`  
**Feeds:** `acme_silver.sales.v_invoice_current`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.invoice'`

#### `sales.sales_order_header`

_3NF insert-only; config-driven from cfg.layer_mappings_

**Type:** STREAMING_TABLE · **Live rows:** 13,000 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `currency_code` | STRING | YES | JDE: ISO currency code of the order amount (SHCRCD).  \|\|  QAD: ISO currency code of the order amount (so_curr).  \|\|  SAP: ISO currency code of the order amount (WAERK). |
| `order_amount` | STRING | YES | JDE: order amount (SHOTOT) stored as an implied-2-decimal integer, divided by 100 here to get the true decimal amount.  \|\|  QAD: order total amount (so_t_amt), currency per so_curr.  \|\|  SAP: net order value (NETWR) in the order document currency, not yet USD; order_amount_usd is derived downstream via fx_rates. |
| `order_date` | STRING | YES | JDE: order date stored as a Julian date (CYYDDD, SHTRDJ), converted here to a calendar DATE.  \|\|  QAD: order entry date (so_ord_date).  \|\|  SAP: date the order was created (ERDAT), converted from the SAP YYYYMMDD date format. |
| `source_system` | STRING | YES | Which source ERP this order originated from, part of the natural key alongside src_order_id. |
| `src_customer_id` | STRING | YES | JDE: address book number (SHAN8) of the sold-to customer.  \|\|  QAD: customer code (so_cust) of the sold-to party.  \|\|  SAP: sold-to customer number (KUNNR); joins to customer.src_customer_id within the same source_system. |
| `src_order_id` | STRING | YES | JDE: composite order key (company, document number, document type) concatenated into one natural key, since no single JDE column uniquely identifies an order.  \|\|  QAD: sales order number (so_nbr).  \|\|  SAP: sales order document number (VBELN), the natural key for the order header. |
| `hk` | STRING | YES |  |
| `record_hash` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |
| `usd_rate` | DOUBLE | YES |  |
| `as_of` | DATE | YES |  |
| `order_amount_usd` | DOUBLE | YES |  |

**Reads from:** `acme_bronze.jde.f4201`, `acme_bronze.qad.so_mstr`, `acme_bronze.sap.vbak`, `acme_silver.ref.fx_rates`  
**Feeds:** `acme_silver.sales.v_sales_order_header_current`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.sales_order_header'`

#### `sales.shipment`

_3NF insert-only delivery items (SAP LIPS; JDE/QAD = mapping rows); config-driven_

**Type:** STREAMING_TABLE · **Live rows:** 3,478 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `plant` | STRING | YES | SAP: plant or shipping location code (WERKS). |
| `qty` | STRING | YES | SAP: delivered quantity (LFIMG) for this line, in the delivery base unit of measure. |
| `ship_date` | DATE | YES | SAP: date the delivery document was created (ERDAT). |
| `source_system` | STRING | YES | Which source ERP this shipment record originated from. |
| `src_order_id` | STRING | YES | SAP: reference (VGBEL) back to the originating sales order document number. |
| `src_shipment_id` | STRING | YES | SAP: delivery document number (VBELN). |
| `src_shipment_line` | STRING | YES | SAP: delivery line item number (POSNR) within the delivery document. |
| `hk` | STRING | YES |  |
| `record_hash` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |

**Reads from:** `acme_bronze.sap.lips`  
**Feeds:** `acme_silver.sales.v_shipment_current`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.shipment'`

#### `sales.v_invoice_current`

**Type:** MATERIALIZED_VIEW · **Live rows:** 2,767 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `invoice_amount` | STRING | YES |  |
| `invoice_date` | DATE | YES |  |
| `source_system` | STRING | YES |  |
| `src_invoice_id` | STRING | YES |  |
| `src_invoice_line` | STRING | YES |  |
| `src_order_id` | STRING | YES |  |
| `src_shipment_id` | STRING | YES |  |
| `hk` | STRING | YES |  |
| `record_hash` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |

**Reads from:** `acme_silver.sales.invoice`  
**Feeds:** `acme_gold.sales.bridge_order_fulfillment`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.v_invoice_current'`

#### `sales.v_sales_order_header_current`

**Type:** MATERIALIZED_VIEW · **Live rows:** 13,000 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `currency_code` | STRING | YES |  |
| `order_amount` | STRING | YES |  |
| `order_date` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `src_customer_id` | STRING | YES |  |
| `src_order_id` | STRING | YES |  |
| `hk` | STRING | YES |  |
| `record_hash` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |
| `usd_rate` | DOUBLE | YES |  |
| `as_of` | DATE | YES |  |
| `order_amount_usd` | DOUBLE | YES |  |

**Reads from:** `acme_silver.sales.sales_order_header`  
**Feeds:** `acme_gold.sales.bridge_order_fulfillment`, `acme_gold.sales.fact_sales_orders`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.v_sales_order_header_current'`

#### `sales.v_shipment_current`

**Type:** MATERIALIZED_VIEW · **Live rows:** 3,478 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `plant` | STRING | YES |  |
| `qty` | STRING | YES |  |
| `ship_date` | DATE | YES |  |
| `source_system` | STRING | YES |  |
| `src_order_id` | STRING | YES |  |
| `src_shipment_id` | STRING | YES |  |
| `src_shipment_line` | STRING | YES |  |
| `hk` | STRING | YES |  |
| `record_hash` | STRING | YES |  |
| `effective_ts` | TIMESTAMP | YES |  |

**Reads from:** `acme_silver.sales.shipment`  
**Feeds:** `acme_gold.sales.bridge_order_fulfillment`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'sales.v_shipment_current'`

### acme_silver.ref

#### `ref.fx_rates`

**Type:** MANAGED · **Live rows:** 4 · **Sampled to Excel:** 4 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `currency_code` | STRING | YES |  |
| `usd_rate` | DOUBLE | YES |  |
| `as_of` | DATE | YES |  |

**Reads from:** _none — landing table_  
**Feeds:** `acme_silver.sales.fx_rates`, `acme_silver.sales.sales_order_header`  

**Sample data:** `data/exports/excel/acme_silver.xlsx → sheet 'ref.fx_rates'`

## Gold layer

_star schema + DV2.0 + ML/AI_

### acme_gold.sales

#### `sales.agg_sales_daily`

_Pre-aggregated for AI/BI dashboards + Genie_

**Type:** MATERIALIZED_VIEW · **Live rows:** 1,499 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `order_date` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `revenue_usd` | DOUBLE | YES |  |
| `orders` | LONG | YES |  |

**Reads from:** `acme_gold.sales.fact_sales_orders`  
**Feeds:** `acme_products.ops.v_melt_to_margin`  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.agg_sales_daily'`

#### `sales.bridge_order_fulfillment`

_DV2.0 bridge: order->shipment->invoice hash keys + lifecycle dates/flags. Grain: one row per current order. One join for O2C, backlog, Genie._

**Type:** MATERIALIZED_VIEW · **Live rows:** 13,000 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `order_hk` | STRING | YES |  |
| `customer_hk` | STRING | YES |  |
| `shipment_hk` | STRING | YES |  |
| `invoice_hk` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `order_date` | STRING | YES |  |
| `ship_date` | DATE | YES |  |
| `invoice_date` | DATE | YES |  |
| `is_shipped` | BOOLEAN | YES |  |
| `is_invoiced` | BOOLEAN | YES |  |

**Reads from:** `acme_gold.sales.dim_customer`, `acme_silver.sales.v_invoice_current`, `acme_silver.sales.v_sales_order_header_current`, `acme_silver.sales.v_shipment_current`  
**Feeds:** `acme_gold.ml.customer_features`, `acme_gold.sales.customer_narratives`, `acme_products.sales.order_to_cash`, `acme_products.sales.v_customer_360`, `acme_products.sales.v_sales_orders_unified`  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.bridge_order_fulfillment'`

#### `sales.customer_narratives`

**Type:** MANAGED · **Live rows:** 1,001 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `customer_hk` | STRING | YES |  |
| `customer_name` | STRING | YES |  |
| `narrative` | STRING | YES |  |

**Reads from:** `acme_gold.sales.bridge_order_fulfillment`, `acme_gold.sales.dim_customer`  
**Feeds:** `acme_gold.ai.customer_profile_text`, `acme_products.sales.v_customer_360`  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.customer_narratives'`

#### `sales.dim_customer`

_MDM-survived customer dim; PK = customer_hk_

**Type:** MATERIALIZED_VIEW · **Live rows:** 1,001 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `customer_hk` | STRING | YES |  |
| `src_customer_id` | STRING | YES |  |
| `customer_name` | STRING | YES |  |
| `country` | STRING | YES |  |
| `source_system` | STRING | YES |  |

**Reads from:** `acme_silver.sales.customer`  
**Feeds:** `acme_gold.sales.bridge_order_fulfillment`, `acme_gold.sales.customer_narratives`, `acme_gold.sales.fact_sales_orders`, `acme_products.sales.order_to_cash`, `acme_products.sales.v_customer_360`, `acme_products.sales.v_sales_orders_unified`  

**Governance:**
- Row filter: acme_gold.sec.region_filter ON (source_system) — analysts see only their region
- Column mask: customer_name → acme_gold.sec.mask_customer_name (visible unmasked only to data_steward)
- PII tags: customer_name='name', src_customer_id='identifier'

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.dim_customer'`

#### `sales.fact_heat_quality`

_OT-to-business: furnace conditions joined to daily shipped tonnage_

**Type:** MATERIALIZED_VIEW · **Live rows:** 639 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `heat_hk` | STRING | YES |  |
| `site` | STRING | YES |  |
| `asset` | STRING | YES |  |
| `tag` | STRING | YES |  |
| `window_start` | TIMESTAMP | YES |  |
| `avg_value` | DOUBLE | YES |  |
| `max_value` | DOUBLE | YES |  |

**Reads from:** `acme_silver.sales.furnace_heat_5min`  
**Feeds:** `acme_products.ops.v_melt_to_margin`  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.fact_heat_quality'`

#### `sales.fact_sales_orders`

_Grain: one row per order per source; FKs are hash keys_

**Type:** MATERIALIZED_VIEW · **Live rows:** 13,000 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `order_hk` | STRING | YES |  |
| `customer_hk` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `order_date` | STRING | YES |  |
| `order_amount_usd` | DOUBLE | YES |  |
| `currency_code` | STRING | YES |  |

**Reads from:** `acme_gold.sales.dim_customer`, `acme_silver.sales.v_sales_order_header_current`  
**Feeds:** `acme_gold.ml.customer_features`, `acme_gold.sales.agg_sales_daily`, `acme_gold.sales.mv_sales_metrics`, `acme_products.sales.order_to_cash`, `acme_products.sales.v_customer_360`, `acme_products.sales.v_sales_orders`, `acme_products.sales.v_sales_orders_unified`  

**Governance:**
- Row filter: acme_gold.sec.region_filter ON (source_system)

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.fact_sales_orders'`

#### `sales.mv_sales_metrics`

**Type:** METRIC_VIEW · **Live rows:** 13,000 · **Sampled to Excel:** 0 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `order_date` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `revenue_usd` | DOUBLE | YES |  |
| `order_count` | LONG | NO |  |
| `avg_order_value` | DOUBLE | YES |  |

**Reads from:** `acme_gold.sales.fact_sales_orders`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.mv_sales_metrics'`

#### `sales.pit_customer`

_DV2.0 PIT: (snapshot_date, customer_hk) -> as_of_ts of the Silver version current that day. Equality as-of joins; no BETWEEN scans, no label leakage._

**Type:** MATERIALIZED_VIEW · **Live rows:** 16,016 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `snapshot_date` | DATE | YES |  |
| `customer_hk` | STRING | YES |  |
| `as_of_ts` | TIMESTAMP | YES |  |
| `source_system` | STRING | YES |  |

**Reads from:** `acme_silver.sales.customer`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'sales.pit_customer'`

### acme_gold.ml

#### `ml.customer_features`

**Type:** MANAGED · **Live rows:** 1,001 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `customer_hk` | STRING | NO |  |
| `as_of_date` | DATE | NO |  |
| `rev_l30d_usd` | DOUBLE | YES |  |
| `rev_l90d_usd` | DOUBLE | YES |  |
| `rev_l365d_usd` | DOUBLE | YES |  |
| `order_cnt_l365d` | LONG | YES |  |
| `days_since_last_order` | INT | YES |  |
| `backlog_orders` | LONG | YES |  |
| `churn_risk_score` | DOUBLE | YES |  |
| `feature_ts` | TIMESTAMP | YES |  |

**Reads from:** `acme_gold.sales.bridge_order_fulfillment`, `acme_gold.sales.fact_sales_orders`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'ml.customer_features'`

### acme_gold.ai

#### `ai.customer_profile_idx`

_Managed Vector Index with Delta Sync_

**Type:** FOREIGN · **Live rows:** n/a · **Sampled to Excel:** 0 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `customer_hk` | STRING | YES |  |
| `profile_text` | STRING | YES |  |
| `__db_profile_text_vector` | ARRAY | YES |  |

**Reads from:** `acme_gold.ai.customer_profile_text`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'ai.customer_profile_idx'`

#### `ai.customer_profile_text`

**Type:** MANAGED · **Live rows:** 1,001 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `customer_hk` | STRING | YES |  |
| `profile_text` | STRING | YES |  |

**Reads from:** `acme_gold.sales.customer_narratives`  
**Feeds:** `acme_gold.ai.customer_profile_idx`  

**Sample data:** `data/exports/excel/acme_gold.xlsx → sheet 'ai.customer_profile_text'`

## Products layer

_governed output ports_

### acme_products.sales

#### `sales.order_to_cash`

**Type:** VIEW · **Live rows:** 13,000 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `order_id` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `order_date` | DATE | YES |  |
| `customer_name` | STRING | YES |  |
| `country` | STRING | YES |  |
| `order_amount_usd` | DOUBLE | YES |  |
| `currency_code` | STRING | YES |  |
| `is_shipped` | BOOLEAN | NO |  |
| `is_invoiced` | BOOLEAN | NO |  |
| `ship_date` | DATE | YES |  |
| `invoice_date` | DATE | YES |  |
| `lifecycle_status` | STRING | NO |  |

**Reads from:** `acme_gold.sales.bridge_order_fulfillment`, `acme_gold.sales.dim_customer`, `acme_gold.sales.fact_sales_orders`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_products.xlsx → sheet 'sales.order_to_cash'`

#### `sales.v_customer_360`

_DATA PRODUCT customer_360 | owner: sales-data-team | SLA: 60-min freshness, 99.5% | masked PII + row filter inherit from dim_customer_

**Type:** VIEW · **Live rows:** 1,001 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `customer_hk` | STRING | YES |  |
| `customer_name` | STRING | YES |  |
| `country` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `narrative` | STRING | YES |  |
| `orders` | LONG | YES |  |
| `revenue_usd` | DOUBLE | YES |  |
| `backlog_orders` | LONG | YES |  |
| `last_order_date` | STRING | YES |  |
| `days_since_last_order` | INT | YES |  |

**Reads from:** `acme_gold.sales.bridge_order_fulfillment`, `acme_gold.sales.customer_narratives`, `acme_gold.sales.dim_customer`, `acme_gold.sales.fact_sales_orders`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_products.xlsx → sheet 'sales.v_customer_360'`

#### `sales.v_sales_orders`

_DATA PRODUCT sales_orders_unified | owner: sales-data-team | SLA: 30-min freshness, 99.5% | trust score: acme_products.meta.v_product_trust_scores_

**Type:** VIEW · **Live rows:** 13,000 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `order_hk` | STRING | YES |  |
| `customer_hk` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `order_date` | STRING | YES |  |
| `order_amount_usd` | DOUBLE | YES |  |

**Reads from:** `acme_gold.sales.fact_sales_orders`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_products.xlsx → sheet 'sales.v_sales_orders'`

#### `sales.v_sales_orders_unified`

**Type:** VIEW · **Live rows:** 13,000 · **Sampled to Excel:** 500 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `order_hk` | STRING | YES |  |
| `customer_name` | STRING | YES |  |
| `country` | STRING | YES |  |
| `source_system` | STRING | YES |  |
| `order_date` | STRING | YES |  |
| `order_amount_usd` | DOUBLE | YES |  |
| `currency_code` | STRING | YES |  |
| `ship_date` | DATE | YES |  |
| `invoice_date` | DATE | YES |  |
| `is_shipped` | BOOLEAN | YES |  |
| `is_invoiced` | BOOLEAN | YES |  |

**Reads from:** `acme_gold.sales.bridge_order_fulfillment`, `acme_gold.sales.dim_customer`, `acme_gold.sales.fact_sales_orders`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_products.xlsx → sheet 'sales.v_sales_orders_unified'`

### acme_products.ops

#### `ops.v_melt_to_margin`

_DATA PRODUCT melt_to_margin | owner: ot-data-team | SLA: 15-min freshness, 99.0% | OT furnace conditions joined to daily revenue_

**Type:** VIEW · **Live rows:** 36 · **Sampled to Excel:** 36 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `site` | STRING | YES |  |
| `asset` | STRING | YES |  |
| `tag` | STRING | YES |  |
| `heat_date` | DATE | YES |  |
| `avg_reading` | DOUBLE | YES |  |
| `peak_reading` | DOUBLE | YES |  |
| `revenue_usd` | DOUBLE | YES |  |
| `orders` | LONG | YES |  |

**Reads from:** `acme_gold.sales.agg_sales_daily`, `acme_gold.sales.fact_heat_quality`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_products.xlsx → sheet 'ops.v_melt_to_margin'`

### acme_products.meta

#### `meta.v_product_trust_scores`

**Type:** VIEW · **Live rows:** 5 · **Sampled to Excel:** 5 rows

| Column | Type | Nullable | Comment |
|---|---|---|---|
| `product_name` | STRING | YES |  |
| `view_name` | STRING | YES |  |
| `trust_score` | DECIMAL | YES |  |
| `checks_evaluated` | LONG | NO |  |

**Reads from:** `acme_bronze.audit.dq_results`, `acme_bronze.cfg.product_registry`  
**Feeds:** _none — terminal / not yet consumed_  

**Sample data:** `data/exports/excel/acme_products.xlsx → sheet 'meta.v_product_trust_scores'`

## Appendix — regenerating this file

```
# 1. discover schema + pull row counts / 500-row samples (needs databricks-connect serverless)
DATABRICKS_CONFIG_PROFILE=<profile> DATABRICKS_CLI_PATH=<databricks.exe> \
  python scripts/extract_data_model.py   # discovery + row counts + samples + config lineage
# 2. build the per-layer Excel workbooks (pure pandas/openpyxl, no Spark needed)
python scripts/build_excel_exports.py
# 3. regenerate this file + docs/DATA_CATALOG.html from the extraction output
python scripts/generate_data_docs.py
```
