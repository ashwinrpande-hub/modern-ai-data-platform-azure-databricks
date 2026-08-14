-- Trace ONE order from its raw source-system CSV row (Bronze) through the DV2.0-style hash
-- key (Silver) to the star schema and query-assist tables (Gold).
--
-- To trace a different order: change source_system/src_order_id in the `target` CTE at the
-- top of each step below (they must match, since the hash key is deterministic:
-- hk = sha2(concat_ws('|', source_system, src_order_id), 256) -- see pipelines/silver_dlt.py).
-- Worked example here is SAP order VBELN = 004002000, which has a matching shipment (LIPS)
-- and invoice (VBRP), i.e. a fully closed order-to-cash lifecycle.

-- ============ STEP 1: Bronze -- raw rows as they landed from source ============
-- Order header (SAP VBAK)
SELECT VBELN, KUNNR, NETWR, WAERK, ERDAT, MATNR, _source_system, _ingest_ts
FROM acme_bronze.sap.vbak
WHERE VBELN = '004002000';

-- Related shipment line (SAP LIPS, joined on VGBEL = order number)
SELECT VBELN AS delivery_id, POSNR, VGBEL AS order_id, LFIMG AS qty, ERDAT AS ship_date, WERKS AS plant
FROM acme_bronze.sap.lips
WHERE VGBEL = '004002000';

-- Related invoice line (SAP VBRP, joined on AUBEL = order number)
SELECT VBELN AS invoice_id, POSNR, AUBEL AS order_id, VGBEL AS delivery_id, NETWR AS amount, ERDAT AS invoice_date
FROM acme_bronze.sap.vbrp
WHERE AUBEL = '004002000';

-- ============ STEP 2: Silver -- hashed, normalized, FX-converted, insert-only ============
WITH target AS (SELECT 'SAP' AS source_system, '004002000' AS src_order_id)
SELECT s.hk, s.src_order_id, s.source_system, s.order_amount, s.order_amount_usd,
       s.currency_code, s.order_date, s.effective_ts, s.record_hash
FROM acme_silver.sales.sales_order_header s, target t
WHERE s.hk = sha2(concat_ws('|', t.source_system, t.src_order_id), 256);

-- The "current" view of the same row (latest version per hk -- matters once history has
-- multiple versions; with a single load batch it's identical to Step 2 today)
WITH target AS (SELECT 'SAP' AS source_system, '004002000' AS src_order_id)
SELECT v.* FROM acme_silver.sales.v_sales_order_header_current v, target t
WHERE v.hk = sha2(concat_ws('|', t.source_system, t.src_order_id), 256);

-- ============ STEP 3: Gold -- star schema fact, joined to its customer dimension ============
WITH target AS (SELECT 'SAP' AS source_system, '004002000' AS src_order_id)
SELECT f.order_hk, f.customer_hk, f.source_system, f.order_date, f.order_amount_usd, f.currency_code,
       d.src_customer_id, d.customer_name, d.country
FROM acme_gold.sales.fact_sales_orders f
JOIN acme_gold.sales.dim_customer d ON d.customer_hk = f.customer_hk
, target t
WHERE f.order_hk = sha2(concat_ws('|', t.source_system, t.src_order_id), 256);

-- ============ STEP 4: Gold DV2.0 bridge -- order -> shipment -> invoice, one row ============
WITH target AS (SELECT 'SAP' AS source_system, '004002000' AS src_order_id)
SELECT b.* FROM acme_gold.sales.bridge_order_fulfillment b, target t
WHERE b.order_hk = sha2(concat_ws('|', t.source_system, t.src_order_id), 256);

-- ============ STEP 5: Gold DV2.0 PIT -- customer's as-of state for today's snapshot ============
-- NOTE: this demo's synthetic data was loaded in a single batch, so pit_customer currently
-- only has one snapshot_date (today, via current_date()) rather than real history back to the
-- order date -- that's expected for a one-shot seed, not a bug.
WITH target AS (SELECT 'SAP' AS source_system, '004002000' AS src_order_id),
     ord AS (
       SELECT customer_hk FROM acme_gold.sales.fact_sales_orders f, target t
       WHERE f.order_hk = sha2(concat_ws('|', t.source_system, t.src_order_id), 256)
     )
SELECT p.* FROM acme_gold.sales.pit_customer p
JOIN ord ON ord.customer_hk = p.customer_hk
WHERE p.snapshot_date = current_date();

-- ============ STEP 6: Gold aggregate -- the daily rollup this order contributes to ============
WITH target AS (SELECT 'SAP' AS source_system, '004002000' AS src_order_id),
     ord AS (
       SELECT f.order_date, f.source_system FROM acme_gold.sales.fact_sales_orders f, target t
       WHERE f.order_hk = sha2(concat_ws('|', t.source_system, t.src_order_id), 256)
     )
SELECT a.* FROM acme_gold.sales.agg_sales_daily a
JOIN ord ON ord.order_date = a.order_date AND ord.source_system = a.source_system;

-- ============ STEP 7: Gold entity resolution -- this customer's cross-source match key ============
-- NEW 2026-08-14: dim_customer.customer_key_mdm = sha2(normalized_name|normalized_country, 256)
-- -- the first (deterministic exact-match) tier of MDM. See pipelines/gold_dlt.py and
-- docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md for the honestly-scoped story: exact-match
-- only, fuzzy/probabilistic matching (Zingg/Splink) named as the production upgrade path, not
-- built. customer_hk stays the stable per-source FK grain every fact joins on; customer_key_mdm
-- is the separate, actual cross-source identity key.

-- 7a. This order's customer -- the normalized inputs that produced its match key
WITH target AS (SELECT 'SAP' AS source_system, '004002000' AS src_order_id),
     ord AS (
       SELECT customer_hk FROM acme_gold.sales.fact_sales_orders f, target t
       WHERE f.order_hk = sha2(concat_ws('|', t.source_system, t.src_order_id), 256)
     )
SELECT d.customer_hk, d.customer_key_mdm, d.customer_name, d.country, d.source_system
FROM acme_gold.sales.dim_customer d
JOIN ord ON ord.customer_hk = d.customer_hk;

-- 7b. The intended use: every customer_hk sharing this match key is the same real-world
-- customer, however many ERPs it was scraped from. For this order's customer, expect exactly
-- 1 row back -- not because the logic is broken, see 7c for why.
WITH this_customer AS (
  SELECT customer_key_mdm FROM acme_gold.sales.dim_customer WHERE customer_hk = (
    SELECT customer_hk FROM acme_gold.sales.fact_sales_orders
    WHERE order_hk = sha2(concat_ws('|', 'SAP', '004002000'), 256))
)
SELECT d.customer_hk, d.customer_name, d.country, d.source_system
FROM acme_gold.sales.dim_customer d, this_customer c
WHERE d.customer_key_mdm = c.customer_key_mdm;

-- 7c. Platform-wide, honest proof of scope: every match key mapping to MORE than one
-- customer_hk is a resolved cross-source duplicate. As of 2026-08-14 this returns zero rows --
-- not a bug. scripts/generate_synthetic_data.py creates each customer once, in one source
-- system, so there's nothing to collapse yet (1,001 rows in, 1,001 distinct keys out, verified
-- live). This query is what would prove the key *also* resolves duplicates, the day the data
-- has any -- today it only proves the key computes and is unique per row.
SELECT customer_key_mdm, count(*) AS customer_hk_count,
       collect_list(source_system) AS source_systems,
       collect_list(customer_name) AS customer_names
FROM acme_gold.sales.dim_customer
GROUP BY customer_key_mdm
HAVING count(*) > 1
ORDER BY customer_hk_count DESC;
