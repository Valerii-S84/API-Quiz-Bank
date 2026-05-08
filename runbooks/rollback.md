# API Quiz Bank Rollback Runbook

Status: local rollback/disable baseline and future pilot/beta/production gate placeholder.

## Scope

Use this runbook for local MVP rollback tabletop and containment planning.
It does not prove production rollback readiness without a deployment target,
release owner, backup/restore evidence and monitored rollback execution.

## Local Rollback Table

| Failure | First containment | Recovery check |
|---|---|---|
| Bad item selected | Transition item to `blocked` or `retired`. | Repeat next-item request returns no delivery for that item. |
| Bad consumer access | `transition-consumer-status --to-status suspended` or `blocked`. | Next-item request returns `CONSUMER_NOT_ACTIVE`. |
| Quota or entitlement defect | Set quota to zero or disable entitlement through governed DB/admin path. | Request returns `QUOTA_EXCEEDED` or entitlement denial. |
| Bad local DB state | Restore SQLite backup into isolated path before replacing active DB. | `/ready` returns `ok` and dry run passes. |
| Bad code change | Revert through normal Git review path or return to previous branch/commit locally. | Unit tests and dry run pass. |
| Bad release artifact | Regenerate from source or revert generated artifact through Git review. | Invariant tests pass and diff is reviewed. |

## Local Tabletop Command Set

```bash
python3 -m unittest discover -s tests -p "test_*.py"
PYTHONPATH=src python3 tools/run_pre_pilot_dry_run.py
git diff --check
```

## Evidence Rule

Rollback evidence must record:

- scenario;
- containment command or action;
- expected observable result;
- actual local result;
- limitation;
- whether an external environment remains blocked.

## Production Boundary

Production rollback remains blocked until a production deployment target,
release owner, monitored backup, restore drill, migration discipline and launch
approval exist.
