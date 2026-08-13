"""DQ Root-Cause agent — deep correlation pass over dq_monitor_rca's failing checks.

Deterministic: for each check failing in the most recent dq_monitor_rca run, finds the
first run_at where it started failing (walking acme_bronze.audit.dq_results history), and
correlates against acme_bronze.audit.batch_log (recent batches for the affected
source/table). LLM pass: turns the correlation into a root-cause note per check — suspected
source, first bad batch, blast radius, suggested fix.

This is a deeper, trend-based companion to dq_monitor_rca.py's per-run investigation, not a
replacement for it — depends on dq_monitor_rca having already populated dq_results (see
resources/agents.yml task ordering). Where the original spec (dq_rca_agent.md) calls for
posting to #data-quality / a steward ticket / a Genie space, this instead notes the
recommended next step in the report for a human to carry out.
"""
import sys
import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

RCA_SYSTEM = """You are the deep DQ root-cause agent for the acme lakehouse. You're given,
per currently-failing check: when it first started failing, and (if available) recent
batch_log rows for the affected table/source. Correlate these: does the failure window line
up with a batch anomaly (volume spike, rejected rows, a failed/errored batch)? Produce a
markdown RCA note per check: suspected source, first bad batch_id (or 'unknown - batch_log
has no matching rows yet, which is expected since the quarantine writer isn't scheduled'),
blast radius (downstream Gold tables consuming this table), and a suggested fix. Note where
a human should post to #data-quality or open a steward ticket — you never do this yourself,
only recommend it. You are READ-ONLY: use run_sql to verify, never to write."""


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log = []

    latest_run = spark.sql(
        "SELECT run_id FROM acme_bronze.audit.dq_results "
        "ORDER BY run_at DESC LIMIT 1").collect()
    if not latest_run:
        print("No dq_results rows yet — dq_monitor_rca hasn't run.")
        log_run(spark, "dq_rca_agent", "deterministic", "NO_DATA", started, log)
        return
    run_id = latest_run[0].run_id

    failing = spark.sql(f"""
        SELECT table_name, dq_dimension, check_name FROM acme_bronze.audit.dq_results
        WHERE run_id = '{run_id}' AND passed = false""").collect()
    log.append(f"latest run {run_id}: {len(failing)} failing check(s)")

    if not failing:
        print("Latest dq_monitor_rca run is fully green — nothing to correlate.")
        log_run(spark, "dq_rca_agent", "deterministic", "GREEN", started, log)
        return

    correlations = []
    for f in failing:
        first_bad = spark.sql(f"""
            SELECT min(run_at) AS ts FROM acme_bronze.audit.dq_results
            WHERE check_name = '{f.check_name}' AND passed = false""").collect()[0].ts
        try:
            batches = spark.sql(f"""
                SELECT batch_id, rows_read, rows_written, rows_rejected, status, started_at
                FROM acme_bronze.audit.batch_log
                WHERE source_name IN (
                    SELECT source_name FROM acme_bronze.cfg.source_registry
                    WHERE target_table = '{f.table_name}')
                ORDER BY started_at DESC LIMIT 5""").collect()
        except Exception as e:
            batches = []
            log.append(f"batch_log correlation failed for {f.check_name}: {str(e)[:120]}")
        correlations.append({
            "check_name": f.check_name, "dimension": f.dq_dimension, "table": f.table_name,
            "first_failed_at": str(first_bad),
            "recent_batches": [dict(b.asDict()) for b in batches] or
                              "no batch_log rows for this source",
        })

    desc = "\n\n".join(
        f"- {c['check_name']} ({c['dimension']}) on {c['table']}: failing since "
        f"{c['first_failed_at']}. Recent batches: {c['recent_batches']}"
        for c in correlations)
    print(f"Correlated failures:\n{desc}")

    report = run_reasoning(
        spark, "dq_rca_agent", RCA_SYSTEM,
        f"Currently-failing checks with history correlation:\n{desc}\n\n"
        "Produce the RCA note per check.", log)
    if not report:
        report = ("# DQ correlation (deterministic only)\n\n" + desc
                  + "\n\nLLM RCA drafting skipped (Anthropic key unavailable - "
                    "see agent_runs log).")

    save_report(spark, "dq_rca_agent", f"DQ RCA (correlated): {len(failing)} check(s)", report)
    print("\n===== RCA REPORT =====\n" + report)

    mode = "llm" if "deterministic only" not in report else "deterministic"
    log_run(spark, "dq_rca_agent", mode, f"CORRELATED_{len(failing)}", started, log)


if __name__ == "__main__":
    main()
