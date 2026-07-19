"""DQ Monitor + RCA agent — owns Bronze→Silver gates and the audit schema.

Deterministic: runs 10 DAMA-dimension checks across Bronze/Silver/Gold and writes one
row per check to acme_bronze.audit.dq_results (this is what validate.py check 10 reads).
LLM pass: investigates any failing check with read-only SQL — first bad batch, blast
radius through lineage — and files a structured RCA report.
"""
import sys
import os
import uuid
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

# (check_name, dama_dimension, table, sql) — each SQL returns a single BIGINT of violations
CHECKS = [
    ("order_keys_not_null", "completeness", "acme_silver.sales.sales_order_header",
     "SELECT count(*) FROM acme_silver.sales.sales_order_header WHERE src_order_id IS NULL OR source_system IS NULL"),
    ("customer_name_not_null", "completeness", "acme_gold.sales.dim_customer",
     "SELECT count(*) FROM acme_gold.sales.dim_customer WHERE customer_name IS NULL"),
    ("hash_key_64_hex", "validity", "acme_silver.sales.sales_order_header",
     "SELECT count(*) FROM acme_silver.sales.sales_order_header WHERE hk NOT RLIKE '^[0-9a-f]{64}$'"),
    ("currency_in_fx_reference", "validity", "acme_silver.sales.sales_order_header",
     "SELECT count(*) FROM acme_silver.sales.v_sales_order_header_current c "
     "LEFT ANTI JOIN acme_silver.ref.fx_rates f ON c.currency_code = f.currency_code"),
    ("no_duplicate_current_orders", "uniqueness", "acme_silver.sales.v_sales_order_header_current",
     "SELECT count(*) FROM (SELECT source_system, src_order_id, count(*) c "
     "FROM acme_silver.sales.v_sales_order_header_current GROUP BY 1, 2 HAVING c > 1)"),
    ("fact_customer_fk_resolves", "consistency", "acme_gold.sales.fact_sales_orders",
     "SELECT count(*) FROM acme_gold.sales.fact_sales_orders f "
     "LEFT ANTI JOIN acme_gold.sales.dim_customer d ON f.customer_hk = d.customer_hk "
     "WHERE f.customer_hk IS NOT NULL"),
    ("silver_gold_row_parity", "consistency", "acme_gold.sales.fact_sales_orders",
     "SELECT abs((SELECT count(*) FROM acme_silver.sales.v_sales_order_header_current) - "
     "(SELECT count(*) FROM acme_gold.sales.fact_sales_orders))"),
    ("usd_amount_reconciles", "accuracy", "acme_gold.sales.fact_sales_orders",
     "SELECT CASE WHEN abs((SELECT sum(order_amount_usd) FROM acme_silver.sales.v_sales_order_header_current) - "
     "(SELECT sum(order_amount_usd) FROM acme_gold.sales.fact_sales_orders)) > 0.01 THEN 1 ELSE 0 END"),
    ("bronze_ingest_fresh_24h", "timeliness", "acme_bronze.sap.vbak",
     "SELECT CASE WHEN max(_ingest_ts) < current_timestamp() - INTERVAL 24 HOURS THEN 1 ELSE 0 END "
     "FROM acme_bronze.sap.vbak"),
    ("orders_arriving_30d", "timeliness", "acme_gold.sales.fact_sales_orders",
     "SELECT CASE WHEN max(order_date) < current_date() - INTERVAL 30 DAYS THEN 1 ELSE 0 END "
     "FROM acme_gold.sales.fact_sales_orders"),
]

RCA_SYSTEM = """You are the DQ root-cause-analysis agent for the acme sales lakehouse
(Azure Databricks, medallion: acme_bronze -> acme_silver.sales -> acme_gold.sales).
Bronze rows carry envelope columns _source_system, _ingest_ts, _batch_id, _op_type, _seq.
Silver is insert-only with hk = sha2(source_system|pk) and effective_ts versions.
You are READ-ONLY: investigate with the run_sql tool; never propose executing writes.
For each failing check: (1) verify the failure yourself, (2) find the earliest evidence
(batch, date, source system), (3) state blast radius (which downstream tables consume it),
(4) classify root cause (source data vs pipeline logic vs staleness) with your confidence.
Finish with a markdown RCA report: one section per failing check, then a prioritized
remediation list. Recommendations only — a human owns every change."""


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log, results, run_id = [], [], str(uuid.uuid4())

    for name, dim, table, sql in CHECKS:
        try:
            violations = int(spark.sql(sql).collect()[0][0] or 0)
        except Exception as e:
            violations = -1
            log.append(f"check {name} errored: {str(e)[:150]}")
        passed = violations == 0
        results.append((name, dim, table, passed, violations))
        spark.sql(
            "INSERT INTO acme_bronze.audit.dq_results VALUES "
            f"('{run_id}', current_timestamp(), '{table}', '{dim}', '{name}', {str(passed).lower()}, {violations})")
        print(f"{'PASS' if passed else 'FAIL'}  [{dim:<12}] {name} (violations={violations})")

    failures = [r for r in results if not r[3]]
    log.append(f"{len(CHECKS)} checks run, {len(failures)} failing")

    report = None
    if failures:
        failing_desc = "\n".join(
            f"- {n} ({d}) on {t}: {v} violations" for n, d, t, _p, v in failures)
        report = run_reasoning(
            spark, "dq_monitor_rca", RCA_SYSTEM,
            f"DQ run {run_id} finished with {len(failures)} failing check(s):\n{failing_desc}\n\n"
            "Investigate each failure and produce the RCA report.", log)
    if report:
        save_report(spark, "dq_monitor_rca", f"DQ RCA — {len(failures)} failing check(s)", report)
        print("\n===== RCA REPORT =====\n" + report)

    mode = "llm" if report else "deterministic"
    status = "GREEN" if not failures else ("RCA_FILED" if report else "FAILURES_NO_RCA")
    log_run(spark, "dq_monitor_rca", mode, status, started, log)
    print(f"\ndq_monitor_rca finished: mode={mode}, status={status}")


if __name__ == "__main__":
    main()
