#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate docs/index.html — the tabbed documentation site — from the current docs/*.md
(plus top-level JUSTIFICATION_NOTES-style) files. Do not hand-edit docs/index.html; it drifts
stale the moment any source .md changes (see CLAUDE.md rule 7 and the 2026-08-14 SESSION_NOTES
entry — this is the fix for exactly that problem). Re-run this after editing any doc in TABS
below, or after adding a new one.

Uses the `markdown` package (already in .venv) with tables + fenced_code extensions, then
post-processes ```mermaid fences into <pre class="mermaid"> (mermaid.js only auto-renders that
class, not the `language-mermaid` class fenced_code emits by default) and lightly renders
`- [ ]` / `- [x]` checklist items, since standard Markdown doesn't.
"""
import html as H
import os
import re

import markdown

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, ".."))
DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(DOCS, "index.html")

# (tab label, path relative to repo root)
TABS = [
    ("Architecture", "docs/ARCHITECTURE.md"),
    ("AI Agents Overview", "docs/AI_AGENTS_OVERVIEW.md"),
    ("Code Graph", "docs/CODE_GRAPH.md"),
    ("Data Vault PIT Bridge", "docs/DATA_VAULT_PIT_BRIDGE.md"),
    ("Justification Notes", "docs/JUSTIFICATION_NOTES.md"),
    ("Replication Patterns", "docs/REPLICATION_PATTERNS.md"),
    ("Traceability Matrix", "docs/TRACEABILITY_MATRIX.md"),
    ("Agent Reliability Guardrails", "docs/AGENT_RELIABILITY_GUARDRAILS.md"),
    ("DASF Alignment", "docs/DASF_ALIGNMENT.md"),
    ("Governance DQ Ingestion AI Audit", "docs/GOVERNANCE_DQ_INGESTION_AI_AUDIT.md"),
    ("Databricks Governance Ebook Comparison", "docs/DATABRICKS_GOVERNANCE_EBOOK_COMPARISON.md"),
    ("Ralph Loop", "docs/ralph_loop.md"),
    ("Demo Runbook", "docs/DEMO_RUNBOOK.md"),
    ("Gap Analysis", "docs/GAP_ANALYSIS.md"),
    ("Session Notes", "docs/SESSION_NOTES.md"),
    ("Jd Alignment", "docs/JD_ALIGNMENT.md"),
]

CHECKLIST_RE = re.compile(r"^(\s*)-\s\[( |x|X)\]\s+", re.MULTILINE)


def render_checklists(text):
    def repl(m):
        box = "☑" if m.group(2).lower() == "x" else "☐"
        return f"{m.group(1)}- {box} "
    return CHECKLIST_RE.sub(repl, text)


def md_to_html(md_text):
    body = markdown.markdown(
        render_checklists(md_text),
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    # fenced_code emits <pre><code class="language-mermaid">...; mermaid.js only auto-renders
    # elements carrying class="mermaid" directly, so unwrap those specific blocks.
    def mermaid_sub(m):
        inner = H.unescape(m.group(1))
        return f'<pre class="mermaid">{inner}</pre>'
    body = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        mermaid_sub, body, flags=re.DOTALL,
    )
    return body


def slugify(label):
    return "".join(c for c in label.lower().replace(" ", "-") if c.isalnum() or c == "-")


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>acme Sales Lakehouse — Documentation</title>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({startOnLoad:true, theme:'dark', themeVariables:{fontFamily:'IBM Plex Sans'}});
</script>
<style>
:root{
  --bg:#111315; --plate:#1A1D21; --line:#2B3037; --txt:#C6CBD1; --bright:#F5F6F7;
  --dim:#7D848C; --acc:#1F6F4F; --acc2:#3FA378; --cool:#5C7A93;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font:15.5px/1.65 "IBM Plex Sans",sans-serif;padding:0 0 70px}
.wrap{max-width:1080px;margin:0 auto;padding:0 28px}
header{border-bottom:1px solid var(--line);padding:38px 0 24px;margin-bottom:0}
.eyebrow{font:600 12px "IBM Plex Mono";letter-spacing:.18em;color:var(--acc2);text-transform:uppercase;margin-bottom:8px}
header h1{font:800 40px/1.05 "Saira Condensed";color:var(--bright);text-transform:uppercase}
.tabs{display:flex;gap:8px;margin:22px 0 0;flex-wrap:wrap;position:sticky;top:0;
  background:rgba(17,19,21,.96);backdrop-filter:blur(4px);padding:12px 0 0;z-index:9}
.tabs button{background:var(--plate);border:1px solid var(--line);color:var(--txt);padding:9px 18px;
  border-radius:6px 6px 0 0;font:600 13.5px "IBM Plex Sans";cursor:pointer}
.tabs button[aria-selected="true"]{background:#0E1114;border-bottom-color:#0E1114;color:var(--acc2);border-top:2px solid var(--acc)}
.tabpanel{display:none;background:#0E1114;border:1px solid var(--line);border-radius:0 8px 8px 8px;padding:26px 30px 34px}
.tabpanel.show{display:block}
.srcfile{font:500 11px "IBM Plex Mono";color:var(--dim);margin-bottom:14px;letter-spacing:.05em}
.tabpanel h1{font:700 30px/1.15 "Saira Condensed";color:var(--bright);text-transform:uppercase;margin:6px 0 14px}
.tabpanel h2{font:700 22px/1.15 "Saira Condensed";color:var(--bright);text-transform:uppercase;
  margin:26px 0 10px;padding-top:16px;border-top:1px solid var(--line)}
.tabpanel h3{font:600 16px "IBM Plex Sans";color:var(--bright);margin:18px 0 8px}
.tabpanel p{margin:9px 0;max-width:92ch}
.tabpanel ul,.tabpanel ol{margin:9px 0 9px 24px}
.tabpanel li{margin:4px 0}
.tabpanel a{color:var(--acc2)}
.tabpanel strong{color:var(--bright)}
code{font:13px "IBM Plex Mono";color:var(--acc2);background:#15181C;border:1px solid #232A33;
  border-radius:3px;padding:1px 5px}
pre{background:#15181C;border:1px solid var(--line);border-radius:6px;padding:14px 16px;
  font:12.5px/1.55 "IBM Plex Mono";color:#B7C6D3;overflow-x:auto;margin:12px 0}
pre code{background:none;border:none;padding:0;color:inherit}
pre.mermaid{background:#15181C;text-align:center}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;display:block;overflow-x:auto}
th{font:600 11px "IBM Plex Mono";letter-spacing:.1em;text-transform:uppercase;color:var(--dim);
  text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:8px 10px;border-bottom:1px solid #232A33;vertical-align:top}
td:first-child{color:var(--bright)}
.genmeta{font:500 11px "IBM Plex Mono";color:var(--dim);margin-top:10px}
@media print{
  body{background:#fff;color:#222}
  .tabs{display:none}
  .tabpanel{display:block;border-color:#bbb;background:#fff;page-break-before:always}
  .tabpanel h1,.tabpanel h2,.tabpanel h3,td:first-child,.tabpanel strong{color:#000}
}
</style>
</head>
<body>
<header><div class="wrap">
  <div class="eyebrow">acme &middot; Sales Lakehouse on Azure Databricks &middot; Project Documentation</div>
  <h1>Documentation</h1>
  <p class="genmeta">Generated {gen_date} by scripts/generate_docs_site.py from the docs/*.md files below &mdash; do not hand-edit this file, edit the source .md and re-run the generator.</p>
</div></header>
<div class="wrap">
"""

TAIL = """
</div>
<script>
function tab(btn,id){
  btn.parentElement.querySelectorAll('button').forEach(b=>b.setAttribute('aria-selected','false'));
  btn.setAttribute('aria-selected','true');
  document.querySelectorAll('.tabpanel').forEach(p=>p.classList.remove('show'));
  document.getElementById(id).classList.add('show');
}
</script>
</body>
</html>
"""


def main():
    from datetime import date

    tab_buttons = []
    panels = []
    for i, (label, rel_path) in enumerate(TABS):
        full_path = os.path.join(ROOT, rel_path.replace("/", os.sep))
        panel_id = f"p{i}"
        selected = "true" if i == 0 else "false"
        tab_buttons.append(
            f'<button role="tab" aria-selected="{selected}" onclick="tab(this,\'{panel_id}\')">{H.escape(label)}</button>'
        )
        if not os.path.exists(full_path):
            print(f"WARNING: missing {full_path}, skipping tab '{label}'")
            body_html = f"<p><em>Source file not found: {H.escape(rel_path)}</em></p>"
        else:
            with open(full_path, encoding="utf-8-sig") as f:
                md_text = f.read()
            body_html = md_to_html(md_text)
        show_cls = " show" if i == 0 else ""
        panels.append(
            f'<div id="{panel_id}" class="tabpanel{show_cls}" role="tabpanel">\n'
            f'<p class="srcfile">source: {H.escape(rel_path)}</p>\n'
            f"{body_html}\n</div>"
        )

    out = (
        HEAD.replace("{gen_date}", date.today().isoformat())
        + '<div class="tabs" role="tablist">' + "".join(tab_buttons) + "</div>\n"
        + "\n".join(panels)
        + TAIL
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {OUT} ({len(TABS)} tabs, {len(out)} bytes)")


if __name__ == "__main__":
    main()
