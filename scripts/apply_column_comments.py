#!/usr/bin/env python3
"""Applies column-level business definitions as Unity Catalog column comments.

Source of truth is acme_bronze.cfg.layer_mappings.business_definition (config table, not
code — CLAUDE.md rule: config tables > YAML > code defaults). Multiple source systems can
each contribute a definition for the same Silver tgt_column (e.g. SAP's and JDE's differing
notes on order_amount); since UC allows one comment per column, distinct definitions are
concatenated in a deterministic order rather than picking one arbitrarily.

Run after config/seed_layer_mappings.sql has been applied (scripts/deploy.py step 3) and
after silver_pipeline has created the tables at least once.

Usage:
  python scripts/apply_column_comments.py           # apply
  python scripts/apply_column_comments.py --dry-run # print the ALTER statements only
"""
import argparse

SEP = "  ||  "


def get_spark():
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception:
        from databricks.connect import DatabricksSession
        return DatabricksSession.builder.serverless(True).getOrCreate()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                    help="print ALTER statements without executing them")
    args = p.parse_args()

    spark = get_spark()
    rows = spark.sql(f"""
        SELECT tgt_table, tgt_column,
               concat_ws('{SEP}', sort_array(collect_set(business_definition))) AS definition
        FROM acme_bronze.cfg.layer_mappings
        WHERE valid_to IS NULL AND tgt_column IS NOT NULL AND business_definition IS NOT NULL
        GROUP BY tgt_table, tgt_column
        ORDER BY tgt_table, tgt_column""").collect()

    if not rows:
        print("No business_definition values found in cfg.layer_mappings — nothing to apply. "
              "Did you run config/seed_layer_mappings.sql?")
        return

    applied, failed = 0, 0
    for r in rows:
        full_table = f"acme_silver.sales.{r.tgt_table}"
        comment = r.definition.replace("'", "''")
        stmt = f"ALTER TABLE {full_table} ALTER COLUMN {r.tgt_column} COMMENT '{comment}'"
        if args.dry_run:
            print(f"[dry-run] {stmt}")
            continue
        try:
            spark.sql(stmt)
            print(f"[applied] {full_table}.{r.tgt_column}")
            applied += 1
        except Exception as e:
            print(f"[FAILED]  {full_table}.{r.tgt_column}: {str(e)[:200]}")
            failed += 1

    if not args.dry_run:
        print(f"\n{applied} column comment(s) applied, {failed} failed "
              f"(failures usually mean the table/column doesn't exist yet — "
              f"run silver_pipeline first).")


if __name__ == "__main__":
    main()
