"""GOLD — consumption-optimized. Dims & facts connect via Silver SHA-256 hash keys."""
import dlt
from pyspark.sql import functions as F

@dlt.table(name="dim_customer",
           comment="Customer dim; PK = customer_hk (one row per source-system record, latest "
                   "SCD version). customer_key_mdm is a deterministic cross-source "
                   "entity-resolution key (normalized name + country) — the join point for "
                   "the same real-world customer appearing under different source_system IDs. "
                   "On this repo's independently-generated synthetic data, SAP/JDE/QAD "
                   "customers don't model overlapping real entities, so customer_key_mdm "
                   "rarely collapses rows today; the mechanism is real and is where a "
                   "production fuzzy-match step (Zingg/Splink) would plug in for near-"
                   "duplicates this exact-match misses.",
           table_properties={"delta.enableChangeDataFeed": "true"},
           # Governance is declared here, not via ALTER: DLT-materialized tables reject
           # ALTER TABLE SET ROW FILTER / SET MASK (they are views to the ALTER path).
           # Functions live in acme_gold.sec (security/unity_catalog_policies.sql).
           schema="""customer_hk STRING COMMENT 'Silver hash key: sha2(source_system|src_customer_id). Stable per-source FK grain used by fact_sales_orders — never changes when the MDM match logic changes.',
                     customer_key_mdm STRING COMMENT 'Deterministic cross-source entity-resolution key: sha2(normalized_name|country). Equal across source systems only when name and country match exactly after normalization (case, punctuation, common corporate suffixes stripped).',
                     src_customer_id STRING COMMENT 'Customer ID as recorded in the source ERP (SAP KUNNR / JDE ABAN8 / QAD so_cust).',
                     customer_name STRING COMMENT 'Customer legal/short name from the source ERP, pre-match (not yet resolved across sources).' MASK acme_gold.sec.mask_customer_name,
                     country STRING COMMENT 'ISO-2 country code of the customer address, as recorded by the source ERP.',
                     source_system STRING COMMENT 'Which ERP this record came from: SAP, JDE, or QAD.'""",
           row_filter="ROW FILTER acme_gold.sec.region_filter ON (source_system)")
def dim_customer():
    from pyspark.sql.window import Window
    c = dlt.read("acme_silver.sales.customer")
    # collapse Silver's Type-2 versions to the current row per source-system record
    w = Window.partitionBy("hk").orderBy(F.col("effective_ts").desc())
    latest = c.withColumn("rn", F.row_number().over(w)).filter("rn=1")

    # Entity resolution: exact match on a normalized (name, country) key. This is the
    # deterministic tier — real duplicates that differ by more than casing/punctuation/a
    # corporate suffix (typos, abbreviations, transliteration) won't collapse here; that's
    # the gap a probabilistic matcher (Zingg/Splink) fills in production.
    norm_name = F.upper(F.trim(F.col("customer_name")))
    norm_name = F.regexp_replace(norm_name, r"[.,]", "")
    norm_name = F.regexp_replace(norm_name, r"\s+(INC|LLC|LTD|CORP|CO|GMBH|AG|SA)\.?$", "")
    norm_name = F.trim(F.regexp_replace(norm_name, r"\s+", " "))
    norm_country = F.upper(F.trim(F.col("country")))

    return (latest
            .withColumn("customer_key_mdm",
                        F.sha2(F.concat_ws("|", norm_name, norm_country), 256))
            .select(F.col("hk").alias("customer_hk"), "customer_key_mdm", "src_customer_id",
                    "customer_name", "country", "source_system"))

@dlt.table(name="fact_sales_orders",
           comment="Grain: one row per order per source; FKs are hash keys",
           cluster_by=["order_date", "customer_hk"],           # liquid clustering
           row_filter="ROW FILTER acme_gold.sec.region_filter ON (source_system)")
@dlt.expect_all({"fk_customer": "customer_hk IS NOT NULL"})
def fact_sales_orders():
    soh = dlt.read("acme_silver.sales.v_sales_order_header_current")
    cust = dlt.read("dim_customer").select("customer_hk", "src_customer_id", "source_system")
    return (soh.alias("o")
        .join(cust.alias("c"),
              (F.col("o.src_customer_id") == F.col("c.src_customer_id")) &
              (F.col("o.source_system") == F.col("c.source_system")), "left")
        .select(F.col("o.hk").alias("order_hk"), F.col("c.customer_hk"),
                "o.source_system", "o.order_date", "o.order_amount_usd", "o.currency_code"))

@dlt.table(name="fact_heat_quality", cluster_by=["window_start"],
           comment="OT-to-business: furnace conditions joined to daily shipped tonnage")
def fact_heat_quality():
    ot = dlt.read("acme_silver.sales.furnace_heat_5min")
    return ot.select(F.col("hk").alias("heat_hk"), "site", "asset", "tag",
                     "window_start", "avg_value", "max_value")

# ---- DV2.0 query-assistance tables (docs/DATA_VAULT_PIT_BRIDGE.md) ----
@dlt.table(name="pit_customer", cluster_by=["snapshot_date"],
           comment="DV2.0 PIT: (snapshot_date, customer_hk) -> as_of_ts of the Silver version "
                   "current that day. Equality as-of joins; no BETWEEN scans, no label leakage.")
def pit_customer():
    c = (dlt.read("acme_silver.sales.customer")
           .select(F.col("hk").alias("customer_hk"), "effective_ts", "source_system")
           .withColumn("eff_date", F.to_date("effective_ts")))
    spine = (c.agg(F.min("eff_date").alias("lo"))
               .select(F.explode(F.sequence(F.col("lo"), F.current_date())).alias("snapshot_date")))
    # demo-scale recompute; at scale switch to incremental append of the new day only
    return (c.join(spine, c["eff_date"] <= spine["snapshot_date"])
             .groupBy("snapshot_date", "customer_hk")
             .agg(F.max("effective_ts").alias("as_of_ts"),
                  F.max_by("source_system", "effective_ts").alias("source_system")))

@dlt.table(name="bridge_order_fulfillment", cluster_by=["order_date"],
           comment="DV2.0 bridge: order->shipment->invoice hash keys + lifecycle dates/flags. "
                   "Grain: one row per current order. One join for O2C, backlog, Genie.")
@dlt.expect_all({"fk_order": "order_hk IS NOT NULL"})
def bridge_order_fulfillment():
    o = dlt.read("acme_silver.sales.v_sales_order_header_current").select(
        F.col("hk").alias("order_hk"), "src_order_id", "src_customer_id",
        "source_system", "order_date")
    s = (dlt.read("acme_silver.sales.v_shipment_current")
         .groupBy("src_order_id", "source_system")
         .agg(F.min("ship_date").alias("ship_date"),
              F.min_by("hk", "ship_date").alias("shipment_hk")))        # first shipment
    i = (dlt.read("acme_silver.sales.v_invoice_current")
         .groupBy("src_order_id", "source_system")
         .agg(F.min("invoice_date").alias("invoice_date"),
              F.min_by("hk", "invoice_date").alias("invoice_hk")))      # first invoice
    cust = dlt.read("dim_customer").select("customer_hk", "src_customer_id", "source_system")
    return (o.join(s, ["src_order_id", "source_system"], "left")
             .join(i, ["src_order_id", "source_system"], "left")
             .join(cust, ["src_customer_id", "source_system"], "left")
             .withColumn("is_shipped", F.col("shipment_hk").isNotNull())
             .withColumn("is_invoiced", F.col("invoice_hk").isNotNull())
             .select("order_hk", "customer_hk", "shipment_hk", "invoice_hk", "source_system",
                     "order_date", "ship_date", "invoice_date", "is_shipped", "is_invoiced"))

# Materialized aggregate for BI (Genie / dashboards hit this, not the fact)
@dlt.table(name="agg_sales_daily", comment="Pre-aggregated for AI/BI dashboards + Genie")
def agg_sales_daily():
    f = dlt.read("fact_sales_orders")
    return (f.groupBy("order_date", "source_system")
             .agg(F.sum("order_amount_usd").alias("revenue_usd"),
                  F.countDistinct("order_hk").alias("orders")))

