# Code & data-flow graph
```mermaid
flowchart LR
  subgraph Sources
    SAP[SAP / Oracle EBS]; SQL[SQL Server / QAD]; SFDC[Salesforce]; OT[PLCs via Litmus Edge]
  end
  SAP -->|GoldenGate avro_op| L[ADLS landing]
  SFDC -->|API export| L
  OT -->|UNS topics| EH[Event Hubs Kafka]
  OT -->|parquet| L
  SQL -->|Lakeflow Connect CDC| B
  L -->|Auto Loader| T1[ingestion/templates/bronze_ingest_template.py]
  EH --> T2[ingestion/litmus_ot/litmus_eventhub_dlt.py]
  T1 --> B[(acme_bronze)]
  T2 --> B
  CFG[[config/replication_sources.yaml]] -.drives.-> T1 & T2 & DEP[scripts/deploy.py]
  B --> S1[pipelines/silver_dlt.py] --> S[(acme_silver 3NF insert-only, hk=sha256)]
  S --> G1[pipelines/gold_dlt.py] --> G[(acme_gold star + agg)]
  G1 --> PIT[pit_customer DV2.0 point-in-time] & BR[bridge_order_fulfillment DV2.0 bridge]
  PIT --> FS
  BR --> BI[AI/BI + Genie one-join lifecycle]
  G --> FS[ml/feature_store.py] & VS[ai/vector_search_rag.py] & P[data_products/publish_marketplace.sql]
  P --> MKT[Databricks Marketplace] & UI[marketplace-ui/]
  DQ[dq/dama_dq_framework.py] -.gates.-> S & G
  DQ -->|breach| RCA[agents/dq_rca_agent.md]
  JOBFAIL[Lakeflow failure] --> HEAL[agents/pipeline_healer.md]
  VAL[scripts/validate.py] -.CI gate.-> ALL[(all layers)]
  DAB[[databricks.yml + resources/pipelines.yml]] -.deploys.-> S1 & G1
  Q[sql/*.sql] -.traces.-> B & S & G
```

Files referenced above that don't exist yet in this repo (`ingestion/templates/bronze_ingest_template.py`,
`ingestion/litmus_ot/litmus_eventhub_dlt.py`, `scripts/deploy.py`, `ml/feature_store.py`,
`ai/vector_search_rag.py`, `data_products/publish_marketplace.sql`, `marketplace-ui/`) describe the
target design, not the current state — tracked as open gaps, same as `docs/SESSION_NOTES.md`'s
2026-07-05 gap analysis. What's real and running today: `pipelines/silver_dlt.py` and
`pipelines/gold_dlt.py`, deployed via `databricks.yml`/`resources/pipelines.yml`, reading from
Bronze tables seeded directly from `scripts/generate_synthetic_data.py` output (no ingestion pipeline
yet — see `docs/ARCHITECTURE.md`'s Deployment section) and `config/seed_layer_mappings.sql`-seeded
config tables; `sql/*.sql` traces a row through all three layers end to end against that real data;
and `agents/*.py` — six platform agents (DQ monitor+RCA, schema evolution, product creator,
vector/content, deployment gate, operational intel) deployed as two serverless jobs via
`resources/agents.yml`, sharing `agents/agent_core.py` (read-only-SQL tool guard, decision logging to
`audit.agent_runs`, reports to `audit.agent_reports`). Agents run deterministic checks always and add
Claude reasoning (claude-opus-4-8) when the Databricks secret `agents/anthropic_api_key` (or env
`ANTHROPIC_API_KEY`) is present; without it they run in deterministic mode. The DQ agent populates
`audit.dq_results` (closing validate.py check 10); the product creator ships
`acme_products.sales.v_sales_orders_unified`; the content agent builds
`acme_gold.sales.customer_narratives`.

