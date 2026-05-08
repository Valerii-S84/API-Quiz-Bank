# API Quiz Bank Support and Issue Triage Runbook

Status: Public MVP / Protected Beta support path baseline; not a production
support SLA.

## Intake Channels

Use private owner-approved channels for security, privacy, billing or sensitive
learner data. Do not place secrets, raw tokens, private identifiers or full
request dumps in public issues.

Public MVP / Protected Beta intake exposes these user-visible paths:

- GitHub `support_abuse` issue template for non-sensitive delivery, content,
  access/quota, abuse and privacy-routing issues;
- `SECURITY.md` for security and sensitive-report routing;
- `runbooks/privacy_request_workflow.md` for export, deletion, correction and
  access-scope complaints;
- owner-reviewed internal triage register for every protected beta issue.

Private sensitive contact is recorded without public contact details in
`reports/compliance/public_mvp_support_security_contact_2026-05-08.md`.

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

## Public MVP / Protected Beta Gate

| Requirement | Status | Evidence |
|---|---|---|
| Named support owner | closed for protected beta | project owner / authorized VPS operator |
| Consumer suspension path tested | closed for protected beta | `reports/rollback/public_mvp_runtime_rollback_drill_2026-05-08.md` |
| Incident path linked from support records | closed for protected beta | `runbooks/incident_response.md` and this runbook |
| Privacy/security escalation route confirmed | closed for protected beta | `SECURITY.md` and `reports/compliance/public_mvp_support_security_contact_2026-05-08.md` |
| Quality issue reporting visible to protected beta consumers | closed for protected beta | GitHub support/abuse issue template |
| Public support/abuse/privacy paths published | closed for protected beta | `.github/ISSUE_TEMPLATE/support_abuse.md`, `SECURITY.md`, `runbooks/privacy_request_workflow.md` |

Production support remains out of scope.
