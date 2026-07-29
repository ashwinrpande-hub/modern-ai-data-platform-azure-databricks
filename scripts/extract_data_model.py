#!/usr/bin/env python3
"""Discover the full table/column inventory across acme_bronze/silver/gold/products
directly from the live Unity Catalog metastore, pull row counts + a 500-row sample
per table, and dump the live bronze->silver lineage config tables. Writes everything
needed by build_excel_exports.py and generate_data_docs.py to data/exports/_extraction/.

Needs: DATABRICKS_CONFIG_PROFILE + DATABRICKS_CLI_PATH set, databricks-connect installed.
"""
import json, os, time
from databricks.connect import DatabricksSession

OUT_DIR = os.path.join("data", "exports", "_extraction")
CATALOGS = ["acme_bronze", "acme_silver", "acme_gold", "acme_products"]


def is_internal(name):
    return name.startswith("__") or name.startswith("event_log_")


def main():
    os.makedirs(os.path.join(OUT_DIR, "samples"), exist_ok=True)
    spark = DatabricksSession.builder.serverless(True).getOrCreate()
    in_list = ",".join(f"'{c}'" for c in CATALOGS)

    tables = [r.asDict() for r in spark.sql(f"""
        SELECT table_catalog, table_schema, table_name, table_type, comment
        FROM system.information_schema.tables
        WHERE table_catalog IN ({in_list}) AND table_schema NOT IN ('information_schema')
        ORDER BY table_catalog, table_schema, table_name""").collect()]

    cols = [r.asDict() for r in spark.sql(f"""
        SELECT table_catalog, table_schema, table_name, column_name, ordinal_position,
               data_type, is_nullable, comment
        FROM system.information_schema.columns
        WHERE table_catalog IN ({in_list})
        ORDER BY table_catalog, table_schema, table_name, ordinal_position""").collect()]

    from collections import defaultdict
    col_map = defaultdict(list)
    for c in cols:
        col_map[(c["table_catalog"], c["table_schema"], c["table_name"])].append(c)

    business_tables = [t for t in tables if not is_internal(t["table_name"])]
    print(f"Business tables: {len(business_tables)} (of {len(tables)} total incl. DLT internals)")

    t0 = time.time()
    for i, t in enumerate(business_tables):
        t["columns"] = col_map.get((t["table_catalog"], t["table_schema"], t["table_name"]), [])
        fq = f"{t['table_catalog']}.{t['table_schema']}.{t['table_name']}"
        try:
            t["row_count"] = spark.sql(f"SELECT count(*) c FROM {fq}").collect()[0]["c"]
        except Exception as e:
            t["row_count"], t["count_error"] = None, str(e)[:200]
        try:
            pdf = spark.sql(f"SELECT * FROM {fq} LIMIT 500").toPandas()
            csv_path = os.path.join(OUT_DIR, "samples", f"{t['table_catalog']}__{t['table_schema']}__{t['table_name']}.csv")
            pdf.to_csv(csv_path, index=False)
            t["sample_rows"], t["sample_csv"] = len(pdf), csv_path
        except Exception as e:
            t["sample_rows"], t["sample_error"] = 0, str(e)[:200]
        print(f"[{i+1}/{len(business_tables)}] {fq}  rows={t['row_count']}  sampled={t.get('sample_rows')}  ({time.time()-t0:.0f}s)")

    layer_mappings = [r.asDict() for r in spark.sql(
        "SELECT * FROM acme_bronze.cfg.layer_mappings ORDER BY tgt_table, src_table, tgt_column").collect()]
    source_registry = [r.asDict() for r in spark.sql(
        "SELECT * FROM acme_bronze.cfg.source_registry ORDER BY system, source_name").collect()]
    product_registry = [r.asDict() for r in spark.sql(
        "SELECT * FROM acme_bronze.cfg.product_registry").collect()]

    out_path = os.path.join(OUT_DIR, "extraction_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "tables": business_tables,
            "layer_mappings": layer_mappings,
            "source_registry": source_registry,
            "product_registry": product_registry,
        }, f, default=str, indent=2)
    print(f"\nDone in {time.time()-t0:.0f}s. Wrote {out_path}")


if __name__ == "__main__":
    main()
