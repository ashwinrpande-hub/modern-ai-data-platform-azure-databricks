"""Customer features: PIT-correct offline table + LOW-LATENCY ONLINE serving (gap B4).
Online path uses a Lakebase-synced table — Lakebase (managed Postgres) is GA on Azure
(Mar 2026) with autoscaling, HA, and scale-to-zero; it replaces legacy Online Tables
as the recommended low-latency feature-serving store."""
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from databricks.sdk import WorkspaceClient
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

OFFLINE = "nucor_gold.ml.customer_features"
if not spark.catalog.tableExists(OFFLINE):
    fe.create_table(name=OFFLINE, primary_keys=["customer_hk"], timestamp_keys=["feature_ts"],
                    df=features, description="Sales customer features; versioned by feature_ts")
else:
    fe.write_table(name=OFFLINE, df=features, mode="merge")   # append new feature versions

# ---- ONLINE: sync to Lakebase for ms-latency lookups (model serving + apps) ----
w = WorkspaceClient()
try:
    w.database.create_synced_database_table({
        "name": "nucor_gold.ml.customer_features_online",
        "spec": {"source_table_full_name": OFFLINE,
                 "primary_key_columns": ["customer_hk"],
                 "timeseries_key": "feature_ts",
                 "scheduling_policy": "TRIGGERED",         # refresh with this job
                 "database_instance_name": "nucor-lakebase",
                 "logical_database_name": "features"}})
except Exception as e:      # already exists -> triggered refresh happens automatically
    print(f"synced table: {e}")

# Training set (PIT join prevents leakage):
# fe.create_training_set(df=labels, feature_lookups=[FeatureLookup(
#     table_name=OFFLINE, lookup_key="customer_hk", timestamp_lookup_key="label_ts")],
#     label="churned")
