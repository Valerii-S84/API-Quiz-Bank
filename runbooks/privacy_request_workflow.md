# API Quiz Bank — Privacy Request Workflow

**Документ:** `runbooks/privacy_request_workflow.md`  
**Статус:** operational workflow baseline for export, deletion, correction and privacy-related requests  
**Дата:** 2026-05-07  
**Власник:** project owner / privacy-compliance maintainer  
**Пов'язані артефакти:** `policies/privacy_notice_baseline.md`, `policies/data_retention_policy.md`, `reports/compliance/legal_review_record.md`

---

## 1. Purpose

This runbook defines how privacy-related requests should be handled before production-scale automation exists.

Covered request classes:

- data export request
- deletion request
- anonymization request
- correction request
- access-scope complaint
- retention/overexposure incident follow-up

---

## 2. Workflow Principles

1. No privacy request is handled only from memory or informal chat.
2. Identity and authority of the requester must be verified before disclosure or destructive action.
3. Scope must be identified precisely: which subject, which consumer, which records, which period.
4. Requests must consider audit, billing, security and legal obligations before deletion.
5. Outcome must be logged in a durable ticket or equivalent record.

---

## 3. Minimum Request Record

Each request should record:

- request ID
- received date/time
- requester identity
- requester authority basis
- request type
- affected scopes and identifiers
- requested deadline if any
- owner handling the request
- decision
- completion date
- notes on retained/legal-hold data if applicable

Repository baseline register:

- `reports/compliance/privacy_request_register.csv`

---

## 4. Intake Flow

```text
request received
  → request logged
  → requester identity verified
  → scope clarified
  → affected systems/data families listed
  → legal/operational constraints checked
  → action plan approved
  → result executed/documented
  → requester receives controlled response
```

---

## 5. Export Request Path

For export requests:

1. Verify requester identity and scope entitlement.
2. Determine which data families are in scope.
3. Exclude unrelated consumer/school/user data.
4. Prepare authorized export only.
5. Review for secrets, cross-consumer leakage and internal-only notes.
6. Record what was exported and when.

Export must be scope-limited and reviewed before release.

---

## 6. Deletion or Anonymization Path

For deletion-related requests:

1. Verify requester identity and scope.
2. Determine whether full deletion is possible.
3. Check whether data is still needed for:
   - audit/security
   - billing/accounting
   - dispute support
   - required operational integrity
4. If full deletion is not appropriate, prefer minimization/anonymization.
5. Record exactly what was deleted, detached, anonymized or retained.

Deletion must not destroy required product integrity evidence blindly.

Repository baseline register:

- `reports/compliance/deletion_action_register.csv`

---

## 7. Correction Path

For correction requests:

1. Verify requester identity.
2. Confirm the data element is inaccurate.
3. Correct only the authorized record.
4. Preserve auditability of the correction.
5. Avoid rewriting historical delivery or billing evidence beyond what policy allows.

---

## 8. Access Complaint Path

If a requester claims overexposure or cross-consumer leakage:

1. Open incident or issue record immediately.
2. Preserve evidence.
3. Contain access if needed.
4. Review logs, analytics/report scope and authorization path.
5. Document root cause and remediation.

This path should coordinate with security/operations incident handling when risk is active.

---

## 9. Manual-Phase Rule

Until automation exists, the workflow may be manual, but it must still be:

- documented
- reproducible
- scope-reviewed
- access-controlled
- auditable

---

## 10. Exit Criteria

A privacy request is not done until:

- action taken is documented
- retained data has a stated reason if applicable
- requester-facing response is prepared or sent
- follow-up fixes are tracked if a defect was found

---

## 11. Future Automation Hooks

Future implementation should support:

- request ticket IDs
- export job IDs
- deletion/anonymization job IDs
- per-data-family completion evidence
- legal-hold override state
- retention-expiry execution logs
