import { useState } from "react";

const STEEL = {
  bg: "#0a0c10",
  surface: "#111318",
  card: "#161b22",
  border: "#21262d",
  accent: "#e8912d",
  accentDim: "#9a5e1a",
  blue: "#3b8fd4",
  blueDim: "#1e4a7a",
  green: "#2ea043",
  teal: "#1f8b8b",
  text: "#e6edf3",
  muted: "#8b949e",
  subtle: "#484f58",
};

const styles = {
  root: {
    fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
    background: STEEL.bg,
    color: STEEL.text,
    minHeight: "100vh",
    fontSize: "13px",
    lineHeight: "1.7",
  },
  header: {
    background: `linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1c2128 100%)`,
    borderBottom: `2px solid ${STEEL.accent}`,
    padding: "32px 40px 24px",
    position: "relative",
    overflow: "hidden",
  },
  headerStripe: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: "3px",
    background: `repeating-linear-gradient(90deg, ${STEEL.accent} 0px, ${STEEL.accent} 40px, transparent 40px, transparent 60px)`,
  },
  headerEyebrow: {
    color: STEEL.accent,
    fontSize: "10px",
    letterSpacing: "3px",
    textTransform: "uppercase",
    marginBottom: "8px",
    fontWeight: 600,
  },
  headerTitle: {
    fontSize: "22px",
    fontWeight: 700,
    color: STEEL.text,
    letterSpacing: "-0.3px",
    marginBottom: "6px",
  },
  headerSub: {
    color: STEEL.muted,
    fontSize: "12px",
    letterSpacing: "0.5px",
  },
  pillRow: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    marginTop: "16px",
  },
  pill: {
    background: "#1c2128",
    border: `1px solid ${STEEL.border}`,
    borderRadius: "4px",
    padding: "3px 10px",
    fontSize: "10px",
    color: STEEL.muted,
    letterSpacing: "1px",
    textTransform: "uppercase",
  },
  nav: {
    display: "flex",
    background: STEEL.surface,
    borderBottom: `1px solid ${STEEL.border}`,
    padding: "0 24px",
    overflowX: "auto",
    gap: "0",
  },
  navTab: (active) => ({
    padding: "14px 18px",
    fontSize: "11px",
    letterSpacing: "1px",
    textTransform: "uppercase",
    cursor: "pointer",
    color: active ? STEEL.accent : STEEL.muted,
    borderBottom: active ? `2px solid ${STEEL.accent}` : "2px solid transparent",
    background: "none",
    border: "none",
    borderBottom: active ? `2px solid ${STEEL.accent}` : "2px solid transparent",
    whiteSpace: "nowrap",
    fontFamily: "inherit",
    fontWeight: active ? 700 : 400,
    transition: "color 0.2s",
  }),
  body: {
    padding: "32px 40px",
    maxWidth: "1100px",
    margin: "0 auto",
  },
  sectionLabel: {
    color: STEEL.accent,
    fontSize: "10px",
    letterSpacing: "3px",
    textTransform: "uppercase",
    marginBottom: "6px",
    fontWeight: 700,
  },
  sectionTitle: {
    fontSize: "18px",
    fontWeight: 700,
    color: STEEL.text,
    marginBottom: "6px",
  },
  sectionDesc: {
    color: STEEL.muted,
    fontSize: "12px",
    marginBottom: "28px",
    maxWidth: "700px",
    lineHeight: "1.8",
  },
  grid2: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "16px",
    marginBottom: "20px",
  },
  grid3: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: "16px",
    marginBottom: "20px",
  },
  card: {
    background: STEEL.card,
    border: `1px solid ${STEEL.border}`,
    borderRadius: "6px",
    padding: "20px",
  },
  cardAccent: (color) => ({
    background: STEEL.card,
    border: `1px solid ${STEEL.border}`,
    borderLeft: `3px solid ${color || STEEL.accent}`,
    borderRadius: "6px",
    padding: "20px",
  }),
  cardTitle: {
    fontSize: "12px",
    fontWeight: 700,
    color: STEEL.text,
    marginBottom: "10px",
    textTransform: "uppercase",
    letterSpacing: "1px",
  },
  cardNum: {
    color: STEEL.accent,
    fontSize: "24px",
    fontWeight: 700,
    marginBottom: "4px",
  },
  cardNumLabel: {
    color: STEEL.muted,
    fontSize: "10px",
    textTransform: "uppercase",
    letterSpacing: "1px",
  },
  qBlock: {
    background: STEEL.card,
    border: `1px solid ${STEEL.border}`,
    borderRadius: "6px",
    marginBottom: "12px",
    overflow: "hidden",
  },
  qHeader: {
    display: "flex",
    alignItems: "flex-start",
    gap: "14px",
    padding: "16px 20px",
  },
  qNum: {
    background: STEEL.accent,
    color: "#000",
    fontSize: "10px",
    fontWeight: 700,
    width: "22px",
    height: "22px",
    borderRadius: "3px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    marginTop: "1px",
  },
  qText: {
    color: STEEL.text,
    fontSize: "13px",
    fontWeight: 600,
    flex: 1,
  },
  qWhy: {
    color: STEEL.muted,
    fontSize: "11px",
    marginTop: "4px",
    fontStyle: "italic",
  },
  qOptions: {
    padding: "0 20px 16px 56px",
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
  },
  qOpt: (color) => ({
    background: "#1c2128",
    border: `1px solid ${color || STEEL.subtle}`,
    borderRadius: "3px",
    padding: "3px 10px",
    fontSize: "11px",
    color: STEEL.muted,
  }),
  divider: {
    borderTop: `1px solid ${STEEL.border}`,
    margin: "28px 0",
  },
  tag: (color) => ({
    display: "inline-block",
    background: `${color}22`,
    border: `1px solid ${color}55`,
    color: color,
    borderRadius: "3px",
    padding: "2px 8px",
    fontSize: "10px",
    fontWeight: 700,
    letterSpacing: "1px",
    textTransform: "uppercase",
    marginRight: "6px",
    marginBottom: "4px",
  }),
  layerBox: (color) => ({
    border: `1px solid ${color}44`,
    borderLeft: `3px solid ${color}`,
    background: `${color}08`,
    borderRadius: "6px",
    padding: "16px 20px",
    marginBottom: "12px",
  }),
  layerTitle: (color) => ({
    color: color,
    fontSize: "11px",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "2px",
    marginBottom: "8px",
  }),
  badge: (color) => ({
    background: `${color}22`,
    color: color,
    border: `1px solid ${color}44`,
    borderRadius: "3px",
    padding: "2px 8px",
    fontSize: "10px",
    fontWeight: 600,
    display: "inline-block",
    margin: "2px 3px",
  }),
  timeline: {
    position: "relative",
    paddingLeft: "32px",
  },
  timelineItem: {
    position: "relative",
    marginBottom: "24px",
  },
  timelineDot: (color) => ({
    position: "absolute",
    left: "-37px",
    top: "4px",
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    background: color,
    border: `2px solid ${STEEL.bg}`,
    boxShadow: `0 0 0 1px ${color}`,
  }),
  timelineLine: {
    position: "absolute",
    left: "-32px",
    top: "0",
    bottom: "-24px",
    width: "2px",
    background: STEEL.border,
  },
  phaseLabel: (color) => ({
    color: color,
    fontSize: "10px",
    fontWeight: 700,
    letterSpacing: "2px",
    textTransform: "uppercase",
    marginBottom: "4px",
  }),
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "12px",
    marginBottom: "16px",
  },
  th: {
    background: "#1c2128",
    color: STEEL.accent,
    padding: "10px 14px",
    textAlign: "left",
    fontSize: "10px",
    letterSpacing: "1.5px",
    textTransform: "uppercase",
    fontWeight: 700,
    borderBottom: `1px solid ${STEEL.border}`,
  },
  td: {
    padding: "10px 14px",
    borderBottom: `1px solid ${STEEL.border}`,
    color: STEEL.text,
    verticalAlign: "top",
  },
  trAlt: {
    background: "#13181f",
  },
  infoBox: (color) => ({
    background: `${color}11`,
    border: `1px solid ${color}33`,
    borderRadius: "6px",
    padding: "14px 18px",
    marginBottom: "14px",
  }),
  infoTitle: (color) => ({
    color: color,
    fontSize: "11px",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "1.5px",
    marginBottom: "6px",
  }),
  ul: {
    margin: "8px 0",
    paddingLeft: "16px",
    color: STEEL.muted,
    fontSize: "12px",
    lineHeight: "1.9",
  },
  li: { marginBottom: "3px" },
  strong: { color: STEEL.text, fontWeight: 700 },
};

// ── Data ────────────────────────────────────────────────────────────────────

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "questionnaire", label: "Discovery Q&A" },
  { id: "architecture", label: "Reference Architecture" },
  { id: "datamesh", label: "Data Mesh Design" },
  { id: "quality", label: "6-Pillar DQ" },
  { id: "platforms", label: "Platform Blueprint" },
  { id: "governance", label: "DAMA Governance" },
  { id: "roadmap", label: "Phased Roadmap" },
  { id: "cost", label: "Cost Strategy" },
];

const QUESTIONNAIRE = [
  {
    category: "Business & Strategic Context",
    color: STEEL.accent,
    questions: [
      {
        q: "What are the top 3 strategic business objectives driving this initiative (e.g., predictive maintenance, yield optimization, scrap reduction)?",
        why: "Anchors every architecture decision to measurable business value",
        opts: ["Predictive Maintenance", "Yield Optimization", "Scrap Reduction", "Energy Efficiency", "Supply Chain Visibility", "ESG/Carbon Reporting"],
      },
      {
        q: "Who are the primary consumers of data products — plant floor operators, C-suite, external regulators, or AI/ML models?",
        why: "Drives latency, access patterns, UX, and data contract design",
        opts: ["Plant Operators", "Data Scientists", "Finance/Executive", "Regulators", "ERP Systems", "ML Pipelines"],
      },
      {
        q: "Which business domains are most data-mature today and which are greenfield?",
        why: "Identifies anchor domains for initial Data Mesh adoption vs domains needing uplift",
        opts: ["Production/MES", "Quality/Metallurgy", "Maintenance", "Supply Chain", "Energy", "Finance/ERP"],
      },
      {
        q: "What is the approved capital/OpEx envelope for Year 1 and 3-year TCO target?",
        why: "Hard constraint that shapes platform licensing, Databricks SKU, and Fabric capacity sizing",
        opts: ["< $500K/yr", "$500K–$2M/yr", "$2M–$5M/yr", "> $5M/yr"],
      },
    ],
  },
  {
    category: "Current State — SQL Server Landscape",
    color: STEEL.blue,
    questions: [
      {
        q: "How many SQL Server instances exist and what versions are in use (2012–2022)? Are any on-premises vs. SQL Managed Instance?",
        why: "Determines migration complexity, CDC feasibility, and Fabric Mirroring eligibility",
        opts: ["< 50 instances", "50–150 instances", "> 150 instances", "Mix of versions", "Some SQL MI already", "All on-premises"],
      },
      {
        q: "What is the total data volume across all SQL Server databases, and what is daily change/insert rate per domain?",
        why: "Drives Delta Lake partition strategy, Fabric capacity F-SKU selection, and egress costs",
        opts: ["< 10 TB total", "10–100 TB", "100–500 TB", "> 500 TB", "High-churn transactional", "Mostly static master data"],
      },
      {
        q: "Are SQL Server transaction logs available for CDC? Are there existing ETL pipelines (SSIS, ADF, custom)?",
        why: "CDC availability unlocks real-time ingestion vs. batch-only; avoids rebuilding existing working pipelines",
        opts: ["CDC enabled on key DBs", "No CDC today", "SSIS pipelines exist", "ADF pipelines exist", "Custom ETL", "No structured ETL"],
      },
      {
        q: "Which SQL Server databases contain PII, health, financial, or IP-sensitive data requiring masking or encryption?",
        why: "Mandatory for Microsoft Purview sensitivity labeling and row-level security design",
        opts: ["HR/Payroll DBs", "Customer data", "Financial DBs", "IP/Recipes", "Regulatory data", "Not classified yet"],
      },
      {
        q: "Are there existing data contracts or SLAs between source teams and downstream consumers?",
        why: "Reveals governance debt; critical for Data Mesh domain contract enforcement",
        opts: ["Formal SLAs exist", "Informal agreements", "No contracts at all", "Partial per domain"],
      },
    ],
  },
  {
    category: "Data Mesh & Domain Ownership",
    color: STEEL.teal,
    questions: [
      {
        q: "Can organizational units align to data domains with a named Domain Data Owner (DDO) per domain?",
        why: "Federated ownership is the foundational prerequisite of Data Mesh — without it, Mesh degenerates into a lake",
        opts: ["Yes, org chart aligns", "Partial alignment", "No — central IT owns all", "Need restructuring"],
      },
      {
        q: "Which domains can realistically self-serve for data product publishing vs. which need central platform team scaffolding?",
        why: "Defines the split between domain-autonomous teams vs. 'Data Product as a Service' delivery model",
        opts: ["MES/Production", "Quality Lab", "Maintenance", "Supply Chain", "Energy", "Finance"],
      },
      {
        q: "Is there appetite for domain teams to own Delta Lake schemas and Fabric Lakehouses within their domain workspace?",
        why: "Determines workspace topology — per-domain workspaces vs. shared with RBAC isolation",
        opts: ["Full domain ownership", "Shared with RBAC", "Central team preference", "Evaluate per domain"],
      },
      {
        q: "How should cross-domain data products be governed — federated catalog, central broker, or event-mesh with contracts?",
        why: "Shapes the interoperability layer: Fabric Data Catalog + Databricks Unity Catalog integration",
        opts: ["Federated catalog", "Central broker", "Event-based contracts", "Undecided"],
      },
    ],
  },
  {
    category: "AI / ML Objectives",
    color: "#9a6dd7",
    questions: [
      {
        q: "Which AI use-cases are in the 12-month roadmap — predictive maintenance, scrap prediction, energy optimization, computer vision on defects?",
        why: "Determines feature store requirements, real-time inference latency, and Databricks MLflow scope",
        opts: ["Predictive Maintenance", "Scrap/Yield Prediction", "Energy Optimization", "Visual Defect Detection", "Demand Forecasting", "LLM-based QA Assist"],
      },
      {
        q: "Is the ML platform preference Databricks MLflow/Mosaic AI, Azure ML, Microsoft Fabric Notebooks, or Copilot Studio?",
        why: "Prevents vendor lock-in duplication; consolidates experiment tracking and model registry",
        opts: ["Databricks Mosaic AI", "Azure ML", "Fabric Notebooks", "Copilot Studio", "Open to recommendation"],
      },
      {
        q: "What is the required inference latency for AI models — real-time (< 100ms), near-real-time (< 5s), or batch overnight?",
        why: "Real-time requires event streaming (Fabric Eventstream + Kafka); batch is cost-much cheaper",
        opts: ["Real-time < 100ms", "Near-real-time < 5s", "Batch hourly", "Batch daily", "Mix per use-case"],
      },
      {
        q: "Do AI models need to operate on sensor/IoT time-series data from plant floors?",
        why: "IoT streaming requires different ingestion path: Azure IoT Hub → Fabric Eventstream vs. SQL Server polling",
        opts: ["Yes, OT/IoT data critical", "Partial IoT integration", "No IoT today", "Future consideration"],
      },
    ],
  },
  {
    category: "Platform & Technology",
    color: STEEL.green,
    questions: [
      {
        q: "What Microsoft Fabric capacity tier is planned or under evaluation (F2–F2048)?",
        why: "F-SKU drives throughput ceilings for Dataflows, Pipelines, and Warehouse — under-sizing causes cost spikes",
        opts: ["F2–F8 (dev/test)", "F16–F64 (pilot)", "F128–F256 (mid)", "F512+ (enterprise)", "Not yet decided"],
      },
      {
        q: "Is Databricks already licensed or greenfield? What DBU tier — Standard, Premium, or Enterprise (Unity Catalog requirement)?",
        why: "Unity Catalog requires Premium/Enterprise; without it, cross-workspace governance breaks",
        opts: ["Databricks greenfield", "Existing Standard", "Existing Premium", "Existing Enterprise", "Evaluating"],
      },
      {
        q: "Is Azure Purview / Microsoft Purview already deployed for data catalog and lineage?",
        why: "Purview is the metadata backbone — retrofitting it is 3× harder than starting with it",
        opts: ["Fully deployed", "Partial deployment", "Not deployed", "Evaluating"],
      },
      {
        q: "What is the network topology — single Azure region, multi-region, hybrid on-prem/cloud, or sovereign cloud requirements?",
        why: "Multi-region adds latency and replication costs; sovereignty may restrict Fabric tenant placement",
        opts: ["Single region", "Multi-region", "Hybrid on-prem", "Sovereign/air-gap", "Not defined"],
      },
      {
        q: "Is Fabric Mirroring viable for source SQL Servers (Mirroring requires SQL Server 2022+ or SQL MI)?",
        why: "Fabric Mirroring is the lowest-cost, near-zero-latency ingestion path — highest priority for eligible DBs",
        opts: ["SQL Server 2022 ready", "SQL MI available", "Older SQL versions", "Mixed estate", "Unsure"],
      },
    ],
  },
  {
    category: "Data Quality & DAMA Alignment",
    color: "#d4a017",
    questions: [
      {
        q: "Are there currently documented data quality rules or business glossaries, even informally in spreadsheets or tribal knowledge?",
        why: "Existing rules accelerate DQ rule migration into Fabric DQ Monitor and Databricks expectations",
        opts: ["Formal DQ rules exist", "Informal/spreadsheets", "In business heads only", "Nothing documented"],
      },
      {
        q: "Which of the 6 pillars of data quality is most broken today — Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity?",
        why: "Enables targeted remediation sprints rather than boiling-the-ocean DQ programs",
        opts: ["Completeness", "Accuracy", "Consistency", "Timeliness", "Uniqueness", "Validity"],
      },
      {
        q: "Is there a Master Data Management (MDM) system for material grades, plant codes, supplier codes, or equipment IDs?",
        why: "Steel manufacturing without material grade MDM produces fatally inconsistent quality metrics across plants",
        opts: ["SAP MDM active", "Custom MDM", "No MDM — critical gap", "Spreadsheet-based"],
      },
      {
        q: "What are the regulatory/compliance frameworks — ISO 9001, ISO 50001, REACH, CBAM (Carbon Border), OSHA?",
        why: "Each regulation demands specific data retention, lineage, and audit trail requirements on Fabric/Purview",
        opts: ["ISO 9001", "ISO 50001", "REACH/CBAM", "OSHA", "SEC/Financial", "Customer spec compliance"],
      },
    ],
  },
  {
    category: "Team, Skills & Operating Model",
    color: "#58a6ff",
    questions: [
      {
        q: "What is the current headcount split — central data engineering, domain/embedded engineers, and data scientists?",
        why: "Data Mesh requires embedded domain engineers; a 100% central team cannot scale across hundreds of domains",
        opts: ["Central heavy", "Domain embedded", "Mixed model", "Mostly outsourced", "Team to be hired"],
      },
      {
        q: "Is there Databricks/Spark expertise in-house, or is PySpark skill-building part of this program?",
        why: "Skill gaps on Spark directly add 3–6 months to delivery; training must be in the roadmap",
        opts: ["Strong Spark skills", "Some PySpark", "SQL-only today", "Training budget available", "Contract resource plan"],
      },
      {
        q: "What is the preferred data product deployment cadence — continuous (GitOps/CI-CD) or release trains?",
        why: "CI/CD with Fabric Git integration + Databricks Asset Bundles enables 10× faster data product delivery",
        opts: ["CI/CD GitOps", "Sprint release trains", "Monthly releases", "Ad hoc today"],
      },
    ],
  },
];

const ARCH_LAYERS = [
  {
    label: "Layer 0 — Sources",
    color: "#8b949e",
    items: ["100s SQL Server 2012–2022 (on-prem & Azure SQL MI)", "SAP ERP / MES Systems (PI, Aveva)", "OT/IoT Sensors (PLCs, SCADA)", "Lab / LIMS Systems", "External: Supplier APIs, LME Prices, Weather"],
    tools: ["SQL Server CDC", "ADF Self-hosted IR", "IoT Hub / Edge Hub", "Kafka (plant-floor)"],
  },
  {
    label: "Layer 1 — Ingestion & Landing",
    color: STEEL.blue,
    items: ["Fabric Mirroring for SQL 2022+ / SQL MI (near-zero latency, zero-cost ingestion)", "ADF / Fabric Pipelines for older SQL versions (batch CDC)", "Fabric Eventstream for IoT/Kafka real-time", "SFTP / REST connectors for external data"],
    tools: ["Fabric Mirroring", "Fabric Eventstream", "ADF v2", "Event Hubs"],
  },
  {
    label: "Layer 2 — Raw / Bronze Zone",
    color: "#9a6dd7",
    items: ["Domain-partitioned OneLake Lakehouses per Data Mesh domain", "Delta Lake format — full fidelity, immutable append", "Databricks Autoloader for high-volume bulk ingestion", "Schema-on-read with Purview auto-discovery tagging"],
    tools: ["OneLake", "Delta Lake", "Databricks Autoloader", "Purview Scanner"],
  },
  {
    label: "Layer 3 — Cleansed / Silver Zone",
    color: STEEL.teal,
    items: ["Domain-owned DQ enforcement (6-pillar checks as Delta constraints)", "Databricks DLT (Delta Live Tables) for declarative ELT pipelines", "Fabric Dataflows Gen2 for citizen-accessible transformations", "Standardized schema registry: material grade, plant, equipment master"],
    tools: ["Databricks DLT", "Fabric Dataflows Gen2", "Great Expectations (via DLT)", "Unity Catalog"],
  },
  {
    label: "Layer 4 — Curated / Gold Zone",
    color: STEEL.accent,
    items: ["Published Data Products — domain contracts, SLOs, versioned schemas", "Fabric Warehouses for BI/SQL analytics consumers", "Databricks Lakehouse for ML feature pipelines", "Aggregated KPIs: OEE, Yield Rate, Heat-to-Heat quality, Energy Intensity"],
    tools: ["Fabric Warehouse", "Databricks Feature Store", "dbt (for complex transforms)", "Power BI Semantic Models"],
  },
  {
    label: "Layer 5 — AI / Intelligence",
    color: "#2ea043",
    items: ["Databricks Mosaic AI: model training, MLflow registry, inference serving", "Azure ML for regulated/explainable AI models (ISO audit trail)", "Microsoft Fabric Copilot / Real-Time Intelligence for operational alerts", "Copilot Studio agents for floor-operator natural language Q&A"],
    tools: ["Databricks Mosaic AI", "Azure ML", "Fabric Real-Time Intelligence", "Copilot Studio"],
  },
  {
    label: "Layer 6 — Consumption",
    color: "#d4a017",
    items: ["Power BI Premium (Gen2) — Direct Lake mode for zero-copy BI", "Fabric Real-Time Dashboards for plant floor operators", "REST/GraphQL Data Product APIs for downstream apps", "Azure OpenAI / RAG over operational documents"],
    tools: ["Power BI Direct Lake", "Fabric RT Dashboards", "APIM Data Product Gateway", "Azure OpenAI"],
  },
  {
    label: "Cross-Cutting — Governance Fabric",
    color: "#e05252",
    items: ["Microsoft Purview: catalog, lineage, sensitivity labels, DLP policies", "Databricks Unity Catalog: table ACLs, column masking, audit logs", "Entra ID (AAD): identity, RBAC, Conditional Access for Fabric/Databricks", "Azure Policy + Defender for Cloud: compliance posture"],
    tools: ["Microsoft Purview", "Unity Catalog", "Entra ID", "Azure Policy"],
  },
];

const DQ_PILLARS = [
  {
    pillar: "Completeness",
    icon: "◉",
    color: STEEL.accent,
    definition: "All required data attributes are present and non-null for every entity",
    steelContext: "Critical for heat records — missing mill temperature or chemistry results invalidates the entire cast",
    fabricImpl: "Fabric DQ Monitor: null-rate checks per column, per domain. Alert threshold: >99.5% completeness SLA on critical fields",
    databricksImpl: "DLT Expectations: @dlt.expect_or_drop('temp_not_null', 'cast_temp IS NOT NULL'). Quarantine incomplete records to Bronze reject Delta table",
    kpis: ["Null Rate %", "Missing Record Rate", "Completeness Score per Domain"],
    dama: "DAMA DM-BOK: Data Quality Assessment — Completeness is Dimension 1",
  },
  {
    pillar: "Accuracy",
    icon: "◎",
    color: STEEL.blue,
    definition: "Data values correctly represent the real-world entity or event they describe",
    steelContext: "Alloy composition (C%, Mn%, Si%) must match spectrometer lab results to within ±0.002%. Erroneous values cause downstream grade mis-classification",
    fabricImpl: "Fabric DQ Rules: range validation against ISO grade spec tables. Cross-reference SQL Server source vs. LIMS lab confirmation",
    databricksImpl: "Delta constraints: CHECK (carbon_pct BETWEEN 0.001 AND 1.50). DLT quarantine pipeline with MLflow anomaly scoring for outlier detection",
    kpis: ["Accuracy Rate vs. Reference System", "Out-of-Spec Detection Rate", "LIMS Reconciliation Score"],
    dama: "DAMA: Cross-reference to authoritative source systems required",
  },
  {
    pillar: "Consistency",
    icon: "⬡",
    color: STEEL.teal,
    definition: "Same data represents the same value across multiple systems, domains, and time points",
    steelContext: "Material grade 'S355J2' must be coded identically across SAP, MES, LIMS, and Logistics — currently 6+ variants exist",
    fabricImpl: "Purview Business Glossary: canonical term for every material grade, equipment ID, plant code. Fabric DQ cross-domain reconciliation reports",
    databricksImpl: "Unity Catalog shared dimension tables as Gold-layer master data. Delta Sharing for cross-domain reads. DLT cross-join consistency assertion",
    kpis: ["Cross-System Match Rate", "MDM Golden Record Adoption %", "Inconsistency Event Count"],
    dama: "DAMA: MDM and Reference Data Management are mandatory sub-disciplines",
  },
  {
    pillar: "Timeliness",
    icon: "◷",
    color: "#2ea043",
    definition: "Data is available when needed and represents a current enough view of reality",
    steelContext: "Predictive maintenance models need vibration sensor data within 10 seconds of emission. End-of-shift production summaries needed by 06:00 for day-shift planning",
    fabricImpl: "Fabric Eventstream SLA monitoring: watermark lag alerts. Fabric Pipeline run freshness checks via Data Activator triggers",
    databricksImpl: "DLT continuous pipelines for streaming Silver tables. MLflow model freshness: auto-retrain trigger if training data > 30 days old",
    kpis: ["Data Latency P95", "Pipeline SLA Breach Count", "Freshness Score per Product"],
    dama: "DAMA: Currency and Timeliness are separate but related dimensions",
  },
  {
    pillar: "Uniqueness",
    icon: "◈",
    color: "#d4a017",
    definition: "Each real-world entity is represented exactly once — no duplicates, no phantom records",
    steelContext: "Heat numbers must be globally unique across 100s of SQL Server DBs. Coil IDs sometimes duplicated across plant systems due to legacy numbering",
    fabricImpl: "Fabric DQ Monitor: duplicate key detection at ingestion. Fabric Warehouse UNIQUE constraints on dimension keys. Alert on duplicate load",
    databricksImpl: "DLT: @dlt.expect_or_fail('unique_heat_id', 'COUNT(*) = COUNT(DISTINCT heat_id)'). Merge (UPSERT) pattern in Silver to deduplicate",
    kpis: ["Duplicate Rate per Entity", "Golden Record Merge Success Rate", "Unique Key Violation Count"],
    dama: "DAMA: Uniqueness/Deduplication is addressed under Data Integration and Interoperability",
  },
  {
    pillar: "Validity",
    icon: "◇",
    color: "#9a6dd7",
    definition: "Data conforms to defined business rules, formats, referential integrity, and permitted value sets",
    steelContext: "Steel grade codes must exist in the grade master. Rolling temperatures must be physically possible (e.g., 700°C–1300°C). Negative tonnage is invalid",
    fabricImpl: "Purview Data Quality: rule-based validity checks tied to Business Glossary constraints. Fabric Warehouse FK constraints on dimension tables",
    databricksImpl: "Delta Lake CHECK constraints in DDL. DLT multi-expectation suites mapped to ISO 9001 control points. Quarantine invalid rows with error code tagging",
    kpis: ["Rule Pass Rate %", "Invalid Record Rejection Count", "Business Rule Coverage %"],
    dama: "DAMA: Validity maps to Data Architecture standards and business rule documentation",
  },
];

const DAMA_AREAS = [
  { area: "Data Governance", tool: "Microsoft Purview + Fabric Admin Portal", detail: "Federated governance council: CDO + Domain Data Owners. Purview policies enforce data access. Fabric tenant-level DLP.", priority: "CRITICAL" },
  { area: "Data Architecture", tool: "Medallion Lakehouse + Data Mesh domains", detail: "OneLake as single logical storage. Domain-isolated Lakehouses. Fabric Workspace = Domain boundary.", priority: "CRITICAL" },
  { area: "Data Modeling", tool: "dbt + Fabric Warehouse + Unity Catalog", detail: "Dimensional models for BI. OBT (One Big Table) patterns for ML. Physical data catalog in Purview.", priority: "HIGH" },
  { area: "Data Storage & Operations", tool: "OneLake Delta Lake + SQL MI", detail: "Delta Lake ACID transactions. Backup via OneLake versioning. SQL MI for operational workloads.", priority: "HIGH" },
  { area: "Data Security", tool: "Entra ID + Unity Catalog + Purview DLP", detail: "Attribute-based access control. Column-level masking on PII. Row-level security per plant/role.", priority: "CRITICAL" },
  { area: "Data Integration", tool: "Fabric Mirroring + ADF + Eventstream", detail: "Event-driven ingestion preferred. CDC over batch. API-first data product publishing.", priority: "HIGH" },
  { area: "Reference & Master Data", tool: "Fabric Warehouse MDM layer + SAP integration", detail: "Material Grade, Equipment, Plant master in Gold. SAP as system of record for MDM.", priority: "CRITICAL" },
  { area: "Data Warehousing & BI", tool: "Fabric Warehouse + Power BI Direct Lake", detail: "Direct Lake mode eliminates import latency. Composite models for cross-domain BI.", priority: "HIGH" },
  { area: "Document & Content Mgmt", tool: "Azure AI Search + SharePoint Premium", detail: "Technical standards, SDS, ISO documents searchable via RAG-based Copilot.", priority: "MEDIUM" },
  { area: "Metadata Management", tool: "Microsoft Purview + Databricks Unity Catalog", detail: "Auto-scan pipelines register lineage. Business glossary linked to technical assets.", priority: "HIGH" },
  { area: "Data Quality", tool: "Fabric DQ Monitor + Databricks DLT Expectations", detail: "6-pillar DQ framework enforced at Silver layer. DQ dashboards per domain.", priority: "CRITICAL" },
];

const ROADMAP = [
  {
    phase: "Phase 0 — Foundation (Months 1–3)",
    color: STEEL.blue,
    theme: "Land, Discover, Govern",
    tracks: [
      { track: "Platform", items: ["Provision Microsoft Fabric capacity (F64 pilot)", "Deploy Databricks Premium workspace (Unity Catalog on)", "Configure Entra ID groups & Fabric RBAC", "Set up Purview account + auto-scan SQL Server catalog"] },
      { track: "Architecture", items: ["Define 5–7 anchor data domains (Production, Quality, Maintenance, Energy, Supply Chain, Finance, MDM)", "Create domain Fabric Workspaces + OneLake Lakehouses (Bronze/Silver/Gold per domain)", "Establish Medallion naming conventions and Delta Lake standards doc"] },
      { track: "Ingestion", items: ["Enable Fabric Mirroring on top 10 SQL Server 2022/SQL MI databases", "Deploy ADF Self-hosted IR for on-premises SQL Server access", "Validate CDC pipelines for 3 anchor domains"] },
      { track: "Governance", items: ["Identify Domain Data Owners — get sign-off from business leads", "Draft first 3 Data Product contracts (schema, SLA, owner, consumers)", "Publish initial Business Glossary in Purview: 50 core steel terms"] },
    ],
    deliverables: ["Fabric Workspace topology live", "Purview catalog with SQL Server inventory", "3 domain Bronze tables streaming", "DQ baseline metrics for anchor domains"],
  },
  {
    phase: "Phase 1 — Core Data Mesh (Months 4–9)",
    color: STEEL.accent,
    theme: "Build, Publish, Consume",
    tracks: [
      { track: "Ingestion", items: ["Scale Fabric Mirroring to 50+ SQL Server DBs", "Deploy Eventstream for IoT/SCADA sensor data (Predictive Maint domain)", "Complete CDC coverage for all anchor domains"] },
      { track: "Data Products", items: ["Publish 10 certified Gold Data Products (Heat Master, Coil Registry, Grade Quality, OEE, Energy KPI, Supplier Perf, etc.)", "Deploy Data Product API gateway via Azure APIM", "Power BI Direct Lake semantic models for 5 core dashboards"] },
      { track: "DQ", items: ["Implement 6-pillar DQ rules in Databricks DLT for all Silver tables", "Deploy Fabric DQ Monitor dashboards per domain", "MDM Golden Record for Material Grade and Equipment IDs live in SAP-sync"] },
      { track: "AI/ML", items: ["ML Feature Store in Databricks for Predictive Maintenance", "First production model: Bearing failure prediction (F1 > 0.80 target)", "MLflow registry with model governance (approval workflow)"] },
    ],
    deliverables: ["10 published data products", "6-pillar DQ dashboard live", "First AI model in production", "Direct Lake Power BI platform"],
  },
  {
    phase: "Phase 2 — Scale & Optimize (Months 10–18)",
    color: STEEL.teal,
    theme: "Scale, Optimize, AI-First",
    tracks: [
      { track: "Scale", items: ["Migrate remaining SQL Server databases (target: 80% of estate covered)", "On-board 4 additional data domains", "Scale Fabric capacity to F128–F256 based on actual utilization telemetry"] },
      { track: "AI/ML", items: ["Scrap & yield prediction model (target: 2% yield improvement)", "Energy optimization model (ISO 50001 baseline)", "Copilot Studio agent for floor operator Q&A on quality specs"] },
      { track: "Self-Service", items: ["Domain team CI/CD pipelines via Fabric Git integration + Azure DevOps", "Databricks Asset Bundles for domain-owned job deployments", "Data product marketplace (Purview catalog front-end)"] },
      { track: "Governance", items: ["Full Purview lineage coverage (source SQL → Gold data product)", "CBAM/Carbon reporting data product (ESG domain)", "ISO 9001 audit trail via Purview + Unity Catalog audit logs"] },
    ],
    deliverables: ["80%+ SQL estate migrated", "5 AI models in production", "Self-serve data product publishing", "ESG data product for CBAM compliance"],
  },
  {
    phase: "Phase 3 — Intelligent Enterprise (Months 19–30)",
    color: "#2ea043",
    theme: "Intelligence, Innovation, Platform Product",
    tracks: [
      { track: "AI", items: ["Computer vision for surface defect detection (Azure Vision + Databricks)", "GenAI knowledge base: ISO standards, metallurgical recipes, customer specs", "Real-time inference on mill floor (< 1s latency via Databricks Model Serving)"] },
      { track: "Platform", items: ["Data product versioning, deprecation workflow", "Chargeback model: per-domain cost allocation via Fabric capacity metrics", "Evaluate Fabric vs. Databricks rationalization for long-term TCO"] },
      { track: "Innovation", items: ["Digital Twin of critical assets (Azure Digital Twins + Fabric)", "Supplier data collaboration via Delta Sharing", "Industry benchmark data product for peer comparison"] },
    ],
    deliverables: ["Full AI-driven operations capability", "Domain chargeback live", "Digital Twin MVP", "Data product marketplace with 30+ certified products"],
  },
];

const COST_STRATEGIES = [
  { strategy: "Fabric Mirroring as Zero-Ingestion-Cost Path", saving: "HIGH", detail: "Fabric Mirroring for SQL 2022/SQL MI replaces ADF pipelines — no Data Movement Units charged, no self-hosted IR cost for eligible sources. Prioritize SQL Server upgrades to 2022 to unlock this." },
  { strategy: "Delta Lake OPTIMIZE + ZORDER on Query Patterns", saving: "HIGH", detail: "Unoptimized Delta tables cause full-scan reads, inflating Fabric CU consumption. OPTIMIZE with ZORDER on heat_id, plant_code, and timestamp cuts query CUs by 60–80% on hot paths." },
  { strategy: "Direct Lake Mode (Power BI) — Eliminate Import", saving: "HIGH", detail: "Import mode duplicates data and requires scheduled refreshes consuming capacity. Direct Lake reads Delta files directly — zero duplication, no refresh cost, sub-second queries." },
  { strategy: "Databricks Spot/Preemptible Clusters for Batch ELT", saving: "MEDIUM", detail: "DLT triggered batch pipelines run on spot instances (70% cost reduction). Reserve On-Demand only for streaming DLT and inference serving endpoints." },
  { strategy: "Fabric Capacity Pause Scheduler for Non-Production", saving: "MEDIUM", detail: "Dev/Test Fabric capacities pause overnight and weekends (18 hrs/day = 75% cost saving on dev F-SKU). Use Fabric Admin API with Azure Automation runbooks." },
  { strategy: "Unity Catalog for Cross-Workspace Data Sharing", saving: "MEDIUM", detail: "Without Unity Catalog, teams copy data between workspaces (storage + CU cost). Unity Catalog enables read-in-place — one Delta table, many consumers, zero copy." },
  { strategy: "Tiered Storage: Hot/Cool/Archive in OneLake", saving: "MEDIUM", detail: "Raw Bronze older than 90 days moves to Azure Cool Blob tier (50% storage cost reduction). Archive tier for regulatory data > 3 years. Fabric shortcuts maintain transparent access." },
  { strategy: "Right-size Databricks SQL Warehouses", saving: "MEDIUM", detail: "Auto-stop SQL warehouses after 10-min idle. Use Serverless SQL Warehouse for ad-hoc queries (per-second billing vs. minimum 10-min classic cluster). Scale-down medium to small for off-peak BI." },
];

// ── Components ───────────────────────────────────────────────────────────────

function OverviewTab() {
  const stats = [
    { num: "7", label: "Data Domains", color: STEEL.accent },
    { num: "6", label: "DQ Pillars", color: STEEL.blue },
    { num: "4", label: "Delivery Phases", color: STEEL.teal },
    { num: "11", label: "DAMA Areas", color: "#9a6dd7" },
    { num: "8", label: "Architecture Layers", color: "#2ea043" },
    { num: "30mo", label: "Full Delivery", color: "#d4a017" },
  ];

  return (
    <div>
      <div style={styles.sectionLabel}>Strategic Data Architecture</div>
      <div style={styles.sectionTitle}>Steel Manufacturing — AI-Optimized Data Platform</div>
      <div style={styles.sectionDesc}>
        A comprehensive reference architecture for migrating hundreds of SQL Server databases into a unified, AI-ready data platform on Microsoft Fabric, Azure, and Databricks — governed by Data Mesh principles, DAMA DM-BOK, and enforced 6-pillar data quality.
      </div>

      <div style={{ ...styles.grid3, gridTemplateColumns: "repeat(6, 1fr)" }}>
        {stats.map((s) => (
          <div key={s.label} style={styles.cardAccent(s.color)}>
            <div style={{ color: s.color, fontSize: "26px", fontWeight: 700 }}>{s.num}</div>
            <div style={{ color: STEEL.muted, fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div style={styles.divider} />

      <div style={styles.grid2}>
        <div>
          <div style={styles.infoBox(STEEL.accent)}>
            <div style={styles.infoTitle(STEEL.accent)}>⚡ Design Principles</div>
            <ul style={styles.ul}>
              <li><span style={styles.strong}>Mesh over Monolith</span> — Federated domain ownership with central governance guardrails</li>
              <li><span style={styles.strong}>OneLake as the Nervous System</span> — All domains write to OneLake; zero data silos, no copies</li>
              <li><span style={styles.strong}>Mirroring First</span> — Prefer Fabric Mirroring for SQL 2022+ before ADF pipelines</li>
              <li><span style={styles.strong}>DQ as Pipeline Code</span> — Data quality rules in Delta constraints, DLT expectations, Fabric DQ Monitor</li>
              <li><span style={styles.strong}>AI Baked In</span> — Feature Store and MLflow from Day 1; not bolted on later</li>
              <li><span style={styles.strong}>GitOps Everything</span> — Fabric Git + Databricks Asset Bundles for reproducible deployments</li>
              <li><span style={styles.strong}>Cost Telemetry First</span> — Fabric Capacity Metrics app deployed before production workloads</li>
            </ul>
          </div>
        </div>
        <div>
          <div style={styles.infoBox(STEEL.blue)}>
            <div style={styles.infoTitle(STEEL.blue)}>🏭 Steel Domain Map</div>
            {[
              ["Production / MES", "Heat records, cast sequences, rolling schedules"],
              ["Quality / Metallurgy", "Chemistry, mechanical props, grade classification"],
              ["Maintenance", "Asset health, work orders, sensor telemetry"],
              ["Energy", "Gas, electricity, water consumption per heat"],
              ["Supply Chain", "Raw materials, scrap grading, logistics"],
              ["Finance / Costing", "Cost per tonne, variance, P&L per product"],
              ["MDM / Reference", "Material grades, plant codes, equipment master"],
            ].map(([d, desc]) => (
              <div key={d} style={{ marginBottom: "8px" }}>
                <span style={{ color: STEEL.text, fontWeight: 700, fontSize: "12px" }}>{d}</span>
                <span style={{ color: STEEL.muted, fontSize: "11px" }}> — {desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={styles.infoBox(STEEL.teal)}>
        <div style={styles.infoTitle(STEEL.teal)}>🎯 Platform Triad — Why Fabric + Azure + Databricks Together?</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
          {[
            { p: "Microsoft Fabric", role: "Unified BI, warehousing, and orchestration", strengths: ["OneLake single-store", "Direct Lake for Power BI", "Fabric Mirroring ingestion", "Eventstream for IoT", "Fabric DQ Monitor", "Native Purview integration"] },
            { p: "Azure PaaS", role: "Identity, governance, connectivity backbone", strengths: ["Entra ID for RBAC", "Azure Purview catalog & lineage", "ADF for complex ingestion", "Azure OpenAI for LLM workloads", "APIM for data product APIs", "Azure Policy for compliance"] },
            { p: "Databricks", role: "Heavy ELT, ML engineering, and advanced analytics", strengths: ["Delta Live Tables (DLT)", "Unity Catalog cross-platform", "MLflow + Mosaic AI", "Feature Store", "Photon engine for Spark performance", "Streaming + batch unification"] },
          ].map((p) => (
            <div key={p.p}>
              <div style={{ color: STEEL.text, fontWeight: 700, fontSize: "12px", marginBottom: "4px" }}>{p.p}</div>
              <div style={{ color: STEEL.muted, fontSize: "11px", marginBottom: "6px", fontStyle: "italic" }}>{p.role}</div>
              <ul style={{ ...styles.ul, paddingLeft: "12px" }}>
                {p.strengths.map((s) => <li key={s}>{s}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function QuestionnaireTab() {
  const [open, setOpen] = useState({});
  const toggle = (key) => setOpen((o) => ({ ...o, [key]: !o[key] }));
  let globalIdx = 0;

  return (
    <div>
      <div style={styles.sectionLabel}>Phase 0 Discovery</div>
      <div style={styles.sectionTitle}>Architecture Discovery Questionnaire</div>
      <div style={styles.sectionDesc}>
        42 targeted questions across 7 domains. Conduct as structured workshops with Domain Data Owners, plant IT leads, and business stakeholders. Answers directly shape platform sizing, ingestion strategy, and domain boundary design.
      </div>

      {QUESTIONNAIRE.map((section) => (
        <div key={section.category} style={{ marginBottom: "28px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
            <div style={{ width: "4px", height: "24px", background: section.color, borderRadius: "2px" }} />
            <div style={{ color: section.color, fontSize: "12px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "2px" }}>{section.category}</div>
          </div>
          {section.questions.map((q) => {
            globalIdx++;
            const idx = globalIdx;
            const key = `${section.category}-${idx}`;
            return (
              <div key={key} style={styles.qBlock}>
                <div style={{ ...styles.qHeader, cursor: "pointer" }} onClick={() => toggle(key)}>
                  <div style={styles.qNum}>{idx}</div>
                  <div style={{ flex: 1 }}>
                    <div style={styles.qText}>{q.q}</div>
                    {open[key] && <div style={styles.qWhy}>↳ Architect's rationale: {q.why}</div>}
                  </div>
                  <div style={{ color: STEEL.subtle, fontSize: "16px", marginLeft: "8px" }}>{open[key] ? "▲" : "▼"}</div>
                </div>
                {open[key] && (
                  <div style={styles.qOptions}>
                    {q.opts.map((o) => (
                      <div key={o} style={styles.qOpt(section.color)}>{o}</div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function ArchitectureTab() {
  return (
    <div>
      <div style={styles.sectionLabel}>Technical Blueprint</div>
      <div style={styles.sectionTitle}>8-Layer Reference Architecture</div>
      <div style={styles.sectionDesc}>
        Medallion Lakehouse extended with a Data Mesh domain layer. Every layer maps to specific Microsoft Fabric, Azure, and Databricks components optimized for steel manufacturing workloads.
      </div>

      {ARCH_LAYERS.map((layer) => (
        <div key={layer.label} style={styles.layerBox(layer.color)}>
          <div style={styles.layerTitle(layer.color)}>{layer.label}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <div style={{ color: STEEL.muted, fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }}>Capabilities</div>
              <ul style={{ ...styles.ul, marginTop: 0 }}>
                {layer.items.map((i) => <li key={i} style={styles.li}>{i}</li>)}
              </ul>
            </div>
            <div>
              <div style={{ color: STEEL.muted, fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }}>Primary Tools</div>
              <div style={{ display: "flex", flexWrap: "wrap" }}>
                {layer.tools.map((t) => <span key={t} style={styles.badge(layer.color)}>{t}</span>)}
              </div>
            </div>
          </div>
        </div>
      ))}

      <div style={styles.divider} />

      <div style={styles.infoBox(STEEL.accent)}>
        <div style={styles.infoTitle(STEEL.accent)}>🔑 Architecture Decision Records (ADRs)</div>
        {[
          ["ADR-001", "OneLake as single logical storage — no cross-cloud replication", "OneLake eliminates storage fragmentation. All Fabric and Databricks workloads reference the same ADLS Gen2 endpoint via Fabric Shortcuts"],
          ["ADR-002", "Delta Lake as universal table format", "Delta provides ACID transactions, schema enforcement, time travel, and CDC compatibility across Fabric Warehouse, Databricks, and direct OneLake access"],
          ["ADR-003", "Domain Workspace isolation over shared multi-domain Lakehouse", "Prevents noisy-neighbor CU contention. Each domain has independent Fabric Workspace, enabling per-domain capacity charging and access boundary enforcement"],
          ["ADR-004", "Databricks Unity Catalog as enterprise metadata layer", "Unity Catalog spans Databricks and Fabric (via mirrored catalog). Single governance point for table ACLs, column masking, and audit logs across both platforms"],
          ["ADR-005", "Fabric Mirroring prioritized over ADF CDC for SQL 2022+", "Mirroring has no DFU cost, sub-minute latency, and zero-code setup. Saves estimated $120K/yr in ADF pipeline costs for 100+ eligible SQL Server databases"],
        ].map(([id, title, detail]) => (
          <div key={id} style={{ marginBottom: "12px", paddingBottom: "12px", borderBottom: `1px solid ${STEEL.border}` }}>
            <div style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
              <span style={styles.badge(STEEL.accent)}>{id}</span>
              <div>
                <div style={{ color: STEEL.text, fontWeight: 700, fontSize: "12px", marginBottom: "3px" }}>{title}</div>
                <div style={{ color: STEEL.muted, fontSize: "11px" }}>{detail}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DataMeshTab() {
  return (
    <div>
      <div style={styles.sectionLabel}>Data Mesh Implementation</div>
      <div style={styles.sectionTitle}>Federated Domain Architecture</div>
      <div style={styles.sectionDesc}>
        Applying all 4 Data Mesh principles to steel manufacturing: domain ownership, data as a product, self-serve platform, and federated computational governance — without sacrificing centralized cost control.
      </div>

      <div style={styles.grid2}>
        {[
          { p: "Principle 1: Domain Ownership", color: STEEL.accent, impl: [
            "Each steel domain (Production, Quality, Maintenance, Energy, Supply Chain, Finance) has a named Domain Data Owner (DDO)",
            "DDO signs Data Product contracts — schema, SLA, quality thresholds, retention policy",
            "Domain teams own their Fabric Workspace: Lakehouse (Bronze/Silver/Gold), Pipelines, Notebooks, and Warehouses",
            "Central Platform Team owns: OneLake tenant, Purview, Unity Catalog, Fabric Admin Portal, Entra ID groups only",
          ]},
          { p: "Principle 2: Data as a Product", color: STEEL.blue, impl: [
            "Data Product definition: discoverable (Purview catalog), addressable (OneLake URI + API), trustworthy (DQ SLA), self-describing (schema in Unity Catalog), interoperable (Delta format + REST API), secure (row-level security)",
            "Minimum Viable Data Product checklist enforced via GitHub PR template",
            "Data Product versioning: semantic versioning (v1.0.0) with breaking-change deprecation policy",
            "Power BI semantic model is also a Data Product — governed same way",
          ]},
          { p: "Principle 3: Self-Serve Platform", color: STEEL.teal, impl: [
            "Fabric Workspace provisioning automated via Terraform + Azure DevOps (< 2hr from request to ready)",
            "Domain pipeline templates in GitHub: Bronze ingestion, DLT Silver, Gold aggregation — parameterize and deploy in hours",
            "Databricks Asset Bundles for ML pipeline self-service deployment",
            "Catalog discovery via Purview with one-click Delta Sharing access request workflow",
          ]},
          { p: "Principle 4: Federated Computational Governance", color: "#9a6dd7", impl: [
            "Governance policies enforced by platform, not by process: Unity Catalog masks PII automatically, Purview DLP blocks exfiltration",
            "Domain teams cannot bypass governance rails — Entra ID Conditional Access + Fabric workspace policies",
            "Cross-domain data sharing via Delta Sharing contracts, not data copies — each share has an audit log",
            "Data Governance Council: CDO (chair) + 1 DDO per domain + Platform Architect + Security — meets bi-weekly",
          ]},
        ].map((item) => (
          <div key={item.p} style={styles.cardAccent(item.color)}>
            <div style={{ color: item.color, fontSize: "11px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "10px" }}>{item.p}</div>
            <ul style={styles.ul}>
              {item.impl.map((i, idx) => <li key={idx} style={styles.li}>{i}</li>)}
            </ul>
          </div>
        ))}
      </div>

      <div style={styles.divider} />

      <div style={styles.sectionTitle} style={{ fontSize: "14px", fontWeight: 700, color: STEEL.text, marginBottom: "16px" }}>Domain Topology — Fabric Workspace per Domain</div>

      <table style={styles.table}>
        <thead>
          <tr>
            {["Domain", "DDO Role", "Primary Sources", "Key Data Products", "Consumers", "Priority"].map((h) => (
              <th key={h} style={styles.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[
            ["Production / MES", "Plant Manager", "MES SQL DBs, PI Historian", "Heat Master, Cast Schedule, OEE", "Quality, Finance, AI/ML", "CRITICAL"],
            ["Quality / Metallurgy", "Chief Metallurgist", "LIMS SQL DBs, Lab Apps", "Coil Quality, Grade Cert, Defect Rate", "Production, Sales, Compliance", "CRITICAL"],
            ["Maintenance", "Maintenance Director", "CMMS SQL DBs, SCADA", "Asset Health, Work Orders, MTBF", "Production, Finance, AI/ML", "HIGH"],
            ["Energy", "Energy Manager", "SCADA, Metering DBs", "Energy per Heat, Carbon Intensity", "Finance, ESG, Compliance", "HIGH"],
            ["Supply Chain", "Supply Chain VP", "SAP MM, Logistics DBs", "Scrap Grade, Inventory, Supplier Perf", "Production, Finance", "HIGH"],
            ["Finance / Costing", "CFO/Controller", "SAP FI/CO, ERP DBs", "Cost per Tonne, Variance, P&L", "Executive, BI Users", "MEDIUM"],
            ["MDM / Reference", "Chief Data Officer", "SAP MDM, Manual spreadsheets", "Material Grade Master, Plant Codes", "ALL domains", "CRITICAL"],
          ].map(([domain, ddo, src, products, consumers, prio], i) => (
            <tr key={domain} style={i % 2 === 1 ? styles.trAlt : {}}>
              <td style={{ ...styles.td, fontWeight: 700, color: STEEL.text }}>{domain}</td>
              <td style={{ ...styles.td, color: STEEL.muted }}>{ddo}</td>
              <td style={{ ...styles.td, color: STEEL.muted, fontSize: "11px" }}>{src}</td>
              <td style={{ ...styles.td, color: STEEL.muted, fontSize: "11px" }}>{products}</td>
              <td style={{ ...styles.td, color: STEEL.muted, fontSize: "11px" }}>{consumers}</td>
              <td style={styles.td}>
                <span style={styles.badge(prio === "CRITICAL" ? STEEL.accent : prio === "HIGH" ? STEEL.blue : STEEL.teal)}>{prio}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function QualityTab() {
  const [active, setActive] = useState(0);
  const p = DQ_PILLARS[active];

  return (
    <div>
      <div style={styles.sectionLabel}>DAMA + ISO 8000</div>
      <div style={styles.sectionTitle}>6 Pillars of Data Quality — Steel Manufacturing Implementation</div>
      <div style={styles.sectionDesc}>
        Each pillar is enforced as code — not as a spreadsheet audit. Rules live in Delta Lake constraints, Databricks DLT expectations, and Fabric DQ Monitor policies, creating automated, measurable, and auditable data quality.
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "20px", flexWrap: "wrap" }}>
        {DQ_PILLARS.map((pp, i) => (
          <button
            key={pp.pillar}
            onClick={() => setActive(i)}
            style={{
              background: active === i ? pp.color : "#1c2128",
              color: active === i ? "#000" : STEEL.muted,
              border: `1px solid ${active === i ? pp.color : STEEL.border}`,
              borderRadius: "4px",
              padding: "8px 16px",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "inherit",
              letterSpacing: "1px",
              textTransform: "uppercase",
            }}
          >
            {pp.icon} {pp.pillar}
          </button>
        ))}
      </div>

      <div style={styles.layerBox(p.color)}>
        <div style={styles.layerTitle(p.color)}>{p.icon} {p.pillar}</div>
        <div style={{ marginBottom: "14px" }}>
          <div style={{ color: STEEL.muted, fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>Definition</div>
          <div style={{ color: STEEL.text, fontSize: "13px" }}>{p.definition}</div>
        </div>
        <div style={{ marginBottom: "14px" }}>
          <div style={{ color: STEEL.muted, fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>Steel Manufacturing Context</div>
          <div style={{ color: STEEL.text, fontSize: "12px", fontStyle: "italic" }}>{p.steelContext}</div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "14px" }}>
          <div style={styles.infoBox(STEEL.blue)}>
            <div style={styles.infoTitle(STEEL.blue)}>Microsoft Fabric Implementation</div>
            <div style={{ color: STEEL.text, fontSize: "12px" }}>{p.fabricImpl}</div>
          </div>
          <div style={styles.infoBox("#9a6dd7")}>
            <div style={styles.infoTitle("#9a6dd7")}>Databricks DLT Implementation</div>
            <div style={{ color: STEEL.text, fontSize: "12px", fontFamily: "monospace" }}>{p.databricksImpl}</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <div style={{ color: STEEL.muted, fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }}>KPIs to Track</div>
            <div>{p.kpis.map((k) => <span key={k} style={styles.badge(p.color)}>{k}</span>)}</div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: STEEL.muted, fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }}>DAMA Reference</div>
            <div style={{ color: STEEL.muted, fontSize: "11px", fontStyle: "italic" }}>{p.dama}</div>
          </div>
        </div>
      </div>

      <div style={styles.infoBox(STEEL.accent)}>
        <div style={styles.infoTitle(STEEL.accent)}>DQ Enforcement Architecture — How All 6 Pillars Work Together</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
          {[
            { layer: "Bronze (Raw)", rules: ["Schema validation", "Null detection logging", "Duplicate flagging (not rejected)"], note: "Log-only, never reject at Bronze" },
            { layer: "Silver (Cleansed)", rules: ["DLT Expectations enforce all 6 pillars", "Quarantine table for rejections", "DQ score persisted as metadata column"], note: "Hard enforcement — quarantine bad rows" },
            { layer: "Gold (Certified)", rules: ["Domain SLA compliance check", "Cross-domain consistency validation", "Purview DQ scan results published"], note: "Consumer-facing SLA guarantee" },
          ].map((l) => (
            <div key={l.layer}>
              <div style={{ color: STEEL.text, fontWeight: 700, fontSize: "12px", marginBottom: "4px" }}>{l.layer}</div>
              <ul style={styles.ul}>
                {l.rules.map((r) => <li key={r}>{r}</li>)}
              </ul>
              <div style={{ color: STEEL.accent, fontSize: "10px", fontStyle: "italic", marginTop: "4px" }}>{l.note}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PlatformsTab() {
  return (
    <div>
      <div style={styles.sectionLabel}>Platform Configuration</div>
      <div style={styles.sectionTitle}>Microsoft Fabric + Azure + Databricks Blueprint</div>
      <div style={styles.sectionDesc}>
        Detailed configuration guidance for each platform component, including recommended SKUs, integration patterns, and steel-specific configuration decisions.
      </div>

      {[
        {
          title: "Microsoft Fabric — Configuration Blueprint",
          color: STEEL.accent,
          sections: [
            { name: "Capacity Sizing", items: ["F64 for pilot (covers 1–2 domains, dev+prod)", "F128 for Phase 1 scale (5 domains, production workloads)", "F256+ for Phase 2 (all domains + Eventstream + Real-Time Intelligence)", "Separate F8 capacity for Dev/Test environments (pause overnight)", "Monitor via Fabric Capacity Metrics app — set CU alert at 80% before throttling"] },
            { name: "Workspace Topology", items: ["1 Workspace per domain × 3 environments (Dev/Test/Prod) = 21 workspaces for 7 domains", "Central shared workspace for: Purview integration, Admin dashboards, MDM Gold tables", "Fabric Git integration: each workspace linked to Azure DevOps repo branch", "Workspace identity: Managed Identity per workspace for secure ADF/AKV access"] },
            { name: "Fabric Mirroring Strategy", items: ["Tier 1 (Immediate): All SQL Server 2022 and SQL MI databases — enable Mirroring within weeks", "Tier 2 (Upgrade path): SQL Server 2019 databases — upgrade to 2022 in 3–6 months, then migrate", "Tier 3 (ADF CDC): SQL Server 2016 and older — use ADF with self-hosted IR, batch CDC", "Mirroring latency: typically 10–30 seconds; confirm network bandwidth from on-prem to Azure"] },
            { name: "Real-Time Intelligence", items: ["Fabric Eventstream: connect Azure IoT Hub → Eventstream → Bronze Lakehouse for plant sensor data", "Kusto (KQL) Database for millisecond-latency sensor queries (vibration, temperature, pressure)", "Data Activator for alert-to-action: trigger maintenance work order when bearing temp exceeds threshold", "Real-Time Dashboard for plant floor operators: OEE live, active alarms, production counts"] },
          ],
        },
        {
          title: "Databricks — Configuration Blueprint",
          color: STEEL.blue,
          sections: [
            { name: "Workspace & Unity Catalog Setup", items: ["1 Databricks workspace per Azure region (avoid cross-region Unity Catalog limitations)", "Unity Catalog metastore: 1 per region, register Fabric OneLake external locations as external storage", "3-tier namespace: catalog (domain) → schema (medallion layer) → table (data product)", "Example: steel_production.silver.heat_master, steel_quality.gold.coil_certification"] },
            { name: "Cluster Strategy", items: ["DLT pipelines: Enhanced Autoscaling clusters, spot instances for batch (savings ~70%)", "Streaming DLT: On-demand small clusters (spot not reliable for streaming)", "ML Training: GPU clusters (Standard_NC6s_v3) on spot with auto-terminate after job", "SQL Warehouse: Serverless for ad-hoc analysis, Classic Medium for BI tools with auto-stop at 10min"] },
            { name: "Delta Live Tables (DLT) Patterns", items: ["Bronze → Silver: Streaming DLT tables reading from OneLake Bronze Delta files (near-real-time)", "Silver DQ: @dlt.expect_or_quarantine decorators for all 6 DQ pillars per domain table", "Gold aggregations: Materialized views in DLT for daily/hourly KPI aggregations", "Trigger modes: Continuous for Maintenance/IoT domains; Triggered (15min) for Production/Quality domains"] },
            { name: "MLflow + Mosaic AI", items: ["MLflow Tracking: experiment tracking for all domain models (mandatory — no untracked experiments)", "Model Registry: staged workflow (Staging → Production → Archived) with approval gates", "Feature Store: shared feature tables in Unity Catalog — reuse features across domains", "Inference: Model Serving endpoints for real-time prediction; Databricks Jobs for batch scoring"] },
          ],
        },
        {
          title: "Azure Services — Integration Blueprint",
          color: STEEL.teal,
          sections: [
            { name: "Microsoft Purview", items: ["Auto-scan all SQL Server sources via Self-Hosted IR: schedule weekly full scan + daily incremental", "Sensitivity labels: Confidential (PII, IP), Internal (financial), Public (aggregated KPIs)", "Business Glossary: 200 steel terms minimum (ASTM grades, process terms, KPI definitions)", "Lineage: configure ADF + Databricks + Fabric lineage connectors — end-to-end source-to-report lineage"] },
            { name: "Azure Data Factory (ADF)", items: ["Purpose: Legacy SQL Server ingestion (pre-2022) + complex orchestration patterns only", "Self-Hosted Integration Runtime: deploy on-premises for SQL Server network access (2 nodes for HA)", "Parameterized pipelines: 1 pipeline template handles 100+ SQL Server sources via metadata-driven config", "Cost control: use Azure IR for cloud-to-cloud only; minimize self-hosted IR node count"] },
            { name: "Azure Key Vault + APIM", items: ["AKV: all connection strings, service principal secrets, and API keys — never hardcoded", "APIM: Data Product API gateway for external consumers and cross-domain API access", "APIM policies: rate limiting, OAuth2 (Entra ID), request logging to Log Analytics", "Data Product discovery portal: Azure API Portal as self-service catalog for data consumers"] },
            { name: "Azure OpenAI + AI Search", items: ["GPT-4o for Copilot Studio floor operator agent (Q&A on quality specs, ISO standards)", "AI Search: index technical documents (ASTM standards, customer specs, metallurgical recipes)", "RAG pattern: Copilot Studio → APIM → Azure AI Search → GPT-4o → domain knowledge response", "Safety: content filter on all OpenAI endpoints; no customer PII in prompts"] },
          ],
        },
      ].map((platform) => (
        <div key={platform.title} style={{ marginBottom: "28px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
            <div style={{ width: "4px", height: "24px", background: platform.color, borderRadius: "2px" }} />
            <div style={{ color: platform.color, fontSize: "13px", fontWeight: 700 }}>{platform.title}</div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            {platform.sections.map((s) => (
              <div key={s.name} style={styles.cardAccent(platform.color)}>
                <div style={{ color: platform.color, fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "8px" }}>{s.name}</div>
                <ul style={styles.ul}>
                  {s.items.map((i, idx) => <li key={idx} style={styles.li}>{i}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function GovernanceTab() {
  return (
    <div>
      <div style={styles.sectionLabel}>DAMA DM-BOK v2 Alignment</div>
      <div style={styles.sectionTitle}>11 DAMA Knowledge Areas — Steel Platform Mapping</div>
      <div style={styles.sectionDesc}>
        Every DAMA knowledge area mapped to specific platform tools, implementation approach, and priority tier. This becomes the Data Management Charter for the program.
      </div>

      <table style={styles.table}>
        <thead>
          <tr>
            {["DAMA Knowledge Area", "Platform Tool", "Steel Implementation Detail", "Priority"].map((h) => (
              <th key={h} style={styles.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {DAMA_AREAS.map((row, i) => (
            <tr key={row.area} style={i % 2 === 1 ? styles.trAlt : {}}>
              <td style={{ ...styles.td, fontWeight: 700, color: STEEL.text, width: "180px" }}>{row.area}</td>
              <td style={{ ...styles.td, color: STEEL.blue, fontSize: "11px", width: "220px" }}>{row.tool}</td>
              <td style={{ ...styles.td, color: STEEL.muted, fontSize: "11px" }}>{row.detail}</td>
              <td style={styles.td}>
                <span style={styles.badge(row.priority === "CRITICAL" ? STEEL.accent : row.priority === "HIGH" ? STEEL.blue : STEEL.teal)}>
                  {row.priority}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={styles.divider} />

      <div style={styles.grid2}>
        <div style={styles.infoBox(STEEL.accent)}>
          <div style={styles.infoTitle(STEEL.accent)}>Data Governance Operating Model</div>
          <ul style={styles.ul}>
            <li><span style={styles.strong}>CDO (Chief Data Officer)</span> — ultimate accountability for data as an asset</li>
            <li><span style={styles.strong}>Data Governance Council</span> — CDO + DDOs + Platform Architect, bi-weekly</li>
            <li><span style={styles.strong}>Domain Data Owners (DDO)</span> — business leads accountable for domain data quality & contracts</li>
            <li><span style={styles.strong}>Domain Data Stewards</span> — embedded engineers responsible for daily DQ operations</li>
            <li><span style={styles.strong}>Central Platform Team</span> — owns OneLake, Purview, Unity Catalog, Entra ID, cost governance</li>
            <li><span style={styles.strong}>Data Product Council</span> — reviews and certifies Gold data products before publication</li>
          </ul>
        </div>
        <div style={styles.infoBox(STEEL.blue)}>
          <div style={styles.infoTitle(STEEL.blue)}>Data Product Contract — Required Fields</div>
          <ul style={styles.ul}>
            <li><span style={styles.strong}>Identity</span>: Product name, version (semver), domain, DDO</li>
            <li><span style={styles.strong}>Schema</span>: Delta table URI, column definitions, data types, nullable policy</li>
            <li><span style={styles.strong}>Quality SLA</span>: Completeness %, Freshness window, Accuracy assertion</li>
            <li><span style={styles.strong}>Access Policy</span>: Allowed consumers, row/column filters, expiry</li>
            <li><span style={styles.strong}>Lineage</span>: Source systems, transformation pipeline links</li>
            <li><span style={styles.strong}>Retention</span>: Hot/warm/cold period, archival policy, legal hold flag</li>
            <li><span style={styles.strong}>Change Log</span>: Breaking change notice period (minimum 30 days)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function RoadmapTab() {
  return (
    <div>
      <div style={styles.sectionLabel}>30-Month Execution Plan</div>
      <div style={styles.sectionTitle}>Phased Delivery Roadmap</div>
      <div style={styles.sectionDesc}>
        4 phases with clear deliverables, parallel workstream tracks, and escalating scope. Each phase builds on the previous — infrastructure before products, products before scale, scale before innovation.
      </div>

      {ROADMAP.map((phase, pi) => (
        <div key={phase.phase} style={{ marginBottom: "32px" }}>
          <div style={styles.cardAccent(phase.color)}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <div style={styles.phaseLabel(phase.color)}>{phase.phase}</div>
                <div style={{ color: STEEL.text, fontSize: "16px", fontWeight: 700, marginBottom: "4px" }}>{phase.theme}</div>
              </div>
              <div style={styles.badge(phase.color)}>Phase {pi}</div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "16px" }}>
              {phase.tracks.map((track) => (
                <div key={track.track}>
                  <div style={{ color: phase.color, fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "6px" }}>
                    ▸ {track.track}
                  </div>
                  <ul style={styles.ul}>
                    {track.items.map((item, i) => <li key={i} style={styles.li}>{item}</li>)}
                  </ul>
                </div>
              ))}
            </div>
            <div style={{ borderTop: `1px solid ${phase.color}33`, paddingTop: "12px" }}>
              <div style={{ color: phase.color, fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "6px" }}>Phase Gate Deliverables</div>
              <div>{phase.deliverables.map((d) => <span key={d} style={styles.badge(phase.color)}>{d}</span>)}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function CostTab() {
  return (
    <div>
      <div style={styles.sectionLabel}>FinOps Strategy</div>
      <div style={styles.sectionTitle}>Cost Optimization Framework</div>
      <div style={styles.sectionDesc}>
        8 high-impact cost strategies specific to Fabric + Databricks architectures. Combined, these can reduce platform TCO by 40–60% compared to unoptimized deployments.
      </div>

      {COST_STRATEGIES.map((s, i) => (
        <div key={i} style={styles.cardAccent(s.saving === "HIGH" ? STEEL.accent : STEEL.blue)}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
            <div style={{ color: STEEL.text, fontWeight: 700, fontSize: "13px" }}>{s.strategy}</div>
            <span style={styles.badge(s.saving === "HIGH" ? STEEL.accent : STEEL.blue)}>
              {s.saving} IMPACT
            </span>
          </div>
          <div style={{ color: STEEL.muted, fontSize: "12px" }}>{s.detail}</div>
        </div>
      ))}

      <div style={styles.divider} />

      <div style={styles.grid2}>
        <div style={styles.infoBox(STEEL.teal)}>
          <div style={styles.infoTitle(STEEL.teal)}>Indicative TCO Breakdown (Year 1 — Mid-Scale)</div>
          <table style={{ ...styles.table, marginBottom: 0 }}>
            <thead>
              <tr>
                <th style={styles.th}>Component</th>
                <th style={styles.th}>Approx. Annual</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["Fabric F128 Capacity (prod)", "$145K–$190K"],
                ["Fabric F8 (dev/test, paused)", "$8K–$12K"],
                ["Databricks Premium (DBUs)", "$120K–$200K"],
                ["ADF (self-hosted IR + pipelines)", "$15K–$30K"],
                ["Azure Storage (OneLake overage)", "$5K–$20K"],
                ["Purview (scan units)", "$10K–$25K"],
                ["Azure OpenAI (tokens)", "$20K–$50K"],
                ["Azure PaaS (IoT Hub, AKV, APIM)", "$15K–$30K"],
              ].map(([c, cost], i) => (
                <tr key={c} style={i % 2 === 1 ? styles.trAlt : {}}>
                  <td style={styles.td}>{c}</td>
                  <td style={{ ...styles.td, color: STEEL.accent, fontWeight: 700 }}>{cost}</td>
                </tr>
              ))}
              <tr style={{ background: "#1c2128" }}>
                <td style={{ ...styles.td, fontWeight: 700, color: STEEL.text }}>TOTAL ESTIMATE</td>
                <td style={{ ...styles.td, color: STEEL.accent, fontWeight: 700, fontSize: "14px" }}>$340K–$560K/yr</td>
              </tr>
            </tbody>
          </table>
          <div style={{ color: STEEL.muted, fontSize: "10px", marginTop: "8px", fontStyle: "italic" }}>
            * Excluding licenses for Power BI Premium and SAP integration. Apply optimization strategies above to reduce by 40%.
          </div>
        </div>
        <div style={styles.infoBox(STEEL.accent)}>
          <div style={styles.infoTitle(STEEL.accent)}>Cost Governance Model</div>
          <ul style={styles.ul}>
            <li><span style={styles.strong}>Fabric Capacity Metrics App</span>: deployed Day 1, reviewed weekly by Platform Team</li>
            <li><span style={styles.strong}>Per-Domain Chargeback</span>: Phase 3 — Fabric workspace CU consumption tagged to domain cost center</li>
            <li><span style={styles.strong}>Databricks Cost Dashboard</span>: cluster tag policy — all clusters tagged with domain, environment, and owner</li>
            <li><span style={styles.strong}>Azure Cost Management</span>: budget alerts at 80% and 100% per subscription</li>
            <li><span style={styles.strong}>Monthly FinOps Review</span>: CDO + Platform Architect + Finance — cost vs. data product value delivered</li>
            <li><span style={styles.strong}>Reserved Capacity</span>: 1-year Fabric capacity reservation for 15–20% discount on committed F-SKU</li>
            <li><span style={styles.strong}>Databricks Committed Use</span>: negotiate DBU commit post-Phase 1 when consumption is predictable</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [tab, setTab] = useState("overview");

  const renderTab = () => {
    switch (tab) {
      case "overview": return <OverviewTab />;
      case "questionnaire": return <QuestionnaireTab />;
      case "architecture": return <ArchitectureTab />;
      case "datamesh": return <DataMeshTab />;
      case "quality": return <QualityTab />;
      case "platforms": return <PlatformsTab />;
      case "governance": return <GovernanceTab />;
      case "roadmap": return <RoadmapTab />;
      case "cost": return <CostTab />;
      default: return null;
    }
  };

  return (
    <div style={styles.root}>
      <div style={styles.header}>
        <div style={styles.headerStripe} />
        <div style={styles.headerEyebrow}>Principal Data Architect — Strategic Blueprint</div>
        <div style={styles.headerTitle}>AI-Optimized Data Architecture for Steel Manufacturing</div>
        <div style={styles.headerSub}>Microsoft Fabric · Azure · Databricks · Data Mesh · DAMA DM-BOK · 6-Pillar Data Quality</div>
        <div style={styles.pillRow}>
          {["Data Mesh", "Medallion Lakehouse", "DAMA DM-BOK v2", "ISO 8000 DQ", "FinOps", "Federated Governance", "SQL Server Migration", "Delta Lake", "Unity Catalog", "OneLake"].map((p) => (
            <div key={p} style={styles.pill}>{p}</div>
          ))}
        </div>
      </div>
      <nav style={styles.nav}>
        {TABS.map((t) => (
          <button key={t.id} style={styles.navTab(tab === t.id)} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      <div style={styles.body}>{renderTab()}</div>
    </div>
  );
}
