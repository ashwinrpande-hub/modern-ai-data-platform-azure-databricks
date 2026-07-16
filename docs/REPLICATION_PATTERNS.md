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
- Template: `ingestion/templates/bronze_ingest_template.py` (pattern `goldengate`) — reads the
  YAML row, applies AUTO CDC keyed on PK with `sequence_by = csn`, deletes handled via op_type.
- EBS specifics: replicate base tables (e.g., `OE_ORDER_HEADERS_ALL`), not views/APIs;
  keep `ORG_ID`, `LAST_UPDATE_DATE` for partitioning + sequencing.

**Alternatives considered:** (a) Pattern R1b below — now GA. (b) OGG → Kafka →
Structured Streaming — choose when many consumers need the same CDC stream.

---
## Pattern R1b — Oracle / EBS via Lakeflow Connect query-based connector (Databricks-native, GA May 2026)
```
Oracle / EBS --UC connection (Lakehouse Federation)--> Lakeflow Connect query-based pipeline
        --cursor column (e.g. LAST_UPDATE_DATE)--> streaming table in bronze.<schema>.<table>
```
- **Zero extra infra**: no OGG, no gateway, no staging volume — the connector queries the source
  and tracks a high-water mark on a monotonically increasing cursor column.
- YAML: `pattern: lakeflow_query` + `connection_name` + `cursor_column` (see `ebs_ra_customer_trx`).
- **Choose R1 (OGG) when**: hard deletes must be captured, exact ordered replay (CSN) matters,
  or the table lacks a reliable cursor column. **Choose R1b when**: soft-delete/insert-update
  tables with `LAST_UPDATE_DATE` — most EBS transactional tables qualify.
- Strategic answer to "Databricks-native for Oracle": R1b per table where the cursor works,
  R1 retained only for the CDC-hard subset; both are one-line pattern swaps in the YAML.

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
   ├─ Path B (low latency): Litmus → Azure Event Hubs (Kafka API) --> Structured Streaming --> bronze.ot.*
   └─ Path C (2026, evaluate): Litmus flow → **Zerobus** (Lakeflow Connect direct-write API,
      ~100MB/s, <5s latency) --> bronze.ot.*  — removes the Event Hubs hop + consumer entirely
```
- Sub-second OT alerting (e.g., furnace excursion) is a fit for Lakeflow **real-time mode**
  (`update_flow`, Public Preview) on Path B/C streams — keep out of the default path until GA.
- Topic→table mapping is config: `ingestion/litmus_ot/uns_topic_map.yaml`
  (e.g., `acme/berkeley/meltshop/furnace1/temperature` → `bronze.ot.furnace_telemetry`).
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
4. **Same DQ gate**: expectations from YAML; rejects → `acme_bronze.audit.rejected_records` with reason.
5. **Same registration**: `deploy.py --register-source` writes config tables, creates the DLT
   pipeline via REST, and records lineage in `acme_bronze.audit.source_registry`.

