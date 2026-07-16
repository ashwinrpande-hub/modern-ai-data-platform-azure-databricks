"""Marketplace API. Independent: only env vars connect it to Databricks."""
from fastapi import FastAPI, Query
import os, json, urllib.request

app = FastAPI(title="acme Data Marketplace API")
HOST, TOKEN = os.environ["DATABRICKS_HOST"], os.environ["DATABRICKS_TOKEN"]

def dbx(path, payload=None):
    req = urllib.request.Request(f"{HOST}{path}", method="POST" if payload else "GET",
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

@app.get("/health")
def health(): return {"ok": True}

@app.get("/products")
def products():
    """Data products = tagged secure views in acme_products (UC tags drive discovery)."""
    r = dbx("/api/2.0/sql/statements", {"warehouse_id": os.environ["DATABRICKS_WAREHOUSE_ID"],
        "statement": """SELECT v.table_name, v.comment, t.tag_value AS domain
                        FROM acme_products.information_schema.views v
                        LEFT JOIN system.information_schema.table_tags t
                          ON t.table_name=v.table_name AND t.tag_name='domain'""",
        "wait_timeout": "30s"})
    return [{"name": x[0], "description": x[1], "domain": x[2]} for x in r["result"]["data_array"]]

@app.get("/search")
def ai_search(q: str = Query(...)):
    """AI-powered metadata search via Databricks Vector Search over product descriptions."""
    r = dbx("/api/2.0/vector-search/indexes/acme_gold.ai.product_metadata_idx/query",
        {"query_text": q, "num_results": 5, "columns": ["product_name", "description", "owner"]})
    return r.get("result", {}).get("data_array", [])

