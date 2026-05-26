# API Quiz Bank — Quality Assurance Strategy

**Документ:** `docs/09_quality_assurance.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational QA and test strategy; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`, `01_product_charter.md`, `02_requirements_srs.md`, `03_use_cases.md`, `04_domain_model.md`, `05_architecture.md`, `06_data_standard.md`, `07_api_standard.md`, `08_security_threat_model.md`  
**Дата:** 2026-04-30  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized QA maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/06_data_standard.md`, `docs/07_api_standard.md`, `docs/08_security_threat_model.md`  
**Наступні документи:** `10_operations.md`, `11_billing_model.md`, `12_analytics_model.md`, `13_stanford_presentation_outline.md`

---

## 0. Executive Summary

`09_quality_assurance.md` визначає Quality Assurance strategy для **API Quiz Bank**.

Цей документ не є декоративним чеклістом. Він є операційним QA contract, який відповідає на питання:

```text
Що саме вважається якістю для API Quiz Bank?
Які речі мають бути перевірені до MVP, Pilot, Beta, Production and Stanford-style demo?
Які тести блокують запуск?
Як requirements перетворюються на acceptance tests?
Як перевіряється, що raw files не стали хаотичним production layer?
Як перевіряється, що draft items не видаються users?
Як перевіряється, що future quiz files onboarded, not dropped?
Як перевіряються API, Telegram, billing, analytics, security, operations?
Які докази треба мати для професійної презентації?
```

API Quiz Bank має стартовий operational baseline:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 canonical themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Цей baseline є стартовим активом, але не proof of production readiness. QA має перевіряти не те, що файли існують, а те, що content asset перетворюється на керовану platform:

```text
source files
  → source registry
  → checksums
  → file inventory
  → import manifest
  → parser profile
  → dry-run import
  → canonical validation
  → duplicate/conflict classification
  → import batch
  → canonical quiz items
  → status workflow
  → production database
  → selection engine
  → versioned API
  → Telegram/web/bot/app/school delivery
  → delivery logs
  → attempts
  → analytics
  → entitlements
  → operations
  → demo evidence
```

Головна QA-теза:

```text
API Quiz Bank is not quality-ready because tests exist.
API Quiz Bank is quality-ready when every release claim can be traced to:
requirement → use case → domain rule → implementation behavior → test result → evidence artifact.
```

Найважливіше QA-правило:

```text
No launch without evidence.
No evidence without traceability.
No traceability without stable requirements and test IDs.
```

---

## 1. Role of This Document

### 1.1. Призначення

Цей документ визначає:

- QA principles;
- test strategy;
- verification methods;
- test ID system;
- test levels;
- test types;
- test artifacts;
- test data and fixtures;
- CI/CD quality gates;
- launch gates;
- release blocking rules;
- defect severity model;
- traceability model;
- Stanford-style demo evidence requirements.

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
implementation / tests / CI / release / operations / demo
```

### 1.3. Що цей документ робить

Цей документ:

```text
1. Перетворює SRS requirements у QA obligations.
2. Перетворює use cases у acceptance test scenarios.
3. Перетворює data/API/security standards у contract tests.
4. Визначає, що саме має пройти перед MVP/Pilot/Beta/Production.
5. Визначає, які порушення автоматично блокують launch.
6. Визначає, як створити evidence package для Stanford-style presentation.
```

### 1.4. Що цей документ не робить

Цей документ не є:

- повторним content audit кожної вже перевіреної вікторини;
- заміною SRS;
- заміною Security Threat Model;
- заміною Operations Runbook;
- повним automation implementation;
- UI test script for every future screen;
- гарантією, що всі future features реалізуються в MVP.

Поточні quiz items вважаються content-verified assets. QA першого етапу перевіряє platform readiness: governance, import, schema, status, delivery safety, API behavior, authorization, entitlements, logging, analytics, operations and demo evidence.

---

## 2. Stanford-Style QA Discipline

### 2.1. Meaning of Stanford-style in this project

У межах API Quiz Bank “Stanford-style” означає інженерну дисципліну, а не формальне схвалення Stanford.

QA має підтримувати ланцюг:

```text
goal
  → needs
  → features
  → requirements
  → use cases
  → domain model
  → architecture
  → data/API/security contracts
  → tests
  → operations
  → demo evidence
  → change control
```

### 2.2. QA принципи

| Principle | Meaning |
|---|---|
| Traceability first | Кожен P0/P1 test має знати, яку requirement/use case/domain rule він перевіряє. |
| Evidence over assertion | “Працює” не приймається без test result, log, report, screenshot, artifact або demo run. |
| Risk-based depth | Найбільше тестування отримують ризики: draft delivery, answer leakage, auth bypass, quota bypass, data corruption. |
| Contract discipline | API/data/security behavior тестується як contract, а не як внутрішня випадковість implementation. |
| Launch gates are real | Gate не є побажанням; він блокує відповідний launch scope. |
| Regression memory | Кожен critical bug породжує regression test. |
| Demo honesty | Demo не має видавати planned features за implemented features. |
| Quality is continuous | QA не закінчується на MVP; вона переходить у monitoring, analytics, operations and incident learning. |

### 2.3. QA definition of done

Feature is QA-ready only when:

```text
requirement exists;
use case or business rule exists;
acceptance criteria exist;
test case exists;
test data or fixture exists;
automated test exists where feasible;
manual/evidence checklist exists where automation is not feasible yet;
negative path is covered;
security/authorization impact is considered;
result is recorded;
known limitations are documented.
```

---

## 3. Quality Thesis

### 3.1. Core quality thesis

```text
Quality for API Quiz Bank is the ability to safely transform verified content
into governed, validated, authorized, logged, measurable and recoverable delivery.
```

### 3.2. What quality means for this product

Quality means:

```text
source traceability exists;
new files are onboarded, not dropped;
import is reproducible;
canonical schema is enforced;
status lifecycle is enforced;
draft/blocked/retired items are not delivered;
selection respects consumer rules and repeat policy;
API responses match contract;
correct answers are exposed only in allowed modes;
entitlements and quotas are enforced;
admin actions are audited;
Telegram compatibility is validated;
delivery is logged;
attempts are recorded correctly;
analytics are scoped and trustworthy;
security controls are verified;
backup/restore is tested;
release claims are evidence-backed.
```

### 3.3. What quality does not mean

Quality does not mean:

```text
all future features implemented;
manual perfection of every UI screen before core data/API work;
complete linguistic re-audit of all existing verified items;
zero future defects;
claiming production readiness based only on corpus size;
claiming platform readiness because a Telegram bot can send one poll;
claiming API readiness because one endpoint returns one question.
```

---

## 4. QA Scope

### 4.1. In scope

QA covers:

```text
documentation quality;
requirements traceability;
source registry and inventory;
future source onboarding;
import manifest and parser profiles;
dry-run import;
canonical data validation;
duplicate/conflict detection;
status lifecycle;
taxonomy and coverage;
production database behavior;
selection engine;
API contract and behavior;
Telegram delivery adapter;
admin workflow;
billing and entitlements;
analytics and reporting;
security controls;
privacy/data exposure;
performance baseline;
CI/CD gates;
backup/restore drills;
release gates;
Stanford-style demo rehearsal.
```

### 4.2. Out of scope for QA MVP

Out of MVP QA unless promoted by change control:

```text
full adaptive learning validation;
IRT/CAT statistical model verification;
AI-generated question evaluation;
full LMS integration testing;
native mobile app testing;
large-scale school deployment testing;
complete public marketplace moderation testing;
full legal/compliance certification.
```

### 4.3. Content audit boundary

QA SHALL NOT re-open a full content audit of all existing verified quiz answers.

QA SHALL verify:

```text
structure;
required fields;
source traceability;
correct answer references are structurally valid;
option count constraints;
CEFR/theme/objective/pattern values;
status eligibility;
Telegram/API compatibility;
no forbidden delivery;
issue-report workflow for flagged items.
```

If a user, teacher, admin or automated rule flags a specific item, that item may enter review. This is targeted quality feedback, not a full re-audit mandate.

---

## 5. Standards Baseline

### 5.1. Internal project standards

QA SHALL align with:

```text
CONSTITUTION.md
00_vision.md
01_product_charter.md
02_requirements_srs.md
03_use_cases.md
04_domain_model.md
05_architecture.md
06_data_standard.md
07_api_standard.md
08_security_threat_model.md
```

### 5.2. External standards and references

The project QA strategy aligns with these external references:

| Standard / reference | QA relevance |
|---|---|
| Stanford/SLAC-style requirements methodology | Traceability from goals to requirements, use cases, test/QA and change control. |
| SLAC Quality Assurance Program concept | Quality as documented compliance and continual improvement, not one-time inspection. |
| CEFR | Canonical A1–C2 level model for educational coverage and level validation. |
| OpenAPI Specification | API contract tests and machine-readable API documentation. |
| JSON Schema Draft 2020-12 | Canonical data validation for quiz items and related artifacts. |
| RFC 9110 | HTTP method semantics; delivery-producing operations must respect safe/unsafe method logic. |
| RFC 9457 | Problem Details error contract for machine-readable API errors. |
| OWASP API Security Top 10 | API-specific security risk coverage. |
| OWASP ASVS | Security verification controls for application/API security. |
| OWASP WSTG | Web/API security test method reference. |
| NIST SSDF | Secure software development practices and verification mindset. |
| Telegram Bot API | Telegram quiz/poll adapter validation and compatibility. |
| GitHub protected branches/status checks | CI gate discipline before merge/release. |

### 5.3. Standard conflict rule

If standards conflict:

```text
1. Safety and security win.
2. Constitution wins over lower documents.
3. SRS wins over implementation convenience.
4. API/Data standards win over ad hoc client behavior.
5. Launch gate wins over deadline pressure.
6. Known limitations must be documented honestly.
```

---

## 6. QA Inputs

QA uses these inputs:

| Input | Purpose |
|---|---|
| `CONSTITUTION.md` | Binding project rules and non-negotiables. |
| `README.md` generated snapshot | Current corpus baseline and generated inventory/report evidence. |
| `00_vision.md` | Strategic objectives and future source onboarding vision. |
| `01_product_charter.md` | Product scope, MVP gates, decision rights. |
| `02_requirements_srs.md` | Formal functional/non-functional requirements. |
| `03_use_cases.md` | Use case scenarios and test seeds. |
| `04_domain_model.md` | Entities, statuses, invariants and relationships. |
| `05_architecture.md` | Components, test architecture, launch gates. |
| `06_data_standard.md` | Canonical field rules, validation rules, schemas. |
| `07_api_standard.md` | Endpoint behavior, projections, errors, auth, quotas. |
| `08_security_threat_model.md` | Threats, controls, security tests and security gates. |
| Source files / fixtures | Raw and sample data for source/import tests. |
| Generated reports | Evidence artifacts for inventory, import, coverage and operations. |

---

## 7. Quality Objectives

### 7.1. Master objectives

| ID | Objective | Success meaning |
|---|---|---|
| QOBJ-001 | Requirements traceability | P0 requirements have acceptance method and evidence path. |
| QOBJ-002 | Source governance quality | Current and future sources have source_id, checksum, inventory and state. |
| QOBJ-003 | Import safety | Dry-run cannot publish; import preserves traceability and reports errors. |
| QOBJ-004 | Canonical data integrity | Publishable items conform to schema and required metadata. |
| QOBJ-005 | Status safety | Normal delivery never returns draft/imported/needs_review/retired/blocked items. |
| QOBJ-006 | Selection correctness | Selection respects consumer rules, repeat policy, quota and eligibility. |
| QOBJ-007 | API contract integrity | API matches OpenAPI, Problem Details, auth, versioning and projections. |
| QOBJ-008 | Correct answer safety | Answers are exposed only in allowed interaction modes. |
| QOBJ-009 | Access control safety | Object-level and function-level authorization are tested. |
| QOBJ-010 | Telegram reliability | Telegram adapter validates compatibility, logging and retry/idempotency. |
| QOBJ-011 | Entitlement reliability | Paid/limited access uses entitlements and quotas, not payment status alone. |
| QOBJ-012 | Analytics trust | Analytics are scoped, consistent and not cross-consumer leaking. |
| QOBJ-013 | Operations readiness | Monitoring, backups, restore, incident paths are testable. |
| QOBJ-014 | Regression protection | Critical bugs become tests. |
| QOBJ-015 | Demo credibility | Stanford-style demo has repeatable evidence and no overclaiming. |

### 7.2. North Star QA metric

```text
Percentage of production delivery attempts that satisfy all platform rules:
source traceability + approved/published status + entitlement/quota + selection rules + delivery logging + safe projection.
```

Target for production claim:

```text
100% for tested delivery scenarios.
0 known P0 violations.
0 unresolved critical launch-blocking defects.
```

---

## 8. QA Roles and Responsibilities

### 8.1. Role catalog

| Role | Responsibility |
|---|---|
| Project Owner | Accepts launch gates, resolves risk tradeoffs, approves demo claims. |
| QA Owner | Owns QA strategy, test catalog, evidence, release quality sign-off. |
| Engineering Owner | Ensures implementation supports testability, CI, logs and automation. |
| Data Owner | Owns source/import/schema/taxonomy validation rules. |
| API Owner | Owns OpenAPI contract, endpoint tests, auth/error behavior. |
| Security Owner | Owns security test plan, threat controls, vulnerability triage. |
| Operations Owner | Owns backup/restore, monitoring, incident and readiness drills. |
| Content Admin | Executes or validates import/review/status workflow tests. |
| Telegram Owner | Verifies Telegram worker, adapter compatibility and delivery logs. |
| Billing Owner | Verifies entitlements, quotas, webhooks and manual overrides. |
| Demo Owner | Owns Stanford-style demo rehearsal, evidence bundle and fallback artifacts. |

### 8.2. RACI matrix

| Area | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| QA strategy | QA Owner | Project Owner | Engineering, Security, Data | All stakeholders |
| Source/import tests | Data Owner | QA Owner | Content Admin, Engineering | Project Owner |
| API tests | API Owner | QA Owner | Security, Engineering | Project Owner |
| Security tests | Security Owner | Project Owner | QA, Engineering | All maintainers |
| Telegram tests | Telegram Owner | QA Owner | API, Operations | Project Owner |
| Billing tests | Billing Owner | Product Owner | Security, QA | Project Owner |
| Operations drills | Operations Owner | Project Owner | QA, Engineering | Stakeholders |
| Stanford demo | Demo Owner | Project Owner | QA, Engineering, Product | External audience |

---

## 9. Verification Methods

### 9.1. Method codes

| Code | Method | Meaning |
|---|---|---|
| T | Automated Test | Repeatable test executed by CI or test runner. |
| I | Inspection | Document, schema, config or code review. |
| D | Demonstration | Controlled demo of behavior. |
| A | Analysis | Report, metric, log analysis or coverage analysis. |
| O | Operational Drill | Backup/restore, incident, rollback or failover drill. |
| M | Manual Test | Structured human-executed test where automation is not yet feasible. |
| R | Rehearsal | Stanford/demo run with evidence capture. |

### 9.2. Evidence hierarchy

Preferred evidence order:

```text
automated test report
  → contract validation report
  → generated data/report artifact
  → operational drill log
  → manual test record
  → signed inspection checklist
  → demo recording/screenshot with limitations
```

### 9.3. Evidence requirements

Every launch-blocking QA item MUST have:

```text
test_id or gate_id;
requirement_id(s);
component;
preconditions;
steps or command;
expected result;
actual result;
pass/fail;
artifact/log/report reference;
owner;
date;
known limitations if any.
```

---

## 10. Test ID System

### 10.1. Test ID format

```text
QA-<AREA>-<NUMBER>
```

Examples:

```text
QA-SRC-001       source registry test
QA-ONB-001       future source onboarding test
QA-IMP-001       import pipeline test
QA-DATA-001      canonical data validation test
QA-STAT-001      status lifecycle test
QA-SEL-001       selection engine test
QA-API-001       API contract test
QA-TG-001        Telegram adapter test
QA-BILL-001      entitlement/quota test
QA-SEC-001       security test
QA-OPS-001       operations drill
QA-DEMO-001      Stanford demo rehearsal test
```

### 10.2. Test area codes

| Code | Area |
|---|---|
| DOC | Documentation and traceability |
| SRC | Source registry and inventory |
| ONB | Future source onboarding |
| IMP | Import and parser pipeline |
| DATA | Canonical data validation |
| TAX | CEFR/taxonomy/coverage |
| DUP | Duplicate and conflict handling |
| STAT | Status workflow and publication control |
| DB | Database and persistence |
| SEL | Selection engine |
| API | API contract and behavior |
| TG | Telegram delivery |
| ADM | Admin workflow |
| BILL | Billing, entitlements and quotas |
| AN | Analytics and reporting |
| SEC | Security and privacy |
| PERF | Performance and scale |
| REL | Reliability and resilience |
| OPS | Operations, backup, restore, monitoring |
| CI | CI/CD and repository governance |
| DEMO | Stanford-style demo evidence |
| REG | Regression tests |

### 10.3. Requirement-to-test mapping

Every P0 requirement SHALL map to at least one of:

```text
QA test case;
launch gate;
inspection checklist;
operational drill;
demo evidence item.
```

Every P0 automated behavior SHOULD eventually map to at least one automated test, unless documented as not automatable yet.

---

## 11. Test Levels

### 11.1. Level overview

```text
Static checks
  documentation, schemas, manifests, OpenAPI, security configs

Unit tests
  validators, parsers, selection filters, status transitions, entitlement decisions

Integration tests
  import + database, API + DB, worker + API, billing webhook + entitlements

Contract tests
  OpenAPI schemas, JSON Schema, Problem Details, projections

End-to-end tests
  source onboarding → import → approve → API next quiz → delivery → attempt → analytics

Security tests
  auth, object-level authorization, answer exposure, webhook verification, secrets/logs

Operational drills
  backup, restore, rollback, incident simulation

Demo rehearsal
  deterministic Stanford-style demo path and evidence package
```

### 11.2. Test pyramid for API Quiz Bank

```text
          Demo / E2E / Operational drills
        Contract / Integration / Security tests
      Unit tests / Validators / Domain rule tests
    Static checks / Schema checks / Documentation checks
```

Unit and contract tests should be broad. E2E tests should be fewer but represent critical business flows.

---

## 12. Test Types

| Test type | Purpose | Examples |
|---|---|---|
| Documentation tests | Ensure required docs exist and align | docs present, versioned, no missing references |
| Schema tests | Validate data contracts | `quiz_item.schema.json`, manifest schema |
| Parser tests | Validate source parsing | valid CSV, invalid row, unknown column |
| Import tests | Verify dry-run/import behavior | dry-run no production write, report generated |
| Data-quality tests | Verify canonical item integrity | required fields, correct option IDs, CEFR values |
| Status tests | Verify lifecycle and publication gates | draft blocked, approved eligible, retired excluded |
| Selection tests | Verify candidate filtering | level/theme/repeat/quota/status filtering |
| API tests | Verify endpoint behavior | auth, `/v1`, Problem Details, projections |
| Contract tests | Verify machine-readable contract | OpenAPI conformance, response schemas |
| Security tests | Verify controls | object authorization, answer leakage, token logs |
| Telegram tests | Verify adapter delivery | poll constraints, retry, delivery log |
| Billing tests | Verify access control | entitlements, quotas, webhook replay |
| Analytics tests | Verify reporting correctness | delivery counts, coverage, scoped reports |
| Performance tests | Verify baseline responsiveness | selection latency, API latency, import duration |
| Reliability tests | Verify failure behavior | retry, rollback, idempotency, no double delivery |
| Regression tests | Prevent known bugs | every critical issue becomes a test |
| Smoke tests | Fast release confidence | health, readiness, one approved item delivery |
| Exploratory tests | Human investigation | admin workflows, edge cases, UX gaps |
| Demo tests | Verify presentation path | deterministic demo script and fallback artifacts |

---

## 13. Test Environments

### 13.1. Environment types

| Environment | Purpose | Data allowed | Gate use |
|---|---|---|---|
| Local | Developer/QA testing | sample fixtures, local DB | development |
| CI | Automated checks | synthetic fixtures, small corpus subset | merge/release gating |
| Test/Staging | Integration and E2E | controlled subset, anonymized/safe data | MVP/Pilot gates |
| Demo | Stanford-style presentation | controlled demo data + safe corpus reports | demo gate |
| Pilot | Limited real consumers | approved pilot data | pilot gate |
| Production | Real product | production data only after gates | production gate |

### 13.2. Environment rules

```text
Production secrets must not exist in local/CI logs.
Demo environment must not expose secrets or private user data.
CI must not require Telegram real posting for all tests.
Telegram send tests may be simulated unless pilot gate requires controlled real send.
Billing provider tests may use test mode or signed fixture events.
Database destructive tests must run only against test databases.
```

---

## 14. Test Data and Fixtures

### 14.1. Required fixture catalog

| Fixture | Purpose |
|---|---|
| `fixture_valid_source_csv` | Valid source file for parser/import tests. |
| `fixture_invalid_source_csv` | Invalid rows, missing fields, wrong CEFR. |
| `fixture_unknown_cefr_item` | Valid structure but invalid level. |
| `fixture_duplicate_item` | Exact duplicate detection. |
| `fixture_answer_conflict_item` | Same stem/options with conflicting correct answer. |
| `fixture_valid_canonical_item` | JSON Schema positive case. |
| `fixture_invalid_canonical_item` | Missing answer/invalid option reference. |
| `fixture_draft_item` | Must never be delivered to normal consumer. |
| `fixture_approved_item` | Should be eligible for selection. |
| `fixture_blocked_item` | Must never be delivered. |
| `fixture_retired_item` | Must never be selected for new delivery. |
| `fixture_consumer_active` | Active consumer with rules. |
| `fixture_consumer_no_entitlement` | Entitlement denial. |
| `fixture_consumer_quota_exceeded` | Quota denial. |
| `fixture_telegram_compatible_item` | Telegram adapter success. |
| `fixture_telegram_incompatible_item` | Too many options/too long question/etc. |
| `fixture_billing_webhook_valid` | Signed billing event. |
| `fixture_billing_webhook_invalid` | Signature/replay rejection. |
| `fixture_demo_future_source` | Sample new file onboarding demo. |

### 14.2. Fixture rules

```text
Fixtures must be small, stable and version-controlled.
Fixtures must not contain secrets.
Fixtures must not contain private user data.
Fixtures should include both positive and negative cases.
Each fixture should have documented purpose and expected result.
```

### 14.3. Golden dataset rule

For regression and demo:

```text
Maintain a small golden dataset that can demonstrate:
source registration;
dry-run import;
canonical validation;
approval;
selection;
API delivery;
attempt submission;
analytics report;
blocking of draft/unauthorized/quota cases.
```

The golden dataset is not the full corpus. It is a controlled test asset.

---

## 15. QA Artifact Model

### 15.1. Required QA artifacts

| Artifact | Suggested path | Purpose |
|---|---|---|
| QA strategy | `docs/09_quality_assurance.md` | This document. |
| Test catalog | `tests/TEST_CATALOG.md` or generated report | Master list of tests. |
| Requirements traceability matrix | `docs/traceability/requirements_tests_matrix.md` | Requirement → test mapping. |
| Test fixtures README | `tests/fixtures/README.md` | Fixture meaning and expected results. |
| CI quality workflow | `.github/workflows/quality.yml` | Automated checks. |
| Data quality report | `reports/data_quality_report.json/md` | Schema/status/taxonomy results. |
| Import test report | `reports/import_test_report.json/md` | Dry-run/import evidence. |
| API contract report | `reports/api_contract_report.json/md` | OpenAPI validation evidence. |
| Security test report | `reports/security_test_report.json/md` | Security evidence. |
| Release QA report | `reports/release_qa_report.md` | Gate summary. |
| Demo evidence package | `demo/evidence/` | Stanford-style proof. |

### 15.2. Test result record format

```yaml
test_id: QA-API-001
requirement_ids:
  - SRS-API-001
  - SRS-API-002
use_case_ids:
  - UC-005
component: api-service
phase: MVP
priority: P0
method: T
preconditions:
  - active consumer exists
  - approved item exists
steps:
  - call POST /v1/quiz-items/next with valid consumer
expected_result:
  - response is 200
  - returned item status is approved or published
  - delivery record exists
actual_result: TBD
status: not_run
artifact: reports/api_contract_report.json
owner: QA Owner
date: null
notes: null
```

---

## 16. Traceability Model

### 16.1. Traceability chain

Every critical QA item should trace:

```text
Vision objective
  → Product goal
  → SRS requirement
  → Use case / business rule
  → Domain entity / invariant
  → Architecture component
  → Data/API/security contract
  → Test case
  → Evidence artifact
  → Launch gate
```

### 16.2. Traceability matrix columns

Recommended columns:

```text
requirement_id
requirement_area
priority
phase
use_case_id
business_rule_id
domain_entity
component
contract_artifact
test_id
verification_method
ci_job
launch_gate
evidence_artifact
owner
status
last_verified_at
```

### 16.3. Minimum traceability before MVP

Before MVP acceptance:

```text
All P0 requirements have at least one verification method.
All P0 delivery-safety rules have automated tests where feasible.
All P0 launch gates have evidence.
All demo-critical use cases have rehearsal steps.
All known P0 limitations are documented.
```

---

## 17. SRS QA Requirements Compliance

The SRS defines core QA requirements. This document adopts them as binding QA obligations.

| SRS ID | Requirement summary | QA implementation |
|---|---|---|
| NFR-QA-001 | Every P0 requirement has acceptance method | Requirements-test matrix required. |
| NFR-QA-002 | Data validation tests cover required fields, status, CEFR, options, answers | QA-DATA and QA-STAT suites. |
| NFR-QA-003 | API tests cover auth, filtering, next-item, quota, errors | QA-API and QA-SEC suites. |
| NFR-QA-004 | Import tests cover dry-run, invalid rows, traceability | QA-IMP suite. |
| NFR-QA-005 | Selection tests cover anti-repeat, status, consumer rules | QA-SEL suite. |
| NFR-QA-006 | Telegram pilot tests cover compatibility and delivery logging | QA-TG suite. |
| NFR-QA-007 | Security tests cover object-level authorization | QA-SEC suite. |
| NFR-QA-008 | Demo rehearsal before Stanford-style presentation | QA-DEMO suite. |
| NFR-QA-009 | Known limitations documented | Release notes and demo notes. |
| NFR-QA-010 | Test failures block production launch for affected scope | Launch gate enforcement. |

---

## 18. P0 Release-Blocking Rules

The following failures are automatic launch blockers for the affected scope.

### 18.1. Universal blockers

```text
P0 requirement without verification method;
critical test failure without accepted waiver;
missing release QA report;
known limitation hidden from release/demo materials;
secrets committed to repository;
raw source files exposed to normal consumers;
production DB destructive test risk in non-isolated test run;
```

### 18.2. Content/data blockers

```text
approved/published item missing source traceability;
invalid correct answer reference accepted as publishable;
unrecognized CEFR level accepted in approved/published item;
status enum not enforced;
new source can bypass onboarding gate;
dry-run import creates production item;
source without source_id/checksum imported;
```

### 18.3. Delivery blockers

```text
draft item delivered to normal consumer;
blocked item delivered;
retired item delivered for new delivery;
consumer rules ignored;
repeat policy violated in tested scenario;
delivery-producing endpoint fails to log or reserve delivery;
```

### 18.4. API/security blockers

```text
unauthorized consumer can access another consumer resource;
normal consumer receives admin-only data;
correct answer leaks in hidden mode;
quota exceeded still delivers item;
Problem Details/error contract absent for P0 errors;
admin endpoint usable with normal token;
billing webhook accepted without verification if billing is active;
```

### 18.5. Operations blockers

```text
no backup before production claim;
restore not tested before production claim;
no incident path before production claim;
no monitoring/readiness evidence before production claim;
production launch with unresolved P0 security risk;
```

---

## 19. Documentation QA

### 19.1. Purpose

Documentation is infrastructure. QA must verify documentation exists, aligns, and does not make unsupported claims.

### 19.2. Required tests

| Test ID | Test | Phase | Method | Blocks? |
|---|---|---|---|---|
| QA-DOC-001 | Required foundational docs exist and are versioned. | MVP | I | Yes |
| QA-DOC-002 | SRS P0 requirements have test/verification mapping. | MVP | I | Yes |
| QA-DOC-003 | Use cases UC-001 to UC-030 have acceptance criteria or test seeds. | MVP/Pilot | I | Yes for demo-critical |
| QA-DOC-004 | Architecture/data/API/security docs do not contradict SRS gates. | MVP | I | Yes |
| QA-DOC-005 | Release notes include known limitations. | Pilot/Beta/Demo | I | Yes |
| QA-DOC-006 | Demo script distinguishes implemented, simulated and planned features. | Demo | I/R | Yes |

### 19.3. Documentation defects

Documentation defects are serious when they cause:

```text
wrong implementation;
wrong launch decision;
security misunderstanding;
demo overclaiming;
loss of source traceability;
wrong API contract;
false production readiness claim.
```

---

## 20. Source Registry and Inventory QA

### 20.1. Quality goal

Every source file must be governable, identifiable, traceable and safely onboardable.

### 20.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-SRC-001 | Current corpus inventory can be generated or inspected. | P0 | MVP | T/I |
| QA-SRC-002 | Every active source has stable `source_id`. | P0 | MVP | T |
| QA-SRC-003 | Every active/importable source has checksum. | P0 | MVP | T |
| QA-SRC-004 | Service template is distinguished from active bank files. | P0 | MVP | T/I |
| QA-SRC-005 | Duplicate active `source_id` is rejected. | P0 | MVP | T |
| QA-SRC-006 | Duplicate checksum is flagged for review. | P1 | Pilot | T/A |
| QA-SRC-007 | Archived/rejected/blocked source states prevent new production import. | P1 | Pilot | T |
| QA-SRC-008 | Inventory report includes row/item counts where available. | P1 | Pilot | A |
| QA-SRC-009 | Source history remains after archive/rejection/block. | P1 | Pilot | T/I |
| QA-SRC-010 | Source registry supports future files without changing ID strategy. | P0 | MVP | I/T |

### 20.3. Negative tests

```text
attempt import source without source_id → reject;
attempt import source without checksum → reject;
register duplicate source_id → reject;
mark source blocked then import → reject;
service template appears as active quiz bank source → fail;
```

---

## 21. Future Source Onboarding QA

### 21.1. Quality goal

New quiz files must be onboarded, not dropped.

### 21.2. Onboarding test path

```text
candidate source
  → source_id
  → checksum
  → inventory record
  → manifest entry
  → parser profile
  → dry-run import
  → validation report
  → duplicate/conflict report
  → import batch
  → status workflow
  → generated reports
```

### 21.3. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-ONB-001 | New source starts in non-production state. | P0 | MVP | T |
| QA-ONB-002 | New source receives source_id and checksum before parser assignment. | P0 | MVP | T |
| QA-ONB-003 | New source cannot dry-run without manifest entry. | P0 | MVP | T |
| QA-ONB-004 | New source cannot publish without validation/status workflow. | P0 | MVP | T |
| QA-ONB-005 | Onboarding report records parser, defaults, validation errors and accepted count. | P1 | Pilot | A |
| QA-ONB-006 | Candidate source can be rejected with reason code and audit trail. | P1 | Pilot | T/I |
| QA-ONB-007 | Sample future source onboarding can be demonstrated. | P0 | MVP/Demo | D/R |
| QA-ONB-008 | Source onboarding prevents direct production source drops. | P0 | MVP | T/I |

### 21.4. Stanford demo requirement

Demo must include either:

```text
live onboarding of a small sample future source;
```

or:

```text
recorded/generated evidence showing source_id, checksum, dry-run import, validation and status gating.
```

---

## 22. Import and Parser QA

### 22.1. Quality goal

Import must transform raw files into normalized candidates and canonical items safely, reproducibly and with evidence.

### 22.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-IMP-001 | Dry-run import creates no production items. | P0 | MVP | T |
| QA-IMP-002 | Dry-run report includes rows seen, parsed, skipped, errors. | P0 | MVP | T/A |
| QA-IMP-003 | Invalid row is rejected or quarantined with reason. | P0 | MVP | T |
| QA-IMP-004 | Source locator is preserved for normalized candidate. | P0 | MVP | T |
| QA-IMP-005 | Content hash is generated for normalized candidate. | P0 | MVP | T |
| QA-IMP-006 | Unknown CEFR/theme/objective/pattern is not silently coerced. | P0 | MVP | T |
| QA-IMP-007 | Parser failure produces structured failure report. | P1 | Pilot | T/A |
| QA-IMP-008 | Same source checksum + manifest + parser version produces reproducible result. | P1 | Pilot | T/A |
| QA-IMP-009 | Parser profile field mappings are tested with fixture source. | P0 | MVP | T |
| QA-IMP-010 | Actual import references source_id and import_batch_id. | P0 | MVP | T |
| QA-IMP-011 | Failed import does not corrupt existing production data. | P0 | MVP/Pilot | T |
| QA-IMP-012 | Import report is stored as evidence artifact. | P1 | Pilot | A |

### 22.3. Parser fixture set

Minimum parser fixtures:

```text
valid CSV with expected columns;
CSV with missing stem;
CSV with missing options;
CSV with invalid correct answer reference;
CSV with unknown CEFR;
CSV with duplicate row;
CSV with encoding/delimiter variation if applicable;
CSV with current compatibility field such as sublevel → cefr_level.
```

---

## 23. Canonical Data Validation QA

### 23.1. Quality goal

Every publishable quiz item must satisfy canonical schema, required metadata and consumer compatibility rules.

### 23.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-DATA-001 | Valid canonical item passes JSON Schema. | P0 | MVP | T |
| QA-DATA-002 | Missing stem fails validation. | P0 | MVP | T |
| QA-DATA-003 | Fewer than 2 options fails validation. | P0 | MVP | T |
| QA-DATA-004 | Invalid correct option reference fails validation. | P0 | MVP | T |
| QA-DATA-005 | Approved/published item requires CEFR level. | P0 | MVP | T |
| QA-DATA-006 | Approved/published item requires primary theme. | P0 | MVP | T |
| QA-DATA-007 | Approved/published item requires source_id and content_hash. | P0 | MVP | T |
| QA-DATA-008 | Status enum accepts only allowed values. | P0 | MVP | T |
| QA-DATA-009 | Compatibility field `sublevel` maps to canonical `cefr_level`. | P0 | MVP | T/I |
| QA-DATA-010 | API projection validates against response schema. | P0 | MVP | T |
| QA-DATA-011 | Telegram projection validates against Telegram profile. | P1 | Pilot | T |
| QA-DATA-012 | Schema evolution does not break existing valid sample items. | P1 | Pilot | T |

### 23.3. Data validation stop-ship rules

Stop ship if:

```text
invalid correct-answer reference can be approved;
approved/published item lacks source traceability;
unknown CEFR is accepted as publishable;
status enum is not enforced;
normal consumer receives internal-only data fields;
```

---

## 24. Taxonomy and Coverage QA

### 24.1. Quality goal

The system must correctly represent CEFR, 18 themes, objectives, patterns and coverage matrix.

### 24.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-TAX-001 | CEFR values limited to A1, A2, B1, B2, C1, C2. | P0 | MVP | T |
| QA-TAX-002 | 18 canonical theme IDs are represented. | P0 | MVP | T/I |
| QA-TAX-003 | Objective IDs validate against known taxonomy. | P0/P1 | MVP/Pilot | T |
| QA-TAX-004 | Pattern IDs validate against known taxonomy. | P0/P1 | MVP/Pilot | T |
| QA-TAX-005 | Coverage report can be generated. | P1 | Pilot | A |
| QA-TAX-006 | Coverage report distinguishes draft/approved/published. | P1 | Pilot | A |
| QA-TAX-007 | Taxonomy change requires change control evidence. | P1 | Pilot | I |
| QA-TAX-008 | Selection cannot request unsupported taxonomy silently. | P0 | MVP | T |

### 24.3. Coverage report expectations

Coverage report should include:

```text
count by status;
count by CEFR level;
count by theme;
count by objective;
count by pattern;
level × theme matrix;
level × theme × objective × pattern where feasible;
coverage gaps;
changes since previous snapshot;
```

---

## 25. Duplicate and Conflict QA

### 25.1. Quality goal

Duplicates and conflicts must be detected, classified and resolved explicitly, especially for future source onboarding.

### 25.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-DUP-001 | Exact duplicate content hash is detected. | P1 | Pilot | T |
| QA-DUP-002 | Near duplicate is classified for review. | P1 | Pilot | T/A |
| QA-DUP-003 | Same stem/options with conflicting answer is blocker. | P0/P1 | MVP/Pilot | T |
| QA-DUP-004 | Duplicate resolution is logged with actor/reason. | P1 | Pilot | T/I |
| QA-DUP-005 | Exact duplicate is not silently published as second active item. | P1 | Pilot | T |
| QA-DUP-006 | Variant acceptance requires explicit reason. | P1 | Pilot | T/I |

### 25.3. Negative tests

```text
import duplicate with no resolution → block or needs_review;
import same question with different correct answer → block;
admin override without reason → reject;
```

---

## 26. Status Lifecycle QA

### 26.1. Quality goal

Publication eligibility must be controlled by status, never by file existence alone.

### 26.2. Allowed item statuses

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

### 26.3. Delivery-eligible statuses

Normal consumers may receive only:

```text
approved
published
```

### 26.4. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-STAT-001 | Every quiz item has exactly one status. | P0 | MVP | T |
| QA-STAT-002 | Draft item is not delivered to normal consumer. | P0 | MVP | T |
| QA-STAT-003 | Imported item is not delivered. | P0 | MVP | T |
| QA-STAT-004 | Needs_review item is not delivered. | P0 | MVP | T |
| QA-STAT-005 | Blocked item is not delivered. | P0 | MVP | T |
| QA-STAT-006 | Retired item is not selected for new delivery. | P0/P1 | MVP/Pilot | T |
| QA-STAT-007 | Approved item can become eligible for selection. | P0 | MVP | T |
| QA-STAT-008 | Published item can become eligible for selection. | P1 | Pilot | T |
| QA-STAT-009 | Status transition is audited. | P0 | MVP | T/I |
| QA-STAT-010 | Invalid status transition is rejected or logged as controlled override. | P1 | Pilot | T/I |

### 26.5. Regression rule

Any bug where a non-delivery status reaches normal consumer MUST create regression test `QA-REG-STAT-*`.

---

## 27. Database and Persistence QA

### 27.1. Quality goal

The database must preserve source traceability, versioning, delivery history, attempts, entitlements and audit records reliably.

### 27.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-DB-001 | Migrations apply cleanly from empty database. | P0 | MVP | T |
| QA-DB-002 | Migrations are reversible or rollback path is documented. | P1 | Pilot | T/I |
| QA-DB-003 | Source-item-import relationships preserve traceability. | P0 | MVP | T |
| QA-DB-004 | Delivery history remains after item retirement. | P1 | Pilot | T |
| QA-DB-005 | Attempt records reference valid delivery/item/user context. | P1 | Pilot | T |
| QA-DB-006 | Audit logs are append-only or protected from normal mutation. | P1 | Pilot | T/I |
| QA-DB-007 | Duplicate public IDs are rejected. | P0 | MVP | T |
| QA-DB-008 | Required indexes exist for selection/API baseline. | P1 | Pilot | I/A |

### 27.3. Persistence negative tests

```text
delete retired item with delivery history → reject or preserve history;
insert item without source_id/import_batch_id → reject for publishable state;
insert duplicate public_id → reject;
```

---

## 28. Selection Engine QA

### 28.1. Quality goal

Selection engine must choose only eligible items and explain why no item is eligible.

### 28.2. Selection filters to test

```text
status;
CEFR level;
theme;
objective;
pattern;
consumer rules;
entitlements;
quota;
repeat policy;
quality flags;
compatibility constraints;
blocked/retired exclusion;
```

### 28.3. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-SEL-001 | Approved item can be selected for eligible consumer. | P0 | MVP | T |
| QA-SEL-002 | Draft item is excluded. | P0 | MVP | T |
| QA-SEL-003 | Blocked item is excluded. | P0 | MVP | T |
| QA-SEL-004 | Consumer level rules are respected. | P0 | MVP | T |
| QA-SEL-005 | Consumer theme rules are respected. | P0 | MVP | T |
| QA-SEL-006 | Entitlement restrictions are respected. | P0 | MVP | T |
| QA-SEL-007 | Quota exceeded prevents selection/delivery. | P0 | MVP | T |
| QA-SEL-008 | Repeat policy excludes recently delivered item. | P0 | MVP | T |
| QA-SEL-009 | No eligible item returns machine-readable reason. | P0 | MVP | T |
| QA-SEL-010 | Selection can be deterministic in demo/test mode. | P1 | Demo | T/D |
| QA-SEL-011 | Selection creates reservation or delivery trace when required. | P0/P1 | MVP/Pilot | T |
| QA-SEL-012 | Concurrent selection avoids duplicate reservation where policy forbids it. | P1 | Pilot | T |

### 28.4. Stop-ship selection defects

```text
non-approved item selected;
consumer receives forbidden level/theme;
quota bypass;
repeat policy ignored in tested scenario;
no delivery/reservation trace for delivery-producing request;
```

---

## 29. API QA

### 29.1. Quality goal

API must be a versioned, secure, documented, contract-tested product surface.

### 29.2. API test categories

```text
OpenAPI contract tests;
request schema tests;
response schema tests;
authentication tests;
object-level authorization tests;
object-property exposure tests;
status filtering tests;
entitlement/quota tests;
selection/no-repeat tests;
Problem Details tests;
idempotency tests;
attempt submission tests;
admin source/import tests;
Telegram projection tests;
analytics authorization tests;
```

### 29.3. Core API behavior tests

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-API-001 | `/v1/health` returns basic health. | P0 | MVP | T |
| QA-API-002 | `/v1/readiness` reflects dependencies. | P1 | Pilot | T |
| QA-API-003 | OpenAPI contract exists and validates. | P0 | MVP | T/I |
| QA-API-004 | API uses versioned `/v1` routes. | P0 | MVP | T/I |
| QA-API-005 | `POST /v1/quiz-items/next` returns approved/published item only. | P0 | MVP | T |
| QA-API-006 | Delivery-producing next-quiz request records delivery/reservation. | P0 | MVP/Pilot | T |
| QA-API-007 | Draft item never appears in normal response. | P0 | MVP | T |
| QA-API-008 | Quota exceeded returns 429 Problem Details or documented equivalent. | P0 | MVP | T |
| QA-API-009 | No eligible item returns machine-readable reason. | P0 | MVP | T |
| QA-API-010 | Unauthorized request is denied. | P0 | MVP | T |
| QA-API-011 | Cross-consumer access is denied. | P0 | MVP | T |
| QA-API-012 | Correct answer is not exposed in hidden mode. | P0 | MVP | T |
| QA-API-013 | Admin-only fields are not exposed to normal consumers. | P0 | MVP | T |
| QA-API-014 | `POST /v1/attempts` validates option IDs. | P1 | Pilot | T |
| QA-API-015 | Attempt submission stores correctness only when allowed. | P1 | Pilot | T |
| QA-API-016 | API examples in OpenAPI remain valid. | P1 | Pilot | T |
| QA-API-017 | ProblemDetails schema is used for errors. | P0 | MVP | T |
| QA-API-018 | Internal/admin endpoints are not accidentally public. | P0 | MVP | T/I |

### 29.4. HTTP semantics QA

Delivery-producing requests that create delivery/reservation/usage state SHOULD use `POST`, not `GET`, because they are not safe read-only operations.

QA SHALL verify:

```text
POST /v1/quiz-items/next is normative for delivery-producing behavior;
GET compatibility/preview route, if present, does not create delivery state unless explicitly documented;
cache headers do not cause accidental replay or exposure of protected quiz responses;
```

---

## 30. Correct Answer Exposure QA

### 30.1. Quality goal

Correct answers must be exposed only in permitted modes and channels.

### 30.2. Exposure modes

| Mode | Correct answer exposure |
|---|---|
| Hidden learner mode | Do not expose correct answer before attempt/poll completion. |
| Telegram quiz mode | Provide correct option IDs only to Telegram API payload as required, not to public API consumer if hidden. |
| Admin mode | Full answer data allowed to authorized admin. |
| Teacher pack mode | Configurable, must respect entitlement and context. |
| Post-attempt mode | Correct answer may be returned after valid attempt if product policy allows. |
| Demo mode | Clearly marked and safe; no hidden production secrets. |

### 30.3. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-ANS-001 | Hidden mode response omits correct answer fields. | P0 | MVP | T |
| QA-ANS-002 | Admin view includes answers only with admin authorization. | P0/P1 | MVP/Pilot | T |
| QA-ANS-003 | Attempt result exposes allowed feedback only after valid attempt. | P1 | Pilot | T |
| QA-ANS-004 | Telegram payload contains correct option IDs only inside worker/adapter path. | P1 | Pilot | T/I |
| QA-ANS-005 | Logs do not expose correct answers unnecessarily. | P1 | Pilot | T/I |

---

## 31. Telegram QA

### 31.1. Quality goal

Telegram delivery must use API/selection engine, validate poll compatibility, log delivery and handle failures safely.

### 31.2. Compatibility checks

Telegram-facing validation SHALL check:

```text
question text length;
option count;
option text length where applicable;
quiz vs regular poll type;
correct_option_ids / multiple-answer compatibility;
explanation constraints;
posting schedule;
chat/channel identity;
worker authorization;
```

### 31.3. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-TG-001 | Telegram worker does not read raw CSV. | P0 | Pilot | I/T |
| QA-TG-002 | Worker requests quiz through API/selection engine. | P0 | Pilot | T/D |
| QA-TG-003 | Worker posts only approved/published item. | P0 | Pilot | T |
| QA-TG-004 | Incompatible item is blocked before send. | P1 | Pilot | T |
| QA-TG-005 | Successful send records delivery status and message ID where available. | P1 | Pilot | T/D |
| QA-TG-006 | Send failure is logged with reason. | P1 | Pilot | T/D |
| QA-TG-007 | Retry/idempotency prevents uncontrolled duplicate posting. | P1 | Pilot | T |
| QA-TG-008 | Schedule respects consumer rules and entitlement. | P1 | Pilot | T |
| QA-TG-009 | Dry-run mode creates payload without posting. | P1 | Demo/Pilot | T/D |
| QA-TG-010 | Demo Telegram delivery can be simulated if real posting is not safe. | P1 | Demo | R |

### 31.4. Telegram stop-ship defects

```text
worker reads raw CSV;
worker bypasses selection engine;
worker posts draft/blocked item;
Telegram send failure creates duplicate without trace;
Telegram token appears in logs or repository;
```

---

## 32. Admin Workflow QA

### 32.1. Quality goal

Admin actions must be authorized, auditable and unable to bypass publication gates.

### 32.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-ADM-001 | Source registration requires admin authorization. | P0 | MVP | T |
| QA-ADM-002 | Dry-run import requires authorized admin/system actor. | P0 | MVP | T |
| QA-ADM-003 | Approving item requires required metadata. | P0 | MVP | T |
| QA-ADM-004 | Status changes are audited. | P0 | MVP | T/I |
| QA-ADM-005 | Retiring item preserves delivery history. | P1 | Pilot | T |
| QA-ADM-006 | Blocking item excludes it from delivery. | P0 | MVP | T |
| QA-ADM-007 | Manual entitlement override requires reason and audit log. | P1 | Pilot | T/I |
| QA-ADM-008 | Batch action creates batch audit evidence. | P1 | Pilot | T/I |
| QA-ADM-009 | Normal user cannot access admin function. | P0 | MVP | T |
| QA-ADM-010 | Admin CLI path, if used before UI, still logs high-risk actions. | P0/P1 | MVP/Pilot | I/D |

---

## 33. Billing, Entitlements and Quota QA

### 33.1. Quality goal

Access must be controlled by internal entitlements and quotas, not raw payment status alone.

### 33.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-BILL-001 | Consumer with valid entitlement can request allowed quiz. | P0/P1 | MVP/Pilot | T |
| QA-BILL-002 | Consumer without entitlement is denied. | P0 | MVP | T |
| QA-BILL-003 | Quota exceeded denies delivery with machine-readable error. | P0 | MVP | T |
| QA-BILL-004 | Usage is recorded when delivery occurs. | P1 | Pilot | T |
| QA-BILL-005 | Payment webhook updates entitlement, not direct delivery permission. | P1 | Beta | T/I |
| QA-BILL-006 | Fake webhook is rejected. | P1 | Beta | T |
| QA-BILL-007 | Replayed webhook does not duplicate grant. | P1 | Beta | T |
| QA-BILL-008 | Manual override requires audit trail. | P1 | Pilot | T/I |
| QA-BILL-009 | Entitlement narrower than request narrows or denies request. | P0/P1 | MVP/Pilot | T |
| QA-BILL-010 | Expired entitlement blocks protected delivery. | P1 | Pilot | T |

### 33.3. Billing launch rule

Paid public launch MUST NOT occur until:

```text
entitlement model is operational;
quota enforcement is tested;
payment-provider webhook verification is tested if provider is active;
manual overrides are audited;
usage reports can support dispute/debug workflows;
```

---

## 34. Analytics and Reporting QA

### 34.1. Quality goal

Analytics must be consistent, scoped, explainable and safe.

### 34.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-AN-001 | Delivery count matches delivery records. | P1 | Pilot | T/A |
| QA-AN-002 | Attempt count matches attempt records. | P1 | Pilot | T/A |
| QA-AN-003 | Coverage report matches corpus state by status/level/theme. | P1 | Pilot | A |
| QA-AN-004 | Analytics distinguish draft from approved/published. | P1 | Pilot | A |
| QA-AN-005 | Consumer-scoped analytics do not expose other consumers. | P0/P1 | MVP/Pilot | T |
| QA-AN-006 | Quality issue reports appear in admin/reporting path. | P1 | Beta | T/D |
| QA-AN-007 | Analytics report has generated timestamp and input snapshot reference. | P1 | Pilot | A/I |
| QA-AN-008 | Demo analytics use safe demo data or clearly marked aggregate corpus reports. | P1 | Demo | I/R |

---

## 35. Security QA

### 35.1. Quality goal

Security controls must be verified according to the threat model and API risk profile.

### 35.2. Security test categories

```text
authentication tests;
object-level authorization tests;
function-level authorization tests;
object-property exposure tests;
correct-answer leakage tests;
admin endpoint tests;
source onboarding gate tests;
import validation abuse tests;
selection/status filter tests;
entitlement/quota tests;
webhook signature/replay tests;
Telegram token and retry tests;
secrets/log redaction tests;
OpenAPI security scheme checks;
rate-limit/abuse tests;
backup/restore security checks;
CI secret/dependency scanning;
```

### 35.3. Core security tests

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-SEC-001 | Non-public endpoints require auth. | P0 | MVP | T |
| QA-SEC-002 | Object-level authorization blocks cross-consumer access. | P0 | MVP | T |
| QA-SEC-003 | Normal API token cannot call admin endpoint. | P0 | MVP | T |
| QA-SEC-004 | Learner-safe projection does not expose correct answers. | P0 | MVP | T |
| QA-SEC-005 | Draft/blocked items cannot be forced into delivery. | P0 | MVP | T |
| QA-SEC-006 | API keys/secrets are not committed to repository. | P0 | MVP | T/I |
| QA-SEC-007 | Logs do not contain raw tokens/secrets. | P1 | Pilot | T/I |
| QA-SEC-008 | Webhook signature check rejects fake event. | P1 | Beta | T |
| QA-SEC-009 | Webhook replay does not duplicate entitlement. | P1 | Beta | T |
| QA-SEC-010 | Rate limiting or usage controls exist for public/pilot scope. | P1 | Pilot/Beta | T/I |
| QA-SEC-011 | OpenAPI security schemes match implementation. | P1 | Beta | T/I |
| QA-SEC-012 | Dependency/security scanning is configured. | P1 | Beta | T/I |
| QA-SEC-013 | Demo credentials are limited and non-production. | P1 | Demo | I/R |
| QA-SEC-014 | Security risk register has no hidden P0 contradiction. | P1 | Demo/Prod | I |

### 35.4. Security regression rule

Any issue involving:

```text
authorization bypass;
answer leakage;
draft/blocked item delivery;
quota bypass;
webhook spoofing;
secret leakage;
admin privilege abuse;
```

MUST produce a regression test before closure.

---

## 36. Operations and Reliability QA

### 36.1. Quality goal

The system must be observable, recoverable and operationally honest before production claims.

### 36.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-OPS-001 | Health check endpoint or command works. | P0 | MVP | T/D |
| QA-OPS-002 | Readiness check reflects database/API dependencies. | P1 | Pilot | T/D |
| QA-OPS-003 | Backup artifact can be created. | P1 | Pilot/Prod | O |
| QA-OPS-004 | Restore drill succeeds on test environment. | P1/P0 | Pilot/Prod | O |
| QA-OPS-005 | Incident playbook exists. | P1 | Pilot/Prod | I |
| QA-OPS-006 | Rollback/deployment recovery path exists. | P1 | Pilot/Prod | I/O |
| QA-OPS-007 | Critical errors are logged with correlation ID where feasible. | P1 | Pilot | T/I |
| QA-OPS-008 | Logs avoid secrets/private data. | P1 | Pilot | T/I |
| QA-OPS-009 | Failed Telegram delivery is observable. | P1 | Pilot | T/D |
| QA-OPS-010 | Failed import is observable and does not corrupt production data. | P0/P1 | MVP/Pilot | T/D |
| QA-OPS-011 | Known limitations are documented in release notes. | P1 | Pilot/Demo | I |

### 36.3. Production operations gate

Production claim requires:

```text
backup exists;
restore tested;
monitoring exists;
incident path exists;
admin actions logged;
critical tests pass;
known limitations documented;
```

---

## 37. Performance and Scale QA

### 37.1. Quality goal

Performance tests should prove that core flows are not obviously unsafe or unusable at expected MVP/Pilot scale.

### 37.2. MVP performance scope

MVP performance QA SHOULD measure:

```text
source inventory generation time;
dry-run import time for sample/pilot source;
canonical validation throughput;
selection latency for controlled dataset;
API next-quiz response time under small concurrent load;
delivery logging overhead;
coverage report generation time;
```

### 37.3. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| QA-PERF-001 | Selection latency measured on pilot dataset. | P1 | Pilot | A/T |
| QA-PERF-002 | API next-quiz latency measured under baseline load. | P1 | Pilot | A/T |
| QA-PERF-003 | Import dry-run duration measured for representative source. | P1 | Pilot | A |
| QA-PERF-004 | Coverage report generation measured. | P2 | Beta | A |
| QA-PERF-005 | Rate limit behavior tested under abusive request pattern. | P1/P2 | Beta | T/A |
| QA-PERF-006 | Concurrent next-quiz requests do not break reservation policy. | P1 | Pilot | T/A |

### 37.4. Scale honesty rule

Do not claim large-scale readiness unless load/performance tests support it. For Stanford-style presentation, distinguish:

```text
implemented and tested;
implemented but not load-tested;
planned scale architecture;
future optimization path;
```

---

## 38. CI/CD Quality Gates

### 38.1. CI purpose

CI must make quality visible and block unsafe changes before they reach protected branches or release.

### 38.2. Recommended CI checks

```text
documentation lint where feasible;
no-secrets scan;
JSON Schema validation;
import fixture tests;
unit tests;
database migration tests;
API contract validation;
OpenAPI validation;
Problem Details schema tests;
security smoke tests;
selection engine tests;
Telegram projection tests;
coverage/report generation smoke test;
```

### 38.3. CI gate matrix

| Gate | Required checks |
|---|---|
| Pull request | unit tests, schema tests, no-secrets scan, lint, targeted tests |
| Data/schema change | schema validation, import fixture tests, coverage report smoke test |
| API change | OpenAPI validation, contract tests, error schema tests, auth smoke tests |
| Security-sensitive change | security tests, no-secrets scan, authorization tests |
| Release candidate | full P0 suite, regression suite, generated QA report |
| Production release | release QA report, launch gates, backup/restore evidence where applicable |

### 38.4. Protected branch rule

Changes to `main` or release branches SHOULD require passing status checks. Required checks for launch-blocking areas MUST not be bypassed without documented waiver by Project Owner and QA Owner.

### 38.5. Illustrative CI workflow

Current committed CI is `.github/workflows/ci.yml`. It uses `unittest`,
`coverage`, committed public fixtures and dependency-free import/style guards.
The illustrative workflow below remains a target-pattern example, not the
source of exact command names.

```yaml
name: quality

on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: No secrets scan
        run: ./tools/scan_no_secrets.sh
      - name: Validate JSON schemas
        run: ./tools/validate_schemas.sh
      - name: Validate import manifest
        run: python3 tools/validate_manifest.py --manifest data/manifests/import_manifest.yml
      - name: Run unit tests
        run: pytest tests/unit
      - name: Run data-quality tests
        run: pytest tests/data-quality
      - name: Run API contract tests
        run: pytest tests/contract
      - name: Generate QA report
        run: python3 tools/generate_qa_report.py --out reports/release_qa_report.md
```

Tool names are illustrative unless already implemented.

---

## 39. Regression QA

### 39.1. Regression principle

Critical defects become permanent tests.

### 39.2. Regression test triggers

Create regression tests for any defect involving:

```text
draft/blocked/retired item delivery;
source traceability loss;
dry-run production write;
incorrect answer reference accepted;
API auth bypass;
object-level authorization bypass;
correct answer leakage;
quota/entitlement bypass;
wrong consumer analytics exposure;
Telegram duplicate posting;
webhook spoof/replay;
secret leakage;
backup/restore failure;
```

### 39.3. Regression test naming

```text
QA-REG-STAT-001
QA-REG-API-001
QA-REG-SEC-001
QA-REG-TG-001
```

### 39.4. Regression closure rule

A critical defect is not closed until:

```text
root cause identified;
fix implemented;
regression test added;
relevant QA suite passes;
release notes or incident notes updated if needed;
```

---

## 40. Defect Severity Model

### 40.1. Severity levels

| Severity | Meaning | Examples | Launch impact |
|---|---|---|---|
| S0 Critical | Safety/security/data integrity failure | auth bypass, draft delivery, secret leak, data corruption | Blocks launch immediately |
| S1 High | Major product rule failure | quota bypass, wrong status filter, broken import traceability | Blocks affected scope |
| S2 Medium | Important defect with workaround | report count mismatch, admin UX issue, non-critical validation gap | May block pilot/beta depending risk |
| S3 Low | Minor issue | copy, formatting, minor docs inconsistency | Does not block unless accumulates |
| S4 Enhancement | Improvement request | better dashboard, extra report | Not a defect |

### 40.2. Priority levels

| Priority | Meaning |
|---|---|
| P0 | Must fix before MVP/public delivery if relevant. |
| P1 | Must fix before Pilot/Production or accepted as residual risk. |
| P2 | Important for Beta/Scale. |
| P3 | Future enhancement. |

### 40.3. Defect record format

```yaml
defect_id: DEF-2026-0001
title: Draft item returned by next quiz endpoint
severity: S0
priority: P0
component: api / selection
requirement_ids:
  - SRS-STAT-004
  - SRS-API-005
test_id: QA-API-007
reproduction_steps:
  - create draft item
  - call POST /v1/quiz-items/next
expected: draft item excluded
actual: draft item returned
impact: normal consumer can receive non-production content
status: open
owner: API Owner
regression_required: true
```

---

## 41. Quality Metrics

### 41.1. Core QA metrics

| Metric | Target for MVP | Target for Pilot/Production |
|---|---:|---:|
| P0 requirements with verification method | 100% | 100% |
| P0 automated tests pass | 100% | 100% |
| Unresolved S0 defects | 0 | 0 |
| Unresolved P0 launch blockers | 0 | 0 |
| Approved/published items with source traceability | 100% | 100% |
| Delivery of non-eligible statuses in tests | 0 | 0 |
| API contract validation for core endpoints | pass | pass |
| Security smoke tests | pass | pass |
| Known limitations documented | yes | yes |
| Demo rehearsal completed | yes for demo | yes for major demos |

### 41.2. Data quality metrics

```text
validated canonical item count;
items by status;
items by CEFR;
items by theme;
items missing required metadata;
invalid correct answer reference count;
source traceability completeness;
duplicate/conflict candidates;
Telegram compatibility pass/fail count;
```

### 41.3. API quality metrics

```text
contract test pass rate;
P0 endpoint pass rate;
Problem Details coverage;
authorization test pass rate;
quota denial correctness;
average response time;
error rate;
```

### 41.4. Operations quality metrics

```text
backup success;
restore drill result;
incident response drill status;
monitoring coverage;
failed delivery count;
failed import count;
retry duplicate count;
```

---

## 42. Launch Gates — QA

### 42.1. MVP QA Gate

MVP QA gate passes when:

```text
QA-MVP-001  Foundational documents exist and are aligned.
QA-MVP-002  P0 requirements have verification methods.
QA-MVP-003  Source inventory exists or generation workflow exists.
QA-MVP-004  At least one sample/pilot source has source_id and checksum.
QA-MVP-005  Import manifest exists for at least one pilot source.
QA-MVP-006  Dry-run import creates structured report and no production items.
QA-MVP-007  Canonical schema exists and validates sample item.
QA-MVP-008  Draft items are blocked from normal delivery.
QA-MVP-009  Approved item can be selected for eligible consumer.
QA-MVP-010  API next-quiz endpoint returns only eligible status.
QA-MVP-011  Quota/entitlement denial can be demonstrated or simulated.
QA-MVP-012  Object-level authorization test exists for consumer-specific data.
QA-MVP-013  Correct answer hidden-mode exposure test exists.
QA-MVP-014  Delivery/reservation logging is demonstrated for delivery-producing request.
QA-MVP-015  New source onboarding can be demonstrated with sample file or evidence artifact.
QA-MVP-016  No unresolved S0 or P0 blockers for MVP scope.
```

### 42.2. Pilot QA Gate

Pilot QA gate passes when:

```text
QA-PILOT-001  Pilot sources have source_id/checksum/manifest/parser records.
QA-PILOT-002  Pilot import is reproducible.
QA-PILOT-003  Duplicate/conflict report exists for pilot import if applicable.
QA-PILOT-004  Telegram compatibility tests pass for pilot Telegram delivery.
QA-PILOT-005  Telegram worker logs successful and failed deliveries.
QA-PILOT-006  Entitlement/quota model works for pilot consumers.
QA-PILOT-007  API contract tests pass for pilot endpoints.
QA-PILOT-008  Security smoke tests pass.
QA-PILOT-009  Monitoring/logging exists for pilot.
QA-PILOT-010  Backup exists for pilot data if real pilot users/channels exist.
QA-PILOT-011  Known limitations are documented.
```

### 42.3. Beta QA Gate

Beta QA gate passes when:

```text
QA-BETA-001  Public API docs/OpenAPI are available for beta scope.
QA-BETA-002  Rate limits or usage controls exist and are tested.
QA-BETA-003  Security tests cover public beta attack surface.
QA-BETA-004  Billing/webhook tests pass if paid beta is active.
QA-BETA-005  Support/abuse reporting path exists.
QA-BETA-006  Analytics and logs do not expose private/cross-consumer data.
QA-BETA-007  Regression suite passes.
QA-BETA-008  Release QA report is generated.
```

### 42.4. Production QA Gate

Production QA gate passes when:

```text
QA-PROD-001  Production corpus is imported through controlled pipeline.
QA-PROD-002  No normal consumer can access raw CSV.
QA-PROD-003  P0/P1 release tests pass or residual P1 risks are formally accepted.
QA-PROD-004  Security baseline implemented and verified.
QA-PROD-005  Backup and restore drill completed.
QA-PROD-006  Monitoring and incident playbook exist.
QA-PROD-007  Deployment/rollback path exists.
QA-PROD-008  Payment/entitlement path verified if paid launch.
QA-PROD-009  No unresolved S0/P0 defects.
QA-PROD-010  Launch approval recorded.
```

### 42.5. Stanford Demo QA Gate

Stanford-style demo gate passes when:

```text
QA-DEMO-GATE-001  Demo script exists.
QA-DEMO-GATE-002  Demo data is safe and controlled.
QA-DEMO-GATE-003  Demo credentials are limited and non-production.
QA-DEMO-GATE-004  Demo shows corpus baseline and generated reports.
QA-DEMO-GATE-005  Demo shows source onboarding or evidence artifact.
QA-DEMO-GATE-006  Demo shows canonical validation.
QA-DEMO-GATE-007  Demo shows API next-quiz delivery.
QA-DEMO-GATE-008  Demo shows at least one negative control: draft blocked, quota denied or auth denied.
QA-DEMO-GATE-009  Demo shows delivery logging or evidence.
QA-DEMO-GATE-010  Demo limitations are explicit.
QA-DEMO-GATE-011  Demo rehearsal completed and recorded in QA evidence.
```

---

## 43. Stanford-Style Demo Verification Plan

### 43.1. Demo thesis

The demo must prove:

```text
This is not a folder of quiz files.
This is a governed API-first educational content platform.
```

### 43.2. Demo flow

Recommended demo path:

```text
1. Show corpus baseline report.
2. Show source inventory and manifest concept.
3. Register/onboard sample future source.
4. Run dry-run import.
5. Show canonical validation report.
6. Approve or use pre-approved sample item.
7. Call POST /v1/quiz-items/next for demo consumer.
8. Show delivery/reservation record.
9. Submit attempt or simulate attempt.
10. Show analytics/report update.
11. Show negative control: draft blocked or quota denied or auth denied.
12. Show Telegram simulated payload or controlled send.
13. Show QA gate/evidence summary.
```

### 43.3. Demo test cases

| Test ID | Demo test | Method |
|---|---|---|
| QA-DEMO-001 | Demo script can run end-to-end in demo environment. | R |
| QA-DEMO-002 | Demo source onboarding evidence exists. | R/D |
| QA-DEMO-003 | API next-quiz demo returns eligible item only. | R/T |
| QA-DEMO-004 | Negative control works. | R/T |
| QA-DEMO-005 | Demo does not expose secrets. | R/I |
| QA-DEMO-006 | Demo claims match implemented evidence. | I/R |
| QA-DEMO-007 | Fallback artifacts exist if live service fails. | I/R |

### 43.4. Demo evidence package

```text
demo script;
corpus snapshot report;
source onboarding report;
dry-run import report;
canonical validation report;
OpenAPI excerpt;
API request/response examples;
Problem Details negative-control example;
delivery log example;
Telegram simulated payload or controlled message evidence;
QA gate summary;
known limitations sheet;
architecture diagram;
roadmap boundaries;
```

### 43.5. Demo honesty rule

Every demo statement must be marked as one of:

```text
implemented and tested;
implemented and demonstrated manually;
simulated in controlled demo;
documented design, not yet implemented;
future roadmap;
```

---

## 44. Risk-Based QA Matrix

| Risk | Impact | QA control | Blocking level |
|---|---|---|---|
| Draft item delivered | Trust loss, product violation | QA-STAT-002, QA-API-007, QA-SEL-002 | S0/P0 |
| Correct answer leaked | Learning integrity/security issue | QA-ANS-001, QA-SEC-004 | S0/P0 |
| Cross-consumer access | Privacy/security breach | QA-SEC-002, QA-API-011 | S0/P0 |
| New source bypasses onboarding | Corpus chaos | QA-ONB-004, QA-ONB-008 | S0/P0 |
| Dry-run writes production data | Data corruption/governance failure | QA-IMP-001 | S0/P0 |
| Entitlement/quota bypass | Monetization failure | QA-BILL-002/003, QA-SEL-006/007 | S1/P0 |
| Telegram duplicate posting | Channel trust loss | QA-TG-007 | S1/P1 |
| Webhook spoofing | Unauthorized access grant | QA-BILL-006, QA-SEC-008 | S0/P1 |
| Analytics cross-leak | Privacy/business risk | QA-AN-005 | S0/P1 |
| Backup restore failure | Production recovery failure | QA-OPS-004 | S0/P0 for prod |
| Demo overclaiming | Credibility failure | QA-DEMO-006 | S1/P1 |

---

## 45. Change Control for QA

### 45.1. When QA artifacts must change

Update QA when any of these change:

```text
SRS requirement added/changed/removed;
use case added/changed/removed;
domain entity/status changes;
canonical schema changes;
OpenAPI endpoint/schema changes;
security threat/control changes;
source onboarding workflow changes;
billing/entitlement logic changes;
Telegram adapter constraints change;
launch gate changes;
critical defect discovered;
```

### 45.2. QA change record

QA-impacting PR should answer:

```text
What requirement changed?
What tests are added/updated?
What existing tests may fail?
Does this affect launch gates?
Does this affect demo claims?
Does this create new security or operations risk?
```

### 45.3. No orphan change rule

A new feature is not complete if it has:

```text
no requirement mapping;
no test mapping;
no negative test for serious risk;
no documentation update when contract changes;
```

---

## 46. Manual QA and Exploratory Testing

### 46.1. When manual QA is appropriate

Manual QA is appropriate for:

```text
admin workflow usability;
content review process observation;
demo rehearsal;
new ambiguous source format exploration;
first Telegram real channel pilot;
visual inspection of generated reports;
edge case discovery before automation;
```

### 46.2. Manual QA rules

Manual QA must still be structured:

```text
test_id;
scenario;
preconditions;
steps;
expected result;
actual result;
evidence screenshot/log/report;
pass/fail;
owners;
date;
follow-up defects;
```

### 46.3. Exploratory charter examples

```text
Explore admin approval workflow for missing metadata.
Explore import behavior with unusual CSV delimiters.
Explore API error messages for invalid filters.
Explore Telegram payload with long German compound nouns.
Explore teacher pack request with narrow CEFR/theme filters.
Explore analytics reports for empty/edge datasets.
```

---

## 47. Sample P0 Test Suite

### 47.1. Minimal P0 MVP suite

```text
QA-DOC-001    Foundational docs exist.
QA-DOC-002    P0 requirements have verification mapping.
QA-SRC-001    Inventory exists or can be generated.
QA-SRC-002    Active source has source_id.
QA-SRC-003    Active/importable source has checksum.
QA-ONB-004    New source cannot publish without validation/status workflow.
QA-IMP-001    Dry-run import creates no production items.
QA-IMP-004    Source locator is preserved.
QA-DATA-001   Valid canonical item passes schema.
QA-DATA-004   Invalid correct option reference fails.
QA-DATA-008   Status enum enforced.
QA-TAX-001    CEFR values constrained to A1-C2.
QA-STAT-002   Draft item not delivered.
QA-STAT-005   Blocked item not delivered.
QA-SEL-001    Approved item selectable.
QA-SEL-007    Quota exceeded prevents delivery.
QA-API-003    OpenAPI contract exists.
QA-API-005    POST /v1/quiz-items/next returns eligible item only.
QA-API-008    Quota exceeded returns machine-readable error.
QA-API-010    Unauthorized request denied.
QA-API-012    Correct answer hidden in hidden mode.
QA-SEC-002    Cross-consumer access denied.
QA-SEC-006    No secrets in repository.
QA-DEMO-004   Negative control works.
```

### 47.2. Minimal Pilot add-on suite

```text
QA-DUP-001    Exact duplicate detected.
QA-DUP-003    Answer conflict blocks publication.
QA-TG-002     Telegram worker uses API/selection engine.
QA-TG-004     Telegram incompatible item blocked.
QA-TG-005     Telegram delivery logged.
QA-BILL-004   Usage recorded.
QA-AN-001     Delivery analytics match records.
QA-OPS-003    Backup artifact created.
QA-OPS-004    Restore drill succeeds.
QA-PERF-001   Selection latency measured.
```

---

## 48. Test Command Seeds

Current committed commands are listed first. Later examples remain illustrative
where the exact future tool does not exist yet.

```bash
# Current committed MVP gates
python3 tools/no_secrets_scan.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m unittest tests.test_import_cycle_guard tests.test_style_numeric_limits tests.test_database_backend_contract
python3 -m coverage run -m unittest tests.test_database_backend_contract tests.test_mvp_admin tests.test_mvp_coverage_branches tests.test_mvp_projections tests.test_mvp_rate_limit tests.test_mvp_runtime tests.test_mvp_selection_contract tests.test_mvp_selection_decisions tests.test_mvp_selection_policy tests.test_mvp_weighted_selection tests.test_pre_pilot_runtime_invariants tests.test_protected_beta tests.test_telegram_shuffle tests.test_telegram_photo_gate_coverage tests.test_visual_access_gate_coverage tests.test_visual_cache tests.test_visual_prompt_builder tests.test_visual_provider tests.test_visual_qa tests.test_visual_runtime_gate_coverage tests.test_visual_settings tests.test_website_quiz_teaser_beta
python3 -m coverage report

# Documentation / inventory
python3 tools/quizbank_readme.py --quizbank-dir QuizBank --out README.md
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --format json --out reports/inventory.json
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank --format json --out reports/constitution_check.json

# Manifest and schema
python3 tools/validate_manifest.py --manifest data/manifests/import_manifest.yml
python3 tools/validate_schema.py --schema data/schemas/quiz_item.schema.json --input tests/fixtures/valid_quiz_item.json
python3 tools/validate_schema.py --schema data/schemas/quiz_item.schema.json --input tests/fixtures/invalid_quiz_item.json --expect-fail

# Import
python3 tools/run_import.py --source-id src_fixture_valid --dry-run --out reports/import_dry_run.json
python3 tools/run_import.py --source-id src_fixture_invalid --dry-run --expect-validation-errors

# API
pytest tests/contract
pytest tests/integration/test_next_quiz.py
pytest tests/security/test_object_authorization.py

# Telegram
pytest tests/integration/test_telegram_projection.py
pytest tests/integration/test_telegram_worker_dry_run.py

# Reports
python3 tools/coverage_report.py --format json --out reports/coverage.json
python3 tools/generate_release_qa_report.py --out reports/release_qa_report.md
```

---

## 49. Release QA Report Template

```markdown
# API Quiz Bank — Release QA Report

Release: <version / date / commit>
Environment: <MVP / Pilot / Beta / Production / Demo>
QA Owner: <name>
Date: <date>

## 1. Scope

## 2. Documents verified

## 3. Requirements coverage

| Priority | Total | Verified | Missing | Notes |
|---|---:|---:|---:|---|

## 4. Test summary

| Suite | Passed | Failed | Skipped | Blockers |
|---|---:|---:|---:|---:|

## 5. Launch gates

| Gate | Status | Evidence |
|---|---|---|

## 6. Defects

| Defect | Severity | Status | Decision |
|---|---|---|---|

## 7. Security summary

## 8. Data quality summary

## 9. API quality summary

## 10. Operations readiness

## 11. Known limitations

## 12. Release decision

Decision: approved / blocked / approved with accepted limitations
Approver:
Date:
```

---

## 50. QA Acceptance Criteria

This QA strategy is accepted when:

```text
AC-QA-001   It defines QA scope and non-goals.
AC-QA-002   It aligns with SRS NFR-QA requirements.
AC-QA-003   It defines test ID system.
AC-QA-004   It defines verification methods and evidence requirements.
AC-QA-005   It covers source registry and future source onboarding.
AC-QA-006   It covers import, dry-run and canonical validation.
AC-QA-007   It covers status lifecycle and publication control.
AC-QA-008   It covers selection engine and anti-repeat logic.
AC-QA-009   It covers API contract, Problem Details, auth and projections.
AC-QA-010   It covers correct answer exposure.
AC-QA-011   It covers Telegram adapter and delivery logging.
AC-QA-012   It covers billing, entitlements and quotas.
AC-QA-013   It covers analytics and reporting.
AC-QA-014   It covers security testing and threat model alignment.
AC-QA-015   It covers operations, backup/restore and incident readiness.
AC-QA-016   It defines CI/CD gates.
AC-QA-017   It defines launch gates for MVP, Pilot, Beta, Production and Demo.
AC-QA-018   It defines defect severity and regression rules.
AC-QA-019   It defines Stanford-style demo evidence requirements.
AC-QA-020   It states that hidden limitations and unsupported launch claims are not allowed.
```

---

## 51. Open QA Questions

These questions must be resolved or explicitly deferred:

```text
OQ-QA-001   Which test runner/framework will be used for backend/API tests?
OQ-QA-002   Will import/data validation tools be Python-first, service-integrated or both?
OQ-QA-003   Which OpenAPI validation tool will be used in CI?
OQ-QA-004   Which secrets scanner will be mandatory in CI?
OQ-QA-005   Which environment will host Stanford-style demo?
OQ-QA-006   What is the first pilot source file for import demonstration?
OQ-QA-007   What is the first Telegram pilot channel or simulated channel?
OQ-QA-008   What exact SLA/latency targets should apply after MVP?
OQ-QA-009   What billing provider will be first, if any?
OQ-QA-010   Which tests must be automated before Pilot vs allowed manual evidence?
```

Open questions do not block this QA strategy document. They block implementation or launch only when they affect a required gate.

---

## 52. Reference Standards and Alignment

### 52.1. Project references

```text
CONSTITUTION.md
README.md
00_vision.md
01_product_charter.md
02_requirements_srs.md
03_use_cases.md
04_domain_model.md
05_architecture.md
06_data_standard.md
07_api_standard.md
08_security_threat_model.md
```

### 52.2. External references

```text
Stanford/SLAC Software Requirements and Analysis Methodology
SLAC Quality Assurance Program
CEFR level descriptions
OpenAPI Specification
JSON Schema Draft 2020-12
RFC 9110 HTTP Semantics
RFC 9457 Problem Details for HTTP APIs
OWASP API Security Top 10
OWASP Application Security Verification Standard
OWASP Web Security Testing Guide
NIST SP 800-218 Secure Software Development Framework
Telegram Bot API
GitHub protected branches / required status checks
```

---

## 53. Final QA Rule

```text
API Quiz Bank is not quality-ready because files exist.
API Quiz Bank is not quality-ready because a test suite exists.
API Quiz Bank is not quality-ready because one demo works once.

API Quiz Bank is quality-ready only when the system can prove, with traceable evidence,
that governed sources become validated canonical data,
canonical data becomes controlled production records,
production records are selected only by explicit rules,
API delivery is authorized, safe and logged,
Telegram and other consumers cannot bypass the platform core,
entitlements and quotas are enforced,
security risks are tested,
operations can recover,
future quiz files can be onboarded safely,
and every launch or presentation claim is backed by a requirement, test, report, log or demo artifact.
```
