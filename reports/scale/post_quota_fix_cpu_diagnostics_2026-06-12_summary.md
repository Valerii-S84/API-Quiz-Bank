# Post-Quota Fix CPU Diagnostics - 2026-06-12

## Scope

Production-safe CPU/latency diagnosis after the quota-lock fix. No deploy, rebuild, restart, Postgres restart, migrations, Stage 4 or Stage 5 load were performed.

## Existing Report Analysis

| Source | Requests | Statuses | p50 | p95 | p99 | Max | PG CPU max | DB conn max | Blocked locks max |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| protected smoke | 85 | `{"200": 85}` | 121.261 | 311.249 | 376.85 | 381.623 | 80.11 | n/a | 0 |
| quota lock probe | 1200 | `{"200": 1200}` | 1713.424 | 2373.93 | 2577.845 | 2898.439 | 101.46 | 19 | 0 |

Existing artifacts do not store ordered per-request latency, per-consumer distribution, or a CPU timeline. From aggregate latency alone, the prior probe looked like a broad elevated-latency window rather than one isolated spike; the live repro below confirms that shape.

## Production Sanity

| Check | Before | Final |
|---|---:|---:|
| server SHA | `3c86649` | `3c86649` |
| public health/ready | 200 / 200 | 200 / 200 |
| API container | running/healthy, restart 0 | running/healthy, restart 0 |
| Postgres container | running/healthy, restart 0 | running/healthy, restart 0 |
| DB connections | 1 | 1 |
| blocked locks | 0 | 0 |
| non-diagnostic consumers | 21 | 21 |

## Short CPU Repro Probe

| Metric | Value |
|---|---:|
| stop reason | `postgres_cpu_gt_90_gt_30s` |
| isolated consumers | 20 |
| requests | 461 |
| statuses | `{"200": 461}` |
| 5xx / timeouts / network errors | 0 / 0 / 0 |
| p50 / p95 / p99 / max | 1620.427 / 2159.653 / 2322.067 / 2407.067 ms |
| latency shape | `broad_elevated_plateau` |
| candidate count min/max | 300 / 300 |
| Postgres CPU max | 103.13% |
| API CPU max | 60.77% |
| DB connections max/last probe sample | 20 / 20 |
| blocked locks max | 0 |

The probe stopped because Postgres CPU stayed above 90% for more than 30 seconds. It did not hit the p95 > 2500 ms, timeout, 5xx, or blocked-lock stop gates.

## Query Sampler Rollup

| Query type | Samples | Max age seconds |
|---|---:|---:|
| `SELECT FROM quiz_items` | 34 | 0.404 |
| `SELECT FROM deliveries` | 13 | 0.392 |
| `SELECT FROM api_credentials` | 10 | 0.096 |
| `INSERT INTO deliveries` | 7 | 0.204 |
| `SELECT FROM entitlements` | 5 | 0.199 |
| `BEGIN OTHER` | 3 | 0.116 |
| `INSERT INTO selection_decisions` | 3 | 0.104 |
| `SELECT FROM consumers` | 3 | 0.185 |
| `INSERT INTO quota_usage` | 2 | 0.005 |
| `COMMIT OTHER` | 1 | 0.002 |

## Root Cause

The CPU-heavy path is narrowed to the synchronous read side of `/v1/quiz-items/next`: bounded candidate selection plus delivery-history grouped metrics. The quota lock fix removed blocked locks in this repro, but each successful request still fetches a 300-row candidate pool and runs delivery-history metric reads before writing delivery evidence.

Write paths were not the primary CPU source in this run: `quota_usage` had no lock wait and only two active samples, `deliveries` and `selection_decisions` inserts were not dominant, and final blocked locks returned to zero.

## Cleanup

- Diagnostic credentials revoked: `True`
- Active diagnostic credentials after cleanup: `0`
- Revoked-key check: `403`
- Temp raw key files created: `False`
- Temp raw key files removed: `True`

## Verification

- `python3 -m unittest discover -s tests -p "test_*.py"` -> OK, 380 tests
- `python3 tools/no_secrets_scan.py` -> No committed secrets detected
- `git diff --check` -> passed
- JSON parse for new diagnostic report -> passed
- Targeted scan for raw keys, DB URL, secret header values, private keys and quiz content markers -> passed

## Post-Verification Final Sanity

- health/ready: `200/200`
- API/Postgres: `running/healthy` / `running/healthy`, restart counts `0/0`
- DB connections: `1`
- blocked locks: `0`
- active diagnostic credentials: `0`

## Result

`Done`: root cause is narrowed to the read/selection path, specifically candidate pool plus delivery-history grouped metric lookups under 20-consumer concurrency. Stage 4 and Stage 5 remain not run.
