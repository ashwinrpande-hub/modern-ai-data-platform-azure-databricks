# Gap Analysis — repo vs. requirement (July 2026)

Legend: 🔴 broken/missing (claimed but not real) · 🟠 required but absent · 🟡 improvement / new-feature opportunity · ✅ solid

## A. Claimed-in-docs but NOT in code (highest interview risk — fix first)

| # | Gap | Evidence | Fix (in this package) |
|---|---|---|---|
| A1 | 🔴 **Silver is NOT config-driven.** `silver_dlt.py` docstring says mappings come from `cfg.layer_mappings`; all mappings are hardcoded. `layer_mappings` is never seeded, never read. | `pipelines/silver_dlt.py` vs `config/config_tables.sql` | Updated `silver_dlt.py` (reads `cfg.layer_mappings`, hardcoded specs kept only as seed/fallback) + `config/seed_layer_mappings.sql` |
| A2 | 🔴 **`batch_log` never written.** Requirement: "automated checks and logging for the rejected records **and batches**". Table exists; zero writers. | grep: no writer for `audit.batch_log` | `dq/quarantine_writer.py` writes batch_log from the DLT event log every run |
| A3 | 🔴 **DLT-dropped rows never reach `rejected_records`.** `expect_all_or_drop` silently drops; the promised `dq/quarantine_writer.py` doesn't exist (referenced in `bronze_ingest_template.py`). Only the batch DQ job quarantines. | `ingestion/templates/bronze_ingest_template.py` comment | New `dq/quarantine_writer.py`: parses pipeline event log expectations → rejected_records with DAMA dimension tag |
| A4 | 🔴 **`validate.py` check #3 can never pass.** "Sources registered ≥6" reads `cfg.source_registry`, but `deploy.py --register-source` never inserts into it. | `scripts/deploy.py` | Updated `deploy.py` inserts registry row per source |
| A5 | 🔴 **Referenced files missing**: `ingestion/litmus_ot/uns_topic_map.yaml` (REPLICATION_PATTERNS R3), `gg_bronze_dlt.py` (R1 — actually covered by the shared template), `fx_rates` table (read by Silver, never created), `docs/SESSION_NOTES.md` (CLAUDE.md rule 4). | docs vs tree | Added `uns_topic_map.yaml`; `fx_rates` created+seeded in `seed_layer_mappings.sql`; R1 doc corrected to name the real template; SESSION_NOTES.md stub |

## B. Requirement present, repo silent (🟠 required)

| # | Requirement text | Gap | Fix |
|---|---|---|---|
| B1 | "dashboard showing that metrics" (DAMA 6 DQ dimensions) + trust in data products | No dashboard artifact at all. `dq_results` exists but nothing consumes it. | `dashboards/dq_trust_dashboard.sql` — Lakeview-ready dataset queries: score by dimension over time, product trust scorecard, reject drill-down, freshness SLO |
| B2 | "oracle EBS **and D365** data along with **MES**" in region/sensitivity policies | No EBS, D365, or MES source rows; security SQL only covers SAP/JDE/QAD | 3 new rows in `replication_sources.yaml` (EBS via OGG, D365 via Lakeflow Connect managed connector, MES via Litmus); `unity_catalog_policies.sql` region filter extended (EBS→AMERICAS, D365→GLOBAL-masked, MES→ot_engineer) |
| B3 | Workflow orchestration (JD: "workflow orchestration tools"; deploy.py step 7 "jobs (DQ, features, vectors)") | No job definitions exist anywhere | `pipelines/jobs/lakeflow_jobs.yaml` — Declarative Automation Bundle resources: dq job (with failure→healer webhook), quarantine writer, feature refresh, vector sync |
| B4 | ML Feature Store "low-latency serving" | Only a comment; no online path | `ml/feature_store.py` updated: publishes a **Lakebase**-synced online feature table (Lakebase is GA on Azure since Mar 2026) |
| B5 | "RAG patterns" / Agent Bricks | `vector_search_rag.py` ends in a comment where the agent should be | `ai/rag_agent.py` — retriever tool + agent + Model Serving endpoint via Mosaic AI Agent Framework |
| B6 | Synthetic data "from multiple source systems" | Generator covers SAP VBAK, JDE F4201, OT only. No KNA1/F0101 (Silver customer reads them!), no QAD, SFDC, D365; `STEEL` product list defined but unused | `generate_synthetic_data.py` extended: kna1, f0101, qad so_mstr, sfdc opportunity, d365 salesorders — with product codes so a `dim_product` becomes possible |
| B7 | Gold star schema depth ("dimensional modeling") | Only `dim_customer` + 2 facts; no `dim_date`, no `dim_product`; `fact_heat_quality` comment promises a tonnage join it doesn't do | Deliberately **not** auto-fixed (would need your grain decisions) — flagged as open question below |

## C. Latest-feature upgrades (🟡 — what changed since the repo was written)

| # | Feature (status, July 2026) | Where it lands |
|---|---|---|
| C1 | **Oracle query-based connector — GA May 2026.** Databricks-native Oracle/EBS ingestion via cursor column, no gateway, no OGG. | New pattern `lakeflow_query` in YAML + REPLICATION_PATTERNS R1b. Positioning: OGG stays for true CDC/deletes; query-based for cursor-friendly tables (EBS `LAST_UPDATE_DATE`). This directly answers "how to do it Databricks-native." |
| C2 | **Zerobus (Lakeflow Connect direct-write API)** — high-throughput (~100MB/s), <5s latency event ingestion without managing Event Hubs consumers. | Documented as Path C for Litmus OT in R3; Litmus can push straight to the lakehouse. Event Hubs path kept as default (Litmus ships a native EH connector today). |
| C3 | **AUTO CDC replaces `apply_changes`** in Lakeflow Spark Declarative Pipelines; `dlt` module direction is `pyspark.pipelines`. | Bronze template updated to `create_auto_cdc_flow` with graceful fallback; comment notes the module rename so the repo doesn't look pre-2025. |
| C4 | **Unity Catalog Metric Views / Business Semantics — GA**, integrated with AI/BI Dashboards + Genie. | `semantics/sales_metric_view.sql` — revenue/orders/AOV defined once; Genie space and dashboards both bind to it. Replaces "Genie hits agg table" with the 2026-correct answer. |
| C5 | **Lakebase GA on Azure (Mar 2026)** — autoscaling, HA, scale-to-zero. | B4 above; also noted as the backing store for the marketplace UI if it needs app state. |
| C6 | **Data Quality Monitoring / Anomaly Detection (Public Preview) + table health indicators.** | Noted in dashboard SQL header: complements (not replaces) the DAMA framework — anomaly detection = unknown-unknowns, DAMA rules = contractual thresholds. Good interview talking point. |
| C7 | **Declarative Automation Bundles** (Asset Bundles renamed). | `lakeflow_jobs.yaml` written in bundle resource shape; deploy.py notes `databricks bundle deploy` as the target-state deployer vs raw REST. |
| C8 | Real-time mode (`update_flow`, ms-latency, Public Preview) | Documented option in R3 for OT alerting use cases; not defaulted (preview). |

## D. Open questions (per CLAUDE.md rule 3 — no assumptions made)

1. **Gold dims**: should `dim_product` key off SAP MATNR / JDE item / QAD part unified by hash key, and what survivorship order? (B7)
2. **fact_heat_quality ↔ shipped tonnage**: which table carries daily tonnage — JDE F4211 lines or MES? Join grain (site+date?) needs your call.
3. **D365 scope**: which entities (salesorders only, or accounts/quotes)? Managed connector vs Synapse Link landing?
4. **OGG retirement horizon**: if EBS tables all have reliable `LAST_UPDATE_DATE`, query-based connector could retire OGG entirely — licensing decision, not technical.
5. `Old/` folder still ships stale content (599-line old README, jsx) — delete before sharing repo access at the interview?
