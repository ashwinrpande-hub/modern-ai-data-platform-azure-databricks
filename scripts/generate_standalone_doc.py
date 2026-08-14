#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render one docs/*.md file as a standalone, single-page styled HTML document — for docs that
deserve their own shareable link rather than living only as a tab inside docs/index.html.

Reuses generate_docs_site.py's markdown->HTML conversion (checklist rendering, mermaid-fence
unwrapping) instead of re-implementing it, so the two outputs never drift apart in how they
render the same Markdown. Do not hand-edit the generated .html; re-run this after editing the
source .md.

Usage: python scripts/generate_standalone_doc.py docs/AI_AGENTS_OVERVIEW.md
"""
import html as H
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_docs_site import md_to_html  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, ".."))

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — acme Sales Lakehouse</title>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({{startOnLoad:true, theme:'dark', themeVariables:{{fontFamily:'IBM Plex Sans'}}}});
</script>
<style>
:root{{
  --bg:#111315; --plate:#1A1D21; --line:#2B3037; --txt:#C6CBD1; --bright:#F5F6F7;
  --dim:#7D848C; --acc:#1F6F4F; --acc2:#3FA378; --cool:#5C7A93;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font:15.5px/1.65 "IBM Plex Sans",sans-serif;padding:0 0 70px}}
.wrap{{max-width:900px;margin:0 auto;padding:0 28px}}
header{{border-bottom:1px solid var(--line);padding:38px 0 24px;margin-bottom:26px}}
.eyebrow{{font:600 12px "IBM Plex Mono";letter-spacing:.18em;color:var(--acc2);text-transform:uppercase;margin-bottom:8px}}
header h1{{font:800 36px/1.1 "Saira Condensed";color:var(--bright);text-transform:uppercase}}
.genmeta{{font:500 11px "IBM Plex Mono";color:var(--dim);margin-top:10px}}
h1{{font:700 28px/1.15 "Saira Condensed";color:var(--bright);text-transform:uppercase;margin:6px 0 14px}}
h2{{font:700 21px/1.15 "Saira Condensed";color:var(--bright);text-transform:uppercase;
  margin:30px 0 10px;padding-top:18px;border-top:1px solid var(--line)}}
h3{{font:600 16px "IBM Plex Sans";color:var(--bright);margin:18px 0 8px}}
p{{margin:9px 0;max-width:88ch}}
ul,ol{{margin:9px 0 9px 24px}}
li{{margin:4px 0}}
a{{color:var(--acc2)}}
strong{{color:var(--bright)}}
code{{font:13px "IBM Plex Mono";color:var(--acc2);background:#15181C;border:1px solid #232A33;
  border-radius:3px;padding:1px 5px}}
pre{{background:#15181C;border:1px solid var(--line);border-radius:6px;padding:14px 16px;
  font:12.5px/1.55 "IBM Plex Mono";color:#B7C6D3;overflow-x:auto;margin:12px 0}}
pre code{{background:none;border:none;padding:0;color:inherit}}
pre.mermaid{{background:#15181C;text-align:center}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:13.5px;display:block;overflow-x:auto}}
th{{font:600 11px "IBM Plex Mono";letter-spacing:.1em;text-transform:uppercase;color:var(--dim);
  text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}}
td{{padding:8px 10px;border-bottom:1px solid #232A33;vertical-align:top}}
td:first-child{{color:var(--bright)}}
@media print{{
  body{{background:#fff;color:#222}}
  h1,h2,h3,td:first-child,strong{{color:#000}}
}}
</style>
</head>
<body>
<header><div class="wrap">
  <div class="eyebrow">acme &middot; Sales Lakehouse on Azure Databricks</div>
  <h1>{title}</h1>
  <p class="genmeta">Generated {gen_date} by scripts/generate_standalone_doc.py from {src} &mdash; do not hand-edit this file, edit the source .md and re-run the generator.</p>
</div></header>
<div class="wrap">
{body}
</div>
</body>
</html>
"""


def render(md_rel_path, title=None):
    full_path = os.path.join(ROOT, md_rel_path.replace("/", os.sep))
    with open(full_path, encoding="utf-8-sig") as f:
        md_text = f.read()
    body_html = md_to_html(md_text)
    if title is None:
        title = os.path.splitext(os.path.basename(md_rel_path))[0].replace("_", " ").title()
    out_path = os.path.splitext(full_path)[0] + ".html"
    out = PAGE.format(
        title=H.escape(title), gen_date=date.today().isoformat(),
        src=H.escape(md_rel_path), body=body_html,
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {out_path} ({len(out)} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_standalone_doc.py docs/SOME_DOC.md [Title]")
        sys.exit(1)
    render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
