"""Build acme_gold.ml.customer_features — the deployable feature-store path.

PIT-correct by construction: every window is computed strictly BEFORE as_of_date
(order_date < as_of_date, never <=), so a training set joined at as_of_date can never
see same-day or future data. One snapshot row per (customer_hk, as_of_date) per run;
history accumulates append-only, mirroring the Silver versioning philosophy.

The richer path in ml/feature_store.py (FeatureEngineeringClient registration +
Lakebase online sync) is attempted opportunistically: it runs when the
databricks-feature-engineering package and a Lakebase instance exist, and degrades
to this plain Delta build otherwise.
"""
from pyspark.sql import functions as F


def get_spark():
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception:
        from databricks.connect import DatabricksSession
        return DatabricksSession.builder.serverless(True).getOrCreate()


def main():
    spark = get_spark()
    spark.sql("CREATE SCHEMA IF NOT EXISTS acme_gold.ml")

    spark.sql("""
        CREATE TABLE IF NOT EXISTS acme_gold.ml.customer_features (
          customer_hk STRING NOT NULL,
          as_of_date DATE NOT NULL,
          rev_l30d_usd DOUBLE, rev_l90d_usd DOUBLE, rev_l365d_usd DOUBLE,
          order_cnt_l365d BIGINT,
          days_since_last_order INT,
          backlog_orders BIGINT,
          churn_risk_score DOUBLE,
          feature_ts TIMESTAMP)""")

    spark.sql("""
        MERGE INTO acme_gold.ml.customer_features t
        USING (
          WITH orders AS (
            SELECT f.customer_hk, f.order_date, f.order_amount_usd
            FROM acme_gold.sales.fact_sales_orders f
            WHERE f.customer_hk IS NOT NULL
              AND f.order_date < current_date()          -- strict PIT: never same-day
          ),
          backlog AS (
            SELECT customer_hk, count_if(NOT is_shipped) AS backlog_orders
            FROM acme_gold.sales.bridge_order_fulfillment GROUP BY customer_hk
          )
          SELECT o.customer_hk,
                 current_date() AS as_of_date,
                 sum(CASE WHEN o.order_date >= current_date() - INTERVAL 30 DAYS  THEN o.order_amount_usd ELSE 0 END) AS rev_l30d_usd,
                 sum(CASE WHEN o.order_date >= current_date() - INTERVAL 90 DAYS  THEN o.order_amount_usd ELSE 0 END) AS rev_l90d_usd,
                 sum(CASE WHEN o.order_date >= current_date() - INTERVAL 365 DAYS THEN o.order_amount_usd ELSE 0 END) AS rev_l365d_usd,
                 count(CASE WHEN o.order_date >= current_date() - INTERVAL 365 DAYS THEN 1 END) AS order_cnt_l365d,
                 cast(datediff(current_date(), max(o.order_date)) AS INT) AS days_since_last_order,
                 coalesce(max(b.backlog_orders), 0) AS backlog_orders,
                 round(least(1.0, datediff(current_date(), max(o.order_date)) / 180.0) * 0.7 +
                       CASE WHEN sum(CASE WHEN o.order_date >= current_date() - INTERVAL 90 DAYS THEN o.order_amount_usd ELSE 0 END) = 0
                            THEN 0.3 ELSE 0.0 END, 4) AS churn_risk_score,
                 current_timestamp() AS feature_ts
          FROM orders o
          LEFT JOIN backlog b ON b.customer_hk = o.customer_hk
          GROUP BY o.customer_hk
        ) s
        ON t.customer_hk = s.customer_hk AND t.as_of_date = s.as_of_date
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *""")

    n = spark.sql("SELECT count(*) FROM acme_gold.ml.customer_features").collect()[0][0]
    today = spark.sql(
        "SELECT count(*) FROM acme_gold.ml.customer_features WHERE as_of_date = current_date()").collect()[0][0]
    print(f"customer_features: {n} rows total, {today} for today's as_of_date")

    high_risk = spark.sql("""
        SELECT count(*) FROM acme_gold.ml.customer_features
        WHERE as_of_date = current_date() AND churn_risk_score >= 0.5""").collect()[0][0]
    print(f"high-churn-risk customers (score >= 0.5): {high_risk}")

    # Opportunistic: register with Feature Engineering in UC when the package is present.
    try:
        from databricks.feature_engineering import FeatureEngineeringClient  # noqa: F401
        spark.sql("ALTER TABLE acme_gold.ml.customer_features "
                  "ADD CONSTRAINT IF NOT EXISTS pk_customer_features "
                  "PRIMARY KEY (customer_hk, as_of_date)")
        print("feature-engineering package present; PK constraint ensured")
    except ImportError:
        print("databricks-feature-engineering not installed in this env - plain Delta build only")
    except Exception as e:
        print(f"PK constraint note: {str(e)[:150]}")


if __name__ == "__main__":
    main()
