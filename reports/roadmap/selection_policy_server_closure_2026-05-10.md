# Selection Policy Server Closure Evidence

Date: 2026-05-10.

Scope: deploy and smoke the selection/projection/analytics evidence changes on
the protected VPS runtime at `/opt/api-quiz-bank`.

This closes the protected server runtime evidence for the current selection
policy slice. It does not promote the VPS to a broad production launch target;
the repository's production-readiness NO-GO boundaries remain in force for
persistent production DB, external monitoring, legal/privacy launch approval and
full production rollback governance.

Update: the production runtime blockers named above were later closed for the
owner-operated protected production API runtime in
`reports/roadmap/production_postgresql_runtime_closure_2026-05-10.md`.
Unauthenticated broad public launch, school deployment and paid launch remain
separate approval scopes.

## Source

| Check | Result |
|---|---|
| Local branch | `codex/selection-policy-phase-5` |
| Commit deployed | `736c34c23808784d9f38374afed1cf6c18716236` |
| Commit summary | `feat(selection): expose runtime selection evidence` |
| Server branch | `codex/selection-policy-phase-5` |
| Server path | `/opt/api-quiz-bank` |

## Local Verification

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests -p "test_*.py"` | `Ran 96 tests ... OK` |
| `python3 tools/run_mvp_demo.py` | emitted learner projection, selection decision, runtime analytics, Telegram payload and negative controls |
| `python3 tools/no_secrets_scan.py` | `No committed secrets detected.` |
| `git diff --check` | pass |

## Server Deploy

| Check | Result |
|---|---|
| Container | `api-quiz-bank-pilot` |
| Runtime image | `sha256:dba1cb12baddf2bf8c58ee99783eeddaae3e05274b5e97233126b68731dab66e` |
| Container state | `running/healthy` |
| Started at | `2026-05-10T10:10:11.500772721Z` |
| Port bind | `127.0.0.1:8010` |

## Server Smoke

| Check | Result |
|---|---|
| `./scripts/api_quiz_bank_smoke.sh` | `smoke-ok` |
| Protected public health without `X-API-Key` | `401` |
| Protected public health with `X-API-Key` | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Protected public ready with `X-API-Key` | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |
| Protected public delivery without `X-API-Key` | `401` |
| Protected public authorized entitlement control | `403 ENTITLEMENT_MISSING_FEATURE` |
| Runtime projection/decision import check in container | `runtime-contract-ok` |
| Committed OpenAPI seed on server | `committed-openapi-seed-ok` |

## Backup / Restore

| Command | Result |
|---|---|
| `scripts/api_quiz_bank_backup.sh` | `backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260510T101139Z.sqlite3` |
| `scripts/api_quiz_bank_restore_drill.sh` | `restore-drill-ok /var/restore-drills/api-quiz-bank/restore_drill.sqlite3` |

## Closure

The selection/projection/analytics slice is closed for the protected VPS runtime.
Full production launch remains outside this evidence scope.
