# Public MVP / Protected Beta Monitoring Review

Date: 2026-05-08

Scope: owner-reviewed monitoring surface for protected Public MVP / Protected
Beta. This is not a production dashboard or automated alerting claim.

## Runtime Signals

| Signal | Evidence |
|---|---|
| Host | `ubuntu-8gb-nbg1-1` |
| Runtime path | `/opt/api-quiz-bank` |
| Branch/head after drill | `main` / `aaad3b7cac7c998f7b86119429b7a03d30c59428` |
| Container after recovery | `running/healthy`, image `sha256:fa6adfe5547b8ba15e1767d32ca0cb88f29c36b474cb68834b5f51333e583228` |
| Health | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Readiness | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |
| Local smoke | `smoke-ok` |
| Public no-edge health | `401` |
| Backup timer | `active`, `enabled` |
| Backup result | `backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T184051Z.sqlite3` |
| Restore drill result | `restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T184051Z_public_mvp_6_10_recovery/restore_drill.sqlite3` |
| Rollback drill | rollback to `4f53e52175c197725919c0d4387fe9fde699edfa`, smoke OK, roll-forward to `main`, smoke OK |
| Auth/credential failure | revoked credential returned `AUTH_CREDENTIAL_INACTIVE` with 403 |
| Consumer disable failure | suspended consumer returned `CONSUMER_NOT_ACTIVE` with 403 |
| Delivery guard | suspended/revoked calls created no delivery |

## Review Cadence

During Public MVP / Protected Beta operation, the owner-reviewed checklist is:

- `/health`;
- `/ready`;
- local smoke script;
- protected-route denial signal;
- delivery failures and Telegram failures;
- auth failures and quota spikes;
- backup timer status and latest backup result;
- latest restore drill result;
- support/security/privacy intake queue.

## Decision

```text
GO for owner-reviewed Public MVP / Protected Beta monitoring surface
NO-GO for production monitoring/dashboard/alerting
```
