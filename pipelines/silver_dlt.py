"""
SILVER — 3NF, INSERT-ONLY. hk = sha2(source_system|pk, 256); versions via effective_ts.
NOW ACTUALLY CONFIG-DRIVEN (gap A1): column mappings are read from
acme_bronze.cfg.layer_mappings (layer='silver', latest version, valid_to IS NULL) at
pipeline-graph build time. Adding/changing a column = INSERT a new mapping version
(see config/seed_layer_mappings.sql) + pipeline refresh — no code edit, lineage kept.
Note: Lakeflow Spark Declarative Pipelines is converging on `from pyspark import
pipelines as dp`; `import dlt` remains supported — swap the alias when your runtime does.
"""
import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def hash_key(system_col, *pk_cols):
    return F.sha2(F.concat_ws("|", system_col, *[F.col(c).cast("string") for c in pk_cols]), 256)

def load_mappings(tgt_table):
    """[(src_table, [(tgt_col, sql_expr)])] from config; deterministic column order."""
    rows = (spark.table("acme_bronze.cfg.layer_mappings")
        .filter((F.col("layer") == "silver") & (F.col("tgt_table") == tgt_table)
                & F.col("valid_to").isNull())
        .withColumn("rn", F.row_number().over(
            Window.partitionBy("src_table", "tgt_column").orderBy(F.col("version").desc())))
        .filter("rn = 1").collect())
    by_src = {}
    for r in rows:
        expr = r.transform_expr if r.transform_expr else r.src_column
        by_src.setdefault(r.src_table, []).append((r.tgt_column, expr))
    return sorted((s, sorted(cols)) for s, cols in by_src.items())

def silver_envelope(df, pk_cols):
    return (df
        .withColumn("hk", hash_key(F.col("source_system"), *pk_cols))
        .withColumn("record_hash", F.sha2(F.to_json(F.struct(*df.columns)), 256))
        .withColumn("effective_ts", F.current_timestamp()))

def unioned_entity(tgt_table):
    dfs = []
    for src_table, cols in load_mappings(tgt_table):
        df = dlt.read_stream(src_table).selectExpr(
            *[f"{expr} AS {tgt}" for tgt, expr in cols])
        dfs.append(df)
    out = dfs[0]
    for d in dfs[1:]:
        out = out.unionByName(d, allowMissingColumns=True)
    return out

@dlt.table(name="sales_order_header", comment="3NF insert-only; config-driven from cfg.layer_mappings")
@dlt.expect_all_or_drop({"valid_hk": "hk IS NOT NULL",
                         "valid_amount": "order_amount_usd >= 0",
                         "valid_currency": "currency_code IS NOT NULL"})
def sales_order_header():
    u = unioned_entity("sales_order_header")
    fx = dlt.read("fx_rates")
    return (silver_envelope(u, ["src_order_id"])
        .join(fx, ["currency_code"], "left")
        .withColumn("order_amount_usd", F.col("order_amount") * F.coalesce("usd_rate", F.lit(1.0))))

@dlt.table(name="customer", comment="3NF insert-only customer; config-driven; MDM survivorship in Gold")
@dlt.expect_all_or_drop({"valid_hk": "hk IS NOT NULL"})
def customer():
    return silver_envelope(unioned_entity("customer"), ["src_customer_id"])

@dlt.table(name="fx_rates", comment="Reference: seeded by config/seed_layer_mappings.sql")
def fx_rates():
    return spark.table("acme_silver.sales.fx_rates")

# ---- OT: 5-min furnace aggregates (structural, stays code — no column mapping semantics) ----
@dlt.table(name="furnace_heat_5min", comment="5-min OT aggregates from Litmus bronze")
def furnace_heat_5min():
    return (dlt.read_stream("acme_bronze.ot.furnace_telemetry")
        .withWatermark("ts", "15 minutes")
        .groupBy(F.window("ts", "5 minutes").alias("w"), "site", "asset", "tag")
        .agg(F.avg("value").alias("avg_value"), F.max("value").alias("max_value"),
             F.count("*").alias("samples"))
        .select(F.col("w.start").alias("window_start"), "site", "asset", "tag",
                "avg_value", "max_value", "samples")
        .withColumn("hk", F.sha2(F.concat_ws("|", F.lit("LITMUS"), "site", "asset", "tag",
                                             F.col("window_start").cast("string")), 256))
        .withColumn("effective_ts", F.current_timestamp()))

# "Current" WITHOUT updates: latest version per hk
@dlt.view(name="v_sales_order_header_current")
def v_current():
    w = Window.partitionBy("hk").orderBy(F.col("effective_ts").desc())
    return (dlt.read("sales_order_header")
        .withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn"))

