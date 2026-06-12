# DQ Root-Cause agent
Trigger: dq_results row with met_threshold=false.
Steps: pull failed dimension + sample rejects -> diff against last green batch ->
correlate with batch_log (volume spikes), source_registry (recent changes), lineage ->
produce RCA note: suspected source, first bad batch_id, blast radius (downstream Gold tables),
suggested fix. Post to #data-quality, attach to steward ticket. Genie space used for ad-hoc
"why did completeness drop" follow-ups by stewards.
