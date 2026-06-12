# Modern AI Data Warehouse — Azure Fabric + Databricks

Enterprise-grade, AI-optimized data platform unifying **SAP S/4HANA** (Europe), **JDE E1** (Americas), **QAD** (EMEA), and **Salesforce CRM** into a single medallion lakehouse, governed by **Data Mesh** principles, **DAMA DM-BOK**, and a **6-pillar DQ framework** — built on **Microsoft Fabric**, **Azure Databricks**, and **Azure PaaS**.

---

## Architecture

```
  SAP (Europe)  |  JDE (Americas)  |  QAD (EMEA)  |  Salesforce  |  IoT/Events
                                     |
              +------------------------v--------------------------+
              |   INGESTION LAYER                                 |
              |   Fabric Mirroring (SQL 2022+)                   |
              |   ADF v2 + Self-Hosted IR (legacy ERPs)          |
              |   Fabric Eventstream (Kafka / IoT Hub)           |
              +------------------------+--------------------------+
                                       |
              +------------------------v--------------------------+
              |   BRONZE  — OneLake / Delta Lake                 |  Raw, immutable append
              |   Domain-partitioned Lakehouses per domain       |  Schema-on-read
              |   Databricks Autoloader for bulk ingestion       |  Full-fidelity replay
              +------------------------+--------------------------+
                                       |  Databricks DLT (Delta Live Tables)
              +------------------------v--------------------------+
              |   SILVER  — Cleansed / Conformed                 |  6-Pillar DQ enforced
              |   DLT Expectations (quarantine bad rows)         |  SHA256 surrogate keys
              |   Fabric Dataflows Gen2 (citizen transforms)     |  SCD Type 2, FX normal.
              |   Unity Catalog schema registry                  |  DQ score per record
              +------------------------+--------------------------+
                                       |  Databricks Jobs + Fabric Pipelines
              +------------------------v--------------------------+
              |   GOLD  — Curated / Certified                    |  Star schema + OBT
              |   Fabric Warehouse (SQL analytics, BI)           |  ML Feature Store
              |   Databricks Lakehouse (ML pipelines)            |  Mosaic AI predictions
              |   dbt (complex multi-domain transforms)          |  Azure OpenAI embeddings
              +------------------------+--------------------------+
                                       |  Delta Sharing + Unity Catalog + APIM
              +------------------------v--------------------------+
              |   DATA PRODUCTS — Federated Domain Ownership     |  Output contracts + SLOs
              |   7 domains × certified data products            |  Trust scores
              |   Purview catalog (discoverable + searchable)    |  Semantic versioning
              +------+----------+----------+--------------------+
                     |          |          |
              +------v--+  +----v----+  +--v-----------+
              | Power BI|  | Azure   |  | Claude AI    |
              | Direct  |  | Static  |  | Agents (9)   |
              | Lake    |  | Web App |  | + Copilot    |
              +---------+  +---------+  +--------------+
```

---

## Platform Triad — Why Fabric + Databricks + Azure Together

| Platform | Role | Key Capabilities |
|----------|------|-----------------|
| **Microsoft Fabric** | Unified BI, warehousing, orchestration | OneLake single-store, Direct Lake Power BI, Fabric Mirroring, Eventstream, DQ Monitor, native Purview |
| **Azure Databricks** | Heavy ELT, ML engineering, advanced analytics | Delta Live Tables, Unity Catalog, MLflow + Mosaic AI, Feature Store, Photon engine, streaming + batch unification |
| **Azure PaaS** | Identity, governance, connectivity backbone | Entra ID RBAC, Microsoft Purview catalog + lineage, ADF pipelines, Azure OpenAI, APIM data product gateway, Azure Policy |

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Source ERP systems | 4 (SAP, JDE, QAD, Salesforce) |
| Data domains | 7 (Sales, Customer, Product, Finance, Supply Chain, Service, MDM) |
| Medallion layers | 3 (Bronze → Silver → Gold) + Data Products |
| DQ framework | DAMA 6-pillar (Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity) |
| DLT pipelines | 1 per domain × 3 layers = ~21 Delta Live Tables pipelines |
| ML models | Churn risk, upsell propensity, demand forecast, anomaly detection |
| AI agents | 9 autonomous Claude agents (DQ, lineage, schema evolution, deployment, etc.) |
| Data products | 10+ certified Gold products with output contracts and SLOs |
| Governance | Microsoft Purview + Databricks Unity Catalog + Entra ID |
| CI/CD | Azure DevOps + Fabric Git integration + Databricks Asset Bundles |

---

## Project Structure

```
modern-ai-data-warehouse/
│
├── ingestion/
│   ├── adf/                          # Azure Data Factory pipelines (ARM templates)
│   │   ├── pipelines/                # Parameterized ADF pipelines (SAP, JDE, QAD, SFDC)
│   │   ├── datasets/                 # Source + sink dataset definitions
│   │   ├── linked_services/          # Connection definitions (AKV-referenced)
│   │   └── triggers/                 # Schedule + event-based triggers
│   ├── fabric_mirroring/             # Mirroring config for SQL 2022+ sources
│   └── eventstream/                  # Fabric Eventstream configs (IoT Hub, Kafka)
│
├── databricks/
│   ├── dlt/                          # Delta Live Tables pipeline definitions
│   │   ├── bronze_to_silver/         # Per-domain DLT notebooks (6-pillar DQ)
│   │   └── silver_to_gold/           # Aggregation + feature pipelines
│   ├── notebooks/
│   │   ├── feature_engineering/      # PIT-correct ML feature computation
│   │   ├── ml_training/              # MLflow experiment notebooks
│   │   └── ai_refresh/               # Azure OpenAI embeddings + search index
│   ├── jobs/                         # Databricks Job YAML configs
│   ├── bundles/                      # Databricks Asset Bundle definitions
│   └── unity_catalog/                # Schema DDL + catalog setup SQL
│
├── fabric/
│   ├── warehouse/                    # Fabric Warehouse DDL (star schema, dims, facts)
│   │   ├── 00_setup/                 # Databases, schemas, roles
│   │   ├── 01_dims/                  # DIM_CUSTOMER, DIM_PRODUCT, DIM_DATE, DIM_REGION
│   │   ├── 02_facts/                 # FACT_SALES_ORDERS, FACT_SERVICE_EVENTS
│   │   └── 03_data_products/         # Data product views + output contracts
│   ├── dataflows/                    # Fabric Dataflows Gen2 (citizen transforms)
│   └── pipelines/                    # Fabric Pipeline orchestration JSON
│
├── governance/
│   ├── purview/                      # Purview scan rules, glossary, sensitivity labels
│   ├── unity_catalog/                # Unity Catalog policies, column masking, row filters
│   └── rbac/                         # Entra ID group mappings, Fabric RBAC assignments
│
├── python/
│   ├── data_generator/               # Synthetic ERP data generator (Faker)
│   ├── dq_framework/                 # Python DQ runner (mirrors DLT expectations)
│   └── feature_engineering/          # PIT-correct feature computation (local test)
│
├── agents/
│   ├── dq_rca_agent.py               # Claude AI: DQ root-cause analysis
│   ├── auto_remediation_agent.py     # Claude AI: automated DQ remediation
│   ├── schema_evolution_agent.py     # Claude AI: breaking-change detection
│   ├── lineage_explorer_agent.py     # Claude AI: column-level lineage tracing
│   ├── data_product_creator.py       # Claude AI: NL → certified data product
│   ├── data_steward_chatbot.py       # Claude AI: self-serve data steward Q&A
│   ├── cortex_content_agent.py       # Claude AI: narrative + embedding refresh
│   ├── operational_intel_agent.py    # Claude AI: ops KPI surface and alerting
│   └── deployment_agent.py           # Claude AI: CI/CD orchestration + rollback
│
├── marketplace-ui/
│   ├── frontend/                     # React 18 + Vite (dark theme, data catalog UI)
│   └── backend/                      # FastAPI + Azure Functions adapter
│
├── scripts/
│   ├── deploy.py                     # Orchestrated deployment script
│   ├── validate_deployment.py        # Post-deploy validation checks
│   └── bootstrap_unity_catalog.py    # Unity Catalog metastore + workspace setup
│
├── .github/workflows/                # GitHub Actions CI/CD
├── azure-pipelines/                  # Azure DevOps pipelines (YAML)
├── docs/
│   ├── ARCHITECTURE.md               # This document's companion reference
│   ├── DATA_LINEAGE.md               # Column-level lineage Bronze → Gold
│   ├── DATA_MESH.md                  # Domain topology + Data Product contracts
│   ├── DQ_FRAMEWORK.md               # 6-pillar DQ rules + DLT expectation catalog
│   └── agents/                       # Per-agent documentation (9 agent docs)
├── .env.template
└── requirements.txt
```

---

## Architecture Layers — Detailed

### Layer 0 — Sources

| System | Region | Integration Method | Tables |
|--------|--------|--------------------|--------|
| SAP S/4HANA | Europe | ADF SAP connector + Self-Hosted IR | VBAK, VBAP, KNA1 |
| JDE E1 | Americas | ADF SQL Server connector | F4211, F0101 |
| QAD | EMEA | ADF ODBC + Self-Hosted IR | so_mstr, cust_mstr |
| Salesforce CRM | Global | ADF Salesforce connector | Opportunity, Account |
| IoT / Events | All | Fabric Eventstream ← IoT Hub ← field devices | Sensor telemetry |

### Layer 1 — Bronze (Raw / Landing)

- **Format**: Delta Lake (ACID, time travel, schema enforcement)
- **Storage**: OneLake (ADLS Gen2) — one logical data lake, domain-partitioned
- **Ingestion**: Fabric Mirroring (SQL 2022+) or Databricks Autoloader (bulk)
- **Metadata columns** added at load time:

```python
SOURCE_SYSTEM      # 'SAP', 'JDE', 'QAD', 'SALESFORCE'
SOURCE_REGION      # 'EUROPE', 'AMERICAS', 'EMEA', 'GLOBAL'
LOAD_TIMESTAMP     # Ingestion datetime
BATCH_ID           # UUID per batch
IS_DELETED         # Soft-delete flag
RAW_JSON           # Full record as struct for forensic replay
```

### Layer 2 — Silver (Cleansed / Conformed)

- **Engine**: Databricks Delta Live Tables (DLT) — declarative ELT
- **DQ enforcement**: `@dlt.expect_or_quarantine` for all 6 DAMA pillars
- **Transformations**:
  - SHA256 surrogate keys: `SHA2(source || '|' || primary_key, 256)`
  - FX normalization: `net_amount * fx_to_usd` (LEFT JOIN currency reference)
  - SCD Type 2 via DLT `APPLY CHANGES INTO`
  - DQ score persisted as metadata column per record
- **Quarantine**: Failed records land in `_quarantine` Delta table with error codes

### Layer 3 — Gold (Curated / Certified)

| Sub-layer | Engine | Purpose |
|-----------|--------|---------|
| **BI** | Fabric Warehouse | Star schema: 4 dims + 2 facts, Power BI Direct Lake |
| **ML Features** | Databricks Feature Store | PIT-correct revenue windows, churn/upsell scores |
| **AI/Embeddings** | Databricks + Azure OpenAI | text-embedding-3-large, 1536-dim customer/product vectors |
| **Aggregations** | dbt + Fabric Warehouse | Monthly P&L, OEE, regional KPIs |

### Layer 4 — Data Products

- **Discoverable**: Microsoft Purview catalog (auto-scanned, business glossary linked)
- **Addressable**: OneLake URI + REST API via Azure APIM gateway
- **Trustworthy**: DQ SLA enforced, trust score = `DQ_score × 0.7 + freshness_met × 0.3`
- **Secure**: Unity Catalog row/column policies, Entra ID role-based access
- **Versioned**: Semantic versioning (v1.0.0), 30-day breaking-change notice

---

## Data Mesh Domains

| Domain | Domain Data Owner | Primary Sources | Key Data Products | Priority |
|--------|-------------------|-----------------|-------------------|----------|
| **Sales & Orders** | VP Sales | SAP/JDE/QAD | Sales Performance, Regional Revenue | CRITICAL |
| **Customer 360** | Chief Customer Officer | All ERPs + Salesforce | Customer Master, MDM Golden Record | CRITICAL |
| **Product & Catalog** | Product Management | SAP MM + ERP | Product Catalog, Pricing, SKU Master | HIGH |
| **Finance & Revenue** | CFO | SAP FI/CO, all ERPs | Revenue Analytics, Margin Analysis | HIGH |
| **Supply Chain** | VP Operations | SAP MM, QAD | Inventory, Supplier Performance | HIGH |
| **Service & Field Ops** | VP Service | ServiceMax, Salesforce | Service Events, SLA Compliance | MEDIUM |
| **MDM / Reference** | Chief Data Officer | SAP MDM | Customer Master, Product Master, Geo | CRITICAL |

---

## 6-Pillar Data Quality Framework

Enforced as **code**, not process — rules live in Databricks DLT expectations, Unity Catalog Delta constraints, and Fabric DQ Monitor policies.

| Pillar | DLT Expectation Pattern | Fabric DQ Monitor | KPIs |
|--------|------------------------|-------------------|------|
| **Completeness** | `@dlt.expect_or_quarantine('not_null', 'order_id IS NOT NULL')` | Null-rate alert > 0.5% | Null Rate %, Missing Record Rate |
| **Accuracy** | `@dlt.expect_or_quarantine('amount_valid', 'net_amount >= 0')` | Range validation vs. reference | Out-of-Range Count, Accuracy Rate |
| **Consistency** | `@dlt.expect_or_quarantine('region_match', "source='SAP' AND region='EUROPE'")` | Cross-domain reconciliation | Cross-System Match Rate |
| **Timeliness** | `@dlt.expect_or_quarantine('fresh', 'load_ts > dateadd(hour,-24,now())')` | Pipeline freshness watermark | Data Latency P95, SLA Breach Count |
| **Uniqueness** | `@dlt.expect_or_quarantine('unique_key', 'COUNT(*)=COUNT(DISTINCT order_hk)')` | Duplicate key detection | Duplicate Rate %, Golden Record Rate |
| **Validity** | `@dlt.expect_or_quarantine('status_valid', "status IN ('OPEN','CLOSED','PENDING')")` | Business rule violation scan | Rule Pass Rate %, Rejection Count |

**DQ Score Formula**:
```
TRUST_SCORE = (DQ_overall_score × 0.70) + (freshness_sla_met ? 100 : 50) × 0.30
```
| Band | Score |
|------|-------|
| GREEN | ≥ 98 |
| AMBER | ≥ 95 |
| RED | < 95 |

---

## AI Agents (9 — Claude + Anthropic SDK)

All agents use the **Anthropic Tool Use API** (Claude Sonnet). In live mode, tools call Databricks SQL Warehouse or Azure APIs. In mock mode, they run offline.

| Agent | File | Tools | Trigger |
|-------|------|-------|---------|
| **DQ Root-Cause Analysis** | `dq_rca_agent.py` | Query DLT quarantine, pattern analysis, Purview lineage | On DQ breach |
| **Auto-Remediation** | `auto_remediation_agent.py` | Fix null imputation, dedup, requeue rejected records | After RCA |
| **Schema Evolution** | `schema_evolution_agent.py` | Diff Unity Catalog schemas, flag breaking changes, draft migration | On PR |
| **Lineage Explorer** | `lineage_explorer_agent.py` | Walk column lineage Bronze→Gold via Unity Catalog | On-demand |
| **Data Product Creator** | `data_product_creator.py` | NL → SQL → Delta view → Purview registration → APIM publish | Self-serve |
| **Data Steward Chatbot** | `data_steward_chatbot.py` | Purview glossary Q&A, SLA status, DQ history | Chat UI |
| **Content & Embeddings** | `cortex_content_agent.py` | Generate narratives → Azure OpenAI embeddings → AI Search index | Daily |
| **Operational Intel** | `operational_intel_agent.py` | Surface pipeline KPIs, cost metrics, anomaly alerts | Every 30 min |
| **Deployment Agent** | `deployment_agent.py` | ADF validate → Databricks job deploy → smoke test → merge PR | On push |

---

## ML / AI Layer

### Feature Store (Databricks)

| Feature | Window | SQL Pattern |
|---------|--------|-------------|
| `rev_l7d_usd` | 7 days | `SUM(CASE WHEN order_date >= dateadd(-7, as_of) THEN net_amount END)` |
| `rev_l30d_usd` | 30 days | Same pattern |
| `rev_l90d_usd` | 90 days | Same pattern |
| `rev_l365d_usd` | 365 days | Same pattern |
| `order_count_l90` | 90 days | `COUNT(CASE WHEN 90d window ...)` |
| `days_since_last_order` | All time | `DATEDIFF(DAY, MAX(order_date), as_of)` |
| `churn_risk_score` | 0–1 | Recency + frequency + monetary (RFM) formula |
| `upsell_propensity` | 0–1 | Frequency + revenue + product mix score |

> **PIT Correctness**: All features use strict `WHERE order_date < as_of_date` — no future data leakage.

### MLflow Model Registry

| Stage | Description |
|-------|-------------|
| `Staging` | Registered, not yet approved |
| `Production` | Approved via governance workflow, serving live |
| `Archived` | Deprecated — consumers notified 30 days prior |

### Azure OpenAI Embeddings

- **Model**: `text-embedding-3-large` (1536-dim)
- **Customer vectors**: narrative summary → embedding → AI Search index
- **Product vectors**: product description + spec sheet → embedding
- **RAG pipeline**: Copilot Studio → APIM → Azure AI Search → GPT-4o → response

---

## Data Product Catalog

| ID | Product | Domain | Views | SLO Freshness | Trust Score |
|----|---------|--------|-------|---------------|-------------|
| DP-001 | Sales Performance | Sales | `sales_orders_v1`, `regional_summary_v1` | 15 min | 98.9% |
| DP-002 | Customer 360 | Customer | `customers_v1`, `features_v1` | 5 min | 98.7% |
| DP-003 | Revenue Analytics | Finance | `monthly_revenue_v1` | 60 min | 99.6% |
| DP-004 | Opportunity Signals | Customer | `predictions_v1` | 2 min | 98.7% |
| DP-005 | Product Catalog | Product | `product_master_v1` | 60 min | 99.2% |
| DP-006 | Supply Chain KPIs | Supply Chain | `inventory_v1`, `supplier_v1` | 30 min | 97.8% |

---

## Security & Governance

### RBAC — Entra ID + Unity Catalog

| Role | Bronze | Silver | Gold | Data Products | Purview |
|------|--------|--------|------|---------------|---------|
| `platform_admin` | R/W | R/W | R/W | R/W | Admin |
| `global_analyst` | — | R | R | R | Read |
| `finance_analyst` | — | — | R (Finance) | R (Revenue) | Read |
| `ml_engineer` | — | — | R (ML/AI) | R (Signals) | Read |
| `data_product_owner` | — | — | — | R | Contribute |
| `sap_europe_reader` | R (SAP) | R (filtered) | — | — | — |

### Data Masking — Unity Catalog Column Policies

| Policy | Applied To | Admin | ML Engineer | Others |
|--------|-----------|-------|-------------|--------|
| `mask_pii_string` | Phone, names | Full | SHA256 token | `***-MASKED-***` |
| `mask_email` | Email | Full | — | `****@domain.com` |
| `mask_financial` | Credit limit | Full | — | `-1` sentinel |

### Row-Level Security

Applied via Unity Catalog row filters:
```sql
-- Regional filter: each reader role sees only their region
CASE
  WHEN is_account_group_member('sap_europe_reader') THEN source_region = 'EUROPE'
  WHEN is_account_group_member('jde_americas_reader') THEN source_region = 'AMERICAS'
  ELSE TRUE  -- global_analyst sees all
END
```

---

## Automation Schedule (UTC)

| Time | Job | Engine | Purpose |
|------|-----|--------|---------|
| 01:00 | `dim_customer_merge` | Databricks Job | MDM merge — SAP > JDE > QAD best-source-wins |
| 01:30 | `dim_product_merge` | Databricks Job | Sync product catalog from Silver |
| 02:00 | `ml_feature_pipeline` | Databricks Job | Churn/upsell features for all customers |
| 03:00 | `ai_refresh` | Databricks Job | OpenAI embeddings + AI Search index rebuild |
| `*/15m` | `silver_dlt_trigger` | Databricks DLT | Streaming Silver refresh (continuous for Maintenance/IoT) |
| `*/6h` | `dq_framework_all` | Databricks Job | 6 DAMA checks across all Silver tables |
| `*/30m` | `sli_measurement` | Fabric Pipeline | Freshness + DQ SLI per data product |

---

## CI/CD Pipeline

### Azure DevOps + GitHub Actions

```
Push to feature branch
  │
  ├── validate (black, flake8, pytest, dbt parse)
  │
  ├── plan (Databricks Asset Bundle diff + ADF validate)
  │
  └── deploy (on merge to main)
        │
        ├── databricks bundle deploy --target prod
        ├── adf publish (ARM template → Azure)
        ├── fabric git sync (workspace ← repo)
        ├── dbt run --target prod
        ├── python scripts/validate_deployment.py
        └── deployment_agent.py  (smoke tests + Slack notify)
```

### Fabric Git Integration

Each domain Fabric Workspace is linked to its own Azure DevOps repo branch. Changes flow:
```
Developer Notebook → Fabric Workspace → Git commit → PR → Code Review → Fabric Workspace (prod)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Storage | OneLake (ADLS Gen2), Delta Lake |
| Ingestion | Fabric Mirroring, ADF v2, Fabric Eventstream, Databricks Autoloader |
| Transformation | Databricks DLT, Fabric Dataflows Gen2, dbt |
| Warehousing | Fabric Warehouse (SQL), Databricks Lakehouse |
| ML / AI | Databricks Mosaic AI, MLflow, Azure OpenAI (GPT-4o, text-embedding-3-large) |
| DQ | Databricks DLT Expectations, Fabric DQ Monitor, Great Expectations |
| Governance | Microsoft Purview, Databricks Unity Catalog, Entra ID |
| BI | Power BI Direct Lake, Fabric Real-Time Dashboards |
| AI Agents | Claude Sonnet (Anthropic), Copilot Studio |
| Frontend | React 18, Vite 5 (dark theme — data marketplace UI) |
| Backend | FastAPI + Azure Functions |
| API Gateway | Azure APIM (data product API layer) |
| CI/CD | Azure DevOps, GitHub Actions, Databricks Asset Bundles, Fabric Git |
| IaC | Terraform (Azure resources), Databricks Terraform provider |
| Secrets | Azure Key Vault (all connection strings, API keys) |
| Observability | Azure Monitor, Databricks Lakehouse Monitoring, Fabric Capacity Metrics |

---

## Deployment Guide

### Prerequisites

- Python 3.11+
- Databricks CLI v0.200+
- Azure CLI + ADF extension
- Node.js 18+ (marketplace UI)
- Azure subscription with Contributor access
- Microsoft Fabric capacity (F64 minimum for dev)
- Databricks Premium workspace (Unity Catalog required)

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/modern-ai-data-warehouse
cd modern-ai-data-warehouse
cp .env.template .env
# Edit .env: Azure tenant, Databricks host/token, ADF resource group, AKV name
```

### 2. Bootstrap Unity Catalog

```bash
python scripts/bootstrap_unity_catalog.py --env dev
# Creates: metastore, catalogs (bronze/silver/gold/products), external locations
```

### 3. Deploy Databricks Bundles

```bash
cd databricks
databricks bundle deploy --target dev     # deploy DLT pipelines + jobs
databricks bundle run dq_framework_all    # test run
```

### 4. Deploy ADF Pipelines

```bash
# Via Azure DevOps pipeline or manually:
az datafactory pipeline create \
  --resource-group rg-data-platform \
  --factory-name adf-data-platform \
  --name pl_ingest_sap_orders \
  --pipeline @adf/pipelines/pl_ingest_sap_orders.json
```

### 5. Provision Fabric Workspaces

```bash
# Run Terraform to create domain workspaces + OneLake Lakehouses
cd infra/terraform
terraform init && terraform apply -var-file=dev.tfvars
```

### 6. Load Test Data

```bash
python python/data_generator/data_generator.py --rows 5000 --load
# Loads synthetic SAP/JDE/QAD/Salesforce data to Bronze Delta tables
```

### 7. Run DQ Framework

```bash
python python/dq_framework/dq_runner.py --source ALL --env dev
# Mirrors DLT expectations; runs all 6 DAMA checks; logs to dq_batch_log
```

### 8. Validate Deployment

```bash
python scripts/validate_deployment.py --env dev
# Checks: row counts, DQ scores, Unity Catalog grants, DLT pipeline status
```

### 9. Launch Marketplace UI

```bash
cd marketplace-ui/frontend
npm install && npm run dev   # http://localhost:3000
```

---

## Cost Optimization (FinOps)

| Strategy | Saving | Detail |
|----------|--------|--------|
| Fabric Mirroring over ADF CDC | HIGH | Zero DFU cost, sub-minute latency for SQL 2022+ sources — saves ~$120K/yr for 100+ sources |
| Delta OPTIMIZE + ZORDER | HIGH | Reduces Fabric CU consumption 60–80% on hot query paths (order by `customer_hk, order_date`) |
| Power BI Direct Lake mode | HIGH | Eliminates import copies + scheduled refresh CU cost |
| Databricks Spot clusters (batch DLT) | MEDIUM | ~70% cost reduction vs. on-demand for triggered ELT jobs |
| Fabric capacity pause (dev/test) | MEDIUM | Pause F8 dev capacity 18h/day = 75% dev cost saving |
| Unity Catalog read-in-place | MEDIUM | Eliminates cross-domain data copies — one Delta table, many consumers |
| Tiered OneLake storage | MEDIUM | Bronze > 90 days → Cool tier (50% storage reduction), > 3yr → Archive |
| Serverless Databricks SQL | MEDIUM | Per-second billing for ad-hoc queries vs. minimum 10-min classic cluster |

**Indicative Year-1 TCO (mid-scale, 5 domains):**

| Component | Annual Cost |
|-----------|------------|
| Fabric F128 (production) | $145K – $190K |
| Fabric F8 (dev/test, paused) | $8K – $12K |
| Databricks Premium (DBUs) | $120K – $200K |
| ADF (self-hosted IR + runs) | $15K – $30K |
| Azure OpenAI (token usage) | $20K – $50K |
| Azure Purview (scan units) | $10K – $25K |
| Azure PaaS (AKV, APIM, Monitor) | $15K – $30K |
| **TOTAL** | **$333K – $537K/yr** |

> Apply the 8 FinOps strategies above to reduce TCO by 35–50%.

---

## Phased Roadmap

| Phase | Months | Theme | Key Deliverables |
|-------|--------|-------|-----------------|
| **Phase 0 — Foundation** | 1–3 | Land, Discover, Govern | Fabric workspaces live, Purview catalog with all sources, 3 Bronze domains streaming, Unity Catalog + RBAC |
| **Phase 1 — Core Mesh** | 4–9 | Build, Publish, Consume | 6 certified Gold data products, DLT Silver for all domains, ML Feature Store, Power BI Direct Lake |
| **Phase 2 — Scale & AI** | 10–18 | Scale, Optimize, AI-First | 10+ data products, 3 AI models in production, self-serve data product publishing, full Purview lineage |
| **Phase 3 — Intelligent** | 19–30 | Intelligence, Innovation | GenAI knowledge base, Digital Twin integration, domain chargeback, 30+ certified data products |

---

## DAMA Governance Alignment

| DAMA Knowledge Area | Tool | Priority |
|--------------------|------|----------|
| Data Governance | Microsoft Purview + Fabric Admin Portal | CRITICAL |
| Data Architecture | Medallion Lakehouse + Data Mesh domains | CRITICAL |
| Data Modeling | dbt + Fabric Warehouse + Unity Catalog | HIGH |
| Data Security | Entra ID + Unity Catalog + Purview DLP | CRITICAL |
| Data Integration | Fabric Mirroring + ADF + Eventstream | HIGH |
| Reference & Master Data | MDM domain (Fabric Warehouse) + SAP sync | CRITICAL |
| Data Warehousing & BI | Fabric Warehouse + Power BI Direct Lake | HIGH |
| Metadata Management | Purview + Databricks Unity Catalog | HIGH |
| Data Quality | Fabric DQ Monitor + Databricks DLT Expectations | CRITICAL |
| Document & Content | Azure AI Search + SharePoint + RAG | MEDIUM |

---

## Architecture Decision Records (ADRs)

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | OneLake as single logical storage | Eliminates storage fragmentation; Fabric + Databricks reference same ADLS Gen2 endpoint |
| ADR-002 | Delta Lake as universal table format | ACID transactions, schema enforcement, time travel, CDC compatibility across all engines |
| ADR-003 | Domain workspace isolation | Prevents CU contention; enables per-domain cost charging and access boundary enforcement |
| ADR-004 | Unity Catalog as enterprise metadata layer | Single governance point for table ACLs, column masking, audit logs across Databricks + Fabric |
| ADR-005 | Fabric Mirroring preferred over ADF CDC | Zero DFU cost, sub-minute latency, zero-code for SQL 2022+ — highest priority for eligible sources |
| ADR-006 | Claude agents over Azure-native-only automation | Anthropic Claude provides multi-step reasoning for complex DQ RCA and schema evolution decisions |
| ADR-007 | Power BI Direct Lake over Import mode | Zero data duplication, no scheduled refresh, sub-second queries on Delta files |
| ADR-008 | dbt for complex cross-domain transforms | SQL-first, version-controlled, testable transforms; works with both Databricks and Fabric Warehouse |

---

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Platform reference: databases, RBAC, security, scheduling
- [DATA_LINEAGE.md](docs/DATA_LINEAGE.md) — Column-level transformation lineage Bronze → Gold
- [DATA_MESH.md](docs/DATA_MESH.md) — Domain topology, data product contracts, SLOs
- [DQ_FRAMEWORK.md](docs/DQ_FRAMEWORK.md) — 6-pillar DQ rules, DLT expectation catalog, KPIs
- [docs/agents/](docs/agents/) — Per-agent documentation for all 9 Claude AI agents
- [steel-data-architecture.jsx](steel-data-architecture.jsx) — Interactive reference architecture (React component)

---

## Author

**Ashwin Pande** — Principal Data Architect

Built as a portfolio project demonstrating enterprise data platform engineering with Microsoft Fabric, Azure Databricks, multi-ERP integration, ML/AI, Data Mesh principles, and DAMA governance — designed as the Azure-native evolution of a Snowflake-based platform.

> **Companion project**: [modern-ai-data-platform](https://github.com/ashwinrpande-hub/modern-ai-data-platform) — same architecture on Snowflake (Dynamic Tables, Cortex AI, Snowpark)
