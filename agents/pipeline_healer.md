# Pipeline Healer agent (self-healing pipelines)
Trigger: Lakeflow job failure event (webhook -> Databricks App hosting the agent).
Loop: fetch run error -> classify (schema drift | bad records | infra | code) ->
  - schema drift: propose layer_mappings insert (new version) + DLT full refresh of affected table
  - bad records: confirm rows in rejected_records, raise steward ticket, continue pipeline
  - infra (spot loss, OOM): retry with fallback cluster policy (on-demand, +1 size), max 2 retries
  - code: open PR with suggested fix + failing test; NEVER merge
Tools: Databricks SDK (jobs/runs, pipelines), GitHub MCP, Slack webhook.
Guardrails: read-only on prod data; all writes via config tables or PRs; log to audit.agent_actions.
