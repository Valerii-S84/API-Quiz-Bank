# API Quiz Bank — Legal / Privacy Review Record

**Документ:** `reports/compliance/legal_review_record.md`  
**Статус:** living review record and launch-gate evidence placeholder  
**Дата створення:** 2026-05-07  
**Власник:** project owner / privacy-compliance maintainer

---

## 1. Purpose

This file records whether privacy/legal/compliance review required for a given scope has happened, what remains unresolved, and which launch claims are blocked.

It is not a legal opinion. It is the project record of review status.

---

## 2. Current Snapshot

| Review area | Status | Blocking for launch? | Notes |
|---|---|---|---|
| MVP internal/documentation baseline | documented | no | Privacy baseline exists in repo |
| Stanford/demo presentation safety | partially documented | no, if demo remains controlled | Demo data must remain labeled/safe |
| Closed pilot with limited real consumers | pending | yes for personal-data-heavy pilot | Scope-specific review still needed |
| Public beta privacy posture | pending | yes | Required before broad external access |
| School deployment review | pending | yes | Required before school/teacher learner data scale |
| EU learner-facing production review | pending | yes | Required before EU public learner production |
| Paid public billing/privacy/tax review | pending | yes | Required before public paid launch |
| Provider-specific PCI/privacy review | pending | yes if payment launch proceeds | Billing model forbids premature claim |

---

## 3. Open Review Questions

Current unresolved questions:

1. Which exact legal entity and jurisdiction govern public customer relationships?
2. What exact retention windows apply to attempts, delivery logs and billing records?
3. What deletion/export rights workflow is required for first real users?
4. Which vendors/processors and data regions will be used in real deployment?
5. What EU/school-specific privacy notice and contractual documents are required?

---

## 4. Evidence References

Current repo evidence:

- `docs/19_privacy_compliance.md`
- `policies/privacy_notice_baseline.md`
- `policies/data_retention_policy.md`
- `data/governance/privacy_retention_schedule.csv`
- `data/governance/vendor_register.csv`
- `runbooks/privacy_request_workflow.md`
- `reports/beta/local_beta_security_smoke_2026-05-08.md`
- `reports/publication/beta_launch_subset_2026-05-08.md`
- `reports/observability/beta_alert_review_2026-05-08.md`

## 4.1 Beta Scope Review Snapshot

Current status: pending external approval.

Local beta package now documents consumer-bound API credential behavior,
approved/published-only delivery, local alert-review signals and support/privacy
runbooks. It does not close public beta privacy/legal review because no legal
entity, public support surface, real data processor list or launch owner
approval has been recorded.

---

## 5. Update Rule

This file must be updated when:

- privacy/legal review is completed for a new launch scope
- a vendor/processor is selected
- exact retention windows become legally confirmed
- public beta, school or paid launch planning begins
