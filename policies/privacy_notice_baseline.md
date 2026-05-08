# API Quiz Bank — Privacy Notice Baseline

**Документ:** `policies/privacy_notice_baseline.md`  
**Статус:** operational baseline and draft-ready source for future public privacy notice; not legal advice  
**Дата:** 2026-05-07  
**Власник:** project owner / privacy-compliance maintainer  
**Пов'язані документи:** `docs/19_privacy_compliance.md`, `docs/11_billing_model.md`, `docs/12_analytics_model.md`, `docs/18_telegram_delivery_playbook.md`

---

## 1. Purpose

This file is the repository-controlled baseline for a future public-facing privacy notice. It states what API Quiz Bank currently expects to collect, why, and under which access and retention boundaries.

It is not final legal text and must be reviewed before public/school/EU production use.

---

## 2. What API Quiz Bank Is

API Quiz Bank is a governed quiz-content platform. It may deliver quiz items through API and controlled consumers such as Telegram. It may also record delivery, attempts, access-control events, billing references and operational evidence.

---

## 3. Data Categories

The platform may process:

- account and admin identity data
- consumer ownership and configuration data
- delivery history
- attempt history where feature scope requires it
- billing/customer reference data
- support or issue-report data
- audit and security logs
- analytics derived from governed system records
- Telegram channel/bot identifiers where Telegram delivery is enabled

The platform should avoid collecting unnecessary learner personal data.

---

## 4. Why Data Is Used

Data is used only for justified platform purposes such as:

- content delivery
- access control, entitlements and quota enforcement
- repeat-policy enforcement
- attempt recording and learning flow where applicable
- billing and dispute support
- security, audit and incident response
- authorized aggregate analytics

Data must not silently expand into unrelated profiling or unrestricted marketing datasets without explicit review.

---

## 5. Minimization Commitments

The platform baseline is:

- use internal IDs where possible instead of excessive profile fields
- store API key hashes, not raw API keys
- store billing provider references, not full cardholder data
- store Telegram identifiers only when needed for governed delivery/support
- avoid unnecessary raw payload retention in logs
- prefer aggregate analytics over detailed learner exposure by default

---

## 6. Access Boundaries

Default access posture:

- admins see only data required by their role
- teachers/schools see only their own scoped data
- API consumers see only their own usage and authorized projections
- demo viewers see only safe demo or sanitized artifacts
- billing/admin scopes are separated from general product analytics

Cross-consumer exposure is prohibited.

---

## 7. Retention Baseline

Retention follows `policies/data_retention_policy.md` and `data/governance/privacy_retention_schedule.csv`.

Key baseline:

- operational logs: short-lived
- audit/security logs: longer-lived for investigation
- delivery logs: retained for repeat policy, analytics and support
- attempts: retained only with learning/privacy justification
- billing/invoice references: retained according to support/accounting/legal needs
- demo artifacts: pruned or archived as safe evidence only

---

## 8. Deletion, Export and Correction

Before public/school production, the platform should support documented workflows for:

- verified data export requests
- verified deletion or anonymization requests
- correction of inaccurate account/customer data
- retention-expiry cleanup

These workflows are governed by `runbooks/privacy_request_workflow.md`.

---

## 9. Sensitive Data Boundaries

The platform must not:

- store full card numbers or CVV/CVC
- expose raw secrets or tokens in logs, demos or repository files
- expose hidden correct-answer metadata outside authorized system paths
- claim formal GDPR/PCI/SOC2/ISO compliance without completed review

---

## 10. Review Gate

This baseline must be reviewed and upgraded before:

- broad public launch
- school deployment
- EU learner-facing production use
- paid public launch with real customer billing

## 10.1 Public MVP / Protected Beta Scope

The Public MVP / Protected Beta scope approved on 2026-05-08 is limited to:

- protected public access behind API-key controls;
- owner-operated runtime and manual support/privacy/security handling;
- approved or published quiz item delivery only;
- delivery, entitlement, quota, audit and backup records needed to operate the
  protected beta;
- Telegram target references only for explicitly approved Telegram delivery;
- no paid launch, school deployment, unauthenticated access or production
  readiness claim.

Sensitive support, security and privacy reports must use the private owner
channel recorded outside the public repository. Public GitHub issues are only
for non-sensitive reports.

---

## 11. Change Rule

Any material change to collected data categories, access scopes, vendor flows or retention posture must update this file together with `docs/19_privacy_compliance.md` and the retention/vendor artifacts.
