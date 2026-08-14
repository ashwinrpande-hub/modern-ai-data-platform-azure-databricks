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

## 2026-07-19 — Agents completed: LLM mode enabled and validated end-to-end
Secret scope "agents" created; user stored anthropic_api_key via interactive put-secret (key never
in transcript). Three agent_core fixes from the first LLM runs: (1) secret retrieval now tries
databricks.sdk.runtime.dbutils first (WorkspaceClient().dbutils proved flaky on serverless — one
task got the key, its sibling didn't) with failure reasons logged; (2) tool budget raised 8→12 and
a finalization turn added (tool_choice none, "write the report from gathered evidence") — first RCA
came back truncated mid-investigation; (3) schema_evolution scanner now counts columns referenced
inside transform_expr as consumed (JDE composite-key columns no longer false-positive).

All six agents validated in mode=llm (see audit.agent_runs / agent_reports):
- dq_monitor_rca: full evidence-backed RCA on orders_arriving_30d — correctly diagnosed
  source-side staleness (fresh _ingest_ts, frozen business dates, single-batch snapshot reload,
  identical cutoff across 3 ERPs) and proposed the bronze business-date freshness check that
  would have caught it earlier.
- operational_intel: digest with self-directed drill-downs (top backlog accounts per customer).
- schema_evolution: sampled drifted columns, found MATNR/SHLITM/so_part share identical
  harmonized product codes, proposed 3 mapping INSERTs to a common product_id, and correctly
  recommended skipping so_domain (constant technical field).
- product_creator: NL request → acme_products.sales.order_to_cash (13,000 rows), passed the
  validation gate.
- vector_content: QA caught a REAL artifact — all 501 JDE customers show backlog == orders
  because shipment lifecycle sources are SAP-only in the pilot (LIPS mappings only); flagged as
  ETL gap, plus GmbH-suffix-vs-country synthetic-data mismatch.
- deployment_gate: classified all 5 failures with evidence and issued HOLD on the one genuine
  regression (pit_customer 1 day stale) — cleared by rerunning gold_pipeline (PIT now current).
Remaining known gaps unchanged: row filters/masks not built; validate.py counts stale (checks 2–3).

## 2026-07-19 (later) — Design estate deployed: security, products, ML features, semantics — 14/14
After merging the sibling repo's design estate, deployed the deployable parts:
- SECURITY (checks 8–9 closed): acme_gold.sec schema + region_filter/mask_customer_name
  functions (is_member('admins') escape added so the owner keeps visibility — the account
  groups don't exist yet). Learning: DLT-materialized tables REJECT ALTER TABLE SET ROW
  FILTER/MASK ("expects a table but is a view") — governance must be declared in the pipeline
  definition: gold_dlt.py now sets row_filter= on fact_sales_orders + dim_customer and a
  schema DDL with MASK on dim_customer.customer_name. Verified in information_schema.
  GRANTs to sales_analyst_*/data_engineer fail (PRINCIPAL_DOES_NOT_EXIST — account groups
  not provisioned); staged in security/unity_catalog_policies.sql until an account admin
  creates them. PII tags applied.
- PRODUCTS: v_sales_orders (canonical), v_customer_360 (narrative + fulfillment metrics),
  ops.v_melt_to_margin (36 rows), meta.v_product_trust_scores (from dq_results), all
  commented + tagged; registry entries added. CREATE SHARE denied (needs metastore-level
  privilege) — documented.
- SEMANTICS: acme_gold.sales.mv_sales_metrics metric view (WITH METRICS LANGUAGE YAML)
  created successfully — query with MEASURE().
- ML: ml/build_features.py + resources/ml.yml job acme_ml_features — PIT-correct
  (order_date < as_of_date strictly) customer features: 1,001 rows, churn_risk computed
  (594 high-risk — consistent with the frozen order flow). audit.batch_log created.
- AI: ai/provision_vector_search.py (sdk-based, 3-phase idempotent) — source table
  customer_profile_text (1,001 rows, CDF), endpoint acme-vs PROVISIONING; rerun for index.
  NOTE: the endpoint bills while it exists.
- validate.py baselines refreshed (config tables >=9, sources = 14); deployment_gate
  known-gaps prompt updated to "no open gaps — every failure is a candidate regression".
- RESULT: full validation suite 14/14 GREEN for the first time.
- docs/DEMO_RUNBOOK.md added — 5-station talking-point sequence + honest-answer cards.

## 2026-07-31 — Docs catch-up: requirements traceability, live data model, agent architecture reference
(Not logged same-day; reconstructed 2026-08-02 from commit history.) Added
docs/TRACEABILITY_MATRIX.md (28 requirements scored against live evidence, prioritized gap
table), docs/DATA_MODEL.md + generated HTML catalog/model docs + Excel export tooling, and
docs/AGENT_ARCHITECTURE.html (agent guardrail contract, DAB deployment reference, captured
output from a live agent run). That live run caught a real regression: deployment_gate issued
HOLD and dq_monitor_rca independently confirmed it — scheduled jobs (DQ agent, gold_pipeline)
had stopped producing anything since 2026-07-19, so PIT-snapshot and DQ-freshness checks were
12+ days stale by 2026-07-31. Left unresolved at end of session.

## 2026-08-02 — Cleared the staleness regression; reframed remaining backlog as POC-scope
User directive: this build is a POC, so run the jobs needed to clear the real regression and
stop tracking the rest as open engineering work. `databricks bundle deploy` (workspace already
matched repo) → `silver_pipeline` → `gold_pipeline` (both green, `pit_customer` now stamped
2026-08-02) → `agents_scheduled_job` (dq_monitor_rca + operational_intel, LLM mode) →
`agents_on_demand_job --only deployment_gate`. Gate now reports 14/14 PASS, **PROMOTE**.

RCA on the two still-failing *DQ* checks (distinct from validate.py's 14 — these are the DAMA
checks inside dq_monitor_rca) confirmed two independent, non-fixable-by-rerun root causes: (1)
`orders_arriving_30d` — synthetic generator (`scripts/generate_synthetic_data.py::_date()`) caps
business dates at `2025-01-01 + rand(0,500d)` = max 2026-05-16, deterministic (`random.seed(42)`),
so this check fails permanently as "now" advances past it — by design, previously accepted
2026-07-18; (2) `bronze_ingest_fresh_24h` — bronze is a one-time seed load, not live ingestion
(matrix gap #1), so `_ingest_ts` will always eventually exceed 24h. Rerunning pipelines cannot
fix either; both are POC-scope limitations, not this session's regression (which was specifically
the *meta*-checks — did DQ run recently, is the PIT snapshot from today — now cleared).

New finding from this run (non-blocking): deployment_gate flagged gold FK check as
"green-but-blind" — all 3,000 QAD fact rows have `customer_hk = NULL` because no QAD
customer-master source is registered (`source_registry` has `qad_so_mstr` for orders only);
the FK check only counts non-null orphans so it stays green. Pre-existing since QAD onboarding
(2026-07-18), not introduced this session.

docs/TRACEABILITY_MATRIX.md "Score & open gaps" table reframed: added a POC-scope legend entry
(⏸️) and rewrote the table from "Gap / smallest closing action" to "Item / why deferred (POC
scope) / path to production" — items blocked on account-admin actions (Delta Share, RBAC groups,
read-only access) or scoped as production/stretch work (bronze ingestion template, quarantine
writer wiring, RAG generation layer, marketplace UI, trust dashboard) are now framed as
consciously out of scope for this exercise rather than unfinished work. Nothing in that table
blocks the demo.

## 2026-08-02 (later) — Presentation expanded 19 → 23 slides: platform-depth showcase + live proof
User asked for interview-ready slides on advanced Databricks/Azure/AI-BI/agentic capabilities,
sourced from docs/, inserted after "Data products" and before "Value" (deck stayed at
`presentation/index.html`; the root-level `presentation.html` is the stale pre-rename original,
untouched). Four new slides, each self-contained (eyebrow + lead so they don't need narration):
- **Databricks depth** — capability matrix across 4 categories (Lakeflow/orchestration,
  governance/performance, AI-BI/GenAI, sharing/apps/DevOps), each item tagged LIVE/design/blocked
  against `docs/TRACEABILITY_MATRIX.md`, not asserted from memory.
- **Azure integration** — landing/streaming services (ADLS Gen2, Event Hubs, Litmus) vs. control
  plane (workspace, Azure DevOps `.azuredevops/azure-pipelines.yml`, secret scope), explicit that
  the ADO pipeline is designed but has never actually executed a run.
- **AI/BI maturity** — reused the existing `.road`/`.phase` roadmap component as a 4-rung ladder
  (semantic layer → retrieval → dashboards → generation), citing the 2026-07-31 live vector-search
  query verification rather than just listing the feature.
- **Agentic — live proof** — built entirely from *this session's* real HOLD→PROMOTE fix (see the
  entry above): a before/after check comparison plus the dq_monitor_rca RCA quoted verbatim,
  making the point that the agents reasoned about a real regression today, not scripted output.

Two small consistency touch-ups to older slides so the deck doesn't contradict itself: the "Data
quality" slide's footer previously said "10 green today (gaps tracked openly)" — stale after
today's fix — updated to the current PROMOTE/14-14 result with a forward pointer to the new
"Agentic — live proof" slide. New CSS added (`.caprow`, `.tag.bad`, `.proofgrid`/`.proof`,
`.quote`) — all additive, no existing selectors changed. Verified all 4 new slides + the edited
DQ slide via headless-Chrome screenshots (scratch copies with `go(0)` swapped to the target slide
index — the deck is a one-slide-visible-at-a-time SPA, so a plain screenshot only ever shows the
title slide). Not yet committed.

## 2026-08-02 (still later) — v2 deck: `presentation/index_v2.html`, 23 → 31 slides
User asked for a *new* version (old one preserved at `presentation/index.html` — the root-level
`presentation.html` is the separate stale pre-rename original, untouched by either version) with:
requirement-matrix detail on the agentic architecture, ROI moved to the end with POC/synthetic-data
assumptions up front, per-decision detail from `docs/JUSTIFICATION_NOTES.md`, how RBAC is actually
achieved (not just the policy), the "8 patterns" stat unpacked, and a slide per architecture/decision
doc under `docs/`. Asked one clarifying question first — whether `docs/JD_ALIGNMENT.md`'s named
former employers (BNY, JPMC, UBS, etc.) should appear on-screen — user chose to leave personal
history out, so no slide was built from that file; it stays private interview-prep material.

Eight new slides added to `presentation/index_v2.html` (23 → 31), each sourced from a specific repo
file rather than written from memory:
- **8 patterns** (after Replication) — unpacks the title slide's "8 patterns" stat: all 8 named
  patterns from `config/replication_sources.yaml`'s header comment, cross-referenced against the
  14 source rows to get real usage counts per pattern (`zerobus` = 0, designed but unassigned).
- **Code & data flow** (after the mill diagram) — `docs/CODE_GRAPH.md`'s mermaid graph redrawn as a
  self-contained monospace box diagram (no mermaid.js/CDN dependency, unlike `AGENT_ARCHITECTURE.html`)
  — deliberately a file-path-level view distinct from the existing service-level "Cloud architecture"
  slide, with an explicit real-vs-design-stage-code caption so it doesn't overstate what's deployed.
- **PIT & Bridge** (after Gold) — the two DV2.0 use cases from `docs/DATA_VAULT_PIT_BRIDGE.md` with
  their actual example SQL (as-of join, O2C cycle time query) rather than just naming the tables.
- **RBAC mechanics** (after Governance) — how row filters/masks are *actually* wired: the
  `is_member('admins')` escape hatch, and the real production incident from 2026-07-19 (`ALTER
  TABLE ... SET ROW FILTER` rejected against a DLT-materialized table — governance had to move
  into the pipeline's own `@dlt.table(row_filter=...)` declaration instead).
- **Agentic — traceability** (after Agents) — ties the 6 deployed agents to requirement R9.1 in
  `docs/TRACEABILITY_MATRIX.md` and names the 4 still-design-only agent specs (`pipeline_healer.md`,
  `ingestion_registrar.md`, `lineage_doc_agent.md`, `dq_rca_agent.md`) so the gap is explicit, not
  hidden.
- **Decisions I/II/III** (Ingestion / Modeling / Platform, before Risks) — all 11 decisions from
  `docs/JUSTIFICATION_NOTES.md`, each with its "why" and both rejected alternatives, as three
  4-column tables grouped thematically rather than numerically (was 3+4+4, not the source doc's
  1-11 order) so each slide has a coherent theme.

Plus the two structural changes: the **Value/ROI slide moved from mid-deck to immediately before
Q&A** (after Risks), and gained an assumptions panel at the top — explicit that the $1.2M model is
built against `scripts/generate_synthetic_data.py` output, not acme's real volumes, and every dollar
figure is a bottom-up rate model, not an observed outcome. First version of that panel pushed the
roadmap below the 1000px screenshot viewport (harmless — `.slide` has `overflow-y:auto` — but not
ideal for a live presentation); tightened the panel's padding/copy and re-verified it fits without
scrolling at 1600×1000.

Scoping calls made without asking (flagged here, not blocking): skipped dedicated slides for
`docs/GAP_ANALYSIS.md` (superseded findings from before the DV2.0 pivot — presenting them now would
read as current, misleadingly) and `docs/SESSION_NOTES.md`/`docs/DEMO_RUNBOOK.md` (process/dev-log
docs, not architecture content). `docs/ARCHITECTURE.md`, `DATA_MODEL.md`, `REPLICATION_PATTERNS.md`,
and `TRACEABILITY_MATRIX.md` didn't get new dedicated slides since the existing v1 slides (and the
new ones above) already derive from them.

All 9 new-or-changed slides verified via headless-Chrome screenshots (same scratch-copy-with-`go(N)`
technique as the v1 session). Not yet committed — both `index.html` (v1, untouched) and
`index_v2.html` (v2) currently sit as uncommitted new/modified files.

## 2026-08-13 — Agent self-sufficiency research, governance/DASF audit, data dictionary, 4 spec-only agents implemented
File-level summary already in `CHANGES.md`'s "2026-08-13 update" section — this entry is the
narrative/discussion trail CLAUDE.md rule 4 asks for, not a duplicate of that file list.

Researched Ralph loops (Geoffrey Huntley, mid-2025 agentic-coding pattern — fresh context per
iteration, state in files/git not conversation memory, one stable goal prompt + a verification
gate) and mapped it onto this repo's actual agent design: single-shot today, not looping;
`docs/ralph_loop.md` has the full deployment checklist for closing that gap later.

Audited the repo across governance/DQ/ingestion/AI-data-dictionary
(`docs/GOVERNANCE_DQ_INGESTION_AI_AUDIT.md`) and against Databricks' own "Comprehensive Guide to
Data and AI Governance" ebook, full 39-page PDF extracted and read directly rather than
paraphrased from the gated landing page (`docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md`). Found
two previously-undocumented bugs: `dashboards/dq_trust_dashboard.sql` querying columns
(`dimension`/`score`/`met_threshold`) that don't exist in the live `dq_results` schema (fixed
2026-08-14, see below), and a table-naming mismatch between `vector_content.py`'s
`customer_narratives` and `ai/vector_search_rag.py`'s `customer_profile_text`. The ebook
comparison's priority list drove the rest of this day's and the next day's work: column comments
(done same day), DASF citation (done same day), account-group provisioning (still blocked, not
an engineering task).

Implemented the 4 previously spec-only agents (`pipeline_healer.py`, `dq_rca_agent.py`,
`ingestion_registrar.py`, `lineage_doc_agent.py`) on the same `agent_core.py` guardrail contract
as the original 6 — the PR/Slack/webhook design in their `.md` specs was never buildable here
(no GitHub token, no Slack webhook provisioned), so every recommendation lands in
`acme_bronze.audit.agent_reports` for a human to act on instead, same as every other agent.
`lineage_doc_agent` deliberately does NOT write to the git-tracked `docs/` folder — a file
written from inside a Databricks job container is ephemeral compute state, not a commit, so it
would never reach the repo; caught this before shipping it, not after.

Added `cfg.layer_mappings.business_definition` (one human/AI-facing sentence per `tgt_column`,
stacked across source systems where meanings differ) and applied it live: `ALTER TABLE` +
natural-key `MERGE` (not a raw re-`INSERT` — the live table already had 40 rows; a plain insert
would have duplicated them), then `scripts/apply_column_comments.py` applied 24 real Unity
Catalog column comments, independently verified via `information_schema.columns` rather than
trusting the script's own success log. This directly closes the audit's "column-level comments
are empty everywhere" finding for Silver.

**Gotcha found and worked around**: databricks-connect (serverless, this workspace) silently
corrupts special characters inside SQL `VALUES`-clause string literals passed via `spark.sql(f'...')`
— escaped apostrophes (`''`) were dropped entirely instead of collapsing to `'`, em-dashes came
back as mojibake. Root cause not isolated (Spark Connect transport vs. a `VALUES`-parsing quirk).
Fix: `config/seed_layer_mappings.sql` rewritten plain-ASCII. Logged in memory
(`databricks-tooling-quirks`) so a future session doesn't re-lose time to it.

Also added `pipelines/gold_dlt.py::dim_customer.customer_key_mdm` — a deterministic cross-source
entity-resolution key (normalized name + country, sha2) — and fixed a table comment that had been
overclaiming "MDM-survived" when the code only ever deduped SCD versions within one source, never
actually resolved entities across SAP/JDE/QAD. Committed but **not run** — `gold_pipeline` wasn't
redeployed this session, so this schema change stayed code-only through 2026-08-14 morning (see
below for when it actually went live).

## 2026-08-14 — Live agent verification, reliability guardrails closed against Anthropic's own standards, presentation v3, dashboard fix
Picked up from 2026-08-13's uncommitted state: committed and pushed everything in 4 logical
commits (dashboard fix scope not yet known at that point, data-dictionary + entity-resolution,
DASF doc + `CHANGES.md`, presentation v3), then deployed the bundle for real
(`databricks bundle deploy -t dev`) — confirmed via a live `information_schema.columns` check
that `customer_key_mdm` reached the workspace as a *file* but not as a materialized column
(deploy syncs code, it doesn't run a pipeline update); `gold_pipeline` itself is still not run as
of this entry.

**Ran every agent live and checked the actual results**, not just `bundle validate`: all 5
scheduled-job tasks and all 5 on-demand-job tasks executed successfully — except
`ingestion_registrar`, which reported job-level SUCCESS while doing zero validation. Root cause:
`open()` on the synced YAML hit `[Errno 5] Input/output error` against
`/Workspace/.../files/config/replication_sources.yaml`, a serverless-only flakiness none of the
other agents hit because they all read through `spark.sql()`, not a raw filesystem call. Fixed by
falling back to the Databricks SDK's Workspace Files API (`WorkspaceClient().workspace.download()`)
when `open()` fails; re-ran, all 14 sources validated clean.

Built `presentation/index_v3.html` (34 slides, up from 31 in v2, both older versions untouched) —
a new Technical Summary slide, a dedicated Unity Catalog structure slide (live 4-catalog/
23-schema tree pulled via `SHOW SCHEMAS`/`SHOW TABLES` that same session, not a design doc), and
an AI Security slide scoring the agent fleet against DASF. Refreshed every agent-related slide
from the stale "6 live / 4 spec'd" framing to 10-live, and swapped the RBAC mechanics slide's
illustrative code snippet for the actual live function body pulled from
`information_schema.routines` — which surfaced a real finding along the way: this session's
principal is a workspace admin (`is_member('admins')` true) but resolves `false` on every
`is_account_group_member(...)` check, since no account groups exist yet. That's the precise
mechanism behind the RBAC blocker, not just "GRANTs fail."

Asked what stops the agents from hallucinating, and whether that was documented anywhere — it
wasn't (checked the `agents/*.md` specs and `docs/AGENT_ARCHITECTURE.html` directly; both cover
write-safety, neither uses the word). Wrote `docs/AGENT_RELIABILITY_GUARDRAILS.md`, fetching
Anthropic's current published standards live (Reduce Hallucinations, Trustworthy Agents in
Practice, Building Effective AI Agents, Effective Harnesses for Long-Running Agents — not from
training-data memory) and comparing them against what this repo actually does. Found 4 closable
gaps and closed all 4 the same session, all through the shared `agent_core.py` contract so no
per-agent file needed editing for the first three:
- **Evaluator-optimizer pass**: `run_reasoning()` now runs a second, independent Claude call
  (`verify_report`) that checks the draft report against the `run_sql` evidence log before it's
  saved.
- **Inline citations**: the evidence log itself (not just a reference to `agent_runs`) is now
  appended to every LLM-mode report.
- **Eval scorecard**: `scripts/eval_agent_reports.py`, deterministic, scores per-agent
  verified/flagged rates from `agent_runs.decision_log` over a 30-day window.
- **Plan Mode**: `product_creator` (the one agent that writes directly) got an opt-in `dry_run`
  job parameter, default `false` so existing demo behavior is unchanged.

The best evidence in that doc came from the guardrail catching a real bug in itself: the first
live run of `dq_monitor_rca` under the new verification pass got genuinely flagged — the
evidence log recorded which queries ran but not their *returned values*, so several numbers in
the report weren't strictly re-confirmable from the log alone. Fixed in the same pass
(`safe_sql()` now logs a value snippet per query) and reconfirmed live. Separately confirmed
`product_creator --dry_run=true` proposes without creating by checking the catalog directly
(no view existed) rather than trusting the printed log line.

Fixed `dashboards/dq_trust_dashboard.sql`'s column-name bug found in yesterday's audit
(`dimension`/`score`/`met_threshold` → `dq_dimension`/derived-from-`passed`/`source_table`/
`reason`) and verified all 5 widget queries execute against the live workspace — 2 return real
rows, 3 return 0 rows (expected: `batch_log`/`rejected_records` are only populated by live
ingestion, which doesn't exist yet, not a bug).

**Read every tracked `.md` file in the repo for the first time this session** (prompted by being
asked what gets read at project load, and to make sure changes were actually being traced) —
confirmed the concrete cost of the lazy-loading rule this file used to have: `docs/CODE_GRAPH.md`
and `docs/TRACEABILITY_MATRIX.md` both still said "six agents" after a tenth was added and
deployed, and this file (`SESSION_NOTES.md`) had gone silent for both 2026-08-13 and this day
despite major work, because `CHANGES.md` was carrying that load instead and rule 4 was being
treated as an end-of-session task rather than a running one. Rewrote `CLAUDE.md`: rule 1 now
reads every `.md` file at session start instead of lazily; rule 4 says log as you go; new rule 7
says check and update docs in the same session a change makes them stale. Fixed the two "six
agents" references directly. Other staleness found but deliberately not silently rewritten this
session — flagged instead, since some of it (`docs/DATA_MODEL.md`, machine-generated, marked "do
not hand-edit") needs regeneration via its own pipeline, not hand-patching, and some of it
(`docs/GOVERNANCE_DQ_INGESTION_AI_AUDIT.md`, `docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md`)
are point-in-time snapshots whose value is partly *being* a snapshot — annotating what's since
changed belongs there, not a silent rewrite that erases the record of what was found when.
