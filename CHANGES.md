# Change Summary — July 2026 update package

Apply by copying files over the repo root (paths match exactly). New vs updated marked below.
Full gap matrix: `docs/GAP_ANALYSIS.md`. Nothing outside these files was touched.

## Why this package exists
Three classes of change: (1) **credibility fixes** — things the docs claim that the code
doesn't do (an interviewer running `validate.py` or reading `silver_dlt.py` would find them);
(2) **requirement coverage** — items in the JD/brief with no artifact (DQ dashboard, D365/MES,
orchestration, online features, RAG agent); (3) **currency** — features that went GA since the
repo was written (Oracle query-based connector, Lakebase, Metric Views, Zerobus, AUTO CDC).

## Files

| File | New/Upd | Justification |
|---|---|---|
| `docs/GAP_ANALYSIS.md` | NEW | Full comparison vs requirement, severity-ranked, with 5 open questions that need your decisions (Gold dims, tonnage join, D365 scope, OGG retirement, Old/ cleanup). |
| `pipelines/silver_dlt.py` | UPD | **Gap A1 (credibility)**: docstring promised config-driven mappings from `cfg.layer_mappings`; code hardcoded them. Now genuinely reads mappings at graph-build time — a column change is a config INSERT + refresh, matching the "config tables at each layer" requirement and the lineage story. OT aggregate + current-view logic unchanged. |
| `config/seed_layer_mappings.sql` | NEW | Seeds the mappings Silver now reads; creates+seeds `fx_rates` (read by Silver but never created — would fail on first run); creates `cfg.pipeline_registry` for the quarantine writer. |
| `dq/quarantine_writer.py` | NEW | **Gaps A2/A3**: `batch_log` had zero writers and DLT-dropped rows never reached `rejected_records` (the file was referenced in the bronze template but didn't exist). Parses each pipeline's event log → batch_log (throughput/status) + rejected_records (rule + inferred DAMA dimension). Makes "automated checks and logging for rejected records and batches" true. |
| `pipelines/jobs/lakeflow_jobs.yaml` | NEW | **Gap B3**: deploy.py step 7 mentioned DQ/feature/vector jobs; none were defined. Declarative Automation Bundle (2026 rename of Asset Bundles) resources: hourly DQ job with failure webhook → healer agent, daily feature refresh, vector sync, run-duration health rule. Directly evidences "workflow orchestration tools" from the JD. |
| `dashboards/dq_trust_dashboard.sql` | NEW | **Gap B1**: requirement explicitly asks for a dashboard of the DAMA 6 DQ dimensions proving data-product trust. Five Lakeview widget datasets: dimension heatmap, product trust scorecard, reject drill-down, batch health, freshness-SLO alert query. Header notes how this complements the new DQ Monitoring anomaly detection (good Q&A talking point). |
| `semantics/sales_metric_view.sql` | NEW | **C4**: Unity Catalog Metric Views are GA and now the correct answer for "Genie + AI/BI" — define revenue/orders/AOV once with synonyms/formats; Genie spaces and dashboards bind to it; row filters flow through. Upgrades the old "point Genie at agg_sales_daily" story to 2026. |
| `ml/feature_store.py` | UPD | **Gap B4**: "low-latency serving" was a comment. Adds a Lakebase-synced online feature table (Lakebase GA on Azure, Mar 2026: autoscaling/HA/scale-to-zero). Also made re-runnable (merge instead of create-only). |
| `ai/rag_agent.py` | NEW | **Gap B5**: RAG was a trailing comment. Real agent: UC SQL retriever function (VECTOR_SEARCH TVF — callable by Genie/Agent Bricks too), ChatAgent logged to UC with resource lineage, deployed via `agents.deploy` (endpoint + review app + inference-table audit). |
| `config/replication_sources.yaml` | UPD | **Gap B2 + C1/C2**: requirement names Oracle EBS, D365, MES in the security scope — none existed as sources. Adds: `ebs_oe_order_headers` (OGG, true-CDC path), `ebs_ra_customer_trx` (**`lakeflow_query`** — Oracle query-based connector, GA May 2026, the Databricks-native answer), `d365_salesorders` (Lakeflow Connect D365 connector), `mes_rollmill_orders` (Litmus UNS; Zerobus noted as Path C). Also adds `sap_kna1` + `jde_f0101` — Silver's `customer` table reads these Bronze tables, but they were never registered as sources. |
| `ingestion/litmus_ot/uns_topic_map.yaml` | NEW | **Gap A5**: referenced by REPLICATION_PATTERNS R3 but missing. Includes a catch-all topic so plant data is never silently dropped. |
| `ingestion/templates/bronze_ingest_template.py` | UPD | **C3**: `create_auto_cdc_flow` (current API) with `apply_changes` fallback; stale reference to nonexistent `dq/quarantine_writer.py` now points at the real job. Behavior otherwise identical. |
| `docs/REPLICATION_PATTERNS.md` | UPD | Fixes broken reference to `gg_bronze_dlt.py` (the shared template is the real implementation); adds **R1b** (query-based connector GA — with the R1-vs-R1b decision rule: deletes/replay → OGG, cursor-friendly → native); adds Zerobus Path C + real-time-mode note for OT. |
| `security/unity_catalog_policies.sql` | UPD | **Gap B2**: region filter extended (EBS→AMERICAS, D365→all-analysts-with-mask), MES schema grants + `mes_engineer` group; PII tags enabled (previously commented) — tags now enforce cross-engine via UC ABAC. |
| `scripts/deploy.py` | UPD | **Gap A4**: `--register-source` never inserted into `cfg.source_registry`, so `validate.py` check #3 ("Sources registered ≥6") could never pass. Now inserts registry + pipeline_registry rows; runs the new seed + semantics SQL; points jobs deployment at `databricks bundle deploy`. |
| `scripts/generate_synthetic_data.py` | UPD | **Gap B6**: generator covered 3 of 7+ sources; Silver `customer` would be empty (no KNA1/F0101 data). Adds KNA1, F0101, QAD, SFDC, D365, MES generators; `STEEL` product list now actually emitted (enables `dim_product` later). |
| `docs/SESSION_NOTES.md` | NEW | Stub required by CLAUDE.md rule 4 (was referenced, missing). This update logged as the first entry. |

## Deliberately NOT changed (needs your input — see GAP_ANALYSIS §D)
- `pipelines/gold_dlt.py` — adding `dim_product`/`dim_date` and the real heat-to-tonnage join
  requires grain/survivorship decisions I won't assume.
- `presentation/index.html`, `marketplace-ui/` — no functional gaps found vs requirement;
  cosmetic refresh only if you want the new features reflected on slides.
- `validate.py` — existing 12 checks now become passable; add checks 13–15 (metric view exists,
  batch_log populated, online table synced) after you confirm the above lands.

## Post-apply order
```bash
python scripts/generate_synthetic_data.py
python scripts/deploy.py --env dev          # now seeds mappings + registry
databricks bundle deploy -t dev             # pipelines/jobs/lakeflow_jobs.yaml
python scripts/validate.py --env dev
```

---

# 2026-08-13 update — agent self-sufficiency + governance audit + data dictionary

Two threads: (1) research Ralph-loop-style agent self-sufficiency and audit this repo against
Databricks' own governance/AI-security materials; (2) implement the 4 previously spec-only
agents and close the biggest concrete gap the audit found (empty column comments). Full detail
lives in the docs listed below — this is the file-level summary.

## Files

| File | New/Upd | Justification |
|---|---|---|
| `docs/ralph_loop.md` | NEW | Ralph loop (self-sufficient agent loop) pattern research, mapped onto this repo's actual agent architecture, plus an Azure Databricks deployment checklist. |
| `docs/GOVERNANCE_DQ_INGESTION_AI_AUDIT.md` | NEW | Full repo survey across data governance, data quality, ingestion, and AI-facing data dictionary — what's real vs. aspirational, with file:line citations; found 2 previously-undocumented bugs (a dashboard/table schema mismatch, a vector-content table naming inconsistency). |
| `docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md` | NEW | Chapter-by-chapter comparison against Databricks' "Comprehensive Guide to Data and AI Governance" ebook — full PDF extracted and read directly, not paraphrased from the gated landing page. |
| `docs/DASF_ALIGNMENT.md` | NEW | Risk-by-risk mapping of the agent architecture against the actual Databricks AI Security Framework (DASF v1.1) whitepaper, Components 9 & 10 (Model Serving — the ones that apply to a hosted-LLM consumer rather than a trained-model server). |
| `agents/pipeline_healer.py` | NEW | Implements the previously spec-only `pipeline_healer.md` — scans recent DLT pipeline failures via the Databricks SDK, classifies by heuristic (schema drift / bad records / infra / code), drafts remediation into its report. No PR/Slack integration (none provisioned in this workspace). |
| `agents/dq_rca_agent.py` | NEW | Implements `dq_rca_agent.md` — deepens `dq_monitor_rca`'s output with first-failure-detection + `batch_log` correlation; runs after `dq_monitor_rca` in the job DAG. |
| `agents/ingestion_registrar.py` | NEW | Implements `ingestion_registrar.md` — validates every row in `config/replication_sources.yaml` (pattern, PK, expectations, region, naming) and flags what's unregistered. |
| `agents/lineage_doc_agent.py` | NEW | Implements `lineage_doc_agent.md` — builds lineage edges from live `cfg.layer_mappings` plus UC's `system.access.table_lineage` where available, instead of docs/CODE_GRAPH.md's hand-typed edge list. Writes to `agent_reports` only, not the git-tracked docs folder (a job-container file write wouldn't reach the repo). |
| `agents/README.md` | UPD | Spec/implementation table now reflects reality instead of contradicting the deployed code. |
| `resources/agents.yml` | UPD | Wires the 4 new agents into `agents_scheduled_job`/`agents_on_demand_job`; adds `pyyaml` to the on-demand job's environment for `ingestion_registrar`. |
| `config/config_tables.sql` | UPD | Adds `business_definition STRING` to `cfg.layer_mappings` — the config-table source of truth for UC column comments. |
| `config/seed_layer_mappings.sql` | UPD | 40 real business definitions added, one per mapping row, sourced with multi-system nuance (JDE's Julian date, SAP's doc-currency caveat, etc.). Rewritten in plain ASCII after finding a databricks-connect data-corruption bug (see Gotcha below). |
| `scripts/apply_column_comments.py` | NEW | Applies `business_definition` values as real UC `ALTER TABLE ... ALTER COLUMN ... COMMENT` statements; concatenates distinct definitions when multiple sources contribute to the same column. |
| `pipelines/gold_dlt.py` | UPD | `dim_customer`: added a real `customer_key_mdm` deterministic cross-source entity-resolution key (normalized name + country); fixed a table comment that claimed "MDM-survived" when the code only ever deduped SCD versions within one source, never actually resolved entities across SAP/JDE/QAD. Added per-column `COMMENT` clauses to the schema string. |

## Applied live against the workspace (not just files)
- `acme_bronze.cfg.layer_mappings`: `business_definition` column added via `ALTER TABLE`, then
  backfilled on all 40 existing rows via a natural-key `MERGE` — deliberately not a raw
  re-`INSERT` (the live table already had 40 rows from the original deploy; a plain insert
  would have duplicated them to 80).
- 24 real UC column comments applied across `acme_silver.sales.{customer,invoice,
  sales_order_header,shipment}` — independently verified via `information_schema.columns`,
  not just the script's own success log.
- `databricks bundle validate` confirmed clean against the live workspace (includes the new
  agent job wiring).

## Gotcha found this session
databricks-connect (serverless, this workspace) silently corrupts special characters inside
SQL `VALUES`-clause string literals passed via `spark.sql(f'...')`: escaped apostrophes (`''`)
were dropped entirely instead of collapsing to `'`, and em-dashes came back as `�` mojibake.
Caught by spot-checking an applied value byte-for-byte before trusting it; root cause not
isolated (Spark Connect transport vs. a `VALUES`-parsing quirk — didn't chase it further).
Logged in memory (`databricks-tooling-quirks`) so it doesn't cost debugging time again;
`config/seed_layer_mappings.sql` is deliberately plain-ASCII because of it.

## Deliberately NOT run
`gold_pipeline` has not been redeployed/run — `dim_customer`'s schema change
(`customer_key_mdm` + column comments) is committed in code but not live. Run
`databricks bundle deploy -t dev && databricks bundle run gold_pipeline -t dev` to materialize
it, then re-verify via `information_schema.columns` the same way the Silver comments were
verified above.

## Not yet committed as of this entry
`config/config_tables.sql`, `config/seed_layer_mappings.sql`, `pipelines/gold_dlt.py`
(modified, unstaged) and `docs/DASF_ALIGNMENT.md`, `scripts/apply_column_comments.py`
(untracked) — everything else in this section (the 3 audit docs, 4 new agents, README/
agents.yml wiring) is committed as `1e2fe2c`, `ff9fd24`, `50bb9a3` on `dv2`, 2 commits ahead
of `origin/dv2` and not yet pushed.
