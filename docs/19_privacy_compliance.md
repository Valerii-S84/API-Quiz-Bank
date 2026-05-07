# API Quiz Bank — Privacy and Compliance

**Документ:** `docs/19_privacy_compliance.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational privacy, retention and compliance baseline; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`–`18_telegram_delivery_playbook.md`  
**Дата:** 2026-05-07  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized privacy-compliance maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/02_requirements_srs.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/11_billing_model.md`, `docs/12_analytics_model.md`, `docs/13_stanford_presentation_outline.md`, `docs/14_roadmap.md`, `docs/18_telegram_delivery_playbook.md`  
**Наступні документи:** none in current foundational chain

---

## 0. Executive Summary

`19_privacy_compliance.md` визначає privacy/compliance baseline для **API Quiz Bank**: які дані можна збирати, навіщо, хто їх бачить, як довго вони зберігаються, як працюють deletion/export requests, як обмежуються logs/analytics/demo artifacts і коли privacy/legal review стає launch gate.

Головна теза документа:

```text
Collect only what the platform can justify, protect and govern.
```

У цьому проєкті privacy/compliance правильний path виглядає так:

```text
feature need identified
  → minimal data model chosen
  → role-gated access defined
  → retention window defined
  → logging/analytics exposure limited
  → deletion/export path defined
  → beta/production legal review completed when required
```

Неправильний path:

```text
collect first
  → decide later why it is needed
  → mix demo and production-like data
  → overexpose logs/analytics
  → keep forever
  → claim GDPR/compliance without review
```

Final rule:

```text
No personal or organization-linked data should enter or remain in the platform
unless its purpose, access boundary, retention logic and operational controls are explicit.
```

---

## 1. Role of This Document

### 1.1. Мета документа

`19_privacy_compliance.md` відповідає на питання:

```text
Які data families існують у платформі і які з них можуть бути personal or organization-linked?
Які privacy and minimization rules діють для attempts, deliveries, billing, logs, analytics and Telegram?
Які retention windows рекомендовані на MVP/Pilot/Beta/Production?
Як працюють export, deletion, anonymization and access-review flows?
Коли privacy/legal review є обов'язковим gate для public, school or EU deployment?
```

### 1.2. Місце в документаційній ієрархії

```text
CONSTITUTION.md
  ↓
docs/02_requirements_srs.md
  ↓
docs/04_domain_model.md
  ↓
docs/05_architecture.md
  ↓
docs/08_security_threat_model.md
  ↓
docs/09_quality_assurance.md
  ↓
docs/10_operations.md
  ↓
docs/11_billing_model.md
  ↓
docs/12_analytics_model.md
  ↓
docs/18_telegram_delivery_playbook.md
  ↓
docs/19_privacy_compliance.md
```

### 1.3. Що цей документ робить

Цей документ визначає:

```text
privacy baseline and compliance boundaries
data classification and minimization rules
authorized access model for sensitive data
retention, deletion and anonymization expectations
demo/test data handling
billing and payment-data limits
analytics/logging privacy constraints
EU/school/public deployment review gates
```

### 1.4. Що цей документ не робить

Цей документ НЕ є:

```text
formal legal advice;
substitute for jurisdiction-specific counsel;
full contract template for privacy notice, DPA or terms;
substitute for implementation-level security controls.
```

---

## 2. Privacy and Compliance Thesis

### 2.1. Product thesis

API Quiz Bank is primarily a governed quiz-content platform, not a personal-data product. Personal data must remain secondary and minimal.

### 2.2. Credibility thesis

Privacy is not a footer policy. It is a system property that depends on schema design, access control, logging discipline, analytics boundaries and retention.

### 2.3. Compliance thesis

The project MUST NOT claim formal compliance regimes that have not been reviewed. It may define a baseline that prepares for such review.

---

## 3. Non-Negotiable Privacy Rules

1. MVP MUST minimize personal data collection.
2. Logs MUST avoid secrets, raw tokens and unnecessary personal data.
3. Analytics MUST NOT expose private user or cross-consumer data without authorization.
4. Payment processing data MUST be minimized and full cardholder data MUST NOT be stored.
5. Demo/test data MUST be labeled and must not be confused with real production-like learner data.
6. Privacy/legal review appropriate to scope MUST happen before broad public, school or EU learner deployment.
7. No one may claim GDPR, PCI, SOC 2, ISO or equivalent compliance unless reviewed and evidenced.

---

## 4. Scope and Data Subjects

### 4.1. Relevant subject categories

Potentially affected people or organizations include:

```text
admins/operators
API consumer owners
teachers and schools
learners/users where attempts or accounts exist
billing customers
Telegram channel or bot owners
```

### 4.2. Relevant data families

Privacy/compliance scope in this project covers:

```text
account and admin identity data
consumer configuration and ownership data
delivery logs
attempt history
billing/customer references
support or issue reports
audit/security logs
analytics projections
Telegram identifiers
demo/test datasets and artifacts
```

### 4.3. Scope rule

Raw quiz corpus is not automatically personal data, but reports, logs, support notes, billing references and delivery context may become sensitive when combined with identity or organization fields.

---

## 5. Data Classification Baseline

### 5.1. Classification tiers

Recommended baseline:

```text
public
internal
sensitive operational
personal or organization-linked
restricted secret
```

### 5.2. Example classification map

| Data family | Baseline classification | Notes |
|---|---|---|
| Public product docs/OpenAPI | public | Safe for external sharing if intentionally published |
| Corpus inventory and import reports | internal/sensitive operational | May reveal source paths, review notes or restricted corpus details |
| Delivery logs | sensitive operational / organization-linked | Can identify consumer/channel history |
| Attempt records | personal or organization-linked | Especially if tied to user, class or Telegram identity |
| Billing events/customer references | personal or organization-linked | Support/accounting/legal relevance |
| Audit logs | sensitive operational | Actor identity and security events |
| API credentials and webhook secrets | restricted secret | Never expose in logs/repo/demo |
| Demo artifacts | internal | Must be labeled as demo/sanitized/simulated |

### 5.3. Classification rule

When in doubt, classify higher until explicit review proves lower sensitivity is safe.

---

## 6. Data Minimization Rules

### 6.1. General minimization baseline

Collect only the smallest set of data required for:

```text
feature delivery
access control
quota/billing support
security/audit
repeat policy
operational troubleshooting
authorized analytics
```

### 6.2. Specific minimization rules

The platform SHOULD:

```text
use user/account IDs instead of extra personal profile fields where possible
store API credential hashes, not raw API keys
store provider references, not full payment method details
store IP addresses only if needed and with retention/redaction policy
avoid storing learner email unless truly required
avoid storing unnecessary Telegram user metadata
avoid storing free-text fields that invite sensitive data unless necessary
```

### 6.3. Attempt-data rule

Attempt records SHOULD capture learning and integrity signals, not rich personal dossiers. If user identity is unnecessary, prefer pseudonymous or scoped identifiers.

### 6.4. Billing-data rule

Payment provider IDs may be stored for mapping and support, but full card numbers, CVV/CVC, raw payment tokens and bank credentials must never be stored internally.

---

## 7. Purpose Limitation and Use Boundaries

### 7.1. Allowed purpose categories

Collected data SHOULD map to one or more explicit purposes:

```text
content delivery
selection and anti-repeat
attempt recording and learning flow
consumer access control
billing and dispute support
security/audit
operations and incident response
authorized aggregate analytics
```

### 7.2. Purpose-boundary rule

Data collected for one purpose must not silently become a broader marketing, profiling or unrelated export dataset without explicit product/legal review.

### 7.3. Overcollection rule

If a feature cannot justify why a field is needed, that field should not exist in the canonical model.

---

## 8. Access Control and Authorized Visibility

### 8.1. Access baseline

Sensitive and organization-linked data MUST be role-gated and scope-gated.

### 8.2. Visibility rules

Default expectations:

```text
admins see only what their role requires
teachers/schools see only their own class/group context
API consumers see only their own usage and authorized projections
demo viewers see only safe demo/sanitized outputs
analytics consumers see aggregate defaults before detailed personal views
```

### 8.3. Audit rule

Admin access to sensitive records MUST be auditable.

### 8.4. Cross-consumer rule

Queries, reports and analytics MUST NOT leak unrelated consumer, school or channel data across authorization boundaries.

---

## 9. Logging and Audit Privacy

### 9.1. Log privacy rules

Structured logs are required, but they MUST avoid:

```text
raw tokens
secrets
full payment details
unnecessary learner personal data
hidden correct-answer data outside allowed context
unnecessary raw payloads from third parties
```

### 9.2. Correlation rule

Prefer correlation IDs, request IDs and stable internal identifiers over repeated personal fields.

### 9.3. Audit-log rule

Audit logs may retain actor identity and action context, but must not become a dumping ground for entire sensitive payloads when summarized evidence is sufficient.

---

## 10. Analytics Privacy and Reporting Limits

### 10.1. Analytics baseline

Analytics must reveal enough for product and operations decisions without violating authorization or privacy.

### 10.2. Default analytics restrictions

Analytics outputs SHOULD NOT expose by default:

```text
email addresses unless explicitly authorized
raw billing profile data
payment identifiers beyond need
raw source file system paths
internal review notes
full admin audit payloads
cross-consumer personal history
```

### 10.3. Aggregate-first rule

Teachers, schools, pilots and demos SHOULD receive aggregate or scoped analytics by default. Detailed learner analytics requires explicit privacy/legal posture and role authorization.

### 10.4. Demo analytics rule

Demo analytics SHOULD prefer aggregate, synthetic-safe or sanitized subsets when detailed personal data is unnecessary.

---

## 11. Delivery, Attempt and Telegram Privacy

### 11.1. Delivery history rule

Delivery logs may be retained for repeat policy, analytics and dispute support, but should use scoped internal IDs rather than expanded personal context when possible.

### 11.2. Attempt privacy rule

Attempts MUST NOT expose another consumer's user or class data. Attempt analytics must remain consumer/user authorized.

### 11.3. Telegram privacy rule

Telegram user/channel identifiers are potentially sensitive. Collect only what is needed for governed delivery, scheduling, support and anti-repeat. Do not enrich Telegram records with unnecessary profile data.

### 11.4. Public-response rule

Learner-facing or public-safe APIs and adapters MUST NOT expose hidden correct answers, secret metadata or unrelated operational identifiers.

---

## 12. Billing and Payment Privacy

### 12.1. Payment-data minimization

Preferred posture:

```text
hosted checkout or provider-managed payment collection
provider customer/subscription/invoice references stored internally
no full card number
no CVV/CVC
no raw payment token secrets
```

### 12.2. Billing-visibility rule

Billing data is not general analytics data. Access should be limited to billing/admin/support scopes with clear reason and authorization.

### 12.3. Legal/tax boundary

Public paid launch requires legal/tax/privacy review appropriate to jurisdiction, customer geography and product model. This document defines readiness expectations, not tax advice.

---

## 13. Demo, Test and Training Data

### 13.1. Demo-data rule

Demo data MUST be clearly labeled as:

```text
demo
test
sanitized
simulated
aggregate-only
```

### 13.2. Mixing rule

Do not mix demo/test artifacts with production-like learner/customer records without clear labeling and access boundaries.

### 13.3. Presentation rule

Slides, screenshots, logs and demo analytics must not expose secrets, unauthorized consumer data or private learner details.

---

## 14. Retention Baseline

### 14.1. Retention principle

Retain data long enough for product function, support, audit, security and legal obligations, but not indefinitely by habit.

### 14.2. Baseline retention matrix

| Data family | Suggested baseline |
|---|---|
| Operational app logs | 14–30 days in MVP/Pilot; 30–90 days target in production |
| Security/audit logs | 90 days in MVP/Pilot; 180–365 days target in production depending on legal/privacy posture |
| Demo logs/artifacts | Keep until demo review completes; archive only safe evidence |
| Import reports/source history | Retain indefinitely or tied to source history because traceability is core product evidence |
| Delivery logs | Retain as needed for repeat policy, analytics, support and dispute analysis; exact production window must be policy-defined |
| Attempt records | Retain per learning value and privacy justification; shorter windows or anonymization should be preferred when granular learner identity is unnecessary |
| Support/issue reports | Retain only as long as support, abuse review or quality history requires |
| Billing events/invoices | Retain according to support/accounting/legal obligations; exact jurisdictional policy to be confirmed |
| Backups | MVP/demo keep latest known-good; closed pilot 7–14 daily; public beta 14–30 days; production 30+ days or policy-defined |

### 14.3. Retention rule

If exact legal windows are not yet finalized, the system must still avoid “forever by default” behavior and must document unresolved policy decisions.

---

## 15. Deletion, Anonymization and Export

### 15.1. Capability baseline

Before public/school production, the platform SHOULD define or implement:

```text
user or customer data export path
deletion request handling
anonymization or pseudonymization where deletion would break required history
support workflow for verified requests
retention-expiry cleanup logic
```

### 15.2. Deletion rule

Deletion of personal data does not mean erasing product integrity evidence blindly. Where full deletion would break lawful audit/history obligations, the system should minimize, detach or anonymize identity while preserving required operational records.

### 15.3. Export rule

Exports must be scope-limited, authorized and reviewed to avoid cross-consumer or cross-user leakage.

### 15.4. Request-handling rule

Privacy-related requests SHOULD be ticketed, verified, time-tracked and resolved through documented workflow, not ad hoc operator memory.

---

## 16. Processors, Vendors and Cross-Border Concerns

### 16.1. Vendor baseline

Third-party systems that may process protected data include:

```text
hosting/cloud provider
observability/logging provider
backup storage provider
payment provider
Telegram platform
email/support tooling if introduced
```

### 16.2. Vendor rule

Before relying on a vendor for public or school deployment, the project should understand:

```text
what data is sent
why it is sent
how long it is retained
who can access it
whether cross-border transfer concerns apply
```

### 16.3. EU/school gate

Deployment involving EU learners, schools or broader public educational use SHOULD complete privacy/legal review appropriate to that context before production launch.

---

## 17. Incident and Breach Coordination

### 17.1. Privacy incident examples

```text
cross-consumer analytics exposure
logs reveal token or private user data
Telegram identifiers exposed in public artifacts
billing/customer data exported to wrong party
demo screenshot leaks restricted details
backup or report shared without proper access controls
```

### 17.2. Response minimums

Privacy/security incident handling SHOULD preserve:

```text
incident identifier
scope of affected data
containment action
timeline
review of root cause
remediation and future guardrails
```

### 17.3. Incident rule

Privacy incidents must be treated as operational defects with evidence and follow-up, not as documentation-only concerns.

---

## 18. Evidence and Review Cadence

### 18.1. Required evidence examples

Privacy/compliance baseline should eventually be backed by:

```text
data classification note
retention matrix
authorized analytics examples
log/redaction inspection evidence
demo-data labeling evidence
billing/payment minimization evidence
privacy/legal review record for beta/public/school scope
```

### 18.2. Repository-controlled artifacts

The following artifacts now form the minimum repository baseline for privacy/compliance execution:

```text
policies/privacy_notice_baseline.md
policies/data_retention_policy.md
runbooks/privacy_request_workflow.md
data/governance/privacy_retention_schedule.csv
data/governance/vendor_register.csv
reports/compliance/legal_review_record.md
reports/compliance/privacy_request_register.csv
reports/compliance/deletion_action_register.csv
```

### 18.3. Review triggers

Privacy review SHOULD be revisited when:

```text
new learner/account fields are added
analytics scope expands
Telegram/user identifiers gain new usage
paid public launch is prepared
school deployment is prepared
EU-facing scope increases
new vendor/processor is introduced
```

---

## 19. Anti-Patterns

The following are explicitly prohibited:

```text
claiming GDPR/PCI/SOC2/ISO compliance without review
collecting learner data “just in case”
logging raw tokens or payment secrets
indefinite retention with no policy
demo screenshots containing real private data
cross-consumer analytics exports
billing data appearing in normal product analytics without justification
Telegram delivery requiring unnecessary user profiling
using support notes as unstructured sensitive-data dump
```

---

## 20. Acceptance Criteria

`19_privacy_compliance.md` is acceptable when:

1. It defines privacy/compliance baseline without pretending to be jurisdiction-specific legal advice.
2. It covers data classification, minimization, access control, analytics/logging limits and billing-data boundaries.
3. It includes retention, deletion, anonymization and export expectations.
4. It addresses demo/test data, Telegram identifiers and cross-consumer exposure risks.
5. It defines review gates for public, school and EU-facing deployment.
6. It explicitly forbids unreviewed compliance claims and indefinite uncontrolled retention.
7. It aligns with security, operations, billing and analytics documents already in the repo.

---

## 21. References

Primary references:

```text
CONSTITUTION.md
docs/02_requirements_srs.md
docs/04_domain_model.md
docs/05_architecture.md
docs/08_security_threat_model.md
docs/09_quality_assurance.md
docs/10_operations.md
docs/11_billing_model.md
docs/12_analytics_model.md
docs/13_stanford_presentation_outline.md
docs/18_telegram_delivery_playbook.md
policies/privacy_notice_baseline.md
policies/data_retention_policy.md
runbooks/privacy_request_workflow.md
data/governance/privacy_retention_schedule.csv
data/governance/vendor_register.csv
reports/compliance/legal_review_record.md
reports/compliance/privacy_request_register.csv
reports/compliance/deletion_action_register.csv
```

Key requirement anchors:

```text
NFR-SEC-008
NFR-SEC-011
NFR-SEC-012
SRS-AN-010
AC-PROD-012
SEC-REQ-PRIV-001..006
AC-PRIV-SEC-001..004
QA-BETA-006
OPS-BETA-008
```

---

## 22. Final Privacy Rule

```text
API Quiz Bank may govern content at scale only if every personal or
organization-linked datum is treated as an explicit liability: minimized,
authorized, retained with purpose, and removed or anonymized when that purpose ends.
```
