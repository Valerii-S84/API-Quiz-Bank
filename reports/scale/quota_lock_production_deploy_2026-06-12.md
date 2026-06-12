# Quota Lock Production Deploy - 2026-06-12

## Scope

Production deploy after the quota-lock scope fix was merged to GitHub `main`.

This task restarted/rebuilt only the API container. It did not restart
Postgres, apply migrations, touch real consumers or claim paid pilot readiness.

## Local Main Verification

| Check | Result |
|---|---|
| Local branch | `main` |
| Local SHA | `3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3` |
| Remote `origin/main` SHA | `3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3` |
| `git status --short` | clean |
| Quota-lock fix files in `origin/main` | yes |
| Unit tests | `python3 -m unittest discover -s tests -p "test_*.py"` -> `OK, 380 tests` |
| Secret scan | `python3 tools/no_secrets_scan.py` -> no committed secrets detected |
| Whitespace check | `git diff --check` -> passed |

## Production Preflight

| Check | Before deploy |
|---|---|
| Server host | `ubuntu-8gb-nbg1-1` |
| Server path | `/opt/api-quiz-bank` |
| Server branch | `release/next-route-hotfix-2026-06-11` |
| Server SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Server worktree | clean |
| API container | `running/healthy`, restart `0`, started `2026-06-12T05:43:07.260326705Z` |
| Postgres container | `running/healthy`, restart `0`, started `2026-05-11T15:22:22.710037082Z` |
| Health/ready | `200 / 200` |
| DB connections | `1` |
| Blocked locks | `0` |
| Non-test consumers | `41` |

## Deploy

| Check | Result |
|---|---|
| Fetch target | `origin/main` |
| Checkout/update | `git checkout main` then `git pull --ff-only origin main` |
| New server SHA | `3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3` |
| Server status after checkout | clean |
| New migrations relative to previous production checkout | none |
| Migration action | not applied |
| API rebuild/restart | `docker compose ... up --build -d --no-deps api-quiz-bank` |
| API started after | `2026-06-12T09:57:25.56175087Z` |
| API restart count after | `0` |
| Postgres started after | `2026-05-11T15:22:22.710037082Z` unchanged |
| Postgres restart count after | `0` unchanged |
| Health/ready after | `200 / 200` |
| API errors since deploy start | `0` |
| Postgres errors since deploy start | `0` |

## Protected Smoke

Evidence: `reports/scale/quota_lock_postfix_smoke_2026-06-12.json`.

| Metric | Result |
|---|---:|
| Status distribution | `{"200": 85}` |
| 5xx / timeouts | `0 / 0` |
| p95 | `311.249 ms` |
| p99 | `376.85 ms` |
| Candidate max | `300` |
| Blocked locks max | `0` |
| Max sampled Postgres CPU | `80.11%` |
| Cleanup | credential revoked, revoked-key check `403`, temp key file removed |
| Non-test consumers | `41 / 41` unchanged |

Smoke passed the requested gate.

## Lock Probe

Evidence: `reports/scale/quota_lock_probe_2026-06-12.json`.

| Metric | Result |
|---|---:|
| Profile | 20 isolated consumers, 20 rps, 60 seconds |
| Status distribution | `{"200": 1200}` |
| 5xx / timeouts | `0 / 0` |
| p95 | `2373.93 ms` |
| p99 | `2577.845 ms` |
| Candidate max | `300` |
| Blocked locks max | `0` |
| Final DB connections | `1` |
| Max sampled Postgres CPU | `101.46%` |
| Cleanup | credentials revoked, revoked-key check `403`, temp key files removed |
| Non-test consumers | `41 / 41` unchanged |

The lock probe did not pass because p95 exceeded the `1500 ms` gate and
Postgres CPU reached the near-100% range during the probe. Stage 4 and Stage 5
were therefore not run.

## Final Server State

| Check | Result |
|---|---|
| Server branch | `main` |
| Server SHA | `3c866492ec2f1a42e9dcb512c980b92ebd1fd7e3` |
| Server worktree | clean |
| API container | `running/healthy`, restart `0` |
| Postgres container | `running/healthy`, restart `0` |
| Health/ready | `200 / 200` |
| DB connections | `1` |
| Blocked locks | `0` |
| Active diagnostic credentials | `0` |
| Non-test consumers | `41` |

## Result

Production deploy from `origin/main` and protected smoke passed. The follow-up
lock probe did not pass the latency/CPU gate, so Stage 4 and Stage 5 were
stopped by gate and remain open. Paid pilot readiness is not claimed.
