# Local Rollback Tabletop Evidence

Date: 2026-05-08

Scope: local pre-pilot rollback tabletop only.

No pilot, beta or production environment was created. No production deploy,
external Telegram send or production rollback was executed.

## Tabletop Scenarios

| Scenario | Local containment path | Observable result | Status |
|---|---|---|---|
| Bad consumer access | `transition-consumer-status --to-status suspended` | Next delivery request returns `CONSUMER_NOT_ACTIVE` and no delivery is created. | covered by dry run |
| Escalated consumer block | `transition-consumer-status --to-status blocked` | Next delivery request returns `CONSUMER_NOT_ACTIVE`. | covered by dry run |
| Reactivation after review | `transition-consumer-status --to-status active` | Eligible request returns 200 and creates one delivery. | covered by dry run |
| Repeat containment | Repeat same consumer/item request | Request returns `SELECTION_NO_ELIGIBLE_ITEM`. | covered by dry run |
| Quota containment | Consumer with zero quota | Request returns `QUOTA_EXCEEDED`. | covered by dry run |
| Bad local DB state | Restore SQLite backup into isolated path | `/ready` returns `ok`; restore evidence is recorded separately. | covered by restore report |
| Bad code or artifact | Git rollback/revert through review path | Tests and dry run must pass before release claim. | tabletop only |

## Verification Link

Primary local execution evidence:

- `reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md`
- `reports/restore/mvp_sqlite_restore_drill_2026-05-08.md`
- `runbooks/rollback.md`

## Limitation

This tabletop does not prove production rollback. External rollback still needs
a deployment target, owner, monitored backup, restore drill, migration rollback
discipline and launch approval.
