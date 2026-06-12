# Protected Staged Load After Read Path Fix

Date: 2026-06-12.

Status: `Partial`.

The read-path CPU fix was deployed from `origin/main`
`a46d33f41fabf685dcfbc2cda98f5967f906cbc2` to production. The old server SHA
was `3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3`; the new server SHA is
`a46d33f41fabf685dcfbc2cda98f5967f906cbc2`.

## Gate Results

| Gate | Result |
|---|---|
| Protected smoke | passed |
| CPU/lock probe | failed |
| Stage 4 | not run |
| Stage 5 | not run |

## Smoke Metrics

| Metric | Result |
|---|---:|
| Requests | `85/85` `200` |
| 5xx / timeouts | `0 / 0` |
| p95 / p99 | `268.541 ms / 285.381 ms` |
| Candidate max | `150` |
| Blocked locks max | `0` |
| Postgres CPU max | `51.47%` |
| Delivery / quota increments | `85 / 85` |

## Probe Metrics

| Metric | Result |
|---|---:|
| Requests | `1200/1200` `200` |
| 5xx / timeouts | `0 / 0` |
| p95 / p99 | `1696.847 ms / 1905.301 ms` |
| Candidate max | `150` |
| Blocked locks max | `0` |
| Postgres CPU max | `103.01%` |
| Postgres CPU > 90% longest span | `64 s` |
| Delivery / quota increments | `1200 / 1200` |

## Stage 4 / Stage 5

Stage 4 and Stage 5 were not run because the CPU/lock probe failed. This
preserves the staged gate rule: no stronger load or soak runs after a failed
preceding production gate.

## Cleanup

| Check | Result |
|---|---:|
| Diagnostic credentials revoked | `23` |
| Revoked-key checks | `403 / 403` |
| Active diagnostic credentials final | `0` |
| Non-test consumers before / after | `42 / 42` |
| Temp raw key files | none created; none remaining |
| Final health / ready | `200 / 200` |
| Final blocked locks | `0` |
| Final DB connections | `1` |
| API / Postgres final state | `running/healthy` / `running/healthy` |

Conclusion: the production read path improved candidate bounds and passed the
short smoke, but still does not pass the CPU/lock probe gate required before
Stage 4 and Stage 5.
