# Demo Runbook — sequence of talking points

Five stations, ~2–3 minutes each. Pre-demo checklist at the bottom. Every claim in the
deck maps to something you can open live at one of these stations.

## Station 1 — The deck (presentation/index.html)
Open in a browser, arrow keys to navigate. Slide flow: title (stat band: 4 catalogs ·
14 sources · 32 tables · 25.9K records · 14/14 CI checks) → context → cloud architecture
→ data model (real row counts) → field-level lineage → silver hash keys → gold/DV2.0 →
config-driven → DQ → governance → agent stack → agents → products → ROI → risks.
**Talking point:** "Every number on the title slide is verified against the live workspace."

## Station 2 — The repo (GitHub, branch dv2)
Show: `pipelines/` (2 DLT files — the whole medallion), `agents/` (6 agents + core),
`resources/` (Asset Bundle = the deployment), `sql/` (lineage proofs), `security/`,
`docs/index.html` (tabbed doc site).
**Talking point:** "Deployment is `databricks bundle deploy` — no hand-built notebooks;
CI gate is `scripts/validate.py`, currently 14/14."

## Station 3 — Databricks workspace (adb-7405618665227003.3.azuredatabricks.net)
- Catalog Explorer: acme_bronze → silver → gold → products; open
  `acme_gold.sales.dim_customer` → note ROW FILTER + column MASK badges.
- Pipelines UI: silver_pipeline / gold_pipeline, both green.
- Jobs UI: acme_agents_scheduled (paused cron), acme_agents_on_demand, acme_ml_features.
**Talking point:** "Governance is enforced in the pipeline definition — filters and masks
survive every refresh; account-group grants are staged in security/unity_catalog_policies.sql."

## Station 4 — Live queries (SQL editor or databricks-connect)
```sql
-- one order traced Bronze -> Silver -> Gold (swap the id to any order)
-- run the steps in sql/02_trace_order_lineage.sql

-- governance is real:
SELECT * FROM system.information_schema.row_filters  WHERE table_name = 'fact_sales_orders';
SELECT * FROM system.information_schema.column_masks WHERE table_name = 'dim_customer';

-- products + trust:
SELECT * FROM acme_products.meta.v_product_trust_scores;
SELECT * FROM acme_products.sales.v_customer_360 LIMIT 5;

-- semantic layer (metric view):
SELECT order_date, MEASURE(revenue_usd), MEASURE(avg_order_value)
FROM acme_gold.sales.mv_sales_metrics GROUP BY order_date ORDER BY order_date DESC LIMIT 10;

-- ML features (PIT-correct):
SELECT * FROM acme_gold.ml.customer_features WHERE churn_risk_score >= 0.5 LIMIT 10;
```

## Station 5 — Agent evidence (the differentiator)
```sql
SELECT agent, mode, status, finished_at FROM acme_bronze.audit.agent_runs ORDER BY finished_at DESC;
SELECT agent, title, body FROM acme_bronze.audit.agent_reports ORDER BY created_at DESC LIMIT 3;
```
Read aloud from the DQ RCA report: the agent verified the failure itself, traced it to
source-side staleness (fresh `_ingest_ts`, frozen business dates, one snapshot batch),
and proposed the bronze-layer check that would have caught it two months earlier.
**Talking point:** "The agent's only tool is read-only SQL; every query it ran is in the
decision log; writes happen in deterministic code. That's the guardrail model."
Then: `acme_products.sales.order_to_cash` — a view an agent created from a natural-language
request, through a validation gate.

## Pre-demo checklist (run 30 min before)
1. `databricks bundle run gold_pipeline -t dev` (fresh PIT snapshot — check 13)
2. `databricks bundle run agents_scheduled_job -t dev` (fresh DQ rows + digest; needs the
   `agents/anthropic_api_key` secret for LLM mode)
3. `python scripts/validate.py`-equivalent via connect — confirm 14/14
4. Open all five stations in browser tabs; presentation on second screen

## Honest-answer cards (if pressed)
- Delta Share: `CREATE SHARE` needs metastore-level privilege this workspace user lacks —
  designed in `data_products/publish_marketplace.sql`, blocked on admin action.
- Vector Search: endpoint `acme-vs` provisioned; index created by rerunning
  `ai/provision_vector_search.py` once the endpoint is ONLINE.
- Account groups (sales_analyst_*): filter/mask functions reference them today; the GRANTs
  activate when an account admin creates the groups.
- Bronze ingestion: synthetic seed stands in for the templated Auto Loader/Lakeflow Connect
  estate described in `docs/REPLICATION_PATTERNS.md` — design complete, not deployed.
