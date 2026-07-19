"""Schema Evolution agent — owns the cfg.layer_mappings contract with Bronze.

Deterministic: diffs each mapped Bronze table's actual columns (information_schema)
against the columns cfg.layer_mappings consumes; unmapped, non-envelope columns are
schema drift. LLM pass: drafts versioned mapping-row INSERT proposals for the drift —
as a report for human review, never executed (config changes go through PRs).
"""
import sys
import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

PROPOSAL_SYSTEM = """You are the schema-evolution agent for the acme lakehouse.
cfg.layer_mappings schema: (mapping_id, layer, src_table, src_column, tgt_table, tgt_column,
transform_expr, dq_rule, version, valid_from, valid_to, changed_by). Adding a column to
Silver = INSERT a new mapping row (version 1 for a new tgt_column) — no code change.
You may use run_sql (read-only) to inspect existing mappings and sample the drifted columns.
For each unmapped column, propose: the Silver target table/column it should map to, any
transform_expr, a dq_rule if sensible, and the exact INSERT statement — formatted as a
markdown proposal a human can review and apply via PR. If a column looks intentionally
unmapped (technical/noise), say so instead of forcing a mapping. You never execute writes."""


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log = []

    mapped = spark.sql("""
        SELECT DISTINCT src_table, src_column FROM acme_bronze.cfg.layer_mappings
        WHERE valid_to IS NULL AND src_column IS NOT NULL""").collect()
    by_table = {}
    for r in mapped:
        by_table.setdefault(r.src_table, set()).add(r.src_column)

    drift = {}
    for src_table, mapped_cols in sorted(by_table.items()):
        catalog, schema, table = src_table.split(".")
        actual = {
            r.column_name
            for r in spark.sql(
                f"SELECT column_name FROM {catalog}.information_schema.columns "
                f"WHERE table_schema = '{schema}' AND table_name = '{table}'").collect()
        }
        unmapped = sorted(c for c in actual - mapped_cols if not c.startswith("_"))
        if unmapped:
            drift[src_table] = unmapped
        log.append(f"{src_table}: {len(actual)} cols, {len(unmapped)} unmapped")

    if not drift:
        print("No schema drift: every non-envelope Bronze column is mapped.")
        log_run(spark, "schema_evolution", "deterministic", "NO_DRIFT", started, log)
        return

    drift_desc = "\n".join(f"- {t}: {', '.join(cols)}" for t, cols in drift.items())
    print(f"Schema drift detected:\n{drift_desc}")

    report = run_reasoning(
        spark, "schema_evolution", PROPOSAL_SYSTEM,
        f"These Bronze columns exist but are not consumed by any active mapping:\n{drift_desc}\n\n"
        "Inspect the data, then draft the versioned mapping-row INSERT proposals.", log)
    if not report:
        report = ("# Schema drift (deterministic scan)\n\nUnmapped non-envelope Bronze columns:\n\n"
                  + drift_desc
                  + "\n\nLLM proposal drafting skipped (no API key configured). "
                    "Add mapping rows to config/seed_layer_mappings.sql via PR.")
    save_report(spark, "schema_evolution", f"Schema drift: {sum(len(v) for v in drift.values())} unmapped column(s)", report)
    print("\n===== PROPOSAL =====\n" + report)

    mode = "llm" if "deterministic scan" not in report else "deterministic"
    log_run(spark, "schema_evolution", mode, "DRIFT_REPORTED", started, log)


if __name__ == "__main__":
    main()
