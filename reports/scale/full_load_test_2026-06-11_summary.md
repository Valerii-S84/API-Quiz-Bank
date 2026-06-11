# Full Load Test 2026-06-11

Status: `Partial`.

The full staged production load test was stopped during warm-up. The isolated
consumer `load-test-full-2026-06-11` was created through the runtime API
container DB path with quota `30000`, and only its hash fingerprint was recorded.
The raw key was not printed and the test credential was revoked after the stop.

## Result

| Check | Result |
|---|---|
| Route | `/v1/quiz-items/next` |
| Isolated test writes | 20 deliveries / 20 quota increments |
| Non-test consumers | 19 before / 19 after |
| Containers after stop | API healthy, Postgres healthy, restart count 0 |
| Public health/ready after stop | 200 / 200 |
| API log grep | 0 matches for 5xx/error/timeout patterns |
| Postgres log grep | 1 diagnostic quoting error from the agent probe, not a repeated load error |
| Full stages 1-5 | Not run |

## Stop Reason

The unfiltered warm-up was stopped before stage 1 because resource and latency
risk appeared too early: after 20 isolated writes, Postgres CPU snapshots reached
about 100%, and the warm-up client did not print a final client latency summary
before the targeted stop at about 96 seconds.

The effective app delivery rate limit is `120` requests per `60` seconds per
consumer credential. Running the requested profile with one key would either
hit 429s or require extra isolated credentials that were not created.

## Decision

Do not treat this as paid-pilot readiness. Production remained healthy, real
clients were not touched, and all writes stayed in the isolated test namespace,
but the full staged load profile was not proven.
