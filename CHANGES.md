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
