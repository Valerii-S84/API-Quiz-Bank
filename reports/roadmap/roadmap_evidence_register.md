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
| Phase 7 Closed Pilot Hardening | Partial | `runbooks/backup_restore.md`, `runbooks/support_triage.md`, `docs/18_telegram_delivery_playbook.md` | Not fully verifiable locally | Pilot environment, controlled real send, restore drill evidence, monitoring and support execution are not present. |
| Phase 8 Public Beta Readiness | Partial | `runbooks/release_rollback.md`, `runbooks/support_triage.md`, `policies/privacy_notice_baseline.md`, `reports/compliance/legal_review_record.md` | Not fully verifiable locally | Public beta rate limits, alerting cadence, release execution and beta privacy/legal review are not completed. |
| Phase 9 Production Readiness | Not done | `docs/10_operations.md`, `docs/08_security_threat_model.md`, `runbooks/backup_restore.md`, `runbooks/release_rollback.md` | Not verifiable locally | No production deployment, monitored backups, restore drill, incident exercise, CI/deploy gate or production legal/privacy approval. |

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
python3 -m unittest discover -s tests -p 'test_*.py' -> OK, 35 tests
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank -> active_bank_files=115 active_rows=30974 violations=0
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts -> active_bank_files=115 active_rows=30974
python3 tools/quizbank_import_sample.py -> dry-run import passed: sample_control_001
python3 tools/quizbank_gap_map.py -> level/theme coverage summary printed
python3 tools/quizbank_selection_smoke.py -> selection smoke passed: no eligible item
PYTHONPATH=src python3 tools/run_mvp_demo.py -> health, ready, next_item, delivery_log, repeat_denial and quota_denial shown
PYTHONPATH=src python3 -m quizbank_mvp.cli --help -> CLI commands listed
git diff --check -> no whitespace errors
```

## Closure Rule

Do not change a phase to `Done` unless its evidence artifact and verification command are both
listed here. For Phase 7-9, local documentation alone is insufficient.
