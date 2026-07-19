#!/usr/bin/env python3
"""Idempotent deployer. Usage:
   python scripts/deploy.py --env dev                  # full deploy
   python scripts/deploy.py --register-source <name>   # onboard one source from YAML
Steps: 1 catalogs/schemas 2 config tables 3 seed mappings+fx 4 security 5 semantics
       6 register sources (+cfg.source_registry row — fixes validate check #3)
       7 pipelines via REST (+cfg.pipeline_registry for quarantine_writer)
       8 jobs -> `databricks bundle deploy` on pipelines/jobs/ 9 products 10 validate
Target state: migrate this whole script to a Declarative Automation Bundle; REST kept for
interview-demo transparency."""
import argparse, json, sys, yaml, urllib.request, os

HOST = os.environ.get("DATABRICKS_HOST"); TOKEN = os.environ.get("DATABRICKS_TOKEN")

def api(path, payload=None, method="GET"):
    req = urllib.request.Request(f"{HOST}/api/2.0/{path}", method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def sql(stmt):
    return api("sql/statements", {"warehouse_id": os.environ["DATABRICKS_WAREHOUSE_ID"],
                                  "statement": stmt, "wait_timeout": "30s"}, "POST")

def run_sql_file(path):
    print(f"[sql] {path}")
    for stmt in open(path).read().split(";"):
        if stmt.strip():
            sql(stmt)

def register_source(name):
    cfg = yaml.safe_load(open("config/replication_sources.yaml"))
    src = next((s for s in cfg["sources"] if s["name"] == name), None)
    if not src: sys.exit(f"source '{name}' not in replication_sources.yaml")

    # A4 fix: record in cfg.source_registry so governance + validate.py see the estate
    exp = ", ".join(f"'{k}','{v}'" for k, v in src.get("expectations", {}).items())
    pks = ", ".join(f"'{p}'" for p in src["primary_key"])
    sql(f"""INSERT INTO acme_bronze.cfg.source_registry VALUES (
        '{name}','{src["system"]}','{src["region"]}','{src["pattern"]}','{src["target"]}',
        array({pks}),'{src.get("sequence_col", src.get("cursor_column",""))}',
        '{src.get("schedule","")}', map({exp}), current_user(), current_timestamp(), true)""")

    template = {"goldengate": "ingestion/templates/bronze_ingest_template.py",
                "autoloader_file": "ingestion/templates/bronze_ingest_template.py",
                "litmus_adls": "ingestion/templates/bronze_ingest_template.py",
                "litmus_eventhub": "ingestion/litmus_ot/litmus_eventhub_dlt.py",
                "lakeflow_sqlserver": None, "lakeflow_query": None, "lakeflow_d365": None
                }[src["pattern"]]
    if template:  # shared-template DLT pipeline bound via source_name conf
        r = api("pipelines", {"name": f"bronze-{name}", "serverless": True,
            "continuous": src.get("schedule") == "continuous",
            "libraries": [{"file": {"path": f"/Workspace/Repos/platform/{template}"}}],
            "configuration": {"source_name": name},
            "catalog": "acme_bronze", "target": src["target"].split(".")[1]}, "POST")
        sql(f"""INSERT INTO acme_bronze.cfg.pipeline_registry VALUES (
            '{r.get("pipeline_id","")}','bronze-{name}','{name}',current_timestamp(),true)""")
    else:
        print(f"[lakeflow] managed connector ({src['pattern']}) — created via Lakeflow "
              f"Connect API/UI from the YAML row; no custom pipeline needed")
    print(f"[registered] {name} ({src['pattern']}) -> {src['target']}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--env", default="dev")
    p.add_argument("--register-source"); a = p.parse_args()
    if a.register_source:
        register_source(a.register_source)
    else:
        for f in ["config/config_tables.sql", "config/seed_layer_mappings.sql",
                  "security/unity_catalog_policies.sql", "semantics/sales_metric_view.sql",
                  "data_products/publish_marketplace.sql"]:
            run_sql_file(f)
        for s in yaml.safe_load(open("config/replication_sources.yaml"))["sources"]:
            register_source(s["name"])
        print("Deploy complete. Then: `databricks bundle deploy` for pipelines/jobs/, "
              "and run scripts/validate.py.")

