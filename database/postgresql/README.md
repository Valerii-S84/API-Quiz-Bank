# PostgreSQL Runtime Contract

This directory holds the production-oriented PostgreSQL schema contract for API Quiz Bank.

## Current Boundary

- `database/migrations/` remains the local SQLite MVP runtime path used by the committed FastAPI demo and tests.
- `database/postgresql/001_create_runtime.sql` defines the production runtime seed tables aligned with the MVP delivery domain.
- `database/postgresql/002_add_import_contract.sql` adds the governed import path required before PostgreSQL can be treated as the operational source of truth.
- `database/postgresql/003_add_runtime_delivery_evidence.sql` through `015_optimize_selection_queue_claim_available_index.sql` mirror runtime evidence, admin, schedule, visual delivery, image-quality policy, next-route indexes, content scope and queue-first precomputed selection contracts.
- `src/quizbank_mvp/database_connection.py` contains the PostgreSQL adapter boundary; `QUIZBANK_DATABASE_URL=postgresql://...` selects the PostgreSQL runtime path.

## Production Import Path

The PostgreSQL contract preserves this minimum traceability chain:

```text
sources
  -> import_batches
  -> import_batch_items
  -> quiz_items
  -> deliveries
```

Import validation evidence is stored in `import_validation_results`. A committed import batch must keep the source checksum, parser profile, detected row count, accepted/rejected candidate counts, report URI, timestamps and operator identity.

## Local Contract Smoke

Run the local execution proof with:

```bash
python3 tools/run_postgresql_contract_smoke.py
```

The smoke uses an ephemeral `postgres:16-alpine` Docker container, applies all committed `database/postgresql/*.sql` migrations, loads `reports/imports/control_sample_postgresql_load_plan.json`, then writes `reports/imports/control_sample_postgresql_smoke.json`.

## Unit Contract Gates

Run the dependency-light PostgreSQL boundary checks with:

```bash
python3 -m unittest tests.test_database_backend_contract tests.test_postgresql_contract tests.test_postgresql_load_plan tests.test_postgresql_smoke_report
```

## Not Proven By This Directory

These SQL files do not prove a production database is running. Production readiness still requires:

- migration execution against a managed PostgreSQL environment;
- backup and restore drill evidence for PostgreSQL;
- runtime application wiring against a real managed PostgreSQL instance;
- monitored migration and rollback procedures;
- secret-managed credentials outside the repository.
