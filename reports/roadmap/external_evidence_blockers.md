# Phase 7-9 External Evidence Blockers

Updated: 2026-06-12

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
| Production corpus volume | Closed for the owner-approved active corpus by `reports/publication/owner_corpus_approval_2026-05-11.json`, `reports/publication/verified_corpus_promotion_2026-05-11.json`, `reports/imports/production_corpus_postgresql_smoke_2026-05-11.json` and `reports/publication/production_corpus_gate_2026-05-11.json`; broad launch still depends on the separate legal/privacy, release-governance and scale gates. |
| Production privacy/legal approval | Closed only for owner-operated protected production API runtime in `reports/compliance/legal_review_record.md` section 4.3 and `reports/compliance/legal_privacy_gate_2026-05-10.json`. Exact public legal entity/jurisdiction, vendors, broad public launch, school deployment and paid launch remain separate approval scopes. |
| Release governance | Repository-side controls are defined by `.github/branch_protection_main.json`, `.github/workflows/ci.yml`, `CHANGELOG.md`, `runbooks/migration_approval_checklist.md` and `reports/release/release_governance_gate_2026-05-10.json`; actual GitHub branch-protection enforcement and release tag creation must be verified on remote/release execution. |
| Scale/load | Smoke threshold remains closed for the owner-operated protected business-route checks and the latest read-path postfix smoke. The earlier quota-lock blocker is superseded by deployed quota/read-path fixes and follow-up production probes with blocked locks max `0`. Current evidence is recorded in `reports/scale/read_path_cpu_production_deploy_2026-06-12.md`, `reports/scale/read_path_postfix_smoke_2026-06-12.json`, `reports/scale/read_path_cpu_lock_probe_2026-06-12.json`, `reports/scale/protected_staged_load_after_read_path_fix_2026-06-12.json` and `reports/scale/protected_staged_load_after_read_path_fix_2026-06-12_summary.md`: protected smoke passed with 85/85 `200`, zero 5xx/timeouts, p95 `268.541 ms`, candidate max `150` and blocked locks max `0`; the CPU/lock probe returned 1200/1200 `200`, zero 5xx/timeouts and blocked locks max `0`, but failed the gate with p95 `1696.847 ms` and sampled Postgres CPU above `90%` for `64 s` with max `103.01%`. Stage 4 and Stage 5 were not run. Full scale remains open until the read-path CPU/p95 finding is remediated and approved protected Stage 4/Stage 5 or sustained-CPU gates are rerun. This is not broad public scale, paid launch, school launch, support/SLA or legal/privacy approval. |

## 2026-06-12 Quota Lock Remediation Boundary

Local code remediation and local proof are recorded in
`reports/scale/quota_lock_remediation_2026-06-12.md`,
`reports/scale/quota_transaction_before_after_2026-06-12.md` and
`reports/scale/quota_lock_perf_after_fix_2026-06-12.json`.

This reduces the Stage 4 blocker by moving candidate selection,
delivery-history reads, scoring and eligibility before the atomic quota reserve.
The scale/load blocker remains external until an approved production deploy,
small protected smoke and separate Stage 4/Stage 5 rerun are completed.

## 2026-06-12 Quota Lock Production Rerun Boundary

Production was updated from GitHub `main` at
`3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3` with an API-only rebuild/restart.
Postgres was not restarted and no migrations were applied because there were no
new migration files relative to the previous production checkout.

Evidence is recorded in:

- `reports/scale/quota_lock_production_deploy_2026-06-12.md`
- `reports/scale/quota_lock_postfix_smoke_2026-06-12.json`
- `reports/scale/quota_lock_probe_2026-06-12.json`
- `reports/scale/protected_staged_load_after_quota_fix_2026-06-12.json`
- `reports/scale/protected_staged_load_after_quota_fix_2026-06-12_summary.md`

The protected smoke passed with 85/85 `200`, zero 5xx/timeouts, p95
`311.249 ms`, candidate max `300` and blocked locks max `0`. The short
lock probe returned 1200/1200 `200`, zero 5xx/timeouts and blocked locks max
`0`, but failed the latency/CPU gate with p95 `2373.93 ms` and sampled
Postgres CPU max `101.46%`. Stage 4 and Stage 5 were therefore not run.

The scale/load blocker remains open. This does not claim paid pilot readiness,
broad launch readiness, school launch readiness, support/SLA readiness or
additional legal/privacy approval.

## 2026-06-12 Post-Quota Fix CPU Diagnostics Boundary

Follow-up production-safe CPU diagnostics are recorded in:

- `reports/scale/post_quota_fix_cpu_diagnostics_2026-06-12.json`
- `reports/scale/post_quota_fix_cpu_diagnostics_2026-06-12_summary.md`
- `reports/scale/next_route_slow_query_profile_2026-06-12.md`

The controlled probe used 20 isolated diagnostic consumers and stopped before
Stage 4/Stage 5 scope. It returned 461/461 `200`, zero 5xx, zero timeouts,
p95 `2159.653 ms`, p99 `2322.067 ms`, blocked locks max `0`, candidate count
min/max `300/300` and Postgres CPU max `103.13%`. The stop reason was
Postgres CPU above `90%` for more than 30 seconds.

The new scale blocker is no longer DB lock contention in this repro. It is the
CPU-bound synchronous read path for `/v1/quiz-items/next`: bounded candidate
selection plus delivery-history grouped metric lookups under concurrency.
Expected next-route indexes are present, so no missing index is proven by this
run. Stage 4 and Stage 5 remain blocked until that read path is remediated and
the protected gates are rerun under explicit approval.

## 2026-06-12 Read Path CPU Remediation Boundary

Local read-path remediation is recorded in:

- `reports/scale/read_path_cpu_remediation_2026-06-12.md`
- `reports/scale/read_path_candidate_pool_before_after_2026-06-12.md`
- `reports/scale/read_path_perf_after_fix_2026-06-12.json`

The local proof used a synthetic 30k-item SQLite runtime and recorded 100/100
sequential `/v1/quiz-items/next` responses, p95 `134.965 ms`, candidate max
`150`, query count per success `8`, and zero exceptions/timeouts/5xx. It also
recorded a short local concurrency probe with 24/24 `200` and zero
exceptions/timeouts/5xx.

This closes only the local code-remediation proof. The external scale/load
blocker remains open until an explicitly approved production deploy, protected
smoke and Stage 4/Stage 5 rerun show acceptable PostgreSQL CPU, latency and
lock behavior. This does not claim paid pilot readiness, broad launch
readiness, school launch readiness, support/SLA readiness or additional
legal/privacy approval.

## 2026-06-12 Read Path CPU Production Deploy Boundary

Production was updated from GitHub `main` at
`a46d33f41fabf685dcfbc2cda98f5967f906cbc2` with an API-only rebuild/restart.
Postgres was not restarted and no migrations were applied because there were no
new migration files relative to the previous production checkout
`3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3`.

Evidence is recorded in:

- `reports/scale/read_path_cpu_production_deploy_2026-06-12.md`
- `reports/scale/read_path_postfix_smoke_2026-06-12.json`
- `reports/scale/read_path_cpu_lock_probe_2026-06-12.json`
- `reports/scale/protected_staged_load_after_read_path_fix_2026-06-12.json`
- `reports/scale/protected_staged_load_after_read_path_fix_2026-06-12_summary.md`

The protected smoke passed with 85/85 `200`, zero 5xx/timeouts, p95
`268.541 ms`, candidate max `150` and blocked locks max `0`. The CPU/lock probe
returned 1200/1200 `200`, zero 5xx/timeouts and blocked locks max `0`, but
failed the gate with p95 `1696.847 ms` and sampled Postgres CPU above `90%` for
`64 s` with max `103.01%`.

Stage 4 and Stage 5 were therefore not run. Cleanup revoked all diagnostic
credentials, revoked-key checks returned `403`, active diagnostic credentials
ended at `0`, non-test consumers remained `42`, final health/ready was
`200/200`, final DB connections returned to `1`, and final blocked locks were
`0`.

The scale/load blocker remains open. This does not claim paid pilot readiness,
broad launch readiness, school launch readiness, support/SLA readiness or
additional legal/privacy approval.

## Guardrail

None of these blockers may be marked `Done` from local docs, SQLite evidence,
TestClient responses or CI-only checks.
