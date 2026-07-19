"""Data Product Creator agent — owns the Gold → acme_products output ports.

Takes a natural-language product request (job parameter), generates a secure view over
Gold, validates it against a strict allowlist (CREATE OR REPLACE VIEW in acme_products
only, reading acme_gold only), executes it, and registers the product in the catalog.
Deterministic fallback ships a hand-written order-to-cash view so the port always exists.
"""
import re
import sys
import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

DEFAULT_REQUEST = ("Order-to-cash data product: current orders with customer name, country, "
                   "USD amounts, and shipped/invoiced lifecycle status, for BI consumption.")

FALLBACK_SQL = """
CREATE OR REPLACE VIEW acme_products.sales.v_sales_orders_unified AS
SELECT f.order_hk, d.customer_name, d.country, f.source_system,
       f.order_date, f.order_amount_usd, f.currency_code,
       b.ship_date, b.invoice_date, b.is_shipped, b.is_invoiced
FROM acme_gold.sales.fact_sales_orders f
LEFT JOIN acme_gold.sales.dim_customer d ON f.customer_hk = d.customer_hk
LEFT JOIN acme_gold.sales.bridge_order_fulfillment b ON f.order_hk = b.order_hk
"""

CREATOR_SYSTEM = """You are the data-product-creator agent for the acme lakehouse.
Available Gold tables (catalog acme_gold, schema sales): fact_sales_orders(order_hk,
customer_hk, source_system, order_date, order_amount_usd, currency_code), dim_customer(
customer_hk, src_customer_id, customer_name, country, source_system), bridge_order_fulfillment(
order_hk, customer_hk, shipment_hk, invoice_hk, source_system, order_date, ship_date,
invoice_date, is_shipped, is_invoiced), agg_sales_daily(order_date, source_system,
revenue_usd, orders), pit_customer(snapshot_date, customer_hk, as_of_ts, source_system).
Use run_sql (read-only) to verify columns/joins before finalizing.
Respond with EXACTLY ONE statement inside a ```sql fence, of the form:
CREATE OR REPLACE VIEW acme_products.sales.<snake_case_name> AS SELECT ...
Rules: read only acme_gold.sales tables; no semicolons; no DML/DDL other than that one
CREATE OR REPLACE VIEW; expose no hash keys except order_hk as an opaque id.
After the fence, add one short paragraph describing the product contract."""

VIEW_RE = re.compile(r"^CREATE OR REPLACE VIEW acme_products\.sales\.[a-z0-9_]+\s+AS\s+SELECT\b",
                     re.IGNORECASE | re.DOTALL)
FORBIDDEN = re.compile(r"\b(DROP|DELETE|INSERT|UPDATE|MERGE|GRANT|REVOKE|ALTER|TRUNCATE)\b", re.IGNORECASE)


def extract_sql(report):
    m = re.search(r"```sql\s*(.*?)```", report, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    sql = m.group(1).strip().rstrip(";").strip()
    if ";" in sql or not VIEW_RE.match(sql) or FORBIDDEN.search(sql):
        return None
    if re.search(r"\bacme_(bronze|silver)\b", sql, re.IGNORECASE):
        return None
    return sql


def main():
    started = datetime.now(timezone.utc)
    request = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REQUEST
    spark = get_spark()
    ensure_audit_tables(spark)
    spark.sql("""
        CREATE TABLE IF NOT EXISTS acme_bronze.cfg.product_registry (
          product_name STRING, view_name STRING, request STRING,
          created_by STRING, created_at TIMESTAMP)""")
    log = [f"request: {request[:200]}"]

    report = run_reasoning(
        spark, "product_creator", CREATOR_SYSTEM,
        f"Product request: {request}\n\nVerify the schema you need, then produce the view.", log)

    sql, mode = (None, "deterministic")
    if report:
        sql = extract_sql(report)
        mode = "llm" if sql else "llm_rejected"
        if not sql:
            log.append("LLM output failed validation gate — falling back to hand-written view")
    if not sql:
        sql, report = FALLBACK_SQL.strip(), (report or "Deterministic fallback product (no API key).")

    view_name = re.search(r"acme_products\.sales\.([a-z0-9_]+)", sql, re.IGNORECASE).group(1)
    spark.sql(sql)
    rows = spark.sql(f"SELECT count(*) FROM acme_products.sales.{view_name}").collect()[0][0]
    log.append(f"created acme_products.sales.{view_name} ({rows} rows)")
    print(f"Created acme_products.sales.{view_name} — {rows} rows")

    spark.sql(
        "INSERT INTO acme_bronze.cfg.product_registry VALUES "
        f"('{view_name}', 'acme_products.sales.{view_name}', "
        f"'{request.replace(chr(39), chr(39) * 2)[:500]}', 'product_creator_agent', current_timestamp())")
    save_report(spark, "product_creator", f"Data product created: {view_name}",
                f"Request: {request}\n\n```sql\n{sql}\n```\n\n{report}")
    log_run(spark, "product_creator", mode, "PRODUCT_CREATED", started, log)
    print(f"product_creator finished: mode={mode}")


if __name__ == "__main__":
    main()
