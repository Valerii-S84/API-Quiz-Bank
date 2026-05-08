# Roadmap Evidence Register

Generated/updated: 2026-05-08

This register is the current phase closure ledger for `docs/14_roadmap.md`.
`Done (local)` means the gate is supported by committed local artifacts and commands.
It does not mean pilot, beta or production readiness unless an external environment and
operation evidence are listed.

| Phase | Status | Evidence artifacts | Verification command | Limitation |
|---|---|---|---|---|
| Phase 0 Documentation Foundation | Done (local) | `CONSTITUTION.md`, `docs/00_vision.md` through `docs/19_privacy_compliance.md`, `.agent/AGENTS.md` | `rg -n '\[FILL_PER_PROJECT\]' .agent/project` returns no matches; unittest baseline passes | Docs are local source of truth, not reviewed external launch approval. |
| Phase 1 Source Governance | Done (local) | `data/manifests/file_inventory.csv`, `data/manifests/source_checksums.csv`, `data/manifests/import_manifest.yml`, `data/parser_profiles/parser_profiles.yml`, `docs/16_source_onboarding_playbook.md`, `QuizBank/README.md`, `tests/test_corpus_inventory_invariants.py` | `python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts`; `python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank`; `python3 -m unittest tests.test_corpus_inventory_invariants tests.test_generated_artifacts_invariants` | Corpus remains all draft for production workflow. |
| Phase 2 Canonical Data / Import | Done (local) | `schemas/canonical_quiz_item.schema.json`, `data/imports/control_sample_items.jsonl`, `data/registry/source_registry.csv`, `reports/imports/control_sample_import.json`, `reports/imports/control_sample_postgresql_load_plan.json`, `tests/test_import_validation.py`, `tests/test_generated_artifacts_invariants.py` | `python3 tools/quizbank_import_sample.py`; `python3 tools/quizbank_postgresql_load_plan.py`; `python3 -m unittest tests.test_import_validation tests.test_generated_artifacts_invariants tests.test_postgresql_load_plan` | Dry-run sample only; no production import batch. |
| Phase 3 Database and API Core | Done (MVP-local) | `database/migrations/001_create_mvp_runtime.sql`, `database/migrations/002_add_api_credentials.sql`, `database/postgresql/001_create_runtime.sql`, `database/postgresql/002_add_import_contract.sql`, `src/quizbank_mvp/`, `src/quizbank_mvp/taxonomy.py`, `api/openapi.yaml`, `tests/test_mvp_runtime.py`, `tests/test_contract_schema_invariants.py`, `tests/test_postgresql_contract.py` | `PYTHONPATH=src python3 tools/run_mvp_demo.py`; `python3 -m unittest tests.test_mvp_runtime tests.test_contract_schema_invariants tests.test_postgresql_contract` | SQLite is accepted only as MVP equivalent DB model, not production PostgreSQL; PostgreSQL files are contract seed, not a live production DB. |
| Phase 4 Selection and Controlled Delivery | Done (MVP-local) | `src/quizbank_mvp/selection.py`, `tests/test_mvp_runtime.py`, `tests/test_reports_selection_invariants.py`, `reports/delivery/control_selection_report.json`, `reports/delivery/control_approved_selection_report.json`, `reports/delivery/control_repeat_policy_report.json` | `python3 tools/quizbank_selection_smoke.py`; `python3 -m unittest tests.test_mvp_runtime tests.test_reports_selection_invariants`; unittest status/repeat/quota/auth/filter tests | Delivery is local API/TestClient proof, not live Telegram/public traffic. |
| Phase 5 Admin/Billing/Analytics MVP | Done (MVP-local) | `src/quizbank_mvp/cli.py`, `data/billing/plan_catalog.json`, audit table in migration, audited manual entitlement grant, entitlement/quota tables, `reports/coverage/corpus_coverage.json`, delivery reports | `PYTHONPATH=src python3 -m quizbank_mvp.cli --help`; `python3 tools/quizbank_gap_map.py --quizbank-dir QuizBank --write-artifacts`; unittest audit/entitlement/quota/plan-catalog tests | Billing is manual entitlement/quota model; no payment provider integration. |
| Phase 6 Stanford Demo Package | Done (local) | `docs/13_stanford_presentation_outline.md`, `tools/run_mvp_demo.py`, `tests/test_demo_package.py`, `reports/imports/control_sample_import.json`, `reports/coverage/corpus_coverage.json`, `reports/delivery/`, `data/billing/plan_catalog.json`, this evidence register | `PYTHONPATH=src python3 tools/run_mvp_demo.py`; `python3 -m unittest tests.test_demo_package` | Demo is local and artifact-backed; no real external send is claimed. |
| Phase 7 Closed Pilot Hardening | Done (local-only/internal pilot) | `docs/observability_contract.md`, `runbooks/backup_restore.md`, `runbooks/incident_response.md`, `runbooks/support_triage.md`, `runbooks/rollback.md`, `runbooks/server_deploy.md`, `docs/18_telegram_delivery_playbook.md`, `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md`, `reports/pre_pilot/telegram_dry_run_readiness_2026-05-08.md`, `reports/pre_pilot/telegram_secret_wiring_2026-05-08.md`, `reports/pre_pilot/public_api_key_route_evidence_2026-05-08.md`, `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md`, `reports/roadmap/phase_7_9_gate_matrix.md`, `reports/roadmap/phase_7_10_closure_decision_2026-05-08.md`, `transition-consumer-status` CLI and tests | VPS checkout-only sync, health, readiness, smoke, backup, restore drill, lifecycle, delivery, repeat guard, quota, Telegram dry-run, Telegram secret wiring and protected public route evidence; `python3 -m unittest discover -s tests -p "test_*.py"` | Telegram real send, external dashboard, public support-channel execution and production-like managed restore are not present. |
| Phase 8 Public Beta Readiness | Closed decision: NO-GO public beta | `docs/observability_contract.md`, `runbooks/release_rollback.md`, `runbooks/rollback.md`, `runbooks/incident_response.md`, `runbooks/support_triage.md`, `policies/privacy_notice_baseline.md`, `reports/compliance/legal_review_record.md`, `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md`, `reports/pre_pilot/public_api_key_route_evidence_2026-05-08.md`, `reports/rollback/local_rollback_tabletop_2026-05-08.md`, `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md`, `reports/roadmap/phase_7_9_gate_matrix.md`, `reports/roadmap/phase_7_10_closure_decision_2026-05-08.md`, quota/entitlement runtime tests | Protected public route smoke; `python3 -m unittest discover -s tests -p "test_*.py"`; `git diff --check` | Public beta is explicitly not approved: no beta legal/privacy approval, public support/abuse path, public traffic evidence or beta alerting dashboard. |
| Phase 9 Production Readiness | Closed decision: NO-GO production | `.github/workflows/ci.yml`, `database/migrations/001_create_mvp_runtime.sql`, `docs/10_operations.md`, `docs/08_security_threat_model.md`, `docs/observability_contract.md`, `runbooks/backup_restore.md`, `runbooks/incident_response.md`, `runbooks/rollback.md`, `runbooks/release_rollback.md`, `reports/rollback/local_rollback_tabletop_2026-05-08.md`, `reports/roadmap/external_evidence_blockers.md`, `reports/roadmap/phase_7_9_gate_matrix.md`, `reports/roadmap/phase_7_10_closure_decision_2026-05-08.md` | `python3 -m unittest discover -s tests -p "test_*.py"`; `git diff --check` | Production is explicitly not approved: no production deployment, monitored backups, production-like restore drill, dashboard, incident exercise, rollback execution or production legal/privacy approval. |
| Phase 10 Pilot Execution Package | Done (local package) | `docs/pilot_environment_requirements.md`, `docs/pilot_launch_contract.md`, `runbooks/pilot_launch_runbook.md`, `runbooks/telegram_controlled_send_runbook.md`, `runbooks/backup_restore_operational_runbook.md`, `runbooks/monitoring_alerts_runbook.md`, `reports/roadmap/pilot_execution_checklist.md`, `reports/roadmap/pilot_go_no_go_matrix.md`, `reports/roadmap/phase_10_evidence_register.md`, `reports/roadmap/phase_7_10_closure_decision_2026-05-08.md` | `python3 -m unittest discover -s tests -p "test_*.py"`; `git diff --check` | Package, local-only evidence and protected route smoke are closed; unauthenticated public access and Telegram real send remain not approved/not done. |

## Baseline Evidence

Verified at start of this execution pass:

```text
python3 -m unittest discover -s tests -p 'test_*.py' -> OK, 26 tests before changes
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank -> active_bank_files=115 active_rows=30974 violations=0
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts -> active_bank_files=115 active_rows=30974
python3 tools/quizbank_import_sample.py -> dry-run import passed: sample_control_001
python3 tools/quizbank_gap_map.py -> levels and theme coverage printed
python3 tools/quizbank_selection_smoke.py -> selection smoke passed: no eligible item
PYTHONPATH=src python3 tools/run_mvp_demo.py -> health, ready, next_item, delivery_log, repeat_denial and quota_denial shown
```

## Current Verification

Verified after this execution pass:

```text
python3 -m unittest discover -s tests -p "test_*.py" -> OK, 62 tests
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank -> active_bank_files=115 active_rows=30974 violations=0
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts -> active_bank_files=115 active_rows=30974
python3 tools/quizbank_import_sample.py -> dry-run import passed: sample_control_001
python3 tools/quizbank_postgresql_load_plan.py -> PostgreSQL load plan written: reports/imports/control_sample_postgresql_load_plan.json
python3 tools/quizbank_emit_standards.py -> wrote schema, taxonomy and OpenAPI seed artifacts
PYTHONPATH=src python3 tools/run_mvp_demo.py -> health, ready, next_item, delivery_log, repeat_denial and quota_denial shown
GET /v1/levels and GET /v1/topics -> covered by tests/test_mvp_runtime.py and api/openapi.yaml
Phase 4 selection controls -> level/theme filtering, consumer scope denials, status filtering, repeat denial, quota denial and delivery log creation covered by tests/test_mvp_runtime.py plus reports/delivery/*.json
Phase 5 admin/billing/analytics -> plan catalog seed, audited manual entitlement grant, quota usage, status transition audit and coverage report covered by tests and reports/coverage/corpus_coverage.json
Phase 6 demo package -> tools/run_mvp_demo.py prints source_governance, canonical_validation, analytics_snapshot, billing_plan_catalog, next_item, delivery_log, repeat_denial, quota_denial and billing_usage_audit
PYTHONPATH=src python3 -m quizbank_mvp.cli --help -> transition-consumer-status listed
PYTHONPATH=src python3 tools/run_pre_pilot_dry_run.py -> lifecycle, delivery, repeat and quota evidence shown
local SQLite restore drill command in reports/restore/mvp_sqlite_restore_drill_2026-05-08.md -> database_is_ready=True
Phase 10 package docs -> pilot environment requirements, launch contract, controlled send, backup/restore, monitoring and go/no-go protocols recorded
VPS checkout-only sync -> /opt/api-quiz-bank fast-forwarded 61e32d7 to a86d625 without container restart; health/ready/smoke/backup/restore drill OK
VPS lifecycle/delivery evidence -> active delivery 200, suspended denial 403, blocked denial 403, repeat guard 404, quota denial 429; post-run restore drill OK
Telegram dry-run -> endpoint, adapter payload shape, log contract, stop conditions and VPS dry-run result recorded; real send not approved/not done
Telegram secret wiring -> current token stored in root-only VPS secret file and mounted by path into container; value not committed or printed
Protected public route -> api.valerchik.de no-key health 401, authorized health/ready 200, no-key delivery 401, authorized entitlement control 403
git diff --check -> no whitespace errors
```

Additional Phase 7-9 local evidence recorded in this pass:

```text
transition-consumer-status CLI added and covered by runtime test -> suspended consumer receives CONSUMER_NOT_ACTIVE before delivery creation
local pre-pilot dry run -> active->suspended->blocked->active lifecycle, allowed delivery, repeat denial and quota denial
local rollback tabletop -> consumer containment, repeat containment, quota containment and local DB/code rollback paths recorded
observability contract -> health, readiness, lifecycle, delivery, denial and rollback signal names recorded
external evidence blockers -> pilot, beta and production blockers listed separately from local evidence
Phase 10 pilot execution package -> package remains local; later local-only VPS evidence is linked separately under Phase 7
local SQLite restore drill -> database_is_ready=True, backup_sha256=da08cfb61574197b75bff75b9300b20e1327c55193c9019dad033f49ad0d0dab, restore_size_bytes=77824
Phase 7-9 gate matrix -> local gates separated from blocked external gates
local-only VPS pilot evidence -> environment id `local-only-vps`, owner boundary, `/opt/api-quiz-bank`, active DB path, `/var/backups/api-quiz-bank`, loopback bind, restart count and ops cadence recorded
Phase 7-10 closure decision -> Phase 7 GO local-only/internal, Phase 8 NO-GO public beta, Phase 9 NO-GO production, Phase 10 Done local package
```

## Closure Rule

Do not change a phase to `Done` unless its evidence artifact and verification command are both
listed here. For Phase 7-9, local documentation alone is insufficient.
