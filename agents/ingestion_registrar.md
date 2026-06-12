# Ingestion Registrar agent
Trigger: PR adding a row to config/replication_sources.yaml.
Validates: pattern in allowed set, PK present, expectations parse, target naming convention,
region in {EUROPE, AMERICAS, EMEA, GLOBAL}. Dry-runs template render. Comments validation
report on the PR. On merge: calls deploy.py --register-source <name>.
This is what lets ANY technical person onboard a source safely.
