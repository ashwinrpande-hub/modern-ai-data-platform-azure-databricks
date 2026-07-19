"""Operational Intelligence agent — owns platform-wide observability.

Deterministic: gathers the daily metric set (layer row counts, ingest freshness,
fulfillment backlog and its value, top accounts, today's DQ failures). LLM pass:
composes the daily operations digest — anomalies called out, plain-language, for
domain leads. Deterministic fallback emits the same metrics as a plain-text digest.
"""
import sys
import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

METRIC_SQL = {
    "bronze_order_rows": "SELECT count(*) FROM acme_bronze.sap.vbak",
    "silver_order_versions": "SELECT count(*) FROM acme_silver.sales.sales_order_header",
    "gold_fact_rows": "SELECT count(*) FROM acme_gold.sales.fact_sales_orders",
    "bronze_ingest_age_hours":
        "SELECT cast((unix_timestamp(current_timestamp()) - unix_timestamp(max(_ingest_ts))) / 3600 AS INT) "
        "FROM acme_bronze.sap.vbak",
    "backlog_orders":
        "SELECT count(*) FROM acme_gold.sales.bridge_order_fulfillment WHERE NOT is_shipped",
    "backlog_value_usd":
        "SELECT cast(coalesce(sum(f.order_amount_usd), 0) AS BIGINT) "
        "FROM acme_gold.sales.bridge_order_fulfillment b "
        "JOIN acme_gold.sales.fact_sales_orders f ON f.order_hk = b.order_hk WHERE NOT b.is_shipped",
    "shipped_not_invoiced":
        "SELECT count(*) FROM acme_gold.sales.bridge_order_fulfillment WHERE is_shipped AND NOT is_invoiced",
    "dq_failures_today":
        "SELECT count(*) FROM acme_bronze.audit.dq_results "
        "WHERE NOT passed AND run_at > current_timestamp() - INTERVAL 24 HOURS",
}

DIGEST_SYSTEM = """You are the operational-intelligence agent for the acme sales lakehouse.
You receive today's platform metrics and may use run_sql (read-only) to drill into anything
that looks anomalous (e.g. top customers behind the backlog value, which DQ checks failed).
Write the daily operations digest in markdown for domain leads: 3-6 bullet headline section
first (biggest numbers + anything unusual), then short sections for pipeline health,
fulfillment backlog, and data quality. Plain business language, units on every number,
no invented figures — every number must come from the metrics given or your own queries."""


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log, metrics = [], {}

    for key, sql in METRIC_SQL.items():
        try:
            metrics[key] = spark.sql(sql).collect()[0][0]
        except Exception as e:
            metrics[key] = f"ERR {str(e)[:80]}"
        print(f"{key}: {metrics[key]}")
    log.append("metrics gathered: " + ", ".join(f"{k}={v}" for k, v in metrics.items()))

    top = spark.sql("""
        SELECT d.customer_name, cast(sum(f.order_amount_usd) AS BIGINT) AS revenue_usd
        FROM acme_gold.sales.fact_sales_orders f
        JOIN acme_gold.sales.dim_customer d ON d.customer_hk = f.customer_hk
        GROUP BY d.customer_name ORDER BY revenue_usd DESC LIMIT 5""").collect()
    top_desc = "\n".join(f"  {r.customer_name}: ${r.revenue_usd:,}" for r in top)

    metric_desc = "\n".join(f"- {k}: {v}" for k, v in metrics.items())
    report = run_reasoning(
        spark, "operational_intel", DIGEST_SYSTEM,
        f"Today's metrics:\n{metric_desc}\n\nTop 5 customers by revenue:\n{top_desc}\n\n"
        "Compose the daily digest.", log)
    if not report:
        report = (f"# Daily operations digest (deterministic)\n\n{metric_desc}\n\n"
                  f"Top 5 customers by revenue:\n{top_desc}\n\n"
                  "LLM narrative skipped (no API key configured).")
    save_report(spark, "operational_intel", f"Daily digest {started.date()}", report)
    print("\n===== DIGEST =====\n" + report)

    mode = "llm" if "deterministic)" not in report.splitlines()[0] else "deterministic"
    log_run(spark, "operational_intel", mode, "DIGEST_SENT", started, log)


if __name__ == "__main__":
    main()
