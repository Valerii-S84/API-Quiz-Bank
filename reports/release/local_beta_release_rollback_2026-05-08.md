# Local Beta Release and Rollback Drill

Date: 2026-05-08

Scope: local repository/runtime only; no deploy and no production state change.

## Release Checks

| Check | Result |
|---|---|
| Runtime auth/security tests | pass |
| OpenAPI route contract check | pass |
| No-secrets scan | pass |
| Local dry-run with auth, quota, lifecycle and selection signals | pass |

## Rollback / Disable Path

The local disable path uses `transition-consumer-status` and is exercised by
`tools/run_pre_pilot_dry_run.py`:

```bash
PYTHONPATH=src python3 -m quizbank_mvp.cli \
  --db-path var/quizbank_mvp.sqlite3 \
  transition-consumer-status \
  --consumer-id consumer_demo \
  --to-status suspended \
  --actor local_admin \
  --reason "beta containment"
```

## Owner Decision

Decision: no external beta release executed.

Reason: public beta still requires owner/legal/privacy approval, beta support
path, monitored backup evidence and protected public route smoke with real beta
credentials.
