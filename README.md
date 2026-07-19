# acme Modern AI Data Platform — Azure Databricks

Production-ready Lakehouse for the **Sales domain** of a steel manufacturer (acme), unifying
**SAP S/4HANA (Europe)**, **JDE E1 (Americas)**, **QAD (EMEA)**, **Salesforce CRM**,
**SQL Server operational DBs**, and **Litmus Edge OT/plant-floor data** on
**Azure Databricks + Delta Lake + Unity Catalog**.

## What this repo demonstrates
| Capability | Where |
|---|---|
| Templatized replication to Bronze (GoldenGate, SQL Server CDC, Litmus OT) | `ingestion/`, `docs/REPLICATION_PATTERNS.md` |
| Medallion (Bronze/Silver 3NF, Gold star) with Lakeflow Declarative Pipelines (DLT) | `pipelines/` |
| Insert-only Silver with SHA-256 hash keys | `pipelines/silver_dlt.py` |
| Config-driven source→target mappings + lineage | `config/` |
| DAMA 6-dimension DQ + quarantine + rejected-record logging | `dq/` |
| Unity Catalog RBAC, region row filters (SAP=Europe, JDE=Americas, QAD=EMEA), PII masks | `security/` |
| ML Feature Store (point-in-time correct) | `ml/` |
| Vector Search + RAG (AI-ready Gold) | `ai/` |
| Data Products, contracts, SLOs, Databricks Marketplace publishing | `data_products/` |
| Custom Marketplace UI (independent code) | `marketplace-ui/` |
| Agentic workflows (self-healing pipelines, DQ RCA) | `agents/` |
| CI/CD (Azure DevOps) | `.azuredevops/azure-pipelines.yml` |
| Interactive 60-min presentation | `presentation/index.html` |

## Quick start
```bash
pip install -r requirements.txt
python scripts/generate_synthetic_data.py          # synthetic SAP/JDE/QAD/SFDC/OT data
python scripts/deploy.py --env dev                 # creates catalogs, schemas, config tables, pipelines
python scripts/validate.py --env dev               # post-deploy validation (12 checks)
```

## Layered catalogs (Unity Catalog)
```
acme_bronze   raw, schema-on-write, CDC feeds, OT streams   (3NF mirror of source)
acme_silver   3NF, insert-only, SHA-256 hash keys, DQ-gated
acme_gold     star schema (hash-key joins), feature store, vectors
acme_products governed data products, Delta Sharing / Marketplace
```

Read `docs/ARCHITECTURE.md` first; every design decision and its two rejected
alternatives are in `docs/JUSTIFICATION_NOTES.md`.

