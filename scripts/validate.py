#!/usr/bin/env python3
"""Post-deployment validation — 12 checks, exits non-zero on failure (CI gate)."""
CHECKS = [
 ("Catalogs exist",            "SELECT count(*) FROM system.information_schema.catalogs WHERE catalog_name IN ('nucor_bronze','nucor_silver','nucor_gold','nucor_products')", 4),
 ("Config tables",             "SELECT count(*) FROM nucor_bronze.information_schema.tables WHERE table_schema IN ('cfg','audit')", 5),
 ("Sources registered",        "SELECT count(*) FROM nucor_bronze.cfg.source_registry WHERE active", 6),
 ("Bronze envelope present",   "SELECT count(*) FROM nucor_bronze.information_schema.columns WHERE column_name='_ingest_ts'", ">=6"),
 ("Silver insert-only (no deletes in history)", "SELECT count(*) FROM (DESCRIBE HISTORY nucor_silver.sales.sales_order_header) WHERE operation IN ('DELETE','UPDATE')", 0),
 ("Hash keys 64-char hex",     "SELECT count(*) FROM nucor_silver.sales.sales_order_header WHERE hk NOT RLIKE '^[0-9a-f]{64}$'", 0),
 ("Gold FK integrity",         "SELECT count(*) FROM nucor_gold.sales.fact_sales_orders f LEFT ANTI JOIN nucor_gold.sales.dim_customer d ON f.customer_hk=d.customer_hk WHERE f.customer_hk IS NOT NULL", 0),
 ("Row filter active",         "SELECT count(*) FROM system.information_schema.row_filters WHERE table_name='fact_sales_orders'", 1),
 ("Mask active",               "SELECT count(*) FROM system.information_schema.column_masks WHERE table_name='dim_customer'", 1),
 ("DQ ran in 24h",             "SELECT count(*) FROM nucor_bronze.audit.dq_results WHERE run_at > current_timestamp() - INTERVAL 1 DAY", ">=6"),
 ("Rejects are logged w/ dimension", "SELECT count(*) FROM nucor_bronze.audit.rejected_records WHERE dq_dimension IS NULL", 0),
 ("Products published",        "SELECT count(*) FROM nucor_products.information_schema.views", ">=1"),
]
if __name__ == "__main__":
    import os, json, urllib.request, sys
    wh, host, tok = os.environ["DATABRICKS_WAREHOUSE_ID"], os.environ["DATABRICKS_HOST"], os.environ["DATABRICKS_TOKEN"]
    failed = []
    for name, sql, expect in CHECKS:
        req = urllib.request.Request(f"{host}/api/2.0/sql/statements", method="POST",
            data=json.dumps({"warehouse_id": wh, "statement": sql, "wait_timeout": "30s"}).encode(),
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            val = int(json.loads(urllib.request.urlopen(req).read())["result"]["data_array"][0][0])
            ok = val >= int(str(expect)[2:]) if str(expect).startswith(">=") else val == expect
        except Exception as e:
            ok, val = False, f"ERR {e}"
        print(f"{'PASS' if ok else 'FAIL'}  {name}  (got {val}, want {expect})")
        if not ok: failed.append(name)
    sys.exit(1 if failed else 0)
