"""Ingestion Registrar agent — validates config/replication_sources.yaml.

Deterministic: parses every source row and checks pattern is in the allowed set,
primary_key is present, expectations parses as a map, region is a known value, and target
follows the <catalog>.<schema>.<table> naming convention. Cross-checks each source against
acme_bronze.cfg.source_registry to flag which ones are declared in the YAML but not yet
registered (candidates for `scripts/deploy.py --register-source <name>`).

Originally spec'd (ingestion_registrar.md) as PR-triggered, commenting a validation report
directly on the PR and calling deploy.py on merge; this runs the same validation as an
on-demand scan instead, since no GitHub integration exists yet. LLM pass turns the results
into a readable onboarding summary. Never calls deploy.py or writes to source_registry
itself — registration stays a human action.
"""
import sys
import os
import yaml
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(globals().get("__file__") or sys.argv[0]))
sys.path.insert(0, _HERE)
from agent_core import ensure_audit_tables, get_spark, log_run, run_reasoning, save_report

ALLOWED_PATTERNS = {
    "goldengate", "lakeflow_sqlserver", "lakeflow_query", "lakeflow_d365",
    "litmus_adls", "litmus_eventhub", "zerobus", "autoloader_file",
}
ALLOWED_REGIONS = {"EUROPE", "AMERICAS", "EMEA", "GLOBAL"}
YAML_PATH = os.path.abspath(os.path.join(_HERE, "..", "config", "replication_sources.yaml"))

REGISTRAR_SYSTEM = """You are the ingestion-registrar agent for the acme lakehouse. You're
given the validation results for every source row in config/replication_sources.yaml, plus
which ones are missing from acme_bronze.cfg.source_registry. Write a short markdown
onboarding summary: sources with validation issues (what to fix before merge), and sources
that pass validation but aren't registered yet (the exact `scripts/deploy.py
--register-source <name>` command to run for each, one at a time). You never run deploy.py
yourself — a human runs it after reviewing."""


def validate_source(src):
    issues = []
    if src.get("pattern") not in ALLOWED_PATTERNS:
        issues.append(f"pattern '{src.get('pattern')}' not in allowed set")
    if not src.get("primary_key"):
        issues.append("no primary_key")
    if not isinstance(src.get("expectations", {}), dict):
        issues.append("expectations block does not parse as a map")
    if src.get("region") not in ALLOWED_REGIONS:
        issues.append(f"region '{src.get('region')}' not in {sorted(ALLOWED_REGIONS)}")
    target = src.get("target", "")
    if target.count(".") != 2:
        issues.append(f"target '{target}' doesn't follow <catalog>.<schema>.<table>")
    return issues


def main():
    started = datetime.now(timezone.utc)
    spark = get_spark()
    ensure_audit_tables(spark)
    log = []

    try:
        with open(YAML_PATH, "r", encoding="utf-8-sig") as fh:
            cfg = yaml.safe_load(fh)
    except Exception as e:
        log.append(f"could not read {YAML_PATH}: {str(e)[:200]}")
        log_run(spark, "ingestion_registrar", "deterministic", "YAML_UNREADABLE", started, log)
        print(f"ERROR: {log[-1]}")
        return

    sources = cfg.get("sources", [])
    registered = {
        r.source_name for r in spark.sql(
            "SELECT source_name FROM acme_bronze.cfg.source_registry").collect()}

    results = []
    for src in sources:
        issues = validate_source(src)
        results.append({
            "name": src.get("name"), "pattern": src.get("pattern"),
            "issues": issues, "registered": src.get("name") in registered,
        })
    log.append(f"{len(sources)} source(s) in YAML, "
               f"{sum(1 for r in results if r['issues'])} with validation issues, "
               f"{sum(1 for r in results if not r['registered'])} unregistered")

    desc = "\n".join(
        f"- {r['name']} ({r['pattern']}): "
        f"{'OK' if not r['issues'] else 'ISSUES: ' + '; '.join(r['issues'])}, "
        f"{'registered' if r['registered'] else 'NOT REGISTERED'}"
        for r in results)
    print(f"Ingestion estate validation:\n{desc}")

    report = run_reasoning(
        spark, "ingestion_registrar", REGISTRAR_SYSTEM,
        f"Validation results for {len(sources)} source(s):\n{desc}\n\n"
        "Write the onboarding summary.", log)
    if not report:
        report = ("# Ingestion estate validation (deterministic only)\n\n" + desc
                  + "\n\nLLM summary skipped (Anthropic key unavailable - see agent_runs log).")

    save_report(spark, "ingestion_registrar",
               f"Ingestion validation: {len(sources)} source(s)", report)
    print("\n===== REGISTRAR REPORT =====\n" + report)

    mode = "llm" if "deterministic only" not in report else "deterministic"
    any_issues = any(r["issues"] for r in results)
    log_run(spark, "ingestion_registrar", mode,
           "ISSUES_FOUND" if any_issues else "ALL_VALID", started, log)


if __name__ == "__main__":
    main()
