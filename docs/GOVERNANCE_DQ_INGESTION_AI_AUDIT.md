# Governance / DQ / Ingestion / AI Data-Dictionary audit

Status: **inventory only, nothing changed.** Captured 2026-08-12 via a full repo survey
(4 parallel searches: governance, data quality, ingestion, AI-facing data dictionary).

Cross-cutting theme: in all four areas the design work is real and often good (row filters,
DAMA framework, ingestion templates, metric-view semantics), but roughly half of it stops at
"spec'd or coded" and never reaches "in the deployed bundle." Consistent with this being an
honestly-scoped POC, not a hidden gap.

---

## 1. Data Governance

### Implemented (real config/code/resource exists)
- **Row-level security**: `security/unity_catalog_policies.sql:7-13` —
  `acme_gold.sec.region_filter(source_system STRING)`, ABAC-style region rule using
  `is_account_group_member()` (EUROPE→SAP, AMERICAS→JDE/EBS, EMEA→QAD, D365 open to all
  analysts). Applied via `ALTER TABLE ... SET ROW FILTER`
  (`security/unity_catalog_policies.sql:15-18`) and also declared directly in the DLT table
  decorator in `pipelines/gold_dlt.py:16,29` (DLT-materialized tables reject `ALTER TABLE`).
- **Column masking**: `mask_customer_name()` (`security/unity_catalog_policies.sql:21-25`),
  unmasked only for `data_steward` group; wired into DLT schema DDL
  (`pipelines/gold_dlt.py:13`).
- **PII tagging**: `customer_name`→`pii=name`, `src_customer_id`→`pii=identifier`
  (`security/unity_catalog_policies.sql:40-41`).
- **Grants (least privilege)**: real SQL for `sales_analyst_emea/americas/europe`,
  `data_engineer`, `ml_engineer`, `ot_engineer`, `mes_engineer`
  (`security/unity_catalog_policies.sql:28-36`).
- **Automated governance verification**: `scripts/validate.py` checks 8-9 query
  `system.information_schema.row_filters`/`column_masks` to confirm the filter/mask are
  actually active.
- **Audit logging**: `agents/agent_core.py:38-46` creates and populates
  `acme_bronze.audit.agent_runs`/`agent_reports` — genuinely written by deployed agents.
- **Data-product ownership/SLA metadata**: `data_products/data_products.yaml` (`owner`, `sla`
  per product); `COMMENT ON VIEW`/`SET TAGS` in `data_products/publish_marketplace.sql:9-15`
  for discovery/governance.
- `acme_products` catalog deliberately structured as a governed output-port layer distinct
  from bronze/silver/gold (`docs/ARCHITECTURE.md:29`).

### Documented but not implemented / aspirational only
- **Account groups never provisioned**: every group referenced by the row filter/GRANTs
  (`sales_analyst_*`, `data_engineer`, `ml_engineer`, `data_steward`, `ot_engineer`,
  `mes_engineer`, `exec_readonly`) does not exist in the workspace — GRANTs fail with
  `PRINCIPAL_DOES_NOT_EXIST`. Blocked on account-admin group creation
  (`docs/TRACEABILITY_MATRIX.md`, `docs/SESSION_NOTES.md`). Practical effect: the
  `data_steward` masking exception and all region-based GRANTs are non-functional today even
  though the SQL exists.
- **Delta Sharing / Marketplace listing**: `CREATE SHARE`/`ALTER SHARE`
  (`data_products/publish_marketplace.sql:18-19`) written but fails — "CREATE SHARE denied,
  metastore privilege missing" (`docs/TRACEABILITY_MATRIX.md`).
- **Read-only interview/reviewer access grant**: documented as a manual admin step, never
  executed.
- **Steward ticketing / Slack escalation**: only exists in the unimplemented
  `agents/pipeline_healer.md` (`log to audit.agent_actions` — table doesn't exist anywhere;
  real audit tables are `agent_runs`/`agent_reports`) and `agents/dq_rca_agent.md` specs.
- **Lineage-based audit agent**: `agents/lineage_doc_agent.md` spec-only, never implemented;
  no code anywhere queries `system.access.table_lineage`.
- **`acme_products.meta.v_product_trust_scores`**: referenced as live everywhere (row counts
  in `docs/DATA_MODEL.md`, read by `scripts/generate_data_docs.py`) but **no `CREATE VIEW`
  DDL exists in the repo** — created ad hoc directly in the workspace, not IaC.
- **Legacy `Old/` design (superseded, not current)**: a materially richer governance stack —
  Purview scan rules/glossary/sensitivity labels, Entra ID RBAC mapping, a full
  masking-policy table (email/financial masks), a `data_steward_chatbot.py` — described in
  `Old/README.md` but none of it carried forward. `docs/GAP_ANALYSIS.md` already flags this
  folder as stale content to delete before sharing repo access.

### Not present at all
- No systematic data-classification/sensitivity-labeling scheme (only 2 columns on 1 table
  carry a `pii` tag).
- No masking beyond `mask_customer_name` (no email/phone/financial masks).
- No compliance-framework references (GDPR/CCPA/HIPAA/SOC2) outside the stale `Old/` folder.
- No business glossary / third-party catalog integration — deliberately rejected in
  `docs/JUSTIFICATION_NOTES.md` as "heavy for a pilot."
- No job/pipeline-level `permissions:` blocks in `databricks.yml`/`resources/*.yml`.
- No query of native UC access-audit system tables (`system.access.*`) anywhere in code.
- No steward ticketing/workflow tool actually implemented.

---

## 2. Data Quality

### Two parallel DQ suites exist — only one is deployed
**A. `agents/dq_monitor_rca.py` — DEPLOYED, live**, writes to `acme_bronze.audit.dq_results`.
Runs as part of `agents_scheduled_job` (`resources/agents.yml`, cron `0 0 6 * * ?`, currently
**PAUSED**). 10 hardcoded checks (`agents/dq_monitor_rca.py:18-47`):

| check_name | dimension | table | what it checks |
|---|---|---|---|
| order_keys_not_null | completeness | sales_order_header | src_order_id/source_system not null |
| customer_name_not_null | completeness | dim_customer | customer_name not null |
| hash_key_64_hex | validity | sales_order_header | hk matches `^[0-9a-f]{64}$` |
| currency_in_fx_reference | validity | v_sales_order_header_current | currency resolves against fx_rates |
| no_duplicate_current_orders | uniqueness | v_sales_order_header_current | no dup (source_system, src_order_id) |
| fact_customer_fk_resolves | consistency | fact_sales_orders | customer_hk FK resolves (LEFT ANTI JOIN) |
| silver_gold_row_parity | consistency | fact_sales_orders | row-count parity Silver↔Gold |
| usd_amount_reconciles | accuracy | fact_sales_orders | sum(order_amount_usd) reconciles within 0.01 |
| bronze_ingest_fresh_24h | timeliness | acme_bronze.sap.vbak | max(_ingest_ts) within 24h |
| orders_arriving_30d | timeliness | fact_sales_orders | max(order_date) within 30d |

Pass/fail is binary (zero violations), hardcoded in the check SQL — not read from a config
table. Failing checks trigger a read-only Claude RCA pass (`agent_core.run_reasoning`) that
writes a report to `acme_bronze.audit.agent_reports`.

**B. `dq/dama_dq_framework.py` — NOT deployed** (design-stage, confirmed by
`docs/CODE_GRAPH.md`). 6 DAMA-tagged rules with per-rule thresholds (completeness 0.99,
validity 0.999, uniqueness 0.999, timeliness 0.95, consistency 0.98, accuracy 0.99) —
numerically match `data_products/data_products.yaml`'s `dq_dimensions_threshold`, but the
executing code hardcodes the tuple rather than reading the YAML; its docstring claims rules
"live in `acme_bronze.cfg.layer_mappings.dq_rule`" but the actual code doesn't query that
column. Its owning job (`pipelines/jobs/lakeflow_jobs.yaml`) was never added to the deployed
bundle — `databricks.yml` only globs `resources/*.yml`, so this suite has never run.

**DLT-inline expectations (deployed)**: `@dlt.expect_all_or_drop` on Silver tables
(`pipelines/silver_dlt.py:49-51,60,65,70`), `@dlt.expect_all` (warn-only) on Gold fact/bridge
tables (`pipelines/gold_dlt.py:30,67`). Hardcoded decorator args, not config-driven.

**CI/deployment-gate suite**: `scripts/validate.py` — 14 checks, DQ-relevant ones include
Gold FK integrity, DQ-ran-in-24h freshness, rejects-logged-with-dimension, bridge FK
integrity. `agents/deployment_gate.py` imports this exact `CHECKS` list and has Claude
classify failures vs. known/tracked gaps to issue PROMOTE/HOLD.

### Bug found (not previously documented)
`dashboards/dq_trust_dashboard.sql` queries columns (`dimension`, `score`, `met_threshold`)
that belong to the **undeployed** DAMA framework's schema. The actual live `dq_results` table
(populated by `dq_monitor_rca.py`) has different columns (`dq_dimension`, `passed`,
`row_count`) — this dashboard SQL would not run against the real table as written.

### Quarantine / rejected-records
Schema exists (`config/config_tables.sql:25-34`: `rejected_records`, `batch_log`); a writer
exists (`dq/quarantine_writer.py`, maps DLT expectation failures to DAMA dimensions via a
naming-convention heuristic); but neither writer's owning job is in the deployed bundle —
**the tables are defined but not populated by any deployed pipeline.**

### How rules are defined/configured
- Config-driven (real DDL): `acme_bronze.cfg.source_registry`/`layer_mappings`; per-source
  `expectations:` maps in `config/replication_sources.yaml`; per-product `sla`/
  `dq_dimensions_threshold` in `data_products/data_products.yaml`.
- Hardcoded in code: the actually-executing check suite (`dq_monitor_rca.py`), the CI gate
  (`validate.py`), DLT decorator expectations, and the DAMA thresholds tuple.

### Known gaps/deferred items (already tracked, not new)
- `rejected_records`/`batch_log` exist but unwired — tracked in `docs/TRACEABILITY_MATRIX.md`
  as POC-scope deferred.
- `orders_arriving_30d`/`bronze_ingest_fresh_24h` fail permanently by design — synthetic
  generator caps business dates at 2026-05-16 (`scripts/generate_synthetic_data.py::_date()`,
  seed 42); bronze is a one-time seed, not live ingestion.
- QAD FK check is "green-but-blind": 3,000 QAD fact rows have `customer_hk = NULL` because no
  QAD customer-master source is registered; the check only counts non-null orphans so it
  stays green regardless.
- A real staleness regression (jobs silent for 12+ days, 2026-07-19→2026-07-31) was caught by
  `deployment_gate`/`dq_monitor_rca` and fixed 2026-08-02 — this was a genuine catch, not a
  design gap.

---

## 3. Data Ingestion

### Sources registered (`config/replication_sources.yaml` — "the ingestion estate")
14 source-object rows across 8 patterns:

| System | Sources | Pattern |
|---|---|---|
| SAP (Europe) | vbak_sales_header, kna1_customer, lips_delivery_item, vbrp_billing_item | goldengate |
| JDE (Americas) | f4201_sales_header, f0101_address_book | goldengate |
| EBS/Oracle | oe_order_headers, ra_customer_trx | goldengate / lakeflow_query |
| D365 | salesorders | lakeflow_d365 |
| QAD (EMEA) | so_mstr | lakeflow_sqlserver |
| Salesforce | opportunity | autoloader_file |
| Litmus (OT) | furnace_telemetry, caster_history | litmus_eventhub / litmus_adls |
| MES | rollmill_orders | litmus_eventhub |

### Mechanism: synthetic/one-time, NOT live — verified explicitly
No live/scheduled ingestion pipeline runs against any of these 14 sources. Bronze is
populated entirely by `scripts/generate_synthetic_data.py`, run once and loaded manually —
confirmed in `docs/SESSION_NOTES.md` ("no bronze ingestion pipeline exists in-repo... loaded
generator output into Bronze as a stand-in"), `docs/CODE_GRAPH.md`, and
`docs/TRACEABILITY_MATRIX.md`. No code anywhere reads the generated files back into Bronze on
a schedule (confirmed via repo-wide grep). **No EBS synthetic data generation exists at all**
despite EBS being registered.

### Templates/patterns available (built, never deployed)
- `ingestion/templates/bronze_ingest_template.py` — generic config-driven Lakeflow DLT
  template (goldengate/litmus_adls/autoloader_file patterns), explicitly: "ANY new source =
  a row in `config/replication_sources.yaml`. Do not copy this file."
- `ingestion/litmus_ot/litmus_eventhub_dlt.py` + `uns_topic_map.yaml` — Litmus/OT template.
- `ingestion/sqlserver/lakeflow_sqlserver.yaml` + `enable_cdc.sql` — declarative Lakeflow
  Connect config for QAD (managed connector, no custom code).
- `ingestion/goldengate/gg_adls_handler.props` — OGG-for-Big-Data handler config.
- `docs/REPLICATION_PATTERNS.md` documents 3 reusable pattern families and the onboarding
  contract: one YAML row → `scripts/deploy.py --register-source <name>`.
- `scripts/deploy.py::register_source()` is the real onboarding mechanism — inserts a row
  into `cfg.source_registry` and, for template-backed patterns, POSTs a DLT pipeline-create
  call; for managed-connector patterns it prints a no-op message.
- **Ingestion Registrar agent is spec-only** — `agents/ingestion_registrar.md` describes
  PR-triggered validation + registration on merge, but no `.py` implementation exists.

### Bronze→Silver transform coverage gap
`acme_bronze.cfg.layer_mappings` (seeded by `config/seed_layer_mappings.sql`) covers SAP
VBAK/KNA1/LIPS/VBRP, JDE F4201/F0101, QAD so_mstr → `sales_order_header`/`customer`/
`shipment`/`invoice`. **SFDC, D365, EBS, MES have zero rows** — even the synthetic seed
pipeline has no Silver transform for 4 of the 14 registered sources. OT
(`furnace_heat_5min`) is deliberately hardcoded, not config-driven (no column-mapping
semantics).

### Gaps (explicitly documented)
1. No live ingestion pipeline for any source (`docs/TRACEABILITY_MATRIX.md` gap #1) — path to
   production: deploy `bronze_ingest_template.py` as a DLT pipeline for one pattern
   (autoloader_file over `data/` uploads).
2. `rejected_records`/`batch_log` never written (see DQ section).
3. `validate.py`'s "sources registered" check was structurally broken until fixed —
   `deploy.py --register-source` originally never inserted into `cfg.source_registry`; now
   fixed.
4. EBS/D365/MES registered but no synthetic data (EBS) or Silver mapping (SFDC/D365/EBS/MES).
5. Ingestion Registrar agent aspirational only.

---

## 4. Data Dictionary / Definitions for AI

### Where definitions live, and how rich they are
- **Table-level comments exist and are useful**: `@dlt.table(comment=...)` in
  `pipelines/silver_dlt.py`/`gold_dlt.py` (e.g. VBRP billing-item comment calls out that
  amount is doc-currency — join VBRK before finance use).
- **Column-level comments are empty everywhere** — confirmed against the live-generated
  `docs/DATA_MODEL.md` (pulled straight from `system.information_schema.columns.comment` via
  `scripts/extract_data_model.py`). Sampled Bronze `sap.kna1` and Gold `sales.dim_customer` —
  every column's Comment field is blank. `cfg.layer_mappings` also has no
  `description`/`business_meaning` field, only `transform_expr`/`dq_rule`.
- **Closest thing to a central data dictionary is machine-generated, not hand-authored**:
  `scripts/extract_data_model.py` → `scripts/generate_data_docs.py` → `docs/DATA_MODEL.md` /
  `docs/DATA_CATALOG.html`. Table/column metadata is real, but lineage edges
  (`generate_data_docs.py::EDGES`) and governance annotations (`GOVERNANCE_NOTES`) are
  **hand-curated Python literals**, not derived from live UC lineage APIs. It's a manual
  batch-regeneration snapshot (dated "Generated 2026-07-29"), not queried live.
- `docs/DATA_VAULT_PIT_BRIDGE.md` — genuinely rich hand-written doc for `pit_customer`/
  `bridge_order_fulfillment` specifically (grain, worked SQL, use-cases), but static and not
  wired into any agent or retrieval path.

### AI-facing semantic/metadata layer that exists today
- **`semantics/sales_metric_view.sql`** — the one real AI-facing semantic layer: a UC Metric
  View (`WITH METRICS LANGUAGE YAML`) defining `revenue_usd`, `order_count`,
  `avg_order_value`, `active_customers` with `display_name` and `synonyms` per metric,
  explicitly built "so Genie grounds NL questions deterministically." Strongest
  "AI-reads-a-definition-before-acting" pattern in the repo.
- **`agents/vector_content.py`** builds `customer_narratives` — one NL sentence per customer
  (name, country, source, revenue, order count, backlog) for Vector Search embedding. This is
  a **business-entity content corpus for retrieval, not a schema/column dictionary** — it
  describes customer facts, not what `order_amount_usd` or `customer_hk` mean.
- **`agents/product_creator.py`** — the NL→data-product agent's system prompt **hand-writes**
  the available Gold table/column list as prose, not read dynamically from UC comments or
  `docs/DATA_MODEL.md`. It has a read-only `run_sql` tool and is told to verify columns before
  finalizing, but nothing requires it to query comments — the schema-of-record is a
  hand-maintained string that can silently drift from the real `gold_dlt.py` schema.
- **`ai/rag_agent.py`** — a UC SQL retriever function wrapping `VECTOR_SEARCH` over
  `customer_profile_idx`, grounding on citation of `customer_hk`. Retrieval of the same
  customer-narrative corpus, not a table/column dictionary.

### Naming inconsistency found (not previously documented)
`vector_content.py` writes to `acme_gold.sales.customer_narratives`, but
`ai/vector_search_rag.py` sources its index from a **different table**,
`acme_gold.ai.customer_profile_text`. `generate_data_docs.py` papers over this with a
hand-added lineage edge, but no code in the repo actually performs that copy/rename.

### Gaps
- No column-level comments anywhere — an AI agent has no per-column business definitions to
  read from UC metadata even where table comments exist.
- `agents/lineage_doc_agent.md` — spec-only, confirmed no `.py`, not scheduled anywhere;
  `docs/CODE_GRAPH.md` (the doc it's supposed to auto-generate) is hand-maintained instead.
- RAG **generation** layer is design-only — `ai/rag_agent.py` unwired into any job; only
  retrieval is live (already known; now pinpointed to the exact file).
- No system dynamically feeds table/column comments to any agent as runtime grounding — the
  generated docs are for human browsing, not agent consumption.
- Metadata is scattered across 4 disconnected artifacts (pipeline-code comments,
  manually-triggered `DATA_MODEL.md`, hand-written `DATA_VAULT_PIT_BRIDGE.md`,
  `product_creator.py`'s hardcoded prompt string) with nothing reconciling them automatically.
