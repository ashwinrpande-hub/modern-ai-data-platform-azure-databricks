# Agent reliability guardrails: what stops hallucination, and how it compares to Anthropic's current standards

**Update:** the four closable gaps found below (evaluator-optimizer pass, inline citations,
an eval scorecard, and a Plan-Mode option for the one agent that writes) were implemented the
same session this doc was written — see "Closed this session" at the bottom. The comparison
table and gap list below are left as originally written, then annotated, so the record of
what was found vs. what was fixed stays honest and traceable.

**Direct answer to "is this documented in the md file?": no, not centrally.** The 10 `agents/*.md`
spec files (the original one-paragraph specs for `pipeline_healer`, `dq_rca_agent`,
`ingestion_registrar`, `lineage_doc_agent`) say nothing about hallucination — they only cover
triggers, tool access, and *write*-safety ("never merge", "read-only on prod data").
`docs/AGENT_ARCHITECTURE.html` documents a "Guardrails" section, but it's framed entirely around
write-safety (the read-only tool, deterministic-writes-only, tool budget) — it never uses the word
"hallucination" and doesn't frame the design as an accuracy measure. The actual anti-hallucination
instructions are real and working, but they live scattered across `agent_core.py` and individual
system prompts in the `.py` files, not written down anywhere as a named policy. **This doc is that
missing writeup**, plus the comparison you asked for.

## Sources consulted (current, fetched live — not from training-data memory)

- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — Claude Docs
- [Trustworthy agents in practice](https://www.anthropic.com/research/trustworthy-agents) — Anthropic Research
- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Anthropic Engineering
- [Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic Research

## Legend

✅ done and verified live · 🟡 partial / inconsistent · ❌ missing

## Comparison

| Standard (source) | Status | Evidence in this repo |
|---|---|---|
| **External knowledge restriction** — ground every claim in provided data, not general knowledge (*Reduce hallucinations*) | ✅ | `agent_core.py:98-100` — the *one* tool every agent shares, `run_sql`, is described as: *"Call this whenever a claim needs evidence — **never guess row counts or values**."* Applies uniformly to all 10 agents since they all import this same tool definition — not a per-agent copy-paste that could drift. |
| **Allow the model to say "I don't know"** (*Reduce hallucinations*) | ✅ | `lineage_doc_agent.py:29` — system prompt: *"This is a factual restatement of the edges you were given — **do not invent tables or edges that weren't in the input**."* Proven live in today's actual run: when `system.access.table_lineage` wasn't queryable, the agent wrote *"I confirmed that Unity Catalog's native lineage isn't accessible to me (insufficient privileges)... so no silver/gold-side edges were available"* instead of fabricating them. `vector_content` and `operational_intel` did the same live today when their data sources were unreachable — see `docs/SESSION_NOTES.md` / today's run output. |
| **No invented figures** (*Reduce hallucinations* — "external knowledge restriction") | 🟡 | `operational_intel.py:42` states it explicitly: *"no invented figures — every number must come from the metrics given or your own queries."* Not every agent's prompt repeats this in words, but the shared `run_sql` tool description (above) enforces the same rule structurally for all 10. |
| **Verification loop / evidence before conclusion** (*Reduce hallucinations* — chain-of-thought verification; *Building Effective Agents* — evaluator-optimizer) | 🟡 → **✅ CLOSED** | `dq_monitor_rca.py:53-54`, `dq_rca_agent.py:31`: *"You are READ-ONLY: investigate with the run_sql tool... (1) verify the failure yourself, (2) find the earliest evidence."* was already real. Now backed by a genuine second pass — see "Closed this session". |
| **Citations / auditable claims** (*Reduce hallucinations* — "verify with citations") | 🟡 → **✅ CLOSED** | Was: evidence lived only in `agent_runs`, not surfaced in the report. Now: every LLM-mode report carries an "Evidence log" section inline — see "Closed this session". |
| **Human control & approval gates**, tiered permissioning (*Trustworthy agents in practice*) | ✅ (simpler than the standard, but consistent) | Hard rule across all 10 agents: *"agents propose fixes into their reports; never auto-merge... never write outside their own audit tables"* (`agents/README.md:18-19`). Anthropic's model is a *tiered* permission system (always-allow / needs-approval / block, per tool); this repo uses a *blanket* one (every agent's only tool is read-only SQL, full stop) — simpler, more conservative, no per-tool nuance needed because there's only one tool. |
| **"Pause rather than assume" in ambiguous situations** (*Trustworthy agents in practice*) | 🟡 → **partially closed** | The forced-finalization behavior in `agent_core.py:118-121,129-133` (flag uncertainty rather than guess) was already real. The missing "Plan Mode" piece — a proposal a human approves *before* anything happens — now exists for `product_creator`, the one agent that writes directly; see "Closed this session". `schema_evolution` was always plan-only (never executes). |
| **Poka-yoke tool design** — make mistakes mechanically impossible, not just discouraged (*Building Effective Agents*) | ✅ | `agent_core.py:71-85` `safe_sql()` — rejects anything with a semicolon or not starting with `SELECT/WITH/SHOW/DESCRIBE` *before* it reaches Spark. `product_creator.py`'s `VIEW_RE` + `FORBIDDEN` regex do the same for LLM-generated SQL text before it's ever executed — allowlist shape-match + denylist verbs + catalog restriction, checked in code, not left to the model's discretion. |
| **Bounded execution / prevent compounding errors** (*Building Effective Agents* names this risk explicitly) | ✅ | `MAX_STEPS = 12` hard tool-call ceiling per agent run, with a forced no-tool finalization turn if exhausted — a runaway investigation can't spiral indefinitely. |
| **Simplicity first — don't add agentic complexity you don't need** (*Building Effective Agents*) | ✅ | Deterministic-first design: every agent's factual checks run as plain SQL/Python *before* any LLM call, and would produce a complete (if less narrated) artifact even with zero LLM involvement. The LLM is additive narration over ground-truth facts, not the source of the facts — architecturally stronger than most of Anthropic's own examples, which generally assume the LLM's claims need separate verification because the LLM *is* the source of the facts. Here, for the 10 checks in `dq_monitor_rca` for instance, the LLM never touches the pass/fail numbers at all. |
| **Transparency — show planning/reasoning, not just conclusions** (*Building Effective Agents*) | 🟡 | Full audit log exists (`agent_runs`), but it's a *post-hoc* transcript, not a live, human-facing plan shown before the agent acts. Since every action is already read-only, the risk this addresses (silently taking a wrong *action*) doesn't really apply — but the transparency of *reasoning*, specifically, is only visible if someone goes and reads the log. |
| **Evaluator-optimizer pattern** — a second LLM checks the first's output (*Building Effective Agents*) | ❌ → **✅ CLOSED** | See "Closed this session" — `agent_core.verify_report()`. |
| **Best-of-N / self-consistency check** (*Reduce hallucinations*) | ❌ still open | Each agent still runs exactly once per job trigger. `verify_report()` is a genuine second, independent pass, but it's an *evaluator* checking the first draft against evidence, not the same task run N times and diffed — a different mechanism, not a substitute. Not implemented: would add real cost/latency for a benefit largely already covered by the evaluator pass. |
| **Direct-quote extraction before analysis** (*Reduce hallucinations* — for long-document tasks) | N/A | Doesn't apply cleanly here — these agents reason over SQL query results, not long unstructured documents, so there's no analogous "long document" to quote-extract from. The inline evidence log (see "Closed this session") is the applicable equivalent. |
| **Formal eval suite measuring output accuracy over time** (*Trustworthy agents in practice*, *Building Effective Agents* — "extensive testing") | ❌ → **✅ CLOSED** | See "Closed this session" — `scripts/eval_agent_reports.py`. |
| **Prompt-injection-specific defenses** (*Trustworthy agents in practice*) | 🟡 | Not explicitly named as a threat model anywhere except `docs/DASF_ALIGNMENT.md` (DASF risks 9.1-9.9), which covers it structurally: the only untrusted input any agent sees is SQL result rows, and the only action is another read-only query or a regex-gated text proposal — so there's no path from "attacker controls a row of data" to "attacker executes a write." That's a real, effective mitigation, but it's incidental to the read-only design, not a purpose-built injection defense (no input scanning, no red-teaming done). |

## What's already done well (the honest positive case)

1. **The core hallucination guardrail is centralized, not scattered.** Because every agent shares one `run_sql` tool definition (`agent_core.py`), the "never guess, get evidence" instruction is enforced once, for all 10 agents, rather than copy-pasted per-agent where it could drift or get forgotten on the next new agent.
2. **It's proven live, today, three separate times** (`lineage_doc_agent`, `vector_content`, `operational_intel` in the same run) — each hit a data source it couldn't reach and said so explicitly instead of fabricating a plausible-sounding answer. That's the single strongest piece of evidence: not "the prompt says X," but "the prompt said X and the model actually did X under real failure conditions."
3. **The architecture goes further than most of Anthropic's own guidance assumes is necessary**: the deterministic-first design means the *facts* (row counts, pass/fail, violation counts) never pass through the LLM at all — they're computed in plain SQL/Python first, and the LLM only narrates over them. Most hallucination-mitigation advice (quote-grounding, citation-verification) exists because the model usually *is* the source of the facts; here it structurally isn't, for the highest-stakes numbers.
4. **Tool design follows the "poka-yoke" principle exactly** — `safe_sql()` and `product_creator`'s SQL-shape allowlist make bad actions mechanically impossible rather than merely prompted-against.

## What was genuinely missing when this doc was first written (now closed — see below)

1. ~~No evaluator-optimizer / second-pass verification.~~ **Closed.**
2. ~~No inline citations in the saved report.~~ **Closed.**
3. ~~No eval suite for agent output quality.~~ **Closed.**
4. ~~No "Plan Mode" equivalent for the write-adjacent agents.~~ **Closed for `product_creator`** (the only one that ever executes a write); `schema_evolution` never executed anything to begin with, so it didn't need one.
5. ~~Not documented as a named policy anywhere.~~ **Closed** — cross-referenced from `agents/README.md` and `docs/AGENT_ARCHITECTURE.html`.

## Closed this session

**1 & 2 — evaluator pass + inline citations, `agents/agent_core.py`:** `run_reasoning()` now
calls a new `verify_report(client, text, log)` after the model produces its draft — a
*second*, independent `client.messages.create()` call (no tools, terse system prompt) whose
only job is to check every claim in the draft against the `run_sql` calls actually logged, and
say so if something isn't backed by evidence. The final text `run_reasoning()` returns to every
agent now has the draft, an inline **Evidence log** (the actual queries run, extracted from the
tool-call log), and an **Independent verification** verdict, appended automatically — no changes
needed in any of the 10 individual agent files, since they all call this one shared function.
Applies to every agent uniformly, same as the original `run_sql` guardrail did.

**3 — eval scorecard, `scripts/eval_agent_reports.py`:** deterministic (no LLM — the eval
itself can't hallucinate), queries `acme_bronze.audit.agent_runs.decision_log` for the
`verification: ...` line every run now carries, and reports per-agent counts of clean /
flagged / verification-errored / no-LLM-pass runs over a 30-day window, plus an overall
"claims verified" rate. Not wired into a schedule — run on demand, same as `validate.py`.

**4 — Plan Mode for `product_creator`, `agents/product_creator.py` + `resources/agents.yml`:**
new `dry_run` job parameter (default `"false"`, so the existing one-shot demo behavior is
unchanged unless you opt in). With `dry_run=true`, the agent still does the full investigation
and generates the SQL, but stops before `spark.sql(sql)` — the proposed view is written to
`agent_reports` clearly marked `PROPOSED (dry run, awaiting review)`, and nothing is created
until a human re-runs it with `dry_run=false`. `schema_evolution` needed no change — it was
already propose-only, never executing anything.

**5 — cross-references:** `agents/README.md` and `docs/AGENT_ARCHITECTURE.html` both now link
to this file.

**Honest residual gap:** Best-of-N / self-consistency (running the same agent twice and diffing)
is still not implemented — see the table row above for why that was a deliberate skip, not an
oversight.

**Live proof the evaluator pass actually works, not just exists:** the first real run of
`dq_monitor_rca` after deploying this (`run 904966710921460`, 2026-08-14) got genuinely flagged
— the verifier correctly noticed that `safe_sql()`'s evidence log recorded which queries ran and
how many rows came back, but not the *returned values*, so several specific numbers in the
report (exact timestamps, per-source row counts) weren't strictly re-confirmable from the log
alone. That's the mechanism catching a real gap in its own supporting infrastructure, not a
false positive — fixed immediately in the same session (`safe_sql()` now logs a value snippet
per query, not just the query text), and confirmed via `scripts/eval_agent_reports.py`, which
shows the flag on record. This is the single best piece of evidence in this whole document:
not "the guardrail should work," but "the guardrail worked, on its first try, against code that
had existed for weeks."
