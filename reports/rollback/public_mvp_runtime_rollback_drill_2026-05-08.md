# Public MVP / Protected Beta Runtime Rollback Drill

Date: 2026-05-08

Scope: protected VPS runtime at `/opt/api-quiz-bank`. This drill does not
approve production rollback readiness.

## Environment

| Field | Evidence |
|---|---|
| Host | `ubuntu-8gb-nbg1-1` |
| Runtime path | `/opt/api-quiz-bank` |
| Current branch | `main` |
| Current head | `aaad3b7cac7c998f7b86119429b7a03d30c59428` |
| Rollback head | `4f53e52175c197725919c0d4387fe9fde699edfa` |
| Tracked dirty count | `0` before and after drill |

## Containment Drill

| Check | Result |
|---|---|
| Initial delivery | `200`, delivery created |
| Revoked credential denial | `403 AUTH_CREDENTIAL_INACTIVE`, no delivery created |
| Suspended consumer denial | `403 CONSUMER_NOT_ACTIVE`, no delivery created |
| Delivery count for evidence consumer | `1` |
| Latest audit | `consumer_status_transition`, `active` -> `suspended` |

## Backup / Restore Guard

| Step | Result |
|---|---|
| Pre-drill backup | `backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T184120Z.sqlite3` |
| Post-drill isolated restore | `restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T184120Z_public_mvp_rollback_success/restore_drill.sqlite3` |

## Container Rollback Drill

First attempt finding:

```text
rollback container was recreated, but the immediate curl ran while health was
still starting and returned connection reset.
```

The drill was repeated with an explicit wait-for-healthy guard.

| Step | Result |
|---|---|
| Checkout rollback ref | `4f53e52175c197725919c0d4387fe9fde699edfa` |
| Rollback container | `running/healthy`, image `sha256:bec821f9e3ae561019394c2e51474e35e97469bc55287c76d3dbea5281abc1c3` |
| Rollback health | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Rollback readiness | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |
| Rollback smoke | `smoke-ok` |
| Roll-forward ref | `main` / `aaad3b7cac7c998f7b86119429b7a03d30c59428` |
| Roll-forward container | `running/healthy`, image `sha256:fa6adfe5547b8ba15e1767d32ca0cb88f29c36b474cb68834b5f51333e583228` |
| Roll-forward health | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Roll-forward readiness | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |
| Roll-forward smoke | `smoke-ok` |

## Decision

```text
GO for Public MVP / Protected Beta runtime rollback gate
NO-GO for production rollback readiness
```

## Boundary

This proves rollback/roll-forward for the protected SQLite MVP runtime only.
It does not prove production DB rollback, migration rollback, production traffic
rollback or production incident readiness.
