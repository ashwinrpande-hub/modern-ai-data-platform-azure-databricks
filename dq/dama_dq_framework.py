"""
DAMA 6-dimension DQ framework. Rules live in acme_bronze.cfg.layer_mappings.dq_rule
tagged with a dimension. Run as a Lakeflow Job after each Silver/Gold refresh.
Dimensions: COMPLETENESS, ACCURACY, CONSISTENCY, VALIDITY, UNIQUENESS, TIMELINESS.
Outputs: acme_bronze.audit.dq_results (scores) + rejected_records (row-level).
"""
from pyspark.sql import SparkSession, functions as F
import uuid, datetime

spark = SparkSession.builder.getOrCreate()

RULES = [  # (table, dimension, rule_sql, threshold)
    ("acme_silver.sales.sales_order_header", "COMPLETENESS", "src_customer_id IS NOT NULL", 0.99),
    ("acme_silver.sales.sales_order_header", "VALIDITY",     "order_amount_usd BETWEEN 0 AND 50000000", 0.999),
    ("acme_silver.sales.sales_order_header", "UNIQUENESS",   None, 0.999),   # dup hk+effective_ts
    ("acme_silver.sales.sales_order_header", "TIMELINESS",   "effective_ts >= current_timestamp() - INTERVAL 1 DAY", 0.95),
    ("acme_silver.sales.customer",           "CONSISTENCY",  "country RLIKE '^[A-Z]{2}$'", 0.98),
    ("acme_gold.sales.fact_sales_orders",    "ACCURACY",     "customer_hk IS NOT NULL", 0.99),
]

def run():
    batch = str(uuid.uuid4()); results = []
    for table, dim, rule, threshold in RULES:
        df = spark.table(table)
        total = df.count()
        if dim == "UNIQUENESS":
            passed = df.select("hk", "effective_ts").distinct().count()
        else:
            passed = df.filter(rule).count()
            # row-level quarantine of failures
            (df.filter(f"NOT ({rule})").limit(10000)
               .select(F.lit(str(uuid.uuid4())).alias("reject_id"), F.lit(batch).alias("batch_id"),
                       F.lit(table).alias("source_name"), F.lit(table).alias("target_table"),
                       F.lit("silver").alias("layer"), F.lit(rule).alias("failed_rule"),
                       F.lit(dim).alias("dq_dimension"),
                       F.to_json(F.struct("*")).alias("record_payload"),
                       F.current_timestamp().alias("rejected_at"))
               .write.mode("append").saveAsTable("acme_bronze.audit.rejected_records"))
        score = passed / total if total else 1.0
        results.append((batch, table, dim, rule or "distinct(hk,effective_ts)",
                        total, passed, round(score, 5), score >= threshold,
                        datetime.datetime.utcnow()))
    spark.createDataFrame(results,
        "batch_id string, table_name string, dimension string, rule string, total long, "
        "passed long, score double, met_threshold boolean, run_at timestamp"
    ).write.mode("append").saveAsTable("acme_bronze.audit.dq_results")
    # fail the job if any critical dimension breached -> triggers healer agent
    breaches = [r for r in results if not r[7]]
    if breaches:
        raise Exception(f"DQ thresholds breached: {[(b[1], b[2]) for b in breaches]}")

if __name__ == "__main__":
    run()

