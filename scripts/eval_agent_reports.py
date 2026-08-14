"""Agent reliability scorecard.

Scores how often each agent's independent verification pass (agent_core.verify_report)
found every claim in its report backed by the evidence log, vs found gaps, vs never ran
(deterministic mode, no Anthropic key). Reads acme_bronze.audit.agent_runs.decision_log,
which carries a "verification: ..." line per LLM-mode run since agent_core.run_reasoning
started appending one.

Deterministic only -- no LLM involved in scoring, so the eval itself can't hallucinate
about how well the agents are doing. Run on demand; not wired into a schedule, same as
validate.py is run on demand rather than continuously.
"""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, os.path.join(_HERE, "..", "agents"))
from agent_core import get_spark

LOOKBACK_DAYS = 30


def main():
    spark = get_spark()
    rows = spark.sql(f"""
        SELECT agent,
               count(*) AS runs,
               count_if(decision_log LIKE '%verification: All claims verified%') AS clean,
               count_if(decision_log LIKE '%verification:%'
                        AND decision_log NOT LIKE '%verification: All claims verified%'
                        AND decision_log NOT LIKE '%verification: No run_sql evidence%'
                        AND decision_log NOT LIKE '%Verification pass failed to run%') AS flagged,
               count_if(decision_log LIKE '%Verification pass failed to run%') AS verify_errored,
               count_if(decision_log NOT LIKE '%verification:%') AS no_llm_pass
        FROM acme_bronze.audit.agent_runs
        WHERE started_at > current_timestamp() - INTERVAL {LOOKBACK_DAYS} DAYS
        GROUP BY agent ORDER BY agent
    """).collect()

    if not rows:
        print(f"No agent_runs in the last {LOOKBACK_DAYS} days.")
        return

    print(f"Agent reliability scorecard -- last {LOOKBACK_DAYS} days\n")
    print(f"{'agent':<20}{'runs':>6}{'clean':>7}{'flagged':>9}{'verify_err':>12}{'no_llm':>8}")
    total_clean = total_checked = 0
    for r in rows:
        print(f"{r.agent:<20}{r.runs:>6}{r.clean:>7}{r.flagged:>9}{r.verify_errored:>12}{r.no_llm_pass:>8}")
        total_clean += r.clean
        total_checked += r.clean + r.flagged

    if total_checked:
        pct = round(100 * total_clean / total_checked, 1)
        print(f"\nOverall: {total_clean}/{total_checked} verified runs had every claim "
              f"backed by evidence ({pct}%). 'no_llm' runs (deterministic mode, or "
              "verification found nothing to check against) are excluded from that rate.")
    else:
        print("\nNo runs with a completed verification pass in this window.")

    flagged_rows = [r for r in rows if r.flagged > 0]
    if flagged_rows:
        print("\nAgents with at least one flagged (unsupported-claim) run -- inspect their "
              "agent_reports for the 'Independent verification' section:")
        for r in flagged_rows:
            print(f"  - {r.agent}: {r.flagged} flagged run(s)")


if __name__ == "__main__":
    main()
