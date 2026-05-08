# Edge/App Header Split Smoke Evidence

Date: 2026-05-08

Scope: live VPS pilot smoke after separating the edge Caddy key from the
consumer-bound app credential. Secret values were not printed or committed.

## Deployment

| Check | Result |
|---|---|
| Deployed branch | `codex/split-edge-app-credentials` |
| Deployed commit | `f7ea7ba` |
| Runtime image | `sha256:5edc1a2692c3439ca24004334679f1163d3240786ff5347fc05325c75cb81a2b` |
| Container | `api-quiz-bank-pilot` |
| Container state | `running/healthy` |
| Public route | `https://api.valerchik.de` |
| Edge header | `X-API-Key` |
| App credential header | `X-QuizBank-API-Key` |
| App credential file | `/root/api-quiz-bank/app-consumer-api-key`, mode `600 root:root` |

## Public Smoke

| Check | Result |
|---|---|
| Health with edge key | `200` |
| Readiness with edge key | `200` |
| Delivery without edge key | `401` |
| Delivery without app credential | `401 AUTH_REQUIRED` |
| Next item with both headers | `200` |
| Delivery id present | yes |
| Delivery read with both headers | `200` |
| Quota denial with both headers | `429 QUOTA_EXCEEDED` |
| Entitlement denial with both headers | `403 ENTITLEMENT_MISSING_FEATURE` |
| Answer key leaked | no |
| Explanation leaked | no |

## Decision

The edge/app credential split is proven for controlled public smoke. Broader
beta still requires owner/legal/privacy launch approval and a signed or private
security contact.
