# API Quiz Bank — Roadmap

**Документ:** `docs/14_roadmap.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational execution roadmap and phase-planning model; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`–`13_stanford_presentation_outline.md`  
**Дата:** 2026-05-07  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized roadmap maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/06_data_standard.md`, `docs/07_api_standard.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/11_billing_model.md`, `docs/12_analytics_model.md`, `docs/13_stanford_presentation_outline.md`  
**Наступні документи:** `15_repository_governance.md`, `16_source_onboarding_playbook.md`, `17_admin_workflow.md`, `18_telegram_delivery_playbook.md`, `19_privacy_compliance.md`

---

## 0. Executive Summary

`14_roadmap.md` визначає, у якій послідовності **API Quiz Bank** має рухатися від governed corpus до demo-ready, pilot-ready, beta-ready and production-ready platform.

Головна теза документа:

```text
Roadmap is not a wish list.
Roadmap is controlled sequencing of proof, delivery and risk reduction.
```

У цьому проєкті roadmap повинен відповідати на три питання:

```text
Що саме робимо спочатку?
Чому саме в такій послідовності?
Який proof/gate переводить нас у наступну фазу?
```

Правильна roadmap logic:

```text
governance and source control
  → canonical data and import
  → database and API core
  → selection and controlled delivery
  → admin / billing / analytics
  → Stanford demo readiness
  → pilot hardening
  → beta readiness
  → production discipline
```

Неправильна roadmap logic:

```text
UI / website / public claims first
  → API and data model later
  → governance gaps hidden under demos
```

Foundational doc set currently uses this baseline:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 canonical themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Roadmap must remain evidence-aware. Future implementation may operate on a newer corpus snapshot, but phase gates and success criteria must still remain governed by the same rules.

Final rule:

```text
No phase may be treated as complete because code exists.
A phase is complete only when its gate criteria, artifacts and limitations are explicit.
```

---

## 1. Role of This Document

### 1.1. Мета документа

`14_roadmap.md` відповідає на питання:

```text
Які фази є між current repo state and production-ready platform?
Які workstreams ідуть паралельно, а які є blocking?
Які artifacts and gates визначають завершення фази?
Що входить у MVP, Pilot, Beta, Production and Stanford demo?
Які anti-patterns не дозволяють чесно рухатися вперед?
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
docs/03_use_cases.md
  ↓
docs/04_domain_model.md
  ↓
docs/05_architecture.md
  ↓
docs/06_data_standard.md
  ↓
docs/07_api_standard.md
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
docs/13_stanford_presentation_outline.md
  ↓
docs/14_roadmap.md
  ↓
execution planning / implementation sequencing / launch planning
```

### 1.3. Що цей документ робить

Цей документ визначає:

```text
roadmap thesis
phase model
workstream model
dependency model
gates and exit criteria
phase-by-phase deliverables
MVP/Pilot/Beta/Production cut
Stanford demo positioning
risk-driven sequencing
anti-patterns
```

### 1.4. Що цей документ не робить

Цей документ НЕ є:

```text
day-by-day sprint board;
team staffing plan;
budget plan;
cloud vendor migration guide;
substitute for individual playbooks and runbooks;
permission to skip constitutional gates.
```

---

## 2. Roadmap Discipline

У межах API Quiz Bank roadmap є engineering sequencing layer між docs and execution.

### 2.1. Roadmap quality attributes

Roadmap має бути:

| Attribute | Meaning |
|---|---|
| Traceable | Кожна фаза пов'язана з docs, gates, requirements or demo proof. |
| Dependency-aware | Blocking prerequisites explicit. |
| Honest | Planned later work не маскується під MVP. |
| Risk-reducing | Послідовність спершу закриває highest structural risks. |
| Governed | Phase completion вимагає artifacts and criteria, не лише активність. |
| Non-chaotic | Public/pilot work не стартує до стабілізації data/API core. |

### 2.2. Roadmap verification rule

Bad roadmap statement:

```text
Build website, bot and billing, then formalize data later.
```

Good roadmap statement:

```text
Finish source governance, canonical schema, import traceability, database-backed delivery and status-aware API
before broadening adapters, public beta claims or paid scale.
```

---

## 3. Core Roadmap Thesis

### 3.1. Execution thesis

```text
API Quiz Bank should prove governability before scale,
prove controlled delivery before audience expansion,
and prove operations before production claims.
```

### 3.2. Sequence thesis

The platform should mature in this order:

```text
documents and governance
  → source onboarding discipline
  → canonical data discipline
  → production database
  → API and selection
  → consumer delivery
  → admin control
  → billing and analytics
  → demo proof
  → pilot operations
  → beta hardening
  → production launch discipline
```

### 3.3. Main roadmap principle

New capability is allowed to expand only if the lower layer it depends on is already governed enough for that expansion.

---

## 4. Non-Negotiable Sequencing Rules

1. Do not build public-facing scale features before canonical data and selection rules are stable enough for MVP.
2. Do not let Telegram, web or API consumers read raw CSV directly.
3. Do not claim paid access before internal entitlement and quota logic exists.
4. Do not claim analytics maturity before report lineage and scope controls exist.
5. Do not claim production readiness before backup/restore, monitoring and incident paths exist.
6. Do not treat demo readiness as a substitute for MVP readiness.
7. Do not postpone governance work in favor of cosmetic presentation work.

---

## 5. Roadmap Objectives

The roadmap should achieve:

1. Govern current corpus and future sources.
2. Establish canonical data and operational source of truth.
3. Deliver one controlled next-quiz API path.
4. Prove status-aware, anti-repeat, entitlement-aware delivery.
5. Provide operator/admin control for publication decisions.
6. Provide analytics, billing and demo evidence.
7. Prepare for pilot, beta and production without architectural contradiction.

---

## 6. Workstream Model

### 6.1. Primary workstreams

| Workstream | Responsibility |
|---|---|
| Documentation and governance | Constitution, standards, playbooks, gates |
| Source and import | Inventory, source IDs, checksums, parser mapping, dry-run import |
| Data and schema | Canonical schema, taxonomy, normalized data model |
| Database and migrations | PostgreSQL or equivalent operational storage |
| API and contracts | OpenAPI, health/readiness, next-item endpoint, error model |
| Selection and delivery | Status filter, anti-repeat, consumer rules, delivery logs |
| Telegram adapter | Controlled Telegram delivery and failure logging |
| Admin workflow | Review, approve, publish, block, retire, audit trail |
| Billing and entitlements | Plans, entitlements, quota enforcement, usage events |
| Analytics and reports | Corpus, delivery, usage, quality and ops reports |
| Operations and security | Logs, health, backups, restore, incident, auth/privacy controls |
| Demo and presentation | Demo script, fallback artifacts, evidence package |

### 6.2. Workstream rule

No workstream is fully independent. Roadmap must preserve the order in which one stream unlocks another.

---

## 7. Dependency Model

### 7.1. Main dependency chain

```text
Governance docs
  → Source inventory / manifest / taxonomy
  → Canonical schema / importer
  → Database model
  → API contract / health / next-item
  → Selection and delivery logging
  → Telegram / admin / billing / analytics
  → Demo package
  → Pilot/Beta/Production hardening
```

### 7.2. Blocking dependencies

| Capability | Blocked by |
|---|---|
| Next eligible item API | canonical schema, database, selection rules |
| Telegram delivery | API/selection, status-aware delivery, logging |
| Billing enforcement | consumer model, API decision path, usage logging |
| Delivery analytics | delivery log |
| Attempt analytics | attempt capture model |
| Admin publish flow | status model, source traceability, audit log |
| Production claim | ops/security/privacy gates |
| Stanford demo claim | artifact set, demo script, negative control, honest limitations |

---

## 8. Launch and Maturity Model

The roadmap distinguishes:

```text
MVP
Stanford demo
Closed pilot
Public beta
Production
```

### 8.1. MVP meaning

MVP exists to prove the core thesis:

```text
governed corpus
canonical schema
database-backed API
controlled next-item delivery
basic logging, admin path, billing logic and analytics proof
```

### 8.2. Stanford demo meaning

Stanford demo is not a separate product phase from reality. It is a proof packaging layer on top of MVP/pilot-capable system behavior and artifacts.

### 8.3. Closed pilot meaning

Closed pilot adds controlled external or semi-external usage with real operational visibility, especially around Telegram, delivery reliability and support boundaries.

### 8.4. Public beta meaning

Public beta adds stronger rate limits, privacy posture, alerting, support and consumer-facing stability.

### 8.5. Production meaning

Production requires disciplined operations, security, privacy, deployment, backup/restore and documented limitations beyond MVP proof.

---

## 9. Phase Overview

Recommended roadmap phases:

1. Foundation documentation and governance
2. Source governance and corpus inventory
3. Canonical data and import foundation
4. Database and API core
5. Selection and controlled delivery
6. Admin, billing and analytics MVP
7. Stanford-ready demo package
8. Closed pilot hardening
9. Public beta readiness
10. Production readiness

Current phase status and evidence are tracked in:

```text
reports/roadmap/roadmap_evidence_register.md
```

That register is the phase closure ledger. It must distinguish local MVP proof from pilot,
beta or production evidence, and it must not mark external gates complete without
artifact-backed environment proof.

---

## 10. Phase 0 — Documentation Foundation

### 10.1. Goal

```text
Establish constitutional, product, requirements and architecture source of truth.
```

### 10.2. Deliverables

```text
Constitution
Vision
Product Charter
SRS
Use Cases
Domain Model
Architecture
Data/API/Security/QA/Operations standards
Billing/Analytics/Presentation docs
```

### 10.3. Exit criteria

```text
core documentation stack exists
phase gates are documented
source-of-truth hierarchy is explicit
major workstreams have normative guidance
```

---

## 11. Phase 1 — Source Governance and Corpus Inventory

### 11.1. Goal

```text
Turn the corpus from loose files into governed source assets.
```

### 11.2. Deliverables

```text
file inventory
source IDs
checksums
import manifest
taxonomy files
generated README/report discipline
sample future source onboarding path
```

### 11.3. Exit criteria

```text
all active sources have source_id and checksum
manifest exists
taxonomy exists
inventory is reproducible
new sample source can be onboarded through governed path
```

### 11.4. Main gates

```text
Constitution Gate 0
Constitution Gate 1 partial
AC-MVP-001
AC-MVP-002
```

---

## 12. Phase 2 — Canonical Data and Import Foundation

### 12.1. Goal

```text
Define one canonical item model and controlled import pipeline.
```

### 12.2. Deliverables

```text
canonical schema
normalized sample JSONL
parser mapping
dry-run import path
validation report
status lifecycle
duplicate/conflict handling foundation
```

### 12.3. Exit criteria

```text
schema validation passes for pilot subset
canonical output exists
import traceability preserved
status lifecycle documented and testable
```

### 12.4. Main gates

```text
Constitution Gate 1
AC-MVP-003
AC-MVP-004
SRS-ONB / SRS-IMP / SRS-STAT foundations
```

---

## 13. Phase 3 — Database and API Core

### 13.1. Goal

```text
Move from raw/source-centric model to operational source of truth and controlled API surface.
```

### 13.2. Deliverables

```text
PostgreSQL schema or equivalent DB model
migrations
quiz_items/options/sources/consumers/deliveries tables
OpenAPI contract
health endpoint
topics/levels endpoints
next-item endpoint
Problem Details error model
auth foundation
```

### 13.3. Exit criteria

```text
database stores core entities
API contract exists
next-item API can return eligible item
status filtering and failure responses are visible
```

### 13.4. Main gates

```text
Constitution Gate 2
Constitution Gate 3
AC-MVP-005
AC-MVP-006
AC-MVP-007
```

---

## 14. Phase 4 — Selection and Controlled Delivery

### 14.1. Goal

```text
Prove that delivery is status-aware, consumer-aware and non-chaotic.
```

### 14.2. Deliverables

```text
selection engine
level/theme filtering
anti-repeat per consumer
quota check
delivery reservation/logging
delivery error handling
one consumer delivery path
```

### 14.3. Exit criteria

```text
repeat policy is demonstrable
delivery logs are created
quota/auth/status denials are demonstrable
normal consumers do not receive draft items
```

### 14.4. Main gates

```text
Constitution Gate 4
AC-MVP-008
AC-MVP-009
AC-MVP-010
```

---

## 15. Phase 5 — Admin, Billing and Analytics MVP

### 15.1. Goal

```text
Give operators controlled product governance and basic business/analytics proof.
```

### 15.2. Deliverables

```text
admin/operational workflow for status changes
approve/publish/block/retire path
audit log
plan model
entitlement model
quota model
manual grants
usage tracking
basic corpus/delivery analytics reports
quality and coverage visibility
```

### 15.3. Exit criteria

```text
admin can control publication lifecycle
consumer access is entitlement-based
quota enforcement is testable
basic analytics report exists
```

### 15.4. Main gates

```text
Constitution Gate 6
Constitution Gate 7
AC-MVP-011
AC-MVP-012
```

---

## 16. Phase 6 — Stanford-Ready Demo Package

### 16.1. Goal

```text
Package the governed system into reproducible technical presentation proof.
```

### 16.2. Deliverables

```text
presentation outline
architecture and data-flow diagrams
demo script
source onboarding proof
canonical validation proof
API next-item proof
negative control proof
delivery log excerpt
analytics snapshot
billing/usage proof where in scope
fallback artifact package
known limitations sheet
```

### 16.3. Exit criteria

```text
demo script exists
demo can run end-to-end or degrade to artifact-backed proof
negative control is shown
claims are evidence-backed
limitations are explicit
```

### 16.4. Main gates

```text
AC-MVP-013
AC-MVP-014
AC-MVP-015
QA-DEMO-GATE-001..011
OPS-DEMO-001..010
```

---

## 17. Phase 7 — Closed Pilot Hardening

### 17.1. Goal

```text
Support one or more controlled pilot consumers with real operational visibility.
```

### 17.2. Deliverables

```text
identified pilot environment
Telegram dry-run or controlled real send
worker failure visibility
backup process
restore procedure
incident playbook
consumer disable/suspension path
support/issue path
consumer-scoped analytics
```

### 17.3. Exit criteria

```text
pilot environment is controlled
delivery failures are observable
ops/security basics exist for pilot
consumer-scoped data isolation is respected
```

### 17.4. Main gates

```text
Constitution Gate 5
OPS-PILOT-001..009
Pilot-level SRS-TG / SRS-AN / SRS-CONS checks
```

---

## 18. Phase 8 — Public Beta Readiness

### 18.1. Goal

```text
Expand from controlled pilot to broader but still limited public use with stronger safeguards.
```

### 18.2. Deliverables

```text
rate limits or usage controls
alerts or reviewed ops cadence
restore drill evidence
release/rollback process
privacy review for beta scope
quality issue reporting visibility
consumer-facing stability improvements
```

### 18.3. Exit criteria

```text
beta safety controls exist
privacy/security posture fits beta scope
reporting and support can handle broader usage
```

### 18.4. Main gates

```text
OPS-BETA-001..008
Beta-level SRS security/privacy/performance expectations
```

---

## 19. Phase 9 — Production Readiness

### 19.1. Goal

```text
Make production claims only after operational, security and privacy discipline is real.
```

### 19.2. Deliverables

```text
CI/CD or controlled deployment process
monitored backups
recorded restore drill
monitoring dashboard
critical alerts or formal owner review
incident playbook
verified rollback paths
versioned/tested migrations
support/contact path
privacy/legal review
documented launch limitations
```

### 19.3. Exit criteria

```text
production operations gate passes
production acceptance criteria are met
public/paid claims can be defended with evidence
```

### 19.4. Main gates

```text
AC-PROD-001..012
OPS-PROD-001..012
Constitution public/pilot launch gate
```

---

## 20. MVP Cut

### 20.1. What MVP includes

MVP should include enough to prove:

```text
governed source onboarding
canonical schema
database-backed next-item API
status-aware selection
anti-repeat and delivery logging
admin/operational publication workflow
manual/provider-light entitlement/quota logic
basic analytics report
demo path
```

### 20.2. What MVP does not require

By default MVP does not require:

```text
full public website
fully automated payment provider integration
advanced per-user learner analytics
multi-channel Telegram scale
organization-grade dashboards
warehouse/BI platform
production SLO maturity
```

---

## 21. Stanford Demo Cut

Stanford demo sits on top of MVP and partial pilot evidence.

### 21.1. Demo requires

```text
governed corpus baseline
source onboarding proof
canonical validation proof
next-item API proof
delivery log proof
negative control
analytics evidence
artifact-backed limitations
```

### 21.2. Demo does not require

```text
full production launch
complete automation of every admin path
massive scale proof
public-grade consumer UI
```

---

## 22. Cross-Workstream Phase Mapping

| Phase | Primary owning workstreams |
|---|---|
| Documentation Foundation | Documentation, governance |
| Source Governance | Source/import, data, docs |
| Canonical Data | Source/import, data/schema, QA |
| Database/API Core | Database, API/contracts, security |
| Selection/Delivery | Selection/delivery, API, analytics, QA |
| Admin/Billing/Analytics MVP | Admin, billing, analytics, audit/security |
| Stanford Demo | Demo/presentation, operations, analytics, billing |
| Closed Pilot | Telegram, operations, support, analytics |
| Public Beta | Ops/security/privacy, performance, support |
| Production | All critical workstreams with ops/security lead gating |

---

## 23. Gate Mapping Summary

| Roadmap phase | Main gate families |
|---|---|
| Documentation Foundation | Governance foundation |
| Source Governance | Gate 0, Gate 1 |
| Canonical Data | Gate 1, MVP data acceptance |
| Database/API Core | Gate 2, Gate 3 |
| Selection/Delivery | Gate 4, MVP delivery acceptance |
| Admin/Billing/Analytics MVP | Gate 6, Gate 7, MVP acceptance |
| Stanford Demo | QA demo gate, ops demo gate |
| Closed Pilot | Gate 5, ops pilot gate |
| Public Beta | ops beta gate, privacy/security beta checks |
| Production | public/pilot launch gate, production acceptance, ops production gate |

---

## 24. Anti-Patterns and Scope Failures

Roadmap failure patterns include:

```text
public site before canonical data/API core;
Telegram bot becoming hidden core logic;
billing before entitlement model;
analytics dashboards before trustworthy records;
presentation work replacing delivery/system proof;
manual MVP steps left undocumented;
production claims from demo-only evidence;
source onboarding skipped because “current files already exist”.
```

---

## 25. Risk-Driven Prioritization

### 25.1. Highest structural risks first

Priority should first reduce:

```text
raw file chaos
missing source traceability
lack of canonical schema
direct consumer access to CSV
status-free delivery
missing delivery logs
unclear publication control
demo overclaiming
```

### 25.2. Later optimization risks

Later phases may address:

```text
advanced analytics
scaling performance
warehouse optimization
full provider automation
organization dashboards
adaptive difficulty
```

---

## 26. Roadmap Review and Change Control

### 26.1. When roadmap must change

Roadmap review is required if:

```text
phase gate changes
MVP scope changes
new consumer type is promoted earlier
security/privacy requirement changes phase
demo claim changes materially
production launch timeline changes due to missing gates
```

### 26.2. Change control rule

Roadmap changes affecting launch sequence, public claims or MVP boundaries should be reflected in Product Charter, SRS and affected downstream playbooks.

---

## 27. Open Roadmap Questions

OQ-RM-001  Which implementation stack lands first in committed code: Python/FastAPI or another equivalent stack?  
OQ-RM-002  What exact environment will host first closed pilot?  
OQ-RM-003  What first real consumer after internal demo is prioritized: Telegram channel, external API client or teacher workflow?  
OQ-RM-004  How much of admin workflow remains CLI-based through MVP and pilot?  
OQ-RM-005  Which privacy/legal constraints may pull `19_privacy_compliance.md` earlier as a blocking document?  
OQ-RM-006  What exact sample future source file is used as recurring onboarding proof?  
OQ-RM-007  Which production-facing capability is intentionally delayed even if technically feasible, to preserve roadmap discipline?  

---

## 28. Roadmap Acceptance Criteria

RM-AC-001  This document defines explicit phases from documentation foundation to production readiness.  
RM-AC-002  It defines workstreams and dependencies, not only a linear wish list.  
RM-AC-003  It defines MVP, Stanford demo, pilot, beta and production cuts.  
RM-AC-004  It maps phases to documented gates and acceptance criteria.  
RM-AC-005  It states what must not be done out of order.  
RM-AC-006  It aligns roadmap sequencing with Constitution, Product Charter, SRS, Operations, Billing, Analytics and Presentation documents.  

---

## 29. Reference Standards and Alignment

This document aligns with:

- `CONSTITUTION.md` section 25 release and launch gates and section 33 implementation roadmap
- `docs/01_product_charter.md` sections 12, 13, 14 and 32
- `docs/02_requirements_srs.md` MVP and production acceptance criteria
- `docs/10_operations.md` launch gates and remaining-documents sequencing
- `docs/11_billing_model.md` phased billing roadmap
- `docs/12_analytics_model.md` analytics implementation roadmap
- `docs/13_stanford_presentation_outline.md` presentation-asset roadmap

---

## 30. Final Roadmap Rule

API Quiz Bank is not moving forward because more things are being built.

API Quiz Bank is moving forward when each phase can answer:

```text
what was governed,
what was proven,
what risk was reduced,
what gate was passed,
what remains limited,
and why the next phase is now justified.
```

If a capability depends on a lower layer that is still undocumented, ungoverned or unproven, that capability should stay later in the roadmap.
