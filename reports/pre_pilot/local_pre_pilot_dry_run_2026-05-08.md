# Local Pre-Pilot Dry Run Evidence

Date: 2026-05-08

Scope: local only; no pilot, beta, production or external send.

## Result

```json
{
  "audit_summary": {
    "consumer_transitions": [
      "active->suspended",
      "suspended->blocked",
      "blocked->active"
    ],
    "delivery_count": 1
  },
  "auth_behavior": {
    "reason_code": "AUTH_INVALID_API_KEY",
    "status_code": 401
  },
  "consumer_lifecycle": {
    "blocked_denial": {
      "delivery_created": false,
      "reason_code": "CONSUMER_NOT_ACTIVE",
      "status_code": 403
    },
    "reactivated_allowed": {
      "delivery_created": true,
      "reason_code": null,
      "status_code": 200
    },
    "states": [
      "active",
      "suspended",
      "blocked",
      "active"
    ],
    "suspended_denial": {
      "delivery_created": false,
      "reason_code": "CONSUMER_NOT_ACTIVE",
      "status_code": 403
    }
  },
  "health": "ok",
  "observability_events": [
    "health",
    "ready",
    "consumer_status_transition",
    "delivery_created",
    "auth_denial",
    "selection_denial",
    "quota_denial"
  ],
  "quota_behavior": {
    "delivery_created": false,
    "reason_code": "QUOTA_EXCEEDED",
    "status_code": 429
  },
  "ready": "ok",
  "repeat_behavior": {
    "delivery_created": false,
    "reason_code": "SELECTION_NO_ELIGIBLE_ITEM",
    "status_code": 404
  }
}
```

## Limitation

This proves local pre-pilot behavior only. It is not external pilot,
public beta or production readiness evidence.
