"""Deployment Gate agent — owns CI/CD verification.

Deterministic: executes the same 14 checks as scripts/validate.py (imported, not
duplicated) directly through Spark SQL. LLM pass: reads the results, separates
regressions from known/tracked gaps, and issues a promote / hold recommendation.
The job itself never hard-fails on known gaps — the human reads the recommendation.
"""
import sys
import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..")))
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report
from scripts.validate import CHECKS

GATE_SYSTEM = """You are the deployment-gate agent for the acme lakehouse CI pipeline.
You receive the results of the 14-check validation suite. As of 2026-07-19 there are NO
open known gaps: UC row filters/masks are applied via the gold pipeline definition, and
validate.py baselines were refreshed (config tables >=9, sources = 14). Treat every
failing check as a candidate regression and investigate it with run_sql (read-only)
before judging. Output: a markdown gate report — table of results, per-failure diagnosis,
and a final PROMOTE or HOLD recommendation with one-line justification. A human merges."""


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log, results = [], []

    for name, sql, expect in CHECKS:
        try:
            val = spark.sql(sql).collect()[0][0]
            val = int(val) if val is not None else 0
            ok = val >= int(str(expect)[2:]) if str(expect).startswith(">=") else val == expect
        except Exception as e:
            ok, val = False, f"ERR {str(e)[:120]}"
        results.append((name, ok, val, expect))
        print(f"{'PASS' if ok else 'FAIL'}  {name} (got {val}, want {expect})")

    passed = sum(1 for _, ok, _, _ in results if ok)
    log.append(f"validate suite: {passed}/{len(results)} passing")
    result_desc = "\n".join(
        f"- {'PASS' if ok else 'FAIL'}: {n} (got {v}, want {e})" for n, ok, v, e in results)

    report = run_reasoning(
        spark, "deployment_gate", GATE_SYSTEM,
        f"Validation suite results ({passed}/{len(results)} passing):\n{result_desc}\n\n"
        "Classify failures and issue the gate recommendation.", log)
    if not report:
        report = (f"# Deployment gate (deterministic)\n\n{passed}/{len(results)} checks passing.\n\n"
                  + result_desc
                  + "\n\nLLM classification skipped (Anthropic key unavailable - see agent_runs log).")
    save_report(spark, "deployment_gate", f"Gate: {passed}/{len(results)} checks green", report)
    print("\n===== GATE REPORT =====\n" + report)

    mode = "llm" if "deterministic)" not in report.splitlines()[0] else "deterministic"
    log_run(spark, "deployment_gate", mode,
            "ALL_GREEN" if passed == len(results) else f"DEGRADED_{passed}_OF_{len(results)}",
            started, log)


if __name__ == "__main__":
    main()
