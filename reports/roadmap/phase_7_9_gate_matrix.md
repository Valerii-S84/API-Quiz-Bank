# Phase 7-9 Gate Matrix

Updated: 2026-05-08

This matrix records local evidence for `docs/14_roadmap.md` Phase 7-9 and
separates locally proven gates from external environment gates.
External blockers are listed in `reports/roadmap/external_evidence_blockers.md`.

Status values:

- `closed-local`: supported by committed local artifacts and verification.
- `partial`: local artifact exists, but the gate needs execution evidence.
- `blocked-external`: cannot close without pilot/beta/production environment,
  approved real send, owner assignment, legal review or deployment evidence.

## Phase 7 Closed Pilot Hardening

| Gate | Status | Evidence | Remaining blocker |
|---|---|---|---|
| OPS-PILOT-001 pilot environment identified | closed-local | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md`, `runbooks/server_deploy.md` | Environment is local-only VPS; not public beta or production. |
| OPS-PILOT-002 health/readiness checks exist | closed-local | `/health`, `/ready`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md`, `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`, tests | External public readiness check not in scope. |
| OPS-PILOT-003 monitoring/logging exists | closed-local | `docs/observability_contract.md`, delivery logs, audit log, pre-pilot dry run, VPS owner-review cadence in `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Owner-review evidence only; no external dashboard or worker log stream. |
| OPS-PILOT-004 backup process exists | closed-local | `runbooks/backup_restore.md`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Backup is manual/owner-reviewed for local-only pilot, not automated public beta backup. |
| OPS-PILOT-005 restore procedure exists | closed-local | `runbooks/backup_restore.md`, `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Restore evidence is local-only VPS SQLite, not production-like managed DB. |
| OPS-PILOT-006 incident playbook exists | closed-local | `runbooks/incident_response.md`, `runbooks/support_triage.md`, `runbooks/rollback.md`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Incident drill not executed. |
| OPS-PILOT-007 Telegram failures observable | closed-local | `docs/18_telegram_delivery_playbook.md`, delivery negative controls, `reports/pre_pilot/telegram_dry_run_readiness_2026-05-08.md`, `reports/pre_pilot/telegram_secret_wiring_2026-05-08.md` | Dry-run and token secret wiring only; no real Telegram worker target or controlled send evidence. |
| OPS-PILOT-008 consumer disable path exists | closed-local | `transition-consumer-status` CLI, `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md`, runtime tests | Covered for local-only VPS; public/beta/prod operator execution remains out of scope. |
| OPS-PILOT-009 support/issue path exists | closed-local | `runbooks/support_triage.md`, `SECURITY.md` | No external pilot support channel is configured. |

Phase 7 result: closed for local-only/internal pilot. The phase is not
public-beta or production ready, and Telegram remains dry-run only.

Local pre-pilot result: active -> suspended -> blocked -> reactivated -> allowed
consumer lifecycle is proven locally; delivery, repeat and quota behavior are
proven locally; health, readiness, smoke, backup, restore drill, lifecycle,
delivery, repeat guard, quota denial, Telegram dry-run and Telegram token secret
wiring are proven on the VPS; Telegram real send remains blocked.

## Phase 8 Public Beta Readiness

| Gate | Status | Evidence | Remaining blocker |
|---|---|---|---|
| OPS-BETA-001 rate/usage controls operational | closed-local | quota/entitlement runtime tests, pre-pilot dry run, 429 quota response | No public beta traffic or deployed control evidence. |
| OPS-BETA-002 alerts or monitored review exists | partial | `docs/observability_contract.md`, `runbooks/incident_response.md`, `reports/pre_pilot/public_api_key_route_evidence_2026-05-08.md` | No beta dashboard or alert source. |
| OPS-BETA-003 backup schedule controlled | partial | `runbooks/backup_restore.md` | No automated/reliable beta backup schedule. |
| OPS-BETA-004 restore drill evidence exists | partial | `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md` | Local SQLite only; no beta environment drill. |
| OPS-BETA-005 incident escalation model exists | closed-local | `runbooks/incident_response.md`, `runbooks/support_triage.md` | No beta owner assignment. |
| OPS-BETA-006 release/rollback process exists | partial | `runbooks/release_rollback.md`, `runbooks/rollback.md`, `reports/rollback/local_rollback_tabletop_2026-05-08.md`, `.github/workflows/ci.yml` | No executed beta release/rollback checklist. |
| OPS-BETA-007 security operations baseline exists | partial | `SECURITY.md`, `docs/08_security_threat_model.md` | No public vulnerability channel or beta monitoring. |
| OPS-BETA-008 privacy/legal review completed | blocked-external | `reports/compliance/legal_review_record.md` | Beta review remains pending. |

Phase 8 result: still `NO-GO public beta`. Protected public route evidence now
exists for `api.valerchik.de`, but public beta readiness remains blocked by
beta alerting/dashboard, controlled public/beta backup cadence, public
support/abuse path and legal review evidence.

## Phase 9 Production Readiness

| Gate | Status | Evidence | Remaining blocker |
|---|---|---|---|
| OPS-PROD-001 controlled deployment exists | partial | `.github/workflows/ci.yml`, branch/PR governance docs | No production deployment target or release owner. |
| OPS-PROD-002 monitored backups exist | blocked-external | `runbooks/backup_restore.md` | No production DB, backup monitor or owner. |
| OPS-PROD-003 restore drill completed | blocked-external | local restore drill report | No production-like restore drill. |
| OPS-PROD-004 monitoring dashboard exists | blocked-external | none | No dashboard. |
| OPS-PROD-005 critical alerts or owner review exists | blocked-external | `docs/observability_contract.md`, `runbooks/incident_response.md` | No alert source or formal review owner. |
| OPS-PROD-006 incident playbook owner assigned | partial | `runbooks/incident_response.md`, `runbooks/support_triage.md` | No production owner assignment or drill. |
| OPS-PROD-007 rollback/disable paths verified | partial | `runbooks/rollback.md`, `reports/rollback/local_rollback_tabletop_2026-05-08.md`, consumer lifecycle dry run | No production rollback execution. |
| OPS-PROD-008 migrations versioned/tested | closed-local | `database/migrations/001_create_mvp_runtime.sql`, tests | SQLite MVP only; not production PostgreSQL. |
| OPS-PROD-009 security baseline implemented | partial | `SECURITY.md`, threat model, tests | No production hardening or security review. |
| OPS-PROD-010 support/contact path exists | partial | `runbooks/support_triage.md`, `SECURITY.md` | No public production support/contact. |
| OPS-PROD-011 launch risks documented | closed-local | `reports/roadmap/roadmap_evidence_register.md`, `reports/roadmap/external_evidence_blockers.md`, this matrix | External launch risks still unresolved. |
| OPS-PROD-012 launch approval recorded | blocked-external | `reports/compliance/legal_review_record.md` | No production approval. |

Phase 9 result: closed as `NO-GO production`. Production cannot be marked ready
from local documentation, MVP SQLite evidence, local-only VPS evidence or CI
checks alone.
