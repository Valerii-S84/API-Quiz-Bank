# Monitoring and Alerts Runbook

Status: Public MVP / Protected Beta owner-review monitoring protocol; not a
production monitoring system.

## Scope

This runbook defines monitoring and alert expectations for controlled pilot and
Public MVP / Protected Beta operation. It records an owner-reviewed monitoring
surface, not an external dashboard or production alerting system.

## Minimum Pilot Signals

| Signal | Required evidence |
|---|---|
| Service health | `/health` or equivalent output from pilot environment. |
| Service readiness | `/ready` or dependency readiness output. |
| Delivery creation | Count and log excerpt for created deliveries. |
| Auth denial | `AUTH_REQUIRED`, `AUTH_INVALID_API_KEY`, `AUTH_CONSUMER_MISMATCH` or inactive credential/consumer count. |
| Selection denial | Reason codes for no eligible item, repeat denial or status denial. |
| Quota denial | `QUOTA_EXCEEDED` count or log excerpt. |
| Consumer status transition | Audit rows for suspend/block/reactivate. |
| Telegram send outcome | Sent, failed, skipped, cancelled or dry-run result. |
| Backup job | Success/failure status or owner-reviewed backup record. |
| Incident/support intake | Link or record for support/security issue path. |

## Alert or Review Cadence

For closed pilot, one of these must exist:

- automated alert to named owner; or
- daily owner-reviewed operational checklist; or
- launch-window live monitoring by named operator.

## Suggested Pilot Alert Conditions

- `/ready` fails.
- API credential denial spikes or cross-consumer mismatch occurs.
- delivery failure count exceeds pilot threshold.
- Telegram send failure occurs.
- blocked/suspended consumer receives delivery.
- draft/blocked/retired item is selected.
- backup job fails.
- support/security issue is opened.

## Evidence Template

Each monitoring review should record:

- review id;
- time window;
- environment;
- owner;
- signals checked;
- anomalies;
- containment action;
- follow-up owner.

## Public MVP / Protected Beta Evidence

Protected beta monitoring is closed by owner-reviewed evidence only:

- `reports/observability/public_mvp_monitoring_review_2026-05-08.md`;
- `reports/beta/vps_live_ops_evidence_2026-05-08.md`;
- `reports/beta/backup_timer_evidence_2026-05-08.md`;
- `reports/rollback/public_mvp_runtime_rollback_drill_2026-05-08.md`.

This surface covers health, readiness, smoke result, delivery/credential
failure signals, auth failures, quota denial, backup timer status, backup
result, restore drill result and rollback/disable evidence.

## Non-Closure Rule

This runbook does not close production monitoring readiness. Production
monitoring readiness requires an external log source, dashboard, alert rule,
incident owner and production drill evidence.
