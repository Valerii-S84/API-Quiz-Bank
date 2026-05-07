# API Quiz Bank — Software Requirements Specification

**Документ:** `docs/02_requirements_srs.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** formal SRS draft; subordinate to `CONSTITUTION.md`, aligned with `00_vision.md` and `01_product_charter.md`  
**Дата:** 2026-04-27  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized product maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`  
**Наступні документи:** `03_use_cases.md`, `04_domain_model.md`, `05_architecture.md`, `06_data_standard.md`, `07_api_standard.md`, `08_security_threat_model.md`, `09_quality_assurance.md`, `10_operations.md`, `11_billing_model.md`, `12_analytics_model.md`, `13_stanford_presentation_outline.md`

---

## 0. Executive Summary

**API Quiz Bank** — це керована API-first платформа для німецьких вікторин. Цей Software Requirements Specification перетворює Конституцію, Vision і Product Charter у формальні вимоги, які можна реалізувати, тестувати, перевіряти, трасувати й презентувати як серйозний engineering product.

Головний принцип SRS:

```text
No serious implementation without traceable requirements.
No public delivery without source traceability, status control, entitlement control and delivery logging.
No scale claim without tests, operations and measurable acceptance criteria.
```

Поточний operational baseline:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Цей SRS НЕ повторює аудит правильності самих вікторин. Вікторини вже перевірені як content asset. SRS визначає, як перетворити цей asset у production-grade platform:

```text
raw / candidate source files
  → source registry
  → inventory and checksum
  → import manifest
  → parser profile
  → dry-run import
  → canonical validation
  → duplicate/conflict classification
  → import batch
  → production database
  → status workflow
  → selection engine
  → versioned API
  → Telegram / web / bots / schools / external clients
  → delivery logs / attempts / analytics / billing / operations
```

Ключове розширювальне правило:

```text
New quiz files are onboarded, not dropped.
```

Майбутні файли з вікторинами повинні проходити source onboarding workflow. Жоден новий файл не може напряму потрапити у production delivery, Telegram, сайт або платний API.

---

## 1. Purpose of This SRS

### 1.1. Мета документа

`02_requirements_srs.md` визначає:

- functional requirements;
- non-functional requirements;
- data requirements;
- API/interface requirements;
- security requirements;
- operations requirements;
- launch gates;
- acceptance criteria;
- traceability rules;
- test and verification logic;
- MVP, beta, production and Stanford-ready readiness requirements.

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
implementation / tests / launch / operations
```

Якщо цей SRS суперечить Конституції, пріоритет має `CONSTITUTION.md`. Якщо implementation суперечить цьому SRS, implementation має бути виправлена або SRS має бути офіційно змінений через change control.

### 1.3. Чим цей SRS не є

Цей документ не є:

- повною database schema;
- повним OpenAPI contract;
- UI design specification;
- повторним content audit;
- business plan;
- юридичною політикою privacy/compliance;
- backlog task list;
- документацією конкретного framework;
- гарантією, що всі вимоги будуть реалізовані в першому MVP.

SRS визначає **що система повинна робити** і **як це буде перевірятися**. Architecture and implementation documents визначатимуть, **як саме це буде реалізовано**.

---

## 2. Stanford-Style Requirements Discipline

У межах API Quiz Bank “Stanford-style” означає не формальне схвалення Stanford, а інженерну дисципліну рівня professional review:

```text
vision → needs → features → requirements → use cases → architecture → contracts → tests → operations → demo evidence
```

### 2.1. Принципи SRS

1. **Traceability.** Кожна важлива вимога повинна бути повʼязана з product goal, use case, component, test and acceptance criterion.
2. **Verifiability.** Вимога не вважається якісною, якщо її неможливо перевірити через test, inspection, demonstration або analysis.
3. **Change control.** Вимоги не змінюються хаотично. Зміни проходять versioning, changelog and approval.
4. **Operational realism.** Вимоги мають враховувати source files, import, API, Telegram, billing, analytics, security and operations together.
5. **MVP discipline.** MVP має довести core thesis, а не реалізувати всі future features.
6. **No hidden product logic.** Selection, entitlements, status filtering and anti-repeat logic must not be hidden inside one consumer such as Telegram worker.
7. **Evidence-based presentation.** Stanford-ready demo claims must be backed by working artifacts, logs, reports or documented constraints.

### 2.2. Requirement quality rule

Кожна requirement statement має бути:

```text
specific
bounded
testable
traceable
owned
versionable
implementable
aligned with Constitution
```

---

## 3. Product Scope Covered by This SRS

### 3.1. In scope

This SRS covers:

```text
source registry
future source onboarding
file inventory
import manifest
parser assignment
import pipeline
canonical quiz item data
taxonomy and CEFR metadata
status lifecycle
production database requirements
selection engine requirements
versioned API requirements
consumer management
Telegram delivery worker
admin workflow
billing and entitlements
analytics and reporting
security and privacy baseline
operations and observability
CI/CD and repository governance
launch gates
Stanford-ready demo requirements
```

### 3.2. Out of scope for MVP

The following are out of scope for first MVP unless explicitly promoted by change control:

- full adaptive learning engine;
- Item Response Theory / Computerized Adaptive Testing;
- AI-generated production questions;
- public marketplace for third-party quiz submissions;
- native mobile apps;
- full LMS replacement;
- full teacher/school CRM;
- complex gamification;
- uncontrolled public contribution;
- direct raw CSV access by consumers;
- publication of draft items;
- billing provider lock-in before internal entitlement model exists.

### 3.3. Content audit boundary

The system SHALL NOT treat this SRS as a mandate to re-audit every existing quiz answer. The first implementation focus is operational readiness:

```text
inventory
source traceability
canonical schema
status workflow
API delivery
selection controls
analytics
billing/security/operations
```

Technical validation is in scope. Re-checking the linguistic correctness of every verified item is not part of Sprint 0/MVP unless a specific item is reported or flagged.

---

## 4. System Overview

### 4.1. System formula

```text
Verified German quiz content
  → governed sources
  → canonical quiz items
  → production database
  → selection engine
  → versioned API
  → consumers
  → delivery / attempts / analytics / billing / operations
```

### 4.2. High-level modules

| Module | Description | MVP role |
|---|---|---|
| Source Registry | Records all existing and candidate source files | Required |
| Import Manifest | Describes source files, parser profiles and defaults | Required |
| Import Pipeline | Parses, normalizes, validates and reports | Required |
| Canonical Data Core | Defines quiz item shape and metadata | Required |
| Taxonomy Core | CEFR, themes, objectives, patterns, tags | Required |
| Production Database | Stores operational source of truth | Required |
| Status Workflow | Controls draft/imported/approved/published/etc. | Required |
| Selection Engine | Chooses eligible quiz items for consumers | Required |
| API Service | Versioned external/internal delivery surface | Required |
| Consumer Management | Manages API, Telegram, web, school consumers | Required |
| Delivery Logging | Records what was delivered to whom and when | Required |
| Attempt Logging | Records answers and outcomes | MVP-light |
| Admin Workflow | Source/item review and operational control | MVP-light / required for scale |
| Telegram Worker | Scheduled quiz delivery to Telegram | Pilot |
| Billing/Entitlements | Feature access, quotas and plan control | MVP-light |
| Analytics | Usage, quality, coverage and operations reports | MVP-light |
| Operations | Monitoring, backup, rollback, incidents | Required before production |

### 4.3. Dependency rule

The system SHALL respect this dependency order:

```text
source governance before import
import before production database use
production database before public API use
API before external consumers
selection engine before Telegram scaling
entitlements before paid access
analytics before scale claims
operations before production launch
```

---

## 5. User Classes and Stakeholders

| Class | Description | Primary needs |
|---|---|---|
| Learner | Individual German learner | Level/topic quiz practice, feedback, no excessive repeats |
| Teacher | German instructor | Packs by level/topic, group insight, quality-controlled content |
| Telegram Channel Owner | Runs educational Telegram channel | Scheduled quiz posting, no-repeat, quality and reliability |
| School / Course Provider | Educational organization | Controlled access, reporting, scalable content delivery |
| API Client Developer | Builds external app or service | Stable API, docs, keys, quotas, machine-readable errors |
| Admin / Content Operator | Maintains content/system | Source onboarding, import, review, status changes, reports |
| Product Owner | Owns roadmap and monetization | Scope control, launch gates, metrics, demo readiness |
| Engineering Owner | Owns implementation | Clear requirements, architecture, tests, operations |
| Security/Ops Owner | Owns trust layer | Auth, authorization, monitoring, backup, incident handling |
| Demo/Review Audience | Stanford-style review stakeholders | Evidence that project is governed, scalable and credible |

---

## 6. Operating Environment

### 6.1. Expected environments

The system SHALL support at least these operational modes:

| Mode | Purpose | Allowed capabilities |
|---|---|---|
| Local development | Build and test locally | Sample data, local DB, CLI imports, tests |
| Internal prototype | Validate import/API assumptions | Internal data subset, no paid users, no public Telegram |
| Closed pilot | Controlled real-world use | Limited consumers, monitored delivery, manual support |
| Public beta | Limited public access | Stable API version, quotas, monitoring, support path |
| Production | Supported product | Auth, billing/entitlements, monitoring, backups, incident plan |
| Stanford demo | Professional demonstration | Reproducible demo, clear artifacts, no misrepresented claims |

### 6.2. Technology constraints

This SRS does not mandate a specific framework, but the implementation SHOULD support:

- versioned HTTP API;
- relational database with indexes and migrations;
- reproducible imports;
- generated reports;
- CI checks;
- OpenAPI documentation;
- JSON Schema validation;
- structured logs;
- deployable services for API and workers.

---

## 7. Assumptions, Constraints and Dependencies

### 7.1. Assumptions

| ID | Assumption |
|---|---|
| ASM-001 | Existing quiz files are already content-verified and do not require full re-audit in MVP. |
| ASM-002 | Current corpus starts with 115 active bank files and 30,974 active rows/items. |
| ASM-003 | Current items may remain `draft` until operational workflow promotes them. |
| ASM-004 | Future quiz files will be added over time and must be onboarded safely. |
| ASM-005 | API Quiz Bank will support multiple consumer types, not only Telegram. |
| ASM-006 | Payment provider may change, so entitlements must be internal and provider-neutral. |
| ASM-007 | Admin UI may begin as CLI/manual workflow in MVP if actions are logged and documented. |
| ASM-008 | Stanford-ready presentation may use a controlled dataset if limitations are clearly stated. |

### 7.2. Constraints

| ID | Constraint |
|---|---|
| CON-001 | Raw source files MUST NOT be used directly by public consumers. |
| CON-002 | Draft items MUST NOT be delivered to normal production consumers. |
| CON-003 | All external consumers MUST use versioned API. |
| CON-004 | All production quiz items MUST preserve source traceability. |
| CON-005 | All paid/limited access MUST use entitlements and quotas, not direct payment status only. |
| CON-006 | Telegram delivery MUST respect Telegram quiz/poll compatibility rules. |
| CON-007 | Security-sensitive data MUST NOT be committed to repository. |
| CON-008 | Production launch MUST NOT happen without backup, monitoring and incident path. |

### 7.3. External dependencies

| Dependency | Expected use |
|---|---|
| CEFR | Level model A1–C2 |
| OpenAPI | API contract documentation |
| JSON Schema | Canonical data validation |
| RFC 9457 Problem Details | Machine-readable API errors |
| OWASP API Security | API security baseline |
| Telegram Bot API | Telegram quiz delivery adapter |
| Git/GitHub or equivalent | Versioning, PRs, CI, branch protection |
| Payment provider | Optional payment collection, not source of entitlement truth |

---

## 8. Requirement Identification System

### 8.1. Requirement ID format

```text
SRS-<AREA>-<NUMBER>
```

Examples:

```text
SRS-SRC-001   Source registry requirement
SRS-IMP-001   Import requirement
SRS-DATA-001  Canonical data requirement
SRS-API-001   API requirement
NFR-SEC-001   Security non-functional requirement
NFR-OPS-001   Operations non-functional requirement
```

### 8.2. Requirement area codes

| Code | Area |
|---|---|
| CORE | Core platform rules |
| SRC | Source registry and inventory |
| ONB | Future source onboarding |
| IMP | Import pipeline |
| DATA | Canonical data model |
| TAX | Taxonomy, CEFR, coverage |
| STAT | Status lifecycle and publication control |
| DB | Database and storage |
| SEL | Selection engine |
| API | Versioned API |
| CONS | Consumer management |
| TG | Telegram delivery |
| ADM | Admin workflow |
| BILL | Billing and entitlements |
| AN | Analytics and reporting |
| DOC | Documentation and generated reports |
| DEMO | Stanford-ready demo |
| SEC | Security and privacy |
| OPS | Operations, monitoring, backup |
| PERF | Performance and scale |
| REL | Reliability and availability |
| ENG | Engineering workflow and maintainability |
| QA | Testing and quality assurance |

### 8.3. Priority levels

| Priority | Meaning |
|---|---|
| P0 | Blocking: required before MVP or before any public delivery if relevant |
| P1 | Required for closed pilot / credible platform operation |
| P2 | Required for public beta / scale readiness |
| P3 | Future enhancement or optimization |

### 8.4. Verification methods

| Method | Meaning |
|---|---|
| T | Automated test |
| I | Inspection / document review |
| D | Demonstration |
| A | Analysis / report / metric |
| O | Operational drill |
| M | Manual review where automation is not yet available |

---

## 9. Master Functional Requirements

### 9.1. Core Platform Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-CORE-001 | The system SHALL operate as an API-first content platform, not as a direct CSV-serving application. | P0 | MVP | I, D |
| SRS-CORE-002 | The system SHALL treat raw files as source assets and the production database as operational source of truth after controlled import. | P0 | MVP | I, D |
| SRS-CORE-003 | The system SHALL prevent public consumers from directly reading raw CSV files. | P0 | MVP | T, I |
| SRS-CORE-004 | The system SHALL support multiple consumer types including API client, Telegram channel, Telegram bot, web app, school account and internal demo client. | P1 | Pilot | T, D |
| SRS-CORE-005 | The system SHALL provide a clear lifecycle from source registration to production delivery. | P0 | MVP | I, D |
| SRS-CORE-006 | The system SHALL preserve traceability from every production quiz item back to source file and import batch. | P0 | MVP | T, A |
| SRS-CORE-007 | The system SHALL separate content validation, status approval, selection, delivery and billing logic into explicit components or modules. | P0 | MVP | I, D |
| SRS-CORE-008 | The system SHALL support generated reports for inventory, import, coverage and operational checks. | P1 | Pilot | D, A |
| SRS-CORE-009 | The system SHALL support controlled future expansion of corpus through onboarding workflow. | P0 | MVP | D, T |
| SRS-CORE-010 | The system SHALL maintain documentation sufficient to reproduce core demo and operational checks. | P1 | Pilot | I, D |

### 9.2. Source Registry and Inventory Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-SRC-001 | The system SHALL maintain an inventory for all active, archived and candidate source files. | P0 | MVP | T, I |
| SRS-SRC-002 | Every source file SHALL have a stable `source_id` before import. | P0 | MVP | T |
| SRS-SRC-003 | Every source file SHALL have filename, original path, format, encoding when known, checksum, source state and registration timestamp. | P0 | MVP | T, I |
| SRS-SRC-004 | Source inventory SHALL distinguish active bank files, service templates, archived files, rejected files and candidate files. | P0 | MVP | T, I |
| SRS-SRC-005 | Source inventory SHALL record approximate or actual item counts for every active source. | P1 | Pilot | A |
| SRS-SRC-006 | Source inventory SHALL support generated output such as `file_inventory.csv` or equivalent structured report. | P0 | MVP | D |
| SRS-SRC-007 | Source registry SHALL preserve historical source records even if a file is retired or replaced. | P1 | Pilot | T |
| SRS-SRC-008 | Source registry SHALL prevent two active source files from sharing the same `source_id`. | P0 | MVP | T |
| SRS-SRC-009 | Source registry SHOULD detect duplicate checksums and flag them for review. | P1 | Pilot | T, A |
| SRS-SRC-010 | Source registry SHALL support the current corpus baseline and future corpus expansion without changing ID strategy. | P0 | MVP | I, T |

### 9.3. Future Source Onboarding Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-ONB-001 | The system SHALL provide a defined workflow for registering a new quiz file before it can be imported. | P0 | MVP | D, I |
| SRS-ONB-002 | A new source file SHALL start in `candidate` or equivalent non-production source state. | P0 | MVP | T |
| SRS-ONB-003 | A new source file SHALL receive stable `source_id` and checksum before parser assignment. | P0 | MVP | T |
| SRS-ONB-004 | A new source file SHALL be added to import manifest before dry-run import. | P0 | MVP | T, I |
| SRS-ONB-005 | The system SHALL support source states: `candidate`, `registered`, `parser_pending`, `parser_assigned`, `dry_run_failed`, `dry_run_passed`, `imported`, `active`, `archived`, `rejected`, `blocked`. | P1 | Pilot | T, I |
| SRS-ONB-006 | The system SHALL block production delivery of items from a new source until import, validation and status workflow have completed. | P0 | MVP | T |
| SRS-ONB-007 | The system SHALL generate onboarding report for each new source. | P1 | Pilot | D, A |
| SRS-ONB-008 | The onboarding workflow SHALL record parser used, defaults applied, validation failures, duplicate candidates and accepted item count. | P1 | Pilot | A |
| SRS-ONB-009 | The system SHALL support rejection of a candidate source with reason code and audit trail. | P1 | Pilot | T, I |
| SRS-ONB-010 | The system SHALL demonstrate onboarding of at least one sample future source before MVP acceptance. | P0 | MVP | D |

### 9.4. Import Manifest and Parser Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-IMP-001 | The system SHALL maintain an import manifest mapping source files to parser profiles, defaults and source states. | P0 | MVP | I, T |
| SRS-IMP-002 | Import manifest SHALL be version-controlled. | P0 | MVP | I |
| SRS-IMP-003 | Import manifest SHALL reference source files by stable `source_id`, not only by filename. | P0 | MVP | T |
| SRS-IMP-004 | Import manifest SHALL support default CEFR level, theme, objective and pattern when appropriate. | P1 | Pilot | T |
| SRS-IMP-005 | Import pipeline SHALL support dry-run mode that does not write production items. | P0 | MVP | D, T |
| SRS-IMP-006 | Import pipeline SHALL produce structured import report for every run. | P0 | MVP | D, A |
| SRS-IMP-007 | Import report SHALL include accepted rows, skipped rows, validation errors, duplicate candidates, parser warnings and source traceability summary. | P0 | MVP | A |
| SRS-IMP-008 | Import pipeline SHALL preserve original source row or equivalent locator when available. | P0 | MVP | T |
| SRS-IMP-009 | Import pipeline SHALL generate or preserve content hash for every normalized item. | P0 | MVP | T |
| SRS-IMP-010 | Import pipeline SHALL fail or quarantine rows that do not meet minimum canonical requirements. | P0 | MVP | T |
| SRS-IMP-011 | Import pipeline SHOULD support parser profiles for multiple CSV structures. | P1 | Pilot | D, T |
| SRS-IMP-012 | Import pipeline SHALL not silently coerce unknown levels, themes, objectives or patterns into valid values. | P0 | MVP | T |
| SRS-IMP-013 | Import pipeline SHALL classify row problems using machine-readable error categories. | P1 | Pilot | T, A |
| SRS-IMP-014 | Import pipeline SHALL be reproducible for same source content and same manifest configuration. | P1 | Pilot | T, A |
| SRS-IMP-015 | Import pipeline SHOULD support sample normalized JSONL output for inspection and demo. | P1 | Pilot | D |

### 9.5. Canonical Data Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-DATA-001 | Every production quiz item SHALL conform to canonical quiz item schema. | P0 | MVP | T |
| SRS-DATA-002 | Every quiz item SHALL have stable internal ID after database import. | P0 | MVP | T |
| SRS-DATA-003 | Every publishable quiz item SHALL have a public-safe item identifier or API identifier. | P1 | Pilot | T |
| SRS-DATA-004 | Every quiz item SHALL include German question/stem text. | P0 | MVP | T |
| SRS-DATA-005 | Every quiz item SHALL include at least 2 answer options and at most the configured delivery-compatible maximum for target consumer. | P0 | MVP | T |
| SRS-DATA-006 | Every quiz item SHALL identify at least one correct answer option. | P0 | MVP | T |
| SRS-DATA-007 | Every quiz item SHALL include status. | P0 | MVP | T |
| SRS-DATA-008 | Every approved or published quiz item SHALL include CEFR level. | P0 | MVP | T |
| SRS-DATA-009 | Every approved or published quiz item SHALL include primary theme. | P0 | MVP | T |
| SRS-DATA-010 | Every approved or published quiz item SHALL include objective and pattern metadata when required by taxonomy policy. | P1 | Pilot | T, A |
| SRS-DATA-011 | Every quiz item SHALL preserve `source_id` and source locator when available. | P0 | MVP | T |
| SRS-DATA-012 | Every quiz item SHALL include `content_hash` for dedupe/versioning. | P0 | MVP | T |
| SRS-DATA-013 | Canonical schema SHALL support optional explanations in German and Ukrainian where available. | P1 | Pilot | T |
| SRS-DATA-014 | Canonical schema SHALL support tags as a list, not as a single folder-only classification. | P1 | Pilot | T |
| SRS-DATA-015 | Canonical schema SHALL support metadata for item type, language mode and consumer compatibility flags. | P1 | Pilot | T |
| SRS-DATA-016 | Canonical schema SHALL support source and import batch metadata. | P0 | MVP | T |
| SRS-DATA-017 | Canonical schema SHALL reject impossible or ambiguous correct-answer references. | P0 | MVP | T |
| SRS-DATA-018 | Canonical schema SHALL support future extension without breaking existing valid items. | P1 | Pilot | I, T |

### 9.6. Taxonomy, CEFR and Coverage Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-TAX-001 | The system SHALL represent CEFR levels `A1`, `A2`, `B1`, `B2`, `C1`, `C2` as canonical level values. | P0 | MVP | T |
| SRS-TAX-002 | The system SHALL represent 18 canonical themes for the current corpus. | P0 | MVP | T, I |
| SRS-TAX-003 | The system SHALL support objective IDs and pattern IDs as part of coverage model. | P0 | MVP | T |
| SRS-TAX-004 | The system SHALL define coverage matrix as `level × theme_id × objective_id × pattern_id`. | P0 | MVP | I, A |
| SRS-TAX-005 | The system SHALL generate coverage report for corpus state. | P1 | Pilot | A |
| SRS-TAX-006 | The system SHALL distinguish canonical CEFR level from compatibility field names such as `sublevel`. | P0 | MVP | I, T |
| SRS-TAX-007 | The system SHALL not allow unrecognized CEFR levels in approved/published items. | P0 | MVP | T |
| SRS-TAX-008 | The system SHALL allow future taxonomy expansion through change control. | P1 | Pilot | I |
| SRS-TAX-009 | The system SHOULD support multiple tags per item. | P1 | Pilot | T |
| SRS-TAX-010 | The system SHOULD track taxonomy confidence or review requirement for auto-classified items. | P2 | Beta | T, A |

### 9.7. Status Lifecycle and Publication Control Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-STAT-001 | Every quiz item SHALL have exactly one operational status. | P0 | MVP | T |
| SRS-STAT-002 | The system SHALL support statuses: `draft`, `imported`, `normalized`, `needs_review`, `approved`, `published`, `monitored`, `retired`, `blocked`. | P0 | MVP | T, I |
| SRS-STAT-003 | The system SHALL treat `draft` as not production-released, not as proof of incorrectness. | P0 | MVP | I |
| SRS-STAT-004 | The system SHALL prevent delivery of `draft`, `imported`, `normalized`, `needs_review`, `retired` or `blocked` items to normal consumers. | P0 | MVP | T |
| SRS-STAT-005 | The system SHALL allow delivery only for `approved` or `published` items unless explicit internal demo override is used. | P0 | MVP | T |
| SRS-STAT-006 | Status changes SHALL be logged with actor, timestamp, previous status, new status and reason when available. | P0 | MVP | T, I |
| SRS-STAT-007 | The system SHALL support retiring problematic items without deleting historical delivery and attempt records. | P1 | Pilot | T |
| SRS-STAT-008 | The system SHALL support blocking items from all delivery. | P0 | MVP | T |
| SRS-STAT-009 | The system SHALL expose item status to admin and operational reports. | P1 | Pilot | D |
| SRS-STAT-010 | The system SHOULD support batch status changes with audit trail. | P1 | Pilot | D, T |

### 9.8. Database and Storage Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-DB-001 | The system SHALL store source files metadata, import batches, quiz items, options, taxonomy, consumers, rules, deliveries and attempts in durable storage. | P0 | MVP | T, I |
| SRS-DB-002 | The database SHALL enforce referential integrity for quiz items and options. | P0 | MVP | T |
| SRS-DB-003 | The database SHALL support migrations under version control. | P0 | MVP | I, T |
| SRS-DB-004 | The database SHALL index common selection fields including status, level, theme and consumer delivery history. | P1 | Pilot | A, I |
| SRS-DB-005 | The database SHALL preserve delivery history even if item is retired. | P1 | Pilot | T |
| SRS-DB-006 | The database SHALL prevent duplicate active content hashes unless explicitly allowed through versioning policy. | P1 | Pilot | T |
| SRS-DB-007 | The database SHALL support audit log records for admin and critical system actions. | P0 | MVP | T |
| SRS-DB-008 | The database SHOULD support structured metadata fields for extensibility. | P1 | Pilot | I, T |
| SRS-DB-009 | The database SHALL support backup and restore procedures before production launch. | P0 | Production | O |
| SRS-DB-010 | The database schema SHALL be documented in `04_domain_model.md` and/or database migrations. | P1 | Pilot | I |

### 9.9. Selection Engine Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-SEL-001 | The system SHALL use centralized selection engine for quiz item selection. | P0 | MVP | I, D |
| SRS-SEL-002 | Selection engine SHALL filter by publishable status before returning candidates. | P0 | MVP | T |
| SRS-SEL-003 | Selection engine SHALL respect consumer rules for allowed levels. | P0 | MVP | T |
| SRS-SEL-004 | Selection engine SHALL respect consumer rules for allowed themes. | P0 | MVP | T |
| SRS-SEL-005 | Selection engine SHALL enforce repeat policy based on delivery history. | P0 | MVP | T, D |
| SRS-SEL-006 | Selection engine SHALL exclude blocked items. | P0 | MVP | T |
| SRS-SEL-007 | Selection engine SHALL support quota/entitlement decision before or during selection. | P0 | MVP | T |
| SRS-SEL-008 | Selection engine SHALL write or enable writing a delivery record when item is delivered. | P0 | MVP | T |
| SRS-SEL-009 | Selection engine SHOULD support weighted selection by freshness, coverage balance and quality score. | P2 | Beta | A, T |
| SRS-SEL-010 | Selection engine SHOULD support deterministic mode for demo and tests. | P1 | Pilot | T, D |
| SRS-SEL-011 | Selection engine SHALL handle no-eligible-item state with machine-readable reason. | P0 | MVP | T |
| SRS-SEL-012 | Selection engine SHALL not be implemented only inside Telegram worker. | P0 | MVP | I |
| SRS-SEL-013 | Selection engine SHOULD support objective/pattern balancing when enough items exist. | P2 | Beta | A |
| SRS-SEL-014 | Selection engine SHALL log selection decision metadata sufficient for debugging. | P1 | Pilot | A, I |

### 9.10. API Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-API-001 | All external consumers SHALL access quiz content through versioned API. | P0 | MVP | D, I |
| SRS-API-002 | API SHALL expose versioned routes under `/v1` for MVP. | P0 | MVP | T |
| SRS-API-003 | API SHALL provide health or readiness endpoint for operations. | P1 | Pilot | T |
| SRS-API-004 | API SHALL provide endpoint to list available topics/themes. | P1 | Pilot | T |
| SRS-API-005 | API SHALL provide endpoint to request next eligible quiz item. | P0 | MVP | T, D |
| SRS-API-006 | API SHALL provide endpoint to submit or record attempt when applicable. | P1 | Pilot | T |
| SRS-API-007 | API SHALL not return draft or blocked items to normal consumers. | P0 | MVP | T |
| SRS-API-008 | API SHALL enforce authentication for non-public endpoints. | P0 | MVP | T |
| SRS-API-009 | API SHALL enforce object-level authorization for consumer-specific data. | P0 | MVP | T |
| SRS-API-010 | API SHALL enforce entitlement and quota checks for protected delivery. | P0 | MVP | T, D |
| SRS-API-011 | API errors SHALL be machine-readable using a standard problem details format or documented equivalent. | P0 | MVP | T, I |
| SRS-API-012 | API SHALL have an OpenAPI specification before external consumer access. | P0 | MVP | I |
| SRS-API-013 | API SHALL document authentication, request schemas, response schemas, error models and status codes. | P0 | MVP | I |
| SRS-API-014 | API SHOULD support idempotency or duplicate prevention for attempt submissions where needed. | P2 | Beta | T |
| SRS-API-015 | API SHALL support rate limiting or usage controls before public beta. | P1 | Pilot/Beta | T, A |
| SRS-API-016 | API SHALL not expose internal source file paths to normal consumers. | P0 | MVP | T |
| SRS-API-017 | API SHALL expose only public-safe item metadata to learner-facing consumers. | P0 | MVP | T, I |
| SRS-API-018 | API SHOULD support admin endpoints for imports/reviews only under admin authorization. | P1 | Pilot | T |

### 9.11. Consumer Management Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-CONS-001 | The system SHALL represent consumers as first-class entities. | P0 | MVP | T |
| SRS-CONS-002 | The system SHALL support consumer types including `telegram_channel`, `telegram_bot`, `web_app`, `school_account`, `external_api_client`, `internal_demo_client`. | P1 | Pilot | T |
| SRS-CONS-003 | Every consumer SHALL have lifecycle status. | P0 | MVP | T |
| SRS-CONS-004 | Every active consumer SHALL have delivery rules or inherit safe defaults. | P0 | MVP | T |
| SRS-CONS-005 | Consumer rules SHALL include allowed levels, themes, limits and repeat policy where applicable. | P0 | MVP | T |
| SRS-CONS-006 | The system SHALL support suspending or blocking a consumer. | P1 | Pilot | T |
| SRS-CONS-007 | Consumer-specific analytics SHALL be isolated by authorization. | P1 | Pilot | T |
| SRS-CONS-008 | Consumer configuration changes SHALL be logged. | P1 | Pilot | I, T |
| SRS-CONS-009 | Consumer setup SHOULD support owner/buyer distinction from learner/user identity. | P2 | Beta | I |
| SRS-CONS-010 | Internal demo consumer SHALL be clearly marked and not confused with production consumers. | P1 | Pilot | I, D |

### 9.12. Telegram Delivery Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-TG-001 | Telegram worker SHALL obtain quiz items through API/selection engine, not by reading raw CSV. | P0 | MVP/Pilot | T, I |
| SRS-TG-002 | Telegram worker SHALL deliver only approved/published items. | P0 | MVP/Pilot | T |
| SRS-TG-003 | Telegram worker SHALL validate Telegram poll/quiz compatibility before sending. | P0 | Pilot | T |
| SRS-TG-004 | Telegram worker SHALL record delivery status and Telegram message identifier when available. | P0 | Pilot | T |
| SRS-TG-005 | Telegram worker SHALL respect channel schedule and posting window. | P1 | Pilot | D, T |
| SRS-TG-006 | Telegram worker SHALL respect repeat policy for each channel. | P0 | Pilot | T, D |
| SRS-TG-007 | Telegram worker SHALL handle send failures and record failure reasons. | P1 | Pilot | T, A |
| SRS-TG-008 | Telegram worker SHALL not expose correct answer before Telegram quiz mechanics require it. | P1 | Pilot | D, T |
| SRS-TG-009 | Telegram worker SHOULD support dry-run/simulated delivery mode. | P1 | Pilot | D |
| SRS-TG-010 | Telegram delivery SHALL have operational gate before real channel posting. | P0 | Pilot | I |
| SRS-TG-011 | Telegram worker SHOULD support multiple channels after single-channel pilot proves repeat and logging. | P2 | Beta | D, A |
| SRS-TG-012 | Telegram worker SHALL not bypass entitlement or consumer status checks. | P0 | Pilot | T |

### 9.13. Admin Workflow Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-ADM-001 | The system SHALL provide admin or operational workflow for source registration. | P0 | MVP | D |
| SRS-ADM-002 | The system SHALL provide admin or operational workflow for dry-run import review. | P0 | MVP | D |
| SRS-ADM-003 | The system SHALL provide admin or operational workflow for item status changes. | P0 | MVP | D, T |
| SRS-ADM-004 | The system SHALL provide ability to approve, publish, retire and block items. | P0 | MVP | D, T |
| SRS-ADM-005 | Admin actions SHALL be authenticated and authorized. | P0 | MVP | T |
| SRS-ADM-006 | Admin actions SHALL be logged. | P0 | MVP | T, I |
| SRS-ADM-007 | Admin workflow SHALL expose item source traceability. | P1 | Pilot | D |
| SRS-ADM-008 | Admin workflow SHOULD expose validation errors and conflict categories. | P1 | Pilot | D |
| SRS-ADM-009 | Admin workflow SHOULD support filtering by status, level, theme, source and validation flag. | P1 | Pilot | D |
| SRS-ADM-010 | Admin workflow MAY be CLI-based in MVP if it is documented, reproducible and logged. | P0 | MVP | I, D |
| SRS-ADM-011 | Admin UI SHOULD be introduced before scaling manual review volume. | P2 | Beta | D |
| SRS-ADM-012 | Admin workflow SHALL support emergency blocking of problematic item or source. | P1 | Pilot | D, T |

### 9.14. Billing and Entitlements Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-BILL-001 | The system SHALL model access using internal entitlements. | P0 | MVP | T, I |
| SRS-BILL-002 | Payment provider status SHALL NOT be the sole source of access truth. | P0 | MVP | I, T |
| SRS-BILL-003 | The system SHALL support quotas for API or consumer delivery. | P0 | MVP | T, D |
| SRS-BILL-004 | The system SHALL deny delivery when required entitlement is missing or quota is exceeded. | P0 | MVP | T, D |
| SRS-BILL-005 | Entitlements SHALL support feature, value/limit, consumer/account scope and validity period. | P1 | Pilot | T |
| SRS-BILL-006 | Billing model SHALL support manual override for MVP/closed pilot with audit trail. | P1 | Pilot | T, I |
| SRS-BILL-007 | Billing integration SHALL be provider-neutral at internal model level. | P1 | Pilot | I |
| SRS-BILL-008 | Payment webhooks, when implemented, SHALL update internal entitlement records rather than bypassing them. | P1 | Beta | T |
| SRS-BILL-009 | The system SHALL log quota usage events sufficient for billing dispute analysis. | P2 | Beta | A |
| SRS-BILL-010 | The system SHOULD support plan definitions for Free, Student, Teacher, Channel, School and API Pro or equivalent tiers. | P2 | Beta | I |

### 9.15. Analytics and Reporting Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-AN-001 | The system SHALL record delivery events for delivered quiz items. | P0 | MVP | T |
| SRS-AN-002 | Delivery event SHALL include consumer, item, channel/type, timestamp and outcome status. | P0 | MVP | T |
| SRS-AN-003 | The system SHALL support attempt recording when consumer context allows it. | P1 | Pilot | T |
| SRS-AN-004 | Attempt event SHOULD include selected option, correctness and response timestamp when available. | P1 | Pilot | T |
| SRS-AN-005 | The system SHALL generate basic corpus report by status, level and theme. | P0 | MVP | A |
| SRS-AN-006 | The system SHALL generate delivery report for MVP demo or pilot. | P1 | Pilot | A, D |
| SRS-AN-007 | The system SHOULD report repeat-policy violations or attempted violations. | P1 | Pilot | A |
| SRS-AN-008 | The system SHOULD track item issue reports. | P2 | Beta | D, T |
| SRS-AN-009 | The system SHOULD support correctness rate analytics after enough attempts are collected. | P2 | Beta | A |
| SRS-AN-010 | Analytics SHALL not expose private user or consumer data without authorization. | P0 | MVP | T |
| SRS-AN-011 | Basic analytics SHALL be available for Stanford-style demo evidence. | P1 | Pilot | D, A |

### 9.16. Documentation and Generated Report Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-DOC-001 | Repository SHALL contain `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md` and this SRS before serious implementation. | P0 | MVP | I |
| SRS-DOC-002 | Repository SHOULD contain use cases, domain model, architecture, data standard, API standard, security model and operations plan before production. | P1 | Pilot/Prod | I |
| SRS-DOC-003 | README SHOULD be generated or clearly marked if manually maintained. | P1 | Pilot | I |
| SRS-DOC-004 | Inventory and coverage reports SHALL be reproducible by tooling. | P1 | Pilot | D |
| SRS-DOC-005 | SRS requirement changes SHALL be versioned and documented. | P0 | MVP | I |
| SRS-DOC-006 | OpenAPI contract SHALL be available before external API access. | P0 | MVP | I |
| SRS-DOC-007 | Data standard SHALL document canonical quiz item fields and validation rules. | P1 | Pilot | I |
| SRS-DOC-008 | Operations documentation SHALL include backup, restore and incident handling before production launch. | P0 | Production | I, O |

### 9.17. Stanford-Ready Demo Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| SRS-DEMO-001 | Stanford-style demo SHALL show governed corpus, not just static files. | P0 | Demo | D |
| SRS-DEMO-002 | Demo SHALL show source inventory and/or manifest. | P0 | Demo | D |
| SRS-DEMO-003 | Demo SHALL show canonical item or schema validation. | P0 | Demo | D |
| SRS-DEMO-004 | Demo SHALL show API returning next eligible quiz item. | P0 | Demo | D |
| SRS-DEMO-005 | Demo SHALL show that draft items are not delivered to normal consumers. | P0 | Demo | D, T |
| SRS-DEMO-006 | Demo SHALL show delivery logging. | P0 | Demo | D |
| SRS-DEMO-007 | Demo SHALL show repeat-policy behavior. | P1 | Demo | D |
| SRS-DEMO-008 | Demo SHALL show entitlement/quota denial or simulated denial. | P1 | Demo | D |
| SRS-DEMO-009 | Demo SHALL show source onboarding for a new sample file or explain planned controlled path with artifact. | P0 | Demo | D, I |
| SRS-DEMO-010 | Demo SHALL include architecture/data-flow diagram or equivalent visual artifact. | P1 | Demo | I |
| SRS-DEMO-011 | Demo SHALL not claim features that are only planned without marking them as planned. | P0 | Demo | I |
| SRS-DEMO-012 | Demo SHALL include known risks and next engineering milestones. | P1 | Demo | I |

---

## 10. Non-Functional Requirements

### 10.1. Security and Privacy Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| NFR-SEC-001 | API keys and secrets SHALL NOT be stored in plaintext in repository. | P0 | MVP | I, T |
| NFR-SEC-002 | Stored API keys SHALL be hashed or otherwise protected according to implementation standard. | P0 | Pilot | I, T |
| NFR-SEC-003 | Admin endpoints/actions SHALL require authentication. | P0 | MVP | T |
| NFR-SEC-004 | Admin endpoints/actions SHALL enforce authorization by role/permission. | P0 | MVP | T |
| NFR-SEC-005 | Consumer data SHALL be protected by object-level authorization. | P0 | MVP | T |
| NFR-SEC-006 | The system SHALL validate input for API and import operations. | P0 | MVP | T |
| NFR-SEC-007 | The system SHALL log security-relevant admin and access events. | P0 | MVP | T, I |
| NFR-SEC-008 | Sensitive operational logs SHALL avoid leaking secrets, tokens or private personal data. | P0 | MVP | I, T |
| NFR-SEC-009 | Public API SHALL implement rate limiting or abuse protection before public beta. | P1 | Beta | T, A |
| NFR-SEC-010 | The system SHALL support revocation or disabling of API access for a consumer. | P1 | Pilot | T |
| NFR-SEC-011 | The system SHALL minimize personal data collection in MVP. | P0 | MVP | I |
| NFR-SEC-012 | Privacy/legal review SHALL be completed before broad public or school deployment. | P1 | Production | I |
| NFR-SEC-013 | Security baseline SHALL be documented in `08_security_threat_model.md` before production launch. | P1 | Production | I |
| NFR-SEC-014 | The system SHALL not expose correct answer data to clients when inappropriate for quiz interaction mode. | P1 | Pilot | T |
| NFR-SEC-015 | The system SHALL protect payment-provider webhook endpoints when implemented. | P1 | Beta | T |

### 10.2. Operations Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| NFR-OPS-001 | Production deployment SHALL have documented backup procedure. | P0 | Production | I |
| NFR-OPS-002 | Production deployment SHALL have tested restore procedure. | P0 | Production | O |
| NFR-OPS-003 | System SHALL provide structured logs for API, import pipeline and delivery workers. | P1 | Pilot | I, A |
| NFR-OPS-004 | System SHALL provide health/readiness checks for service monitoring. | P1 | Pilot | T |
| NFR-OPS-005 | System SHALL record import failures and delivery failures with reason codes. | P0 | MVP/Pilot | A |
| NFR-OPS-006 | Production deployment SHALL have monitoring and alerting for API and worker failures. | P1 | Production | D, I |
| NFR-OPS-007 | Production deployment SHALL have rollback path for code and schema migrations. | P1 | Production | I, O |
| NFR-OPS-008 | Incident response playbook SHALL exist before public production launch. | P1 | Production | I |
| NFR-OPS-009 | System SHALL support maintenance mode or controlled suspension of consumers when needed. | P2 | Beta | D |
| NFR-OPS-010 | Operational dashboards or reports SHALL show import status, delivery failures and quota usage before scale. | P2 | Beta | D |

### 10.3. Performance and Scalability Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| NFR-PERF-001 | System SHALL support the current corpus size without manual file-by-file delivery logic. | P0 | MVP | D, A |
| NFR-PERF-002 | Selection queries SHALL use indexed fields or equivalent optimization for status, level, theme and repeat filtering. | P1 | Pilot | A, I |
| NFR-PERF-003 | API `/v1/quiz-items/next` SHOULD respond within a documented target under expected MVP load. | P1 | Pilot | A |
| NFR-PERF-004 | Import pipeline SHOULD process current corpus in reproducible batches with reports. | P1 | Pilot | A |
| NFR-PERF-005 | System architecture SHOULD allow corpus expansion beyond current 30,974 items without schema redesign. | P1 | Pilot | I, A |
| NFR-PERF-006 | System SHOULD support adding consumers without creating separate selection logic per consumer. | P1 | Pilot | I, D |
| NFR-PERF-007 | Public API SHOULD define rate limits or usage tiers. | P1 | Beta | I, T |
| NFR-PERF-008 | Performance benchmarks SHOULD be recorded before production scale claims. | P2 | Beta | A |

### 10.4. Reliability and Availability Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| NFR-REL-001 | Delivery worker SHALL record failure status instead of silently dropping failed deliveries. | P0 | Pilot | T, A |
| NFR-REL-002 | Import pipeline SHALL not corrupt existing production data on failed import. | P0 | MVP | T |
| NFR-REL-003 | Import batches SHOULD be reversible or quarantined before production activation. | P1 | Pilot | D, I |
| NFR-REL-004 | API SHALL return meaningful error when no eligible item exists. | P0 | MVP | T |
| NFR-REL-005 | System SHALL preserve historical delivery records across item retirement. | P1 | Pilot | T |
| NFR-REL-006 | Scheduled delivery SHOULD be idempotent or protected against duplicate send when worker retries. | P1 | Pilot | T |
| NFR-REL-007 | System SHALL support disabling a failing consumer without disabling the whole platform. | P1 | Pilot | D |
| NFR-REL-008 | Production system SHALL define target availability and support expectations before launch. | P1 | Production | I |

### 10.5. Maintainability and Engineering Workflow Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| NFR-ENG-001 | Repository SHALL maintain clear directory structure for docs, data, services, libs, database, infra and tests. | P0 | MVP | I |
| NFR-ENG-002 | Main branch SHOULD be protected by required checks before production work. | P1 | Pilot | I |
| NFR-ENG-003 | CI SHALL run tests relevant to changed components before merge. | P1 | Pilot | D, I |
| NFR-ENG-004 | Data validation checks SHALL be available in CI or documented local workflow. | P0 | MVP | D |
| NFR-ENG-005 | Schema changes SHALL include migration or documented migration plan. | P0 | MVP | I |
| NFR-ENG-006 | API changes SHALL update OpenAPI contract. | P0 | MVP | I |
| NFR-ENG-007 | Requirement-impacting changes SHALL update SRS or record why no SRS update is needed. | P1 | Pilot | I |
| NFR-ENG-008 | Code SHOULD separate domain logic from delivery adapters. | P1 | Pilot | I |
| NFR-ENG-009 | Selection logic SHALL be tested independently from Telegram worker. | P0 | MVP/Pilot | T |
| NFR-ENG-010 | Repository SHOULD include changelog for production-relevant changes. | P1 | Pilot | I |

### 10.6. Quality Assurance Requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| NFR-QA-001 | Every P0 requirement SHALL have at least one acceptance method before MVP acceptance. | P0 | MVP | I |
| NFR-QA-002 | Data validation tests SHALL cover required fields, status rules, CEFR values, option counts and correct-answer references. | P0 | MVP | T |
| NFR-QA-003 | API tests SHALL cover auth, status filtering, next-item selection, quota denial and error format. | P0 | MVP | T |
| NFR-QA-004 | Import tests SHALL cover dry-run, invalid row handling and source traceability. | P0 | MVP | T |
| NFR-QA-005 | Selection tests SHALL cover anti-repeat, status filtering and consumer rule filtering. | P0 | MVP | T |
| NFR-QA-006 | Telegram pilot tests SHALL cover adapter compatibility and delivery logging. | P1 | Pilot | T, D |
| NFR-QA-007 | Security tests SHALL cover object-level authorization for consumer-specific resources. | P0 | MVP | T |
| NFR-QA-008 | Demo rehearsal SHALL be executed before Stanford-style presentation. | P1 | Demo | D |
| NFR-QA-009 | Known limitations SHALL be documented in release/demo notes. | P1 | Pilot/Demo | I |
| NFR-QA-010 | Test failures SHALL block production launch for affected scope. | P0 | Production | I |

---

## 11. External Interface Requirements

### 11.1. API interface

MVP API SHOULD include at minimum:

```text
GET  /v1/health
GET  /v1/topics
GET  /v1/quiz-items/next
POST /v1/attempts
GET  /v1/consumers/{consumer_id}/rules
```

Admin/API endpoints MAY include in MVP or Pilot:

```text
POST /v1/admin/imports/dry-run
POST /v1/admin/imports
GET  /v1/admin/imports/{import_batch_id}
GET  /v1/admin/reviews
POST /v1/admin/quiz-items/{id}/status
GET  /v1/analytics/corpus
GET  /v1/analytics/deliveries
```

API interface requirements:

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| IF-API-001 | API SHALL use JSON request/response bodies for MVP except documented file/report endpoints. | P0 | T, I |
| IF-API-002 | API SHALL document schemas in OpenAPI. | P0 | I |
| IF-API-003 | API SHALL return stable machine-readable errors. | P0 | T |
| IF-API-004 | API SHALL not require clients to know raw file names to request quiz items. | P0 | T |
| IF-API-005 | API SHOULD support pagination for list endpoints. | P1 | T |
| IF-API-006 | API SHALL distinguish public learner-safe data from admin-only data. | P0 | T |

### 11.2. Telegram interface

Telegram delivery interface requirements:

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| IF-TG-001 | Telegram adapter SHALL convert canonical quiz item into Telegram-compatible quiz/poll payload. | P0 | T |
| IF-TG-002 | Telegram adapter SHALL validate question length, options count and correct answer representation according to configured Telegram constraints. | P0 | T |
| IF-TG-003 | Telegram adapter SHALL record send result. | P0 | T |
| IF-TG-004 | Telegram adapter SHALL support dry-run output for demo and testing. | P1 | D |
| IF-TG-005 | Telegram adapter SHALL not own core selection logic. | P0 | I |

### 11.3. Admin interface

Admin interface may be UI, CLI or both in MVP. Requirements:

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| IF-ADM-001 | Admin interface SHALL support source registration or equivalent operational command. | P0 | D |
| IF-ADM-002 | Admin interface SHALL support dry-run import execution or review. | P0 | D |
| IF-ADM-003 | Admin interface SHALL support status change with audit trail. | P0 | D, T |
| IF-ADM-004 | Admin interface SHOULD show validation errors and source traceability. | P1 | D |
| IF-ADM-005 | Admin interface SHALL require admin authorization. | P0 | T |

### 11.4. Generated report interface

Generated reports SHOULD be stored or exportable as:

```text
Markdown
CSV
JSON
YAML
```

At minimum, reports SHOULD include:

```text
file inventory
import report
coverage report
status breakdown
delivery report
SRS requirement verification summary
```

---

## 12. Data Requirements Summary

Detailed schema will be defined in `06_data_standard.md`, but SRS requires these entity groups:

| Entity group | Minimum required purpose |
|---|---|
| `source_files` | Track all raw/candidate source files |
| `import_batches` | Track import/dry-run runs and outcomes |
| `quiz_items` | Store canonical quiz item records |
| `quiz_options` | Store answer options and correctness |
| `taxonomy_*` | Store levels, themes, objectives, patterns, tags |
| `consumers` | Store delivery/API consumers |
| `consumer_rules` | Store levels/themes/schedules/repeat policy |
| `deliveries` | Store what was delivered, where and when |
| `attempts` | Store user/consumer answer events when available |
| `plans` | Store access plan definitions |
| `entitlements` | Store feature/quota rights |
| `usage_events` | Store billable or quota-relevant usage |
| `audit_log` | Store admin/security-relevant actions |
| `issue_reports` | Store reported content/technical issues |

Minimum quiz item fields for publishable items:

```text
id
public_id or api_id
stem_de
options[]
correct_option_ids[]
cefr_level
theme_id
objective_id
pattern_id
status
source_id
source_locator or source_line when available
content_hash
created_at
updated_at
approved_at or published_at when applicable
```

---

## 13. Launch Gates as Requirements

### 13.1. Document Gate

| Gate requirement | Acceptance |
|---|---|
| `CONSTITUTION.md` exists | Document present and accepted |
| `00_vision.md` exists | Document present and aligned |
| `01_product_charter.md` exists | Document present and aligned |
| `02_requirements_srs.md` exists | This document present and versioned |
| Next docs planned | Use cases, domain model, architecture, data/API standards listed |

### 13.2. Data Gate

Before import at scale:

```text
inventory exists
manifest exists
source_id convention exists
checksum policy exists
taxonomy exists
canonical schema exists
```

### 13.3. Import Gate

Before database publication:

```text
parser profile exists
dry-run report exists
validation report exists
duplicates/conflicts classified
source traceability preserved
import batch reproducible
```

### 13.4. API Gate

Before external API consumer access:

```text
OpenAPI spec exists
/v1 versioning exists
auth model exists
Problem Details or documented error model exists
status filtering works
entitlement/quota checks work
rate limits or usage controls exist
```

### 13.5. Telegram Gate

Before real channel posting:

```text
Telegram adapter uses API/selection engine
only approved/published items used
Telegram compatibility validation exists
delivery log exists
repeat policy exists
failure handling exists
posting schedule controlled
```

### 13.6. Production Gate

Before production claim:

```text
backup exists
restore tested
monitoring exists
incident playbook exists
security baseline implemented
admin actions logged
CI/checks defined
known limitations documented
```

---

## 14. MVP Acceptance Criteria

MVP is accepted only when all applicable P0 MVP requirements pass verification and these acceptance criteria are met:

```text
AC-MVP-001: Existing corpus has inventory/manifest workflow.
AC-MVP-002: A new sample source can be onboarded through defined process.
AC-MVP-003: Canonical quiz item schema exists.
AC-MVP-004: Import pipeline preserves source traceability.
AC-MVP-005: Database stores quiz items, options, sources, consumers and deliveries.
AC-MVP-006: API can return next eligible quiz item.
AC-MVP-007: API returns no draft items to normal consumers.
AC-MVP-008: Delivery logs are created.
AC-MVP-009: Repeat policy is demonstrable.
AC-MVP-010: Entitlement/quota denial is demonstrable.
AC-MVP-011: Admin or operational workflow can approve/publish/retire/block items.
AC-MVP-012: Basic analytics/corpus report exists.
AC-MVP-013: Demo script works end-to-end.
AC-MVP-014: SRS P0 requirements have verification evidence.
AC-MVP-015: Known MVP limitations are documented.
```

---

## 15. Production Acceptance Criteria

Production claim requires:

```text
AC-PROD-001: CI/CD or controlled deployment process exists.
AC-PROD-002: Backups and restore procedure exist.
AC-PROD-003: Monitoring and logs exist.
AC-PROD-004: Security baseline is implemented.
AC-PROD-005: Paid access uses internal entitlements.
AC-PROD-006: Public consumers cannot access draft/blocked items.
AC-PROD-007: API contract is documented.
AC-PROD-008: Incident playbook exists.
AC-PROD-009: Data migrations are versioned.
AC-PROD-010: Launch risks and limitations are documented.
AC-PROD-011: Support or issue-reporting path exists.
AC-PROD-012: Privacy/legal review appropriate to deployment context is completed.
```

---

## 16. Traceability Matrix

### 16.1. Vision Objective to Requirement Areas

| Vision Objective | Meaning | SRS requirement areas |
|---|---|---|
| VOBJ-001 Governed Corpus | Files are controlled assets | SRC, ONB, IMP, DOC |
| VOBJ-002 Canonical Data Model | One internal quiz item shape | DATA, DB, QA |
| VOBJ-003 API-First Delivery | Consumers use versioned API | API, CONS, SEC |
| VOBJ-004 CEFR-Aware Learning | A1–C2 education logic | TAX, DATA, SEL |
| VOBJ-005 Topic/Objective/Pattern Coverage | Coverage matrix | TAX, AN, DOC |
| VOBJ-006 Centralized Selection | One selection engine | SEL, API, TG |
| VOBJ-007 Multi-Consumer Support | Web/Telegram/bots/schools/API | CONS, API, TG, BILL |
| VOBJ-008 Delivery Traceability | Every delivery recorded | AN, DB, SEL |
| VOBJ-009 Monetized Access Control | Plans, quotas, entitlements | BILL, API, SEC |
| VOBJ-010 Operational Trust | Backups, logs, monitoring | OPS, REL, ENG |
| VOBJ-011 Presentation Readiness | Demo can prove platform | DEMO, DOC, QA |
| VOBJ-012 Future Source Expansion | New files onboarded safely | ONB, SRC, IMP, DATA |

### 16.2. Product Goal to Requirement Areas

| Product Goal | SRS areas |
|---|---|
| PG-001 Govern the corpus | SRC, ONB, IMP, DOC |
| PG-002 Normalize content | IMP, DATA, TAX |
| PG-003 Serve through API | API, CONS, SEC |
| PG-004 Control delivery | SEL, AN, TG |
| PG-005 Enable channels | CONS, TG, API |
| PG-006 Monetize responsibly | BILL, API, SEC, AN |
| PG-007 Measure outcomes | AN, DB, DOC |
| PG-008 Scale content | ONB, IMP, DATA, PERF |
| PG-009 Prove readiness | DEMO, QA, OPS, DOC |

---

## 17. Use Case Mapping Seed

Future `03_use_cases.md` SHALL map at least these use cases to SRS requirements:

| Use Case | Primary SRS areas |
|---|---|
| UC-001 Admin registers a new source file | ONB, SRC, ADM |
| UC-002 Admin runs dry-run import | IMP, ADM, QA |
| UC-003 Admin resolves duplicate/conflict candidates | IMP, ADM, DATA |
| UC-004 Admin approves imported quiz item | STAT, ADM, DATA |
| UC-005 API consumer requests next quiz | API, SEL, CONS, BILL |
| UC-006 API consumer submits attempt | API, AN, SEC |
| UC-007 Telegram channel receives scheduled quiz | TG, SEL, CONS, AN |
| UC-008 Consumer exceeds quota | BILL, API, SEL |
| UC-009 Teacher requests quiz pack by level/topic | API, SEL, TAX, CONS |
| UC-010 User reports item issue | AN, ADM, STAT |
| UC-011 Admin retires problematic item | STAT, ADM, DB |
| UC-012 Product owner reviews corpus coverage | TAX, AN, DOC |
| UC-013 Billing webhook updates entitlement | BILL, SEC, AN |
| UC-014 Operations owner restores backup | OPS, DB, REL |
| UC-015 Demo owner executes Stanford-style demo | DEMO, DOC, QA |

---

## 18. Test Strategy Requirements

### 18.1. Test categories

The project SHALL maintain or plan these test categories:

```text
data validation tests
import pipeline tests
schema tests
selection engine unit tests
API contract tests
API authorization tests
Telegram adapter tests
delivery logging tests
billing/quota tests
admin workflow tests
analytics/report tests
migration tests
backup/restore drills
end-to-end demo tests
```

### 18.2. P0 test rule

Every P0 requirement SHALL have one of:

```text
automated test
manual verification checklist
inspection evidence
demo evidence
operational drill evidence
```

Before production, P0 requirements relevant to live operation SHOULD move from manual-only verification toward automated or repeatable verification wherever feasible.

---

## 19. Risk-Control Requirements

| Risk | Required control |
|---|---|
| File chaos after adding new content | Source onboarding workflow, manifest, checksum, dry-run import |
| Draft items accidentally delivered | Status filtering in selection/API, tests |
| Telegram becomes hidden product logic | Telegram worker uses API/selection engine |
| Paid access bypasses quotas | Internal entitlements and quota checks |
| Corpus loses traceability | Source IDs, content hashes, import batches |
| Duplicate content causes poor experience | Content hash and duplicate candidate reports |
| Demo overclaims readiness | Demo evidence, limitations, documented artifacts |
| Security incident through API misuse | Auth, authorization, rate limits, logging |
| Operational data loss | Backup and restore procedure |
| Scope creep before MVP | MVP gates and SRS priority levels |

---

## 20. Change Control for Requirements

### 20.1. Change categories

| Category | Examples | Required action |
|---|---|---|
| Minor wording | Clarify non-substantive text | Update version patch or changelog note |
| Requirement change | Add/remove/change requirement | Update SRS, traceability and tests |
| Scope change | Promote future feature to MVP | Product owner approval and charter alignment |
| Architecture-impacting | New database/API/worker assumptions | Architecture and domain model update |
| Security-impacting | Auth, keys, permissions, data exposure | Security review |
| Data-impacting | Schema, taxonomy, source workflow | Data standard and migration review |

### 20.2. Requirement lifecycle

Requirement statuses:

```text
proposed
accepted
implemented
verified
deferred
retired
superseded
```

P0 requirements cannot be retired or weakened without product-owner approval and updated launch gate rationale.

---

## 21. Open Questions

These questions do not block drafting this SRS but should be resolved in later documents or implementation planning:

1. Which exact stack will be used for API service, database migrations and worker scheduling?
2. Will first admin workflow be CLI-only, simple web UI, or hybrid?
3. Which payment provider will be used first, if any, during closed pilot?
4. Which Telegram channel or simulated consumer will be used for first delivery demo?
5. What exact 18 theme names and translations will be frozen in `topics.yml`?
6. Which source files are highest priority for first importer implementation?
7. What is the minimum validated pilot subset before loading the entire corpus into production database?
8. What are the first API rate limits and free-plan quotas?
9. What privacy/legal posture is required for learners, schools and EU users?
10. What hosting environment will be used for demo, pilot and production?
11. What SLO/availability target is realistic for first production launch?
12. What level of analytics is allowed before personal user identity is introduced?

---

## 22. Reference Standards and Alignment

This SRS aligns with the following reference standards and engineering conventions. These references are directional and should be checked/updated in later technical standard documents:

```text
Stanford/SLAC-style requirements methodology:
- goal → features → system requirements
- use cases
- test/QA requirements
- traceability
- change control

CEFR:
- A1, A2, B1, B2, C1, C2 level model for language learning

OpenAPI:
- versioned HTTP API contract
- schemas
- auth
- errors

JSON Schema:
- canonical quiz item validation

RFC 9457 Problem Details:
- machine-readable API error format

OWASP API Security:
- object-level authorization
- object-property authorization
- auth, rate limits, input validation and logging

Telegram Bot API:
- quiz/poll delivery constraints

Git/GitHub-style repository governance:
- branch protection
- CI checks
- CODEOWNERS or ownership rules
- changelog and versioning
```

---

## 23. SRS Acceptance Criteria

This SRS document is accepted when it:

```text
AC-SRS-001: Aligns with CONSTITUTION.md.
AC-SRS-002: Aligns with 00_vision.md.
AC-SRS-003: Aligns with 01_product_charter.md.
AC-SRS-004: Defines requirement ID system.
AC-SRS-005: Defines functional requirements.
AC-SRS-006: Defines non-functional requirements.
AC-SRS-007: Defines future source onboarding requirements.
AC-SRS-008: Defines API-first and no-direct-CSV rules.
AC-SRS-009: Defines status and publication rules.
AC-SRS-010: Defines selection, anti-repeat and delivery logging rules.
AC-SRS-011: Defines entitlement/quota rules.
AC-SRS-012: Defines launch gates and acceptance criteria.
AC-SRS-013: Defines traceability from vision/product goals to requirement areas.
AC-SRS-014: Defines test/verification method categories.
AC-SRS-015: Distinguishes MVP, pilot, beta, production and demo readiness.
```

---

## 24. Final SRS Rule

The final binding rule of this SRS:

```text
API Quiz Bank is not ready because files exist.
API Quiz Bank is ready when governed sources become validated canonical data,
canonical data becomes controlled production records,
production records are selected by explicit rules,
API delivery is authorized and logged,
and every serious claim can be traced to a requirement, artifact, test or demo.
```
