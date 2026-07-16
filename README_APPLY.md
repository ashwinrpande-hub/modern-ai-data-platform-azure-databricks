# DV2.0 + PIT/Bridge update — 2026-07-11

Drop these 12 files into the repo root (paths match). New: docs/DATA_VAULT_PIT_BRIDGE.md.
All others are surgical edits. Verified: py_compile (4 scripts), YAML parse (14 sources),
SQL balance, generator run (5000 orders -> 3478 LIPS -> 2767 VBRP, zero orphans).

Commit suggestion: "DV2.0 methodology: pit_customer + bridge_order_fulfillment in Gold;
SAP LIPS/VBRP lifecycle (config-driven); validate checks 13-14; decision #5 revised, #10-11 added"
