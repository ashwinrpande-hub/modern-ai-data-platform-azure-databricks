# Session notes (append-only, dated) — required by CLAUDE.md rule 4

## 2026-07-05 — Gap analysis + 2026 feature refresh
Compared repo vs requirement; produced docs/GAP_ANALYSIS.md. Fixed credibility gaps
(config-driven Silver made real, batch_log/quarantine writers, source_registry inserts),
added missing requirement artifacts (DQ trust dashboard, EBS/D365/MES sources, jobs,
Lakebase online features, RAG agent, metric view), refreshed patterns for GA features
(Oracle query-based connector, Zerobus, AUTO CDC). Open decisions in GAP_ANALYSIS §D.

## 2026-07-11 — Data Vault 2.0 methodology + PIT/bridge in Gold
Requirement now names DV2.0 explicitly. Adopted DV2.0 methodology over existing hash-key design
(decision revised in JUSTIFICATION_NOTES #5; new #10 PIT, #11 bridge — 2 alternatives each).
New: docs/DATA_VAULT_PIT_BRIDGE.md (use cases), gold pit_customer + bridge_order_fulfillment,
silver shipment/invoice (config-driven; SAP LIPS/VBRP seed mappings + YAML sources + synthetic
lips/vbrp), validate.py checks 13–14 (PIT freshness, bridge FK), ARCHITECTURE.md rewritten,
presentation Gold layer text updated. User-confirmed scope: customer PIT + order-lifecycle
bridge; JDE/QAD lifecycle onboarding deferred to mapping rows (no code).

## 2026-07-18 — First real deploy: DAB resources, bronze seeding, bug fixes, lineage queries
Went from "code exists" to "pipelines actually run against real data" for the first time. Added
`databricks.yml` + `resources/pipelines.yml` (DAB) to deploy `silver_dlt.py`/`gold_dlt.py` as
Lakeflow Declarative Pipelines. Workspace had none of the `acme_*` UC catalogs provisioned and no
bronze ingestion pipeline exists in-repo (gap, see docs/CODE_GRAPH.md) — provisioned catalogs/schemas/
cfg+audit tables directly and loaded `scripts/generate_synthetic_data.py` output into Bronze as a
stand-in, since building the full templated ingestion layer was out of scope for getting the two
existing pipelines running.

Found and fixed 5 pre-existing bugs surfaced by actually running this for the first time:
`config/seed_layer_mappings.sql`'s `MERGE ... USING (VALUES...) s(cols)` (column aliases not allowed
on this Spark version → temp view instead), `uuid()` inside an inline `VALUES` table (non-deterministic,
not foldable → moved to outer SELECT), `pipelines/{silver,gold}_dlt.py` had a UTF-8 BOM the Lakeflow
parser rejects, `silver_dlt.py`'s `fx_rates` table read from its own publish target
(`acme_silver.sales.fx_rates`) causing a DLT graph cycle — reference table moved to `acme_silver.ref`,
and the three `_current` tables were `@dlt.view` (pipeline-local, never reach Unity Catalog) but
`gold_dlt.py` reads them cross-pipeline by fully-qualified name — changed to `@dlt.table`.

`scripts/validate.py` needs a SQL warehouse (none provisioned); ran the same 14 checks via a
serverless Spark Connect session instead — 10/14 pass. Failures are real, pre-existing gaps: no UC
row filter/column mask exists anywhere in the repo (checks 8–9), no DQ framework exists to populate
`audit.dq_results` (check 10), and `validate.py`'s expected active-source count (6) is stale against
`replication_sources.yaml`'s current 14 (check 3) — never updated when EBS/D365/MES were added
2026-07-05.

Added `sql/01_explore_tables.sql`, `sql/02_trace_order_lineage.sql`,
`sql/03_full_lineage_reconciliation.sql` — Bronze→Silver→Gold lineage queries, all verified against
the live data (all 13,000 synthetic orders across SAP/JDE/QAD reconcile with zero orphans). Restyled
`presentation/index.html`: swapped the orange/amber "molten glow" UI chrome for a restrained
industrial-corporate palette (charcoal/steel-gray/green), in the tone of steel-sector sites like
nucor.com (public site loads styling via external JS/CSS, so exact brand hex values weren't
extractable — this is a stylistic approximation, not a literal brand match); kept the literal
molten-steel SVG gradient warm since that's a realistic detail, and gave the Bronze/Silver/Gold
medallion circles their literal metal colors instead of the old arbitrary orange/amber/blue mapping.

Later same day: presentation expanded 14 → 17 slides, structure borrowed from the Vertiv V5 deck
(same author's prior Snowflake platform presentation): title slide gained a platform-at-a-glance stat
band using this build's verified numbers (4 catalogs · 14 sources/8 patterns · 32 tables · 40 mapping
rows · 25.9K records · 13K orders zero-orphan · 14 CI checks · 99.0% avg DQ score); two new data-
architecture slides (per-layer table/row-count model, field-level source→Bronze→Silver→Gold lineage
matrix drawn from cfg.layer_mappings transforms); one new agentic-AI architecture slide (6 agents —
DQ RCA, schema evolution, product creator, vector/content, deployment, operational intel — each mapped
to the platform layer it owns, with triggers/orchestrator/tools strips and guardrails line); value
slide upgraded with the Vertiv deck's ROI framing ($1.2M/yr with 4-driver breakdown, before/after
table, $105K run cost, 11.4×/24× ROI, per-phase roadmap values). DQ slide got a live-result line
(14 checks, 10 green, gaps named). All 5 changed slides verified via headless-Chrome screenshots.
Then two more diagram slides (deck now 19): "Cloud architecture" — six-swimlane Azure/Databricks
service-flow map (sources → ADLS/Event Hubs/Lakeflow Connect/Auto Loader/Zerobus → Bronze → the two
DLT pipelines + UC → Delta Sharing/Genie/Vector Search/Lakebase → consumers) with a DevOps-spine strip;
and "Agent stack" — five-band agentic services diagram (triggers → Claude Agent SDK orchestrator →
MCP/API tools → six agents → platform surfaces acted on, write paths marked PR-only). Both verified
via headless-Chrome screenshots.

Final stretch: the six agents were BUILT AND DEPLOYED for real (agents/ + resources/agents.yml —
two serverless jobs: acme_agents_scheduled with daily-06:00-UTC cron PAUSED, acme_agents_on_demand
with a product_request job parameter). Design: deterministic work always runs (DAMA checks,
drift scan, corpus build, gate, digest); Claude reasoning (claude-opus-4-8, adaptive thinking,
manual tool loop with ONE read-only-SQL tool, everything logged to audit.agent_runs) activates when
env ANTHROPIC_API_KEY or Databricks secret agents/anthropic_api_key exists — currently NEITHER is
configured, so all validated runs were deterministic mode. To enable LLM mode: create secret scope
"agents", put anthropic_api_key in it. Both jobs ran SUCCESS on serverless (env spec
environment_version 3 + pip anthropic). One deploy bug fixed: __file__ is undefined in serverless
spark_python_task (script exec'd in IPython kernel) — path bootstrap falls back to sys.argv[0].
Validated outputs: audit.dq_results now populated (10 checks, 9 pass; orders_arriving_30d fails
by design — synthetic data max order_date ~2026-05); schema drift found for real (unmapped MATNR,
SHLITM/SHKCOO/SHDOCO/SHDCTO, so_domain/so_part — the JDE key columns are consumed via a
concat transform_expr with src_column NULL, so the scanner over-reports them: known limitation);
acme_products.sales.v_sales_orders_unified created (13,000 rows); customer_narratives 1,001 rows;
gate reads 9/14 — two NEW failures are side effects, not regressions (config-table count grew to 7
because agents added agent_runs/agent_reports and validate.py expects exactly 5; PIT freshness
fails because UTC date rolled past the last gold_pipeline run — rerun gold_pipeline to clear).
