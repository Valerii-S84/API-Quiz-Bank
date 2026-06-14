# Read Path CPU Production Deploy

Date: 2026-06-12.

Scope: deploy the `/v1/quiz-items/next` read-path CPU fix from GitHub `main`,
run protected smoke and the CPU/lock probe, then stop before Stage 4/Stage 5 if
any gate fails.

## Git / Deploy

| Check | Result |
|---|---|
| Fix commit | `46db9787691edc0583ea273fd2aeaea32b761d92` |
| PR | `#40` |
| Origin main SHA | `a46d33f41fabf685dcfbc2cda98f5967f906cbc2` |
| Old server SHA | `3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3` |
| New server SHA | `a46d33f41fabf685dcfbc2cda98f5967f906cbc2` |
| Server branch | `main` |
| Server tree before deploy | clean |
| Server tree after checkout | clean |
| New migrations | none |
| Migration action | not applied |
| API action | rebuilt/restarted only `api-quiz-bank` with `--no-deps` |
| Postgres action | not restarted |

Deploy command used the same compose file set as the running API container:

- `docker-compose.api-quiz-bank.yml`
- `docker-compose.api-quiz-bank.postgres.yml`
- `docker-compose.api-quiz-bank.secrets.yml`

## Production Preflight

| Check | Result |
|---|---:|
| API state | `running/healthy`, restart `0` |
| Postgres state | `running/healthy`, restart `0` |
| Health / ready | `200 / 200` |
| Non-test consumers | `42` |
| Active diagnostic credentials | `0` |
| DB connections | `1` |
| Blocked locks | `0` |

## Post-Deploy Health

| Check | Result |
|---|---:|
| API started after deploy | `2026-06-12T12:29:15.581030596Z` |
| API restart count | `0` |
| Postgres started after deploy | `2026-05-11T15:22:22.710037082Z` unchanged |
| Postgres restart count | `0` unchanged |
| Health / ready after deploy | `200 / 200` |
| API runtime error count since deploy | `0` |
| Postgres error count since deploy | `0` |

## Protected Smoke

Evidence: `reports/scale/read_path_postfix_smoke_2026-06-12.json`.

| Metric | Result |
|---|---:|
| Status distribution | `{"200": 85}` |
| 5xx / timeouts | `0 / 0` |
| p95 / p99 | `268.541 ms / 285.381 ms` |
| Candidate max | `150` |
| Blocked locks max | `0` |
| Postgres CPU max | `51.47%` |
| DB connections max | `3` |
| Delivery / quota increments | `85 / 85` |
| Gate | passed |

## CPU / Lock Probe

Evidence: `reports/scale/read_path_cpu_lock_probe_2026-06-12.json`.

| Metric | Result |
|---|---:|
| Status distribution | `{"200": 1200}` |
| 5xx / timeouts | `0 / 0` |
| p95 / p99 | `1696.847 ms / 1905.301 ms` |
| Candidate max | `150` |
| Blocked locks max | `0` |
| DB connections max | `20` |
| Postgres CPU max | `103.01%` |
| Postgres CPU > 90% longest span | `64 s` |
| Delivery / quota increments | `1200 / 1200` |
| Gate | failed |

The probe failed because p95 exceeded `1500 ms` and Postgres CPU stayed above
`90%` longer than `30 s`. Stage 4 and Stage 5 were not run.

## Cleanup

| Check | Result |
|---|---:|
| Diagnostic credentials revoked | `23` |
| Revoked-key checks | `403 / 403` |
| Active diagnostic credentials final | `0` |
| Temp raw key files | none created; none remaining |
| Temp harness files | removed |
| Non-test consumers before / after | `42 / 42` |
| Final health / ready | `200 / 200` |
| Final DB connections | `1` |
| Final blocked locks | `0` |
| Final API state | `running/healthy`, restart `0` |
| Final Postgres state | `running/healthy`, restart `0` |
| Final API CPU/RAM | `0.17%`, `59.21MiB / 512MiB` |
| Final Postgres CPU/RAM | `0.17%`, `156.7MiB / 512MiB` |

## Conclusion

Status: `Partial`.

The fix was committed, merged to `main`, deployed from `origin/main`, and the
protected smoke passed. The CPU/lock probe did not pass the latency and sustained
Postgres CPU gates, so Stage 4 and Stage 5 remained blocked.
