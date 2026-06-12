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

5. **3NF Silver, star Gold joined on hash keys**
   Why: 3NF preserves source semantics + supports many Gold shapes; star optimizes BI; hash-key
   FKs mean dims/facts assemble without lookups. Alt A: One Big Table — fast for one dashboard,
   unmaintainable at domain scale. Alt B: Data Vault 2.0 — strong audit, but hub/link/sat overhead
   unjustified for one domain pilot (hash keys here borrow DV's best idea).

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
