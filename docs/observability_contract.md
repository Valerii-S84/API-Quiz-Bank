# API Quiz Bank Observability Contract

Status: local pre-pilot observability baseline; not a production monitoring claim.

## Scope

This contract defines the minimum local signals that Phase 7-9 pre-pilot
evidence must preserve. It does not create a pilot, beta or production
monitoring dashboard.

## Required Local Signals

| Signal | Source | Minimum evidence |
|---|---|---|
| Health check | `/health`, `/v1/health` | Service returns `status=ok`. |
| Readiness check | `/ready`, `/v1/ready` | Database dependency returns `status=ok`. |
| Consumer lifecycle | `audit_log` | `consumer_status_transition` records actor, status change and reason. |
| Delivery creation | `deliveries` table and API response | Delivery id exists only after eligible active consumer request. |
| Repeat denial | Problem Details response | Repeat request returns `SELECTION_NO_ELIGIBLE_ITEM`. |
| Quota denial | Problem Details response | Quota-exhausted consumer returns `QUOTA_EXCEEDED`. |
| Support containment | CLI + audit log | `transition-consumer-status` can suspend/block/reactivate a consumer. |
| Rollback/disable | runbook evidence | Local rollback tabletop names containment and recovery path. |

## Event Names

Local reports should use these canonical event labels:

- `health`
- `ready`
- `consumer_status_transition`
- `delivery_created`
- `selection_denial`
- `quota_denial`
- `rollback_tabletop`

## Redaction Rules

Observability artifacts must not include secrets, tokens, private headers,
raw credential files, full external request dumps or real learner personal data.

## Phase Boundary

This contract supports local pre-pilot evidence only. Pilot, beta or production
observability still requires an external log source, monitoring owner, alert
cadence, dashboard or equivalent operational review evidence.
