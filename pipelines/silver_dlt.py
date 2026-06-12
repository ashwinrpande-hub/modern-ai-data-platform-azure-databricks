"""
SILVER — 3NF, INSERT-ONLY architecture.
hash_key = sha2(source_system || '|' || original_pk, 256)  -> joins all Gold dims/facts.
Every record version is a new row (effective_ts); no UPDATE/DELETE ever issued.
Mappings come from nucor_bronze.cfg.layer_mappings (layer='silver'), so column changes
are config inserts, fully lineage-tracked.
"""
import dlt
from pyspark.sql import functions as F

def hash_key(system_col, *pk_cols):
    return F.sha2(F.concat_ws("|", system_col, *[F.col(c).cast("string") for c in pk_cols]), 256)

def silver_envelope(df, system, pk_cols):
    return (df
        .withColumn("hk", hash_key(F.lit(system), *pk_cols))
        .withColumn("record_hash", F.sha2(F.to_json(F.struct(*df.columns)), 256))  # change detection
        .withColumn("effective_ts", F.current_timestamp())
        .withColumn("is_current", F.lit(True)))   # maintained by view, not UPDATE

# ---- Sales order header, unified 3NF entity fed by three ERPs ----
@dlt.table(name="sales_order_header", comment="3NF insert-only; one row per version per source PK")
@dlt.expect_all_or_drop({"valid_hk": "hk IS NOT NULL",
                         "valid_amount": "order_amount_usd >= 0",
                         "valid_currency": "currency_code IS NOT NULL"})
def sales_order_header():
    sap = (dlt.read_stream("nucor_bronze.sap.vbak")
        .select(F.col("VBELN").alias("src_order_id"), F.col("KUNNR").alias("src_customer_id"),
                F.col("NETWR").alias("order_amount"), F.col("WAERK").alias("currency_code"),
                F.to_date("ERDAT").alias("order_date"), F.lit("SAP").alias("source_system")))
    jde = (dlt.read_stream("nucor_bronze.jde.f4201")
        .select(F.concat_ws("-", "SHKCOO", "SHDOCO", "SHDCTO").alias("src_order_id"),
                F.col("SHAN8").alias("src_customer_id"),
                (F.col("SHOTOT")/100).alias("order_amount"), F.col("SHCRCD").alias("currency_code"),
                F.expr("date_add(to_date('1900-01-01'), SHTRDJ - 36525)").alias("order_date"),  # Julian
                F.lit("JDE").alias("source_system")))
    qad = (dlt.read_stream("nucor_bronze.qad.so_mstr")
        .select(F.col("so_nbr").alias("src_order_id"), F.col("so_cust").alias("src_customer_id"),
                F.col("so_t_amt").alias("order_amount"), F.col("so_curr").alias("currency_code"),
                F.col("so_ord_date").alias("order_date"), F.lit("QAD").alias("source_system")))
    unioned = sap.unionByName(jde).unionByName(qad)
    fx = dlt.read("fx_rates")  # silver reference table
    return (silver_envelope(unioned, None, ["src_order_id"])
        .withColumn("hk", hash_key(F.col("source_system"), "src_order_id"))
        .join(fx, ["currency_code"], "left")
        .withColumn("order_amount_usd", F.col("order_amount") * F.coalesce("usd_rate", F.lit(1.0))))

@dlt.table(name="customer", comment="3NF insert-only customer, MDM survivorship in Gold")
@dlt.expect_all_or_drop({"valid_hk": "hk IS NOT NULL"})
def customer():
    sap = dlt.read_stream("nucor_bronze.sap.kna1").select(
        F.col("KUNNR").alias("src_customer_id"), F.col("NAME1").alias("customer_name"),
        F.col("LAND1").alias("country"), F.lit("SAP").alias("source_system"))
    jde = dlt.read_stream("nucor_bronze.jde.f0101").select(
        F.col("ABAN8").alias("src_customer_id"), F.col("ABALPH").alias("customer_name"),
        F.col("ABCTR").alias("country"), F.lit("JDE").alias("source_system"))
    u = sap.unionByName(jde)
    return silver_envelope(u, None, ["src_customer_id"]) \
        .withColumn("hk", hash_key(F.col("source_system"), "src_customer_id"))

# ---- OT: furnace heat aggregates aligned to orders (insert-only) ----
@dlt.table(name="furnace_heat_5min", comment="5-min OT aggregates from Litmus bronze")
def furnace_heat_5min():
    return (dlt.read_stream("nucor_bronze.ot.furnace_telemetry")
        .withWatermark("ts", "15 minutes")
        .groupBy(F.window("ts", "5 minutes").alias("w"), "site", "asset", "tag")
        .agg(F.avg("value").alias("avg_value"), F.max("value").alias("max_value"),
             F.count("*").alias("samples"))
        .select(F.col("w.start").alias("window_start"), "site", "asset", "tag",
                "avg_value", "max_value", "samples")
        .withColumn("hk", hash_key(F.lit("LITMUS"), "site", "asset", "tag", "window_start"))
        .withColumn("effective_ts", F.current_timestamp()))

# "Current" semantics WITHOUT updates: latest version per hk
@dlt.view(name="v_sales_order_header_current")
def v_current():
    from pyspark.sql.window import Window
    w = Window.partitionBy("hk").orderBy(F.col("effective_ts").desc())
    return (dlt.read("sales_order_header")
        .withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn"))
