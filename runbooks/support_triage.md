# API Quiz Bank Support and Issue Triage Runbook

Status: MVP-local support path and future pilot/beta gate placeholder.

## Intake Channels

Use private owner-approved channels for security, privacy, billing or sensitive learner data.
Do not place secrets, raw tokens, private identifiers or full request dumps in public issues.

## Triage Fields

- issue_id
- reporter or internal owner
- affected consumer/channel/environment
- category: content, API, delivery, entitlement/quota, privacy/security, ops, demo
- severity: S1 critical, S2 important, S3 routine, S4 low-risk
- reproduction command or artifact
- containment action
- owner
- status

## MVP Containment Paths

| Issue | First containment |
|---|---|
| Draft/blocked/retired item delivered | Block item, preserve delivery log, open incident record. |
| Wrong entitlement/quota behavior | Suspend affected consumer access and preserve quota records. |
| API access mismatch | Verify `X-Consumer-Id` behavior and delivery ownership checks. |
| Import/source issue | Stop publication, rerun dry-run import, preserve checksum evidence. |
| Privacy/security issue | Follow `runbooks/incident_response.md`, `runbooks/privacy_request_workflow.md` and `SECURITY.md`. |

## MVP Consumer Suspension Path

Use the governed CLI path for local MVP consumer suspension:

```bash
PYTHONPATH=src python3 -m quizbank_mvp.cli \
  --db-path var/quizbank_mvp.sqlite3 \
  transition-consumer-status \
  --consumer-id consumer_demo \
  --to-status suspended \
  --actor local_admin \
  --reason "support containment"
```

Record the related audit log entry with the support issue.

## Pilot/Beta Requirements

- Named support owner.
- Consumer suspension path tested.
- Incident path linked from support records.
- Privacy/security escalation route confirmed.
- Quality issue reporting visible to pilot/beta consumers.
