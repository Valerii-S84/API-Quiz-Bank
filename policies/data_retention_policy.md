# API Quiz Bank — Data Retention Policy

**Документ:** `policies/data_retention_policy.md`  
**Статус:** governed retention baseline for repository, operations and future automation  
**Дата:** 2026-05-07  
**Власник:** project owner / privacy-compliance maintainer  
**Machine-readable companion:** `data/governance/privacy_retention_schedule.csv`

---

## 1. Purpose

This policy defines the minimum retention discipline for data families that may contain operationally sensitive, personal or organization-linked information.

The goal is to avoid both extremes:

- deleting evidence too early
- keeping sensitive data forever without justification

---

## 2. Governing Rules

1. Retention must have a documented purpose.
2. Expiry should lead to deletion, anonymization, aggregation or controlled archive according to the schedule.
3. Personal data should not be retained longer than product, security, audit or legal need justifies.
4. Import/source traceability evidence may outlive user-linked data because it is core product integrity evidence.
5. If legal windows are unresolved, unresolved status must be explicit and tracked.

---

## 3. Authority Order

Retention decisions are governed by:

1. applicable law and reviewed legal obligations
2. security/audit incident needs
3. billing/accounting obligations
4. documented product and support needs
5. this policy and its machine-readable schedule

If these conflict, higher authority wins and the conflict must be documented.

---

## 4. Retention Actions

Allowed end-of-window actions:

- delete
- anonymize
- aggregate and drop detailed identity
- archive safe evidence only
- retain under documented legal hold

---

## 5. Baseline by Data Family

The canonical retention matrix lives in `data/governance/privacy_retention_schedule.csv`.

Summary expectations:

- operational logs: short operational window
- security/audit logs: longer investigation window
- delivery logs: retained for repeat policy, analytics and support
- attempts: retained only with learning/privacy justification
- support requests: retained while support/abuse/quality context requires
- billing events/invoices: retained per accounting/legal/support needs
- backups: phase-based rolling window
- demo artifacts: keep only while review and evidence needs remain

---

## 6. Automation Intent

This repository does not yet implement runtime retention jobs, but any future automation must use the CSV schedule as source input and must preserve:

- data family identifier
- trigger date field
- retention window
- end-of-window action
- owner
- legal hold override flag if implemented

---

## 7. Review Triggers

Review this policy when:

- new personal-data fields are introduced
- analytics become more user-granular
- billing scope expands
- Telegram or school flows collect new identity data
- vendor/processor footprint changes
- legal review introduces exact mandatory windows

---

## 8. Exception Rule

Retention exceptions must be documented with:

- affected data family
- reason
- approver
- start date
- review date
- planned end state

Ad hoc “keep everything just in case” behavior is prohibited.
