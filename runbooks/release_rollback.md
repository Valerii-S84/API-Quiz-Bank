# API Quiz Bank Release and Rollback Runbook

Status: MVP-local and Public MVP / Protected Beta controlled-deployment
rollback checklist; not a production release process.

## Release Preconditions

- Relevant tests pass.
- Changed contracts, schema, import behavior or delivery behavior are documented.
- Known limitations are recorded.
- Backup/restore readiness is checked for any persistent environment.
- Rollback or disable path is named before release starts.

## MVP Local Release Check

```bash
python3 -m unittest discover -s tests -p "test_*.py"
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank
PYTHONPATH=src python3 tools/run_mvp_demo.py
```

## Rollback / Disable Paths

| Scope | First rollback or containment |
|---|---|
| Local API runtime | Stop Uvicorn process and return to previous branch/commit. |
| SQLite MVP demo DB | Restore from local backup into a safe target, then swap only after verification. |
| Bad item status | Use admin status transition to `blocked` or `retired` and verify delivery denial. |
| Bad consumer access | Disable or remove entitlement/quota access in the governed DB workflow. |
| Bad import artifact | Regenerate from source or revert the generated artifact through normal Git review. |

## Public MVP / Protected Beta Drill Evidence

The protected VPS rollback drill is recorded in
`reports/rollback/public_mvp_runtime_rollback_drill_2026-05-08.md`.

The drill verified:

- backup before runtime rollback;
- previous Git ref checkout and container recreate;
- health, readiness and smoke on rollback ref;
- roll-forward to `main`;
- health, readiness and smoke after recovery;
- credential revocation and consumer suspension containment.

## Production Boundary

This repo has no committed production deployment pipeline. Production rollback
remains blocked until production target, release owner, production
backup/restore drill and monitored rollback path exist.
