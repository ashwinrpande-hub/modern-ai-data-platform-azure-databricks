"""Lineage & Docs agent — companion to the hand-maintained docs/CODE_GRAPH.md.

Deterministic: builds a bronze->silver lineage edge list from the live
acme_bronze.cfg.layer_mappings rows (the real, current config — not hand-typed), and
attempts to read silver/gold-side lineage from the system.access.table_lineage system
table (degrades gracefully if that schema isn't enabled on this metastore). LLM pass turns
the edges into a mermaid diagram + short prose.

Originally spec'd (lineage_doc_agent.md) as a nightly job that regenerates
docs/CODE_GRAPH.md directly. This agent does NOT write to the git-tracked docs/ folder —
a file written from inside a Databricks job container is ephemeral compute state, not a
commit, so it would never actually reach the repo. Instead, like every other agent here,
its output goes to acme_bronze.audit.agent_reports; a human copies the useful parts into
docs/CODE_GRAPH.md (or a new file) via a normal commit.
"""
import sys
import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

LINEAGE_SYSTEM = """You are the lineage-documentation agent for the acme lakehouse. You're
given the current bronze->silver mapping edges (from acme_bronze.cfg.layer_mappings, the
live config) and, if available, silver/gold-side lineage edges captured natively by Unity
Catalog. Produce: a mermaid flowchart of the edges, and one short paragraph per target
table describing what feeds it. This is a factual restatement of the edges you were given —
do not invent tables or edges that weren't in the input."""


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log = []

    mapping_edges = spark.sql("""
        SELECT DISTINCT src_table, tgt_table FROM acme_bronze.cfg.layer_mappings
        WHERE valid_to IS NULL AND layer = 'silver'
        ORDER BY src_table""").collect()
    edges = [(r.src_table, r.tgt_table) for r in mapping_edges]
    log.append(f"{len(edges)} bronze->silver edge(s) from cfg.layer_mappings")

    uc_edges = []
    try:
        uc_edges = [(r.source_table_full_name, r.target_table_full_name) for r in spark.sql("""
            SELECT DISTINCT source_table_full_name, target_table_full_name
            FROM system.access.table_lineage
            WHERE target_table_full_name LIKE 'acme_gold.%'
              AND event_date >= current_date() - INTERVAL 30 DAYS""").collect()]
        log.append(f"{len(uc_edges)} silver->gold edge(s) from system.access.table_lineage")
    except Exception as e:
        log.append(f"system.access.table_lineage unavailable: {str(e)[:150]} "
                   "(system tables schema may not be enabled on this metastore)")

    all_edges = edges + uc_edges
    if not all_edges:
        print("No lineage edges available from either source.")
        log_run(spark, "lineage_doc_agent", "deterministic", "NO_EDGES", started, log)
        return

    edges_desc = "\n".join(f"- {s} -> {t}" for s, t in all_edges)
    print(f"Lineage edges:\n{edges_desc}")

    report = run_reasoning(
        spark, "lineage_doc_agent", LINEAGE_SYSTEM,
        f"Lineage edges:\n{edges_desc}\n\nProduce the mermaid diagram + per-table prose.", log)
    if not report:
        report = ("# Lineage edges (deterministic only)\n\n```mermaid\nflowchart LR\n"
                  + "\n".join(f'  "{s}" --> "{t}"' for s, t in all_edges)
                  + "\n```\n\nLLM narrative skipped (Anthropic key unavailable - "
                    "see agent_runs log).")

    save_report(spark, "lineage_doc_agent", f"Lineage: {len(all_edges)} edge(s)", report)
    print("\n===== LINEAGE REPORT =====\n" + report)

    mode = "llm" if "deterministic only" not in report else "deterministic"
    log_run(spark, "lineage_doc_agent", mode, f"EDGES_{len(all_edges)}", started, log)


if __name__ == "__main__":
    main()
