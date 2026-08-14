"""Shared core for the acme platform agents.

Every agent follows the same contract:
  1. Deterministic work runs first (checks, table builds, drift scans) — always executes,
     with or without an LLM available. The platform never depends on a model being up.
  2. If an Anthropic API key is available (env ANTHROPIC_API_KEY or Databricks secret
     agents/anthropic_api_key), a Claude reasoning pass runs on top with ONE tool:
     run_sql, hard-guarded to read-only statements. Without a key the agent logs
     "deterministic mode" and still produces its artifact.

Guardrails (deliberate, and load-bearing for the design):
  - The model's only action surface is read-only SQL. All writes (dq_results, reports,
    tables, views) happen in deterministic framework code after validation.
  - Every tool call and result summary is appended to a decision log persisted in
    acme_bronze.audit.agent_runs — agents are auditable like any pipeline.
  - Every report is independently fact-checked before it's saved: a second, separate
    Claude call (verify_report) checks each claim in the draft against the evidence log
    from the first pass, and the report a human actually reads carries both the raw
    evidence log and that verdict inline — see docs/AGENT_RELIABILITY_GUARDRAILS.md.
"""
import json
import os
import uuid
from datetime import datetime, timezone

MODEL = "claude-opus-4-8"
MAX_STEPS = 12
READONLY_PREFIXES = ("SELECT", "WITH", "SHOW", "DESCRIBE", "DESC ")


def get_spark():
    # On a Databricks job the session already exists; locally fall back to
    # databricks-connect serverless (used for dev runs of the same scripts).
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception:
        from databricks.connect import DatabricksSession
        return DatabricksSession.builder.serverless(True).getOrCreate()


def ensure_audit_tables(spark):
    spark.sql("""
        CREATE TABLE IF NOT EXISTS acme_bronze.audit.agent_runs (
          run_id STRING, agent STRING, mode STRING, status STRING,
          started_at TIMESTAMP, finished_at TIMESTAMP, decision_log STRING)""")
    spark.sql("""
        CREATE TABLE IF NOT EXISTS acme_bronze.audit.agent_reports (
          report_id STRING, agent STRING, created_at TIMESTAMP,
          title STRING, body STRING)""")


def get_anthropic_key(log=None):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    # On serverless jobs the runtime-ambient dbutils is the reliable path;
    # WorkspaceClient().dbutils has proven flaky there — keep it as fallback only.
    errors = []
    try:
        from databricks.sdk.runtime import dbutils
        return dbutils.secrets.get(scope="agents", key="anthropic_api_key")
    except Exception as e:
        errors.append(f"runtime dbutils: {str(e)[:120]}")
    try:
        from databricks.sdk import WorkspaceClient
        return WorkspaceClient().dbutils.secrets.get(scope="agents", key="anthropic_api_key")
    except Exception as e:
        errors.append(f"WorkspaceClient dbutils: {str(e)[:120]}")
    if log is not None:
        log.append("secret retrieval failed — " + "; ".join(errors))
    return None


def safe_sql(spark, query, log, max_rows=50):
    """The model's only tool. Rejects anything that is not a plain read."""
    q = query.strip().rstrip(";").strip()
    if ";" in q or not q.upper().startswith(READONLY_PREFIXES):
        log.append(f"REJECTED non-read-only query: {q[:120]}")
        return "ERROR: only single read-only statements (SELECT/WITH/SHOW/DESCRIBE) are allowed."
    try:
        rows = spark.sql(q).limit(max_rows).collect()
        out = json.dumps([r.asDict() for r in rows], default=str)[:4000]
        # Log the returned values too, not just the query -- otherwise the evidence log
        # can't actually ground specific numbers in a report, only prove a query ran. Found
        # live: the verification pass correctly flagged this gap on its first real run.
        log.append(f"run_sql ({len(rows)} rows): {q[:200]} -> {out[:200] if rows else '(no rows)'}")
        return out if rows else "(no rows)"
    except Exception as e:
        msg = f"SQL ERROR: {str(e)[:400]}"
        log.append(f"run_sql failed: {q[:120]} -> {msg[:120]}")
        return msg


VERIFY_SYSTEM = (
    "You are an independent fact-checker, not the agent that wrote this report. You will be "
    "given a report and the log of tool calls actually made while producing it. Check every "
    "specific factual claim in the report -- numbers, table names, statuses, dates -- against "
    "the evidence log. List any claim NOT directly supported by something in the log. If every "
    "claim is supported, respond with exactly: 'All claims verified against the evidence log.' "
    "Be terse -- a short list of gaps, or that one line. Never restate the whole report."
)


def verify_report(client, report, log):
    """Second, independent pass over the first pass's own output: catches an agent that
    queried real data correctly but then misreported what it found -- the class of error a
    single-pass agent structurally cannot see in itself. Failure to run is reported as such,
    not swallowed, and never blocks the report from saving (verification degrades the
    confidence signal, it doesn't gate the artifact)."""
    evidence = "\n".join(l for l in log if l.startswith("run_sql"))
    if not evidence:
        return "No run_sql evidence was logged for this report -- nothing to verify against."
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=1024,
            system=VERIFY_SYSTEM,
            messages=[{"role": "user", "content":
                      f"EVIDENCE LOG (tool calls actually made):\n{evidence}\n\n"
                      f"REPORT TO VERIFY:\n{report}"}])
        return "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception as e:
        return f"Verification pass failed to run: {str(e)[:150]} (report not independently checked)"


def run_reasoning(spark, agent_name, system, user_prompt, log):
    """Claude tool loop. Returns final report text, or None in deterministic mode."""
    key = get_anthropic_key(log)
    if not key:
        log.append("no Anthropic key available — deterministic mode")
        return None
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    tools = [{
        "name": "run_sql",
        "description": ("Run one read-only SQL statement (SELECT/WITH/SHOW/DESCRIBE) against "
                        "Unity Catalog to investigate the lakehouse. Call this whenever a claim "
                        "needs evidence — never guess row counts or values."),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "A single read-only SQL statement"}},
            "required": ["query"],
        },
    }]
    messages = [{"role": "user", "content": user_prompt}]
    response = None
    for _ in range(MAX_STEPS):
        response = client.messages.create(
            model=MODEL, max_tokens=8000,
            thinking={"type": "adaptive"}, output_config={"effort": "high"},
            system=system, tools=tools, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason == "tool_use":
            results = [
                {"type": "tool_result", "tool_use_id": b.id,
                 "content": safe_sql(spark, b.input.get("query", ""), log)}
                for b in response.content if b.type == "tool_use"
            ]
            messages.append({"role": "user", "content": results})
            continue
        break
    if response is None:
        return None
    if response.stop_reason == "tool_use":
        # Tool budget exhausted mid-investigation: force a final report from the
        # evidence gathered so far instead of persisting interim narration.
        log.append(f"tool budget ({MAX_STEPS}) exhausted — forcing finalization turn")
        messages.append({"role": "user", "content":
                         "Tool budget exhausted. Write your final report NOW from the "
                         "evidence you already gathered; note anything left unverified."})
        response = client.messages.create(
            model=MODEL, max_tokens=8000,
            thinking={"type": "adaptive"}, output_config={"effort": "high"},
            system=system, tools=tools, tool_choice={"type": "none"}, messages=messages,
        )
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    log.append(f"reasoning finished: stop_reason={response.stop_reason}, "
               f"out_tokens={response.usage.output_tokens}")
    if not text:
        return None

    verdict = verify_report(client, text, log)
    log.append(f"verification: {verdict[:300]}")
    evidence_lines = [l for l in log if l.startswith("run_sql")]
    evidence_block = "\n".join(f"- {l}" for l in evidence_lines) or "(no run_sql calls made)"
    return (f"{text}\n\n---\n\n"
            f"## Evidence log\n{evidence_block}\n\n"
            f"## Independent verification\n{verdict}")


def log_run(spark, agent, mode, status, started_at, log):
    spark.sql("""
        INSERT INTO acme_bronze.audit.agent_runs VALUES
        ('{run_id}', '{agent}', '{mode}', '{status}', '{started}', current_timestamp(), '{log}')
    """.format(run_id=str(uuid.uuid4()), agent=agent, mode=mode, status=status,
               started=started_at.strftime("%Y-%m-%d %H:%M:%S"),
               log=" | ".join(log).replace("'", "''")[:8000]))


def save_report(spark, agent, title, body):
    df = spark.createDataFrame(
        [(str(uuid.uuid4()), agent, datetime.now(timezone.utc), title, body[:60000])],
        schema="report_id STRING, agent STRING, created_at TIMESTAMP, title STRING, body STRING")
    df.write.mode("append").saveAsTable("acme_bronze.audit.agent_reports")
