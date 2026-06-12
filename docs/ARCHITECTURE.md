# Architecture — Nucor Sales Lakehouse on Azure Databricks

## Source landscape → Bronze (templatized, see REPLICATION_PATTERNS.md)
SAP S/4HANA (EU) & Oracle EBS → GoldenGate → ADLS → Auto Loader/APPLY CHANGES
SQL Server (QAD host) → Lakeflow Connect SQL Server (CDC) — replaces Fabric Mirroring
Salesforce → file/API landing → Auto Loader
OT (PLCs/SCADA) → Litmus Edge UNS → Event Hubs (Kafka) or ADLS parquet → Structured Streaming

## Medallion
- **Bronze (nucor_bronze)** — schema-on-write mirror of source 3NF structures; envelope columns
  (`_source_system,_ingest_ts,_batch_id,_op_type,_seq,_raw`); raw payload preserved in `_raw`
  (schema-on-read escape hatch). DLT expectations quarantine bad rows.
- **Silver (nucor_silver)** — 3NF, **insert-only**. `hk = sha2(source_system|pk, 256)`;
  `record_hash` for change detection; `effective_ts` versioning; "current" exposed as a view
  (row_number over hk), never via UPDATE. FX-normalized to USD. DAMA DQ gates.
- **Gold (nucor_gold)** — star schema (dims + facts **joined on hash keys**), pre-aggregations for
  AI/BI + Genie, ML feature store (PIT-correct), vector indexes for semantic search/RAG.
- **Products (nucor_products)** — secure-view output ports, Delta Sharing, Marketplace listings.

## Databricks features used (and why)
Lakeflow Declarative Pipelines (DLT) — expectations, AUTO CDC, serverless;
Lakeflow Connect — managed SQL Server CDC; Lakeflow Jobs — orchestration;
Unity Catalog — RBAC, row filters/masks, lineage, tags; Liquid Clustering — fact pruning;
Predictive Optimization — auto OPTIMIZE/VACUUM; Genie — NL Q&A on agg tables;
Agent Bricks / Mosaic AI — DQ RCA + healer agents, RAG serving; Online/Lakebase — low-latency features;
Databricks Apps — marketplace portal + agent hosting; Delta Sharing/Marketplace — product distribution.

## Performance & cost
Serverless DLT + SQL warehouses with auto-stop (10 min) and autoscale 1→4;
liquid clustering on (order_date, customer_hk); materialized aggregates for BI;
photon on; result + disk cache for dashboards; shallow clone for dev/test (zero-copy);
budget policies + system.billing alerts; spot for non-critical jobs.

## Observability
batch_log + dq_results + rejected_records tables; Lakeflow job notifications → webhook →
healer agent; UC system tables for lineage + audit; SQL alerts on freshness SLOs.
