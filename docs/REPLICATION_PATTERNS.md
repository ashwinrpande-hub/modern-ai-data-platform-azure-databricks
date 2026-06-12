# Reusable Replication Patterns → Bronze

Goal: **any technical person** lands a new source in Bronze by (1) adding one row to
`config/replication_sources.yaml`, (2) running `scripts/deploy.py --register-source <name>`.
No new code. Three patterns cover the estate.

---
## Pattern R1 — Oracle DB / Oracle EBS via GoldenGate
**Today:** OGG classic replicat → target DB.
**Target state (Databricks-native landing):**
```
Oracle / EBS --OGG Extract--> OGG for Distributed Apps & Analytics (BigData)
        --> ADLS Gen2 landing zone (Avro/JSON, op_type + CSN metadata)
        --> Auto Loader (cloudFiles) --> DLT AUTO CDC / APPLY CHANGES INTO --> bronze.<schema>.<table>
```
- OGG handler: `abs` (Azure Blob/ADLS) or the Kafka handler if sub-minute latency is needed.
- Template: `ingestion/goldengate/gg_bronze_dlt.py` — reads the YAML row, applies
  `APPLY CHANGES` keyed on PK with `sequence_by = csn`, preserving deletes as soft flags.
- EBS specifics: replicate base tables (e.g., `OE_ORDER_HEADERS_ALL`), not views/APIs;
  keep `ORG_ID`, `LAST_UPDATE_DATE` for partitioning + sequencing.

**Alternatives considered:** (a) Lakeflow Connect Oracle connector — preferred once GA for your
region/tier; swap by changing `pattern: lakeflow_oracle` in YAML, template stays. (b) OGG → Kafka →
Structured Streaming — choose when many consumers need the same CDC stream.

---
## Pattern R2 — SQL Server (replacing Fabric Mirroring)
**Databricks-native:** **Lakeflow Connect SQL Server connector** (managed; uses CDC / Change Tracking):
```
SQL Server (CDC or CT enabled) --> Lakeflow Connect ingestion gateway (classic compute in your VNet)
        --> staging volume --> managed ingestion pipeline --> bronze tables (SCD-ready)
```
- Enable per-table: CDC for full before/after images; Change Tracking when only keys/net changes are needed.
- Config in `ingestion/sqlserver/lakeflow_sqlserver.yaml`; one gateway per SQL instance, one
  pipeline per database, table list driven by the same `replication_sources.yaml`.

**Alternatives considered:** (a) keep Fabric Mirroring + read via shortcut/external location —
zero ingestion compute, but data lives in OneLake and governance splits across two platforms.
(b) Debezium → Event Hubs (Kafka API) → Structured Streaming — most control/lowest latency,
highest ops burden.

---
## Pattern R3 — OT / plant-floor data via Litmus Edge
**Today:** Litmus syncs to Delta/Parquet landing.
**Templatized target:**
```
PLCs/SCADA/Historians --> Litmus Edge (UNS topics, normalization at edge)
   ├─ Path A (default): Litmus → ADLS Gen2 parquet landing --> Auto Loader --> bronze.ot.*
   └─ Path B (low latency): Litmus → Azure Event Hubs (Kafka API) --> Structured Streaming --> bronze.ot.*
```
- Topic→table mapping is config: `ingestion/litmus_ot/uns_topic_map.yaml`
  (e.g., `nucor/berkeley/meltshop/furnace1/temperature` → `bronze.ot.furnace_telemetry`).
- Template enforces the OT envelope: `site, area, line, asset, tag, ts, value, quality, ingest_ts`.
- Late/out-of-order events handled with watermarking; raw payload kept in `_raw` (schema-on-read).

**Alternatives considered:** (a) Litmus → IoT Hub / IoT Operations → Event Hubs — adds device
management you do not need since Litmus owns the edge. (b) direct historian pull (PI via JDBC) —
batch-only, loses edge normalization and UNS context.

---
## The contract every pattern obeys (what makes it reusable)
1. **One YAML row per source object** → `config/replication_sources.yaml`
   (system, pattern, pk, sequence_col, region, schedule, expectations).
2. **Same Bronze envelope** on every table: `_source_system, _ingest_ts, _batch_id, _op_type, _seq, _raw`.
3. **Same template per pattern** in `ingestion/templates/` — parameterized DLT, never copied.
4. **Same DQ gate**: expectations from YAML; rejects → `nucor_bronze.audit.rejected_records` with reason.
5. **Same registration**: `deploy.py --register-source` writes config tables, creates the DLT
   pipeline via REST, and records lineage in `nucor_bronze.audit.source_registry`.
