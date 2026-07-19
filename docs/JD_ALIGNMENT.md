# JD Alignment — Senior Data Engineer (Agentic Lakehouse)

Maps each requirement to (a) proof in this repo, (b) real project history. Use for resume
tailoring and interview talking points. Source-of-truth for both: this file only — do not
duplicate into ARCHITECTURE.md or REPLICATION_PATTERNS.md.

| JD requirement | Repo evidence | Real-world evidence |
|---|---|---|
| 6+ yrs modern data platforms/pipelines | Full Bronze→Silver→Gold→Products lakehouse, config-driven | 19+ yrs; BNY (Customer MDM/governance), JPMC, UBS, Bank of America, Westfield, Autoliv, Bayer |
| AI/ML-driven workflows | `agents/` (dq_rca_agent, pipeline_healer, lineage_doc_agent, ingestion_registrar); `ml/feature_store.py`; `ai/vector_search_rag.py` | New — this repo is the primary proof point; position as hands-on agentic build, not just theory |
| Strong SQL & Python | `config/config_tables.sql`, `dq/dama_dq_framework.py`, `pipelines/*_dlt.py`, `scripts/*.py` | Snowflake/T-SQL/PySpark across all prior engagements |
| Databricks, Delta Lake, Spark hands-on | Entire repo: DLT pipelines, Delta tables, Liquid Clustering, Unity Catalog | Azure Databricks at Westfield Insurance (P&C) and Autoliv (manufacturing) |
| ETL/ELT in Azure | ADLS Gen2 landing, Lakeflow Connect, Azure DevOps CI/CD | Azure Databricks/ADF pipelines at Westfield, Autoliv |
| Workflow orchestration tools | Lakeflow Jobs orchestration; `.azuredevops/azure-pipelines.yml` | ADF/Databricks Workflows at prior engagements |
| Agentic automation concepts | `agents/*.md` specs: self-healing pipelines, DQ root-cause-analysis agent, lineage-doc agent, ingestion registrar agent — all config-driven, no hardcoded logic | Differentiator — most candidates will only have orchestration, not self-healing/agentic design |
| DW/DL/Lakehouse design | Medallion (3NF Bronze/Silver, star Gold), hash-key joins, config-table lineage | Data Vault 2.0 on Snowflake at Autoliv; Snowflake medallion at Vertiv-style platform build |
| CI/CD (Azure DevOps preferred) | `.azuredevops/azure-pipelines.yml`, `scripts/validate.py` as CI gate | Azure DevOps pipelines in prior Azure engagements |
| Agile | — | Standard across all consulting engagements (BNY, Westfield, Autoliv) |
| MDM / Reference Data collaboration | `security/unity_catalog_policies.sql` (region-based RBAC), hash-key dimension model as reference-data backbone | Direct: Customer MDM + data governance frameworks at BNY |
| Observability/monitoring/alerting | `dq/` quarantine + rejected-record logging; batch_log/dq_results tables; SQL freshness alerts | Standard governance practice from BNY/Westfield engagements |

## How to use this in interview prep
- Lead with BNY MDM + governance as the "why data quality/lineage/config-driven design matters to me" story.
- Use this repo as the concrete Databricks-native answer to "have you worked with agentic pipelines?" — walk through `agents/pipeline_healer.md` and `agents/dq_rca_agent.md` specifically, since that's the requirement most candidates will fake or hand-wave.
- Bridge Data Vault 2.0 (Autoliv/Snowflake) → hash-key Silver design here: same deterministic-key idea, applied without full hub/link/sat overhead (see `JUSTIFICATION_NOTES.md` #4–5 for the reasoning to repeat verbatim in an interview).
- If asked about production Databricks depth specifically (vs. Snowflake): be upfront that Westfield/Autoliv is your hands-on Databricks base, and this repo demonstrates the newer Databricks 2025/2026 surface (Lakeflow Connect, Agent Bricks, Genie, Lakebase) applied to that same real-world pattern set.

## Gaps to name honestly (don't oversell)
- No production Databricks Marketplace publish in real engagements — `data_products/publish_marketplace.sql` here is a design/demo, say so if asked directly.
- Agentic pipeline healing is a **build**, not yet **production-run-at-scale** — frame as "designed and implemented in a representative environment," not "running in prod for N years."
