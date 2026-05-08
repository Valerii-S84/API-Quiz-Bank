# Phase 7-9 Gate Matrix

Updated: 2026-05-08

This matrix records local evidence for `docs/14_roadmap.md` Phase 7-9 and
separates locally proven gates from external environment gates.
External blockers are listed in `reports/roadmap/external_evidence_blockers.md`.

Status values:

- `closed-local`: supported by committed local artifacts and verification.
- `partial`: local artifact exists, but the gate needs execution evidence.
- `closed-protected-beta`: supported by protected VPS/runtime evidence for
  Public MVP / Protected Beta, not production.
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
| OPS-PILOT-007 Telegram failures observable | partial | `docs/18_telegram_delivery_playbook.md`, `src/quizbank_mvp/telegram_delivery.py`, `tools/run_telegram_delivery_smoke.py`, `database/migrations/003_add_telegram_delivery_results.sql`, runtime tests, `reports/pre_pilot/telegram_dry_run_readiness_2026-05-08.md`, `reports/pre_pilot/telegram_secret_wiring_2026-05-08.md`, `reports/pre_pilot/telegram_controlled_send_2026-05-08.md` | Controlled direct Bot API send succeeded; local worker records delivery id and status, but deployed worker real-send evidence is not recorded. |
| OPS-PILOT-008 consumer disable path exists | closed-local | `transition-consumer-status` CLI, `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`, `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md`, runtime tests | Covered for local-only VPS; public/beta/prod operator execution remains out of scope. |
| OPS-PILOT-009 support/issue path exists | closed-local | `runbooks/support_triage.md`, `SECURITY.md` | No external pilot support channel is configured. |

Phase 7 result: closed for local-only/internal pilot. The phase is not
public-beta or production ready. Telegram has local worker dry-run/real-send
code, but deployed worker real-send remains unproven.

Local pre-pilot result: active -> suspended -> blocked -> reactivated -> allowed
consumer lifecycle is proven locally; delivery, repeat and quota behavior are
proven locally; health, readiness, smoke, backup, restore drill, lifecycle,
delivery, repeat guard, quota denial, Telegram dry-run, Telegram token secret
wiring, protected public route smoke and one controlled direct Telegram real
send are proven on the VPS; runtime worker delivery is now implemented locally,
but worker real-send through the deployed runtime is not proven.

## Phase 8 Public Beta Readiness

| Gate | Status | Evidence | Remaining blocker |
|---|---|---|---|
| OPS-BETA-001 rate/usage controls operational | closed-local | quota/entitlement/auth runtime tests, pre-pilot dry run, 429 quota response, `reports/beta/local_beta_security_smoke_2026-05-08.md`, `reports/beta/app_level_public_smoke_2026-05-08.md`, `reports/beta/edge_app_header_split_smoke_2026-05-08.md` | Controlled public route smoke exists; broader beta traffic not started. |
| OPS-BETA-002 alerts or monitored review exists | closed-protected-beta | `docs/observability_contract.md`, `runbooks/incident_response.md`, `reports/observability/beta_alert_review_2026-05-08.md`, `reports/observability/public_mvp_monitoring_review_2026-05-08.md`, `reports/beta/vps_live_ops_evidence_2026-05-08.md`, `reports/pre_pilot/public_api_key_route_evidence_2026-05-08.md` | Owner-reviewed evidence only; no production dashboard or alert source. |
| OPS-BETA-003 backup schedule controlled | closed-local | `runbooks/backup_restore.md`, `reports/beta/vps_live_ops_evidence_2026-05-08.md`, `reports/beta/backup_timer_evidence_2026-05-08.md` | VPS SQLite cadence exists; production monitored backup still separate. |
| OPS-BETA-004 restore drill evidence exists | closed-protected-beta | `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md`, `reports/beta/vps_live_ops_evidence_2026-05-08.md`, `reports/restore/public_mvp_backup_restore_2026-05-08.md` | VPS SQLite restore drill exists; no production-like PostgreSQL restore drill. |
| OPS-BETA-005 incident escalation model exists | closed-protected-beta | `runbooks/incident_response.md`, `runbooks/support_triage.md`, `reports/compliance/public_mvp_support_security_contact_2026-05-08.md` | Production incident owner/SLA remains out of scope. |
| OPS-BETA-006 release/rollback process exists | closed-protected-beta | `runbooks/release_rollback.md`, `runbooks/rollback.md`, `reports/release/local_beta_release_rollback_2026-05-08.md`, `reports/rollback/public_mvp_runtime_rollback_drill_2026-05-08.md`, `reports/beta/app_level_public_smoke_2026-05-08.md`, `reports/beta/edge_app_header_split_smoke_2026-05-08.md`, `.github/workflows/ci.yml` | Production rollback remains separate. |
| OPS-BETA-007 security operations baseline exists | closed-protected-beta | `SECURITY.md`, `docs/08_security_threat_model.md`, consumer-bound API credentials, no-secrets CI scan, `reports/compliance/public_mvp_support_security_contact_2026-05-08.md` | No formal vulnerability disclosure program or production security review. |
| OPS-BETA-008 privacy/legal review completed | closed-protected-beta | `reports/compliance/legal_review_record.md`, `policies/privacy_notice_baseline.md` | Approved only for Public MVP / Protected Beta; production, paid, school and broad public launch remain pending. |

Phase 8 result: Public MVP / Protected Beta operational gates for support,
privacy/legal, owner-reviewed monitoring, backup/restore and rollback are
closed. This does not approve production, paid launch, school deployment,
unauthenticated access or broad public launch. Overall Public MVP launch still
requires the remaining Telegram worker/runtime send gates and owner GO/NO-GO
record.

## Phase 9 Production Readiness

| Gate | Status | Evidence | Remaining blocker |
|---|---|---|---|
| OPS-PROD-001 controlled deployment exists | partial | `.github/workflows/ci.yml`, branch/PR governance docs | No production deployment target or release owner. |
| OPS-PROD-002 monitored backups exist | blocked-external | `runbooks/backup_restore.md`, `runbooks/backup_restore_operational_runbook.md`, `reports/restore/public_mvp_backup_restore_2026-05-08.md` | No production DB or production backup monitor. |
| OPS-PROD-003 restore drill completed | blocked-external | local restore drill report, PostgreSQL profile in `database/postgresql/001_create_runtime.sql` | No production-like restore drill execution. |
| OPS-PROD-004 monitoring dashboard exists | blocked-external | none | No dashboard. |
| OPS-PROD-005 critical alerts or owner review exists | blocked-external | `docs/observability_contract.md`, `runbooks/incident_response.md`, `reports/observability/public_mvp_monitoring_review_2026-05-08.md` | No production alert source or dashboard. |
| OPS-PROD-006 incident playbook owner assigned | partial | `runbooks/incident_response.md`, `runbooks/support_triage.md`, `reports/compliance/public_mvp_support_security_contact_2026-05-08.md` | No production owner assignment or drill. |
| OPS-PROD-007 rollback/disable paths verified | partial | `runbooks/rollback.md`, `reports/rollback/local_rollback_tabletop_2026-05-08.md`, `reports/rollback/public_mvp_runtime_rollback_drill_2026-05-08.md`, consumer lifecycle dry run | No production rollback execution. |
| OPS-PROD-008 migrations versioned/tested | partial | SQLite migrations, PostgreSQL schema profile, tests | PostgreSQL profile not executed against a database target. |
| OPS-PROD-009 security baseline implemented | partial | `SECURITY.md`, threat model, consumer-bound API credentials, no-secrets CI scan, tests | No production hardening or security review. |
| OPS-PROD-010 support/contact path exists | partial | `runbooks/support_triage.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/support_abuse.md` | Public issue path exists; no signed/security private contact. |
| OPS-PROD-011 launch risks documented | closed-local | `reports/roadmap/roadmap_evidence_register.md`, `reports/roadmap/external_evidence_blockers.md`, this matrix | External launch risks still unresolved. |
| OPS-PROD-012 launch approval recorded | blocked-external | `reports/compliance/legal_review_record.md` | No production approval. |

Phase 9 result: closed as `NO-GO production`. Production cannot be marked ready
from local documentation, MVP SQLite evidence, local-only VPS evidence or CI
checks alone.
