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
| Public MVP / Protected Beta privacy posture | approved for protected beta only | no for protected beta; yes for production | Scope-specific owner approval recorded in section 4.2 |
| Owner-operated protected production API runtime | approved for protected API runtime only | no for protected API runtime; yes for broader launch scopes | Scope-specific owner-operated runtime approval recorded in section 4.3 |
| Broad public beta privacy posture | pending | yes | Required before unauthenticated, broad or paid external access |
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
- `reports/compliance/public_mvp_support_security_contact_2026-05-08.md`
- `reports/observability/public_mvp_monitoring_review_2026-05-08.md`
- `reports/restore/public_mvp_backup_restore_2026-05-08.md`
- `reports/rollback/public_mvp_runtime_rollback_drill_2026-05-08.md`
- `reports/roadmap/production_postgresql_runtime_closure_2026-05-10.md`

## 4.1 Beta Scope Review Snapshot

Current status: protected beta privacy/legal gate approved; broad public beta
and production remain pending.

Local beta package now documents consumer-bound API credential behavior,
approved/published-only delivery, local alert-review signals and support/privacy
runbooks. The protected beta gate is limited to the owner-operated runtime and
does not approve paid launch, school deployment, unauthenticated access or
production use.

## 4.2 Public MVP / Protected Beta Approval

Decision:

```text
GO for Public MVP / Protected Beta privacy/legal gate
NO-GO for production, paid public launch, school deployment or broad public beta
```

Scope approved:

- protected public access behind `X-API-Key`;
- owner-operated VPS runtime;
- approved/published controlled quiz items only;
- Telegram delivery only after explicit controlled-send approval;
- manual support/privacy/security intake through documented public and private
  paths;
- no paid launch, no production claim and no school deployment claim.

Data categories in scope:

- consumer id and consumer configuration;
- API credential hash and prefix, not raw API key;
- entitlement/quota records;
- delivery id, quiz item id, delivery status and runtime audit records;
- Telegram target references only when Telegram delivery is explicitly enabled;
- support/privacy/security issue metadata supplied by the reporter.

Access and retention:

- access is limited to project owner / authorized operator for the protected
  beta runtime;
- retention follows `policies/data_retention_policy.md` and
  `data/governance/privacy_retention_schedule.csv`;
- backups are retained under the controlled VPS path documented in
  `reports/restore/public_mvp_backup_restore_2026-05-08.md`;
- deletion/export/correction requests follow
  `runbooks/privacy_request_workflow.md`.

Owner approval:

```text
Approved by project owner for Public MVP / Protected Beta scope on 2026-05-08.
```

This is a project launch-gate record, not external legal advice.

---

## 4.3 Owner-Operated Protected Production API Runtime Approval

Decision:

```text
GO for owner-operated protected production API runtime
NO-GO for unauthenticated broad public launch, school deployment, paid launch
or external legal-advice claims
```

Scope approved:

- protected API access at `api.valerchik.de` behind the edge `X-API-Key`;
- owner-operated VPS runtime at `/opt/api-quiz-bank`;
- PostgreSQL persistent runtime database for controlled quiz delivery;
- consumer-bound application API credentials;
- approved/published controlled quiz items only;
- delivery and selection decision logging;
- production backup/restore, monitoring snapshot and rollback evidence recorded
  in `reports/roadmap/production_postgresql_runtime_closure_2026-05-10.md`.

Data categories in scope:

- consumer id and consumer configuration;
- API credential hash and prefix, not raw API key;
- entitlement/quota records;
- delivery id, quiz item id, delivery status and selection decision metadata;
- operational monitoring snapshots without secrets.

Owner approval:

```text
Approved by project owner for the owner-operated protected production API
runtime scope on 2026-05-10.
```

This is a project launch-gate record, not external legal advice. Any expansion
to unauthenticated public access, school/teacher learner data scale, public paid
billing or broader EU learner-facing production still requires a separate
scope-specific privacy/legal approval.

---

## 5. Update Rule

This file must be updated when:

- privacy/legal review is completed for a new launch scope
- a vendor/processor is selected
- exact retention windows become legally confirmed
- public beta, school or paid launch planning begins
