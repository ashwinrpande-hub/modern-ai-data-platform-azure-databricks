# Architecture — acme Sales Lakehouse on Azure Databricks

## Source landscape → Bronze (templatized, see REPLICATION_PATTERNS.md)
SAP S/4HANA (EU) & Oracle EBS → GoldenGate → ADLS → Auto Loader/AUTO CDC
SQL Server (QAD host) → Lakeflow Connect SQL Server (CDC) — replaces Fabric Mirroring
Salesforce → file/API landing → Auto Loader
OT (PLCs/SCADA) → Litmus Edge UNS → Event Hubs (Kafka) or ADLS parquet → Structured Streaming

## Medallion — Data Vault 2.0 methodology (see DATA_VAULT_PIT_BRIDGE.md)
The lakehouse applies DV2.0 *methodology* without materializing hub/link/sat objects:
- **Business keys → hash keys**: `hk = sha2(source_system|pk, 256)` in Silver plays the DV hub-key
  role — deterministic, source-agnostic, computed not looked-up.
- **Satellites → insert-only versions**: every Silver change is a new row with `effective_ts`;
  full history, no UPDATE. `record_hash` = DV hashdiff (no-op change detection).
- **Links → virtual**: relationships live as hash-key FKs inside 3NF entities, not link tables.
- **Query-assistance tables → materialized in Gold**: `pit_customer` (point-in-time) and
  `bridge_order_fulfillment` (order→shipment→invoice) — the DV2.0 answer to
  "history is cheap to store, expensive to query."

### Layers
- **Bronze (acme_bronze)** — schema-on-write mirror of source 3NF structures; envelope columns
  (`_source_system,_ingest_ts,_batch_id,_op_type,_seq,_raw`); raw payload preserved in `_raw`
  (schema-on-read escape hatch). DLT expectations quarantine bad rows.
- **Silver (acme_silver)** — 3NF, **insert-only**, DV-aligned as above; "current" exposed as a
  view (row_number over hk), never via UPDATE. FX-normalized to USD. DAMA DQ gates.
- **Gold (acme_gold)** — star schema (dims + facts **joined on hash keys**), DV2.0 PIT + bridge
  query-assist tables, pre-aggregations for AI/BI + Genie, ML feature store (PIT-correct via
  `pit_customer`), vector indexes for semantic search/RAG.
- **Products (acme_products)** — secure-view output ports, Delta Sharing, Marketplace listings.

## Databricks features used (and why)
Lakeflow Declarative Pipelines (DLT) — expectations, AUTO CDC, serverless;
Lakeflow Connect — managed SQL Server CDC; Lakeflow Jobs — orchestration;
Unity Catalog — RBAC, row filters/masks, lineage, tags; Liquid Clustering — fact pruning;
Predictive Optimization — auto OPTIMIZE/VACUUM; Genie — NL Q&A on agg tables;
Agent Bricks / Mosaic AI — DQ RCA + healer agents, RAG serving; Online/Lakebase — low-latency features;
Databricks Apps — marketplace portal + agent hosting; Delta Sharing/Marketplace — product distribution.

## Deployment
`databricks.yml` + `resources/pipelines.yml` (Databricks Asset Bundle) deploy `pipelines/silver_dlt.py`
and `pipelines/gold_dlt.py` as two serverless Lakeflow Declarative Pipelines, publishing into
`acme_silver.sales` and `acme_gold.sales`: `databricks bundle deploy -t dev`, then
`databricks bundle run silver_pipeline -t dev` / `gold_pipeline -t dev`. Bronze itself has no
ingestion pipeline yet (see gap below) — `acme_bronze.*` tables in a dev/demo workspace are
seeded directly from `scripts/generate_synthetic_data.py` output plus the envelope columns,
as a stand-in for the templated Auto Loader/Lakeflow Connect ingestion `config/replication_sources.yaml`
describes. `config/seed_layer_mappings.sql` seeds `cfg.layer_mappings` and the `fx_rates`
reference table (kept in `acme_silver.ref`, not `acme_silver.sales` — the pipeline's own publish
target — to avoid a self-referential DLT flow).

## Querying & lineage tracing
`sql/*.sql` — ad hoc queries against the deployed catalogs: `01_explore_tables.sql` (structure/samples
per layer), `02_trace_order_lineage.sql` (one order followed Bronze→Silver→Gold, including the DV2.0
bridge/PIT tables), `03_full_lineage_reconciliation.sql` (bulk reconciliation across all source
systems, using the deterministic `hk = sha2(source_system|src_order_id, 256)` to join layers directly
without a lookup table). Run via Catalog Explorer's SQL editor (needs a SQL warehouse — none is
provisioned in this workspace yet) or a notebook attached to any cluster/serverless compute.

## Performance & cost
Serverless DLT + SQL warehouses with auto-stop (10 min) and autoscale 1→4;
liquid clustering on (order_date, customer_hk) — PIT on snapshot_date, bridge on order_date;
materialized aggregates for BI; photon on; result + disk cache for dashboards;
shallow clone for dev/test (zero-copy); budget policies + system.billing alerts;
spot for non-critical jobs.

## Observability
batch_log + dq_results + rejected_records tables; Lakeflow job notifications → webhook →
healer agent; UC system tables for lineage + audit; SQL alerts on freshness SLOs;
validate.py checks 13–14 assert PIT freshness and bridge referential integrity.

