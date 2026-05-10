# Production PostgreSQL Runtime Closure

Date: 2026-05-10.

Scope: owner-operated protected production API runtime at `api.valerchik.de`,
served from `/opt/api-quiz-bank`, with PostgreSQL as the persistent runtime
database. This closes the production runtime/database path for the protected API
surface. It does not approve unauthenticated broad public launch, school
deployment, paid launch or external legal advice claims.

## Source

| Check | Result |
|---|---|
| Repository | `Valerii-S84/API-Quiz-Bank` |
| Main commit deployed | `4f9ce996910f56aa37ede0007157011fa24fbf43` |
| Runtime path | `/opt/api-quiz-bank` |
| Server branch | `main` |
| API container | `api-quiz-bank-pilot` |
| PostgreSQL container | `api-quiz-bank-postgres` |
| Runtime image | `sha256:6553ad2ac6f46c6542cb9b3628e6098cfd5a8c4e8e6b300b565a69eb7a08f5c4` |

## Local Verification

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests -p "test_*.py"` | `Ran 99 tests ... OK` |
| `git diff --check` | pass |
| `python3 tools/no_secrets_scan.py` | `No committed secrets detected.` |
| `sh -n scripts/api_quiz_bank_production_monitor_snapshot.sh` | pass |

## Runtime Deploy

| Check | Result |
|---|---|
| Docker compose files | `docker-compose.api-quiz-bank.yml`, `docker-compose.api-quiz-bank.secrets.yml`, `docker-compose.api-quiz-bank.postgres.yml` |
| API state | `running/healthy` |
| PostgreSQL state | `running/healthy` |
| Public bind | `127.0.0.1:8010` behind the protected public route |
| Runtime DB config | `postgres-runtime-config-ok` |
| Schema migrations applied | `schema_migrations=3` |
| Runtime delivery evidence | `deliveries=1`, `selection_decisions=1` |

## Public Smoke

| Check | Result |
|---|---|
| App smoke | `smoke-ok` |
| Protected public health with edge key | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Protected public ready with edge key | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |
| Public delivery without edge key | `401` |
| Authorized entitlement negative control | `403 ENTITLEMENT_MISSING_FEATURE` |
| Authorized delivery control | `public-delivery-ok selected_top_score` |

## PostgreSQL Backup / Restore

| Check | Result |
|---|---|
| Manual backup | `postgres-backup-ok /var/backups/api-quiz-bank/api_quiz_bank_pg_20260510T104058Z.dump` |
| Restore drill | `postgres-restore-drill-ok api_quiz_bank_restore_drill` |
| Backup timer | `api-quiz-bank-postgres-backup.timer enabled active` |
| Next scheduled backup | `2026-05-11 03:20:00 UTC` |
| Timer run result | `success/0` |
| Timer-created backup | `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260510T104203Z.dump` |

## Production Monitoring

| Check | Result |
|---|---|
| Monitor script | `scripts/api_quiz_bank_production_monitor_snapshot.sh` |
| Initial snapshot | `production-monitor-snapshot-ok /var/log/api-quiz-bank/monitoring/production_monitor_20260510T104308Z.md` |
| Monitor timer | `api-quiz-bank-production-monitor.timer enabled active` |
| Timer run result | `success/0` |
| Latest snapshots | `/var/log/api-quiz-bank/monitoring/production_monitor_20260510T104309Z.md`, `/var/log/api-quiz-bank/monitoring/production_monitor_20260510T104308Z.md` |

The monitor snapshot checks the public protected route, readiness, expected
auth denial, API container health, PostgreSQL container health and PostgreSQL
backup timer state. It does not write secrets to the report.

## Rollback Drill

| Check | Result |
|---|---|
| Pre-rollback PostgreSQL backup | `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260510T104123Z.dump` |
| Rollback ref | `1a3ae1a0937d3c0acaff2b3f338be3286f7e6313` |
| Rollback smoke | `smoke-ok` |
| Rollback DB runtime | `rollback-postgres-runtime-ok` |
| Rollback API state | `running/healthy` |
| Roll-forward ref | `4f9ce996910f56aa37ede0007157011fa24fbf43` |
| Roll-forward smoke | `smoke-ok` |
| Roll-forward DB runtime | `rollforward-postgres-runtime-ok` |
| Roll-forward API/PostgreSQL state | `running/healthy`, `running/healthy` |

## Closure Decision

```text
GO for owner-operated protected production runtime on PostgreSQL.
NO-GO for unauthenticated broad public launch, school deployment, paid launch
or external legal-advice claims without separate scope-specific approval.
```

The runtime blockers for persistent production DB, production PostgreSQL
backup/restore, production monitoring snapshot, main-branch deployment and
production rollback execution are closed for the protected API scope above.
