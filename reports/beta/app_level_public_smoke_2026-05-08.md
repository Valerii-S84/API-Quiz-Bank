# App-Level Public Credential Smoke Evidence

Date: 2026-05-08

Scope: live VPS deployment and protected public route smoke after app-level
consumer-bound API credentials were deployed. Secret values were not printed or
committed.

## Deployment

| Check | Result |
|---|---|
| Source checkout | clean worktree from `origin/main` |
| Deployed commit | `2919f22` |
| Image | `api-quiz-bank:pilot` / `sha256:17149a8daea866b56faf8607a1621cea29ec24cfb096356a9971da14c562e80e` |
| Runtime container | `api-quiz-bank-pilot` |
| Container state | `running` |
| Public bind | `127.0.0.1:8010` |
| Local health | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Local readiness | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |

The deploy preserved local VPS compose/secrets changes by building from a clean
worktree and recreating the existing service with the existing VPS compose file.

## Public Route Smoke

| Check | Result |
|---|---|
| Public endpoint | `https://api.valerchik.de` |
| Health with key | `200` |
| Readiness with key | `200` |
| Missing key delivery | `401` |
| Next item with app credential | `200` |
| Delivery id present | yes |
| Delivery read | `200` |
| Quota denial | `429 QUOTA_EXCEEDED` |
| Entitlement denial | `403 ENTITLEMENT_MISSING_FEATURE` |
| Answer key leaked | no |
| Explanation leaked | no |

## Boundary

The edge Caddy key is currently also seeded as the app credential for controlled
smoke consumers because the public route and app both use `X-API-Key`. This is
acceptable for this controlled smoke but should be split into separate edge and
consumer credential headers before broader beta.
