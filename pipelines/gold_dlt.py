"""GOLD — consumption-optimized. Dims & facts connect via Silver SHA-256 hash keys."""
import dlt
from pyspark.sql import functions as F

@dlt.table(name="dim_customer",
           comment="MDM-survived customer dim; PK = customer_hk",
           table_properties={"delta.enableChangeDataFeed": "true"})
def dim_customer():
    c = dlt.read("acme_silver.sales.customer")
    # survivorship: prefer SAP > JDE > QAD on name conflicts (latest version per hk)
    from pyspark.sql.window import Window
    w = Window.partitionBy("hk").orderBy(F.col("effective_ts").desc())
    return (c.withColumn("rn", F.row_number().over(w)).filter("rn=1")
             .select(F.col("hk").alias("customer_hk"), "src_customer_id",
                     "customer_name", "country", "source_system"))

@dlt.table(name="fact_sales_orders",
           comment="Grain: one row per order per source; FKs are hash keys",
           cluster_by=["order_date", "customer_hk"])           # liquid clustering
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

