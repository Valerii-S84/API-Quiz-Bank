# Roadmap Evidence Register

Generated/updated: 2026-05-08

This register is the current phase closure ledger for `docs/14_roadmap.md`.
`Done (local)` means the gate is supported by committed local artifacts and commands.
It does not mean pilot, beta or production readiness unless an external environment and
operation evidence are listed.

| Phase | Status | Evidence artifacts | Verification command | Limitation |
|---|---|---|---|---|
| Phase 0 Documentation Foundation | Done (local) | `CONSTITUTION.md`, `docs/00_vision.md` through `docs/19_privacy_compliance.md`, `.agent/AGENTS.md` | `rg -n '\[FILL_PER_PROJECT\]' .agent/project` returns no matches; unittest baseline passes | Docs are local source of truth, not reviewed external launch approval. |
| Phase 1 Source Governance | Done (local) | `data/manifests/file_inventory.csv`, `data/manifests/source_checksums.csv`, `data/manifests/import_manifest.yml`, `QuizBank/README.md` | `python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts`; `python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank` | Corpus remains all draft for production workflow. |
| Phase 2 Canonical Data / Import | Done (local) | `schemas/canonical_quiz_item.schema.json`, `data/imports/control_sample_items.jsonl`, `reports/imports/control_sample_import.json`, `tests/test_import_validation.py` | `python3 tools/quizbank_import_sample.py`; `python3 -m unittest discover -s tests -p "test_*.py"` | Dry-run sample only; no production import batch. |
| Phase 3 Database and API Core | Done (MVP-local) | `database/migrations/001_create_mvp_runtime.sql`, `src/quizbank_mvp/`, `api/openapi.yaml`, `tests/test_mvp_runtime.py` | `PYTHONPATH=src python3 tools/run_mvp_demo.py`; unittest runtime tests | SQLite is accepted only as MVP equivalent DB model, not production PostgreSQL. |
| Phase 4 Selection and Controlled Delivery | Done (MVP-local) | `src/quizbank_mvp/selection.py`, `reports/delivery/control_selection_report.json`, `reports/delivery/control_approved_selection_report.json`, `reports/delivery/control_repeat_policy_report.json` | `python3 tools/quizbank_selection_smoke.py`; unittest status/repeat/quota/auth tests | Delivery is local API/TestClient proof, not live Telegram/public traffic. |
| Phase 5 Admin/Billing/Analytics MVP | Done (MVP-local) | `src/quizbank_mvp/cli.py`, audit table in migration, entitlement/quota tables, `reports/coverage/corpus_coverage.json`, delivery reports | `PYTHONPATH=src python3 -m quizbank_mvp.cli --help`; unittest audit/entitlement/quota tests | Billing is manual entitlement/quota model; no payment provider integration. |
| Phase 6 Stanford Demo Package | Done (local) | `docs/13_stanford_presentation_outline.md`, `tools/run_mvp_demo.py`, `reports/coverage/`, `reports/delivery/`, this evidence register | `PYTHONPATH=src python3 tools/run_mvp_demo.py` | Demo is local and artifact-backed; no real external send is claimed. |
| Phase 7 Closed Pilot Hardening | Partial (local pre-pilot expanded) | `docs/observability_contract.md`, `runbooks/backup_restore.md`, `runbooks/incident_response.md`, `runbooks/support_triage.md`, `runbooks/rollback.md`, `docs/18_telegram_delivery_playbook.md`, `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`, `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md`, `reports/roadmap/phase_7_9_gate_matrix.md`, `transition-consumer-status` CLI and tests | `python3 -m unittest discover -s tests -p "test_*.py"`; `PYTHONPATH=src python3 tools/run_pre_pilot_dry_run.py` | Pilot environment, controlled real send, external monitoring, support-channel execution and managed pilot restore drill are not present. |
| Phase 8 Public Beta Readiness | Partial (local controls expanded) | `docs/observability_contract.md`, `runbooks/release_rollback.md`, `runbooks/rollback.md`, `runbooks/incident_response.md`, `runbooks/support_triage.md`, `policies/privacy_notice_baseline.md`, `reports/compliance/legal_review_record.md`, `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`, `reports/rollback/local_rollback_tabletop_2026-05-08.md`, `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md`, `reports/roadmap/phase_7_9_gate_matrix.md`, quota/entitlement runtime tests | `python3 -m unittest discover -s tests -p "test_*.py"`; `PYTHONPATH=src python3 tools/run_pre_pilot_dry_run.py` | Public beta alerting cadence, controlled backup schedule, release execution, external support/abuse path and beta privacy/legal review are not completed. |
| Phase 9 Production Readiness | Partial (local governance only) | `.github/workflows/ci.yml`, `database/migrations/001_create_mvp_runtime.sql`, `docs/10_operations.md`, `docs/08_security_threat_model.md`, `docs/observability_contract.md`, `runbooks/backup_restore.md`, `runbooks/incident_response.md`, `runbooks/rollback.md`, `runbooks/release_rollback.md`, `reports/rollback/local_rollback_tabletop_2026-05-08.md`, `reports/roadmap/external_evidence_blockers.md`, `reports/roadmap/phase_7_9_gate_matrix.md` | `python3 -m unittest discover -s tests -p "test_*.py"`; `git diff --check` | No production deployment, monitored backups, production-like restore drill, monitoring dashboard, incident exercise, production rollback execution or production legal/privacy approval. |
| Phase 10 Pilot Execution Package Without Environment | Done (local package only) | `docs/pilot_environment_requirements.md`, `docs/pilot_launch_contract.md`, `runbooks/pilot_launch_runbook.md`, `runbooks/telegram_controlled_send_runbook.md`, `runbooks/backup_restore_operational_runbook.md`, `runbooks/monitoring_alerts_runbook.md`, `reports/roadmap/pilot_execution_checklist.md`, `reports/roadmap/pilot_go_no_go_matrix.md`, `reports/roadmap/phase_10_evidence_register.md` | `python3 -m unittest discover -s tests -p "test_*.py"`; `git diff --check` | This closes package preparation only. It does not create a server, deploy, execute Telegram send or close the pilot gate. |

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
python3 -m unittest discover -s tests -p "test_*.py" -> OK, 37 tests
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank -> active_bank_files=115 active_rows=30974 violations=0
PYTHONPATH=src python3 tools/run_mvp_demo.py -> health, ready, next_item, delivery_log, repeat_denial and quota_denial shown
PYTHONPATH=src python3 -m quizbank_mvp.cli --help -> transition-consumer-status listed
PYTHONPATH=src python3 tools/run_pre_pilot_dry_run.py -> lifecycle, delivery, repeat and quota evidence shown
local SQLite restore drill command in reports/restore/mvp_sqlite_restore_drill_2026-05-08.md -> database_is_ready=True
Phase 10 package docs -> pilot environment requirements, launch contract, controlled send, backup/restore, monitoring and go/no-go protocols recorded
git diff --check -> no whitespace errors
```

Additional Phase 7-9 local evidence recorded in this pass:

```text
transition-consumer-status CLI added and covered by runtime test -> suspended consumer receives CONSUMER_NOT_ACTIVE before delivery creation
local pre-pilot dry run -> active->suspended->blocked->active lifecycle, allowed delivery, repeat denial and quota denial
local rollback tabletop -> consumer containment, repeat containment, quota containment and local DB/code rollback paths recorded
observability contract -> health, readiness, lifecycle, delivery, denial and rollback signal names recorded
external evidence blockers -> pilot, beta and production blockers listed separately from local evidence
Phase 10 pilot execution package -> future server-side evidence requirements recorded; pilot go/no-go remains NO-GO without environment evidence
local SQLite restore drill -> database_is_ready=True, backup_sha256=da08cfb61574197b75bff75b9300b20e1327c55193c9019dad033f49ad0d0dab, restore_size_bytes=77824
Phase 7-9 gate matrix -> local gates separated from blocked external gates
```

## Closure Rule

Do not change a phase to `Done` unless its evidence artifact and verification command are both
listed here. For Phase 7-9, local documentation alone is insufficient.
