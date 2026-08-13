# Alignment with the Databricks AI Security Framework (DASF v1.1)

Status: mapping only — cites the actual DASF whitepaper (55 risks across 12 components,
`databricks-ai-security-framework-dasf-whitepaper-v4-final.pdf`), not a paraphrase. Captured
2026-08-13.

This repo's agents (`agents/agent_core.py`) don't serve a trained model — they call a hosted
third-party model (Claude) with a constrained tool surface. That maps almost entirely onto
DASF **Component 9 (Model Serving — Inference Requests)** and **Component 10 (Inference
Responses)**, the 15 risks under "Model deployment and serving." Components 1–8 (raw data
through model build/management) mostly describe *training* a model, which doesn't apply
here — see [docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md](DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md)
for the ⚪ N/A framing on classical-ML governance already established. Component 12 (ML
platform) risks are workspace-admin-level, covered under Chapter 3 of that same doc.

Legend: ✅ Covered · 🟡 Partial · ❌ Gap · ⚪ N/A (doesn't apply to a hosted-model consumer)

## Component 9: Model Serving — Inference Requests

| Risk | Status | Evidence |
|---|---|---|
| 9.1 Prompt injection | 🟡 | The model's only action surface is `run_sql`, hard-guarded to single read-only statements (`agent_core.py::safe_sql` — rejects anything not starting `SELECT/WITH/SHOW/DESCRIBE`, rejects multi-statement via `;`). A successful injection still can't cause a write. But nothing sanitizes untrusted *data* the model reads before it's fed back into the model's context (e.g. a crafted value in a source table read via `run_sql` could carry injected instructions) — no input-side filtering exists. |
| 9.2 Model inversion | ⚪ | Applies to extracting a proprietary trained model's parameters/training data. We don't host or train the model. |
| 9.3 Model breakout | ✅ | All writes happen in deterministic framework code after validation, never directly from the model (`agent_core.py` docstring, lines 3-9). `product_creator.py` additionally regex-gates its one write-adjacent output (a view DDL string) to `CREATE OR REPLACE VIEW acme_products.sales.*` reading `acme_gold` only. |
| 9.4 Looped input | ✅ | `MAX_STEPS = 12` tool-call budget with a forced finalization turn (`tool_choice: {"type": "none"}`) when exhausted — bounds runaway tool-calling loops. |
| 9.5 Infer training data membership | ⚪ | Same as 9.2 — not applicable to a hosted-model consumer. |
| 9.6 Discover ML model ontology | ⚪ | Not applicable — we don't expose model internals. |
| 9.7 Denial of service (DoS) | 🟡 | The 12-step budget bounds cost per *agent run*, but there's no cross-run rate limit or dollar budget — a scheduled job misfiring repeatedly could still run up spend. Flagged as a gap in [docs/ralph_loop.md](ralph_loop.md) section D (cost & runaway controls) for any future looping design. |
| 9.8 LLM hallucinations | 🟡 | System prompts explicitly instruct the model to call `run_sql` for any claim needing evidence ("never guess row counts or values" — `dq_monitor_rca.py::RCA_SYSTEM`), and deterministic checks always compute ground truth *before* the model reasons over it. No output-side fact-checking against the deterministic results, though — the model could still misstate something in its prose that contradicts the numbers it was given. |
| 9.9 Input resource control | ✅ | `safe_sql(..., max_rows=50)` caps result size per query; the 12-step budget caps total queries per run. |
| 9.10 Accidental exposure of unauthorized data to models | ❌ | The agent jobs run under a job/service identity with broad read access across `acme_bronze/silver/gold` needed to run the deterministic checks — not scoped per end-user, and the row filters/masks that would narrow this (`security/unity_catalog_policies.sql`) are non-functional today because the account groups they reference were never provisioned (see [docs/GOVERNANCE_DQ_INGESTION_AI_AUDIT.md](GOVERNANCE_DQ_INGESTION_AI_AUDIT.md)). The model only sees what `run_sql` returns, but nothing today prevents that query from reaching data the *human* reading the report shouldn't see. |

## Component 10: Model Serving — Inference Responses

| Risk | Status | Evidence |
|---|---|---|
| 10.1 Lack of audit and monitoring of inference quality | 🟡 | Every tool call, its query, and the result summary is appended to a decision log persisted in `acme_bronze.audit.agent_runs`; final reports land in `agent_reports` — full audit trail of *what the model did*. But nothing evaluates output *quality* — no toxicity/PII-leakage screening on generated report text, no factuality scoring. Audit: yes. Quality monitoring: no. |
| 10.2 Output manipulation | ❌ | No validation on the free-text report content itself (beyond `product_creator`'s regex gate on the one structured SQL output it produces). A report's prose isn't checked for injected instructions surfacing from upstream data before a human reads it. |
| 10.3 Discover ML model ontology | ⚪ | N/A — hosted-model consumer. |
| 10.4 Discover ML model family | ⚪ | N/A — hosted-model consumer. |
| 10.5 Black-box attacks | ⚪ | N/A — hosted-model consumer. |

## What's needed to close the real gaps here

1. **9.10 (data exposure) is the one that matters most** — and it isn't a new problem, it's the same account-group-provisioning gap blocking RBAC/masking everywhere else in this repo. One fix closes both.
2. **10.1/10.2 (output quality/manipulation)** — no code exists today to screen agent-generated report text before it lands in `agent_reports`. A lightweight addition: a second Claude pass (or a simple keyword/pattern check) scanning the report for PII patterns or instruction-like text lifted from source data, before `save_report()` persists it.
3. **9.7 (cross-run DoS/cost)** — already flagged in `docs/ralph_loop.md`; only matters if/when this repo moves toward looping agents rather than single-shot runs.
4. Everything marked ⚪ requires no action — it's a framework/architecture mismatch (DASF assumes you're serving a model you trained), not a gap in this repo.
