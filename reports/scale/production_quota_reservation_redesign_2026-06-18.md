# Production Quota Reservation Redesign Proof - 2026-06-18

Статус: Done

## Scope

This report records the production deployment proof for the quota reservation
redesign and the follow-up startup fix. Scope is limited to the owner-operated
protected API Quiz Bank runtime.

No new deploy is authorized by this report.

## Production Runtime

| Field | Value |
|---|---|
| VPS host | `ubuntu-8gb-nbg1-1` |
| Production path | `/opt/api-quiz-bank` |
| Commit deployed | `ca24f1cc302d2d32f32fd57ebd83df6147d8f75c` |
| Active image | `sha256:fe78d5e21de40f20b36389a638e1459a9351dc939df93ac622fb7e3dd1198af6` |
| Previous rollback image | `sha256:14d0e1ce0802387c6db3da96fde728887ccd97deafe15698d00fccaf62e616ba` |
| Rollback container | `api-quiz-bank-pilot-rollback-20260618T1454Z` |
| DB backup | `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260618T144853Z.dump` |

## Migration Status

- `016_add_quota_reservations.sql` was applied once and verified in
  `schema_migrations`.
- Migration `016` was not rolled back and was not reapplied during the startup
  fix.
- Production DB facts after deploy remained unchanged:
  - `published_items=30974`
  - `active_sources=116`

## Files Changed Across Redesign

- `Dockerfile`
- `database/migrations/014_add_quota_reservations.sql`
- `database/postgresql/016_add_quota_reservations.sql`
- `database/postgresql/README.md`
- `reports/imports/control_sample_postgresql_smoke.json`
- `reports/scale/production_stabilization_quota_profile_2026-06-16.md`
- `src/quizbank_mvp/admin_service.py`
- `src/quizbank_mvp/database_quota_reservations.py`
- `src/quizbank_mvp/database_runtime.py`
- `src/quizbank_mvp/database_seed.py`
- `src/quizbank_mvp/selection_delivery.py`
- `src/quizbank_mvp/selection_queue_fast_path.py`
- `src/quizbank_mvp/selection_quota.py`
- `src/quizbank_mvp/selection_quota_reservations.py`
- `tests/test_database_backend_contract.py`
- `tests/test_next_route_quota_lock.py`
- `tests/test_postgresql_contract.py`
- `tests/test_postgresql_queue_fast_path_concurrency.py`
- `tests/test_postgresql_quota_reservations.py`
- `tests/test_selection_queue_selector.py`
- `tests/test_startup_demo_reset.py`

## Bugs Fixed

- Hot quota row lock: quota reservation tokens replaced the single hot
  `quota_usage` write path for queue-first `/next`.
- TIMESTAMPTZ PostgreSQL typing bug: reservation timestamp values are explicitly
  cast for PostgreSQL.
- Production startup demo reset FK issue: production image startup no longer
  runs `seed-demo`, and demo reset refuses PostgreSQL/production-like runtime
  databases.

## What Was Not Touched

- No Caddy routing change.
- No Telegram containers, bots, delivery flow or backfill.
- No destructive SQL.
- No production delivery or queue reset.
- No migration rollback.
- No quota design rollback.
- No unrelated Docker services.

## Test Results

- Full unittest suite: `512 tests OK`.
- Targeted startup/queue/quota/backend suite: `44 OK`.
- PostgreSQL quota/queue suite: `7 OK`.
- PostgreSQL contract smoke: OK.
- No-secrets scan: OK.
- `git diff --check`: OK.

## Public Proof

| Stage | Result |
|---|---|
| Smoke | `200=1`, queue `1/1`, quota `1/1`, fallback `0` |
| 5 RPS | `200=5`, p95 `69.852 ms`, queue/quota `5/5` |
| 10 RPS | `200=10`, p95 `76.653 ms`, queue/quota `10/10` |
| 20 RPS | `200=20`, `429=0`, `500=0`, p50 `25.462 ms`, p95 `34.115 ms`, max `35.012 ms`, queue `20/20`, quota `20/20`, fallback `0` |

## Before / After Metrics

| Metric | Before | After |
|---|---:|---:|
| 20 RPS p95 | `238 ms` | `34.115 ms` |
| Quota p95 | `150.866 ms` | `2.296 ms` |

## Linkage And Error Counts

| Check | Result |
|---|---:|
| Queue linkage at 20 RPS | `20/20` |
| Quota linkage at 20 RPS | `20/20` |
| Fallback count at 20 RPS | `0` |
| 429 count at 20 RPS | `0` |
| 500 count at 20 RPS | `0` |

## DB Locks / Waits

- `lock_waiting_activity=0`
- `not_granted_locks=0`

## CPU / Memory

- API: `0.18%`, `50.64MiB/512MiB`
- PostgreSQL: `0.02%`, `91.32MiB/512MiB`

## Runtime Timers

The following API Quiz Bank timers were observed active/waiting after proof:

- `api-quiz-bank-production-monitor.timer`
- `api-quiz-bank-protected-beta-telegram.timer`
- `api-quiz-bank-selection-diagnostics.timer`
- `api-quiz-bank-queue-refill.timer`
- `api-quiz-bank-backup.timer`
- `api-quiz-bank-postgres-backup.timer`

No runtime timers were modified by this task.

## Rollback Path

Rollback remains available through:

- image `sha256:14d0e1ce0802387c6db3da96fde728887ccd97deafe15698d00fccaf62e616ba`;
- container `api-quiz-bank-pilot-rollback-20260618T1454Z`;
- PostgreSQL backup
  `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260618T144853Z.dump`.

Rollback should restore only the API runtime unless a separate incident
requires DB restore.

## Remaining Risks

- Caddy disk/live config mismatch must be handled separately.
- Proof consumer was suspended and its credential was revoked after proof.

## Next Recommended Steps

1. Reconcile Caddy disk/live config in a separate controlled task.
2. Fix `production_corpus_smoke` quota.
3. Fix/check `website_quiz_teaser` key mismatch.
