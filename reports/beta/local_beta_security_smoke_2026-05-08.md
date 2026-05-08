# Local Beta Security Smoke Evidence

Date: 2026-05-08

Scope: local TestClient and isolated SQLite only; no public beta traffic, deploy,
real Telegram send or production credential was used.

## Result

| Gate | Local result | Evidence |
|---|---|---|
| Missing API key denied | pass | `tests.test_mvp_runtime` |
| Invalid API key denied | pass | `tests.test_mvp_runtime` |
| API key bound to consumer | pass | `tests.test_mvp_runtime` |
| Raw key not stored | pass | `tests.test_mvp_runtime` |
| Suspended/blocked consumer denied | pass | `tools/run_pre_pilot_dry_run.py` |
| Quota denial observed | pass | `tools/run_pre_pilot_dry_run.py` |
| Draft/blocked/retired items not delivered | pass | `tests.test_mvp_runtime` |
| Answer key absent from public projection | pass | `tests.test_mvp_runtime` |

## Command

```bash
python3 -m unittest tests.test_mvp_runtime tests.test_pre_pilot_runtime_invariants tests.test_contract_schema_invariants -q
PYTHONPATH=src python3 tools/run_pre_pilot_dry_run.py
```

## Limitation

This is local beta-readiness evidence only. It does not prove protected public
route behavior with real beta credentials.
