# Monitoring and Alerts Runbook

Status: Public MVP / Protected Beta owner-review monitoring protocol plus
owner-operated protected production runtime monitor/alert contract.

## Scope

This runbook defines monitoring and alert expectations for controlled pilot,
Public MVP / Protected Beta and the owner-operated protected production API
runtime. The production path is limited to `X-API-Key` protected operation and
does not approve broad public, school or paid launch.

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

## Protected Production Monitor Contract

The protected production runtime monitor is
`scripts/api_quiz_bank_production_monitor_snapshot.sh`.

It records a timestamped Markdown snapshot under
`API_QUIZ_BANK_MONITOR_REPORT_DIR` and fails the timer run when any required
production signal is outside the expected boundary.

Required protected production signals:

- public `/health` without `X-API-Key` returns `401`;
- protected `/health` with `X-API-Key` returns `200`;
- protected `/ready` with `X-API-Key` returns `200`;
- public delivery request without `X-API-Key` returns `401`;
- API container is `running/healthy`;
- PostgreSQL container is `running/healthy`;
- PostgreSQL backup timer is `active`;
- latest PostgreSQL backup service result is `success/0`;
- disk usage is at or below `API_QUIZ_BANK_DISK_USED_MAX_PERCENT`;
- available memory is at or above `API_QUIZ_BANK_MEM_AVAILABLE_MIN_MB`;
- API and PostgreSQL container restart counts are at or below
  `API_QUIZ_BANK_CONTAINER_RESTART_MAX`.

Failure notification:

- set `API_QUIZ_BANK_ALERT_WEBHOOK_URL` to an owner-controlled webhook endpoint;
- the monitor sends a text/plain failure notification with timestamp, report
  path and failed checks;
- the webhook URL and API key are not written to monitor reports or alert
  payloads;
- if the webhook is not configured, the monitor still records failure and exits
  non-zero for systemd/provider timer alerting.

Covered alert classes:

- `/ready` failure;
- backup timer or latest backup service failure;
- disk pressure;
- low memory;
- API/PostgreSQL container health failure;
- API/PostgreSQL container restart anomaly;
- protected-route auth boundary failure.

## Non-Closure Rule

This runbook closes monitoring/alerting only for the owner-operated protected
production API runtime when the monitor timer is active and either the webhook
is configured or the timer provider surfaces non-zero exits to the named owner.
External SaaS dashboarding, paging vendor integration and broader launch
monitoring remain separate scale decisions.
