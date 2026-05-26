# API Quiz Bank — Repository Governance

**Документ:** `docs/15_repository_governance.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational repository governance, branch discipline and change-control model; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`–`14_roadmap.md`  
**Дата:** 2026-05-07  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized repository governance maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/05_architecture.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/14_roadmap.md`  
**Наступні документи:** `16_source_onboarding_playbook.md`, `17_admin_workflow.md`, `18_telegram_delivery_playbook.md`, `19_privacy_compliance.md`

---

## 0. Executive Summary

`15_repository_governance.md` визначає, як репозиторій **API Quiz Bank** має бути організований, змінюваний, review-ований і захищений як source of engineering truth.

Головна теза документа:

```text
Repository is not a file bucket.
Repository is the change-control surface of the platform.
```

Repository governance у цьому проєкті існує для того, щоб:

```text
зберігати source-of-truth hierarchy;
запобігати тихим breaking changes;
відрізняти source assets від generated artifacts;
захищати critical paths;
робити зміни traceable, reviewable and testable;
не допустити production-relevant drift через хаотичні commits.
```

Правильна repository logic:

```text
governed structure
  → clear ownership
  → protected changes
  → CI visibility
  → changelog/release discipline
  → auditable history
```

Неправильна repository logic:

```text
direct pushes to critical branch
  → undocumented schema/API changes
  → generated files edited manually
  → no owner review
  → no traceability
```

Final rule:

```text
Repository governance must make it hard to hide unsafe change
and easy to prove what changed, why, by whom and under which gate.
```

---

## 1. Role of This Document

### 1.1. Мета документа

`15_repository_governance.md` відповідає на питання:

```text
Яка структура репозиторію вважається governed?
Які branch and PR rules діють для production-relevant work?
Які файли є critical і потребують ownership/review?
Що робити з generated files, docs, schemas, manifests and migrations?
Які CI/check requirements повинні захищати merge path?
Як ведеться changelog, versioning and release-note discipline?
```

### 1.2. Місце в документаційній ієрархії

```text
CONSTITUTION.md
  ↓
docs/00_vision.md
  ↓
docs/01_product_charter.md
  ↓
docs/02_requirements_srs.md
  ↓
docs/05_architecture.md
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
branch rules / CODEOWNERS / CI policy / changelog discipline
```

### 1.3. Що цей документ робить

Цей документ визначає:

```text
repository structure expectations
governance file set
branch protection and PR rules
change classification
required checks
CODEOWNERS scope
generated-file policy
changelog and versioning discipline
security-sensitive path policy
release/change-control rules
```

### 1.4. Що цей документ не робить

Цей документ НЕ є:

```text
full git tutorial;
hosting-provider-specific setup guide;
substitute for CI workflow implementation;
substitute for security incident playbook;
substitute for source onboarding or admin workflow playbooks.
```

---

## 2. Repository Governance Thesis

### 2.1. Core thesis

```text
API Quiz Bank repository must preserve architectural truth, documentation truth,
schema truth and change-control evidence.
```

### 2.2. Governance purpose

Repository governance має захищати:

```text
Constitution and docs integrity
canonical data contracts
API contract integrity
source onboarding discipline
status/delivery safety
billing/analytics/ops traceability
security-sensitive paths
```

### 2.3. Governance outcome

The repository should allow a reviewer to answer:

```text
what changed
why it changed
what risk it affects
what checks ran
which docs/contracts were updated
who reviewed critical scope
```

---

## 3. Non-Negotiable Repository Rules

1. Production-relevant changes SHOULD go through PR or equivalent approved change path.
2. `main` SHOULD be protected before production-relevant work scales.
3. Generated files MUST NOT be treated as manually editable truth.
4. Secrets MUST NOT be committed.
5. Schema/API/status/billing/publication changes MUST update affected docs and changelog/release notes.
6. Critical paths SHOULD have CODEOWNERS or explicit ownership routing.
7. CI or documented local validation MUST exist for repository-critical checks.

---

## 4. Repository Scope and Structure

### 4.1. Repository role

This repository is expected to contain:

```text
governance docs
source corpus assets
future data manifests and schemas
future API/service code
future database migrations
future infra and CI config
reports and evidence artifacts under governed rules
```

### 4.2. Expected top-level structure

Expected repository shape should remain understandable across:

```text
.agent/
docs/
policies/
QuizBank/
data/
api/
services/
database/
infra/
tests/
reports/
runbooks/
.github/
```

### 4.3. Structure rule

Repository SHOULD maintain clear separation between:

```text
source assets
generated artifacts
machine-readable contracts
runtime code
docs
tests
ops/runbooks
```

---

## 5. Required Repository Governance Files

The governed repository SHOULD maintain or progressively add:

```text
CONSTITUTION.md
README.md
CHANGELOG.md
SECURITY.md
CONTRIBUTING.md
CODEOWNERS
.github/workflows/quality.yml
.github/dependabot.yml or equivalent
policies/
runbooks/
```

### 5.1. File roles

| File | Role |
|---|---|
| `CONSTITUTION.md` | Top-level project law and launch/governance contract |
| `README.md` | Current repo orientation and generated/current-state entrypoint |
| `CHANGELOG.md` | Production-relevant change record |
| `SECURITY.md` | Security reporting and disclosure path |
| `CONTRIBUTING.md` | Contribution and change rules |
| `CODEOWNERS` | Review routing for critical paths |

---

## 6. Branch and Merge Policy

### 6.1. Main branch rule

The `main` branch SHOULD be treated as protected branch for production-relevant work.

### 6.2. Direct push policy

Direct push to `main` SHOULD be avoided for production-relevant changes unless an explicitly approved emergency path exists and is documented.

### 6.3. Merge policy

Merge to protected/default branch SHOULD require:

```text
review
required checks
scope-appropriate documentation updates
changelog/release-note decision
```

### 6.4. History rewrite rule

Force-push, history rewrite or bypass of guardrails on protected branch is forbidden unless explicitly approved and operationally justified.

---

## 7. Change Path Model

### 7.1. Normal change path

Recommended path:

```text
branch
  → scoped changes
  → required checks
  → review
  → merge
  → changelog/release-note update if needed
```

### 7.2. Emergency change path

Emergency path may exist only when:

```text
normal path is too slow for containment/recovery;
reason is documented;
owner approval exists where required;
follow-up review/changelog/incident note closes the gap;
```

### 7.3. Change-traceability rule

Every production-relevant change should be traceable through:

```text
commit history
PR or approved change path
check results
artifact/report if relevant
changelog/release note if relevant
```

---

## 8. Change Classification

### 8.1. Change classes

| Class | Examples | Required posture |
|---|---|---|
| Documentation-only | wording, non-normative examples | lightweight review, no hidden semantic drift |
| Contract change | schema, OpenAPI, manifests, taxonomy | owner review, docs update, contract checks |
| Delivery logic change | selection, status filter, Telegram delivery | tests, review, launch-impact awareness |
| Security-sensitive | auth, secrets, permissions, CI credentials | security-aware review, no bypass |
| Production operations | migrations, deploy, rollback, backup paths | ops review, explicit risk notes |
| Generated artifact refresh | README/inventory/reports regeneration | provenance preserved, not hand-edited |

### 8.2. Classification rule

If one change spans multiple classes, apply the strictest governance requirements.

---

## 9. CODEOWNERS and Ownership Routing

### 9.1. Critical path ownership

Critical areas SHOULD have code owners or explicit review routing:

```text
CONSTITUTION.md
docs/
data/schemas/
data/taxonomy/
data/manifests/
services/api/
services/telegram-worker/
database/migrations/
infra/
security-related configs
```

### 9.2. Ownership principle

Ownership is not about bureaucracy. It exists so that:

```text
schema changes get data review
API changes get contract review
security-sensitive paths get security-aware review
ops paths get release/rollback-aware review
```

### 9.3. Minimum routing rule

If `CODEOWNERS` is absent in current snapshot, repository governance still requires explicit review responsibility for critical paths in the approved change path.

---

## 10. Pull Request Policy

### 10.1. PR expectations

Production-relevant PRs SHOULD explain:

```text
scope
affected contracts or docs
required checks
risk or limitation
changelog/release-note impact
```

### 10.2. PR review rules

Review should confirm:

```text
no hidden scope drift
docs updated if behavior/contracts changed
generated artifacts handled correctly
no secret exposure
required checks passed or are explicitly blocked/waived with rationale
```

### 10.3. PR anti-patterns

Avoid:

```text
mixed unrelated changes
schema/API drift without docs
security-sensitive edits hidden in large cosmetic diff
manual edits to generated reports presented as source change
```

---

## 11. Required Checks and CI Gate Policy

### 11.1. Repository-critical checks

Before merge to protected/default branch, checks SHOULD include as relevant:

```text
schema validation
manifest validation
taxonomy validation
unit tests
integration tests
API contract tests
security/dependency scan
lint/static checks
migration check
README/inventory generation check
```

### 11.2. Scope-sensitive check rule

Checks should be relevant to changed scope. However, scope relevance must not be used to skip obvious contract or security validation.

### 11.3. CI visibility rule

CI must make quality visible and block unsafe changes before they reach protected branch or release path.

### 11.4. Current committed CI gates

The current GitHub Actions workflow runs:

```text
no-secrets scan
public fixture inventory and constitution checks
public unittest invariant suite
runtime coverage gate
runtime import-cycle guard
numeric limit and basic whitespace style guard
PostgreSQL backend boundary tests
```

---

## 12. Generated File Policy

### 12.1. Generated artifact principle

Generated files are derived artifacts, not manual truth.

### 12.2. Generated file examples

Typical governed generated files may include:

```text
QuizBank/README.md
inventory reports
coverage reports
import reports
release QA reports
demo evidence reports
```

### 12.3. Generated file rules

1. Generated files should be clearly marked as generated.
2. Manual editing of generated report truth is prohibited.
3. If regeneration changes content unexpectedly, the underlying source/tooling change must be reviewed.
4. Generated outputs should retain timestamps/input references where appropriate.

---

## 13. Documentation Update Policy

### 13.1. When docs must change

Docs must be updated when change affects:

```text
requirements
use cases
architecture
schemas/manifests/taxonomy
API contract
security model
operations
billing/analytics logic
demo/public claims
```

### 13.2. Documentation integrity rule

No silent breaking change to schema, API, database, status rules or public behavior should merge without documentation update or an explicit note explaining why no doc update is needed.

### 13.3. Requirement-impacting changes

Requirement-impacting changes SHOULD update SRS or record why no SRS update is necessary.

---

## 14. Changelog and Release-Note Discipline

### 14.1. Changelog purpose

`CHANGELOG.md` exists to record production-relevant changes in a way that supports traceability, release communication and rollback understanding.

### 14.2. What requires changelog or release-note entry

At minimum:

```text
API behavior changes
schema changes
import result or source workflow changes
publication/status policy changes
billing/entitlement changes
permission or security-impacting changes
production delivery behavior changes
```

### 14.3. Changelog rule

If change would matter to:

```text
operators
integrators
reviewers
future debugging
launch risk assessment
```

then it likely needs changelog or release-note trace.

---

## 15. Versioning Discipline

### 15.1. Versioned artifacts

Repository governance should preserve versioning expectations for:

```text
OpenAPI contract
schemas
migrations
status/publication rules
import manifests and parser defaults
docs with normative behavior
```

### 15.2. Breaking-change rule

Breaking changes to schema, API, database or status rules MUST have:

```text
migration or transition plan
documentation update
change-control note
```

### 15.3. Versioning anti-pattern

Changing contract or schema semantics without versioning, migration note or release-note trace is forbidden.

---

## 16. Security-Sensitive Repository Policy

### 16.1. Secret handling

Secrets MUST NOT be committed to repository.

This includes:

```text
API keys
Telegram bot tokens
payment-provider credentials
deploy/runtime secrets
CI secrets
private keys
```

### 16.2. Sensitive path review

Changes in these areas SHOULD require stricter review:

```text
auth or permission code
billing/security paths
CI/CD config
infra/
database/migrations/
schemas/manifests affecting import safety
```

### 16.3. Repository security rule

Repository and CI are security-critical surfaces. Branch protection, review, secret scanning and least-privilege CI permissions are governance requirements, not optional polish.

---

## 17. Dependency and Supply-Chain Policy

### 17.1. Dependency discipline

Dependency changes SHOULD be:

```text
intentional
reviewed
scanned where tooling exists
traceable in changelog/release notes when risk-relevant
```

### 17.2. Dependency anti-patterns

Avoid:

```text
unreviewed security-sensitive dependency bump
dependency additions “just in case”
lockfile drift with no rationale
```

### 17.3. Supply-chain rule

If a dependency or CI permission meaningfully changes attack surface, governance must treat it as security-sensitive change.

---

## 18. Release and Tagging Posture

### 18.1. Release posture

Repository governance should support:

```text
reviewed merge history
traceable release notes
artifact/regression evidence
rollback understanding
```

### 18.2. Release readiness inputs

Release decision should consider:

```text
required checks
launch gates
changelog completeness
known limitations
security/ops concerns
```

### 18.3. Tagging/version note

Specific tagging/versioning scheme may evolve, but repository governance requires consistency and traceability once public/pilot/production releases are made.

---

## 19. Repository Governance and Environment Boundaries

### 19.1. Repo vs runtime

Repository governance must distinguish:

```text
what belongs in repo
what is generated outside repo
what is secret and must stay outside repo
what is demo-only and must be labeled
```

### 19.2. Boundary rule

Demo credentials must not work in production by accident. Production secrets must not appear in local/demo/CI logs or committed files.

---

## 20. Minimum Governance for Current Snapshot

Given the current repository state, minimum governance already implied by docs is:

```text
protect documentation integrity
do not hand-edit generated QuizBank/README.md as truth
do not commit secrets
keep cross-document references consistent
preserve Constitution priority
record normative document drift through explicit edits, not silent mismatch
```

### 20.1. Current-snapshot caution

The current workspace may not yet have actual git hosting, branch protection, CI configs or CODEOWNERS committed. This document therefore defines the governance contract that implementation/hosting must satisfy once those layers are active.

---

## 21. Repository Governance QA Expectations

Repository governance should be verifiable through:

```text
branch protection inspection
CODEOWNERS presence or explicit review routing
CI workflow visibility
secret scanning results
changelog inspection
PR/change-path audit
generated-file provenance checks
```

### 21.1. Minimum QA questions

1. Can protected branches block unsafe merge?
2. Are required checks visible?
3. Are critical paths owned?
4. Are generated files treated correctly?
5. Are secrets prevented from entering repo?
6. Are contract-changing PRs updating docs/changelog?

---

## 22. Repository Governance Anti-Patterns

Governance failures include:

```text
direct push to protected branch
schema/API change with no doc update
manual edit to generated report treated as source truth
security-sensitive config merged without review
CI bypass for convenience
no owner routing for critical contracts
secret committed and “cleaned later”
```

---

## 23. Open Repository Governance Questions

OQ-REPO-001  Which git hosting platform and branch-protection model will be authoritative first?  
OQ-REPO-002  Which exact CI provider and security/dependency scanners will be mandatory?  
OQ-REPO-003  Will signed commits/tags be required for production releases?  
OQ-REPO-004  What exact PR template fields will be mandatory for production-relevant changes?  
OQ-REPO-005  Which paths must require explicit security-owner review from day one?  

---

## 24. Repository Governance Acceptance Criteria

REPO-AC-001  This document defines repository structure expectations and governance-file set.  
REPO-AC-002  It defines branch protection, PR, CI and review discipline.  
REPO-AC-003  It defines generated-file, changelog and versioning rules.  
REPO-AC-004  It defines security-sensitive repository path handling.  
REPO-AC-005  It aligns repository governance with Constitution, SRS, Architecture, Security, QA, Operations and Roadmap documents.  

---

## 25. Reference Standards and Alignment

This document aligns with:

- `CONSTITUTION.md` section 21 repository structure, protected branch, CODEOWNERS and changelog rules
- `docs/01_product_charter.md` repository discipline references and required governance files
- `docs/02_requirements_srs.md` NFR-ENG-001..010 and production acceptance criteria
- `docs/05_architecture.md` repository/CI discipline and protected-branch expectations
- `docs/08_security_threat_model.md` repository and CI/CD threat model
- `docs/09_quality_assurance.md` CI/CD quality gates and release-note expectations
- `docs/10_operations.md` remaining-documents list and recommended repository governance files
- `docs/14_roadmap.md` sequencing of repository governance as post-roadmap execution document

---

## 26. Final Repository Governance Rule

API Quiz Bank repository is governed only when the team can prove:

```text
which files are source truth,
which files are generated,
which branches are protected,
which checks guard merge,
which changes require owners,
which release notes document behavior shifts,
and which secrets never entered repository history.
```

If a change cannot be reviewed, validated, routed and traced, repository governance is incomplete even if the code itself appears correct.
