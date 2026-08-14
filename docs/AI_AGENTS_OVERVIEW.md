# AI Agents — architecture, deployment, per-agent detail, and where the design still has to grow

One document meant to answer five questions at once: what exists, how it's deployed, what each
agent actually does, why it matters to the business (not just the platform), and — honestly —
what's still missing. Every claim below is either grounded in a file:line citation or in a live
verification run from this build (dates given); nothing here is aspirational unless explicitly
labeled `design` or `not yet`.

## 1. The shape of it, in one paragraph

Ten agents live in `agents/`, deployed as two Databricks Jobs (`acme_agents_scheduled`,
`acme_agents_on_demand`) via a Databricks Asset Bundle, sharing one contract defined once in
`agents/agent_core.py`. Every agent runs a **deterministic phase first** — real SQL checks, table
builds, drift scans — which produces the agent's core artifact whether or not a model is even
reachable. An **LLM reasoning phase** then runs on top, strictly additive, with exactly one tool
(`run_sql`, hard-guarded to read-only statements) and, since 2026-08-14, a second **independent
verification pass** that fact-checks the first pass's own report against the evidence it actually
gathered before anything is saved. All ten were confirmed live via `databricks jobs
get-run-output` on 2026-08-14 — not just `bundle validate`.

## 2. Architecture — the shared contract

Every agent is built on the same four guarantees, enforced once in `agent_core.py` rather than
re-implemented per agent (so a new agent inherits them for free, and can't quietly skip one):

| Guarantee | Mechanism | Why it matters |
|---|---|---|
| **The platform never depends on a model being up** | Deterministic phase always runs and writes the artifact; the LLM pass is optional and additive. No key → agent logs `"deterministic mode"` and still completes. | An LLM outage never becomes a data-platform outage. |
| **The model's only action surface is read-only SQL** | `safe_sql()` rejects anything not starting with `SELECT/WITH/SHOW/DESCRIBE`, or containing a semicolon, before it reaches Spark. Allowlist, not denylist — fails closed. | The model can misinterpret data; it structurally cannot corrupt it. |
| **Every claim is checked against its own evidence before saving** | `verify_report()` — a second, separate Claude call, no tools — checks the draft against the `run_sql` log (queries *and* their returned values) and appends both the evidence log and its verdict to the report. | Catches the class of error a single-pass agent can't see in itself: correctly querying real data, then misreporting what it found. Caught a real gap in its own supporting code on its first live run — see §7. |
| **Full audit trail, human owns every merge** | Every tool call + result logged to `acme_bronze.audit.agent_runs`; narrative output to `acme_bronze.audit.agent_reports`. Agents propose (a report, a draft SQL statement); they never auto-write outside their own audit tables. | Auditable like any pipeline, not a black box. Matches Anthropic's own "human control & approval gates" guidance for agents — see §6. |

## 3. Deployment — how it actually runs

**Infrastructure as code, not click-ops.** `databricks.yml` + `resources/agents.yml` declare
everything; `databricks bundle deploy -t dev` reconciles declared vs. live state. No hand-built
jobs, no notebook copy-paste.

**Two jobs, task-DAG orchestration** — deliberately ordinary. This is the one thing worth being
precise about in an interview: the *orchestration* here is nothing exotic, it's Databricks Jobs'
native task graph, the same mechanism you'd use for any ETL DAG. The only thing that's new is that
some task nodes reason instead of transform.

```
acme_agents_scheduled   -- daily 06:00 UTC cron -- currently PAUSED, run manually today
  dq_monitor_rca ──┬──► dq_rca_agent       (depends_on: dq_monitor_rca)
                   └──► operational_intel  (depends_on: dq_monitor_rca)
  pipeline_healer      (no data dependency — sibling task)
  lineage_doc_agent    (no data dependency — sibling task)

acme_agents_on_demand   -- triggered by job param `product_request`/`dry_run` or manual run
  schema_evolution · ingestion_registrar · vector_content · deployment_gate · product_creator
```

**Compute**: both jobs run on serverless job compute — no clusters defined anywhere.
**Secrets**: one Databricks secret scope, `agents/anthropic_api_key`, resolved via
`databricks.sdk.runtime.dbutils` first (the `WorkspaceClient().dbutils` fallback proved flaky on
serverless — logged, not guessed). **Environment**: `environment_version: "3"`, dependency
`anthropic` (plus `pyyaml` for the on-demand job, needed by `ingestion_registrar`).

## 4. The ten agents

Each row: what it owns, what the deterministic pass produces on its own, what the LLM pass adds
on top.

| Agent | Owns | Deterministic output | LLM reasoning adds |
|---|---|---|---|
| **dq_monitor_rca** | Bronze→Silver DQ gates | Runs 10 DAMA-dimension checks, writes `audit.dq_results` | Root-cause narrative on any breach — verifies the failure itself via `run_sql` before concluding |
| **dq_rca_agent** | Deeper DQ correlation | Reads latest failing checks from `dq_results` | Correlates against `batch_log` ⨝ `source_registry` — a second, independent pass, not a duplicate of the first agent's RCA |
| **pipeline_healer** | Pipeline-failure triage | Scans recent pipeline events via the Databricks SDK | Classifies schema drift / bad records / infra / code, drafts type-specific remediation — never executes it |
| **lineage_doc_agent** | Auto-generated lineage docs | Builds edges from live `cfg.layer_mappings` | Mermaid diagram + prose; explicitly says so when `system.access.table_lineage` isn't reachable, rather than inventing edges |
| **operational_intel** | Platform-wide observability | Gathers the daily metric set (row counts, freshness, backlog, DQ failures) | Composes the daily digest, with self-directed drill-downs (e.g. top backlog accounts) |
| **schema_evolution** | `cfg.layer_mappings` / Bronze contract | Diffs Bronze `information_schema` against active mappings | Drafts versioned mapping-row INSERT proposals for drifted columns — never executed |
| **ingestion_registrar** | `replication_sources.yaml` validation | Validates every source row (pattern, PK, expectations, region, naming), cross-checks `cfg.source_registry` | Onboarding summary — what's unregistered, the exact command to fix it |
| **vector_content** | Gold AI zone / semantic search | Rebuilds `customer_narratives` from dim + fact tables | QA-reviews samples for retrieval-relevant specificity, catches real corpus artifacts |
| **deployment_gate** | CI/CD verification | Runs the *same* 14 checks as `scripts/validate.py` — imported, not duplicated | Classifies each failure as regression vs. known/tracked gap, issues PROMOTE/HOLD |
| **product_creator** | Gold → Products output ports | — | NL request → SQL view in `acme_products`, validated through a regex allowlist before executing; `dry_run=true` proposes without creating, for human review first |

Guardrails on all ten, one shared contract: read-only on prod data via one guarded SQL tool ·
12-turn tool budget with forced finalization · independent verification pass before saving ·
full decision audit · human owns the merge button.

## 5. How this helps Nucor's principals

Nucor publishes ten named culture principles as **"The Nucor Way"** (nucor.com/company/,
nucor.com/careers/ — fetched directly, 2026-08-14, not recalled from training data): Safety,
Integrity, Trust, Innovation, Open Communication, Teamwork, Inclusion, Can-Do Attitude, Courage,
Ownership. Mapping every technical decision in this platform onto all ten would be forcing it —
the honest version only claims the ones with a real, citable design decision behind them:

| Nucor value | Nucor's own words | What in this platform actually earns the claim |
|---|---|---|
| **Trust** | "We have confidence in each other as we relentlessly pursue winning." | The entire deterministic-first architecture (§2) exists so a person can trust an agent's *facts* without trusting the model — checks and digests are real SQL results whether or not the LLM is even reachable. Trust is designed in, not asked for. |
| **Integrity** | "We back up our words with actions and honor our commitments." | `verify_report()` (§2, §7) is integrity as a mechanism, not a value statement: no report is saved until a second, independent pass confirms every claim in it is backed by the evidence actually gathered. It caught a real gap in its own supporting code on its first live run — the mechanism did what it was built to do, not just what it was described to do. |
| **Open Communication** | "We communicate transparently... willing to have challenging conversations." | §8 of this very document. An interview deliverable that only listed what works would be the easy version; this one names the account-groups dead end, the unscreened-output gap, and the paused cron in the same document as the wins, because that's what "transparent" has to mean when it's not free. |
| **Can-Do Attitude** | "We rise to the challenge by turning obstacles into opportunities." | The RAG-agent and bronze-ingestion blockers (missing warehouse, unconnected storage account, no account-level access) were investigated fully rather than waved off — each one converted into a precise, actionable blocker description (§8) instead of a vague "not done." That's the difference between an obstacle and an open ticket. |
| **Courage** | "We stand up for what we believe in and do what's right, even when it's difficult." | Choosing to report `verify_report()`'s first real catch (§7) as a success story about the guardrail — instead of quietly fixing it and saying nothing — is the harder, more honest story to tell in an interview setting. |
| **Ownership** | "We take on the responsibility each of us has for Nucor's continued success." | No agent in this design auto-applies anything outside its own audit tables (§2) — `product_creator`'s `dry_run` flag, `schema_evolution`'s draft-only proposals, `pipeline_healer`'s draft-not-executed remediations. Ownership of every real change stays with a person, by construction, not by policy memo. |
| **Innovation** | "We embrace creativity and embody curiosity, always searching for better solutions." | The evaluator-optimizer verification pass, the evidence-logged audit trail, and the shared `agent_core.py` contract weren't required to make ten scripts run — they were added specifically in response to reading Anthropic's own current reliability guidance and finding this design short of it (§7). |

**Safety, Teamwork, and Inclusion are left out of this table deliberately.** Nucor's stated
meaning for Safety is physical and emotional well-being on a plant floor — stretching it to mean
"the SQL guardrail is safe" would be exactly the kind of forced mapping this document argues
against elsewhere. Teamwork and Inclusion are genuine Nucor culture commitments about how people
treat each other; a data platform doesn't produce evidence about either one, and claiming it does
would be empty. Better to name six real connections than ten hollow ones.

## 6. Databricks / AI-security guidelines this design is measured against

Two separate reference frameworks were used to ground this design, not just described in the
abstract — both fetched and read directly, not recalled from training data:

**Databricks AI Security Framework (DASF v1.1)** — 55 risks across 12 components. This platform
is a hosted-LLM *consumer* (a tool-using client of the Anthropic API), which maps onto Component 9
(Model Serving / Inference Requests) and Component 10 (Inference Responses) — not the
model-training components, which don't apply here. Full risk-by-risk mapping in
`docs/DASF_ALIGNMENT.md`; the honest summary:

| DASF risk | Status | Evidence |
|---|---|---|
| 9.1–9.9 (prompt injection, unbounded tool access) | ✅ covered | One read-only tool, hard-guarded allowlist, full audit log |
| 9.10 (excess data exposure via job identity) | 🟡 open gap | Job identities currently read broadly across catalogs; scoped account-group identities are designed (`security/unity_catalog_policies.sql`) but blocked on the same account-group provisioning gap as RBAC — confirmed 2026-08-14 that this workspace's credentials have no account-level API access at all |
| 10.1–10.2 (unscreened output, PII leakage) | 🟡 open gap | The verification pass (§7) checks output *accuracy* against evidence, not PII/toxicity — a human still reads every report, nothing programmatic screens it yet |
| 9.10, write path (agent-initiated corruption) | ✅ covered | No agent has DDL/DML access; the one agent that emits SQL (`product_creator`) validates it through a regex allowlist + forbidden-verb denylist first |

**Databricks' own governance ebook** ("A Comprehensive Guide to Data and AI Governance") — full
39-page PDF extracted and compared chapter by chapter in
`docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md`. The AI-governance chapter assumes classical ML
(feature stores, drift, SHAP); this platform's "AI" is LLM/agentic, so several of its sections are
a genuine scope mismatch, not a gap — flagged as such rather than force-fit. The concrete,
in-scope gap it named: this design calls the Anthropic SDK directly with a Databricks-secret-held
key, rather than routing through MLflow AI Gateway / Model Serving, which is the platform-native
pattern for centralizing LLM credential/rate-limit governance. Still open.

## 7. What was actually broken, and how it got fixed (2026-08-13 → 2026-08-14)

Not a list of intentions — every line below is a real defect, found live, fixed, and
re-verified, not just described:

- **`ingestion_registrar` reported job-level SUCCESS while doing zero validation.** `open()` on
  the synced YAML hit `[Errno 5] Input/output error` against the workspace filesystem path — a
  serverless-only flakiness none of the other agents hit, because they all read through
  `spark.sql()`, not a raw filesystem call. Its own error handling caught the exception and logged
  `YAML_UNREADABLE` cleanly — visible in the audit log, but invisible to anyone just watching the
  Jobs UI for green/red. Fixed: falls back to the Databricks SDK's Workspace Files API when
  `open()` fails. Re-run: all 14 sources validated clean.
- **Four gaps found comparing this design against Anthropic's own current published agent-
  reliability standards** (fetched live — Reduce Hallucinations, Trustworthy Agents in Practice,
  Building Effective AI Agents, Effective Harnesses for Long-Running Agents — not recalled from
  training data). All four closed the same session, full comparison in
  `docs/AGENT_RELIABILITY_GUARDRAILS.md`:
  1. No evaluator-optimizer pass → added `verify_report()`, a second independent Claude call.
  2. No inline citations in the saved report → the evidence log (queries *and* values) is now
     appended to every report, not just kept in `agent_runs` where nobody reads it.
  3. No eval suite → `scripts/eval_agent_reports.py`, deterministic, scores each agent's
     verified/flagged rate over time — no LLM in the loop, so the eval itself can't hallucinate.
  4. No Plan-Mode option for the one agent that writes → `product_creator` got an opt-in
     `dry_run` job parameter (default `false`, existing behavior unchanged).
- **The evaluator pass caught a bug in its own supporting code, on its first real run.**
  `dq_monitor_rca`'s first run under the new verification pass got genuinely flagged: the evidence
  log recorded which queries ran but not their *returned values*, so several numbers in the report
  weren't strictly re-confirmable from the log alone. Fixed the same session (`safe_sql()` now
  logs a value snippet per query) and reconfirmed. This is the single best piece of evidence for
  the whole reliability effort: not "the guardrail should work," but "the guardrail worked, on its
  first try, against code that had existed for weeks."
- **`dq/quarantine_writer.py` had never actually been executed** — the one real writer for
  `acme_bronze.audit.batch_log` and `.rejected_records`, present in the repo and even synced to
  the workspace by every deploy, but wired into no job. Running it for the first time (2026-08-14)
  surfaced two more real bugs: `layer` was hardcoded to `'bronze'` for every row, including
  obviously-Gold flows; and the `rejected_records` write used a column set that didn't match the
  live table at all (`DELTA_METADATA_MISMATCH` on first attempt). Fixed both, re-ran clean:
  `batch_log` now has 151 correctly-labeled rows, `rejected_records` has 5 — all real, all
  correctly identifying the already-known QAD customer-FK gap instead of being empty. Now wired
  into a real (paused) job, `resources/dq.yml`, instead of being a file nobody calls.
- **Six agents → ten, and every doc that still said six.** Two docs (`docs/CODE_GRAPH.md`,
  `docs/TRACEABILITY_MATRIX.md`) still said "six agents" after a tenth was added and deployed —
  caught only once every `.md` file in the repo was actually being read at session start (a
  `CLAUDE.md` rule change, itself prompted by this exact staleness). Fixed, plus a repo-wide sweep
  for every other "committed but not deployed" reference that had gone stale the same way.

## 8. What still needs structural work — named honestly, not hidden

Ranked by what actually blocks something, not by effort:

1. **Account groups are not provisionable from here at all.** Tested directly, 2026-08-14: this
   workspace's CLI credentials have zero account-level API access (`databricks account groups
   list` returns `Not Found`, not a permission error — the token simply isn't scoped for it).
   Every job identity currently reads broadly across catalogs (DASF 9.10) because the
   account-group-scoped identities designed in `security/unity_catalog_policies.sql` can't be
   created without a different actor entirely — genuine Databricks/Azure account-admin rights,
   which this session's credentials don't have and can't escalate to.
2. **No output-quality/PII screening on generated reports (DASF 10.1/10.2).** The verification
   pass checks accuracy against evidence; nothing checks for sensitive content before a report
   lands in `agent_reports`. A human still reads every one, but that's the only control.
3. **No Best-of-N / self-consistency check.** Deliberately skipped, not forgotten — the evaluator
   pass already covers most of what Best-of-N would catch, and running every agent twice doubles
   cost/latency for a mostly-overlapping benefit. Revisit if the eval scorecard (§7) starts
   showing a real gap this wouldn't close.
4. **No eval suite scoring *correctness*, only *evidence-groundedness*.**
   `scripts/eval_agent_reports.py` measures whether claims trace back to a query — it has no
   golden-answer regression set, so it can't yet tell you whether `dq_rca_agent`'s root-cause
   conclusion was actually the *right* one, only that it was evidenced.
5. **Static job definition — an 11th agent means hand-editing YAML.** `resources/agents.yml`'s
   task list is not generated from a registry the way the Silver pipeline's column mappings are.
   At real multi-domain scale this should be config-generated the same way.
6. **No real trigger loop.** Every agent runs on a schedule or on-demand parameter — none are
   triggered by the event their original `.md` spec named (a job-failure webhook, a PR, a DQ
   breach). No GitHub token or Slack webhook is provisioned in this workspace, so this is a
   deliberate scope cut, not an oversight — but it means "self-healing" today means "healing when
   someone remembers to run the job."
7. **Not a Ralph loop.** Every agent is single-shot: one system prompt, one tool-budget-bounded
   pass, one report, done. No agent re-invokes itself against its own prior output, no goal-until-
   verified loop exists. `docs/ralph_loop.md` has the full deployment checklist for what closing
   this gap would actually take — it's a real design, not a wish list, just not built.
8. **Model tiering doesn't exist.** Every agent uses the same model at the same effort setting,
   set once in `agent_core.py`. A cheap/fast model for digests and QA passes, a higher-effort
   model reserved for RCA and product creation, would be the natural next cost lever — not done.
9. **The scheduled job's cron is still `PAUSED`.** Nothing runs unattended. Every result cited in
   this document came from a manually triggered run.
