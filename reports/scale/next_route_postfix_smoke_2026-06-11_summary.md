# Next Route Postfix Smoke - 2026-06-11

Status: `Partial`.

The protected production postfix smoke was not run because the production
hotfix deploy was stopped before any write.

## Smoke Profile

| Step | Result |
|---|---|
| Warm-up 5 sequential | not run |
| Main 50 sequential | not run |
| Optional concurrency 3 / 30 total | not run |
| Full staged load test | not run |

## Evidence

| Check | Result |
|---|---|
| Local SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Server old SHA | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| Server new SHA | not created |
| Migrations applied | none |
| Indexes confirmed before deploy | target `011` indexes absent |
| Health before stop | API/PostgreSQL healthy, health/ready `200` / `200` |
| Health after stop | API/PostgreSQL healthy, health/ready `200` / `200` |
| Test consumer | `postfix-smoke-next-route-2026-06-11` was not created |
| Key fingerprint | none |
| Request count | `0` |
| Status codes | none |
| Delivery writes | `0` |
| Selection decision writes | `0` |
| Quota increments | `0` |
| Candidate count max | not measured |
| Non-test consumers before | `11` |
| Non-test consumers after | not changed by this pass |
| Credential revoked | not applicable; no credential created |
| Raw key file removed | not applicable; no raw key file created |

## Decision

No latency, p95/p99 or CPU improvement claim is made from production because the
post-fix production code was not deployed. The local synthetic proof remains the
only post-fix performance proof in this pass.
