"""Customer feature tables with point-in-time correctness (Databricks Feature Engineering in UC)."""
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()
fe = FeatureEngineeringClient()

features = (spark.table("nucor_gold.sales.fact_sales_orders")
    .groupBy("customer_hk")
    .agg(F.sum("order_amount_usd").alias("ltv_usd"),
         F.countDistinct("order_hk").alias("order_count_365d"),
         F.max("order_date").alias("last_order_date"))
    .withColumn("days_since_last_order", F.datediff(F.current_date(), "last_order_date"))
    .withColumn("feature_ts", F.current_timestamp()))   # timeseries key -> PIT joins

fe.create_table(
    name="nucor_gold.ml.customer_features",
    primary_keys=["customer_hk"],
    timestamp_keys=["feature_ts"],          # point-in-time correctness
    df=features,
    description="Sales customer features; versioned by feature_ts; served via Online Tables")

# Training set example (PIT join prevents leakage):
# fe.create_training_set(df=labels, feature_lookups=[FeatureLookup(
#     table_name="nucor_gold.ml.customer_features", lookup_key="customer_hk",
#     timestamp_lookup_key="label_ts")], label="churned")
# Low-latency serving: publish as Lakebase-synced Online Feature Store table.
