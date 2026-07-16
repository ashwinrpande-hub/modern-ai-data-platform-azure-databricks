# Decision log — each with two rejected alternatives

1. **Bronze landing via GoldenGate→ADLS→Auto Loader** (Oracle/EBS)
   Why: reuses existing OGG licenses/skills; ADLS landing decouples capture from compute; avro_op
   carries op_type+CSN for exact replay. Alt A: Lakeflow Connect Oracle — cleanest long-term;
   adopt when GA in tenant (YAML pattern swap only). Alt B: OGG→Kafka→streaming — lower latency,
   chosen only if multiple consumers need the CDC stream; otherwise extra infra.

2. **SQL Server via Lakeflow Connect, replacing Fabric Mirroring**
   Why: single governance plane (UC), managed CDC, no OneLake hop, serverless processing.
   Alt A: keep Mirroring + external location/shortcut — cheapest, but split governance, two copies
   of truth. Alt B: Debezium+Event Hubs — max control/latency, highest run cost & on-call burden.

3. **OT via Litmus → Event Hubs (default) with ADLS-parquet fallback**
   Why: Litmus already normalizes to UNS at the edge; Event Hubs Kafka API gives sub-minute
   freshness to Bronze; parquet path stays for high-volume historians. Alt A: Azure IoT
   Operations — duplicates Litmus's job. Alt B: direct historian JDBC pulls — batch-only, loses tags/UNS.

4. **Insert-only Silver with SHA-256 hash keys**
   Why: deterministic keys across 3 ERPs (system|pk), full history for free, audit-trivial,
   merge-free = fast streaming writes; "current" is a cheap window view. Alt A: SCD2 with
   MERGE — familiar, but update-heavy, slower streams, key drift risk. Alt B: identity surrogate
   keys — compact joins but non-deterministic across reloads/environments.

5. **3NF Silver, star Gold joined on hash keys — DV2.0 methodology, not DV2.0 objects**
   (Revised 2026-07-11: requirement now names Data Vault 2.0 explicitly with PIT/bridge in Gold.)
   Why: we adopt DV2.0's methodology — hashed business keys (hub keys), insert-only history with
   hashdiff (satellites), and materialized PIT + bridge query-assist tables in Gold — while keeping
   Silver 3NF instead of physical hub/link/sat objects: 3NF preserves source semantics, halves the
   object count for one domain, and Gold shapes assemble by hash key without lookups.
   Alt A: full raw vault (hubs/links/sats) — maximum auditability and multi-domain integration
   pattern; 3–4x the tables/pipelines for a single-domain pilot, defensible at enterprise scale-out.
   Alt B: One Big Table / plain Kimball star straight from Bronze — fastest to first dashboard, but
   loses deterministic keys, history-by-default, and the PIT/bridge answers below.

6. **Config tables for source→target mapping at each layer**
   Why: changes = versioned inserts (lineage built-in); agents and humans share one contract;
   no code edits to onboard sources. Alt A: dbt-style code-as-mapping — great for analysts, weaker
   for non-SQL OT pipelines. Alt B: hardcoded notebooks — fastest day 1, unscalable day 30.

7. **DQ as DAMA 6 dimensions with quarantine + thresholds that fail jobs**
   Why: business-recognizable scoring, row-level rejects with reasons, breach triggers RCA agent.
   Alt A: DLT expectations only — great inline, but no cross-table/dimension scoring. Alt B:
   Great Expectations — rich but another runtime; revisit at multi-domain scale.

8. **Region access via UC row filters keyed on source_system**
   Why: EUROPE→SAP, AMERICAS→JDE, EMEA→QAD maps 1:1 to source_system column; one function,
   applied to every Gold table. Alt A: separate regional catalogs — strong isolation, triples
   objects. Alt B: BI-tool security — bypassable via SQL, audit gap.

9. **Marketplace = Delta Sharing/Databricks Marketplace + thin custom portal**
   Why: native listing handles entitlements; portal adds branded discovery + AI search without
   owning access control. Alt A: portal-only with direct grants — re-implements entitlements.
   Alt B: third-party catalog (Collibra/Atlan) — strong governance suite, heavy for a pilot.

10. **PIT as a materialized daily-spine table (`pit_customer`), not query-time as-of joins**
   Why: equality joins (snapshot_date, customer_hk) replace BETWEEN range scans; one blessed
   as-of path kills ML label leakage; reproducible month-end reports; derived — safe to rebuild.
   Alt A: query-time AS OF / range joins on effective_ts — zero storage, but every consumer
   rewrites (and mis-writes) temporal logic; slow at scale. Alt B: SCD2 dim with
   valid_from/valid_to — familiar to BI, but needs UPDATE (breaks insert-only Silver) and still
   range-joins at query time.

11. **Bridge as pre-joined lifecycle keys (`bridge_order_fulfillment`), grain = current order**
   Why: order→shipment→invoice in ONE join for O2C cycle time, backlog flags, and Genie (no
   join-path hallucination); NULLs mark incomplete lifecycle stages honestly.
   Alt A: multi-hop joins in the semantic/BI layer — no extra storage, but every tool re-encodes
   join paths and pays 3-table joins per query. Alt B: denormalize lifecycle into a wide
   fact_sales_orders — fastest reads, but grain explosion (order vs shipment-line vs invoice-line)
   and full reload whenever a late stage arrives.
