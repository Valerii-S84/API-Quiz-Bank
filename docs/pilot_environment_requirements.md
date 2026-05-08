# Pilot Environment Requirements

Status: pilot execution package requirement document; no environment created.

## Scope

This document defines the minimum requirements for a future controlled pilot
environment. It is not evidence that such an environment exists.

## Environment Identity

| Requirement | Required pilot evidence |
|---|---|
| Environment name | Stable name such as `pilot-YYYYMM` or equivalent. |
| Owner | Named person or role accountable for launch, rollback and evidence. |
| Purpose | Closed pilot only; not public beta or production. |
| Access boundary | List of operators allowed to access runtime, logs, backups and Telegram controls. |
| Data boundary | Explicit statement that raw CSV is not served directly to consumers. |
| Version | Git commit SHA, migration version and release notes for pilot build. |

## Runtime Requirements

- API service reachable only through approved pilot access path.
- Health endpoint available.
- Readiness endpoint validates database dependency.
- Canonical selection path used for delivery.
- Consumer status, entitlement, quota and repeat policy enforced.
- Delivery log persisted for all created, skipped, failed or denied delivery attempts.
- Admin/operator control path can suspend, block and reactivate a consumer.

## Telegram Requirements

- Telegram target is represented as governed consumer, not only a chat id.
- Bot token or credential is stored outside Git and never printed in logs.
- Dry-run mode is available before controlled real send.
- Controlled real send requires explicit approval and small recipient scope.
- Send result captures success, failure, skipped or cancelled outcome.
- Failure path is visible in monitoring or operator review artifact.

## Data Requirements

- Pilot dataset is approved for pilot scope.
- Items are `approved` or `published` according to environment policy.
- Source traceability is preserved: source id, source type and provenance note.
- Correct answer is not exposed outside authorized delivery/attempt flow.
- No draft, blocked or retired item is deliverable.

## Backup and Restore Requirements

- Backup mechanism identified before launch.
- Backup owner named.
- Backup schedule and retention window recorded.
- Restore target isolated from active pilot runtime.
- Restore drill report recorded before pilot gate can be closed.
- Backup artifacts are access-controlled.

## Monitoring and Alert Requirements

- Health/readiness review cadence defined.
- Delivery failure and denial counts visible.
- Telegram send failure visible if Telegram is in pilot scope.
- Backup success/failure visible or owner-reviewed.
- Critical incident notification path named.
- Evidence retention location named.

## Support and Incident Requirements

- Support intake channel named.
- Security/privacy escalation path named.
- Consumer suspension path tested in pilot environment.
- Incident owner named for pilot window.
- Evidence template available for support and incident records.

## Required Server-Side Evidence

Before the pilot gate can be considered for closure, collect:

- environment identity record;
- deployed commit/version record;
- health/readiness output from the pilot environment;
- backup execution evidence;
- restore drill evidence;
- monitoring or owner-review evidence;
- Telegram dry-run or approved controlled-send evidence;
- consumer lifecycle evidence from the pilot environment;
- delivery/repeat/quota evidence from the pilot environment;
- support/incident contact evidence;
- go/no-go decision record.

## Non-Closure Rule

This requirements document does not close the pilot gate. The pilot gate remains
open until the server-side evidence above is produced and reviewed.
