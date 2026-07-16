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

# Materialized aggregate for BI (Genie / dashboards hit this, not the fact)
@dlt.table(name="agg_sales_daily", comment="Pre-aggregated for AI/BI dashboards + Genie")
def agg_sales_daily():
    f = dlt.read("fact_sales_orders")
    return (f.groupBy("order_date", "source_system")
             .agg(F.sum("order_amount_usd").alias("revenue_usd"),
                  F.countDistinct("order_hk").alias("orders")))

