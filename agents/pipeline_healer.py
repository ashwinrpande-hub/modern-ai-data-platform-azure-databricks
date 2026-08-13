"""Pipeline Healer agent — Lakeflow pipeline failure triage.

Deterministic: scans recent DLT pipeline updates (acme_silver_pipeline, acme_gold_pipeline,
plus anything active in cfg.pipeline_registry) via the Databricks SDK for FAILED updates in
the lookback window, and classifies each with a keyword heuristic (schema drift | bad
records | infra | code). LLM pass: verifies the classification with read-only SQL and
drafts the specific remediation per failure type. No pipeline is ever restarted and no PR
is opened here — every recommendation is written into the report for a human to act on.

Originally spec'd (pipeline_healer.md) as webhook-triggered off a job-failure event; this
runs the same triage as a scheduled scan instead, since no webhook receiver exists yet.
"""
import sys
import os
from datetime import datetime, timezone, timedelta

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

LOOKBACK_HOURS = 24
KNOWN_PIPELINES = ["acme_silver_pipeline", "acme_gold_pipeline"]  # resources/pipelines.yml

CLASSIFY_RULES = [
    ("schema drift", ("schema", "cannot resolve", "column", "cast", "delta_schema")),
    ("bad records", ("expectation", "check constraint", "reject", "constraint")),
    ("infra", ("outofmemory", "spot", "job aborted", "executor", "timeout")),
]


def classify(message):
    text = (message or "").lower()
    for label, keywords in CLASSIFY_RULES:
        if any(k in text for k in keywords):
            return label
    return "code"


HEAL_SYSTEM = """You are the pipeline-healer agent for the acme lakehouse.
For each failed pipeline update below, you're given a heuristic classification (schema
drift | bad records | infra | code) and the raw error text. Verify the classification with
read-only SQL where useful (e.g. check acme_bronze.cfg.layer_mappings for schema drift,
acme_bronze.audit.rejected_records for bad records), then write the specific fix:
- schema drift: the exact layer_mappings INSERT to add the missing column mapping.
- bad records: which rows/rule is failing and whether the pipeline should continue past it.
- infra: recommend a retry with the fallback cluster policy (on-demand, +1 node size), max 2 retries.
- code: describe the bug and sketch the fix as if writing a PR description.
You never execute anything — a human applies every fix via PR or config change. Output a
markdown report, one section per failure, plus a one-line severity/priority per item."""


def scan_pipeline_failures(spark, log):
    failures = []
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

        registry_names = []
        try:
            registry_names = [r.pipeline_name for r in spark.sql(
                "SELECT pipeline_name FROM acme_bronze.cfg.pipeline_registry "
                "WHERE active = true").collect()]
        except Exception as e:
            log.append(f"pipeline_registry read failed (table may not exist yet): {str(e)[:120]}")

        watch = set(KNOWN_PIPELINES) | set(registry_names)
        scanned = 0
        for p in w.pipelines.list_pipelines():
            if p.name not in watch:
                continue
            scanned += 1
            try:
                detail = w.pipelines.get(pipeline_id=p.pipeline_id)
                for u in (detail.latest_updates or [])[:5]:
                    if str(u.state) != "FAILED":
                        continue
                    if u.creation_time and datetime.fromtimestamp(
                            u.creation_time / 1000, tz=timezone.utc) < cutoff:
                        continue
                    events = w.pipelines.list_pipeline_events(
                        pipeline_id=p.pipeline_id, max_results=10)
                    error_text = " | ".join(
                        e.message for e in events if getattr(e, "level", None) == "ERROR")[:1500]
                    failures.append({
                        "pipeline": p.name, "update_id": u.update_id,
                        "error": error_text or "(no ERROR-level event text captured)",
                    })
            except Exception as e:
                log.append(f"pipeline {p.name} inspection failed: {str(e)[:150]}")
        log.append(f"scanned {scanned} known pipeline(s), {len(failures)} FAILED "
                   f"update(s) in last {LOOKBACK_HOURS}h")
    except Exception as e:
        log.append(f"Databricks SDK pipeline scan unavailable: {str(e)[:200]}")
    return failures


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log = []

    failures = scan_pipeline_failures(spark, log)

    if not failures:
        print(f"No failed pipeline updates found in the last {LOOKBACK_HOURS}h "
              "(or SDK scan was unavailable — see log).")
        log_run(spark, "pipeline_healer", "deterministic", "NO_FAILURES", started, log)
        return

    for f in failures:
        f["classification"] = classify(f["error"])
    failing_desc = "\n".join(
        f"- {f['pipeline']} (update {f['update_id']}, classified as {f['classification']}): "
        f"{f['error'][:300]}" for f in failures)
    print(f"Pipeline failures found:\n{failing_desc}")

    report = run_reasoning(
        spark, "pipeline_healer", HEAL_SYSTEM,
        f"{len(failures)} failed pipeline update(s) in the last {LOOKBACK_HOURS}h:\n"
        f"{failing_desc}\n\nVerify each and write the remediation report.", log)
    if not report:
        report = ("# Pipeline failures (deterministic classification only)\n\n" + failing_desc
                  + "\n\nLLM remediation drafting skipped (Anthropic key unavailable - "
                    "see agent_runs log).")

    save_report(spark, "pipeline_healer", f"Pipeline healer: {len(failures)} failure(s)", report)
    print("\n===== HEALER REPORT =====\n" + report)

    mode = "llm" if "deterministic classification only" not in report else "deterministic"
    log_run(spark, "pipeline_healer", mode, f"FAILURES_{len(failures)}", started, log)


if __name__ == "__main__":
    main()
