# Requirements Traceability Matrix

Source: "requirements azure databricks data vault" spec (Nucor tech challenge).
Status legend — ✅ **Deployed & validated** (running in workspace adb-7405618665227003,
verified this build) · 🟡 **Partial** (core deployed, named remainder open) ·
📘 **Design-only** (code/docs in repo, not deployed) · ❌ **Gap** (not built).

Verification anchors: `scripts/validate.py` = 14/14 green (2026-07-19);
`audit.agent_runs` / `agent_reports` = agent evidence; `sql/03` = zero-orphan lineage.

## 1 — Replication / ingestion patterns

| ID | Requirement | Evidence (script / object) | Status |
|----|-------------|----------------------------|--------|
| R1.1 | Oracle / Oracle EBS via GoldenGate pattern | `config/replication_sources.yaml` (goldengate ×5 incl. EBS), `ingestion/goldengate/gg_adls_handler.props`, `docs/REPLICATION_PATTERNS.md`, JUSTIFICATION #1 | 📘 Design-only (Bronze seeded synthetically instead) |
| R1.2 | SQL Server: replace Fabric Mirroring with Databricks-native | `replication_sources.yaml` (lakeflow_sqlserver), `ingestion/sqlserver/enable_cdc.sql` + `lakeflow_sqlserver.yaml`, JUSTIFICATION #2 | 📘 Design-only |
| R1.3 | OT data via Litmus → Delta | `replication_sources.yaml` (litmus_eventhub/adls ×3), `ingestion/litmus_ot/*`, `pipelines/silver_dlt.py::furnace_heat_5min` (watermarked streaming agg — deployed), `acme_bronze.ot.furnace_telemetry` (seeded) | 🟡 Silver OT flow deployed; edge ingestion design-only |
| R1.4 | Reusable templatized patterns any technical person can use | `replication_sources.yaml` (14 sources / 8 patterns — one YAML row per source), `ingestion/templates/bronze_ingest_template.py`, `cfg.source_registry` (14 rows live) | 🟡 Config estate live; template pipeline not deployed |

## 2 — Platform, presentation, justification

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R2.1 | Production-ready platform, Sales domain, Databricks-max | Whole repo; 2 Lakeflow DLT pipelines + 3 jobs deployed via DAB (`databricks.yml`, `resources/*.yml`) | ✅ |
| R2.2 | 60-min interactive HTML presentation | `presentation/index.html` (19 slides, verified via headless Chrome) | ✅ |
| R2.3 | Justification notes, 2 alternatives per decision | `docs/JUSTIFICATION_NOTES.md` (11 decisions × 2 alternatives) | ✅ |
| R2.4 | Real-time ingestion alongside ERP | Design: Event Hubs/Zerobus patterns; deployed: watermarked streaming in `silver_dlt.py` over seeded OT | 🟡 |
| R2.5 | Real/synthetic data from multiple sources | `scripts/generate_synthetic_data.py` → 7 systems, ~25.9K rows in Bronze | ✅ |

## 3 — Medallion + Data Vault 2.0

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R3.1 | Bronze/Silver/Gold with rationale | `pipelines/silver_dlt.py` (9 flows), `pipelines/gold_dlt.py` (6 flows), `docs/ARCHITECTURE.md` | ✅ |
| R3.2 | DV2.0 methodology; PIT + bridge use cases in Gold | `gold_dlt.py::pit_customer` + `bridge_order_fulfillment`, `docs/DATA_VAULT_PIT_BRIDGE.md`, validate checks 13–14 | ✅ |
| R3.3 | DQ/cleansing per DAMA 6 dimensions | `agents/dq_monitor_rca.py` (10 checks → `audit.dq_results`, deployed), DLT expectations in `silver_dlt.py`, `dq/dama_dq_framework.py` (design) | ✅ |
| R3.4 | Advanced features: DLT/Lakeflow, Delta, UC, Genie, Agent Bricks, AI/BI, Serving, Apps, Lakebase | DLT+Jobs+UC+liquid clustering+CDF ✅; metric view for Genie ✅; agents (custom, deployed) ✅; Vector endpoint provisioning 🟡; Lakebase (`ml/feature_store.py`) + Apps (`marketplace-ui/`) 📘 | 🟡 |
| R3.5 | Bronze and Silver in 3NF | Bronze mirrors source 3NF; Silver 3NF entities | ✅ |
| R3.6 | Silver insert-only; sha256(source_system\|pk) hash keys | `silver_dlt.py::hash_key/silver_envelope`; validate checks 5–6 (no UPDATE/DELETE in history; 64-hex) | ✅ |
| R3.7 | Gold joins dimensions on hash keys | `gold_dlt.py` (all joins on *_hk) | ✅ |
| R3.8 | Config tables for source→target mapping per layer, lineage-tracked | `cfg.layer_mappings` (40 versioned rows) drives Silver graph at build time (`silver_dlt.py::load_mappings`); `config/seed_layer_mappings.sql`, `config/config_tables.sql` | 🟡 Silver fully config-driven; Gold intentionally structural (JUSTIFICATION/PIT-bridge notes) |
| R3.9 | Automated checks + logging of rejected records and batches | `scripts/validate.py` (14/14), `audit.dq_results` (populated), `audit.rejected_records` + `batch_log` (tables exist, **not yet written by pipelines** — `dq/quarantine_writer.py` design) | 🟡 |
| R3.10 | Roles/policies: sensitive data + region (EU-SAP, AM-JDE, EMEA-QAD) | `acme_gold.sec.region_filter` + `mask_customer_name` enforced in `gold_dlt.py` (row_filter/MASK — validate checks 8–9 ✅); PII tags; grants staged in `security/unity_catalog_policies.sql` | 🟡 Policies live; account groups pending admin creation |

## 4 — Use-case architectures & performance

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R4.1 | ML feature store: PIT correctness, versioning, low-latency | `ml/build_features.py` + `resources/ml.yml` job (deployed; strict `order_date < as_of_date`; 1,001 rows; append per as_of_date = versioning); Lakebase online serving in `ml/feature_store.py` | 🟡 Offline deployed; online serving design-only |
| R4.2 | BI: dimensional model, aggregations, query performance | Gold star + `agg_sales_daily` + metric view `mv_sales_metrics` (deployed, MEASURE()-queryable); `dashboards/dq_trust_dashboard.sql` (design) | ✅ |
| R4.3 | AI-ready: embeddings, semantic search, RAG | `customer_narratives` + `ai.customer_profile_text` (CDF, deployed); `ai/provision_vector_search.py` (endpoint `acme-vs` provisioning); `ai/vector_search_rag.py`, `ai/rag_agent.py` (design) | 🟡 |
| R4.4 | Clustering, MVs, search optimization | Liquid clustering on fact/PIT/bridge (`gold_dlt.py cluster_by`); DLT materialized views; Photon (serverless default) | ✅ |
| R4.5 | Warehouse sizing/auto-scaling; cost optimization | `docs/ARCHITECTURE.md` (auto-stop, autoscale, budget alerts, shallow clones); serverless everywhere in practice | 🟡 Documented + serverless; no SQL warehouse provisioned |

## 5 — Data products (mesh principles)

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R5.1 | Domain products with input/output contracts | `acme_products.sales.v_sales_orders`, `v_customer_360`, `ops.v_melt_to_margin` (+ agent-built `order_to_cash`) — COMMENT contracts + tags; `data_products/data_products.yaml` | ✅ |
| R5.2 | SLAs, ownership, governance + DQ trust metrics + dashboard | SLA/owner in view comments; `meta.v_product_trust_scores` (live, from dq_results); trust dashboard SQL design-only | 🟡 |
| R5.3 | Publish to Databricks Marketplace; discovery + consumption | UC tags for discovery ✅; `data_products/publish_marketplace.sql`; **CREATE SHARE denied — metastore privilege missing** | 🟡 blocked on admin |

## 6 — Custom marketplace UI (stretch)

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R6.1 | Independent front-end portal, deployed on Azure | `marketplace-ui/backend/app.py` + `frontend/index.html` (independent code) | 📘 Not deployed |
| R6.2 | AI-powered metadata search | Depends on `acme-vs` endpoint (provisioning) + portal deploy | ❌ Stretch, open |

## 7 — Business value

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R7.1 | Quantified value / strategic impact | Presentation "Value·ROI" slide ($1.2M/yr modeled, 4 drivers, before/after) | ✅ |
| R7.2 | Implementation roadmap pilot→enterprise | Presentation roadmap (4 phases with value/yr) | ✅ |
| R7.3 | Risks & mitigations | Presentation "Risks" slide (6 risks) | ✅ |

## 8 — Interview deliverables

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R8.1 | Working Databricks environment + read-only access | Workspace live, all green; **read-only viewer grant = manual admin step** | 🟡 |
| R8.2 | Deployed marketplace UI URL | — | ❌ (stretch) |
| R8.3 | GitHub repository, code + docs | github.com/ashwinrpande-hub/modern-ai-data-platform-azure-databricks (dv2) | ✅ |
| R8.4 | Architecture diagrams incl. performance | Presentation slides 5–8 + `docs/CODE_GRAPH.md` mermaid | ✅ |
| R8.5 | Presentation slides (technical + strategic) | `presentation/index.html` | ✅ |

## 9 — Process & agentic (JD + closing asks)

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| R9.1 | Agentic workflows / self-healing pipelines | `agents/` 6 agents + `agent_core.py`, 3 jobs deployed, all validated `mode=llm`; healer/registrar/lineage-doc specs in `agents/*.md` | 🟡 6 live; 4 spec'd agents design-only |
| R9.2 | .md per section; session summaries; token-optimized docs | `docs/*.md` (12 files) + `docs/index.html` tabbed site; `docs/SESSION_NOTES.md` dated log | ✅ |
| R9.3 | Automation + validation scripts | `scripts/validate.py` (CI gate), `scripts/generate_synthetic_data.py`, `scripts/deploy.py` (design), agents | ✅ |
| R9.4 | Code graph | `docs/CODE_GRAPH.md` (mermaid, rendered in docs site) | ✅ |
| R9.5 | JD skills traceability | `docs/JD_ALIGNMENT.md` (JD → repo → real-world evidence) | ✅ |

## Score & open gaps (prioritized)

**28 requirements: 17 ✅ · 12 🟡 · 4 📘 · 2 ❌** (some IDs span categories).

| # | Gap | Smallest closing action |
|---|-----|------------------------|
| 1 | Bronze ingestion pipelines not deployed (R1.1–R1.4) | Deploy `ingestion/templates/bronze_ingest_template.py` as a DLT pipeline for ONE pattern (autoloader_file over `data/` uploads) to prove the template |
| 2 | `rejected_records`/`batch_log` never written by pipelines (R3.9) | Wire `dq/quarantine_writer.py` logic into `silver_dlt.py` expectations, or extend the DQ agent to snapshot DLT expectation metrics per run |
| 3 | Delta Share / Marketplace listing (R5.3) | Metastore admin grants CREATE SHARE, then run `data_products/publish_marketplace.sql` |
| 4 | Account groups for regional RBAC (R3.10) | Account admin creates `sales_analyst_*`/`data_engineer`/`data_steward`; rerun grants in `security/unity_catalog_policies.sql` |
| 5 | Vector index + RAG serving (R4.3) | Rerun `ai/provision_vector_search.py` once `acme-vs` is ONLINE; then `ai/rag_agent.py` needs a serving endpoint |
| 6 | Marketplace UI not deployed (R6) | Azure App Service / Static Web App deploy of `marketplace-ui/`; point backend at `cfg.product_registry` + trust view |
| 7 | Trust dashboard not live (R5.2) | Create SQL warehouse → import `dashboards/dq_trust_dashboard.sql` as AI/BI dashboard |
| 8 | Read-only interview access (R8.1) | Workspace admin invites reviewer as workspace user with SELECT-only grants on the 4 catalogs |
