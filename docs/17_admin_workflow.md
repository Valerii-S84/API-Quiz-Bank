# API Quiz Bank — Admin Workflow

**Документ:** `docs/17_admin_workflow.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** practical admin operations playbook and controlled decision workflow; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`–`16_source_onboarding_playbook.md`  
**Дата:** 2026-05-07  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized admin workflow maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/14_roadmap.md`, `docs/15_repository_governance.md`, `docs/16_source_onboarding_playbook.md`  
**Наступні документи:** `18_telegram_delivery_playbook.md`, `19_privacy_compliance.md`

---

## 0. Executive Summary

`17_admin_workflow.md` визначає керований operational/admin path для source review, dry-run review, duplicate/conflict resolution, item status changes, publication decisions, consumer controls, overrides та emergency blocking.

Головна теза документа:

```text
Admin workflow is not a hidden backdoor.
It is the controlled decision surface of the platform.
```

У цьому проєкті admin workflow повинен перетворювати sensitive write actions на repeatable, reviewable and auditable decisions:

```text
source registration
  → dry-run review
  → conflict review
  → item review
  → approve/publish/retire/block
  → consumer/rule control
  → audit review
  → rollback or emergency containment if needed
```

Неправильний path:

```text
operator sees problem or opportunity
  → edits DB or metadata directly
  → bypasses review
  → no reason code
  → no audit trail
  → production behavior changes silently
```

Final rule:

```text
Every production-relevant admin action must be authenticated,
authorized, justified, logged and reversible or explicitly bounded.
```

---

## 1. Role of This Document

### 1.1. Мета документа

`17_admin_workflow.md` відповідає на питання:

```text
Хто може виконувати admin actions?
Які дії вважаються high-risk?
Як проходять approve/publish/retire/block workflows?
Як керуються source review, duplicate/conflict review and consumer controls?
Які audit fields and evidence are mandatory?
Як працює emergency path?
Коли CLI acceptable, а коли потрібен admin UI?
```

### 1.2. Місце в документаційній ієрархії

```text
CONSTITUTION.md
  ↓
docs/02_requirements_srs.md
  ↓
docs/03_use_cases.md
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
docs/16_source_onboarding_playbook.md
  ↓
docs/17_admin_workflow.md
```

### 1.3. Що цей документ робить

Цей документ визначає:

```text
admin role model
permission boundaries
action classes
status-change rules
review workflows
consumer and entitlement controls
audit log contract
emergency admin path
MVP CLI constraints
QA and evidence expectations
```

### 1.4. Що цей документ не робить

Цей документ НЕ є:

```text
full UI wireframe spec;
database schema replacement;
security incident handbook replacement;
billing-policy replacement;
Telegram delivery runbook replacement.
```

---

## 2. Admin Workflow Thesis

### 2.1. Control-surface thesis

Admin workflow is the explicit control surface through which humans may influence production-relevant corpus, delivery and consumer state.

### 2.2. Safety thesis

The platform remains trustworthy only if admin powers are narrow, visible and policy-bound.

### 2.3. Scalability thesis

Manual review is acceptable in MVP only if it is documented, reproducible and logged. Growth in review volume requires structured UI and stronger role separation.

---

## 3. Non-Negotiable Admin Rules

1. Every admin action MUST be authenticated and authorized.
2. Every production-relevant admin write action MUST create audit evidence.
3. No admin action may silently publish draft, imported, normalized, needs_review, retired or blocked content.
4. High-risk actions MUST require explicit reason code and subject traceability.
5. Emergency admin actions MAY bypass normal sequencing only under incident policy and with post-action review.
6. CLI-based admin workflow is acceptable in MVP only if commands, inputs, outputs and operator identity are reproducible and logged.
7. Read-only review access MUST exist conceptually even if MVP uses shared operators.

---

## 4. Roles and Permission Model

### 4.1. Canonical admin roles

The architecture-level role model SHOULD use or emulate:

```text
owner
product_admin
content_admin
taxonomy_admin
billing_admin
ops_admin
security_admin
demo_admin
read_only_reviewer
```

### 4.2. Role intent

| Role | Primary responsibility |
|---|---|
| `owner` | Final authority for exceptional changes, policy overrides and launch-critical decisions |
| `product_admin` | Cross-functional operational coordination, visibility and approval routing |
| `content_admin` | Source review, import review, item review, approve/publish/retire/block |
| `taxonomy_admin` | Taxonomy policy, classification changes, controlled taxonomy corrections |
| `billing_admin` | Consumer access, quota override, entitlement override, billing-usage anomaly review |
| `ops_admin` | Operational switches, launch controls, job supervision, rollout/rollback coordination |
| `security_admin` | Security-sensitive controls, key/secret response, access review, containment support |
| `demo_admin` | Demo-safe workflows, demo consumer setup, fallback proof preparation |
| `read_only_reviewer` | Read-only access to review sources, reports, statuses and audit evidence |

### 4.3. Permission rule

One person MAY hold multiple roles in MVP, but the system and runbooks must still distinguish which role authority justified each action.

### 4.4. Separation rule

The following scopes SHOULD be separated before scale:

```text
content approval
taxonomy change
billing override
security override
production launch approval
```

---

## 5. Admin Action Classes

### 5.1. Standard action classes

Admin workflow in this project covers:

```text
source registration
source metadata correction
checksum/inventory confirmation
manifest/parser assignment
dry-run import execution or review
duplicate/conflict resolution
item review and metadata correction
approve/publish/retire/block
batch status operations where safe
consumer enable/disable/suspend/block
consumer rule configuration
manual entitlement override
quota override
taxonomy change through change control
audit review
demo-safe override handling
```

### 5.2. High-risk admin actions

The following are high-risk and MUST be treated accordingly:

```text
source blocking/unblocking
manifest changes after review
parser assignment changes affecting import outcome
import commit after dry-run
duplicate/conflict override
batch approval
quiz item publish
quiz item retire/block
consumer enable/disable for production delivery
quota override
manual entitlement override
API key creation/revocation
secret rotation coordination
manual database correction
launch approval
```

### 5.3. High-risk action rule

High-risk admin actions MUST have explicit actor identity, subject identity, reason code, timestamp and rollback/containment note where relevant.

---

## 6. Workflow Entry Points

Admin workflow may start from:

```text
new source onboarding event
dry-run completion report
duplicate/conflict detection
item validation failure
quality report or user report
coverage or taxonomy gap review
consumer access or billing event
delivery incident
security incident
demo preparation need
```

### 6.1. Entry-point rule

Entry point must not change the governance level. A demo-triggered or urgent-triggered action still follows the same admin law unless emergency policy explicitly applies.

---

## 7. Source Review and Import Review Workflow

### 7.1. Source review linkage

Source onboarding is governed by `docs/16_source_onboarding_playbook.md`. Admin workflow begins once a source requires decision, approval or exception handling.

### 7.2. Minimal source review path

```text
source registered
  → checksum and inventory confirmed
  → manifest/parser/defaults reviewed
  → dry-run import executed
  → validation/conflict report reviewed
  → decision: proceed, hold, reject, block
```

### 7.3. Dry-run review obligations

Dry-run review SHOULD expose:

```text
candidate item count
rejected row/block count
validation error categories
duplicate/conflict categories
taxonomy anomalies
missing required metadata
parser/default mismatch indicators
```

### 7.4. Source decision outputs

Possible admin decisions:

```text
accept and continue
hold for parser/taxonomy correction
re-run dry-run after fix
reject source
block source
escalate for rights/security review
```

### 7.5. Source rule

No dry-run outcome may directly produce publishable items. Import review decides only whether content may move into controlled non-production item states.

---

## 8. Duplicate and Conflict Resolution Workflow

### 8.1. Review triggers

This workflow starts when the system detects:

```text
duplicate content hash
same stem with different answer
same question with metadata divergence
same source repeated with changed checksum
merge candidate requiring manual choice
```

### 8.2. Allowed resolution outcomes

```text
skip candidate
keep both as justified variants
merge metadata under controlled rule
mark needs_review
block candidate
retire existing and replace
allow controlled override with explicit reason
```

### 8.3. Conflict rule

Conflicting correct-answer situations MUST NOT auto-publish and MUST NOT be resolved without audit evidence.

---

## 9. Item Status Workflow

### 9.1. Canonical item statuses

Admin workflow SHOULD use or emulate:

```text
draft
imported
normalized
needs_review
approved
published
monitored
retired
blocked
```

### 9.2. Core transition logic

```text
draft → imported → normalized → approved → published → monitored → retired
                       ↘ needs_review → approved
                       ↘ blocked
approved → retired
approved → blocked
published → monitored
published → retired
published → blocked
monitored → published
monitored → retired
monitored → blocked
retired → approved only by explicit owner-approved path
blocked → needs_review only by explicit owner-approved path
```

### 9.3. Approval gate

Before `approved`, the item MUST satisfy:

```text
canonical structure valid
correct answer reference valid
minimum option policy satisfied
required metadata present
recognized CEFR/theme values present
source traceability present
```

### 9.4. Publication gate

Before `published`, the item MUST satisfy:

```text
already approved
consumer-facing compatibility known
selection/delivery rules allow exposure
no active block or unresolved critical issue
release or batch context documented if relevant
```

### 9.5. Retirement and block semantics

`retired` removes the item from future normal delivery while preserving history.  
`blocked` prohibits delivery due to quality, policy, metadata, rights or security concern.

### 9.6. Status rule

Only `approved` and `published` items may be normal-delivery eligible according to consumer and environment rules. `draft`, `imported`, `normalized`, `needs_review`, `monitored`, `retired` and `blocked` are never normal-delivery eligible by default.

---

## 10. Batch Actions

### 10.1. Allowed batch operations

Batch actions MAY be used for:

```text
approval of fully validated homogeneous import set
publication of already approved release set
retirement of superseded batch
blocking of known-bad affected batch
```

### 10.2. Batch safety conditions

Batch operations require:

```text
stable selection criteria
preview of affected item count
sample or summary review
consistent reason code
auditable batch identifier
rollback/containment path
```

### 10.3. Batch rule

Batch action must never hide item-level invalidity. If eligibility is mixed or uncertain, batch processing must stop or split.

---

## 11. Consumer Controls and Access Overrides

### 11.1. Consumer admin scope

Admin workflow MUST support or emulate:

```text
consumer activation
consumer suspension
consumer blocking
consumer rule adjustment
quota override
manual entitlement grant/revoke
demo-only consumer setup
```

### 11.2. Consumer-control rule

Consumer controls MUST NOT allow bypass of status eligibility. A paid or whitelisted consumer still cannot legitimately receive blocked or non-publishable content.

### 11.3. Billing/admin override rule

Manual entitlement or quota override MUST:

```text
name the consumer
name the changed limit or entitlement
state reason code
state effective period or expiry
be audit logged
```

---

## 12. Audit Log Contract

### 12.1. Required audit fields

Critical admin actions MUST record or emulate:

```text
action_id
actor_id
actor_role
action_type
subject_type
subject_id
previous_state
new_state
reason_code
reason_note when needed
timestamp
request_id or job_id when applicable
```

### 12.2. Audit event examples

```text
source.registered
source.blocked
import.dry_run_reviewed
import.committed
item.approved
item.published
item.retired
item.blocked
consumer.blocked
consumer.rule_changed
entitlement.granted
quota.overridden
taxonomy.changed
emergency.override_applied
```

### 12.3. Audit integrity rule

Admin action without durable audit evidence is considered procedurally invalid, even if the underlying data change succeeded technically.

---

## 13. Emergency Path

### 13.1. Emergency use cases

Emergency admin path exists for:

```text
bad item already delivered
bad source imported
security exposure
billing abuse requiring containment
consumer compromise
wrong answer or policy issue requiring immediate block
```

### 13.2. Emergency minimum requirements

Even in emergency, the following still apply:

```text
immediate risk exists
owner approves or is unavailable under incident policy
action is logged
rollback or containment note exists
post-incident review is recorded
```

### 13.3. Emergency-first actions

Preferred containment order:

```text
pause delivery path if needed
block item/source/consumer
revoke or disable access path
preserve evidence
investigate cause
restore only after review
```

### 13.4. Emergency rule

Emergency path is for containment, not for silent permanent policy change.

---

## 14. Interface Mode: CLI First, UI Later

### 14.1. MVP rule

Per `SRS-ADM-010`, admin workflow MAY be CLI-based in MVP if it is documented, reproducible and logged.

### 14.2. CLI minimum contract

CLI-based admin actions SHOULD preserve:

```text
command or script identity
operator identity
input parameters
target subject identifiers
timestamped output or log artifact
result status
```

### 14.3. UI introduction trigger

Admin UI SHOULD be introduced before scaling manual review volume, especially when review requires:

```text
filtering by status/level/theme/source
validation-error browsing
conflict triage
batch decision previews
read-only reviewer access
```

---

## 15. Evidence and Review Artifacts

Each meaningful admin decision SHOULD produce or reference:

```text
source_id or item_id or consumer_id
import batch or request reference
reason code
validation/conflict report reference when relevant
before/after status
actor and time
rollback or follow-up instruction if needed
```

### 15.1. Reviewability rule

A future reviewer must be able to reconstruct why a content, consumer or billing state changed without relying on operator memory.

---

## 16. QA and Verification Hooks

### 16.1. Admin workflow test expectations

QA coverage SHOULD verify:

```text
unauthorized admin action denied
approve blocked when metadata invalid
publish blocked when item not approved
blocked item not deliverable
retired item not newly delivered
source block prevents future publishable path
manual override creates audit evidence
emergency block path works and is logged
```

### 16.2. Demo and pilot expectations

Demo and pilot proof SHOULD show at least:

```text
one approve or publish action
one negative control such as draft or blocked item denial
one audit evidence sample
one admin review artifact such as dry-run/conflict/status log
```

### 16.3. Launch-gate implication

If admin workflow cannot prove controlled approve/publish/block behavior, MVP and later launch gates are not satisfied.

---

## 17. Anti-Patterns

The following are explicitly prohibited:

```text
publishing via direct DB update with no status event
shared undocumented super-admin behavior
manual override with no expiry or reason
approving items with missing required metadata
conflict resolution with no audit trail
keeping blocked source active for convenience
using demo urgency as reason to bypass controls
granting consumer access that can expose blocked or non-publishable items
```

---

## 18. Acceptance Criteria

`17_admin_workflow.md` is acceptable when:

1. It defines canonical admin roles and permission intent.
2. It covers source review, import review, duplicate/conflict review and item status workflow.
3. It formally defines approve/publish/retire/block semantics and gates.
4. It includes consumer controls, entitlement/quota override rules and audit requirements.
5. It includes an emergency path consistent with `docs/10_operations.md`.
6. It explicitly allows MVP CLI admin workflow only under documentation and logging discipline.
7. It prohibits silent production-relevant admin changes.

---

## 19. References

Primary references:

```text
CONSTITUTION.md
docs/02_requirements_srs.md
docs/03_use_cases.md
docs/04_domain_model.md
docs/05_architecture.md
docs/08_security_threat_model.md
docs/09_quality_assurance.md
docs/10_operations.md
docs/16_source_onboarding_playbook.md
```

Key requirement anchors:

```text
SRS-ADM-001..012
SRS-STAT-001..009
SRS-ONB-001..006
UC-002
UC-003
UC-004
UC-011
UC-018
UC-023
UC-026
OPS admin emergency change rule
```

---

## 20. Final Admin Workflow Rule

```text
No human may change corpus, publication, consumer or override state in a way that
affects production behavior unless the action is policy-bound, role-bound,
traceable, auditable and operationally reviewable.
```
