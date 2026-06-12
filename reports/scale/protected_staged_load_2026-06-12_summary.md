# Protected Staged Load - 2026-06-12

## Scope

Protected staged load for `/v1/quiz-items/next` after the production hotfix deploy.

This test used isolated diagnostic consumers only. It did not deploy, rebuild,
restart, apply migrations, restart Postgres or change runtime logic.

## Result

| Field | Value |
|---|---|
| Final status | `Partial` |
| Server SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Local SHA | `de998f2dc158e42b03ac31fa48225553ad7cea21` |
| Route | `/v1/quiz-items/next` |
| Migration 011 | `applied` |
| Target indexes | `7/7` |
| Isolated consumers | `20` |
| Stop condition | `stopped_blocked_locks` |
| Stop stage | `stage_4_strong_safe_load` |
| Final health/ready | `200/200` |
| Final DB connections | `1` |
| Final blocked locks | `0` |
| Non-test consumers before/after | `23/23` |
| Credentials after cleanup | `active 0, revoked 20` |
| Temp key file removed | `true` |

## Stage Metrics

| Stage | Status | Requests | Statuses | p95 ms | p99 ms | Max ms | Candidate max | PG CPU max % | API CPU max % | Blocked locks max |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `stage_0_warm_up` | `completed` | 20 | `{"200": 20}` | 107.811 | 126.729 | 131.459 | 300 | 7.96 | 0.2 | 0.0 |
| `stage_1_single_credential_limit_check` | `completed` | 100 | `{"200": 100}` | 111.869 | 114.791 | 117.979 | 300 | 7.46 | 21.58 | 0.0 |
| `stage_2_low_multi_consumer_load` | `completed` | 1500 | `{"200": 1500}` | 119.615 | 128.272 | 147.735 | 300 | 12.82 | 21.8 | 0.0 |
| `stage_3_normal_multi_consumer_load` | `completed` | 3000 | `{"200": 3000}` | 120.511 | 129.311 | 235.564 | 300 | 8.94 | 46.32 | 0.0 |
| `stage_4_strong_safe_load` | `stopped_blocked_locks` | 1943 | `{"200": 1942, "502": 1}` | 1241.206 | 1842.176 | 2457.567 | 300 | 35.22 | 20.28 | 2.0 |

## Writes

| Metric | Count |
|---|---:|
| Deliveries | 6562 |
| Selection decisions | 6562 |
| Quota increments | 6562 |

All writes were scoped to consumers with prefix `staged-load-next-route-2026-06-12-`.

## Cleanup

| Check | Result |
|---|---|
| Diagnostic credentials revoked | `true` |
| Revoked key check | `403` |
| Temp key file removed | `true` |
| Test active credentials after cleanup | `0` |
| Test revoked credentials after cleanup | `20` |

## Notes

- Stage 4 stopped on blocked DB locks after 1943 requests; Stage 5 was not run.
- Stage 4 also had 1 transient `502`; this is below the 0.2% 5xx threshold but the blocked-lock stop condition is sufficient for `Partial`.
- One Postgres error-pattern match during Stage 2 came from an operator read-only count probe with a quoting mistake; it did not change data and was not an application runtime error.
- Protected staged load remains `Partial`. Paid pilot readiness is not claimed.
