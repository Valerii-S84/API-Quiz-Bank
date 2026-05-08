# API Quiz Bank Incident Response Runbook

Status: MVP-local incident path and future pilot/beta/production gate baseline.

## Scope

Use this runbook for content safety, API access, delivery, entitlement/quota,
privacy/security and operational incidents.

This runbook does not prove production incident readiness without an assigned
owner, reachable support channel, monitoring source and completed drill evidence.

## Severity Model

| Severity | Meaning | First response |
|---|---|---|
| S1 critical | Unauthorized data exposure, real external delivery of blocked content, destructive data loss, active credential exposure | Contain immediately, preserve evidence, notify owner through private channel |
| S2 important | Consumer access mismatch, repeated delivery failure, incorrect quota/entitlement behavior, privacy request mishandled | Suspend affected consumer or delivery path, open incident record |
| S3 routine | Incorrect item metadata, isolated support defect, non-sensitive report mismatch | Triage and schedule fix through normal issue path |
| S4 low-risk | Documentation or non-operational quality issue | Record and batch with normal maintenance |

## Minimum Incident Record

- incident_id
- opened_at
- reporter or detection source
- environment
- affected consumer/channel/item/source
- severity
- suspected category
- containment action
- owner
- evidence artifacts
- status
- follow-up decision

## First Containment Paths

| Incident class | Containment |
|---|---|
| Bad item delivered | Transition item to `blocked` or `retired`, preserve delivery log and audit log. |
| Consumer access problem | Transition consumer to `suspended` with `transition-consumer-status`, preserve quota and delivery rows. |
| Entitlement/quota problem | Disable entitlement or set quota to zero through governed DB/admin path. |
| Import/source problem | Stop publication/import promotion, rerun dry-run import, preserve checksum and report evidence. |
| Telegram delivery problem | Stop real sends, keep dry-run or failed-send logs, verify no raw CSV path was used. |
| Privacy/security issue | Use private channel, avoid public details, follow `runbooks/privacy_request_workflow.md` and `SECURITY.md`. |

## MVP Local Consumer Suspension Command

```bash
PYTHONPATH=src python3 -m quizbank_mvp.cli \
  --db-path var/quizbank_mvp.sqlite3 \
  transition-consumer-status \
  --consumer-id consumer_demo \
  --to-status suspended \
  --actor local_admin \
  --reason "incident containment"
```

Reactivation uses the same command with `--to-status active` after review.

## Closure Criteria

An incident is closed only when:

- containment is recorded;
- affected evidence is preserved;
- root cause or unresolved status is documented;
- follow-up owner is named;
- any launch-gate impact is reflected in `reports/roadmap/roadmap_evidence_register.md`.
