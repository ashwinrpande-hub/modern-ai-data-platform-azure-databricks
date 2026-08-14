# POC vs. Databricks "A Comprehensive Guide to Data and AI Governance" — gap analysis

Status: **inventory only, nothing changed.** Captured 2026-08-13, comparing this repo against
Databricks' own ebook (`comprehensive-guide-to-data-and-ai-governance.pdf`, 2024, authored by
Databricks Solutions Architecture/Product Management — landing page:
https://www.databricks.com/resources/ebook/data-analytics-and-ai-governance). Extracted the
full 39-page PDF text directly since the landing page itself is a lead-gen gate with no
substantive content.

Builds on [docs/GOVERNANCE_DQ_INGESTION_AI_AUDIT.md](GOVERNANCE_DQ_INGESTION_AI_AUDIT.md) —
that doc has the file:line detail behind most "covered"/"partial" claims below; this doc adds
the ebook-framework elements that weren't part of that earlier audit (data federation, entity
resolution/MDM, Lakehouse Monitoring specifically, DatabricksIQ/Genie, clean rooms, ML
reproducibility/Feature Store, AI Gateway/Model Serving, DASF, platform security/compliance).

Legend: ✅ Covered · 🟡 Partial (coded but blocked, or intent without confirmation) ·
📘 Documented/coded but not deployed · ❌ Not present · ⚪ N/A (out of scope for this POC's
architecture) · ⚠️ Not verifiable from repo (workspace-admin-level setting)

**Update — 2026-08-14, what's since moved** (table rows below left as originally scored —
this is a point-in-time gap analysis, not a living scorecard; re-score explicitly if you want
the table itself updated):
- Ch.1 "Data discovery & classification" (was ❌): column-level UC comments now real for
  Silver (24 applied) — moves toward 🟡, still no systematic tagging/classification beyond that.
- Ch.2 "AI security (DASF)" (was ❌): now ✅ — `docs/DASF_ALIGNMENT.md`, risk-by-risk against
  the actual DASF v1.1 whitepaper, Components 9 & 10.
- Ch.2 "Model monitoring... no toxicity/PII-leakage screening on generated reports" (was ❌):
  moves toward 🟡 — every agent report is now independently fact-checked against its own
  evidence log before saving (`docs/AGENT_RELIABILITY_GUARDRAILS.md`'s evaluator-optimizer
  pass). That's output-*accuracy* monitoring, not toxicity/PII screening specifically — the
  original gap's exact wording is still open.
- Ch.1 "Entity resolution / MDM" (was ❌): a real mechanism exists now —
  `dim_customer.customer_key_mdm`, deterministic exact-match on normalized name+country — but
  it's committed, not deployed (`gold_pipeline` not re-run). Still 📘 at best, and still just
  exact-match, not the fuzzy/probabilistic matching real MDM needs.
- Priority list item 1 (column comments) and item 5 (cite DASF) at the bottom: **done.**
  Items 2 (real UC lineage), 3 (AI Gateway routing), 4 (Lakehouse Monitoring), 6 (account
  groups) are still open.

---

## Chapter 1: Data Governance

| Ebook pillar | Status | Detail |
|---|---|---|
| Data persistence (Delta Lake/DLT) | ✅ | Core to the whole POC — Silver/Gold run as DLT pipelines on Delta tables. |
| Data integration (Workflows/DLT orchestration) | ✅ | `pipelines/silver_dlt.py`/`gold_dlt.py` via Lakeflow, config-driven from `cfg.layer_mappings`. |
| Entity resolution / MDM | ❌ | No dedupe/fuzzy-match logic anywhere (e.g. reconciling the same customer across SAP/JDE/QAD). A real gap given MDM is explicitly named in the JD this repo targets. |
| Data federation (Lakehouse Federation to Snowflake/Oracle/etc.) | ❌ | No federation config anywhere; all sources are ingest-then-transform, never query-federated. |
| Data ingestion (Auto Loader/CDC/Kafka connectors) | 📘 | 14 sources registered in `config/replication_sources.yaml`, real templates exist (`ingestion/templates/`), but Bronze is 100% synthetic one-time seed — no live pipeline runs. |
| Metadata management (UC metastore, catalog hierarchy) | 🟡 | UC catalogs (bronze/silver/gold/products) are real and structurally sound. Ebook's vision includes cataloging *all* asset types (dashboards, notebooks, ML models) — only tables are catalogued here. |
| Data discovery & classification (auto-classification, tags, rich search) | ❌ | Only 2 columns carry a manual `pii` tag; no systematic tagging, no column-level comments anywhere (confirmed empty across the board). Undercuts the "80% of time on discovery" problem the ebook opens with. |
| Access management (RBAC/ABAC) | 🟡 | Row filters + ABAC-style function + GRANTs are real SQL, but the account groups they reference were never provisioned — `PRINCIPAL_DOES_NOT_EXIST`. |
| Auditing entitlements & access | ❌ | Ebook wants "who has access to what, who accessed what, when." POC only audits *agent* actions (`agent_runs`), never queries `system.access.*` for human entitlements/query history. |
| Data lineage | 🟡 | Ebook's pitch is *automatic, real-time* UC lineage. POC hand-maintains lineage as a Python literal (`generate_data_docs.py::EDGES`) rather than reading it from UC's native lineage system tables — `lineage_doc_agent.md` (designed to do this) was never built. |
| Data quality mgmt & monitoring (DLT expectations + Lakehouse Monitoring) | 🟡 | DLT expectations: real. **Databricks Lakehouse Monitoring (the native product)**: not used at all — POC built a fully bespoke check suite (`dq_monitor_rca.py`) instead of the platform-native monitoring/anomaly-detection tooling the ebook centers the whole DQ chapter on. |
| Data intelligence (DatabricksIQ/Genie) | 🟡 | `semantics/sales_metric_view.sql` was explicitly built "so Genie grounds NL questions deterministically" — but nothing confirms Genie is actually configured/enabled in the workspace. |
| Data sharing (Delta Sharing, clean rooms, Marketplace) | 🟡 / ❌ | Delta Share SQL exists, fails on missing metastore privilege. **Clean rooms: not present at all** — never attempted. |

## Chapter 2: AI Governance

The ebook's entire AI-governance chapter assumes **classical ML** (trained models, feature
stores, drift, SHAP). This POC's "AI" is LLM/agentic (Claude tool-calling), not classical ML —
several sections below are a genuine scope mismatch, not just a gap.

| Ebook pillar | Status | Detail |
|---|---|---|
| Compliance & ethics (regulatory input restrictions) | ❌ | No policy anywhere restricting what data can feed AI decisions, no ethics review process. |
| ML reproducibility (Feature Store, MLflow experiment tracking) | ⚪ | No classical model training exists in this POC — no MLflow experiments, no Feature Store usage. Becomes a hard requirement if real ML (e.g. demand forecasting) is ever added. |
| Explainability (SHAP etc.) | ⚪ | No ML models to explain. Closest analog — LLM agent decision logs (`agent_runs.decision_log`) — gives *some* transparency but nothing like feature-attribution explainability. |
| Model monitoring (drift, bias, Lakehouse Monitoring, Inference Tables) | ❌ | No monitoring of Claude output quality, no toxicity/PII-leakage screening on generated reports or `product_creator` output; "drift" doesn't apply without a trained model, but the *spirit* (catching degraded output) has no equivalent for LLM outputs either. |
| Model serving (Databricks Model Serving, MLflow AI Gateway) | ❌ | Concrete gap: `agents/agent_core.py` calls the Anthropic SDK **directly** with a Databricks-secret-stored key. The ebook's recommended pattern — MLflow AI Gateway centralizing credential management, rate limits, and routing for SaaS LLMs — is exactly the control this POC bypasses. |
| AI security (Databricks AI Security Framework — 55 risks / 12 components) | ❌ | Not referenced anywhere. The POC's own guardrails (read-only-SQL-only tool, regex-gated view creation, forced finalization turn, tool budget) are a genuine informal analog to several DASF control categories — just not mapped to the formal framework. |
| Cataloging/documentation for ML (Feature Store + MLflow + UC unified catalog) | ⚪ | No ML models/feature tables exist to catalog. |

## Chapter 3: Platform Security & Compliance

| Ebook pillar | Status | Detail |
|---|---|---|
| Control/data plane, SSO, SCIM, service principals, cluster policies, network security (VPC/VNet, private link) | ⚠️ | Azure workspace-admin-level settings, not application code — can't be confirmed or denied from the repo. Needs a direct check against the workspace admin console. |
| Encryption in transit/at rest, customer-managed keys | ⚠️ | Same — inherited Azure/Databricks defaults unless explicitly configured otherwise. |
| Compliance certifications (ISO 27001, SOC2, HIPAA, PCI, FedRAMP) | ✅ | These are Databricks-the-vendor's certifications, inherited automatically by running on the platform. Not a gap to close — just worth naming correctly if asked. |

---

## What's needed to close the gaps (priority order for a POC/interview context)

1. **Column-level UC comments** — cheapest, highest-leverage fix. Directly addresses the
   "discovery and classification" pillar and the data-dictionary audit finding in one move.
2. **Wire the existing lineage into real UC lineage system tables** instead of the
   hand-maintained `EDGES` list — makes the "automated real-time lineage" claim actually true.
3. **Route the Claude calls through MLflow AI Gateway / Model Serving** instead of a direct SDK
   call — closes the single most concrete AI-governance gap; natural interview talking point
   (centralized credential/rate-limit governance for LLM calls).
4. **Adopt Databricks Lakehouse Monitoring** on at least one Gold table instead of (or
   alongside) the bespoke `dq_monitor_rca.py` suite — shows familiarity with the native
   product, not just a custom reimplementation of it.
5. **Cite the DASF explicitly** and map the existing agent guardrails onto it — low effort,
   since the controls already exist informally.
6. **Finish provisioning the account groups** — this single manual step (already flagged in
   `docs/TRACEABILITY_MATRIX.md`) would flip several "coded but non-functional" items to ✅.
7. Everything else (entity resolution/MDM, Lakehouse Federation, clean rooms, classical-ML
   governance) is legitimately **out of scope** for a POC of this size and can be framed that
   way rather than built.
