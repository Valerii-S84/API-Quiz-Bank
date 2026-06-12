# Next Route Postfix Smoke - 2026-06-12

## Scope

Protected postfix smoke for `/v1/quiz-items/next` after production hotfix deploy
and PostgreSQL migration `011`.

This was not a full load test.

## Production Context

| Field | Value |
|---|---|
| Host | `valerchik.de` |
| Path | `/opt/api-quiz-bank` |
| Release branch | `release/next-route-hotfix-2026-06-11` |
| Server SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| API container | `api-quiz-bank-pilot` |
| Postgres container | `api-quiz-bank-postgres` |

## Diagnostic Consumer

| Field | Value |
|---|---|
| Consumer | `postfix-smoke-next-route-2026-06-12` |
| Key fingerprint | `491f0e93a18ca623` |
| Raw key printed | `no` |
| Credential after cleanup | `revoked` |
| Temp raw key file removed | `yes` |
| Revoked key check | `403`, not usable |
| Non-test consumers before/after | `22 / 22` |

## Smoke Profile

| Phase | Requests |
|---|---:|
| Warm-up sequential | 5 |
| Main sequential | 50 |
| Small concurrency, concurrency 3 | 30 |
| Total | 85 |

## Result

| Metric | Value |
|---|---:|
| Status distribution | `{"200": 85}` |
| 5xx | 0 |
| Timeouts | 0 |
| p50 | `90.953 ms` |
| p90 | `200.212 ms` |
| p95 | `211.445 ms` |
| p99 | `241.626 ms` |
| Max | `296.001 ms` |
| Candidate count max | 300 |
| Delivery writes | 85 |
| Selection decision writes | 85 |
| Quota increments | 85 |
| Max sampled Postgres CPU | `8.36%` |
| Final active DB connections | 1 |
| Final non-granted locks | 0 |

## Health

| Check | Before | After | Final |
|---|---:|---:|---:|
| `/health` | 200 | 200 | 200 |
| `/ready` | 200 | 200 | 200 |
| API container | healthy | healthy | healthy |
| Postgres container | healthy | healthy | healthy |

## Log Notes

No API errors were found after the smoke window. Postgres had no runtime
failures after `2026-06-12T05:52:00Z`.

Four Postgres syntax-error log entries were caused by failed operator
verification commands while quoting SQL through SSH. They did not modify data
except for the successful documented migration and diagnostic consumer flow, and
they were not application runtime failures.

## Acceptance

Passed: 85/85 responses were `200`, no 5xx, no timeouts, p95 and p99 were below
the stop thresholds, candidate count stayed at or below 300, Postgres CPU did
not stay near 100%, production stayed healthy, non-test consumers were
unchanged, the diagnostic credential was revoked, and the temp raw key file was
removed.

This does not claim paid pilot readiness. The next separate gate remains a
protected staged load test.
