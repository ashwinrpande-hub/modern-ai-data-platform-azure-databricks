# Lineage & Docs agent (nightly)
Reads cfg.layer_mappings + UC system tables (system.access.table_lineage) ->
regenerates docs/CODE_GRAPH.md mermaid diagrams + per-product lineage sections.
Token rule: only regenerate sections whose mappings changed (version diff).
