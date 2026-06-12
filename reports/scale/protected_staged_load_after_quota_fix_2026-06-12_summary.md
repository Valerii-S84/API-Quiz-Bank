# Protected Staged Load After Quota Fix - 2026-06-12

## Scope

Gate-controlled rerun after the quota-lock production deploy to `main`.

Stage 4 and Stage 5 were allowed only if protected smoke and the short lock
probe both passed.

## Gate Results

| Gate | Result |
|---|---|
| Production deploy from `origin/main` | passed |
| API-only rebuild/restart | passed |
| Postgres restart | not performed |
| Migrations | not applied; no new migrations relative to previous production checkout |
| Protected smoke | passed |
| Lock probe | failed latency/CPU gate |
| Stage 4 | skipped |
| Stage 5 | skipped |

## Protected Smoke

| Metric | Value |
|---|---:|
| Requests | 85 |
| Status distribution | `{"200": 85}` |
| 5xx | 0 |
| Timeouts | 0 |
| p95 | `311.249 ms` |
| p99 | `376.85 ms` |
| Candidate max | 300 |
| Blocked locks max | 0 |
| Max sampled Postgres CPU | `80.11%` |

## Lock Probe

| Metric | Value |
|---|---:|
| Isolated consumers | 20 |
| Target rate | 20 rps |
| Duration | 60 seconds |
| Requests | 1200 |
| Status distribution | `{"200": 1200}` |
| 5xx | 0 |
| Timeouts | 0 |
| p95 | `2373.93 ms` |
| p99 | `2577.845 ms` |
| Candidate max | 300 |
| Blocked locks max | 0 |
| Final DB connections | 1 |
| Max sampled Postgres CPU | `101.46%` |

## Stop Reason

The lock probe did not pass the required p95 `< 1500 ms` gate. Sampled
Postgres CPU also reached the near-100% range. The hard gate therefore blocked
Stage 4 and Stage 5.

## Cleanup

| Check | Result |
|---|---|
| Diagnostic credentials | revoked |
| Revoked-key check | `403` |
| Temp raw key files | removed |
| Active diagnostic credentials after final cleanup | `0` |
| Non-test consumers | unchanged at `41` |
| Final health/ready | `200 / 200` |
| Final blocked locks | `0` |
| Final DB connections | `1` |

## Result

`Partial`: deploy and smoke passed, but Stage 4 and Stage 5 were not run
because the short lock probe failed the latency/CPU gate. This does not claim
paid pilot readiness.
