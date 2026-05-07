# API Quiz Bank — Use Cases

**Документ:** `docs/03_use_cases.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational use case specification; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`, `01_product_charter.md`, `02_requirements_srs.md`  
**Дата:** 2026-04-28  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized product maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`  
**Наступні документи:** `04_domain_model.md`, `05_architecture.md`, `06_data_standard.md`, `07_api_standard.md`, `08_security_threat_model.md`, `09_quality_assurance.md`, `10_operations.md`, `11_billing_model.md`, `12_analytics_model.md`, `13_stanford_presentation_outline.md`

---

## 0. Executive Summary

`03_use_cases.md` перетворює Vision, Product Charter і SRS у конкретні сценарії роботи системи.

Документ фіксує, як API Quiz Bank має поводитися у реальних ситуаціях:

```text
source onboarding
  → import and normalization
  → canonical validation
  → duplicate/conflict handling
  → status workflow
  → API selection
  → Telegram/web/bot/app/school delivery
  → attempts and analytics
  → billing/entitlements
  → operations
  → Stanford-style demo evidence
```

Головний принцип документа:

```text
A use case is not a story about a screen.
A use case is a traceable operational contract between actor, system, data, rules, requirements and tests.
```

API Quiz Bank будується як керована API-first платформа, а не як папка CSV, сайт або окремий Telegram-бот. Тому кожен use case у цьому документі перевіряє одну або кілька конституційних істин:

```text
raw files are source assets;
production delivery uses canonical data;
consumers access content through API or controlled workers;
selection is centralized;
draft is not production-released;
new quiz files are onboarded, not dropped;
every serious action is traceable;
every production claim can be demonstrated.
```

Поточний operational baseline системи:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 canonical themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Цей baseline є стартовим активом. Use cases нижче гарантують, що поточний corpus можна впорядковано запустити, а майбутні файли з вікторинами можна безпечно додавати через controlled source onboarding workflow.

---

## 1. Role of This Document

### 1.1. Мета документа

Цей документ описує сценарії використання API Quiz Bank на рівні, достатньому для:

```text
product alignment;
engineering planning;
SRS traceability;
acceptance testing;
API design;
admin workflow design;
source onboarding design;
Telegram delivery design;
billing and entitlement design;
analytics and operations design;
Stanford-style presentation rehearsal.
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
implementation / tests / demo
```

### 1.3. Що цей документ робить

Цей документ:

- визначає акторів системи;
- описує primary, alternate and exception flows;
- показує, які дані потрібні у кожному сценарії;
- привʼязує use cases до SRS requirement areas;
- формує seed для test cases;
- задає acceptance criteria;
- показує, які сценарії треба продемонструвати для Stanford-ready review.

### 1.4. Що цей документ не робить

Цей документ не є:

- UI mockup specification;
- остаточним database schema;
- OpenAPI contract;
- security threat model;
- billing provider implementation guide;
- повторним аудитом змісту всіх quiz items;
- інструкцією для ручного редагування CSV.

Зміст вікторин вважається перевіреним на попередньому етапі. Перший launch focus — operational readiness: governance, import, status control, API, selection, delivery logging, entitlements, reports, operations and demo evidence.

---

## 2. Stanford-Style Use Case Discipline

### 2.1. Методологічна рамка

Для цього проєкту “Stanford-style” означає не маркетингову фразу, а дисципліну системної інженерії:

```text
goal
  → needs
  → features
  → requirements
  → use cases
  → test cases
  → traceability
  → change control
  → demo evidence
```

Use case в API Quiz Bank має бути:

| Attribute | Meaning |
|---|---|
| Goal-oriented | Має чітку ціль для актора або системи |
| Traceable | Привʼязаний до SRS IDs або SRS areas |
| Testable | Має acceptance criteria і test seeds |
| Operational | Описує реальну дію, а не тільки побажання |
| Data-aware | Називає дані, які створюються або змінюються |
| Security-aware | Вказує authorization / access boundaries |
| Failure-aware | Має alternate і exception flows |
| Demo-aware | Показує, чи може сценарій бути частиною Stanford demo |

### 2.2. Якість use case

Use case вважається якісним, якщо за ним можна:

```text
1. спроєктувати endpoint, workflow або job;
2. визначити потрібні таблиці/обʼєкти;
3. написати acceptance test;
4. перевірити порушення rules;
5. пояснити сценарій зовнішній аудиторії;
6. показати результат у демо або report artifact.
```

### 2.3. Нормативна мова

У цьому документі:

- **MUST / ОБОВʼЯЗКОВО** — без цього сценарій не compliant;
- **MUST NOT / ЗАБОРОНЕНО** — дія прямо порушує governance;
- **SHOULD / РЕКОМЕНДОВАНО** — бажано для Pilot/Production;
- **MAY / ДОЗВОЛЕНО** — дозволена опція, якщо не порушує Конституцію або SRS.

---

## 3. Product Context for All Use Cases

### 3.1. Product formula

```text
Verified German quiz content
  → governed source system
  → canonical data model
  → import and normalization pipeline
  → production database
  → centralized selection engine
  → versioned API
  → Telegram / web / bots / apps / schools / external clients
  → analytics / billing / quality feedback / scale
```

### 3.2. Source expansion formula

Майбутні quiz-файли додаються не через хаотичне копіювання, а через controlled onboarding:

```text
new quiz file
  → source intake
  → stable source_id
  → checksum and inventory record
  → import_manifest.yml entry
  → parser profile / parser assignment
  → dry-run import
  → canonical schema validation
  → duplicate/conflict detection
  → import batch
  → review/status workflow
  → approved/published production items
  → updated generated inventory and coverage reports
```

### 3.3. Publication rule

Normal consumers receive only `approved` or `published` quiz items.

The system MUST NOT deliver items with status:

```text
draft
imported
normalized
needs_review
retired
blocked
```

Exception: internal demo override MAY expose non-production examples only if the item is clearly marked as demo/non-production and no learner-facing consumer receives it.

### 3.4. API-first rule

No external consumer, Telegram worker, website, bot, school account or app may read directly from raw CSV files.

Delivery path:

```text
consumer request / scheduled job
  → API or authorized internal service
  → selection engine
  → eligibility filters
  → entitlement/quota checks
  → delivery log
  → response/delivery
```

### 3.5. Traceability rule

Every production quiz item MUST be traceable to:

```text
source_id
source file metadata
source checksum
source locator when available
import batch
content_hash
status history
approval/publish action
```

---

## 4. Actors

### 4.1. Primary human actors

| Actor | Description | Main goals |
|---|---|---|
| Project Owner | Власник продуктового напряму | Strategy, scope, launch gates, Stanford readiness |
| Product Owner | Відповідальний за product decisions | Priorities, roadmap, acceptance decisions |
| Content Admin | Оператор контенту | Register sources, review imports, approve/publish/retire items |
| Taxonomy Owner | Відповідальний за CEFR/theme/objective/pattern policy | Coverage, taxonomy changes, classification rules |
| Teacher | Викладач або school operator | Get level/topic-aligned quiz packs and learner workflows |
| Learner | Студент/користувач | Receive quizzes, submit attempts, improve German |
| API Consumer Owner | Власник зовнішнього API-клієнта | Integrate quiz delivery into external product |
| Telegram Channel Owner | Власник Telegram-каналу | Scheduled quiz publishing with correct rules |
| Billing/Admin Owner | Відповідальний за plans/quotas/entitlements | Access control, paid access, overrides |
| Operations Owner | Відповідальний за uptime, backups, restore | Reliability, incidents, recovery |
| Security Owner | Відповідальний за access/security posture | Authorization, abuse control, secure operations |
| Demo Owner | Відповідальний за Stanford-style demo | Rehearsed evidence, narrative, working demo path |

### 4.2. System actors

| System actor | Description |
|---|---|
| Source Registry | Stores source_id, checksum, state, filename/path metadata |
| Import Manifest | Maps source_id to parser, defaults, source state |
| Import Pipeline | Parses, validates, normalizes and reports import results |
| Canonical Validator | Validates quiz item schema and delivery compatibility |
| Duplicate Detector | Classifies duplicate/conflict candidates |
| Status Workflow | Controls item/source lifecycle states |
| Production Database | Durable operational source of truth after controlled import |
| Selection Engine | Centralized candidate filtering and selection |
| API Service | Versioned public/admin contract for consumers and internal workflows |
| Telegram Worker | Scheduled Telegram delivery adapter |
| Billing/Entitlement Engine | Plans, quotas, feature access and limits |
| Analytics Service | Delivery, attempt, coverage and operational reports |
| Monitoring/Logging System | Logs, failures, readiness, audit trails |
| Backup/Restore System | Preserves and restores production data |

### 4.3. External systems

| External system | Role |
|---|---|
| Telegram Bot API | Delivery surface for quiz/poll messages |
| Payment Provider | Optional external payment signal source |
| GitHub / Git platform | Version control, pull requests, protected branches, CI |
| CI/CD System | Runs tests, validators, contract checks and deployment gates |
| External App / LMS | Potential API consumer |

### 4.4. Negative or misuse actors

| Actor | Risk |
|---|---|
| Unauthorized API caller | Attempts to access consumer-specific data or quota-protected delivery |
| Misconfigured consumer | Requests unsupported levels/topics or violates quota |
| Operator mistake | Registers wrong parser/defaults or attempts to publish incomplete items |
| Broken worker | Retries and risks duplicate Telegram delivery |
| Payment spoofing attempt | Sends fake webhook or tries entitlement bypass |
| Data leakage path | Exposes internal source paths, correct answers, tokens or private analytics |

---

## 5. Use Case ID System

Use case IDs use stable numeric IDs:

```text
UC-001, UC-002, UC-003, ...
```

Supporting test case seeds use:

```text
TC-UC-001-01
TC-UC-001-02
```

Use case status values:

| Status | Meaning |
|---|---|
| Required for MVP | Needed to prove core platform readiness |
| Required for Pilot | Needed before real limited users/channels |
| Required for Production | Needed before broad paid/public deployment |
| Demo-critical | Must be rehearsed for Stanford-style presentation |
| Future | Valuable after core launch but not required immediately |

---

## 6. Use Case Catalog

| ID | Use Case | Primary Actor | Phase | Demo Value |
|---|---|---|---|---|
| UC-001 | Admin registers a new source file | Content Admin | MVP | High |
| UC-002 | Admin runs dry-run import | Content Admin | MVP | High |
| UC-003 | Admin resolves duplicate/conflict candidates | Content Admin | MVP/Pilot | Medium |
| UC-004 | Admin approves imported quiz item | Content Admin | MVP | High |
| UC-005 | API consumer requests next quiz | API Consumer | MVP | High |
| UC-006 | API consumer submits attempt | API Consumer / Learner | Pilot | Medium |
| UC-007 | Telegram channel receives scheduled quiz | Telegram Channel Owner / Worker | Pilot | High |
| UC-008 | Consumer exceeds quota | API Consumer / Billing Engine | MVP/Pilot | High |
| UC-009 | Teacher requests quiz pack by level/topic | Teacher | Pilot | High |
| UC-010 | User reports item issue | Learner / Teacher | Beta | Medium |
| UC-011 | Admin retires problematic item | Content Admin | Pilot | Medium |
| UC-012 | Product owner reviews corpus coverage | Product Owner | MVP/Pilot | High |
| UC-013 | Billing webhook updates entitlement | Payment Provider / Billing Engine | Beta | Medium |
| UC-014 | Operations owner restores backup | Operations Owner | Production | Medium |
| UC-015 | Demo owner executes Stanford-style demo | Demo Owner | Demo | Critical |
| UC-016 | Admin assigns parser profile and manifest defaults | Content Admin | MVP | High |
| UC-017 | Admin imports validated batch into canonical storage | Content Admin | MVP | High |
| UC-018 | Admin publishes approved batch | Content Admin | Pilot | Medium |
| UC-019 | System blocks draft item delivery | Selection Engine / API | MVP | High |
| UC-020 | Admin configures consumer rules | Content Admin / Consumer Owner | MVP/Pilot | Medium |
| UC-021 | Telegram worker handles send failure | Telegram Worker | Pilot | Medium |
| UC-022 | Telegram worker runs simulated delivery | Telegram Worker / Demo Owner | Pilot/Demo | High |
| UC-023 | Admin grants manual entitlement override | Billing/Admin Owner | Pilot | Medium |
| UC-024 | Security owner audits object-level authorization | Security Owner | MVP/Pilot | Medium |
| UC-025 | Taxonomy owner updates taxonomy through change control | Taxonomy Owner | Pilot | Medium |
| UC-026 | Admin rejects or blocks candidate source | Content Admin | MVP/Pilot | Medium |
| UC-027 | External app integrates using OpenAPI contract | API Consumer Owner | Pilot | High |
| UC-028 | Learner requests personal quiz by level/topic | Learner | Pilot/Beta | Medium |
| UC-029 | Product owner reviews delivery and usage analytics | Product Owner | Pilot/Beta | Medium |
| UC-030 | Demo owner onboards a sample future source file | Demo Owner / Content Admin | Demo | Critical |

---

## 7. Cross-Cutting Business Rules

### 7.1. Source rules

```text
BR-SRC-001: Every source file must have stable source_id before import.
BR-SRC-002: Every source file must have checksum before parser assignment.
BR-SRC-003: A candidate source cannot become active without manifest entry and import report.
BR-SRC-004: Raw files must not be silently modified after registration.
BR-SRC-005: Source history must remain available after archive/rejection/blocking.
```

### 7.2. Import rules

```text
BR-IMP-001: Dry-run import must not write production quiz items.
BR-IMP-002: Import report must include accepted, skipped, validation errors and duplicates/conflicts.
BR-IMP-003: Unknown CEFR/theme/objective/pattern values must not be silently coerced.
BR-IMP-004: Every normalized item must have content_hash.
BR-IMP-005: Failed import must not corrupt existing production data.
```

### 7.3. Publication rules

```text
BR-STAT-001: Only approved or published items may be delivered to normal consumers.
BR-STAT-002: Draft means not production-released; it does not mean content is wrong.
BR-STAT-003: Every status change must be logged.
BR-STAT-004: Retiring an item must preserve delivery and attempt history.
BR-STAT-005: Blocked items must be excluded from all normal delivery.
```

### 7.4. Selection rules

```text
BR-SEL-001: Selection must be centralized.
BR-SEL-002: Telegram worker must not own core selection logic.
BR-SEL-003: Selection must respect consumer rules, status, level, theme, quota and repeat policy.
BR-SEL-004: If no eligible item exists, system must return machine-readable reason.
BR-SEL-005: Delivery should be logged at or immediately after delivery.
```

### 7.5. API rules

```text
BR-API-001: External consumers must use versioned API.
BR-API-002: API errors must be stable and machine-readable.
BR-API-003: API must not expose raw internal file paths to normal consumers.
BR-API-004: Consumer-specific data requires object-level authorization.
BR-API-005: Public-safe response differs from admin-only response.
```

### 7.6. Billing and entitlement rules

```text
BR-BILL-001: Payment status alone is not access truth.
BR-BILL-002: Internal entitlements control access.
BR-BILL-003: Quota denial must be explicit and logged.
BR-BILL-004: Manual overrides require audit trail.
BR-BILL-005: Webhooks must update internal entitlements, not bypass them.
```

### 7.7. Demo rules

```text
BR-DEMO-001: Demo must prove governed corpus, not just static files.
BR-DEMO-002: Demo must show at least source inventory/manifest, canonical validation, API next item and delivery logging.
BR-DEMO-003: Demo must not claim planned features as implemented.
BR-DEMO-004: Demo should include controlled future source onboarding.
BR-DEMO-005: Known limitations must be explicitly documented.
```

---

## 8. Detailed Use Cases

---

## UC-001 — Admin Registers a New Source File

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Source Registry, checksum tool, generated inventory/report tooling |
| Phase | MVP |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-SRC-001, SRS-SRC-002, SRS-SRC-003, SRS-SRC-004, SRS-SRC-006, SRS-SRC-008, SRS-ONB-001, SRS-ONB-002, SRS-ONB-003, SRS-ADM-001, IF-ADM-001 |

### Goal

Register a current or future quiz file as a controlled source asset before any import, validation or production use.

### Trigger

A new quiz file is received, discovered or prepared for onboarding.

### Preconditions

- Admin is authenticated and authorized.
- File exists in approved intake location or controlled local path.
- File is not already active under the same `source_id`.
- Raw file is treated as immutable after registration.

### Main flow

1. Admin starts source registration.
2. System asks for or generates stable `source_id`.
3. Admin provides filename, original path, format, expected parser family if known, optional default CEFR/theme/objective/pattern hints and notes.
4. System computes checksum.
5. System checks whether the checksum already exists in active/candidate/archive records.
6. System creates source record with state `candidate` or `registered`.
7. System records registration timestamp and actor.
8. System updates or prepares `file_inventory.csv` / source inventory report.
9. System confirms that the file is registered but not importable until manifest/parser configuration is complete.

### Alternate flows

- **A1: Duplicate checksum found.** System flags the new file as possible duplicate and requires admin decision before active registration.
- **A2: Unknown format.** Source may be registered with `parser_pending` state.
- **A3: Current corpus source registration.** Existing active CSV files may be bulk-registered, but each still receives stable source metadata.

### Exception flows

- **E1: File unavailable.** Registration fails; no source record is created except optional failed attempt log.
- **E2: Invalid source_id.** System rejects registration and returns naming rules.
- **E3: Unauthorized actor.** System denies action and logs security event.

### Postconditions

- Source has stable identity.
- Source has checksum.
- Source state is non-production.
- Source is visible in inventory.
- Source cannot deliver items yet.

### Data touched

```text
source_files
source_inventory
source_events / audit_log
file_inventory.csv or equivalent generated report
```

### Acceptance criteria

```text
AC-UC-001-01: Registered source has stable source_id.
AC-UC-001-02: Registered source has checksum.
AC-UC-001-03: Registered source has non-production state.
AC-UC-001-04: System prevents duplicate active source_id.
AC-UC-001-05: Registration is logged with actor and timestamp.
```

### Test seeds

```text
TC-UC-001-01: Register valid CSV source and verify source_id/checksum/state.
TC-UC-001-02: Attempt to register duplicate source_id and expect rejection.
TC-UC-001-03: Attempt unauthorized registration and expect denial.
TC-UC-001-04: Register unknown format and verify parser_pending state.
```

---

## UC-002 — Admin Runs Dry-Run Import

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Import Manifest, Import Pipeline, Canonical Validator, Duplicate Detector |
| Phase | MVP |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-IMP-001, SRS-IMP-005, SRS-IMP-006, SRS-IMP-007, SRS-IMP-008, SRS-IMP-009, SRS-IMP-010, SRS-IMP-012, SRS-IMP-013, SRS-IMP-015, SRS-ADM-002, IF-ADM-002, NFR-QA-004 |

### Goal

Test how a source file will be parsed, normalized and validated without writing production quiz items.

### Trigger

A registered source has parser assignment and manifest entry ready for import validation.

### Preconditions

- Source is registered.
- Source has checksum.
- Import manifest references stable `source_id`.
- Parser profile is assigned.
- Admin is authorized.

### Main flow

1. Admin selects registered source and chooses dry-run import.
2. System reads import manifest.
3. System loads parser profile and configured defaults.
4. Import pipeline parses source rows.
5. Pipeline creates normalized item candidates in memory or temporary dry-run storage.
6. Canonical validator checks required fields, CEFR values, options, correct answer references and source traceability.
7. Duplicate detector classifies duplicate/conflict candidates.
8. System produces structured import report.
9. Report includes accepted candidates, skipped rows, validation errors, duplicate candidates, parser warnings, source traceability and sample normalized JSONL when configured.
10. System does not write production quiz items.

### Alternate flows

- **A1: Parser warnings only.** Report is generated; admin may proceed after review.
- **A2: Unknown taxonomy values.** Rows are rejected or marked needs review; system does not silently coerce values.
- **A3: Partial acceptance.** Valid candidates are listed separately from invalid/skipped rows.

### Exception flows

- **E1: Parser fails.** Source state may become `dry_run_failed`; report includes reason.
- **E2: Manifest missing source_id.** Dry-run is blocked.
- **E3: Unauthorized actor.** Action denied and logged.

### Postconditions

- Dry-run report exists.
- Production database is unchanged.
- Source state may become `dry_run_passed` or `dry_run_failed`.
- Admin has evidence for next decision.

### Data touched

```text
import_batches or dry_run_imports
import_reports
source_events
temporary normalized candidates
validation_error_records
```

### Acceptance criteria

```text
AC-UC-002-01: Dry-run does not create production quiz items.
AC-UC-002-02: Dry-run report includes accepted/skipped/error counts.
AC-UC-002-03: Report includes duplicate/conflict candidates.
AC-UC-002-04: Unknown canonical values are not silently accepted.
AC-UC-002-05: Source traceability is present in normalized candidates.
```

### Test seeds

```text
TC-UC-002-01: Run dry-run on valid source and verify report without DB inserts.
TC-UC-002-02: Run dry-run with invalid CEFR and verify validation error.
TC-UC-002-03: Run dry-run with duplicate content and verify duplicate classification.
TC-UC-002-04: Run dry-run with parser failure and verify failure state/report.
```

---

## UC-003 — Admin Resolves Duplicate/Conflict Candidates

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Duplicate Detector, Import Pipeline, Admin Interface, Canonical Validator |
| Phase | MVP/Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-IMP-006, SRS-IMP-007, SRS-IMP-009, SRS-IMP-013, SRS-DATA-012, SRS-DB-006, SRS-ADM-008, NFR-QA-004 |

### Goal

Resolve duplicate or conflicting quiz candidates before production import or publication.

### Trigger

Dry-run or import report identifies duplicate/conflict candidates.

### Preconditions

- Import report exists.
- Duplicate/conflict records are available.
- Admin has permission to resolve content conflicts.

### Main flow

1. Admin opens duplicate/conflict review.
2. System shows candidate item, existing matching item(s), content_hash, normalized stem/options and source traceability.
3. System classifies issue type: exact duplicate, near duplicate, same stem/different answer, same answer/different options, source collision or hash collision.
4. Admin selects resolution: skip candidate, keep both as versioned variants, merge metadata, mark needs review, block candidate or allow import with override reason.
5. System records decision with actor, timestamp and reason.
6. Import pipeline applies resolution during actual import.
7. Analytics/reporting preserves duplicate decision counts.

### Alternate flows

- **A1: Exact duplicate.** Default recommended action is skip candidate or link to existing item.
- **A2: Same stem but different correct answer.** Default action is `needs_review` or blocked until manual verification.
- **A3: Both variants are pedagogically valid.** Admin may allow both with explicit versioning/variant reason.

### Exception flows

- **E1: Admin lacks permission.** System denies resolution.
- **E2: Candidate disappeared after new dry-run.** System requires report refresh.
- **E3: Resolution would break canonical schema.** System blocks the action.

### Postconditions

- Duplicate/conflict has explicit resolution.
- Import can proceed only for allowed candidates.
- Decision is auditable.

### Acceptance criteria

```text
AC-UC-003-01: Duplicate candidates are not silently imported.
AC-UC-003-02: Resolution decision is logged.
AC-UC-003-03: Exact duplicates can be skipped.
AC-UC-003-04: Conflicting correct answers require review/block/explicit override.
AC-UC-003-05: Production active duplicate policy is enforceable.
```

### Test seeds

```text
TC-UC-003-01: Exact duplicate detected and skipped.
TC-UC-003-02: Conflict detected and moved to needs_review.
TC-UC-003-03: Admin override allows versioned variant with reason.
TC-UC-003-04: Unauthorized user cannot resolve duplicate.
```

---

## UC-004 — Admin Approves Imported Quiz Item

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Status Workflow, Canonical Validator, Admin Interface, Audit Log |
| Phase | MVP |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-DATA-001, SRS-DATA-004, SRS-DATA-005, SRS-DATA-006, SRS-DATA-008, SRS-DATA-009, SRS-STAT-001, SRS-STAT-002, SRS-STAT-004, SRS-STAT-005, SRS-STAT-006, SRS-ADM-003, SRS-ADM-004, SRS-ADM-006, IF-ADM-003 |

### Goal

Move a valid imported/normalized item into `approved` status so it becomes eligible for controlled delivery.

### Trigger

Admin reviews an imported or normalized quiz item and decides it is production-ready.

### Preconditions

- Item exists in canonical/imported storage.
- Item conforms to canonical schema.
- Item has required CEFR level and primary theme.
- Item has source traceability and content_hash.
- Admin is authorized.

### Main flow

1. Admin opens item review.
2. System shows stem, options, correct answer reference, CEFR level, theme, objective, pattern, tags, source_id, source locator, content_hash and validation status.
3. Admin confirms item is ready for approval.
4. System checks required metadata and publication eligibility.
5. System changes status from `imported`, `normalized` or `needs_review` to `approved`.
6. System records status change with actor, timestamp, previous status, new status and optional reason.
7. Item becomes eligible for selection engine, subject to consumer rules and entitlements.

### Alternate flows

- **A1: Missing metadata.** System blocks approval and shows missing fields.
- **A2: Admin marks needs_review.** Item remains non-deliverable.
- **A3: Batch approval.** Admin approves multiple validated items if batch status change policy and audit trail are satisfied.

### Exception flows

- **E1: Invalid correct answer reference.** System blocks approval.
- **E2: Unknown CEFR/theme.** System blocks approval.
- **E3: Unauthorized actor.** Action denied and logged.

### Postconditions

- Approved item is eligible but not guaranteed to be selected.
- Status history is updated.
- Delivery still requires selection, consumer rules and entitlement checks.

### Acceptance criteria

```text
AC-UC-004-01: Approved item has valid schema.
AC-UC-004-02: Approved item has CEFR level and primary theme.
AC-UC-004-03: Status transition is logged.
AC-UC-004-04: Invalid item cannot be approved.
AC-UC-004-05: Draft/imported/needs_review items are not delivered before approval.
```

### Test seeds

```text
TC-UC-004-01: Approve valid normalized item.
TC-UC-004-02: Attempt to approve item without correct answer and expect block.
TC-UC-004-03: Attempt batch approval and verify audit records.
TC-UC-004-04: Verify approved item can appear in eligible candidate set.
```

---

## UC-005 — API Consumer Requests Next Quiz

| Field | Value |
|---|---|
| Primary actor | API Consumer |
| Supporting systems | API Service, Selection Engine, Consumer Rules, Entitlement Engine, Delivery Log |
| Phase | MVP |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-API-001, SRS-API-002, SRS-API-005, SRS-API-007, SRS-API-008, SRS-API-009, SRS-API-010, SRS-API-011, SRS-SEL-001, SRS-SEL-002, SRS-SEL-003, SRS-SEL-004, SRS-SEL-005, SRS-SEL-007, SRS-SEL-008, SRS-CONS-001, SRS-CONS-004, SRS-CONS-005, SRS-AN-001, IF-API-003, IF-API-006 |

### Goal

Return the next eligible quiz item for a consumer through the versioned API.

### Trigger

API client calls:

```text
GET /v1/quiz-items/next
```

with consumer identity and optional filters.

### Preconditions

- Consumer exists and is active.
- Request is authenticated where required.
- Consumer has rules or safe defaults.
- Entitlement/quota permits delivery.
- Approved/published eligible items exist.

### Main flow

1. API receives next quiz request.
2. API authenticates caller.
3. API verifies object-level authorization for requested consumer context.
4. API loads consumer rules: allowed CEFR levels, themes, limits, repeat policy and compatibility constraints.
5. Entitlement engine confirms access and quota.
6. Selection engine filters candidates by approved/published status.
7. Selection engine filters by consumer rules.
8. Selection engine excludes blocked/retired/draft/non-production items.
9. Selection engine applies repeat policy using delivery history.
10. Selection engine selects item.
11. System records delivery or reserves delivery according to implementation policy.
12. API returns public-safe quiz item response.

### Alternate flows

- **A1: Optional filters narrower than consumer rules.** System applies intersection of requested filters and allowed rules.
- **A2: Deterministic demo mode.** Internal demo consumer may request deterministic selection for reproducible presentation.
- **A3: No eligible item.** API returns machine-readable no-eligible-item problem.

### Exception flows

- **E1: Consumer inactive.** API returns access denied or consumer inactive error.
- **E2: Quota exceeded.** API returns quota problem detail.
- **E3: Unauthorized access to another consumer.** API denies and logs security event.
- **E4: Selection engine failure.** API returns service error and logs incident.

### Postconditions

- Returned item is safe for consumer.
- Delivery record exists or delivery reservation is created.
- Quota/usage is updated where required.

### Acceptance criteria

```text
AC-UC-005-01: API returns only approved/published items.
AC-UC-005-02: API respects consumer levels and themes.
AC-UC-005-03: API enforces quota/entitlement.
AC-UC-005-04: API enforces object-level authorization.
AC-UC-005-05: API records delivery or reservation.
AC-UC-005-06: API returns machine-readable error when no eligible item exists.
```

### Test seeds

```text
TC-UC-005-01: Active consumer receives approved item.
TC-UC-005-02: Draft item is never returned.
TC-UC-005-03: Repeat-policy exclusion works.
TC-UC-005-04: Unauthorized consumer access denied.
TC-UC-005-05: No eligible item returns standard error.
```

---

## UC-006 — API Consumer Submits Attempt

| Field | Value |
|---|---|
| Primary actor | API Consumer / Learner |
| Supporting systems | API Service, Attempts Store, Analytics Service, Authorization Layer |
| Phase | Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-API-006, SRS-API-008, SRS-API-009, SRS-API-014, SRS-AN-003, SRS-AN-004, SRS-AN-010, SRS-DATA-006, SRS-DB-001, NFR-SEC-005, NFR-QA-003 |

### Goal

Record learner/API consumer attempt for delivered quiz item and enable analytics.

### Trigger

Consumer submits attempt to:

```text
POST /v1/attempts
```

### Preconditions

- Quiz item was delivered or is valid for attempt context.
- Caller is authenticated if endpoint is protected.
- Caller is authorized for consumer/user context.
- Attempt payload contains item identifier and selected option(s).

### Main flow

1. API receives attempt submission.
2. API authenticates caller.
3. API verifies object-level authorization for consumer/user context.
4. API validates item identifier and selected option references.
5. System determines correctness using canonical answer data.
6. System stores attempt event with timestamp, consumer/user context, selected options and correctness where appropriate.
7. Analytics service updates or makes available aggregate metrics.
8. API returns attempt result according to consumer interaction mode.

### Alternate flows

- **A1: Anonymous Telegram poll context.** Full user attempt may not be available; system records aggregate delivery/attempt data if Telegram exposes it or stores only delivery outcome.
- **A2: Idempotency key provided.** Duplicate submissions are prevented or safely ignored.
- **A3: Delayed submission.** System accepts if within configured window; otherwise returns expired attempt error.

### Exception flows

- **E1: Invalid option ID.** API returns validation error.
- **E2: Attempt for inaccessible consumer.** API denies and logs security event.
- **E3: Item retired after delivery.** System may accept attempt for historical delivery but does not re-enable item for future delivery.

### Postconditions

- Attempt is recorded or rejected with explicit reason.
- Analytics can use attempt data.
- Sensitive answer data is not leaked beyond permitted interaction mode.

### Acceptance criteria

```text
AC-UC-006-01: Valid attempt is stored.
AC-UC-006-02: Invalid option is rejected.
AC-UC-006-03: Unauthorized attempt is denied.
AC-UC-006-04: Duplicate attempt is handled according to idempotency policy.
AC-UC-006-05: Attempt analytics do not expose unauthorized consumer data.
```

### Test seeds

```text
TC-UC-006-01: Submit correct answer and verify stored correctness.
TC-UC-006-02: Submit invalid option and expect validation problem.
TC-UC-006-03: Submit duplicate with idempotency key.
TC-UC-006-04: Attempt cross-consumer access and expect denial.
```

---

## UC-007 — Telegram Channel Receives Scheduled Quiz

| Field | Value |
|---|---|
| Primary actor | Telegram Channel Owner / Telegram Worker |
| Supporting systems | Scheduler, Selection Engine, API Service, Telegram Adapter, Delivery Log |
| Phase | Pilot |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-TG-001, SRS-TG-002, SRS-TG-003, SRS-TG-004, SRS-TG-005, SRS-TG-006, SRS-TG-008, SRS-TG-010, SRS-TG-012, SRS-SEL-001, SRS-SEL-005, SRS-CONS-002, SRS-CONS-004, SRS-AN-001, IF-TG-001, IF-TG-002, IF-TG-003, IF-TG-005, NFR-QA-006 |

### Goal

Publish scheduled quiz to a Telegram channel using approved/published canonical content and centralized selection.

### Trigger

Scheduler reaches configured posting time for a Telegram channel.

### Preconditions

- Telegram consumer exists and is active.
- Channel has schedule, posting window, allowed levels/themes and repeat policy.
- Channel has required entitlement/quota.
- Telegram worker is authorized to post.
- Eligible approved/published item exists.

### Main flow

1. Scheduler triggers Telegram worker.
2. Worker loads channel consumer configuration.
3. Worker requests next quiz through API/selection engine.
4. Selection engine filters by status, rules, repeat policy and entitlement.
5. Worker receives public-safe quiz item.
6. Telegram adapter validates poll/quiz compatibility: question length, option count, correct answer representation and explanation rules.
7. Worker sends Telegram quiz/poll.
8. Worker records delivery status, timestamp and Telegram message identifier when available.
9. Analytics service can report delivery.

### Alternate flows

- **A1: No eligible item.** Worker records no-eligible-item outcome and does not post fallback ungoverned content.
- **A2: Dry-run mode.** Worker generates payload without posting.
- **A3: Multiple scheduled channels.** Each channel uses its own consumer rules and delivery history.

### Exception flows

- **E1: Telegram send failure.** Worker records failure reason and follows retry/idempotency policy.
- **E2: Compatibility failure.** Worker blocks send and records validation reason.
- **E3: Entitlement revoked.** Worker does not post and records access denial.

### Postconditions

- Telegram message is posted or failure is explicitly logged.
- Delivery record exists.
- Repeat policy history is updated.

### Acceptance criteria

```text
AC-UC-007-01: Telegram worker does not read raw CSV.
AC-UC-007-02: Telegram worker posts only approved/published items.
AC-UC-007-03: Telegram compatibility is validated before send.
AC-UC-007-04: Delivery status is recorded.
AC-UC-007-05: Repeat policy is respected.
AC-UC-007-06: Entitlement and consumer status are respected.
```

### Test seeds

```text
TC-UC-007-01: Scheduled channel receives quiz from selection engine.
TC-UC-007-02: Draft item excluded from Telegram delivery.
TC-UC-007-03: Incompatible option count blocks delivery.
TC-UC-007-04: Telegram send result recorded with message ID.
TC-UC-007-05: Repeat window prevents same item.
```

---

## UC-008 — Consumer Exceeds Quota

| Field | Value |
|---|---|
| Primary actor | API Consumer / Billing Engine |
| Supporting systems | API Service, Entitlement Engine, Selection Engine, Analytics/Usage Log |
| Phase | MVP/Pilot |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-BILL-001, SRS-BILL-003, SRS-BILL-004, SRS-BILL-005, SRS-API-010, SRS-API-011, SRS-SEL-007, SRS-CONS-003, SRS-AN-002, NFR-SEC-007 |

### Goal

Deny delivery when consumer quota is exhausted while returning a clear machine-readable error.

### Trigger

Consumer requests next quiz after reaching configured usage limit.

### Preconditions

- Consumer exists.
- Entitlement/quota model is active.
- Usage count is available.
- Consumer has reached or exceeded limit.

### Main flow

1. API receives delivery request.
2. API authenticates and authorizes caller.
3. Entitlement engine checks consumer quota.
4. System detects quota exceeded.
5. Selection is blocked before delivery.
6. API returns machine-readable quota exceeded problem.
7. System records quota denial event.
8. Analytics can show quota usage and denial.

### Alternate flows

- **A1: Manual override exists.** System applies override if valid and logs it.
- **A2: Grace period configured.** System allows limited delivery and records grace usage.
- **A3: Consumer has multiple entitlement scopes.** System checks correct scope for requested feature.

### Exception flows

- **E1: Entitlement service unavailable.** System follows fail-closed or documented safe fallback policy.
- **E2: Usage record inconsistent.** System blocks delivery or uses conservative safe limit and logs anomaly.

### Postconditions

- No quiz is delivered when quota denial applies.
- Denial is auditable.
- Consumer can upgrade/renew through future billing flow.

### Acceptance criteria

```text
AC-UC-008-01: Quota-exceeded consumer receives no quiz.
AC-UC-008-02: Error is machine-readable.
AC-UC-008-03: Denial is logged.
AC-UC-008-04: Manual override is auditable.
AC-UC-008-05: Selection engine does not bypass entitlement check.
```

### Test seeds

```text
TC-UC-008-01: Exhaust quota and verify denial.
TC-UC-008-02: Validate problem details fields.
TC-UC-008-03: Apply manual override and verify delivery allowed.
TC-UC-008-04: Remove override and verify denial resumes.
```

---

## UC-009 — Teacher Requests Quiz Pack by Level/Topic

| Field | Value |
|---|---|
| Primary actor | Teacher |
| Supporting systems | API Service, Selection Engine, Taxonomy Service, Consumer Rules, Entitlement Engine |
| Phase | Pilot |
| Priority | P1 |
| Demo value | High |
| SRS mapping | SRS-TAX-001, SRS-TAX-002, SRS-TAX-003, SRS-TAX-004, SRS-SEL-001, SRS-SEL-003, SRS-SEL-004, SRS-SEL-005, SRS-API-004, SRS-API-005, SRS-CONS-002, SRS-BILL-004 |

### Goal

Allow a teacher to request a controlled quiz pack for a given CEFR level and topic/theme.

### Trigger

Teacher requests a lesson pack such as:

```text
A2 + Travel + 10 items
B1 + Grammar + 15 items
C1 + Administrative/legal procedures + 20 items
```

### Preconditions

- Teacher or school consumer exists.
- Teacher has entitlement for requested level/topic/pack size.
- Taxonomy contains requested level/theme.
- Eligible approved/published items exist.

### Main flow

1. Teacher selects CEFR level, theme/topic and desired number of items.
2. System validates requested taxonomy values.
3. System checks teacher/school entitlement.
4. Selection engine builds eligible candidate pool.
5. Selection engine applies anti-repeat and optional coverage balancing.
6. System returns quiz pack/session.
7. Delivery/session record is created.
8. Teacher can use pack in lesson, app, school dashboard or export mode if allowed.

### Alternate flows

- **A1: Insufficient items.** System returns smaller pack with explanation or no-eligible-item reason.
- **A2: Mixed-level pack.** Teacher may request allowed level range if rules permit.
- **A3: Objective/pattern balancing.** System distributes items across objectives/patterns when configured.

### Exception flows

- **E1: Unknown level/theme.** Request rejected.
- **E2: Entitlement does not cover requested pack.** Request denied.
- **E3: Only draft items exist for requested area.** System does not deliver them and returns no eligible items.

### Postconditions

- Teacher receives valid controlled pack or explicit reason.
- Pack/session can be traced and analyzed.

### Acceptance criteria

```text
AC-UC-009-01: Teacher can request pack by CEFR and theme.
AC-UC-009-02: Unknown taxonomy values are rejected.
AC-UC-009-03: Draft/non-production items are excluded.
AC-UC-009-04: Entitlement controls pack size/access.
AC-UC-009-05: Delivery/session is logged.
```

### Test seeds

```text
TC-UC-009-01: Teacher requests valid A2 topic pack.
TC-UC-009-02: Teacher requests invalid CEFR and receives validation error.
TC-UC-009-03: Teacher requests unavailable topic and receives no-eligible-item reason.
TC-UC-009-04: Teacher exceeds pack entitlement and receives denial.
```

---

## UC-010 — User Reports Item Issue

| Field | Value |
|---|---|
| Primary actor | Learner / Teacher |
| Supporting systems | API Service, Admin Workflow, Analytics Service, Status Workflow |
| Phase | Beta |
| Priority | P2 |
| Demo value | Medium |
| SRS mapping | SRS-AN-008, SRS-ADM-008, SRS-ADM-009, SRS-STAT-009, SRS-STAT-008, SRS-API-011, NFR-SEC-008 |

### Goal

Allow a user or teacher to report a suspected issue with a quiz item without immediately changing production status.

### Trigger

User believes an item has wrong answer, confusing wording, typo, wrong level/theme or inappropriate content.

### Preconditions

- Item has been delivered or is visible in authorized context.
- Reporting endpoint or admin intake exists.
- Reporter context is known or anonymous reporting is allowed.

### Main flow

1. User submits report with item ID and issue category.
2. System validates that item ID is reportable.
3. System stores issue report with timestamp, consumer context and category.
4. Analytics increments issue count.
5. Admin queue shows reported item.
6. Admin may later review and mark item as monitored, needs_review, retired or blocked.

### Alternate flows

- **A1: Anonymous report.** System stores report without personal data.
- **A2: Multiple reports.** System aggregates reports and raises priority.
- **A3: Report from teacher.** Teacher report may receive higher triage priority.

### Exception flows

- **E1: Unknown item ID.** System rejects report.
- **E2: Abuse/spam.** System rate-limits or filters repeated reports.
- **E3: Report contains sensitive data.** System sanitizes stored text according to privacy/logging policy.

### Postconditions

- Issue report exists.
- Item remains in current status until admin action.
- Admin has traceability for quality feedback.

### Acceptance criteria

```text
AC-UC-010-01: Valid item issue report is stored.
AC-UC-010-02: Report does not automatically retire item.
AC-UC-010-03: Admin can see issue category and item traceability.
AC-UC-010-04: Report analytics can be generated.
AC-UC-010-05: Private data is not unnecessarily exposed.
```

### Test seeds

```text
TC-UC-010-01: Submit wrong-answer report and verify admin queue.
TC-UC-010-02: Submit unknown item report and expect validation error.
TC-UC-010-03: Submit repeated reports and verify aggregation/rate handling.
```

---

## UC-011 — Admin Retires Problematic Item

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Status Workflow, Admin Interface, Delivery History, Analytics Service |
| Phase | Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-STAT-006, SRS-STAT-007, SRS-STAT-008, SRS-STAT-009, SRS-ADM-004, SRS-ADM-006, SRS-ADM-012, SRS-DB-005, NFR-REL-005 |

### Goal

Remove a problematic item from future delivery while preserving historical records.

### Trigger

Admin confirms that item should no longer be delivered.

### Preconditions

- Item exists.
- Admin has status-change permission.
- Reason for retirement/blocking is available or required.

### Main flow

1. Admin opens item record.
2. System shows current status, delivery history, attempts, issue reports and source traceability.
3. Admin selects `retired` or `blocked`.
4. System asks for reason if required.
5. System updates item status.
6. System records status transition.
7. Selection engine excludes item from future delivery.
8. Historical delivery and attempt records remain intact.

### Alternate flows

- **A1: Emergency block.** Admin blocks item immediately if there is high-risk issue.
- **A2: Temporary review.** Admin changes status to `needs_review` instead of retired.
- **A3: Source-level block.** If many items from same source are problematic, admin may trigger source review/block workflow.

### Exception flows

- **E1: Item already retired.** System records no-op or prevents duplicate transition.
- **E2: Unauthorized actor.** Action denied and logged.
- **E3: Batch retire without reason.** System blocks if policy requires reason.

### Postconditions

- Item is excluded from future normal delivery.
- Historical records are preserved.
- Audit trail explains status change.

### Acceptance criteria

```text
AC-UC-011-01: Retired item is not selected.
AC-UC-011-02: Delivery history is preserved.
AC-UC-011-03: Status change is logged.
AC-UC-011-04: Emergency block excludes item immediately.
AC-UC-011-05: Unauthorized retirement is denied.
```

### Test seeds

```text
TC-UC-011-01: Retire item and verify excluded from selection.
TC-UC-011-02: Verify old delivery records still exist.
TC-UC-011-03: Block item and verify immediate exclusion.
TC-UC-011-04: Attempt retirement without permission and expect denial.
```

---

## UC-012 — Product Owner Reviews Corpus Coverage

| Field | Value |
|---|---|
| Primary actor | Product Owner |
| Supporting systems | Analytics Service, Coverage Report Tooling, Taxonomy Service, Generated Reports |
| Phase | MVP/Pilot |
| Priority | P1 |
| Demo value | High |
| SRS mapping | SRS-TAX-004, SRS-TAX-005, SRS-AN-005, SRS-AN-011, SRS-DOC-004, SRS-CORE-008, SRS-DEMO-002 |

### Goal

Review corpus distribution and identify coverage gaps across CEFR levels, themes, objectives and patterns.

### Trigger

Product owner requests current coverage report before launch, pilot, roadmap planning or demo.

### Preconditions

- Taxonomy exists.
- Corpus inventory/import state exists.
- Coverage tooling can compute matrix.

### Main flow

1. Product owner opens or generates coverage report.
2. System reports item counts by status, level, theme, objective and pattern.
3. System shows coverage matrix `level × theme_id × objective_id × pattern_id`.
4. System flags missing or underrepresented areas.
5. Product owner uses report to decide launch scope, content priorities and future source onboarding needs.
6. Report is saved or linked as generated artifact.

### Alternate flows

- **A1: Current raw corpus only.** Report may be generated from existing corpus snapshot before database import, clearly marked as source snapshot.
- **A2: Production corpus only.** Report shows only approved/published production items.
- **A3: Comparative report.** System compares raw/imported/approved/published coverage.

### Exception flows

- **E1: Missing taxonomy.** System cannot compute full coverage; report lists missing taxonomy dependency.
- **E2: Incomplete import state.** Report marks counts as provisional.

### Postconditions

- Coverage evidence exists.
- Product priorities can be derived.
- Demo can show governed corpus instead of only total item count.

### Acceptance criteria

```text
AC-UC-012-01: Report shows counts by status/level/theme.
AC-UC-012-02: Report supports coverage matrix.
AC-UC-012-03: Report distinguishes source snapshot from production delivery eligibility.
AC-UC-012-04: Report is reproducible by tooling.
AC-UC-012-05: Report can support Stanford-style demo evidence.
```

### Test seeds

```text
TC-UC-012-01: Generate coverage report for current corpus.
TC-UC-012-02: Verify level/theme counts match expected snapshot.
TC-UC-012-03: Verify draft items are counted but marked non-production.
TC-UC-012-04: Verify missing coverage flags.
```

---

## UC-013 — Billing Webhook Updates Entitlement

| Field | Value |
|---|---|
| Primary actor | Payment Provider / Billing Engine |
| Supporting systems | Webhook Receiver, Entitlement Store, Audit Log, API Service |
| Phase | Beta |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-BILL-001, SRS-BILL-002, SRS-BILL-005, SRS-BILL-007, SRS-BILL-008, SRS-BILL-009, SRS-API-010, NFR-SEC-015 |

### Goal

Convert external payment/subscription events into internal entitlement records without making payment provider status the sole access truth.

### Trigger

Payment provider sends subscription/payment event webhook.

### Preconditions

- Webhook endpoint is configured.
- Provider signature verification or equivalent protection exists.
- Customer/consumer mapping exists.
- Entitlement model exists.

### Main flow

1. Webhook receiver receives provider event.
2. System verifies webhook authenticity.
3. System parses event type.
4. System maps provider customer/subscription to internal account/consumer.
5. System updates internal entitlement records: feature, scope, limit, validity period and status.
6. System records billing event and audit trail.
7. API delivery uses internal entitlements, not raw provider event, for future access decisions.

### Alternate flows

- **A1: Subscription renewed.** System extends validity.
- **A2: Subscription canceled.** System revokes or schedules entitlement expiration.
- **A3: Payment failed.** System may downgrade, suspend or enter grace state according to policy.

### Exception flows

- **E1: Invalid signature.** Webhook rejected and logged.
- **E2: Unknown customer mapping.** Event stored as unresolved and does not grant access.
- **E3: Duplicate webhook.** System handles idempotently.

### Postconditions

- Internal entitlement state reflects accepted provider event.
- Access decisions remain internal and auditable.

### Acceptance criteria

```text
AC-UC-013-01: Valid webhook updates internal entitlement.
AC-UC-013-02: Invalid webhook does not update entitlement.
AC-UC-013-03: Unknown customer does not receive access.
AC-UC-013-04: Duplicate webhook is idempotent.
AC-UC-013-05: Entitlement changes are logged.
```

### Test seeds

```text
TC-UC-013-01: Valid paid event grants entitlement.
TC-UC-013-02: Invalid signature rejected.
TC-UC-013-03: Cancellation revokes entitlement.
TC-UC-013-04: Duplicate event has no double effect.
```

---

## UC-014 — Operations Owner Restores Backup

| Field | Value |
|---|---|
| Primary actor | Operations Owner |
| Supporting systems | Backup/Restore System, Production Database, Monitoring, Incident Log |
| Phase | Production |
| Priority | P0 for production |
| Demo value | Medium |
| SRS mapping | SRS-DB-009, SRS-DOC-008, NFR-OPS-001, NFR-OPS-002, NFR-OPS-007, NFR-OPS-008, NFR-REL-008 |

### Goal

Restore service data from backup after incident, test drill or migration failure.

### Trigger

Incident, restore drill, failed migration, data corruption risk or disaster recovery test.

### Preconditions

- Backup procedure exists.
- Restore procedure exists.
- Backup artifact is available.
- Operations owner is authorized.
- Maintenance/communication policy is known.

### Main flow

1. Operations owner declares restore action or drill.
2. System enters maintenance/safe mode if needed.
3. Operations owner selects backup artifact.
4. Restore procedure validates backup integrity.
5. Database is restored to target environment.
6. Migrations or rollback steps are applied if needed.
7. Health/readiness checks are run.
8. Critical data is verified: sources, items, options, status history, consumers, deliveries, entitlements.
9. Incident/restore log is updated.
10. Service exits maintenance mode when safe.

### Alternate flows

- **A1: Restore drill.** Action happens in non-production environment.
- **A2: Partial restore.** Limited data restored if policy allows.
- **A3: Migration rollback.** Restore is combined with schema rollback.

### Exception flows

- **E1: Backup artifact invalid.** Restore fails; system remains in safe mode.
- **E2: Verification fails.** Service is not declared healthy.
- **E3: Restore would lose recent data.** Owner follows incident playbook and records tradeoff.

### Postconditions

- System data is restored or failure is recorded.
- Operational evidence exists.
- Production readiness claim is supported by tested restore procedure.

### Acceptance criteria

```text
AC-UC-014-01: Restore procedure is documented.
AC-UC-014-02: Restore drill can be executed.
AC-UC-014-03: Restored data passes verification checklist.
AC-UC-014-04: Failed restore does not falsely mark service healthy.
AC-UC-014-05: Incident/restore event is logged.
```

### Test seeds

```text
TC-UC-014-01: Restore backup in staging and run health checks.
TC-UC-014-02: Try invalid backup and verify failure handling.
TC-UC-014-03: Restore after test migration and verify rollback path.
```

---

## UC-015 — Demo Owner Executes Stanford-Style Demo

| Field | Value |
|---|---|
| Primary actor | Demo Owner |
| Supporting systems | Source Reports, Import Pipeline, API, Selection Engine, Telegram Worker, Analytics, Documentation |
| Phase | Demo |
| Priority | P0 for demo |
| Demo value | Critical |
| SRS mapping | SRS-DEMO-001, SRS-DEMO-002, SRS-DEMO-003, SRS-DEMO-004, SRS-DEMO-005, SRS-DEMO-006, SRS-DEMO-007, SRS-DEMO-008, SRS-DEMO-009, SRS-DEMO-010, SRS-DEMO-011, SRS-DEMO-012, NFR-QA-008, NFR-QA-009 |

### Goal

Demonstrate API Quiz Bank as a governed platform, not as static files.

### Trigger

Stanford-style review, investor/partner presentation, internal architecture review or launch readiness presentation.

### Preconditions

- Demo script exists.
- Demo consumer is clearly marked internal.
- Core artifacts exist: Constitution, Vision, Product Charter, SRS, Use Cases, inventory/manifest, schema or canonical sample, API demo, delivery log and architecture narrative.
- Known limitations are documented.

### Main flow

1. Demo owner states problem: quiz content is valuable but not scalable without governance and API-first delivery.
2. Demo shows current corpus baseline and generated inventory/coverage report.
3. Demo shows source governance: source_id, checksum, manifest, parser/dry-run logic.
4. Demo shows canonical item/schema validation.
5. Demo shows status rule: draft items are not delivered to normal consumers.
6. Demo calls API `/v1/quiz-items/next` or equivalent demo endpoint.
7. Demo shows selection engine filters: status, level, theme, repeat policy, entitlement/quota.
8. Demo shows delivery log.
9. Demo optionally shows Telegram dry-run or real pilot delivery.
10. Demo shows quota denial or simulated entitlement denial.
11. Demo shows future source onboarding path.
12. Demo ends with risks, roadmap and next engineering milestones.

### Alternate flows

- **A1: Offline demo.** Pre-generated artifacts and recorded API output are shown if live system unavailable.
- **A2: Partial MVP demo.** Planned features are clearly marked as planned and not misrepresented as implemented.
- **A3: Technical deep dive.** Use cases and SRS traceability are shown to technical audience.

### Exception flows

- **E1: API unavailable.** Demo owner switches to fallback artifacts and honestly marks live limitation.
- **E2: Demo data inconsistent.** Demo is stopped or limitation is disclosed.
- **E3: Security-sensitive data visible.** Demo hides tokens, secrets, internal paths and private data.

### Postconditions

- Audience sees system-level product proof.
- Claims are tied to artifacts or demos.
- Next milestones are clear.

### Acceptance criteria

```text
AC-UC-015-01: Demo shows governed corpus, not only files.
AC-UC-015-02: Demo shows source inventory/manifest.
AC-UC-015-03: Demo shows canonical validation or schema.
AC-UC-015-04: Demo shows API next-item delivery.
AC-UC-015-05: Demo shows draft items are not delivered.
AC-UC-015-06: Demo shows delivery logging.
AC-UC-015-07: Demo shows future source onboarding path.
AC-UC-015-08: Demo marks planned features honestly.
```

### Test seeds

```text
TC-UC-015-01: Rehearse demo from clean environment.
TC-UC-015-02: Verify each claim has artifact/test/demo evidence.
TC-UC-015-03: Run demo script with live API.
TC-UC-015-04: Run fallback demo using artifacts only.
```

---

## UC-016 — Admin Assigns Parser Profile and Manifest Defaults

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Import Manifest, Parser Registry, Taxonomy Service, Source Registry |
| Phase | MVP |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-IMP-001, SRS-IMP-002, SRS-IMP-003, SRS-IMP-004, SRS-IMP-011, SRS-ONB-004, SRS-ONB-005, SRS-ADM-001 |

### Goal

Connect a registered source to the correct parser profile and controlled default metadata before dry-run import.

### Trigger

A source is registered and needs import configuration.

### Preconditions

- Source has `source_id` and checksum.
- Parser profile exists or source is marked `parser_pending`.
- Taxonomy defaults are known if used.
- Admin is authorized.

### Main flow

1. Admin opens source configuration.
2. Admin selects parser profile.
3. Admin configures defaults when appropriate: CEFR level, theme, objective, pattern, item type, language mode.
4. System validates defaults against taxonomy.
5. System updates `import_manifest.yml` or equivalent structured manifest.
6. Manifest references source by `source_id`.
7. System records manifest change under version control or audit log.
8. Source state changes to `parser_assigned`.

### Alternate flows

- **A1: Parser unknown.** Source remains `parser_pending`.
- **A2: Defaults not needed.** Parser extracts metadata per row.
- **A3: Multiple parser candidates.** Admin runs parser detection or selects manually.

### Exception flows

- **E1: Invalid default CEFR/theme.** System rejects manifest update.
- **E2: Manifest references filename only.** System rejects or warns until `source_id` reference is used.
- **E3: Unauthorized manifest change.** Denied and logged.

### Postconditions

- Source has parser profile or explicit parser pending state.
- Manifest is ready for dry-run.
- Defaults are explicit and auditable.

### Acceptance criteria

```text
AC-UC-016-01: Manifest maps source_id to parser profile.
AC-UC-016-02: Defaults validate against canonical taxonomy.
AC-UC-016-03: Unknown values are rejected.
AC-UC-016-04: Manifest change is versioned/audited.
AC-UC-016-05: Source can proceed to dry-run only after parser assignment.
```

### Test seeds

```text
TC-UC-016-01: Assign parser and valid defaults.
TC-UC-016-02: Assign invalid CEFR default and expect rejection.
TC-UC-016-03: Manifest uses filename without source_id and expect failure.
TC-UC-016-04: Source remains parser_pending when no parser exists.
```

---

## UC-017 — Admin Imports Validated Batch into Canonical Storage

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Import Pipeline, Canonical Validator, Production Database, Audit Log |
| Phase | MVP |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-IMP-006, SRS-IMP-008, SRS-IMP-009, SRS-IMP-010, SRS-IMP-014, SRS-DATA-001, SRS-DATA-002, SRS-DATA-011, SRS-DATA-012, SRS-DATA-016, SRS-DB-001, SRS-DB-002, SRS-DB-003, NFR-REL-002 |

### Goal

Persist validated normalized quiz candidates as canonical records while preserving source traceability and import batch history.

### Trigger

Dry-run passed and admin approves real import.

### Preconditions

- Source has dry-run report.
- Duplicate/conflict decisions are resolved or quarantined.
- Import manifest is stable.
- Database migrations are applied.
- Admin is authorized.

### Main flow

1. Admin starts real import for source or batch.
2. System verifies source checksum matches dry-run baseline or records changed source state.
3. Import pipeline parses and normalizes rows using same manifest configuration.
4. Canonical validator validates items.
5. Valid items are inserted into canonical storage with status `imported` or `normalized`.
6. Each item receives internal ID, source_id, source locator, import_batch_id and content_hash.
7. Invalid rows are quarantined/skipped with reason.
8. Import batch report is stored.
9. Existing production data is not corrupted by failures.

### Alternate flows

- **A1: Source changed after dry-run.** System requires new dry-run or explicit controlled override.
- **A2: Partial import allowed.** Valid items are imported; invalid rows quarantined.
- **A3: Batch rollback/quarantine.** Import is reversible or quarantined before activation if policy requires.

### Exception flows

- **E1: Database constraint failure.** Import stops or quarantines affected rows; existing data remains safe.
- **E2: Duplicate active content hash.** Item skipped or versioned per duplicate policy.
- **E3: Unauthorized import.** Denied and logged.

### Postconditions

- Imported items exist in canonical storage.
- Items are not automatically deliverable unless approved/published.
- Import batch is traceable.

### Acceptance criteria

```text
AC-UC-017-01: Imported item has internal ID.
AC-UC-017-02: Imported item has source_id and import_batch_id.
AC-UC-017-03: Imported item has content_hash.
AC-UC-017-04: Imported item starts non-production status.
AC-UC-017-05: Failed import does not corrupt existing data.
```

### Test seeds

```text
TC-UC-017-01: Import valid batch and verify items/status/source traceability.
TC-UC-017-02: Import with invalid row and verify quarantine.
TC-UC-017-03: Change source after dry-run and verify required re-run.
TC-UC-017-04: Simulate DB failure and verify existing data unchanged.
```

---

## UC-018 — Admin Publishes Approved Batch

| Field | Value |
|---|---|
| Primary actor | Content Admin / Product Owner |
| Supporting systems | Status Workflow, Admin Interface, Audit Log, Selection Engine |
| Phase | Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-STAT-002, SRS-STAT-005, SRS-STAT-006, SRS-STAT-010, SRS-ADM-004, SRS-ADM-006, SRS-SEL-002 |

### Goal

Move a group of approved items into `published` status for active delivery scope.

### Trigger

Product owner or content admin decides approved items are ready for a pilot/consumer/product launch.

### Preconditions

- Items are approved.
- Batch is within allowed scope.
- Admin has permission.
- Publication gate is satisfied.

### Main flow

1. Admin selects approved batch.
2. System shows batch summary: counts, levels, themes, sources, validation flags and issue reports.
3. Admin confirms publication scope.
4. System verifies all selected items are eligible.
5. System changes status to `published`.
6. System records batch status transition with actor, timestamp and reason.
7. Selection engine can now include published items.

### Alternate flows

- **A1: Some items have issue flags.** System excludes flagged items or requires explicit review.
- **A2: Publish by topic/level.** Batch publication uses taxonomy filters.
- **A3: Controlled pilot publication.** Items are published only for internal/pilot consumers if deployment model supports scoped publication.

### Exception flows

- **E1: Non-approved item selected.** System blocks or excludes it.
- **E2: Missing audit reason.** System blocks if required.
- **E3: Unauthorized actor.** Denied and logged.

### Postconditions

- Batch is production-eligible.
- Publication audit exists.
- Delivery still respects consumer rules, repeat and quota.

### Acceptance criteria

```text
AC-UC-018-01: Only approved items can be batch-published.
AC-UC-018-02: Status changes are logged.
AC-UC-018-03: Published items become eligible for selection.
AC-UC-018-04: Flagged/ineligible items are not silently published.
```

### Test seeds

```text
TC-UC-018-01: Publish approved batch and verify eligibility.
TC-UC-018-02: Attempt to publish imported item and expect rejection.
TC-UC-018-03: Publish batch with flagged item and verify block/exclusion.
```

---

## UC-019 — System Blocks Draft Item Delivery

| Field | Value |
|---|---|
| Primary actor | Selection Engine / API Service |
| Supporting systems | Status Workflow, API Service, Test Suite |
| Phase | MVP |
| Priority | P0 |
| Demo value | High |
| SRS mapping | SRS-STAT-003, SRS-STAT-004, SRS-STAT-005, SRS-API-007, SRS-SEL-002, SRS-SEL-006, SRS-DEMO-005, NFR-QA-002, NFR-QA-003, NFR-QA-005 |

### Goal

Prove that draft/non-production items cannot be delivered to normal consumers.

### Trigger

Normal consumer requests quiz while only draft or non-production items match requested filters, or test suite intentionally seeds draft candidates.

### Preconditions

- Draft item exists.
- Normal consumer exists.
- Selection filters would otherwise match the draft item.

### Main flow

1. Consumer requests next quiz.
2. Selection engine builds candidate pool.
3. Selection engine applies status filter.
4. Draft item is excluded.
5. If no approved/published item remains, system returns no-eligible-item reason.
6. System records decision metadata where configured.

### Alternate flows

- **A1: Approved item also matches.** Approved item may be returned; draft remains excluded.
- **A2: Internal demo override.** Draft example can be shown only to internal demo context with explicit marking.

### Exception flows

- **E1: Draft item returned to normal consumer.** This is a P0 defect and launch blocker.
- **E2: Status missing.** Item fails validation and is excluded.

### Postconditions

- Normal consumer receives no draft item.
- Test evidence supports publication rule.

### Acceptance criteria

```text
AC-UC-019-01: Draft item is excluded from API delivery.
AC-UC-019-02: Draft item is excluded from Telegram delivery.
AC-UC-019-03: No-eligible-item error is returned when only draft candidates exist.
AC-UC-019-04: Test failure blocks MVP acceptance.
```

### Test seeds

```text
TC-UC-019-01: Seed draft matching item and verify API does not return it.
TC-UC-019-02: Seed draft matching item and verify Telegram worker does not send it.
TC-UC-019-03: Seed only draft items and verify no eligible result.
```

---

## UC-020 — Admin Configures Consumer Rules

| Field | Value |
|---|---|
| Primary actor | Content Admin / Consumer Owner |
| Supporting systems | Consumer Management, Entitlement Engine, Selection Engine, Audit Log |
| Phase | MVP/Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-CONS-001, SRS-CONS-002, SRS-CONS-003, SRS-CONS-004, SRS-CONS-005, SRS-CONS-006, SRS-CONS-008, SRS-SEL-003, SRS-SEL-004, SRS-SEL-005 |

### Goal

Configure what a consumer is allowed to receive and how often.

### Trigger

New consumer is created or existing consumer settings need update.

### Preconditions

- Consumer exists or is being created.
- Admin is authorized.
- Taxonomy values exist.

### Main flow

1. Admin opens consumer settings.
2. Admin sets consumer type: Telegram channel, bot, web app, school account, external API client or internal demo client.
3. Admin sets status: active, suspended, blocked or pilot equivalent.
4. Admin configures allowed CEFR levels and themes.
5. Admin configures daily/monthly limits and repeat policy.
6. Admin configures schedule if consumer is scheduled channel.
7. System validates rules against taxonomy and entitlement constraints.
8. System saves configuration and logs change.
9. Selection engine uses rules for future requests.

### Alternate flows

- **A1: Safe defaults.** Consumer inherits default rules until explicit rules set.
- **A2: Demo consumer.** Internal demo consumer is marked clearly and may use deterministic selection.
- **A3: Suspended consumer.** Rules remain stored but delivery is blocked.

### Exception flows

- **E1: Invalid level/theme.** System rejects configuration.
- **E2: Limit exceeds plan.** System blocks or requires entitlement update.
- **E3: Unauthorized actor.** Denied and logged.

### Postconditions

- Consumer rules are active or safely stored.
- Future selection respects rules.
- Rule change is auditable.

### Acceptance criteria

```text
AC-UC-020-01: Consumer has type and status.
AC-UC-020-02: Active consumer has rules or safe defaults.
AC-UC-020-03: Invalid taxonomy values are rejected.
AC-UC-020-04: Rule changes are logged.
AC-UC-020-05: Selection respects configured levels/themes/repeat.
```

### Test seeds

```text
TC-UC-020-01: Configure active Telegram channel rules.
TC-UC-020-02: Configure invalid theme and expect rejection.
TC-UC-020-03: Suspend consumer and verify delivery denied.
TC-UC-020-04: Change repeat policy and verify selection behavior.
```

---

## UC-021 — Telegram Worker Handles Send Failure

| Field | Value |
|---|---|
| Primary actor | Telegram Worker |
| Supporting systems | Telegram Adapter, Delivery Log, Monitoring, Scheduler |
| Phase | Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-TG-004, SRS-TG-007, SRS-TG-009, SRS-TG-010, NFR-REL-001, NFR-REL-006, NFR-OPS-005, NFR-OPS-010 |

### Goal

Handle Telegram API send failures without silent data loss or duplicate uncontrolled sends.

### Trigger

Telegram send operation fails due to network, API, permission, payload or channel issue.

### Preconditions

- Worker attempted delivery.
- Delivery candidate exists.
- Delivery logging is enabled.

### Main flow

1. Worker attempts Telegram send.
2. Telegram API returns failure or request times out.
3. Worker classifies failure reason.
4. Worker records delivery failure with consumer, item, timestamp and reason.
5. Worker applies retry policy if safe.
6. Retry uses idempotency/duplicate protection where possible.
7. Monitoring/alerting can surface repeated failures.

### Alternate flows

- **A1: Payload invalid.** Worker does not retry until compatibility issue is fixed.
- **A2: Channel permission missing.** Worker records consumer configuration failure.
- **A3: Temporary network failure.** Worker retries within safe window.

### Exception flows

- **E1: Worker crashes before logging.** Recovery process identifies pending/reserved delivery and resolves according to policy.
- **E2: Duplicate post risk.** Worker avoids retry or marks manual review required.

### Postconditions

- Failure is not silent.
- Delivery history is accurate.
- Operations can diagnose issue.

### Acceptance criteria

```text
AC-UC-021-01: Send failure is logged with reason.
AC-UC-021-02: Worker does not silently drop failure.
AC-UC-021-03: Retry policy avoids duplicate uncontrolled sends.
AC-UC-021-04: Repeated failures can be reported.
```

### Test seeds

```text
TC-UC-021-01: Simulate Telegram API error and verify failure log.
TC-UC-021-02: Simulate timeout and verify retry policy.
TC-UC-021-03: Simulate invalid payload and verify no retry.
```

---

## UC-022 — Telegram Worker Runs Simulated Delivery

| Field | Value |
|---|---|
| Primary actor | Telegram Worker / Demo Owner |
| Supporting systems | Selection Engine, Telegram Adapter, API Service, Demo Logs |
| Phase | Pilot/Demo |
| Priority | P1 |
| Demo value | High |
| SRS mapping | SRS-TG-009, SRS-DEMO-004, SRS-DEMO-006, SRS-DEMO-007, IF-TG-004, IF-TG-005 |

### Goal

Generate a Telegram-compatible quiz payload without sending it to a real channel.

### Trigger

Demo rehearsal, test run, staging validation or channel configuration check.

### Preconditions

- Demo/test consumer exists.
- Eligible item exists or deterministic demo item is configured.
- Worker is in dry-run mode.

### Main flow

1. Demo owner or worker starts simulated delivery.
2. Worker requests item through API/selection engine.
3. Adapter converts item to Telegram quiz/poll payload.
4. Adapter validates compatibility.
5. System outputs payload preview and expected delivery metadata.
6. System records dry-run event if configured.
7. No real Telegram message is sent.

### Alternate flows

- **A1: Incompatible item.** Simulation fails with clear reason.
- **A2: Deterministic demo mode.** Same item is selected for repeatable demo.
- **A3: No eligible item.** Simulation returns no-eligible-item reason.

### Exception flows

- **E1: Worker accidentally sends in dry-run.** This is a P0 process defect.
- **E2: Payload reveals hidden correct answer in wrong mode.** Simulation blocks or flags issue.

### Postconditions

- Demo/test payload exists.
- Real channel is untouched.
- Demo evidence can be shown safely.

### Acceptance criteria

```text
AC-UC-022-01: Simulated delivery does not send Telegram message.
AC-UC-022-02: Payload is Telegram-compatible.
AC-UC-022-03: Selection still uses governed path.
AC-UC-022-04: Dry-run output can be used in demo.
```

### Test seeds

```text
TC-UC-022-01: Run Telegram dry-run and verify no send.
TC-UC-022-02: Verify generated payload structure.
TC-UC-022-03: Run dry-run with no eligible items.
```

---

## UC-023 — Admin Grants Manual Entitlement Override

| Field | Value |
|---|---|
| Primary actor | Billing/Admin Owner |
| Supporting systems | Entitlement Engine, Audit Log, Consumer Management |
| Phase | Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-BILL-001, SRS-BILL-005, SRS-BILL-006, SRS-BILL-007, SRS-BILL-009, NFR-SEC-007 |

### Goal

Grant controlled temporary access to a consumer without relying on payment provider integration.

### Trigger

Manual pilot, demo, school trial, support case or billing exception.

### Preconditions

- Consumer exists.
- Admin has entitlement override permission.
- Reason and validity period are required by policy.

### Main flow

1. Billing/admin owner opens consumer entitlement record.
2. Admin selects feature/plan/limit/scope.
3. Admin sets validity period and reason.
4. System validates override policy.
5. System creates entitlement record.
6. System logs actor, timestamp, reason and scope.
7. API/selection uses entitlement for future access decisions.

### Alternate flows

- **A1: Demo-only entitlement.** Access is limited to internal demo consumer.
- **A2: School trial.** Entitlement grants limited group/school features.
- **A3: Emergency revocation.** Admin disables override immediately.

### Exception flows

- **E1: Override without expiry.** System rejects unless explicit policy allows.
- **E2: Unauthorized actor.** Denied and logged.
- **E3: Override exceeds allowed scope.** System blocks or requires higher approval.

### Postconditions

- Consumer has explicit entitlement.
- Override is auditable.
- Expiry/revocation is enforceable.

### Acceptance criteria

```text
AC-UC-023-01: Manual override creates internal entitlement.
AC-UC-023-02: Override has scope and validity period.
AC-UC-023-03: Override has audit trail.
AC-UC-023-04: Revocation blocks future delivery.
```

### Test seeds

```text
TC-UC-023-01: Grant trial entitlement and verify delivery allowed.
TC-UC-023-02: Expire entitlement and verify delivery denied.
TC-UC-023-03: Attempt unauthorized override and expect denial.
```

---

## UC-024 — Security Owner Audits Object-Level Authorization

| Field | Value |
|---|---|
| Primary actor | Security Owner |
| Supporting systems | API Service, Audit Logs, Test Suite, Consumer Management |
| Phase | MVP/Pilot |
| Priority | P0 |
| Demo value | Medium |
| SRS mapping | SRS-API-008, SRS-API-009, SRS-CONS-007, SRS-AN-010, NFR-SEC-003, NFR-SEC-004, NFR-SEC-005, NFR-SEC-007, NFR-QA-007 |

### Goal

Verify that one consumer cannot access another consumerʼs data, rules, deliveries, analytics or entitlements.

### Trigger

Security review, CI security test, pre-pilot gate or incident investigation.

### Preconditions

- At least two consumers exist.
- API authorization layer is implemented.
- Logs/tests are available.

### Main flow

1. Security owner or test suite creates/uses Consumer A and Consumer B.
2. Authorized token/key for Consumer A requests Consumer A resource.
3. System allows valid request.
4. Same token/key requests Consumer B resource.
5. System denies access.
6. Denial is logged as security-relevant event.
7. Security owner reviews test result and logs.

### Alternate flows

- **A1: Admin role.** Admin access is allowed only if role permits and action is logged.
- **A2: Public-safe aggregate report.** Aggregates may be accessible if they contain no private consumer data.
- **A3: Suspended consumer.** Access is denied even if token still exists.

### Exception flows

- **E1: Cross-consumer access succeeds.** This is P0 security defect and launch blocker.
- **E2: Denial not logged.** Security logging requirement fails.

### Postconditions

- Authorization control is verified or defect is filed.
- Launch gate can use evidence.

### Acceptance criteria

```text
AC-UC-024-01: Consumer A cannot access Consumer B data.
AC-UC-024-02: Admin access requires admin permission.
AC-UC-024-03: Security denial is logged.
AC-UC-024-04: Test failure blocks launch for affected API scope.
```

### Test seeds

```text
TC-UC-024-01: Cross-consumer rule access denied.
TC-UC-024-02: Cross-consumer analytics access denied.
TC-UC-024-03: Suspended consumer token denied.
TC-UC-024-04: Admin access succeeds and logs actor.
```

---

## UC-025 — Taxonomy Owner Updates Taxonomy Through Change Control

| Field | Value |
|---|---|
| Primary actor | Taxonomy Owner |
| Supporting systems | Taxonomy Files, SRS/Docs, Import Pipeline, Validator, CI |
| Phase | Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-TAX-001, SRS-TAX-002, SRS-TAX-003, SRS-TAX-004, SRS-TAX-008, SRS-TAX-009, SRS-DATA-018, NFR-ENG-005, NFR-ENG-007 |

### Goal

Update CEFR/theme/objective/pattern/tag taxonomy without breaking existing corpus, validators, reports or API behavior.

### Trigger

New content pack, new educational need, missing theme, refined objective/pattern model or roadmap requirement.

### Preconditions

- Change proposal exists.
- Current taxonomy is version-controlled.
- Impact on existing items and reports is understood.

### Main flow

1. Taxonomy owner proposes change.
2. Proposal states rationale, affected taxonomy files, affected import defaults, affected items and migration needs.
3. Validator/schema impact is reviewed.
4. Change is made in version-controlled files.
5. Tests/checks run: taxonomy validity, import validation, coverage report, API compatibility.
6. SRS/docs are updated if requirement-impacting.
7. Change is merged through approved process.
8. Generated reports are refreshed.

### Alternate flows

- **A1: Add tag only.** Low-impact change may not require schema migration.
- **A2: Add new theme.** Requires coverage and import manifest updates.
- **A3: Rename theme.** Requires migration or alias strategy.

### Exception flows

- **E1: Change breaks existing items.** CI/test blocks merge.
- **E2: Unrecognized levels introduced.** Change rejected unless CEFR policy formally changes.
- **E3: No documentation update.** Change is blocked if requirement-impacting.

### Postconditions

- Taxonomy change is versioned.
- Validators and reports remain consistent.
- Future sources can use updated taxonomy.

### Acceptance criteria

```text
AC-UC-025-01: Taxonomy change is version-controlled.
AC-UC-025-02: Existing valid items remain valid or migration is provided.
AC-UC-025-03: Coverage report still runs.
AC-UC-025-04: Requirement-impacting change updates docs/SRS.
```

### Test seeds

```text
TC-UC-025-01: Add valid tag and run validation.
TC-UC-025-02: Add invalid CEFR and expect failure.
TC-UC-025-03: Rename theme without migration and expect check failure.
```

---

## UC-026 — Admin Rejects or Blocks Candidate Source

| Field | Value |
|---|---|
| Primary actor | Content Admin |
| Supporting systems | Source Registry, Import Manifest, Audit Log, Admin Interface |
| Phase | MVP/Pilot |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-ONB-005, SRS-ONB-006, SRS-ONB-009, SRS-SRC-007, SRS-ADM-012 |

### Goal

Reject or block a source file that should not enter production workflow.

### Trigger

Source is invalid, duplicated, low quality, wrong format, unsafe, unauthorized or not aligned with taxonomy/product scope.

### Preconditions

- Source is registered or candidate.
- Admin is authorized.
- Reason for rejection/blocking is available.

### Main flow

1. Admin opens source record.
2. System shows source state, checksum, dry-run/import reports and related items if any.
3. Admin selects `rejected` or `blocked`.
4. Admin provides reason code and note.
5. System updates source state.
6. System prevents production delivery of items from blocked source unless previously approved items are separately handled by policy.
7. System records audit trail.
8. Inventory/reporting preserves historical source record.

### Alternate flows

- **A1: Rejected before import.** No item records exist; only source history persists.
- **A2: Blocked after import.** Related items are moved to review/blocked according to source block policy.
- **A3: Archived instead of rejected.** Source is valid but no longer active.

### Exception flows

- **E1: Source has published items.** System requires explicit impact decision.
- **E2: Missing reason.** System blocks transition if reason required.
- **E3: Unauthorized actor.** Denied and logged.

### Postconditions

- Source is no longer eligible for normal onboarding/import/delivery path.
- Reason is auditable.
- Historical traceability remains.

### Acceptance criteria

```text
AC-UC-026-01: Candidate source can be rejected with reason.
AC-UC-026-02: Blocked source cannot produce normal delivery items.
AC-UC-026-03: Historical source record remains.
AC-UC-026-04: Published item impact requires explicit decision.
```

### Test seeds

```text
TC-UC-026-01: Reject candidate source and verify no import allowed.
TC-UC-026-02: Block source after import and verify items excluded/reviewed.
TC-UC-026-03: Attempt source rejection without reason and expect block.
```

---

## UC-027 — External App Integrates Using OpenAPI Contract

| Field | Value |
|---|---|
| Primary actor | API Consumer Owner |
| Supporting systems | OpenAPI Contract, API Service, Auth/Keys, Developer Docs |
| Phase | Pilot |
| Priority | P1 |
| Demo value | High |
| SRS mapping | SRS-API-001, SRS-API-002, SRS-API-012, SRS-API-013, SRS-API-017, SRS-DOC-006, IF-API-001, IF-API-002, IF-API-003, IF-API-004, IF-API-006, NFR-ENG-006 |

### Goal

Allow an external app or partner to understand and consume API Quiz Bank through a formal API contract rather than source code inspection.

### Trigger

External app wants to integrate quiz delivery or a demo needs to show API product surface.

### Preconditions

- OpenAPI contract exists.
- API keys/auth model exists for protected endpoints.
- Consumer is created and active.
- Docs define schemas, auth, errors and status codes.

### Main flow

1. API Consumer Owner reads OpenAPI contract.
2. Consumer obtains API credentials through allowed process.
3. Consumer tests health/topic endpoints.
4. Consumer calls next quiz endpoint.
5. API returns public-safe quiz item schema.
6. Consumer submits attempt if applicable.
7. Consumer handles machine-readable error responses.
8. Integration goes through pilot approval before production access.

### Alternate flows

- **A1: Sandbox/demo credentials.** Consumer uses limited demo environment.
- **A2: Public documentation only.** Consumer can inspect docs but not access production data.
- **A3: Contract test.** CI validates consumer or SDK against OpenAPI spec.

### Exception flows

- **E1: OpenAPI missing endpoint schema.** External access blocked until contract updated.
- **E2: API implementation differs from contract.** Contract test fails.
- **E3: Consumer requests admin-only data.** API denies.

### Postconditions

- External integration is contract-based.
- API product surface is demonstrable.
- Implementation and docs stay aligned.

### Acceptance criteria

```text
AC-UC-027-01: OpenAPI contract exists before external access.
AC-UC-027-02: Contract documents auth, schemas, errors and status codes.
AC-UC-027-03: External consumer can request next quiz using documented endpoint.
AC-UC-027-04: Public-safe data boundary is enforced.
AC-UC-027-05: API changes update OpenAPI contract.
```

### Test seeds

```text
TC-UC-027-01: Validate OpenAPI contract.
TC-UC-027-02: Generate sample client or run contract test.
TC-UC-027-03: Verify endpoint response conforms to schema.
TC-UC-027-04: Verify admin-only fields absent in public response.
```

---

## UC-028 — Learner Requests Personal Quiz by Level/Topic

| Field | Value |
|---|---|
| Primary actor | Learner |
| Supporting systems | Web/Bot App, API Service, Selection Engine, Attempts Store, Entitlement Engine |
| Phase | Pilot/Beta |
| Priority | P2 |
| Demo value | Medium |
| SRS mapping | SRS-API-005, SRS-API-006, SRS-SEL-001, SRS-SEL-003, SRS-SEL-004, SRS-SEL-005, SRS-CONS-002, SRS-AN-003, SRS-BILL-004 |

### Goal

Allow an individual learner to receive quiz items matched to selected CEFR level and topic.

### Trigger

Learner chooses level/topic in web app, bot or other consumer interface.

### Preconditions

- Learner session or consumer context exists.
- Requested level/topic is valid.
- Entitlement/quota allows delivery.
- Eligible items exist.

### Main flow

1. Learner selects CEFR level and topic.
2. Consumer interface calls API next quiz or session endpoint.
3. API validates request and consumer/user context.
4. Selection engine chooses eligible item.
5. Learner receives question and options.
6. Learner answers.
7. Attempt is submitted and recorded if supported.
8. Learner receives allowed feedback/explanation.

### Alternate flows

- **A1: Adaptive future mode.** Selection can use past attempts after enough data exists.
- **A2: Free plan limit.** Learner receives limited daily quizzes.
- **A3: Topic unavailable.** System suggests available adjacent topics or returns no-eligible-item reason.

### Exception flows

- **E1: Quota exceeded.** Learner sees upgrade/limit explanation.
- **E2: Invalid level/topic.** Request rejected.
- **E3: Attempt submission fails.** User is informed; system avoids duplicate incorrect records.

### Postconditions

- Learner receives controlled content or clear denial.
- Attempt/usage data may improve analytics.

### Acceptance criteria

```text
AC-UC-028-01: Learner receives only eligible approved/published item.
AC-UC-028-02: Request respects selected level/topic.
AC-UC-028-03: Quota/entitlement applies.
AC-UC-028-04: Attempt can be recorded where supported.
```

### Test seeds

```text
TC-UC-028-01: Learner requests A1 topic quiz and receives valid item.
TC-UC-028-02: Learner exceeds free quota and receives denial.
TC-UC-028-03: Learner submits answer and attempt stored.
```

---

## UC-029 — Product Owner Reviews Delivery and Usage Analytics

| Field | Value |
|---|---|
| Primary actor | Product Owner |
| Supporting systems | Analytics Service, Delivery Log, Attempts Store, Billing Usage Logs |
| Phase | Pilot/Beta |
| Priority | P1 |
| Demo value | Medium |
| SRS mapping | SRS-AN-001, SRS-AN-002, SRS-AN-003, SRS-AN-004, SRS-AN-006, SRS-AN-007, SRS-AN-009, SRS-AN-010, SRS-AN-011, NFR-OPS-010 |

### Goal

Review how the platform is used and whether delivery, repeat, quota and learning metrics behave as expected.

### Trigger

Product review, pilot review, demo preparation, billing analysis or quality improvement cycle.

### Preconditions

- Delivery records exist.
- Attempt records may exist.
- Product owner is authorized for analytics scope.

### Main flow

1. Product owner opens analytics/report.
2. System shows delivery counts by consumer/channel/date/status.
3. System shows repeat-policy events or attempted violations.
4. System shows quota usage and denials.
5. If attempts exist, system shows correctness rates by item/topic/level.
6. System protects private user/consumer data according to authorization.
7. Product owner identifies improvements, risks and roadmap needs.

### Alternate flows

- **A1: MVP analytics only.** Delivery and corpus reports exist; attempt analytics planned.
- **A2: Consumer-specific report.** Owner sees only authorized consumer scope.
- **A3: Demo analytics.** Internal demo data is clearly marked.

### Exception flows

- **E1: Analytics attempts to expose unauthorized data.** System blocks.
- **E2: Missing delivery logs.** Report marks data incomplete and triggers operational fix.

### Postconditions

- Product decisions are informed by evidence.
- Demo/operations can show platform feedback loop.

### Acceptance criteria

```text
AC-UC-029-01: Delivery report is available.
AC-UC-029-02: Quota usage/denial can be reported.
AC-UC-029-03: Repeat-policy violations or attempts can be reported when tracked.
AC-UC-029-04: Analytics respects authorization.
AC-UC-029-05: Demo can show basic analytics evidence.
```

### Test seeds

```text
TC-UC-029-01: Generate delivery report for demo consumer.
TC-UC-029-02: Generate quota usage report.
TC-UC-029-03: Attempt unauthorized analytics access and verify denial.
```

---

## UC-030 — Demo Owner Onboards a Sample Future Source File

| Field | Value |
|---|---|
| Primary actor | Demo Owner / Content Admin |
| Supporting systems | Source Registry, Import Manifest, Import Pipeline, Validator, Reports, Status Workflow |
| Phase | Demo |
| Priority | P0 for demo evidence |
| Demo value | Critical |
| SRS mapping | SRS-ONB-001, SRS-ONB-002, SRS-ONB-003, SRS-ONB-004, SRS-ONB-005, SRS-ONB-006, SRS-ONB-007, SRS-ONB-008, SRS-ONB-010, SRS-DEMO-009, SRS-DEMO-011 |

### Goal

Prove that API Quiz Bank can safely accept new quiz files in the future without breaking governance or delivery.

### Trigger

Stanford-style demo includes future expansion proof, or a pilot source pack is prepared.

### Preconditions

- Sample future source file exists.
- Demo owner is authorized.
- Parser profile exists or parser_pending path is ready to show.
- Onboarding workflow is documented.

### Main flow

1. Demo owner introduces principle: `New quiz files are onboarded, not dropped.`
2. Admin registers sample source file.
3. System assigns stable source_id and checksum.
4. Admin adds source to import manifest with parser/defaults.
5. System runs dry-run import.
6. System produces onboarding/import report.
7. System shows validation results, duplicate/conflict categories and accepted item count.
8. System imports or simulates import of valid items as non-production status.
9. System shows that new source items are not delivered until status workflow approves/publishes them.
10. Demo owner explains how this supports scale beyond current corpus baseline.

### Alternate flows

- **A1: Parser pending demo.** If parser does not exist, demo shows controlled parser_pending state rather than forcing bad import.
- **A2: Invalid sample file.** Demo shows rejection/quarantine path as proof of governance.
- **A3: Dry-run only.** Demo stops at report stage if real import is not ready.

### Exception flows

- **E1: Source cannot be registered.** Demo switches to recorded artifact and marks limitation.
- **E2: Demo accidentally publishes new source items.** This is a governance defect.
- **E3: Unknown taxonomy values silently accepted.** This is a P0 validation defect.

### Postconditions

- Future source onboarding path is demonstrated or clearly artifact-backed.
- New file did not bypass governance.
- Demo proves scalability of content platform.

### Acceptance criteria

```text
AC-UC-030-01: Sample source receives source_id and checksum.
AC-UC-030-02: Sample source appears in inventory/manifest.
AC-UC-030-03: Dry-run report is generated.
AC-UC-030-04: New items remain non-production until approved/published.
AC-UC-030-05: Demo clearly distinguishes implemented and planned parts.
```

### Test seeds

```text
TC-UC-030-01: Onboard valid sample future source through dry-run.
TC-UC-030-02: Onboard invalid sample and verify rejection/quarantine.
TC-UC-030-03: Verify sample source items not delivered before approval.
TC-UC-030-04: Show onboarding report in demo rehearsal.
```

---

## 9. End-to-End Scenario Chains

### 9.1. Source-to-delivery happy path

```text
UC-001 Register source
  → UC-016 Assign parser/manifest defaults
  → UC-002 Dry-run import
  → UC-003 Resolve duplicates/conflicts
  → UC-017 Import validated batch
  → UC-004 Approve item
  → UC-018 Publish batch
  → UC-020 Configure consumer rules
  → UC-005 API consumer requests next quiz
  → UC-006 Consumer submits attempt
  → UC-029 Product owner reviews analytics
```

### 9.2. Future file onboarding demo path

```text
UC-030 Demo owner onboards sample future source
  → UC-001 Register source
  → UC-016 Assign parser
  → UC-002 Dry-run import
  → UC-017 Import as non-production
  → UC-019 Prove draft/non-production not delivered
  → UC-015 Demo owner explains scale path
```

### 9.3. Telegram pilot path

```text
UC-020 Configure Telegram consumer rules
  → UC-005 Selection/API path
  → UC-007 Scheduled Telegram quiz
  → UC-021 Failure handling if needed
  → UC-029 Delivery analytics
```

### 9.4. Paid access path

```text
UC-013 Billing webhook updates entitlement
  → UC-020 Consumer rules active
  → UC-005 Next quiz delivered
  → UC-008 Quota exceeded after limit
  → UC-023 Manual override if approved
```

### 9.5. Quality feedback path

```text
UC-006 Attempt recorded
  → UC-010 User reports issue
  → UC-011 Admin retires problematic item
  → UC-029 Analytics reflects issue/retirement
```

### 9.6. Production reliability path

```text
NFR monitoring detects incident
  → UC-014 Operations owner restores backup
  → health/readiness checks
  → delivery resumes
  → incident report updated
```

---

## 10. Use Case to SRS Traceability Matrix

| Use Case | Core SRS Areas | Key Acceptance Evidence |
|---|---|---|
| UC-001 | SRC, ONB, ADM | source_id, checksum, non-production state, inventory record |
| UC-002 | IMP, ADM, QA | dry-run report, no production writes, validation errors |
| UC-003 | IMP, DATA, DB, ADM | duplicate/conflict decisions and audit trail |
| UC-004 | DATA, STAT, ADM | item approved only after schema/metadata check |
| UC-005 | API, SEL, CONS, BILL, AN | approved item returned, authorization/quota/repeat enforced |
| UC-006 | API, AN, SEC | attempt stored, invalid/unauthorized attempts rejected |
| UC-007 | TG, SEL, CONS, AN | Telegram delivery uses API/selection, delivery logged |
| UC-008 | BILL, API, SEL | quota denial error and usage log |
| UC-009 | TAX, SEL, API, CONS | level/topic pack generated or no-eligible reason |
| UC-010 | AN, ADM, STAT | item issue report stored and visible for review |
| UC-011 | STAT, ADM, DB | retired item excluded; history preserved |
| UC-012 | TAX, AN, DOC | coverage report by status/level/theme/matrix |
| UC-013 | BILL, SEC | provider event updates internal entitlement only after verification |
| UC-014 | OPS, DB, REL | tested restore and verification log |
| UC-015 | DEMO, DOC, QA | rehearsed demo with artifacts and honest scope |
| UC-016 | IMP, ONB, TAX | manifest uses source_id, parser and valid defaults |
| UC-017 | IMP, DATA, DB | imported canonical items with traceability and non-production status |
| UC-018 | STAT, ADM, SEL | approved batch published with audit trail |
| UC-019 | STAT, API, SEL, QA | draft/non-production item never delivered |
| UC-020 | CONS, SEL | consumer rules saved and applied |
| UC-021 | TG, OPS, REL | Telegram failure logged with safe retry behavior |
| UC-022 | TG, DEMO | Telegram-compatible dry-run payload without sending |
| UC-023 | BILL, SEC | manual entitlement override with audit trail |
| UC-024 | API, CONS, SEC, QA | object-level authorization tests pass |
| UC-025 | TAX, DATA, ENG | taxonomy change passes validation/change control |
| UC-026 | ONB, SRC, ADM | rejected/blocked source cannot enter delivery |
| UC-027 | API, DOC, ENG | OpenAPI contract enables consumer integration |
| UC-028 | API, SEL, AN, BILL | learner receives level/topic quiz and attempt flow |
| UC-029 | AN, OPS | delivery/usage reports available and authorized |
| UC-030 | ONB, DEMO | sample future source onboarding demonstrated |

---

## 11. Use Case to Test Category Matrix

| Test Category | Use Cases Covered |
|---|---|
| Data validation tests | UC-002, UC-004, UC-017, UC-019, UC-025 |
| Import pipeline tests | UC-001, UC-002, UC-003, UC-016, UC-017, UC-026, UC-030 |
| Schema tests | UC-002, UC-004, UC-017, UC-027 |
| Selection engine unit tests | UC-005, UC-007, UC-009, UC-019, UC-020, UC-028 |
| API contract tests | UC-005, UC-006, UC-008, UC-027, UC-028 |
| API authorization tests | UC-005, UC-006, UC-024, UC-029 |
| Telegram adapter tests | UC-007, UC-021, UC-022 |
| Delivery logging tests | UC-005, UC-007, UC-021, UC-029 |
| Billing/quota tests | UC-008, UC-013, UC-023 |
| Admin workflow tests | UC-001, UC-003, UC-004, UC-011, UC-016, UC-018, UC-026 |
| Analytics/report tests | UC-012, UC-029 |
| Migration/backup tests | UC-014, UC-025 |
| End-to-end demo tests | UC-015, UC-030 |

---

## 12. MVP Use Case Acceptance Set

MVP cannot be accepted unless these use cases have at least documented/manual acceptance evidence:

```text
UC-001 Admin registers a new source file
UC-002 Admin runs dry-run import
UC-004 Admin approves imported quiz item
UC-005 API consumer requests next quiz
UC-008 Consumer exceeds quota or simulated entitlement denial
UC-012 Product owner reviews corpus coverage
UC-016 Admin assigns parser profile and manifest defaults
UC-017 Admin imports validated batch into canonical storage
UC-019 System blocks draft item delivery
UC-020 Admin configures consumer rules
UC-024 Security owner audits object-level authorization
```

For Stanford-style demo readiness, these must also be rehearsed or artifact-backed:

```text
UC-007 Telegram channel receives scheduled quiz or dry-run equivalent
UC-015 Demo owner executes Stanford-style demo
UC-022 Telegram worker runs simulated delivery
UC-027 External app integrates using OpenAPI contract
UC-030 Demo owner onboards a sample future source file
```

---

## 13. Launch Gate Mapping

| Launch Gate | Required Use Cases |
|---|---|
| Document Gate | UC-015, UC-027, UC-030 |
| Data Gate | UC-001, UC-012, UC-016, UC-017, UC-019 |
| Import Gate | UC-002, UC-003, UC-016, UC-017, UC-026, UC-030 |
| API Gate | UC-005, UC-006, UC-008, UC-019, UC-024, UC-027 |
| Telegram Gate | UC-007, UC-021, UC-022 |
| Billing/Entitlement Gate | UC-008, UC-013, UC-023 |
| Analytics Gate | UC-006, UC-010, UC-012, UC-029 |
| Operations Gate | UC-014, UC-021, UC-024, UC-029 |
| Demo Gate | UC-015, UC-022, UC-027, UC-030 |
| Production Gate | UC-011, UC-014, UC-024, UC-025, UC-029 |

---

## 14. Data Objects Referenced by Use Cases

The detailed domain model will be defined in `04_domain_model.md`. These objects are referenced here as use-case vocabulary:

```text
source_file
source_inventory_record
import_manifest_entry
parser_profile
import_batch
import_report
validation_error
normalized_quiz_candidate
quiz_item
quiz_option
taxonomy_theme
taxonomy_objective
taxonomy_pattern
quiz_item_status_event
consumer
consumer_rule
entitlement
quota_usage
delivery
attempt
item_issue_report
analytics_report
audit_log
backup_artifact
incident_record
demo_script
```

---

## 15. Security and Privacy Notes Across Use Cases

Security is not a separate afterthought. These rules apply across all use cases:

```text
1. Admin actions require authentication and authorization.
2. Consumer-specific API requests require object-level authorization.
3. API keys and secrets must never appear in docs, logs or demo output.
4. Normal consumers must not see internal source paths.
5. Learner-facing responses must not expose admin-only metadata.
6. Correct answer exposure must match interaction mode.
7. Billing webhook actions require authenticity checks.
8. Manual overrides require audit trail.
9. Analytics must not expose private user/consumer data without authorization.
10. Demo must hide secrets and private identifiers.
```

---

## 16. Change Control for Use Cases

### 16.1. When to update this document

Update `03_use_cases.md` when:

```text
a new major actor is introduced;
a new delivery channel is added;
API behavior changes materially;
source onboarding workflow changes;
status lifecycle changes;
entitlement logic changes;
security boundary changes;
launch/demo scope changes;
SRS adds or changes requirements that need scenario coverage.
```

### 16.2. Change impact checklist

Every meaningful use case change SHOULD answer:

```text
Which SRS requirements are affected?
Which API endpoints are affected?
Which data objects are affected?
Which tests need update?
Which documentation files need update?
Does this affect Stanford-style demo narrative?
Does this affect future source onboarding?
Does this affect the rule that normal consumers receive only approved/published items?
```

---

## 17. Open Questions

These questions should be resolved in later documents or implementation planning:

```text
OQ-UC-001: Which admin workflows will be CLI-only in MVP and which require UI before Pilot?
OQ-UC-002: What exact repeat windows should apply to Telegram channels, learners and school accounts?
OQ-UC-003: Should delivery be logged before send as reservation or after send as confirmed delivery?
OQ-UC-004: What is the first external API consumer type: internal demo client, web app, Telegram worker or partner app?
OQ-UC-005: Which payment provider is preferred for first live billing integration?
OQ-UC-006: What exact MVP target should be used for API response time under expected load?
OQ-UC-007: What is the first source file used for UC-030 future source onboarding demo?
OQ-UC-008: Should teacher quiz packs be exported, delivered through session API or both?
OQ-UC-009: What issue report categories should be available in first beta?
OQ-UC-010: What analytics are safe for public demo and what must remain internal?
```

---

## 18. Reference Standards and Alignment

This document aligns with these standards and reference principles:

| Area | Standard / Reference | Use in this document |
|---|---|---|
| Requirements discipline | Stanford/SLAC-style requirements methodology | goal → requirements → use cases → tests → traceability → change control |
| Language levels | CEFR A1–C2 | canonical level values and teacher/learner filters |
| API contract | OpenAPI Specification | external consumer integration and API testability |
| Data validation | JSON Schema Draft 2020-12 | canonical quiz item validation |
| HTTP error model | RFC 9457 Problem Details | machine-readable API errors |
| API security | OWASP API Security Top 10 | object-level authorization, auth, abuse controls |
| Telegram delivery | Telegram Bot API | poll/quiz compatibility and adapter constraints |
| Engineering governance | GitHub protected branches / CI / CODEOWNERS concepts | change control and merge discipline |
| Database operations | PostgreSQL indexing and durable storage concepts | selection/search/report performance planning |

---

## 19. Use Case Document Acceptance Criteria

This document is accepted when:

```text
AC-DOC-UC-001: It covers all 15 seed use cases required by SRS section 17.
AC-DOC-UC-002: It includes source onboarding for future quiz files.
AC-DOC-UC-003: It includes import, approval, publication, selection, API delivery and Telegram delivery scenarios.
AC-DOC-UC-004: It includes quota/entitlement and object-level authorization scenarios.
AC-DOC-UC-005: It includes analytics, operations and Stanford-style demo scenarios.
AC-DOC-UC-006: It includes acceptance criteria and test seeds for each detailed use case.
AC-DOC-UC-007: It maps use cases to SRS areas and launch gates.
AC-DOC-UC-008: It preserves the rule that raw files are not production delivery surfaces.
AC-DOC-UC-009: It preserves the rule that normal consumers receive only approved/published items.
AC-DOC-UC-010: It clearly distinguishes implemented, pilot, beta, production and demo-critical scenarios.
```

---

## 20. Final Use Case Rule

API Quiz Bank is not ready because a user can see a quiz.

API Quiz Bank is ready when the system can show, for every quiz delivered:

```text
where it came from;
how it was registered;
how it was imported;
which canonical rules it passed;
why it was eligible;
which consumer received it;
which access rule allowed it;
whether repeat/quota rules were respected;
what delivery record was created;
what happened after delivery;
and how the system would safely handle the next new source file.
```

That is the difference between a quiz collection and a Stanford-ready API-first educational platform.
