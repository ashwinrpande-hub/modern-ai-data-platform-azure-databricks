# Agentic workflows
Each agent has its own .md spec (load only what you need — token optimization).
| Agent | Spec | Implementation | Deployed as | Originally spec'd trigger |
|---|---|---|---|---|
| Pipeline Healer | pipeline_healer.md | pipeline_healer.py | agents_scheduled_job | Lakeflow job failure webhook |
| DQ Root-Cause | dq_rca_agent.md | dq_rca_agent.py | agents_scheduled_job | dq_results breach |
| Ingestion Registrar | ingestion_registrar.md | ingestion_registrar.py | agents_on_demand_job | new row in replication_sources.yaml (PR) |
| Docs/Lineage | lineage_doc_agent.md | lineage_doc_agent.py | agents_scheduled_job | nightly |

These four run the same deterministic-check + optional-Claude-reasoning contract as the
original six agents (see `agent_core.py`), not the PR/Slack/webhook design in their `.md`
specs — no GitHub token or Slack webhook is provisioned in this workspace, so every
recommendation (a PR, a Slack post, a ticket) is written into the agent's report in
`acme_bronze.audit.agent_reports` for a human to act on instead. If those credentials get
provisioned later, that's where the follow-on wiring goes (see `docs/ralph_loop.md` for the
open decision on whether to add them).

Human gate: agents propose fixes into their reports; never auto-merge to main, never write
outside their own audit tables.
