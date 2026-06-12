#!/usr/bin/env python3
"""Idempotent deployer. Usage:
   python scripts/deploy.py --env dev                  # full deploy
   python scripts/deploy.py --register-source <name>   # onboard one source from YAML
Steps: 1 catalogs/schemas 2 config tables 3 seed mappings 4 security 5 register sources
       6 create/refresh DLT pipelines (REST) 7 jobs (DQ, features, vectors) 8 products 9 validate
"""
import argparse, json, sys, yaml, urllib.request, os

HOST = os.environ.get("DATABRICKS_HOST"); TOKEN = os.environ.get("DATABRICKS_TOKEN")

def api(path, payload=None, method="GET"):
    req = urllib.request.Request(f"{HOST}/api/2.0/{path}", method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def run_sql_file(path):
    print(f"[sql] {path}")
    # executed via Databricks SQL Statement Execution API (warehouse id from env)
    wh = os.environ["DATABRICKS_WAREHOUSE_ID"]
    for stmt in open(path).read().split(";"):
        if stmt.strip():
            api("sql/statements", {"warehouse_id": wh, "statement": stmt}, "POST")

def register_source(name):
    cfg = yaml.safe_load(open("config/replication_sources.yaml"))
    src = next((s for s in cfg["sources"] if s["name"] == name), None)
    if not src: sys.exit(f"source '{name}' not in replication_sources.yaml")
    template = {"goldengate": "ingestion/templates/bronze_ingest_template.py",
                "autoloader_file": "ingestion/templates/bronze_ingest_template.py",
                "litmus_adls": "ingestion/templates/bronze_ingest_template.py",
                "litmus_eventhub": "ingestion/litmus_ot/litmus_eventhub_dlt.py",
                "lakeflow_sqlserver": None}[src["pattern"]]
    if template:  # create a DLT pipeline bound to the shared template + source_name conf
        api("pipelines", {"name": f"bronze-{name}", "serverless": True, "continuous": src.get("schedule")=="continuous",
            "libraries": [{"file": {"path": f"/Workspace/Repos/platform/{template}"}}],
            "configuration": {"source_name": name},
            "catalog": "nucor_bronze", "target": src["target"].split(".")[1]}, "POST")
    else:
        print("[lakeflow] managed connector — apply ingestion/sqlserver/lakeflow_sqlserver.yaml in UI/API")
    print(f"[registered] {name} ({src['pattern']}) -> {src['target']}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--env", default="dev")
    p.add_argument("--register-source"); a = p.parse_args()
    if a.register_source:
        register_source(a.register_source)
    else:
        for f in ["config/config_tables.sql", "security/unity_catalog_policies.sql",
                  "data_products/publish_marketplace.sql"]:
            run_sql_file(f)
        for s in yaml.safe_load(open("config/replication_sources.yaml"))["sources"]:
            register_source(s["name"])
        print("Deploy complete. Run scripts/validate.py next.")
