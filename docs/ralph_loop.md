# Agent self-sufficiency loops ("Ralph loops") — research + deployment checklist

Status: **planning only, nothing implemented yet.** Captured 2026-08-12.

## What a Ralph loop is

There is no "RALF loop" — the real, current (2026) term is the **Ralph loop** (aka "Ralph
Wiggum loop"), coined by Geoffrey Huntley in mid-2025, now mainstream in agentic-coding
circles. OpenAI shipped it as a first-class `/goal` primitive in Codex CLI 0.128.0 in
April 2026.

Core mechanics:
- A coding agent runs inside a plain `while` loop against **one stable goal prompt**.
- Each iteration starts a **fresh context** — no accumulated conversation memory.
- Progress persists in **files + git**, not in the model's context window — the repo *is*
  the memory.
- Each pass does one unit of work, checks a **verification gate**, and either exits (goal
  met) or leaves state for the next pass to pick up.
- Unpredictability of any single run averages out over many runs against a stable target.

Sources:
- https://ghuntley.com/loop/ (primary source, Geoffrey Huntley)
- https://linearb.io/blog/dex-horthy-humanlayer-rpi-methodology-ralph-loop
- https://www.alibabacloud.com/blog/from-react-to-ralph-loop-a-continuous-iteration-paradigm-for-ai-agents_602799
- https://ralphloop.sh/

## How this maps onto this repo today

Grounded in `agents/agent_core.py`, `resources/agents.yml`, and `agents/pipeline_healer.md`
(read 2026-08-12, not assumed):

- The **six live agents** (`dq_monitor_rca`, `schema_evolution`, `operational_intel`,
  `vector_content`, `product_creator`, `deployment_gate`) are **single-shot**: deterministic
  checks run, optionally one Claude reasoning pass (max 12 tool calls, read-only SQL only),
  write a report to `acme_bronze.audit.agent_reports`, done. No looping, no retry, no
  self-evaluation of "am I done."
- The **loop/PR/webhook behavior is only aspirational** — `agents/pipeline_healer.md`,
  `dq_rca_agent.md`, `ingestion_registrar.md`, `lineage_doc_agent.md` describe a different
  design (webhook-triggered, GitHub MCP for PRs, Slack, retry/classify loops) that was
  **never implemented**. No GitHub token/App wiring exists anywhere in the repo (confirmed
  via grep — zero hits outside the spec docs).
- What's already in place and matches the Ralph-loop precondition: **state lives outside the
  model** (`acme_bronze.audit.agent_runs`/`agent_reports`, config tables like
  `replication_sources.yaml`/`layer_mappings`), not in conversation history. Most of "memory
  in files, not context" is already done.
- Human-gate principle already stated in `agents/README.md`: *"agents open PRs / propose
  fixes; never auto-merge to main."* A Ralph loop here should still terminate at a PR, not a
  direct write.
- `acme_agents_scheduled` job is currently `PAUSED` (per session state as of 2026-08-02) —
  a loop needs an active trigger, not a dormant cron.

## Deployment checklist — Azure Databricks

### A. Loop mechanics (per agent, code-level)
- [ ] Define a **goal prompt** per agent (e.g., "drive `dq_results` for X to green" / "get
      `deployment_gate` to PROMOTE") — replaces the fixed single-shot system prompt in
      `agent_core.py`.
- [ ] Add a **verification gate function** the loop can actually run each pass (re-query the
      check it's trying to fix) — not "the LLM says it's done."
- [ ] Add an **iteration cap** per invocation (Ralph loops without a cap = runaway spend).
- [ ] Decide **where loop iterations persist**: extend `agent_runs`/`agent_reports` with a
      `goal_id`/`iteration` column so a loop is a sequence of rows, not one row.
- [ ] Keep the existing guardrail: model's only write path is still a proposed diff/PR/config
      row — never a direct table write.

### B. Git-as-memory + human gate (doesn't exist yet)
- [ ] Provision a **GitHub App or fine-grained PAT** scoped to this repo only (least
      privilege: open PRs, no direct push to `main`/`dv2`).
- [ ] Store it as a **Databricks secret** (new scope, e.g. `agents/github_token`) — same
      pattern as `agents/anthropic_api_key`.
- [ ] Add PR-opening as a real tool in `agent_core.py` (currently the model's only tool is
      `run_sql`) — a second, carefully-scoped write action, needs its own guardrail review.
- [ ] Decide: does the loop read its own **prior PR status** (open/merged/closed) as part of
      "am I done," so a merged fix ends the loop?

### C. Databricks Jobs / compute
- [ ] Decide job shape: **one long-running loop task** vs. **Jobs-triggers-itself pattern**
      (task completes one iteration, triggers a new job run — safer on serverless, which
      isn't built for long-lived processes).
- [ ] If self-triggering: use Databricks SDK `WorkspaceClient().jobs.run_now()` from within
      the task, with iteration count passed as a job parameter and a hard max.
- [ ] Unpause or redesign `acme_agents_scheduled` (currently `PAUSED`) — a loop needs an
      active trigger, not a dormant cron.
- [ ] Confirm `agent_env` environment (`environment_version: 3`, deps `["anthropic"]`) also
      gets a GitHub client dependency (`PyGithub` or plain `requests` against the REST API).

### D. Cost & runaway controls
- [ ] Per-loop **token/dollar budget**, not just a step cap.
- [ ] A **circuit breaker**: N consecutive failed verification checks → loop stops and files
      a report instead of continuing silently.
- [ ] Job-level **timeout** in `resources/agents.yml` as a hard backstop independent of the
      in-code cap.

### E. Observability
- [ ] Extend existing audit tables (don't build new infra) so a loop's iterations are
      queryable as a group — add `goal_id` to `acme_bronze.audit.*`.
- [ ] Surface loop status somewhere a human checks without querying SQL — Slack webhook
      (mentioned in `pipeline_healer.md`, never wired) or a row in `deployment_gate`'s
      existing report.

### F. Azure/secrets
- [ ] New Databricks secret scope entry: `agents/github_token` (and rotate-ability — owner
      of renewal).
- [ ] Optional, more enterprise-y: mirror the secret in Key Vault and reference via
      Databricks' Key-Vault-backed secret scope instead of a Databricks-native scope. Not
      required for POC.

### G. Before flipping it on
- [ ] Dry-run one agent as a loop **against a scratch branch**, cap iterations low (3–5),
      confirm it opens a sane PR and stops. Candidate: `schema_evolution` — smallest blast
      radius, already read-only-scanning.
- [ ] Update `docs/TRACEABILITY_MATRIX.md` and `agents/README.md` once real — don't let docs
      drift ahead of code the way `pipeline_healer.md` already has.

## Open decisions (not yet made)
- Which agent gets a loop first.
- What "done" means per agent (the verification gate definition).
- Whether PR-opening is worth the new write-scoped GitHub credential for a POC/interview
  repo, versus just widening the report the agent already writes.
