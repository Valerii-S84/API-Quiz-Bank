# Phase 7-9 External Evidence Blockers

Updated: 2026-05-10

This file lists blockers that cannot be closed by local repository work alone.
They must remain separate from local pre-pilot evidence.

## Phase 7 Closed Pilot Blockers

| Blocker | Required external evidence |
|---|---|
| Public/broader pilot environment | Protected public route exists for `api.valerchik.de`; broader beta/prod environment still needs owner approval and evidence boundary. |
| Telegram controlled send | Controlled direct real send succeeded after bot administrator access was confirmed and channel-compatible anonymous poll payload was used. Deployed worker real-send also succeeded for Public MVP / Protected Beta; production Telegram monitoring remains separate. |
| Closed external pilot smoke | End-to-end protected route scenario through the deployed runtime worker is recorded in `reports/beta/closed_external_pilot_smoke_2026-05-08.md`. Production-grade pilot monitoring and incident evidence remain separate. |
| Worker monitoring | Owner-reviewed VPS health/readiness evidence exists for Public MVP / Protected Beta; external dashboard or alert source still needed for production closure. |
| Automated pilot backup schedule | VPS backup timer is enabled and latest run succeeded; production monitored backup remains separate. |
| Production-like restore drill | Restore into isolated target using managed/pilot-like data beyond MVP SQLite and recorded result. |
| Support execution | Public MVP / Protected Beta contact gate is recorded; production SLA/support execution remains separate. |

## Phase 8 Public Beta Blockers

| Blocker | Required external evidence |
|---|---|
| Alerting cadence | Owner-reviewed Public MVP / Protected Beta monitoring evidence exists; production dashboard/alert source remains separate. |
| Controlled backup schedule | VPS backup timer is enabled and latest run succeeded; production monitored backup remains separate. |
| Release execution | App-level credential deploy, edge/app header split, protected public smoke and rollback drill are recorded; production rollback remains separate. |
| Public support/abuse path | Public GitHub support/abuse issue path exists; private owner security channel is recorded without secrets. |
| Beta legal/privacy review | Public MVP / Protected Beta review is approved; broad public beta, school, paid and production legal/privacy approval remain separate. |

## Phase 9 Production Blockers

| Blocker | Required external evidence |
|---|---|
| Controlled deployment | Closed for owner-operated protected production API runtime in `reports/roadmap/production_postgresql_runtime_closure_2026-05-10.md`. Broader public/school/paid launch remains separate. |
| Monitored backups | Closed for current PostgreSQL runtime by `api-quiz-bank-postgres-backup.timer` and recorded backup/restore evidence. Repository-side offsite/managed backup, retention, encryption and restore-drill cadence controls are defined in `scripts/api_quiz_bank_postgres_backup.sh`, `scripts/api_quiz_bank_postgres_restore_drill.sh` and the backup runbooks; runtime offsite/managed evidence must be recorded separately when configured. |
| Production restore drill | Closed for current PostgreSQL runtime by `postgres-restore-drill-ok api_quiz_bank_restore_drill`. |
| Monitoring dashboard | Closed for current protected runtime by `scripts/api_quiz_bank_production_monitor_snapshot.sh` and `api-quiz-bank-production-monitor.timer`. Third-party monitoring vendor remains optional/future. |
| Critical alerts | Closed for current protected runtime as formal owner-review timer snapshots. External paging vendor remains optional/future. |
| Incident drill | Closed for current protected runtime through production deploy/smoke, backup/restore and rollback/roll-forward drill evidence. |
| Rollback execution | Closed for current PostgreSQL-capable runtime by rollback to `1a3ae1a0937d3c0acaff2b3f338be3286f7e6313` and roll-forward to `4f9ce996910f56aa37ede0007157011fa24fbf43`. |
| Production security hardening | Repository-side hardening package is closed by `reports/security/production_hardening_review_2026-05-10.md`: nonroot/read-only container runtime, API rate-limit control, secret rotation policy, no-secrets scan, pip audit and Grype high/critical container scan gate. VPS redeploy, image digest capture and host SSH/firewall re-check remain operational verification. |
| Production corpus volume | Gate artifact exists in `reports/publication/production_corpus_gate_2026-05-10.json`; it records 30,974 active rows but 0 approved/published deliverable production items, so production corpus volume remains `NO-GO` until owner-approved promotion/import evidence exists. |
| Production privacy/legal approval | Closed only for owner-operated protected production API runtime in `reports/compliance/legal_review_record.md` section 4.3 and `reports/compliance/legal_privacy_gate_2026-05-10.json`. Exact public legal entity/jurisdiction, vendors, broad public launch, school deployment and paid launch remain separate approval scopes. |
| Release governance | Repository-side controls are defined by `.github/branch_protection_main.json`, `.github/workflows/ci.yml`, `CHANGELOG.md`, `runbooks/migration_approval_checklist.md` and `reports/release/release_governance_gate_2026-05-10.json`; actual GitHub branch-protection enforcement and release tag creation must be verified on remote/release execution. |
| Scale/load | Local protected-runtime concurrent smoke is recorded in `reports/scale/protected_runtime_load_smoke_2026-05-10.json` with 8 concurrent deliveries, auth denial, repeat denial, quota denial and resource-limit evidence. External load test under real traffic remains required before real scale claim. |

## Guardrail

None of these blockers may be marked `Done` from local docs, SQLite evidence,
TestClient responses or CI-only checks.
