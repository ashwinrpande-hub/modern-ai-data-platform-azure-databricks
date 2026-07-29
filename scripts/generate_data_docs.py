#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate docs/DATA_MODEL.md and docs/DATA_CATALOG.html from
data/exports/_extraction/extraction_result.json (see extract_data_model.py) plus a
hand-verified lineage edge list. Self-contained HTML, no external deps at render time.

The edge list below was verified against three independent live/code sources:
  - Bronze->Silver: the live acme_bronze.cfg.layer_mappings config table
  - Gold->Products: live `SHOW CREATE TABLE` DDL on each products view
  - everything else: pipelines/silver_dlt.py, pipelines/gold_dlt.py, ml/build_features.py,
    ai/provision_vector_search.py, agents/vector_content.py (the code actually deployed)
Re-verify edges here if those pipelines change shape.
"""
import json, os, html as H
from datetime import date
from collections import defaultdict

IN_PATH = os.path.join("data", "exports", "_extraction", "extraction_result.json")
OUT_MD = os.path.join("docs", "DATA_MODEL.md")
OUT_HTML = os.path.join("docs", "DATA_CATALOG.html")
WORKSPACE_HOST = "adb-7405618665227003.3.azuredatabricks.net"

with open(IN_PATH, encoding="utf-8") as f:
    D = json.load(f)

TABLES = {f"{t['table_catalog']}.{t['table_schema']}.{t['table_name']}": t for t in D["tables"]}
GOV_SCHEMAS = {("acme_bronze", "audit"), ("acme_bronze", "cfg")}


def is_gov(t):
    return (t["table_catalog"], t["table_schema"]) in GOV_SCHEMAS


gov_tables = {fqn: t for fqn, t in TABLES.items() if is_gov(t)}

B, S, G, P = "acme_bronze", "acme_silver", "acme_gold", "acme_products"
EDGES = [
    (f"{B}.sap.kna1", f"{S}.sales.customer", "bronze2silver"),
    (f"{B}.jde.f0101", f"{S}.sales.customer", "bronze2silver"),
    (f"{B}.sap.vbak", f"{S}.sales.sales_order_header", "bronze2silver"),
    (f"{B}.jde.f4201", f"{S}.sales.sales_order_header", "bronze2silver"),
    (f"{B}.qad.so_mstr", f"{S}.sales.sales_order_header", "bronze2silver"),
    (f"{B}.sap.lips", f"{S}.sales.shipment", "bronze2silver"),
    (f"{B}.sap.vbrp", f"{S}.sales.invoice", "bronze2silver"),
    (f"{B}.ot.furnace_telemetry", f"{S}.sales.furnace_heat_5min", "bronze2silver"),

    (f"{S}.ref.fx_rates", f"{S}.sales.sales_order_header", "silver_internal"),
    (f"{S}.ref.fx_rates", f"{S}.sales.fx_rates", "silver_internal"),
    (f"{S}.sales.sales_order_header", f"{S}.sales.v_sales_order_header_current", "silver_internal"),
    (f"{S}.sales.shipment", f"{S}.sales.v_shipment_current", "silver_internal"),
    (f"{S}.sales.invoice", f"{S}.sales.v_invoice_current", "silver_internal"),

    (f"{S}.sales.customer", f"{G}.sales.dim_customer", "silver2gold"),
    (f"{S}.sales.v_sales_order_header_current", f"{G}.sales.fact_sales_orders", "silver2gold"),
    (f"{G}.sales.dim_customer", f"{G}.sales.fact_sales_orders", "gold_internal"),
    (f"{S}.sales.furnace_heat_5min", f"{G}.sales.fact_heat_quality", "silver2gold"),
    (f"{S}.sales.customer", f"{G}.sales.pit_customer", "silver2gold"),
    (f"{S}.sales.v_sales_order_header_current", f"{G}.sales.bridge_order_fulfillment", "silver2gold"),
    (f"{S}.sales.v_shipment_current", f"{G}.sales.bridge_order_fulfillment", "silver2gold"),
    (f"{S}.sales.v_invoice_current", f"{G}.sales.bridge_order_fulfillment", "silver2gold"),
    (f"{G}.sales.dim_customer", f"{G}.sales.bridge_order_fulfillment", "gold_internal"),

    (f"{G}.sales.fact_sales_orders", f"{G}.sales.agg_sales_daily", "gold_internal"),
    (f"{G}.sales.fact_sales_orders", f"{G}.sales.mv_sales_metrics", "gold_internal"),
    (f"{G}.sales.fact_sales_orders", f"{G}.ml.customer_features", "gold_internal"),
    (f"{G}.sales.bridge_order_fulfillment", f"{G}.ml.customer_features", "gold_internal"),
    (f"{G}.sales.dim_customer", f"{G}.sales.customer_narratives", "gold_internal"),
    (f"{G}.sales.bridge_order_fulfillment", f"{G}.sales.customer_narratives", "gold_internal"),
    (f"{G}.sales.customer_narratives", f"{G}.ai.customer_profile_text", "gold_internal"),
    (f"{G}.ai.customer_profile_text", f"{G}.ai.customer_profile_idx", "gold_internal"),

    (f"{G}.sales.fact_sales_orders", f"{P}.sales.v_sales_orders", "gold2products"),
    (f"{G}.sales.fact_sales_orders", f"{P}.sales.v_sales_orders_unified", "gold2products"),
    (f"{G}.sales.dim_customer", f"{P}.sales.v_sales_orders_unified", "gold2products"),
    (f"{G}.sales.bridge_order_fulfillment", f"{P}.sales.v_sales_orders_unified", "gold2products"),
    (f"{G}.sales.fact_sales_orders", f"{P}.sales.order_to_cash", "gold2products"),
    (f"{G}.sales.dim_customer", f"{P}.sales.order_to_cash", "gold2products"),
    (f"{G}.sales.bridge_order_fulfillment", f"{P}.sales.order_to_cash", "gold2products"),
    (f"{G}.sales.dim_customer", f"{P}.sales.v_customer_360", "gold2products"),
    (f"{G}.sales.customer_narratives", f"{P}.sales.v_customer_360", "gold2products"),
    (f"{G}.sales.bridge_order_fulfillment", f"{P}.sales.v_customer_360", "gold2products"),
    (f"{G}.sales.fact_sales_orders", f"{P}.sales.v_customer_360", "gold2products"),
    (f"{G}.sales.fact_heat_quality", f"{P}.ops.v_melt_to_margin", "gold2products"),
    (f"{G}.sales.agg_sales_daily", f"{P}.ops.v_melt_to_margin", "gold2products"),

    (f"{B}.audit.dq_results", f"{P}.meta.v_product_trust_scores", "governance2products"),
    (f"{B}.cfg.product_registry", f"{P}.meta.v_product_trust_scores", "governance2products"),
]
UNINTEG = [f"{B}.d365.salesorders", f"{B}.sfdc.opportunity", f"{B}.mes.rollmill_orders"]
NOT_LANDED = [
    ("ebs_oe_order_headers", "EBS", "goldengate", "bronze.ebs.oe_order_headers_all"),
    ("ebs_ra_customer_trx", "EBS", "lakeflow_query", "bronze.ebs.ra_customer_trx_all"),
    ("ot_caster_history", "LITMUS", "litmus_adls", "bronze.ot.caster_history"),
]
GOVERNANCE_NOTES = {
    f"{G}.sales.dim_customer": [
        "Row filter: acme_gold.sec.region_filter ON (source_system) — analysts see only their region",
        "Column mask: customer_name → acme_gold.sec.mask_customer_name (visible unmasked only to data_steward)",
        "PII tags: customer_name='name', src_customer_id='identifier'",
    ],
    f"{G}.sales.fact_sales_orders": [
        "Row filter: acme_gold.sec.region_filter ON (source_system)",
    ],
}
LAYER_META = {
    B: dict(label="Bronze", sub="raw, source-shaped", color="#b8752e", text="#ffffff"),
    S: dict(label="Silver", sub="3NF, insert-only, hash-keyed", color="#8a8f98", text="#ffffff"),
    G: dict(label="Gold", sub="star schema + DV2.0 + ML/AI", color="#c9a227", text="#1a1a1a"),
    P: dict(label="Products", sub="governed output ports", color="#2a78d6", text="#ffffff"),
}
SCHEMA_ORDER = {
    B: ["sap", "jde", "qad", "d365", "sfdc", "ot", "mes"],
    S: ["sales", "ref"],
    G: ["sales", "ml", "ai"],
    P: ["sales", "ops", "meta"],
}


def source_badge(t_fq):
    schema_table = t_fq.split(".", 2)[1] + "." + t_fq.split(".", 2)[2]
    for r in D["source_registry"]:
        if r["target"] == f"bronze.{schema_table}":
            return f"{r['system']} · {r['pattern']} · {r['region']}"
    return None


def flow_nodes_by_layer():
    out = {}
    for cat in (B, S, G, P):
        by_schema = defaultdict(list)
        for fqn, t in TABLES.items():
            if t["table_catalog"] != cat or is_gov(t):
                continue
            by_schema[t["table_schema"]].append(fqn)
        order = SCHEMA_ORDER[cat]
        schemas = sorted(by_schema, key=lambda s: order.index(s) if s in order else 99)
        out[cat] = [(s, sorted(by_schema[s])) for s in schemas]
    return out


LAYOUT = flow_nodes_by_layer()
TABLE_COUNT_BY_LAYER = {cat: sum(len(t) for _, t in LAYOUT[cat]) for cat in (B, S, G, P)}
TOTAL_ROWS = sum(t.get("row_count") or 0 for t in D["tables"])
NOW = date.today().isoformat()

# ---------------------------------------------------------------------------
# SVG geometry
# ---------------------------------------------------------------------------
NODE_W, NODE_H = 236, 46
COL_GAP = 118
MARGIN_X, MARGIN_Y = 40, 70
HEADER_H = 20
GROUP_GAP = 18
ROW_GAP = 10


def node_id(fqn):
    return "n_" + fqn.replace(".", "_")


positions = {}
col_x = {}
x = MARGIN_X
for cat in (B, S, G, P):
    col_x[cat] = x
    x += NODE_W + COL_GAP

max_y = 0
for cat in (B, S, G, P):
    y = MARGIN_Y + HEADER_H + 30
    for schema, tbls in LAYOUT[cat]:
        y += HEADER_H
        for fqn in tbls:
            positions[fqn] = (col_x[cat], y)
            y += NODE_H + ROW_GAP
        y += GROUP_GAP
    max_y = max(max_y, y)

SVG_W = col_x[P] + NODE_W + MARGIN_X
SVG_H = max_y + MARGIN_Y


def anchor_right(fqn):
    px, py = positions[fqn]
    return px + NODE_W, py + NODE_H / 2


def anchor_left(fqn):
    px, py = positions[fqn]
    return px, py + NODE_H / 2


def edge_path(s, t, kind):
    if kind in ("silver_internal", "gold_internal"):
        x1, y1 = anchor_right(s)
        x2, y2 = anchor_right(t)
        bulge = 46
        return f"M {x1:.1f} {y1:.1f} C {x1+bulge:.1f} {y1:.1f}, {x2+bulge:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"
    x1, y1 = anchor_right(s)
    x2, y2 = anchor_left(t)
    mx = (x1 + x2) / 2
    return f"M {x1:.1f} {y1:.1f} C {mx:.1f} {y1:.1f}, {mx:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"


EDGE_STYLE = {
    "bronze2silver": dict(cls="flow"), "silver2gold": dict(cls="flow"),
    "gold2products": dict(cls="flow"), "silver_internal": dict(cls="internal"),
    "gold_internal": dict(cls="internal"), "governance2products": dict(cls="flow"),
}
TYPE_ICON = {
    "MANAGED": "TABLE", "STREAMING_TABLE": "STREAM", "MATERIALIZED_VIEW": "MV",
    "VIEW": "VIEW", "METRIC_VIEW": "METRIC", "FOREIGN": "INDEX",
}


def esc(s):
    return H.escape(str(s)) if s is not None else ""


svg_parts = [f'<svg id="lineageSvg" viewBox="0 0 {SVG_W} {SVG_H}" xmlns="http://www.w3.org/2000/svg">',
             '''<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" class="arrowhead"/>
  </marker>
</defs>''']

for cat in (B, S, G, P):
    lm = LAYER_META[cat]
    cx = col_x[cat]
    svg_parts.append(
        f'<g class="col-header"><rect x="{cx}" y="{MARGIN_Y-14}" width="{NODE_W}" height="30" rx="6" '
        f'fill="{lm["color"]}"/><text x="{cx+NODE_W/2}" y="{MARGIN_Y+6}" text-anchor="middle" '
        f'class="col-title" fill="{lm["text"]}">{lm["label"]}</text></g>')
    svg_parts.append(
        f'<text x="{cx+NODE_W/2}" y="{MARGIN_Y+26}" text-anchor="middle" class="col-sub">{esc(lm["sub"])}</text>')

for cat in (B, S, G, P):
    y = MARGIN_Y + HEADER_H + 30
    for schema, tbls in LAYOUT[cat]:
        y += HEADER_H
        svg_parts.append(f'<text x="{col_x[cat]}" y="{y-6}" class="schema-label">{esc(schema)}</text>')
        for fqn in tbls:
            y += NODE_H + ROW_GAP
        y += GROUP_GAP

for s, t, kind in EDGES:
    if s not in positions or t not in positions:
        continue
    d = edge_path(s, t, kind)
    svg_parts.append(f'<path d="{d}" class="edge {EDGE_STYLE[kind]["cls"]}" '
                      f'data-src="{node_id(s)}" data-tgt="{node_id(t)}" marker-end="url(#arrow)"/>')

for cat in (B, S, G, P):
    lm = LAYER_META[cat]
    for schema, tbls in LAYOUT[cat]:
        for fqn in tbls:
            t = TABLES[fqn]
            px, py = positions[fqn]
            nid = node_id(fqn)
            uninteg = fqn in UNINTEG
            dash = ' stroke-dasharray="5,4"' if uninteg else ""
            badge = source_badge(fqn) if cat == B else None
            rc = t.get("row_count")
            rc_txt = f"{rc:,}" if isinstance(rc, int) else "—"
            sub = badge if badge else f"{TYPE_ICON.get(t['table_type'], t['table_type'])} · {rc_txt} rows"
            warn = '<tspan class="warn-mark">⚠</tspan> ' if uninteg else ""
            svg_parts.append(f'''<g class="node{" uninteg" if uninteg else ""}" id="{nid}" data-fq="{esc(fqn)}" tabindex="0">
  <rect x="{px}" y="{py}" width="{NODE_W}" height="{NODE_H}" rx="7" class="node-rect"{dash}/>
  <rect x="{px}" y="{py}" width="5" height="{NODE_H}" rx="2" fill="{lm['color']}"/>
  <text x="{px+14}" y="{py+18}" class="node-title">{warn}{esc(schema)}.{esc(t['table_name'])}</text>
  <text x="{px+14}" y="{py+34}" class="node-sub">{esc(sub)}</text>
</g>''')
svg_parts.append("</svg>")
LINEAGE_SVG = "\n".join(svg_parts)

# ---------------------------------------------------------------------------
# Node data + transitive ancestors/descendants for click-to-trace highlighting
# ---------------------------------------------------------------------------
fwd, rev = defaultdict(set), defaultdict(set)
for s, t, k in EDGES:
    fwd[s].add(t)
    rev[t].add(s)


def transitive(start, graph):
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        for nxt in graph.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


NODE_DATA = {}
for fqn, t in TABLES.items():
    if is_gov(t):
        continue
    cols = sorted(t["columns"], key=lambda c: c["ordinal_position"])
    NODE_DATA[fqn] = {
        "id": node_id(fqn), "fq": fqn,
        "catalog": t["table_catalog"], "schema": t["table_schema"], "table": t["table_name"],
        "type": t["table_type"], "comment": t.get("comment") or "",
        "row_count": t.get("row_count"), "sample_rows": t.get("sample_rows", 0),
        "columns": [{"name": c["column_name"], "type": c["data_type"],
                      "nullable": c["is_nullable"], "comment": c.get("comment")} for c in cols],
        "upstream": sorted(rev.get(fqn, [])), "downstream": sorted(fwd.get(fqn, [])),
        "ancestors": sorted(transitive(fqn, rev)), "descendants": sorted(transitive(fqn, fwd)),
        "governance": GOVERNANCE_NOTES.get(fqn, []),
        "source_badge": source_badge(fqn) if t["table_catalog"] == B else None,
        "uninteg": fqn in UNINTEG,
        "excel_sheet": f"{t['table_catalog']}.xlsx → sheet '{t['table_schema']}.{t['table_name'][:29]}'",
    }

# ---------------------------------------------------------------------------
# Catalog tab HTML (grouped accordion, layer > schema > table)
# ---------------------------------------------------------------------------
def render_table_card(nd, open_default=False, id_prefix="cat_"):
    rc = nd["row_count"]
    rc_txt = f"{rc:,}" if isinstance(rc, int) else "n/a"
    badges = []
    if nd["source_badge"]:
        badges.append(f'<span class="pill pill-src">{esc(nd["source_badge"])}</span>')
    badges.append(f'<span class="pill">{esc(nd["type"])}</span>')
    badges.append(f'<span class="pill">{rc_txt} rows</span>')
    if nd["uninteg"]:
        badges.append('<span class="pill pill-warn">⚠ not yet consumed downstream</span>')
    for g in nd["governance"]:
        badges.append(f'<span class="pill pill-gov">🔒 {esc(g.split(":")[0])}</span>')
    cols_rows = "".join(
        f'<tr><td class="mono">{esc(c["name"])}</td><td class="mono muted">{esc(c["type"])}</td>'
        f'<td class="muted">{esc(c["nullable"])}</td><td class="muted">{esc(c["comment"] or "")}</td></tr>'
        for c in nd["columns"])
    up = ", ".join(f'<code>{esc(x)}</code>' for x in nd["upstream"]) or "<em>none (landing table)</em>"
    down = ", ".join(f'<code>{esc(x)}</code>' for x in nd["downstream"]) or "<em>none (terminal / not yet consumed)</em>"
    gov_html = ("<ul class='gov-list'>" + "".join(f"<li>{esc(g)}</li>" for g in nd["governance"]) + "</ul>") if nd["governance"] else ""
    open_attr = " open" if open_default else ""
    return f'''<details class="cat-table" id="{id_prefix}{nd["id"]}"{open_attr}>
  <summary><span class="cat-table-name">{esc(nd["schema"])}.{esc(nd["table"])}</span>
    <span class="cat-table-comment">{esc(nd["comment"])}</span></summary>
  <div class="cat-table-body">
    <div class="badges">{"".join(badges)}</div>
    <table class="col-table">
      <thead><tr><th>Column</th><th>Type</th><th>Nullable</th><th>Comment</th></tr></thead>
      <tbody>{cols_rows}</tbody>
    </table>
    {gov_html}
    <div class="lineage-text"><b>Reads from:</b> {up}</div>
    <div class="lineage-text"><b>Feeds:</b> {down}</div>
    <div class="sample-note">500-row sample: <code>data/exports/excel/{nd["excel_sheet"]}</code></div>
  </div>
</details>'''


def render_gap_card():
    rows = "".join(
        f"<tr><td class='mono'>{esc(name)}</td><td>{esc(sysname)}</td><td class='mono'>{esc(pattern)}</td>"
        f"<td class='mono muted'>{esc(target)}</td></tr>"
        for name, sysname, pattern, target in NOT_LANDED)
    return f'''<details class="cat-table gap-card">
  <summary><span class="cat-table-name">⚠ Registered but not landed</span>
    <span class="cat-table-comment">3 sources in cfg.source_registry with no matching table in the metastore today</span></summary>
  <div class="cat-table-body">
    <table class="col-table">
      <thead><tr><th>source_name</th><th>system</th><th>pattern</th><th>target (expected)</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <p class="muted">Config says these should exist (registered ingestion sources); the live metastore has no
    such table. This is an authentic gap — not a display bug — surfaced by cross-checking
    <code>acme_bronze.cfg.source_registry</code> against <code>system.information_schema.tables</code>.</p>
  </div>
</details>'''


def catalog_layer_html(cat):
    lm = LAYER_META[cat]
    parts = [f'<section class="cat-layer" data-layer="{cat}">',
             f'<h2 class="cat-layer-title" style="border-color:{lm["color"]}">{lm["label"]} '
             f'<span class="cat-layer-sub">— {esc(lm["sub"])}</span></h2>']
    for schema, tbls in LAYOUT[cat]:
        parts.append(f'<h3 class="cat-schema">{cat}.{esc(schema)}</h3>')
        for fqn in tbls:
            parts.append(render_table_card(NODE_DATA[fqn]))
    if cat == B:
        parts.append(render_gap_card())
    parts.append("</section>")
    return "\n".join(parts)


CATALOG_HTML = "\n".join(catalog_layer_html(cat) for cat in (B, S, G, P))
uninteg_lis = "".join(f"<li><code>{esc(x)}</code></li>" for x in UNINTEG)
notlanded_lis = "".join(f"<li><code>{esc(t)}</code> ({esc(sysn)}, registered as <code>{esc(n)}</code>)</li>"
                         for n, sysn, pat, t in NOT_LANDED)
NODE_DATA_JSON = json.dumps(NODE_DATA)

PAGE = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>acme Sales Lakehouse — Data Catalog &amp; Lineage</title>
<style>
:root {{
  color-scheme: light;
  --surface-1:#fcfcfb; --surface-2:#f2f1ee; --page:#f9f9f7;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#898781;
  --border:rgba(11,11,11,0.10); --grid:#e1e0d9;
  --accent:#2a78d6; --accent-soft:#e8f0fb;
  --edge-flow:#8a8983; --edge-internal:#c3c2b7;
  --pill-bg:#f2f1ee; --code-bg:#f2f1ee;
}}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) {{
    color-scheme: dark;
    --surface-1:#1a1a19; --surface-2:#222221; --page:#0d0d0d;
    --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#898781;
    --border:rgba(255,255,255,0.12); --grid:#2c2c2a;
    --accent:#3987e5; --accent-soft:#132234;
    --edge-flow:#5a5954; --edge-internal:#3a3a38;
    --pill-bg:#25231f; --code-bg:#222221;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --surface-1:#1a1a19; --surface-2:#222221; --page:#0d0d0d;
  --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#898781;
  --border:rgba(255,255,255,0.12); --grid:#2c2c2a;
  --accent:#3987e5; --accent-soft:#132234;
  --edge-flow:#5a5954; --edge-internal:#3a3a38;
  --pill-bg:#25231f; --code-bg:#222221;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--page); color:var(--text-primary);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }}
header.top {{ padding:22px 28px 14px; border-bottom:1px solid var(--border); background:var(--surface-1); }}
header.top h1 {{ margin:0 0 4px; font-size:1.5rem; }}
header.top p {{ margin:0; color:var(--text-secondary); font-size:0.9rem; }}
.stats {{ display:flex; gap:18px; margin-top:12px; flex-wrap:wrap; }}
.stat {{ background:var(--surface-2); border:1px solid var(--border); border-radius:8px; padding:8px 14px; }}
.stat b {{ display:block; font-size:1.15rem; }}
.stat span {{ color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:.04em; }}
nav.tabs {{ display:flex; gap:4px; padding:0 28px; background:var(--surface-1); border-bottom:1px solid var(--border); }}
nav.tabs button {{ background:none; border:none; padding:12px 18px; font-size:0.95rem; color:var(--text-secondary);
  cursor:pointer; border-bottom:2px solid transparent; font-family:inherit; }}
nav.tabs button.active {{ color:var(--text-primary); border-bottom-color:var(--accent); font-weight:600; }}
main {{ padding:20px 28px 60px; max-width:1600px; margin:0 auto; }}
.tabpanel {{ display:none; }}
.tabpanel.show {{ display:block; }}
.legend {{ display:flex; gap:22px; flex-wrap:wrap; align-items:center; margin:0 0 14px; font-size:0.82rem; color:var(--text-secondary); }}
.legend .sw {{ display:inline-block; width:22px; height:2px; margin-right:6px; vertical-align:middle; }}
.legend .sw.flow {{ background:var(--edge-flow); }}
.legend .sw.internal {{ background:var(--edge-internal); border-top:2px dashed var(--edge-internal); height:0; }}
.lineage-wrap {{ display:flex; gap:18px; align-items:flex-start; }}
.svg-scroll {{ flex:1 1 auto; overflow:auto; background:var(--surface-1); border:1px solid var(--border);
  border-radius:10px; padding:10px; max-height:78vh; }}
svg#lineageSvg {{ display:block; width:100%; height:auto; min-width:1100px; }}
.col-title {{ font-size:14px; font-weight:700; }}
.col-sub {{ font-size:10.5px; fill:var(--text-muted); }}
.schema-label {{ font-size:10.5px; fill:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; }}
.node-rect {{ fill:var(--surface-2); stroke:var(--border); stroke-width:1; }}
.node {{ cursor:pointer; }}
.node .node-title {{ font-size:11.5px; font-weight:600; fill:var(--text-primary); }}
.node .node-sub {{ font-size:9.5px; fill:var(--text-muted); }}
.node.uninteg .node-rect {{ fill:var(--surface-1); }}
.warn-mark {{ fill:#d03b3b; }}
.edge {{ fill:none; stroke:var(--edge-flow); stroke-width:1.4; marker-end:url(#arrow); opacity:0.55; }}
.edge.internal {{ stroke:var(--edge-internal); stroke-dasharray:4,3; stroke-width:1.2; opacity:0.5; }}
.arrowhead {{ fill:var(--edge-flow); }}
svg.dimmed .node {{ opacity:0.25; }}
svg.dimmed .edge {{ opacity:0.06; }}
svg.dimmed .node.hl-self, svg.dimmed .node.hl-anc, svg.dimmed .node.hl-desc {{ opacity:1; }}
svg.dimmed .edge.hl {{ opacity:0.95; stroke-width:2.2; }}
.node.hl-self .node-rect {{ stroke:var(--accent); stroke-width:2; }}
.node.hl-anc .node-rect {{ stroke:#1baf7a; stroke-width:1.6; }}
.node.hl-desc .node-rect {{ stroke:#eb6834; stroke-width:1.6; }}
.edge.hl {{ stroke:var(--accent); }}
.detail-panel {{ width:340px; flex:0 0 340px; background:var(--surface-1); border:1px solid var(--border);
  border-radius:10px; padding:16px; max-height:78vh; overflow:auto; position:sticky; top:16px; }}
.detail-panel h3 {{ margin:0 0 4px; font-size:1rem; }}
.detail-panel .muted {{ color:var(--text-muted); }}
.detail-panel .placeholder {{ color:var(--text-muted); font-size:0.9rem; }}
.detail-panel table {{ width:100%; border-collapse:collapse; font-size:0.78rem; margin-top:8px; }}
.detail-panel td, .detail-panel th {{ padding:3px 4px; border-bottom:1px solid var(--grid); text-align:left; }}
.dp-section {{ margin-top:12px; }}
.dp-section b {{ font-size:0.78rem; text-transform:uppercase; letter-spacing:.04em; color:var(--text-muted); }}
.dp-list a {{ display:block; font-size:0.8rem; color:var(--accent); text-decoration:none; margin-top:2px; cursor:pointer; }}
.dp-list a:hover {{ text-decoration:underline; }}
.gap-note {{ margin-top:18px; background:var(--accent-soft); border:1px solid var(--border); border-radius:8px;
  padding:12px 14px; font-size:0.82rem; }}
.gap-note h4 {{ margin:0 0 6px; font-size:0.85rem; }}
.gap-note ul {{ margin:4px 0; padding-left:18px; }}
.gap-note code {{ background:var(--code-bg); padding:1px 5px; border-radius:4px; font-size:0.78rem; }}
input#searchBox {{ width:100%; max-width:420px; padding:9px 12px; border-radius:8px; border:1px solid var(--border);
  background:var(--surface-1); color:var(--text-primary); font-size:0.9rem; margin-bottom:16px; }}
.cat-layer-title {{ border-left:5px solid; padding-left:10px; margin:26px 0 10px; font-size:1.15rem; }}
.cat-layer-sub {{ color:var(--text-muted); font-weight:400; font-size:0.85rem; }}
.cat-schema {{ color:var(--text-muted); font-size:0.78rem; text-transform:uppercase; letter-spacing:.05em;
  margin:16px 0 6px; }}
details.cat-table {{ background:var(--surface-1); border:1px solid var(--border); border-radius:8px;
  margin-bottom:8px; padding:0; }}
details.cat-table summary {{ padding:10px 14px; cursor:pointer; list-style:none; display:flex; gap:12px;
  align-items:baseline; }}
details.cat-table summary::-webkit-details-marker {{ display:none; }}
details.cat-table[open] summary {{ border-bottom:1px solid var(--border); }}
.cat-table-name {{ font-weight:600; font-family:ui-monospace,Consolas,monospace; font-size:0.88rem; white-space:nowrap; }}
.cat-table-comment {{ color:var(--text-muted); font-size:0.82rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.cat-table-body {{ padding:12px 14px 16px; }}
.badges {{ margin-bottom:10px; }}
.pill {{ display:inline-block; background:var(--pill-bg); border:1px solid var(--border); border-radius:20px;
  padding:2px 10px; font-size:0.72rem; margin:0 6px 6px 0; color:var(--text-secondary); }}
.pill-src {{ color:var(--accent); border-color:var(--accent); }}
.pill-warn {{ color:#d03b3b; border-color:#d03b3b; }}
.pill-gov {{ color:#8a6d1a; border-color:#c9a227; }}
table.col-table {{ width:100%; border-collapse:collapse; font-size:0.82rem; margin:6px 0; }}
table.col-table th {{ text-align:left; color:var(--text-muted); font-weight:600; font-size:0.72rem;
  text-transform:uppercase; letter-spacing:.03em; padding:5px 8px; border-bottom:1px solid var(--border); }}
table.col-table td {{ padding:5px 8px; border-bottom:1px solid var(--grid); }}
.mono {{ font-family:ui-monospace,Consolas,monospace; }}
.lineage-text {{ font-size:0.82rem; margin-top:6px; }}
.lineage-text code {{ background:var(--code-bg); padding:1px 5px; border-radius:4px; }}
.sample-note {{ margin-top:10px; font-size:0.78rem; color:var(--text-muted); }}
.sample-note code {{ background:var(--code-bg); padding:1px 5px; border-radius:4px; }}
.gov-list {{ font-size:0.8rem; margin:6px 0; padding-left:18px; }}
.gap-card {{ border-color:#d03b3b !important; }}
footer.pagefoot {{ text-align:center; color:var(--text-muted); font-size:0.78rem; padding:24px; }}
@media (max-width: 980px) {{
  .lineage-wrap {{ flex-direction:column; }}
  .detail-panel {{ width:100%; flex:none; position:static; }}
}}
</style>
</head>
<body>
<header class="top">
  <h1>acme Sales Lakehouse — Data Catalog &amp; Lineage</h1>
  <p>Generated {NOW} directly from Unity Catalog on <code>{WORKSPACE_HOST}</code> —
  table/column inventory via <code>system.information_schema</code>, Bronze→Silver lineage via the live
  <code>acme_bronze.cfg.layer_mappings</code> config table, Gold→Products lineage via live
  <code>SHOW CREATE TABLE</code> on each view, remaining edges from <code>pipelines/silver_dlt.py</code> /
  <code>pipelines/gold_dlt.py</code>.</p>
  <div class="stats">
    <div class="stat"><b>{len(TABLES)}</b><span>tables / views</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[B]}+9</b><span>bronze (+ audit/cfg)</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[S]}</b><span>silver</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[G]}</b><span>gold</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[P]}</b><span>products</span></div>
    <div class="stat"><b>{len(EDGES)}</b><span>lineage edges</span></div>
    <div class="stat"><b>{TOTAL_ROWS:,}</b><span>live rows (sum)</span></div>
  </div>
</header>
<nav class="tabs">
  <button class="tab-btn active" data-tab="lineage">Lineage diagram</button>
  <button class="tab-btn" data-tab="catalog">Data catalog</button>
</nav>
<main>
  <section id="tab-lineage" class="tabpanel show">
    <div class="legend">
      <span><span class="sw flow"></span>data flow (Bronze→Silver→Gold→Products)</span>
      <span><span class="sw internal"></span>internal derivation (same layer)</span>
      <span>⚠ dashed border = landed, not yet consumed downstream</span>
      <span>Click any table to trace its full upstream/downstream lineage</span>
    </div>
    <div class="lineage-wrap">
      <div class="svg-scroll">{LINEAGE_SVG}</div>
      <aside class="detail-panel" id="detailPanel">
        <p class="placeholder">Click a table in the diagram to see its columns, row count, and full lineage trace.</p>
        <div class="gap-note">
          <h4>⚠ Landed but not yet consumed downstream</h4>
          <ul>{uninteg_lis}</ul>
          <h4 style="margin-top:10px">⚠ Registered in cfg.source_registry, no table in the metastore</h4>
          <ul>{notlanded_lis}</ul>
        </div>
      </aside>
    </div>
  </section>
  <section id="tab-catalog" class="tabpanel">
    <input id="searchBox" type="text" placeholder="Search tables or columns (e.g. customer_hk, vbak, dim_customer)…">
    {CATALOG_HTML}
  </section>
</main>
<footer class="pagefoot">acme Sales Lakehouse · data/exports/excel/*.xlsx has the full 500-row samples per table, layer by layer · see docs/DATA_MODEL.md for the plain-text data dictionary</footer>
<script>
const NODE_DATA = {NODE_DATA_JSON};

document.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', () => {{
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tabpanel').forEach(p => p.classList.remove('show'));
  btn.classList.add('active');
  document.getElementById('tab-' + btn.dataset.tab).classList.add('show');
}}));

const svg = document.getElementById('lineageSvg');
const panel = document.getElementById('detailPanel');

function fmtRows(n) {{ return (typeof n === 'number') ? n.toLocaleString() : 'n/a'; }}

function renderDetail(nd) {{
  const cols = nd.columns.map(c =>
    `<tr><td class="mono">${{c.name}}</td><td class="mono muted">${{c.type}}</td><td class="muted">${{c.nullable}}</td></tr>`
  ).join('');
  const upLinks = nd.upstream.length ? nd.upstream.map(f =>
    `<a onclick="selectNode('${{'n_' + f.replace(/\\./g,'_')}}')">${{f}}</a>`).join('') : '<span class="muted">none (landing table)</span>';
  const downLinks = nd.downstream.length ? nd.downstream.map(f =>
    `<a onclick="selectNode('${{'n_' + f.replace(/\\./g,'_')}}')">${{f}}</a>`).join('') : '<span class="muted">none (terminal)</span>';
  const gov = nd.governance.length ? `<div class="dp-section"><b>Governance</b><ul class="gov-list">${{nd.governance.map(g=>`<li>${{g}}</li>`).join('')}}</ul></div>` : '';
  panel.innerHTML = `
    <h3>${{nd.schema}}.${{nd.table}}</h3>
    <div class="muted">${{nd.catalog}} · ${{nd.type}}</div>
    <p>${{nd.comment || ''}}</p>
    <div><b>${{fmtRows(nd.row_count)}}</b> live rows &nbsp;·&nbsp; ${{nd.sample_rows}} sampled to Excel</div>
    ${{gov}}
    <div class="dp-section"><b>Columns (${{nd.columns.length}})</b>
      <table>${{cols}}</table>
    </div>
    <div class="dp-section"><b>Reads from (direct)</b><div class="dp-list">${{upLinks}}</div></div>
    <div class="dp-section"><b>Feeds (direct)</b><div class="dp-list">${{downLinks}}</div></div>
    <div class="dp-section"><b>Full ancestor count</b>: ${{nd.ancestors.length}} tables upstream, ${{nd.descendants.length}} downstream</div>
    <div class="sample-note">Sample: <code>data/exports/excel/${{nd.excel_sheet}}</code></div>
  `;
}}

function selectNode(id) {{
  const nd = Object.values(NODE_DATA).find(n => n.id === id);
  if (!nd) return;
  svg.classList.add('dimmed');
  document.querySelectorAll('.node').forEach(n => n.classList.remove('hl-self','hl-anc','hl-desc'));
  document.querySelectorAll('.edge').forEach(e => e.classList.remove('hl'));
  const ancIds = new Set(nd.ancestors.map(f => 'n_' + f.replace(/\\./g,'_')));
  const descIds = new Set(nd.descendants.map(f => 'n_' + f.replace(/\\./g,'_')));
  document.getElementById(id)?.classList.add('hl-self');
  ancIds.forEach(a => document.getElementById(a)?.classList.add('hl-anc'));
  descIds.forEach(d => document.getElementById(d)?.classList.add('hl-desc'));
  document.querySelectorAll('.edge').forEach(e => {{
    const s = e.dataset.src, t = e.dataset.tgt;
    if (s === id || t === id || (ancIds.has(s) && (ancIds.has(t) || t===id)) || (descIds.has(t) && (descIds.has(s) || s===id))) {{
      e.classList.add('hl');
    }}
  }});
  renderDetail(nd);
  document.getElementById(id)?.scrollIntoView({{block:'center', inline:'center', behavior:'smooth'}});
}}

document.querySelectorAll('.node').forEach(n => {{
  n.addEventListener('click', () => selectNode(n.id));
  n.addEventListener('keypress', (e) => {{ if (e.key === 'Enter') selectNode(n.id); }});
}});

const search = document.getElementById('searchBox');
search.addEventListener('input', () => {{
  const q = search.value.trim().toLowerCase();
  document.querySelectorAll('details.cat-table').forEach(card => {{
    if (!q) {{ card.style.display = ''; card.open = false; return; }}
    const hit = card.innerText.toLowerCase().includes(q);
    card.style.display = hit ? '' : 'none';
    if (hit) card.open = true;
  }});
  document.querySelectorAll('.cat-layer').forEach(sec => {{
    const anyVisible = Array.from(sec.querySelectorAll('details.cat-table')).some(c => c.style.display !== 'none');
    sec.style.display = (!q || anyVisible) ? '' : 'none';
  }});
}});
</script>
</body>
</html>'''

os.makedirs("docs", exist_ok=True)
with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(PAGE)
print(f"Wrote {OUT_HTML} ({len(PAGE)} bytes)")

# ---------------------------------------------------------------------------
# docs/DATA_MODEL.md -- plain-text data dictionary, generated from the same
# NODE_DATA so it can never drift from the HTML catalog.
# ---------------------------------------------------------------------------
def md_escape(s):
    return str(s).replace("|", "\\|") if s is not None else ""


def md_table_section(fqn):
    nd = NODE_DATA[fqn]
    rc = nd["row_count"]
    rc_txt = f"{rc:,}" if isinstance(rc, int) else "n/a"
    lines = [f"#### `{nd['schema']}.{nd['table']}`", ""]
    if nd["comment"]:
        lines += [f"_{nd['comment']}_", ""]
    meta_bits = [f"**Type:** {nd['type']}", f"**Live rows:** {rc_txt}", f"**Sampled to Excel:** {nd['sample_rows']} rows"]
    if nd["source_badge"]:
        meta_bits.append(f"**Source:** {nd['source_badge']}")
    if nd["uninteg"]:
        meta_bits.append("**⚠ Gap:** landed in Bronze, not yet consumed by any downstream table")
    lines.append(" · ".join(meta_bits))
    lines.append("")
    lines.append("| Column | Type | Nullable | Comment |")
    lines.append("|---|---|---|---|")
    for c in nd["columns"]:
        lines.append(f"| `{md_escape(c['name'])}` | {md_escape(c['type'])} | {c['nullable']} | {md_escape(c['comment']) or ''} |")
    lines.append("")
    up = ", ".join(f"`{x}`" for x in nd["upstream"]) or "_none — landing table_"
    down = ", ".join(f"`{x}`" for x in nd["downstream"]) or "_none — terminal / not yet consumed_"
    lines.append(f"**Reads from:** {up}  ")
    lines.append(f"**Feeds:** {down}  ")
    if nd["governance"]:
        lines += ["", "**Governance:**"] + [f"- {g}" for g in nd["governance"]]
    lines += ["", f"**Sample data:** `data/exports/excel/{nd['excel_sheet']}`", ""]
    return "\n".join(lines)


md = [
    "# Data Model — acme Sales Lakehouse (medallion architecture)", "",
    f"Generated {NOW} directly from the live Unity Catalog metastore on `{WORKSPACE_HOST}`. "
    f"Table/column inventory comes from `system.information_schema`; Bronze→Silver lineage from the live "
    f"`acme_bronze.cfg.layer_mappings` config table; Gold→Products lineage from live `SHOW CREATE TABLE` DDL "
    f"on each view; remaining edges (Silver internal, Silver→Gold, Gold internal) from "
    f"`pipelines/silver_dlt.py` / `pipelines/gold_dlt.py` / `ml/build_features.py` / "
    f"`ai/provision_vector_search.py` / `agents/vector_content.py`, all of which are the code actually "
    f"deployed to this workspace.", "",
    "This file is machine-generated (do not hand-edit) — regenerate with the pipeline in the Appendix below. "
    "The interactive version of the same data, with a clickable lineage diagram, is `docs/DATA_CATALOG.html`. "
    "500-row samples of every table below live in `data/exports/excel/{bronze,silver,gold,products}.xlsx` "
    "(one workbook per layer, one sheet per table; gitignored, regenerate locally).", "",
    "## Contents", "",
    "| Layer | Tables/views | Notes |", "|---|---|---|",
    f"| [Bronze](#bronze-layer) | {TABLE_COUNT_BY_LAYER[B]} (+ 9 audit/cfg platform tables) | raw, source-shaped, one row per source object |",
    f"| [Silver](#silver-layer) | {TABLE_COUNT_BY_LAYER[S]} | 3NF, insert-only, SHA-256 hash keys |",
    f"| [Gold](#gold-layer) | {TABLE_COUNT_BY_LAYER[G]} | star schema + Data Vault 2.0 PIT/bridge + ML features + AI/vector |",
    f"| [Products](#products-layer) | {TABLE_COUNT_BY_LAYER[P]} | governed output ports (views), published via Delta Sharing |",
    "",
    f"**{len(TABLES)}** tables/views total, **{len(EDGES)}** lineage edges, **{TOTAL_ROWS:,}** live rows summed across all tables.",
    "",
]

for cat in (B, S, G, P):
    lm = LAYER_META[cat]
    md += [f"## {lm['label']} layer", "", f"_{lm['sub']}_", ""]
    for schema, tbls in LAYOUT[cat]:
        md += [f"### {cat}.{schema}", ""]
        for fqn in tbls:
            md.append(md_table_section(fqn))
    if cat == B:
        md += ["### ⚠ Gaps in Bronze", "",
               "**Landed but not yet consumed downstream** (real tables, zero rows read by Silver/Gold today):"]
        md += [f"- `{u}`" for u in UNINTEG]
        md += ["", "**Registered in `cfg.source_registry` but no matching table in the metastore** "
                    "(config says the source should be landing; the live metastore disagrees):"]
        md += [f"- `{tgt}` — registered as `{n}` ({sysn}, pattern `{pat}`)" for n, sysn, pat, tgt in NOT_LANDED]
        md += ["", "### Platform / governance tables (acme_bronze.audit, acme_bronze.cfg)", "",
               "Not part of the medallion data flow — these carry pipeline config and run audit trail. "
               "Omitted from the lineage diagram; listed here for completeness.", "",
               "| Schema | Table | Type | Live rows | Comment |", "|---|---|---|---|---|"]
        for fqn, t in sorted(gov_tables.items()):
            rc = t.get("row_count")
            rc_txt = f"{rc:,}" if isinstance(rc, int) else "n/a"
            md.append(f"| {t['table_schema']} | `{t['table_name']}` | {t['table_type']} | {rc_txt} | {md_escape(t.get('comment') or '')} |")
        md.append("")

md += [
    "## Appendix — regenerating this file", "", "```",
    "# 1. discover schema + pull row counts / 500-row samples (needs databricks-connect serverless)",
    "DATABRICKS_CONFIG_PROFILE=<profile> DATABRICKS_CLI_PATH=<databricks.exe> \\",
    "  python scripts/extract_data_model.py   # discovery + row counts + samples + config lineage",
    "# 2. build the per-layer Excel workbooks (pure pandas/openpyxl, no Spark needed)",
    "python scripts/build_excel_exports.py",
    "# 3. regenerate this file + docs/DATA_CATALOG.html from the extraction output",
    "python scripts/generate_data_docs.py",
    "```", "",
]

MD_CONTENT = "\n".join(md)
os.makedirs("docs", exist_ok=True)
with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write(MD_CONTENT)
print(f"Wrote {OUT_MD} ({len(MD_CONTENT)} bytes, {MD_CONTENT.count(chr(10))} lines)")

# ---------------------------------------------------------------------------
# docs/DATA_MODEL.html -- readable, static, single-scroll document rendering of
# the same data (all cards pre-expanded, sticky table of contents instead of the
# search/accordion UI used in DATA_CATALOG.html's Catalog tab). Reuses the same
# table-card markup + CSS so the two pages look and read consistently.
# ---------------------------------------------------------------------------
OUT_MODEL_HTML = os.path.join("docs", "DATA_MODEL.html")


def doc_layer_section(cat):
    lm = LAYER_META[cat]
    parts = [f'<section class="cat-layer" id="layer_{cat}" data-layer="{cat}">',
             f'<h2 class="cat-layer-title" style="border-color:{lm["color"]}">{lm["label"]} '
             f'<span class="cat-layer-sub">— {esc(lm["sub"])}</span></h2>']
    for schema, tbls in LAYOUT[cat]:
        parts.append(f'<h3 class="cat-schema" id="schema_{cat}_{schema}">{cat}.{esc(schema)}</h3>')
        for fqn in tbls:
            parts.append(render_table_card(NODE_DATA[fqn], open_default=True, id_prefix="doc_"))
    if cat == B:
        parts.append(render_gap_card())
    if cat == B:
        def _gov_row(t):
            rc = t.get("row_count")
            rc_txt = f"{rc:,}" if isinstance(rc, int) else "n/a"
            return (f"<tr><td>{t['table_schema']}</td><td class='mono'>{esc(t['table_name'])}</td>"
                    f"<td>{esc(t['table_type'])}</td><td>{rc_txt}</td>"
                    f"<td class='muted'>{esc(t.get('comment') or '')}</td></tr>")
        gov_rows = "".join(_gov_row(t) for _, t in sorted(gov_tables.items()))
        parts.append(f'''<details class="cat-table" id="doc_governance" open>
  <summary><span class="cat-table-name">acme_bronze.audit / acme_bronze.cfg</span>
    <span class="cat-table-comment">Platform &amp; governance tables — not part of the medallion data flow, omitted from the lineage diagram</span></summary>
  <div class="cat-table-body">
    <table class="col-table">
      <thead><tr><th>Schema</th><th>Table</th><th>Type</th><th>Live rows</th><th>Comment</th></tr></thead>
      <tbody>{gov_rows}</tbody>
    </table>
  </div>
</details>''')
    parts.append("</section>")
    return "\n".join(parts)


def toc_section(cat):
    lm = LAYER_META[cat]
    items = []
    for schema, tbls in LAYOUT[cat]:
        items.append(f'<li class="toc-schema"><a href="#schema_{cat}_{schema}">{esc(schema)}</a><ul>')
        for fqn in tbls:
            nd = NODE_DATA[fqn]
            items.append(f'<li><a href="#doc_{nd["id"]}">{esc(nd["table"])}</a></li>')
        items.append('</ul></li>')
    extra = '<li><a href="#doc_governance">audit / cfg (governance)</a></li>' if cat == B else ''
    return (f'<div class="toc-layer"><a class="toc-layer-link" href="#layer_{cat}" '
            f'style="border-color:{lm["color"]}">{lm["label"]}</a><ul>{"".join(items)}{extra}</ul></div>')


DOC_BODY = "\n".join(doc_layer_section(cat) for cat in (B, S, G, P))
TOC_HTML = "\n".join(toc_section(cat) for cat in (B, S, G, P))

MODEL_PAGE = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>acme Sales Lakehouse — Data Model</title>
<style>
:root {{
  color-scheme: light;
  --surface-1:#fcfcfb; --surface-2:#f2f1ee; --page:#f9f9f7;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#898781;
  --border:rgba(11,11,11,0.10); --grid:#e1e0d9;
  --accent:#2a78d6; --accent-soft:#e8f0fb;
  --pill-bg:#f2f1ee; --code-bg:#f2f1ee;
}}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) {{
    color-scheme: dark;
    --surface-1:#1a1a19; --surface-2:#222221; --page:#0d0d0d;
    --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#898781;
    --border:rgba(255,255,255,0.12); --grid:#2c2c2a;
    --accent:#3987e5; --accent-soft:#132234;
    --pill-bg:#25231f; --code-bg:#222221;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --surface-1:#1a1a19; --surface-2:#222221; --page:#0d0d0d;
  --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#898781;
  --border:rgba(255,255,255,0.12); --grid:#2c2c2a;
  --accent:#3987e5; --accent-soft:#132234;
  --pill-bg:#25231f; --code-bg:#222221;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--page); color:var(--text-primary);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }}
header.top {{ padding:22px 28px 14px; border-bottom:1px solid var(--border); background:var(--surface-1); }}
header.top h1 {{ margin:0 0 4px; font-size:1.5rem; }}
header.top p {{ margin:0; color:var(--text-secondary); font-size:0.9rem; max-width:1000px; }}
header.top .links {{ margin-top:10px; font-size:0.82rem; }}
header.top .links a {{ color:var(--accent); text-decoration:none; margin-right:16px; }}
header.top .links a:hover {{ text-decoration:underline; }}
.stats {{ display:flex; gap:18px; margin-top:12px; flex-wrap:wrap; }}
.stat {{ background:var(--surface-2); border:1px solid var(--border); border-radius:8px; padding:8px 14px; }}
.stat b {{ display:block; font-size:1.15rem; }}
.stat span {{ color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:.04em; }}
.layout {{ display:flex; align-items:flex-start; max-width:1500px; margin:0 auto; padding:24px 28px 80px; gap:26px; }}
nav.toc {{ width:230px; flex:0 0 230px; position:sticky; top:20px; max-height:92vh; overflow:auto;
  font-size:0.82rem; border-right:1px solid var(--border); padding-right:16px; }}
.toc-layer {{ margin-bottom:16px; }}
.toc-layer-link {{ display:block; font-weight:700; border-left:4px solid; padding-left:8px;
  color:var(--text-primary); text-decoration:none; margin-bottom:4px; }}
nav.toc ul {{ list-style:none; margin:2px 0 0; padding-left:10px; }}
nav.toc li.toc-schema > a {{ color:var(--text-muted); text-transform:uppercase; font-size:0.72rem; letter-spacing:.04em; }}
nav.toc a {{ color:var(--text-secondary); text-decoration:none; display:block; padding:2px 0; }}
nav.toc a:hover {{ color:var(--accent); }}
main.doc {{ flex:1 1 auto; min-width:0; }}
.cat-layer-title {{ border-left:5px solid; padding-left:10px; margin:30px 0 12px; font-size:1.3rem; scroll-margin-top:16px; }}
.cat-layer-sub {{ color:var(--text-muted); font-weight:400; font-size:0.9rem; }}
.cat-schema {{ color:var(--text-muted); font-size:0.8rem; text-transform:uppercase; letter-spacing:.05em;
  margin:20px 0 8px; scroll-margin-top:16px; }}
details.cat-table {{ background:var(--surface-1); border:1px solid var(--border); border-radius:8px;
  margin-bottom:10px; padding:0; scroll-margin-top:16px; }}
details.cat-table summary {{ padding:11px 16px; cursor:pointer; list-style:none; display:flex; gap:12px;
  align-items:baseline; flex-wrap:wrap; }}
details.cat-table summary::-webkit-details-marker {{ display:none; }}
details.cat-table[open] summary {{ border-bottom:1px solid var(--border); }}
.cat-table-name {{ font-weight:600; font-family:ui-monospace,Consolas,monospace; font-size:0.92rem; }}
.cat-table-comment {{ color:var(--text-muted); font-size:0.85rem; }}
.cat-table-body {{ padding:12px 16px 18px; }}
.badges {{ margin-bottom:10px; }}
.pill {{ display:inline-block; background:var(--pill-bg); border:1px solid var(--border); border-radius:20px;
  padding:2px 10px; font-size:0.72rem; margin:0 6px 6px 0; color:var(--text-secondary); }}
.pill-src {{ color:var(--accent); border-color:var(--accent); }}
.pill-warn {{ color:#d03b3b; border-color:#d03b3b; }}
.pill-gov {{ color:#8a6d1a; border-color:#c9a227; }}
table.col-table {{ width:100%; border-collapse:collapse; font-size:0.84rem; margin:6px 0; }}
table.col-table th {{ text-align:left; color:var(--text-muted); font-weight:600; font-size:0.72rem;
  text-transform:uppercase; letter-spacing:.03em; padding:5px 8px; border-bottom:1px solid var(--border); }}
table.col-table td {{ padding:5px 8px; border-bottom:1px solid var(--grid); }}
.mono {{ font-family:ui-monospace,Consolas,monospace; }}
.muted {{ color:var(--text-muted); }}
.lineage-text {{ font-size:0.84rem; margin-top:6px; }}
.lineage-text code {{ background:var(--code-bg); padding:1px 5px; border-radius:4px; }}
.sample-note {{ margin-top:10px; font-size:0.8rem; color:var(--text-muted); }}
.sample-note code {{ background:var(--code-bg); padding:1px 5px; border-radius:4px; }}
.gov-list {{ font-size:0.82rem; margin:6px 0; padding-left:18px; }}
.gap-card {{ border-color:#d03b3b !important; }}
footer.pagefoot {{ text-align:center; color:var(--text-muted); font-size:0.78rem; padding:24px; }}
@media (max-width: 900px) {{
  .layout {{ flex-direction:column; }}
  nav.toc {{ width:100%; flex:none; position:static; max-height:none; border-right:none; border-bottom:1px solid var(--border); padding-bottom:12px; }}
}}
</style>
</head>
<body>
<header class="top">
  <h1>acme Sales Lakehouse — Data Model</h1>
  <p>Generated {NOW} directly from the live Unity Catalog metastore on <code>{WORKSPACE_HOST}</code> —
  table/column inventory via <code>system.information_schema</code>, Bronze→Silver lineage via the live
  <code>acme_bronze.cfg.layer_mappings</code> config table, Gold→Products lineage via live
  <code>SHOW CREATE TABLE</code> on each view, remaining edges from the deployed pipeline code
  (<code>pipelines/silver_dlt.py</code>, <code>pipelines/gold_dlt.py</code>, <code>ml/build_features.py</code>,
  <code>ai/provision_vector_search.py</code>, <code>agents/vector_content.py</code>).</p>
  <div class="links">
    <a href="DATA_CATALOG.html">→ Interactive lineage diagram (DATA_CATALOG.html)</a>
    <a href="DATA_MODEL.md">→ Plain-text version (DATA_MODEL.md)</a>
  </div>
  <div class="stats">
    <div class="stat"><b>{len(TABLES)}</b><span>tables / views</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[B]}+9</b><span>bronze (+ audit/cfg)</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[S]}</b><span>silver</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[G]}</b><span>gold</span></div>
    <div class="stat"><b>{TABLE_COUNT_BY_LAYER[P]}</b><span>products</span></div>
    <div class="stat"><b>{len(EDGES)}</b><span>lineage edges</span></div>
    <div class="stat"><b>{TOTAL_ROWS:,}</b><span>live rows (sum)</span></div>
  </div>
</header>
<div class="layout">
  <nav class="toc">{TOC_HTML}</nav>
  <main class="doc">
    {DOC_BODY}
  </main>
</div>
<footer class="pagefoot">acme Sales Lakehouse · data/exports/excel/*.xlsx has the full 500-row samples per table, layer by layer · docs/DATA_CATALOG.html has the clickable lineage diagram</footer>
</body>
</html>'''

with open(OUT_MODEL_HTML, "w", encoding="utf-8") as f:
    f.write(MODEL_PAGE)
print(f"Wrote {OUT_MODEL_HTML} ({len(MODEL_PAGE)} bytes)")
