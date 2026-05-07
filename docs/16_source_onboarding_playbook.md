# API Quiz Bank — Source Onboarding Playbook

**Документ:** `docs/16_source_onboarding_playbook.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** practical source onboarding playbook and operational workflow; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`–`15_repository_governance.md`  
**Дата:** 2026-05-07  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized source-onboarding maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/06_data_standard.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/14_roadmap.md`, `docs/15_repository_governance.md`  
**Наступні документи:** `17_admin_workflow.md`, `18_telegram_delivery_playbook.md`, `19_privacy_compliance.md`

---

## 0. Executive Summary

`16_source_onboarding_playbook.md` визначає практичний workflow, за яким нові quiz source files додаються в **API Quiz Bank** без хаосу, без direct production drop і без втрати traceability.

Головна теза документа:

```text
New quiz files are onboarded, not dropped.
```

Source onboarding у цьому проєкті означає:

```text
intake
  → source_id
  → checksum
  → inventory record
  → import manifest entry
  → parser assignment
  → dry-run import
  → validation
  → duplicate/conflict classification
  → onboarding report
  → controlled import/status workflow
```

Неправильний path:

```text
new file appears in repo
  → someone points bot/site/API at it
  → production behavior changes
  → no traceability
```

Final rule:

```text
No future source may influence production delivery unless onboarding artifacts,
validation, review decisions and status rules are explicit.
```

---

## 1. Role of This Document

### 1.1. Мета документа

`16_source_onboarding_playbook.md` відповідає на питання:

```text
Як practically onboard-ити новий source file?
Які prechecks обов'язкові до dry-run?
Які source states існують?
Що робити при parser_pending, duplicate checksum, validation failure or rights issue?
Які artifacts мають бути створені?
Що вважається done для onboarding run?
```

### 1.2. Місце в документаційній ієрархії

```text
CONSTITUTION.md
  ↓
docs/01_product_charter.md
  ↓
docs/02_requirements_srs.md
  ↓
docs/03_use_cases.md
  ↓
docs/04_domain_model.md
  ↓
docs/05_architecture.md
  ↓
docs/06_data_standard.md
  ↓
docs/08_security_threat_model.md
  ↓
docs/09_quality_assurance.md
  ↓
docs/10_operations.md
  ↓
docs/14_roadmap.md
  ↓
docs/15_repository_governance.md
  ↓
docs/16_source_onboarding_playbook.md
```

### 1.3. Що цей документ робить

Цей документ визначає:

```text
roles and responsibilities
source states
intake checklist
step-by-step onboarding workflow
decision points
failure and reject/block paths
evidence package
demo and QA hooks
completion criteria
```

### 1.4. Що цей документ не робить

Цей документ НЕ є:

```text
parser implementation guide;
data-standard replacement;
admin UI spec;
production import migration guide for every stack;
legal rights opinion.
```

---

## 2. Core Playbook Thesis

### 2.1. Operational thesis

Adding a new source file is an operational event, not an informal content drop.

### 2.2. Trust thesis

The platform can scale only if each new source repeats the same governed path:

```text
register
verify
configure
dry-run
validate
review
report
promote through status workflow
```

### 2.3. Anti-chaos thesis

Filename, location or urgency must never be used as reasons to bypass source onboarding.

---

## 3. Non-Negotiable Onboarding Rules

1. Every importable source MUST receive stable `source_id` before dry-run import.
2. Every importable source MUST receive checksum before parser assignment.
3. No active source may enter production workflow without manifest entry.
4. Dry-run import MUST happen before any production-relevant import or publication path.
5. Duplicate checksum or conflict signals MUST be reviewed, not ignored.
6. New source items MUST remain non-production until item-level status workflow allows delivery.
7. Generated onboarding/import reports MUST be preserved as evidence.

---

## 4. Roles and Responsibilities

| Role | Responsibility |
|---|---|
| Source Onboarding Admin | Registers source, assigns metadata, coordinates dry-run |
| Data/Content Lead | Reviews parser/defaults/taxonomy correctness |
| Engineering Maintainer | Ensures tooling, parser behavior, import safety |
| Security/Operations Owner | Intervenes for rights issues, blocked source path or sensitive exceptions |
| Demo Owner | Uses same onboarding path or artifact-backed equivalent for demo proof |

### 4.1. Responsibility rule

One person may play multiple roles in MVP, but role responsibilities must still remain explicit.

---

## 5. Source States

The onboarding workflow SHOULD use or emulate these states:

```text
candidate
registered
parser_pending
parser_assigned
dry_run_failed
dry_run_passed
imported
active
archived
rejected
blocked
```

### 5.1. State semantics

| State | Meaning |
|---|---|
| `candidate` | Proposed file exists but not yet registered |
| `registered` | Source has source_id, checksum and inventory record |
| `parser_pending` | Parser profile not yet assigned or ready |
| `parser_assigned` | Manifest/parser/defaults configured |
| `dry_run_failed` | Dry-run blocked or failed |
| `dry_run_passed` | Dry-run completed with acceptable outcome |
| `imported` | Candidates imported into controlled storage, not automatically publishable |
| `active` | Source is accepted as active source asset |
| `archived` | Historical source retained but inactive |
| `rejected` | Source not accepted for onboarding |
| `blocked` | Source explicitly prohibited pending issue resolution |

### 5.2. State rule

`active` source does not mean deliverable items. Item-level publication still depends on item statuses.

---

## 6. Trigger Conditions

This playbook starts when any of the following happens:

```text
new quiz file is proposed
existing source materially changes checksum
source file is split/merged/replaced
demo requires sample future source onboarding proof
source needs re-onboarding due to parser/defaults change
```

### 6.1. Re-onboarding rule

Checksum change MUST trigger import impact review, not silent overwrite.

---

## 7. Preconditions

Before onboarding begins, confirm:

```text
authorized operator exists
source file is available in controlled workspace
intended source type/format is understood enough for intake
inventory and manifest locations are known
target parser profile exists or parser_pending path is acceptable
```

### 7.1. Stop conditions before start

Stop and escalate if:

```text
file origin/rights are unclear
source appears to contain secrets or unrelated sensitive data
duplicate source_id is proposed
required inventory/manifest discipline cannot be applied
```

---

## 8. Required Inputs

Each onboarding run SHOULD capture:

```text
proposed filename
original path/location
format
encoding when known
uploader/source owner if relevant
expected content type
rights/usage note if needed
```

### 8.1. Recommended metadata

Also capture where feasible:

```text
approximate row count
language mode
expected levels/themes
parser expectation
notes about anomalies
```

---

## 9. Intake Checklist

Before registry/manifest work, verify:

1. File is not a template mistakenly presented as source.
2. File is not already represented by active source_id.
3. File is not obviously malformed, empty or unrelated.
4. Usage/ownership concerns are not already disqualifying.
5. File location is recorded for traceability.

### 9.1. Intake anti-pattern

Copying a file into the repo first and documenting it later is forbidden.

---

## 10. Step 1 — Create Source Intake Record

### 10.1. Action

Create source intake record or equivalent operational note.

### 10.2. Minimum fields

```text
intake timestamp
actor
proposed filename
original path
format
notes
initial state = candidate
```

### 10.3. Evidence

Evidence should preserve that the source entered the system through governed intake, not by silent drop.

---

## 11. Step 2 — Assign Stable `source_id`

### 11.1. Action

Assign stable unique `source_id`, for example:

```text
src_0001
src_0002
src_0003
```

### 11.2. Rules

1. `source_id` MUST be globally unique.
2. `source_id` MUST NOT change because file is moved or renamed.
3. `source_id` MUST NOT be reused for a different source.

### 11.3. Reject condition

If duplicate active `source_id` is detected, onboarding stops until resolved.

---

## 12. Step 3 — Compute and Record Checksum

### 12.1. Action

Compute `checksum_sha256` and record it in source registry/inventory context.

### 12.2. Rules

1. Checksum MUST be recorded before parser assignment.
2. Checksum change later MUST trigger import impact review.
3. Duplicate checksum across active sources SHOULD be flagged for review.

### 12.3. Duplicate-checksum handling

Possible outcomes:

```text
allowed duplicate with explicit reason
rejected duplicate source
needs review before continuation
```

---

## 13. Step 4 — Add Inventory Record

### 13.1. Action

Add or regenerate inventory entry including:

```text
source_id
filename
path
format
encoding when known
checksum_sha256
status/state
row_count_detected when available
notes
```

### 13.2. Rule

Inventory must reflect the new source before dry-run import proceeds.

---

## 14. Step 5 — Classify Source Format and Status

### 14.1. Action

Classify:

```text
format
encoding
template vs importable source
initial source state
expected parser family
```

### 14.2. Examples

| Situation | Expected outcome |
|---|---|
| Valid CSV candidate | `registered` |
| Unknown format | `parser_pending` |
| Template sheet | `template` or equivalent non-importable state in inventory |
| Rights issue | `blocked` or `rejected` |

---

## 15. Step 6 — Create Manifest Entry

### 15.1. Action

Add source to `import_manifest.yml` or equivalent structured manifest.

### 15.2. Required manifest discipline

Manifest MUST reference source by:

```text
source_id
```

not by filename only.

### 15.3. Minimum manifest content

Manifest entry SHOULD define:

```text
source_id
parser_profile_id or parser marker
source state
defaults if needed
flags/rules
```

### 15.4. Block condition

New source cannot dry-run without manifest entry.

---

## 16. Step 7 — Assign Parser Profile or `parser_pending`

### 16.1. Action

Choose one:

```text
assign existing parser profile
create/approve new parser profile through governed change path
mark source as parser_pending
```

### 16.2. Rules

1. Parser assignment should happen after `source_id` and checksum.
2. If parser is unknown, do not invent one-off manual import path.
3. Parser-default changes are change-controlled configuration.

### 16.3. Parser-pending path

If parser is not ready:

```text
state = parser_pending
source remains non-importable
onboarding report records blocker
```

---

## 17. Step 8 — Configure Defaults and Validate Taxonomy

### 17.1. Action

Where parser/default model requires it, configure:

```text
CEFR defaults
theme defaults
objective defaults
pattern defaults
item type
language mode
```

### 17.2. Rules

1. Defaults MUST validate against taxonomy.
2. Unknown taxonomy values MUST reject or route to review.
3. Silent coercion is forbidden.

---

## 18. Step 9 — Run Dry-Run Import

### 18.1. Action

Run dry-run import with no production delivery side effects.

### 18.2. Dry-run goals

Dry-run must show:

```text
parseability
schema conformance
candidate row counts
validation failures
duplicate/conflict candidates
accepted/rejected candidate counts
```

### 18.3. Dry-run rule

Dry-run import creates no publishable production items by itself.

---

## 19. Step 10 — Validate Canonical Output

### 19.1. Action

Validate dry-run output against canonical schema and domain rules.

### 19.2. Check categories

Validation should cover:

```text
required fields
option counts
correct-answer references
CEFR values
theme/objective/pattern validity
language mode constraints
status gating assumptions
```

### 19.3. Failure rule

If blocker-level validation fails, source cannot progress to import/publish path.

---

## 20. Step 11 — Classify Duplicates and Conflicts

### 20.1. Action

Review outputs for:

```text
duplicate checksum
duplicate semantic content
answer conflict
taxonomy conflict
near-duplicate review requirement
```

### 20.2. Outcomes

Possible decisions:

```text
proceed
proceed with flagged candidates only
needs review
reject source
block source
```

### 20.3. Rule

Duplicate/conflict classification is explicit review work, not hidden parser behavior.

---

## 21. Step 12 — Generate Onboarding Evidence Package

### 21.1. Required evidence

Each onboarding run should produce:

```text
source intake record
source_id
checksum
inventory entry
manifest entry
parser profile reference or parser_pending note
dry-run report
validation report
duplicate/conflict report
status summary
coverage delta if relevant
```

### 21.2. Evidence rule

Evidence artifacts must be sufficient for:

```text
review
QA verification
demo proof
future audit
```

---

## 22. Step 13 — Decision: Proceed, Hold, Reject or Block

### 22.1. Decision matrix

| Condition | Decision |
|---|---|
| Valid source, parser assigned, dry-run acceptable | proceed |
| Parser missing | hold as `parser_pending` |
| Validation blockers | hold or reject |
| Rights/compliance issue | block or reject |
| Duplicate checksum with unresolved risk | needs review / hold |

### 22.2. Decision rule

Proceed only when onboarding evidence supports a controlled next step. Urgency is not a sufficient reason to override blockers.

---

## 23. Step 14 — Controlled Import and Status Workflow

### 23.1. Action

If proceeding, import accepted candidates into controlled storage and move items through item-level status workflow.

### 23.2. Rules

1. Imported does not mean published.
2. New source items remain non-production until approved/published.
3. Delivery to normal consumers before status approval is forbidden.

### 23.3. Post-import updates

After controlled import:

```text
update generated inventory/coverage reports
record import batch
record release note if production corpus changed
```

---

## 24. Reject and Block Paths

### 24.1. Reject path

Use reject when source should not continue and no temporary hold is needed.

Examples:

```text
irrelevant file
invalid structure with no remediation plan
wrong source class
```

### 24.2. Block path

Use block when source must not proceed until issue is resolved.

Examples:

```text
rights/compliance concern
security-sensitive content problem
serious answer conflict pattern
```

### 24.3. Required records

Reject/block must record:

```text
reason
actor
timestamp
affected source_id
next required action or resolution owner
```

---

## 25. Abort and Rollback Rules

### 25.1. Abort conditions

Abort onboarding run if:

```text
source_id uniqueness breaks
checksum cannot be trusted
manifest discipline is missing
dry-run creates unsafe side effects
rights/compliance issue appears
```

### 25.2. Rollback rule

If controlled import already occurred and later onboarding evidence is invalidated:

```text
route through import/admin/status rollback path
document the event
do not silently delete traceability
```

---

## 26. Demo Path

### 26.1. Demo purpose

This playbook must support UC-030 style proof that future source expansion is governed.

### 26.2. Demo minimum

Demo should show either:

```text
live onboarding of small sample future source
```

or:

```text
artifact-backed onboarding evidence showing source_id, checksum, manifest, dry-run, validation and non-production status.
```

### 26.3. Demo failure rule

If demo accidentally makes new source items deliverable without status workflow, this is a governance defect.

---

## 27. QA and Test Hooks

### 27.1. Minimum QA hooks

This playbook should satisfy:

```text
QA-SRC-002
QA-SRC-003
QA-SRC-005
QA-ONB-001
QA-ONB-002
QA-ONB-003
QA-ONB-004
QA-ONB-007
QA-ONB-008
QA-MVP-015
```

### 27.2. Practical verification questions

1. Did the source get `source_id` before parser assignment?
2. Was checksum recorded before dry-run?
3. Was manifest entry created before dry-run?
4. Did dry-run produce evidence?
5. Are new items still non-production after onboarding proof?

---

## 28. Onboarding Checklist

Use this minimal operational checklist:

```text
[ ] intake record created
[ ] source_id assigned
[ ] checksum recorded
[ ] inventory updated
[ ] manifest entry created
[ ] parser assigned or parser_pending recorded
[ ] defaults validated against taxonomy
[ ] dry-run import executed
[ ] validation report reviewed
[ ] duplicate/conflict outcome reviewed
[ ] onboarding report stored
[ ] next state/decision recorded
```

---

## 29. Completion Criteria

An onboarding run is complete only when:

```text
source state is explicit
evidence package exists
next action is explicit
no hidden production side effects occurred
```

### 29.1. “Done” examples

```text
registered + parser_pending with evidence
dry_run_passed + ready for controlled import review
rejected with reason and audit record
blocked with owner/action recorded
```

### 29.2. Not-done examples

```text
file copied into repo with no source_id
manifest updated but no checksum
dry-run executed but no report preserved
source imported and published through same hidden step
```

---

## 30. Anti-Patterns

Source onboarding failures include:

```text
adding file directly to delivery path
assigning parser before source_id/checksum
manifest references filename only
unknown taxonomy silently accepted
duplicate checksum ignored
dry-run skipped due to urgency
new source items published automatically
```

---

## 31. Open Questions

OQ-ONB-001  Which exact sample future source file will become the canonical recurring onboarding demo fixture?  
OQ-ONB-002  Which parser-profile catalog format will be authoritative first?  
OQ-ONB-003  At what point does parser_pending become blocking enough to require separate roadmap escalation?  
OQ-ONB-004  Which onboarding evidence artifacts will be stored in repo versus external run artifacts?  

---

## 32. Playbook Acceptance Criteria

ONB-AC-001  This document defines a practical onboarding workflow from intake to controlled import/status path.  
ONB-AC-002  It requires source_id, checksum, inventory, manifest and dry-run before production influence.  
ONB-AC-003  It defines parser_pending, reject and block paths.  
ONB-AC-004  It defines onboarding evidence package and demo path.  
ONB-AC-005  It aligns onboarding execution with Constitution, SRS, Use Cases, Data Standard, Security, QA, Operations and Roadmap documents.  

---

## 33. Reference Standards and Alignment

This document aligns with:

- `CONSTITUTION.md` source ID, checksum, manifest and manual-rearrangement rules
- `docs/01_product_charter.md` source onboarding workflow and phase plan
- `docs/02_requirements_srs.md` SRS-SRC, SRS-ONB and SRS-IMP requirements
- `docs/03_use_cases.md` UC-001, UC-002, UC-016 and UC-030
- `docs/04_domain_model.md` source onboarding entities and invariants
- `docs/05_architecture.md` source onboarding flow and failure modes
- `docs/06_data_standard.md` source file and manifest standards
- `docs/08_security_threat_model.md` source/import trust boundary rules
- `docs/09_quality_assurance.md` onboarding QA catalog
- `docs/10_operations.md` onboarding runbook and evidence package
- `docs/14_roadmap.md` phase sequencing for source governance and import foundation

---

## 34. Final Onboarding Rule

API Quiz Bank has safe future expansion only when each new source can be shown to pass through:

```text
intake
source_id
checksum
inventory
manifest
parser assignment
dry-run
validation
duplicate/conflict review
evidence package
status-controlled import path
```

If any of these steps are skipped, hidden or unrecorded, the source is not onboarded. It is merely dropped into the system, and that is prohibited.
