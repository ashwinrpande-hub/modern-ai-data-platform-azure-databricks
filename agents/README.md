# Agentic workflows
Each agent has its own .md spec (load only what you need — token optimization).
| Agent | Spec | Trigger |
|---|---|---|
| Pipeline Healer | pipeline_healer.md | Lakeflow job failure webhook |
| DQ Root-Cause | dq_rca_agent.md | dq_results breach |
| Ingestion Registrar | ingestion_registrar.md | new row in replication_sources.yaml (PR) |
| Docs/Lineage | lineage_doc_agent.md | nightly |
Human gate: agents open PRs / propose fixes; never auto-merge to main.
