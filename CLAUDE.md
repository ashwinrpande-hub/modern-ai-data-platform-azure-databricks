# CLAUDE.md — session guide (token-optimized)

Rules for any Claude Code session in this repo:
1. **Read only what the task needs.** Each domain has its own .md: `agents/*.md`, `docs/*.md`. Never load the whole repo.
2. **Only touch code that is necessary.** Config-driven design means most changes are YAML/config-table rows, not code.
3. **Never assume**: if a mapping, source system, or schema is unknown, ask the user interactively before writing code.
4. **Summarize long sessions** into `docs/SESSION_NOTES.md` (append-only, dated) before context grows large.
5. Source-of-truth order: config tables > YAML in `config/` > code defaults.
6. All new ingestion = a row in `config/replication_sources.yaml` + the matching template in `ingestion/templates/`. Do not fork templates.

## Map of the repo (read instead of scanning)
- Replication patterns → `docs/REPLICATION_PATTERNS.md`
- Pipeline graph → `docs/CODE_GRAPH.md`
- Decisions + alternatives → `docs/JUSTIFICATION_NOTES.md`
- Agents specs → `agents/`
