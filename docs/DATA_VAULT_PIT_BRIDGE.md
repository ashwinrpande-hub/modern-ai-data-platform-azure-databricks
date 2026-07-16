# Data Vault 2.0 — PIT & Bridge use cases in Gold

How DV2.0 concepts map onto this lakehouse (methodology adopted; hub/link/sat objects not
materialized — reasoning in JUSTIFICATION_NOTES #5):

| DV2.0 concept | Here |
|---|---|
| Hub business key (hashed) | Silver `hk = sha2(source_system\|pk, 256)` |
| Satellite (history, hashdiff) | Silver insert-only versions: `effective_ts`, `record_hash` |
| Link | Virtual — hash-key FKs inside 3NF entities |
| PIT table | `nucor_gold.sales.pit_customer` |
| Bridge table | `nucor_gold.sales.bridge_order_fulfillment` |
| Information mart | Gold star (dims/facts) + aggs |

## Use case 1 — `pit_customer` (point-in-time)
**Grain:** one row per `(snapshot_date, customer_hk)`; `as_of_ts` points at the Silver customer
version that was current on that date. Daily spine from first customer version to today.

Solves: "history is cheap to store, expensive to query." Without PIT, every as-of question is a
range join over all versions — easy to write wrong (label leakage) and slow at scale.

1. **Leakage-free ML training sets** — `ml/feature_store.py` joins labels to features via
   `pit_customer` at `label_date`; the model never sees attributes newer than the label.
2. **Reproducible month-end reporting** — re-running a January report in July returns January's
   customer attributes (name/country/region as they were), not today's.
3. **Audit / region policy evidence** — prove which region row-filter applied to a customer on a
   given date (source_system was X on date D).

```sql
-- as-of join: 2 equality joins, no BETWEEN scan
SELECT l.label_date, c.customer_name, c.country
FROM   labels l
JOIN   nucor_gold.sales.pit_customer p
       ON p.customer_hk = l.customer_hk AND p.snapshot_date = l.label_date
JOIN   nucor_silver.sales.customer c
       ON c.hk = p.customer_hk AND c.effective_ts = p.as_of_ts;
```

## Use case 2 — `bridge_order_fulfillment` (order → shipment → invoice)
**Grain:** one row per current order, pre-joined to its shipment and invoice hash keys
(NULL until each lifecycle stage exists). Higher-level "table of keys + measures of interest"
so consumers make ONE join instead of walking the lifecycle.

1. **Order-to-cash cycle time** — `datediff(invoice_date, order_date)` per region/source, no
   3-table join for analysts or Genie.
2. **Backlog dashboards** — `is_shipped = false` / `is_invoiced = false` flags give unshipped and
   shipped-not-billed backlog with a WHERE clause.
3. **Genie/NL-friendly** — natural-language questions ("orders not yet invoiced in EMEA") resolve
   against one table; no join-path hallucination.

```sql
SELECT source_system,
       avg(datediff(invoice_date, order_date)) AS order_to_cash_days,
       count_if(NOT is_shipped)                AS backlog_orders
FROM   nucor_gold.sales.bridge_order_fulfillment
GROUP  BY source_system;
```

## Load pattern & scope notes
- Both are batch materialized views in `pipelines/gold_dlt.py`, recomputed per pipeline run —
  structural logic stays code (same precedent as `furnace_heat_5min`); entity/column semantics
  stay in `cfg.layer_mappings`.
- Lifecycle sources seeded SAP-only in the pilot (LIPS → `shipment`, VBRP → `invoice`);
  JDE/QAD onboarding = mapping rows in `config/seed_layer_mappings.sql`, no code change.
- Invoice currency deliberately omitted (lives on VBRK header, not VBRP item) — add a VBRK
  mapping before using invoice amounts for finance; flagged so we don't misstate SAP schema.
- PIT spine is **daily** (ML need). At scale: restrict spine to business-relevant dates or switch
  to an incremental snapshot job appending only the new day.
- Retention: PIT/bridge are derived — safe to `CREATE OR REPLACE`; truth stays in Silver history.

## Validation (scripts/validate.py)
- Check 13: `pit_customer` has today's snapshot (freshness).
- Check 14: no bridge order_hk missing from `fact_sales_orders` (referential integrity).
