# Stage 4 502 Analysis - 2026-06-12

## Inputs

- `reports/scale/protected_staged_load_2026-06-12.json`
- `reports/scale/protected_staged_load_2026-06-12_summary.md`
- `reports/scale/protected_staged_load_server_sanity_2026-06-12.json`
- Production API/Postgres logs for the Stage 4 window
- Controlled lock probe `lock_diag_20260612T083653Z_700f4f98`

## Stage 4 Facts

Stage 4 ran from `2026-06-12T08:03:48Z` to
`2026-06-12T08:07:17Z` and stopped on blocked DB locks after `1943`
requests.

Status distribution:

- `200`: `1942`
- `502`: `1`
- timeouts: `0`

Latency and runtime pressure:

- p95 `1241.206 ms`
- p99 `1842.176 ms`
- max `2457.567 ms`
- DB connections max `26`
- blocked locks max `2`
- Postgres CPU max `35.22%`
- API CPU max `20.28%`

The committed staged-load report does not include per-request records, so the
exact timestamp and latency of the single client-observed `502` are not present
in the existing artifacts.

## Log Check

Filtered API container logs for `2026-06-12T08:03:48Z` through
`2026-06-12T08:07:17Z` showed `/v1/quiz-items/next` `200 OK` entries and no
app-side 5xx, traceback, exception or fatal error. The only non-200 entry near
the end of the inspected window was the expected cleanup revoked-key check,
which returned `403` after Stage 4.

Postgres error-pattern scans in the Stage 4 report were `0`.

## Controlled Probe Result

The short probe did not reproduce a `502`; it stopped earlier on the first
blocked lock as required:

- run: `lock_diag_20260612T083653Z_700f4f98`
- requests: `31`
- statuses: `{"200": 31}`
- 5xx/timeouts: `0`
- stop: `blocked_locks_detected`

The captured lock was:

- blocked query type: `INSERT INTO quota_usage`
- lock type: `transactionid`
- blocker query type at sample: `SELECT FROM deliveries`

## Conclusion

The `502` is not supported by evidence as a FastAPI handler exception or a
Postgres error. It is narrowed to a transient edge/client-side failure during
the same Stage 4 latency and blocked-lock window.

The proven database root cause for the Stage 4 stop is the quota row update
transaction lock on `quota_usage`, held too long while the transaction continues
through delivery-history reads and later writes. Treat the `502` as a secondary
symptom until a future run captures per-request client timing or edge logs with
the same sanitized discipline.

