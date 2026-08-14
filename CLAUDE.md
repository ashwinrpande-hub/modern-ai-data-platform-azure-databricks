# CLAUDE.md — session guide

Rules for any Claude Code session in this repo:
1. **Read every tracked `.md` file at the start of the session** — `agents/*.md`, `docs/*.md`,
   and the top-level `*.md` files (`README.md`, `CHANGES.md`, `README_APPLY.md`,
   `marketplace-ui/README.md`). As of 2026-08-14 that's ~26 files / ~29K words (skip `Old/` —
   a superseded design kept for reference only; see `docs/GAP_ANALYSIS.md` D5 on removing it).
   This replaces the previous "read only what the task needs" rule: lazy loading is exactly
   what let docs drift stale across this repo (see rule 7's examples). Only the harness's
   automatic load of this file is free; reading the rest is a real, deliberate cost the repo
   is currently small enough to afford — if the doc set grows enough to make this a genuine
   token-budget problem, revisit the rule explicitly rather than silently reverting to it.
2. **Only touch code that is necessary.** Config-driven design means most changes are YAML/config-table rows, not code.
3. **Never assume**: if a mapping, source system, or schema is unknown, ask the user interactively before writing code.
4. **Log as you go, not just at the end.** Every code change *and* the reasoning/discussion
   behind it goes into `docs/SESSION_NOTES.md` (append-only, dated) — or the more specific doc
   it belongs to (security → `docs/DASF_ALIGNMENT.md`, agent reliability →
   `docs/AGENT_RELIABILITY_GUARDRAILS.md`, package-level file lists → `CHANGES.md`). Don't wait
   for "the session is getting long" or for a session to end: `docs/SESSION_NOTES.md` went two
   full days (2026-08-13, 2026-08-14) without an entry despite major changes, because logging
   was treated as an end-of-session task instead of a running one. Traceability needs the *why*,
   captured near the *when* — not reconstructed later from `git log`.
5. Source-of-truth order: config tables > YAML in `config/` > code defaults.
6. All new ingestion = a row in `config/replication_sources.yaml` + the matching template in `ingestion/templates/`. Do not fork templates.
7. **After any change, grep the docs for what it just made stale, and fix it in the same
   session.** A count that changed (agent totals), a code snippet that no longer matches
   reality (a simplified RBAC function vs. the real one), a status this change just resolved
   (an audit doc's "❌ not present" item that's now ✅) — catching it now is strictly cheaper
   than catching it later, and "later" here has concretely meant an interviewer finding it
   instead. This repo has real, on-record examples of both failure modes: `docs/CODE_GRAPH.md`
   and `docs/TRACEABILITY_MATRIX.md` both still say "six agents" after a tenth was added and
   deployed; `dashboards/dq_trust_dashboard.sql` had column names that stopped matching the
   live schema and nobody noticed until it was run. Machine-generated docs (`docs/DATA_MODEL.md`,
   `docs/DATA_CATALOG.html` — marked "do not hand-edit") get flagged as needing regeneration,
   not hand-patched. Point-in-time audit snapshots (`docs/GOVERNANCE_DQ_INGESTION_AI_AUDIT.md`,
   `docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md`) get an annotation noting what's since
   changed, not a silent rewrite — keep the record of what was found vs. later fixed intact,
   the way `docs/AGENT_RELIABILITY_GUARDRAILS.md` does it.

## Map of the repo (for quick navigation, not a substitute for rule 1)
- Replication patterns → `docs/REPLICATION_PATTERNS.md`
- Pipeline graph → `docs/CODE_GRAPH.md`
- Decisions + alternatives → `docs/JUSTIFICATION_NOTES.md`
- Agent reliability / hallucination guardrails → `docs/AGENT_RELIABILITY_GUARDRAILS.md`
- Agents specs → `agents/`
