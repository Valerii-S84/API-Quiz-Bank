# Next Route Production Hotfix Deploy - 2026-06-12

## Scope

Production deploy of hotfix `/v1/quiz-items/next`, migration `011`, API-only
rebuild/restart, protected smoke, cleanup and sanitized evidence.

This task did not run a full load test and does not claim paid pilot readiness.

## Local Preflight

| Check | Result |
|---|---|
| Local host | `DESKTOP-LLPPQ70` |
| Local user | `serputko` |
| Local path | `/mnt/c/Users/User/Desktop/API Quiz Bank` |
| Local branch | `codex/release-governance-evidence` |
| Local SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Remote branch | `origin/release/next-route-hotfix-2026-06-11` |
| Hotfix commit in remote branch | `yes` |
| Unit tests | `python3 -m unittest discover -s tests -p "test_*.py"` -> `OK, 372 tests` |
| Secret scan | `python3 tools/no_secrets_scan.py` -> `No committed secrets detected.` |
| Whitespace check | `git diff --check` -> passed |

Local worktree had existing report changes before this task; they were not
reverted.

## Production Preflight

| Check | Before deploy |
|---|---|
| Server host | `ubuntu-8gb-nbg1-1` |
| Server user | `root` |
| Server path | `/opt/api-quiz-bank` |
| Old server branch | `main` |
| Old server SHA | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| API container | `running/healthy`, restart `0`, started `2026-06-08T12:28:26.861683099Z` |
| Postgres container | `running/healthy`, restart `0`, started `2026-05-11T15:22:22.710037082Z` |
| Health/ready | `200 / 200` |
| Load average | `0.22, 0.23, 0.26` |
| Memory | `7745 MiB total`, `3809 MiB available` |
| Disk `/` | `150G`, `22G used`, `123G available`, `15%` |
| API CPU baseline | `0.17%` |
| Postgres CPU baseline | `4.19%` |
| Active DB connections | `1` |
| Non-granted locks | `0` |
| Non-test consumers before | `22` |

## Dirty Worktree Handling

Dirty tracked server files were backed up and stashed before checkout.

| Field | Value |
|---|---|
| Dirty tracked count | `2` |
| Dirty files | `src/quizbank_mvp/trusted_delivery.py`, `tests/test_shorts_factory_backend.py` |
| Backup path | `/root/api-quiz-bank-dirty-backup-20260612-054009` |
| Patch backup | `/root/api-quiz-bank-dirty-backup-20260612-054009/server_dirty_worktree.patch` |
| Stash ref | `stash@{0} be0713dade0968e3ac61b1e61e2a31a89e8aa09e` |
| Post-stash status | clean |

Detailed sanitized evidence is in
`reports/scale/server_dirty_worktree_deploy_handling_2026-06-12.md`.

## Checkout

| Check | Result |
|---|---|
| Fetch | `origin/release/next-route-hotfix-2026-06-11` fetched through explicit refspec |
| Checkout | local server branch `release/next-route-hotfix-2026-06-11` from remote ref |
| New server SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Server status after checkout | clean |

## Migration 011

| Check | Result |
|---|---|
| `001`-`010` applied before | `10` |
| `011` applied before | `0` |
| Safety review | 7 `CREATE INDEX IF NOT EXISTS`, 0 `DROP`, 0 `DELETE`, 0 `TRUNCATE`, 0 `ALTER` |
| Applied `011` after | `1` |
| Target indexes verified | `7 / 7` |
| Postgres restart | not performed |
| Postgres after migration | `running/healthy`, `pg_isready=ready` |

Detailed migration evidence is in
`reports/scale/next_route_postgres_migration_011_2026-06-12.md`.

## API Rebuild / Restart

| Check | Result |
|---|---|
| Compose files | existing project compose labels: base, PostgreSQL override, server-only secrets override |
| Command scope | API service only with `--no-deps` |
| API started before | `2026-06-08T12:28:26.861683099Z` |
| API started after | `2026-06-12T05:43:07.260326705Z` |
| Postgres started before/after | `2026-05-11T15:22:22.710037082Z` unchanged |
| API after restart | `running/healthy`, restart `0` |
| Postgres after API restart | `running/healthy`, restart `0` |
| Health/ready after | `200 / 200` |
| API errors since deploy start | none found |
| Postgres runtime errors since deploy start | none found |

## Protected Smoke

| Metric | Result |
|---|---:|
| Total requests | 85 |
| Status distribution | `{"200": 85}` |
| 5xx/timeouts | `0 / 0` |
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
| Health before/after/final | `200/200`, `200/200`, `200/200` |

Detailed smoke evidence is in
`reports/scale/next_route_postfix_smoke_2026-06-12.json` and
`reports/scale/next_route_postfix_smoke_2026-06-12_summary.md`.

## Cleanup

| Check | Result |
|---|---|
| Diagnostic consumer | `postfix-smoke-next-route-2026-06-12` |
| Key fingerprint | `491f0e93a18ca623` |
| Raw key printed | `no` |
| Credential status after cleanup | `revoked` |
| Temp raw key file removed | `yes` |
| Revoked credential check | `403`, not usable |
| Non-test consumers after cleanup | `22` |
| API/Postgres final state | `running/healthy` / `running/healthy` |

## Rollback

Rollback was not needed and was not performed.

Documented rollback path remains: checkout the old server SHA
`904babbd998adcf43cfbc7945d5f24d499ec47c4`, rebuild/restart only the API
service, leave non-destructive indexes in place, then verify health/ready and
record rollback evidence.

## Log Notes

Postgres logs contain four operator SQL syntax errors caused by failed quoted
verification/update commands while routing SQL through SSH. They occurred at
`2026-06-12T05:39:05Z`, `2026-06-12T05:41:51Z`,
`2026-06-12T05:49:33Z`, and `2026-06-12T05:51:11Z`.

Final log check after `2026-06-12T05:52:00Z` found no API errors and no
Postgres runtime failures.

## Result

Production is on the hotfix SHA, migration `011` is applied, target indexes are
verified, only the API container was rebuilt/restarted, protected smoke passed,
candidate count stayed at 300 or below, sampled Postgres CPU stayed far below
100%, production remained healthy, non-test consumers were unchanged, the
diagnostic credential was revoked, and the temp raw key file was removed.
