# QuizBank Constitution

**Project:** German QuizBank Platform  
**Document:** CONSTITUTION.md  
**Version:** 1.0.0  
**Status:** Binding Operational Constitution  
**Language:** Ukrainian, with canonical technical terms in English  
**Effective from:** first repository adoption  
**Owner:** QuizBank project owner / authorized product maintainer  
**Purpose:** перетворити перевірений банк німецьких вікторин на керовану, масштабовану, API-first платформу, готову до професійної демонстрації, запуску, підтримки, монетизації та презентації на рівні Stanford-style engineering review.

---

## 0. Преамбула

QuizBank існує не як набір CSV-файлів і не як одноразовий сайт з вікторинами. QuizBank існує як центральна освітньо-технологічна платформа для німецької мови, де перевірений контент перетворюється на керований цифровий продукт через правила, схеми, імпорт, базу даних, API, selection engine, Telegram/боти/сайт/додатки, аналітику, оплату, безпеку й операційну дисципліну.

Ця Конституція є головним законом проєкту. Вона встановлює правила, за якими всі файли, дані, сервіси, команди, інтеграції, документи, релізи та публічні демонстрації мають працювати разом. Якщо інший документ, код, скрипт, README, технічне рішення або усна домовленість суперечить цій Конституції, пріоритет має Конституція.

QuizBank уже має перевірений корпус вікторин. Мета цієї Конституції — не повторний аудит змісту кожного питання, а наведення системного порядку: source governance, canonical data model, import workflow, operational statuses, API-first delivery, publication controls, analytics, billing, access management, documentation, engineering discipline and presentation readiness.

---

## 1. Статус Конституції

### 1.1. Юридично-операційний статус усередині проєкту

Цей документ є обовʼязковим для:

- структури репозиторію;
- правил роботи з raw CSV files;
- import pipeline;
- canonical quiz item schema;
- database model;
- API contract;
- Telegram delivery;
- web/admin products;
- billing and entitlements;
- analytics;
- security;
- CI/CD;
- documentation;
- Stanford-ready presentation package.

### 1.2. Нормативна мова

У цьому документі використовуються такі рівні обовʼязковості:

- **MUST / ОБОВʼЯЗКОВО** — правило, без якого проєкт не може вважатися compliant.
- **MUST NOT / ЗАБОРОНЕНО** — дія, яка прямо порушує Конституцію.
- **SHOULD / РЕКОМЕНДОВАНО** — правило, яке треба виконувати за замовчуванням; виняток дозволений лише з письмовим обґрунтуванням.
- **MAY / ДОЗВОЛЕНО** — опція, яку можна використовувати, якщо вона не порушує жодного обовʼязкового правила.

### 1.3. Конституційний принцип

QuizBank SHALL be governed before it is scaled.  
Спочатку правила, структура, джерела правди, імпорт, схема даних, API, контроль доступу й операційна дисципліна. Потім — сайт, Telegram, автоматизація, платні продукти, інтеграції й масштабування.

---

## 2. Місія

### 2.1. Головна місія

QuizBank має стати масштабованою платформою німецьких вікторин, яка безпечно й контрольовано доставляє перевірений навчальний контент через API, Telegram, сайт, боти, додатки, освітні кабінети, школи, викладачів, зовнішні інтеграції та платні продукти.

### 2.2. Продуктова формула

```text
Verified German quiz content
  → governed source system
  → canonical data model
  → import and normalization pipeline
  → production database
  → selection engine
  → versioned API
  → Telegram / web / bots / apps / schools / external clients
  → analytics / billing / quality feedback / scale
```

### 2.3. Що QuizBank не є

QuizBank НЕ є:

- хаотичною папкою CSV-файлів;
- сайтом, який напряму читає CSV;
- Telegram-ботом, який сам вирішує, які питання видавати;
- разовим освітнім архівом;
- ручною таблицею без versioning;
- системою, де “оплатив” автоматично означає “має доступ до всього”;
- системою, де production-рішення приймаються без schema, manifest, changelog і traceability.

### 2.4. Що QuizBank є

QuizBank Є:

- governed content platform;
- CEFR-aware German quiz bank;
- API-first delivery system;
- source-traceable data product;
- operationally controlled educational infrastructure;
- scalable foundation for Telegram channels, bots, web, apps, schools and API clients;
- platform prepared for professional Stanford-style technical presentation.

---

## 3. Базові факти про поточний корпус

### 3.1. Поточний baseline

На момент актуального corpus snapshot operational baseline має такі ознаки:

- top-level corpus у форматі CSV;
- 115 active bank files;
- 30,974 active rows/items;
- усі active items мають operational status `draft`;
- canonical levels представлені значеннями `A1`, `A2`, `B1`, `B2`, `C1`, `C2`;
- coverage completeness визначається матрицею `level × theme_id × objective_id × pattern_id`;
- локальний constitution check для наявного snapshot не показує порушень.

### 3.2. Тлумачення статусу `draft`

Статус `draft` у поточному корпусі НЕ означає, що вікторини неправильні або неперевірені за змістом. У цьому проєкті `draft` на старті означає: item ще не введений у production workflow платформи, не має повного production metadata package, не пройшов publication gate і не має права автоматично видаватися користувачам.

### 3.3. Відмежування content audit від operational launch

Перший етап роботи після ухвалення Конституції НЕ включає повторний змістовий аудит усіх відповідей. Перший етап включає:

- структуризацію файлів;
- file inventory;
- import manifest;
- source IDs;
- checksums;
- canonical schema;
- статуси;
- importer rules;
- database model;
- API contract;
- selection engine policy;
- publication gates;
- Telegram/API launch discipline.

Operational validation is required. Full re-audit of already checked quiz content is not required unless конкретний item отримує report, conflict, structural anomaly, duplicate conflict, missing required metadata, legal/safety concern or explicit owner request.

---

## 4. Основні принципи

### 4.1. API-first

Усі зовнішні та внутрішні consumers повинні отримувати питання через versioned API або через сервіс, який офіційно використовує API/selection engine. Direct raw file access by consumers is prohibited.

### 4.2. Raw files are source assets, not the product

CSV-файли є джерелом походження та імпорту. Продуктом є керована база знань із canonical items, status lifecycle, API, selection logic, access control, delivery history, analytics and operations.

### 4.3. One canonical data model

Незалежно від того, скільки CSV-файлів, форматів, назв колонок або історичних особливостей існує, production-система повинна мати один canonical quiz item model.

### 4.4. Traceability by design

Кожен production item повинен мати source traceability: source file, source row/block where possible, source checksum, import batch, content hash and version.

### 4.5. No publication without status

Жоден item не може бути виданий у Telegram, API, сайт, бот, додаток, школу або платний продукт без дозволеного publication status.

### 4.6. Centralized selection

Вибір питань повинен здійснювати central selection engine, а не окремий Telegram-бот, сайт, скрипт або випадковий SQL-запит.

### 4.7. Anti-repeat is mandatory

Система повинна знати, що було видано конкретному consumer, user, channel, group, school or API client, і повинна застосовувати repeat policy.

### 4.8. Entitlements, not vague payment

Доступ визначається планами, квотами й entitlements. Payment status alone is insufficient.

### 4.9. Documentation is infrastructure

Документація не є прикрасою. Vision, SRS, use cases, architecture, data standard, API standard, security, operations, billing, presentation outline and changelog are production infrastructure.

### 4.10. Stanford-ready means system-ready

Stanford-ready presentation означає демонстрацію керованої системи, а не тільки великої кількості питань. Потрібно показати corpus, governance, requirements, architecture, data model, API, Telegram demo, analytics, monetization, operations, security and roadmap.

---

## 5. Нормативні стандарти проєкту

### 5.1. Engineering and requirements discipline

QuizBank adopts a Stanford/SLAC-style engineering approach:

```text
goal → needs → features → system requirements → use cases → test cases → traceability → change control → releases
```

Для кожної серйозної функції має існувати звʼязок:

```text
Vision objective
  → requirement ID
  → use case
  → implementation component
  → test/acceptance criteria
  → release note
```

### 5.2. Language learning standard

CEFR levels `A1`, `A2`, `B1`, `B2`, `C1`, `C2` є canonical external learning-level standard. Internal difficulty може існувати як додатковий параметр, але не може замінювати CEFR.

### 5.3. API standard

API contract MUST use OpenAPI. API endpoints MUST be versioned. API consumers MUST be able to understand service capability from the API contract, not from private code.

### 5.4. Data validation standard

Canonical quiz item schema SHOULD be expressed in JSON Schema 2020-12 or compatible schema tooling. Schema must support validation, documentation and machine-readability.

### 5.5. HTTP and error standard

HTTP behavior MUST be consistent. API errors SHOULD use Problem Details style JSON with fields such as `type`, `title`, `status`, `detail`, `instance` and optional project-specific extensions.

### 5.6. Security standard

API security MUST account for broken object-level authorization, broken authentication, object-property authorization, excessive data exposure, unrestricted resource consumption, unsafe third-party integrations and insufficient monitoring.

### 5.7. Repository standard

Repository governance SHOULD include README, CONSTITUTION, LICENSE decision, SECURITY, CONTRIBUTING, CODEOWNERS, CHANGELOG, branch protection, CI checks, dependency monitoring, tests and generated inventory reports.

### 5.8. Telegram compatibility

Telegram delivery MUST respect Telegram poll/quiz constraints, including allowed number of options, quiz mode, correct option handling, explanation limits, scheduling behavior and delivery logging.

---

## 6. Терміни та доменна модель

### 6.1. Core terms

**Quiz Item** — одна одиниця вікторини: питання, варіанти, правильна відповідь, метадані, статус, джерело.  
**Stem** — текст питання або завдання.  
**Option** — один варіант відповіді.  
**Correct Answer** — правильна option або набір правильних options.  
**Explanation** — пояснення, чому відповідь правильна.  
**Source File** — raw CSV або інший файл походження.  
**Source ID** — стабільний ідентифікатор source file.  
**Content Hash** — deterministic fingerprint normalized item content.  
**Canonical Item** — item у єдиній внутрішній структурі платформи.  
**Production Item** — canonical item, доступний production-сервісам згідно зі статусом.  
**Consumer** — сайт, Telegram channel, Telegram bot, mobile app, school, teacher dashboard, API client, scheduler or integration.  
**Delivery** — факт видачі item конкретному consumer/user/channel.  
**Attempt** — відповідь користувача або recorded interaction з item.  
**Entitlement** — конкретне право доступу до feature, level, topic, limit, API quota or channel automation.  
**Publication Gate** — набір умов, які item або release має виконати перед production delivery.

### 6.2. Taxonomy terms

**CEFR Level** — `A1`, `A2`, `B1`, `B2`, `C1`, `C2`.  
**Theme** — одна з головних тем, позначена canonical `theme_id` such as `T01`…`T18`.  
**Objective** — навчальна ціль, позначена `objective_id` such as `O01`…`O15`.  
**Pattern** — тип вправи/мислення/питання, позначений `pattern_id` such as `P01`…`P12`.  
**Tag** — додатковий label для grammar, vocabulary, context, skill, format or usage.  
**Coverage Cell** — комбінація `level × theme_id × objective_id × pattern_id`.

### 6.3. System terms

**Import Manifest** — YAML/JSON document, який описує, які файли імпортуються, яким parser, з якими defaults, checksums and status.  
**File Inventory** — generated or controlled CSV/JSON report про source files.  
**Importer** — tool/service, який читає raw source and emits canonical items.  
**Normalizer** — component, який приводить text, options, levels, theme/objective/pattern IDs до canonical form.  
**Validator** — component, який перевіряє schema and operational rules.  
**Selection Engine** — component, який вибирає items for consumers while respecting levels, topics, status, repeat policy, quotas and quality rules.  
**Admin Workflow** — process for import, review, approval, publication, retirement and monitoring.  
**API Contract** — OpenAPI description of endpoints, schemas, auth, errors and webhooks.

---

## 7. Джерело правди

### 7.1. Three-layer source model

QuizBank uses a three-layer source model:

```text
Layer 1 — Raw Source Assets
  CSV files and original source materials.

Layer 2 — Reproducible Canonical Data
  canonical JSONL/records generated from raw sources through manifest-driven import.

Layer 3 — Production Source of Truth
  production database with versioned records, statuses, delivery history, entitlements, analytics and operational metadata.
```

### 7.2. Raw source rule

Raw CSV files MUST be treated as immutable source assets after snapshot adoption. They may be moved into a governed directory, but their content must not be silently edited. Any correction must be represented through controlled patch, import version, canonical override or explicitly tracked source update.

### 7.3. Production truth rule

Production consumers MUST NOT read raw CSV files directly. Production truth for delivery is the database state created from controlled import pipelines and governed by statuses.

### 7.4. Generated report rule

Generated README/inventory reports MUST NOT be treated as manually editable truth. They are reports derived from source state and tooling.

### 7.5. Conflict resolution

When raw file, canonical item, database item and delivery history disagree, resolution order is:

```text
1. Constitution and data standard
2. Production database with version history
3. Import manifest and source checksum
4. Canonical generated dataset
5. Raw source file
6. Generated README/report
7. Ad hoc manual notes
```

This does not mean raw files are unimportant. It means raw files prove origin; production database governs delivery.

---

## 8. Corpus and file governance

### 8.1. Required corpus directories

The repository SHOULD eventually use this structure:

```text
QuizBank/
  README.md                       # generated report, do not edit manually
  CONSTITUTION.md                 # binding constitution
  docs/
  data/
    raw/
    manifests/
    taxonomy/
    schemas/
    normalized/
  tools/
  services/
  libs/
  database/
  infra/
  tests/
```

If current working state still has top-level CSV files, migration to `data/raw/` MUST be planned through inventory and checksums, not manual chaos.

### 8.2. File inventory

A governed corpus MUST have `data/manifests/file_inventory.csv` or equivalent with at least:

```text
source_id
filename
original_path
current_path
format
encoding
row_count
active_item_count
known_level_range
known_theme_id
known_objective_ids
known_pattern_ids
parser_name
checksum_sha256
status
first_seen_at
last_seen_at
notes
```

### 8.3. Source ID policy

Every active bank file MUST receive a stable `source_id`, for example:

```text
src_0001
src_0002
src_0003
```

Source IDs MUST NOT change because a file is moved, renamed or re-imported. If a source file is split, merged or replaced, the operation MUST be documented.

### 8.4. Checksum policy

Every source file MUST have a checksum. Checksum changes MUST trigger an import impact review.

### 8.5. File status values

Source file status MUST be one of:

```text
active
archived
template
ignored
deprecated
superseded
blocked
under_review
```

### 8.6. Template files

Service templates such as sheet templates MUST be clearly marked as `template` and MUST NOT be imported as active quiz banks.

### 8.7. Manual rearrangement prohibition

Manual moving, renaming, deleting or rewriting source files without updating inventory, manifest and checksums is prohibited.

---

## 9. Import manifest

### 9.1. Import manifest requirement

No active source file may enter production workflow without a manifest entry.

### 9.2. Minimal manifest record

Each manifest entry MUST contain:

```yaml
sources:
  - id: src_0001
    path: data/raw/src_0001/example.csv
    parser: csv_quizbank_v1
    format: csv
    encoding: utf-8
    status: active
    checksum_sha256: "..."
    default_level: null
    default_theme_id: null
    default_objective_id: null
    default_pattern_id: null
    import_policy: standard
    notes: null
```

### 9.3. Parser declaration

Each source MUST declare parser. A parser MUST define:

- expected columns;
- column mapping;
- handling of compatibility fields such as `sublevel`;
- normalization rules;
- error rules;
- row-to-item conversion;
- option mapping;
- correct answer mapping;
- metadata extraction;
- output canonical schema version.

### 9.4. Import batch

Every import run MUST produce an import batch record with:

```text
import_batch_id
started_at
finished_at
operator/tool
source_ids
schema_version
items_created
items_updated
items_unchanged
items_blocked
errors_count
warnings_count
report_path
```

### 9.5. Reproducibility

Given the same raw sources, manifest, parser versions and schema version, import output SHOULD be reproducible.

---

## 10. Canonical quiz item

### 10.1. Canonical item purpose

The canonical quiz item is the single internal representation used by validators, database import, API, selection engine, Telegram worker and analytics.

### 10.2. Required item fields for production

A production item MUST have:

```text
id or public_id
schema_version
stem_de
options
correct_option_ids
cefr_level
theme_id
objective_id
pattern_id
status
source_file_id
source_locator
content_hash
created_at
updated_at
```

### 10.3. Strongly recommended fields

A production-grade item SHOULD have:

```text
explanation_de
explanation_uk
subtheme_id
tags
difficulty_seed
difficulty_calibrated
quality_score
telegram_ready
web_ready
api_ready
review_notes
approved_by
approved_at
published_at
retired_at
metadata_json
```

### 10.4. Options rule

A quiz item MUST have at least 2 options. For Telegram quiz compatibility, production delivery SHOULD support a maximum aligned with Telegram poll limits unless the consumer format explicitly supports more.

### 10.5. Correct answer rule

Every item MUST have at least one correct answer reference. Correct answer references MUST point to existing options.

### 10.6. German text rule

The main learning stem MUST be in German or contain the German-language task being evaluated. Ukrainian explanations, translations or admin notes are allowed as supplementary fields.

### 10.7. Content hash rule

The content hash SHOULD be calculated from normalized stem, normalized options, correct answer references, level, theme, objective and pattern. Hash rules MUST be documented to make duplicate detection reproducible.

### 10.8. Version rule

If content changes materially, item version MUST change. Delivery history MUST preserve which version was delivered.

### 10.9. Compatibility field rule

If historical source uses `sublevel`, it may remain a compatibility source field. Canonical output MUST use `cefr_level` with values `A1–C2`.

---

## 11. Taxonomy and coverage

### 11.1. Canonical taxonomy files

The project MUST maintain taxonomy files:

```text
data/taxonomy/cefr_levels.yml
data/taxonomy/themes.yml
data/taxonomy/objectives.yml
data/taxonomy/patterns.yml
data/taxonomy/tags.yml
```

### 11.2. CEFR levels

Allowed canonical CEFR levels:

```text
A1, A2, B1, B2, C1, C2
```

No production item may use arbitrary values such as `beginner`, `easy`, `advanced`, `A1-A2` as canonical level. Ranges may exist as source metadata or search filters but must resolve to canonical level values for items.

### 11.3. Themes

The project currently uses 18 canonical themes identified as `T01`…`T18`. Each theme MUST have:

```text
theme_id
slug
title_uk
title_de
description
allowed_levels
status
```

### 11.4. Objectives

Each objective MUST have:

```text
objective_id
slug
title_uk
title_de
description
skill_area
status
```

### 11.5. Patterns

Each pattern MUST have:

```text
pattern_id
slug
title_uk
title_de
description
question_type
status
```

### 11.6. Coverage matrix

Coverage MUST be measured by:

```text
level × theme_id × objective_id × pattern_id
```

Coverage reports MUST distinguish:

- fully covered cells;
- thin cells;
- missing cells;
- overrepresented cells;
- cells not required for a given product stage.

### 11.7. Multi-label rule

Each item SHOULD have one primary theme and may have multiple tags. Multi-theme association is allowed, but one primary theme is required for selection and reporting.

---

## 12. Status lifecycle

### 12.1. Item statuses

Every item MUST have exactly one operational status:

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

### 12.2. Status definitions

**draft** — item exists in corpus or canonical staging but is not production-released.  
**imported** — item was read from source and recorded in import batch.  
**normalized** — item was transformed into canonical schema.  
**needs_review** — item requires human or operational review due to missing metadata, low confidence, conflict, duplicate suspicion or report.  
**approved** — item may be used by internal production systems but is not necessarily actively delivered.  
**published** — item may be delivered through API, Telegram, web, bots, schools or paid products.  
**monitored** — item is published but under observation due to reports, unusual analytics or quality flags.  
**retired** — item is no longer used for new delivery but historical data remains.  
**blocked** — item must not be delivered due to error, dispute, policy issue, metadata failure or owner decision.

### 12.3. Allowed transitions

```text
draft → imported → normalized → approved → published → monitored → retired
                         ↘ needs_review → approved
                         ↘ blocked
approved → needs_review
published → monitored
published → retired
published → blocked
monitored → published
monitored → retired
monitored → blocked
retired → approved only by explicit owner approval
blocked → needs_review only by explicit owner approval
```

### 12.4. Publication rule

Only `approved` or `published` items may be candidates for production selection. Public consumer delivery SHOULD use only `published` unless the environment is an internal pilot.

### 12.5. Draft protection

Draft items MUST NOT be delivered to public channels, paid users, external API clients or school consumers.

### 12.6. Blocking rule

Blocked items MUST be excluded from all selection, delivery and demo flows.

### 12.7. Retirement rule

Retired items MUST remain queryable for historical analytics, but MUST NOT be selected for new delivery unless explicitly reactivated.

---

## 13. Quality policy

### 13.1. Scope of quality policy

Quality in QuizBank has two layers:

1. **Content correctness** — чи правильне саме питання й відповідь.
2. **Operational quality** — чи item має правильну структуру, metadata, status, source traceability, delivery compatibility and analytics behavior.

The initial launch foundation focuses on operational quality because content has already been checked.

### 13.2. Operational quality gates

Before production publication, item MUST pass:

```text
schema validation
required fields check
valid level/theme/objective/pattern check
options/correct answer consistency
source traceability check
status check
duplicate/hash check
consumer compatibility check
security/safety exclusion check
```

### 13.3. No unnecessary re-audit

The system MUST NOT require full manual re-audit of every already checked quiz item as a prerequisite for structural launch. However, targeted review MUST occur when:

- item is reported by user/admin;
- answer mapping is structurally ambiguous;
- duplicate conflict exists;
- CEFR/theme/objective/pattern is missing or inconsistent;
- source traceability is broken;
- item violates publication format;
- item has abnormal analytics after delivery;
- owner requests targeted review.

### 13.4. Quality metrics

The platform SHOULD track:

```text
schema pass rate
missing metadata rate
duplicate suspicion rate
blocked item rate
wrong-answer reports
average correctness
item difficulty
item discrimination signal
response time
repeat exposure
consumer satisfaction
coverage gaps
import error rate
delivery failure rate
```

### 13.5. Reports and feedback

Users, teachers, admins and consumers SHOULD have a way to report suspicious items. A reported item SHOULD move to `monitored` or `needs_review` depending on severity.

### 13.6. Quality score

A `quality_score` may be computed from metadata completeness, source confidence, report history, analytics stability and review history. It SHOULD influence selection ranking, but MUST NOT override blocked status.

---

## 14. Database model

### 14.1. Database as production system

Production delivery MUST use a governed database, not direct CSV access.

### 14.2. Core tables

The production database SHOULD include at minimum:

```text
source_files
import_batches
quiz_items
quiz_item_versions
quiz_options
quiz_item_topics
quiz_item_tags
themes
objectives
patterns
consumers
consumer_rules
deliveries
attempts
users
organizations
plans
entitlements
usage_events
reports
audit_log
```

### 14.3. Source metadata

`source_files` MUST preserve:

```text
source_id
filename
original_path
current_path
checksum
parser_name
status
first_imported_at
last_imported_at
notes
```

### 14.4. Item versioning

Material edits to stem, options, correct answers, level, theme, objective or pattern MUST create a new version or explicit version record.

### 14.5. Delivery history

Every production delivery MUST be logged with:

```text
delivery_id
consumer_id
quiz_item_id
quiz_item_version
delivery_channel
delivered_at
status
external_message_id when available
```

### 14.6. Attempts

Every user attempt, where technically available, SHOULD record:

```text
attempt_id
user_id or anonymous/session id
consumer_id
quiz_item_id
quiz_item_version
selected_option_ids
is_correct
response_time_ms
created_at
```

### 14.7. Audit log

Admin actions MUST be logged. Critical actions include approve, publish, block, retire, schema change, manual metadata override, entitlement grant, billing override, consumer rule change and source import.

---

## 15. Selection engine

### 15.1. Central rule

All quiz selection MUST go through the selection engine or a service that implements the selection engine contract.

### 15.2. Selection inputs

Selection engine MUST consider:

```text
consumer_id
consumer type
allowed CEFR levels
allowed themes
allowed objectives
allowed patterns
item status
repeat policy
daily/monthly quota
quality_score
blocked flags
delivery history
user history when available
product plan
channel schedule
language mode
```

### 15.3. Selection output

Selection output MUST include:

```text
quiz_item_id
quiz_item_version
reason/selection metadata
consumer_id
reservation/delivery token when needed
expiration time when needed
```

### 15.4. Anti-repeat policy

Each consumer MUST have repeat policy. A default policy SHOULD be:

```text
same consumer: no repeat within configured window
same user: avoid repeat until topic pool exhausted
same channel: avoid repeat until channel cycle exhausted or window expired
school/group: avoid repeat within assigned module unless intentional review mode
```

### 15.5. Reservation

For scheduled or concurrent delivery, item selection SHOULD support reservation to prevent duplicate delivery in race conditions.

### 15.6. Fallback rule

If no candidates are available, the system MUST NOT randomly ignore rules. It MUST return a controlled error or fallback path, for example:

```text
no_candidate_available
quota_exceeded
coverage_gap
repeat_window_exhausted
consumer_not_configured
```

### 15.7. Adaptive difficulty

The platform MAY introduce calibrated difficulty based on attempts, correctness and response time. This MUST be treated as post-MVP unless enough data exists.

---

## 16. API constitution

### 16.1. API-first rule

All product consumers MUST integrate through API, internal service contract or authorized worker. Direct database access by public consumers is prohibited.

### 16.2. Versioning

API MUST be versioned:

```text
/v1/...
/v2/...
```

Breaking changes require a new major API version or formal migration plan.

### 16.3. Minimum endpoints

MVP API SHOULD include:

```text
GET /v1/health
GET /v1/topics
GET /v1/levels
GET /v1/quiz-items/{id}
GET /v1/quiz-items/next
POST /v1/quiz-sessions
POST /v1/attempts
GET /v1/consumers/{id}/rules
GET /v1/analytics/summary
```

Admin API SHOULD include:

```text
POST /v1/admin/imports
GET /v1/admin/imports/{id}
GET /v1/admin/quiz-items
PATCH /v1/admin/quiz-items/{id}
POST /v1/admin/quiz-items/{id}/approve
POST /v1/admin/quiz-items/{id}/publish
POST /v1/admin/quiz-items/{id}/retire
POST /v1/admin/quiz-items/{id}/block
```

Billing/entitlement API SHOULD include:

```text
GET /v1/me/entitlements
POST /v1/billing/checkout
POST /v1/billing/webhooks/{provider}
GET /v1/usage
```

### 16.4. API responses

API responses MUST NOT expose internal-only fields such as raw source paths, internal review notes, hidden quality flags or unauthorized analytics unless explicitly allowed by role/entitlement.

### 16.5. Error format

Errors SHOULD follow Problem Details style:

```json
{
  "type": "https://api.quizbank.example/problems/quota-exceeded",
  "title": "Quota exceeded",
  "status": 429,
  "detail": "This consumer has reached today's quiz delivery limit.",
  "instance": "/v1/quiz-items/next"
}
```

### 16.6. Auth

API access MUST authenticate consumers. API keys MUST be stored hashed. User tokens MUST be scoped. Admin endpoints MUST require admin role and audit logging.

### 16.7. Authorization

Every endpoint accessing item, consumer, delivery, report, organization, payment or user data MUST enforce object-level authorization.

### 16.8. Rate limits

Public and paid API usage MUST have rate limits, quotas and abuse controls.

### 16.9. OpenAPI contract

The OpenAPI contract MUST be stored in the repository and updated with API changes. Contract tests SHOULD verify implementation consistency.

---

## 17. Telegram constitution

### 17.1. Telegram as consumer

Telegram channels and bots are consumers of QuizBank Core. They MUST NOT own independent quiz selection logic.

### 17.2. Telegram worker

Telegram worker MUST:

```text
read channel/consumer rules
request item from selection engine
respect item status
respect Telegram format constraints
send quiz/poll through Telegram integration
record delivery
handle errors
avoid duplicates
report failures
```

### 17.3. Telegram channel configuration

Each Telegram channel SHOULD have:

```text
consumer_id
telegram_chat_id
channel_name
allowed_levels
allowed_themes
schedule
daily_limit
posting_window
repeat_policy
subscription/entitlement status
language/explanation mode
active/inactive status
```

### 17.4. Telegram quiz compatibility

Before sending to Telegram, item MUST be checked for:

- supported stem length;
- supported option count;
- valid correct option reference;
- explanation length/format when used;
- channel entitlement;
- delivery schedule;
- no blocked/retired status;
- no repeat conflict.

### 17.5. Delivery log

Every Telegram delivery MUST be logged with Telegram message/poll metadata when available.

### 17.6. Bot behavior

Telegram bot SHOULD support:

```text
/start
choose level
choose topic
get quiz
submit/record answer when available
show explanation
show progress
manage subscription or plan
report item
```

### 17.7. Failure handling

If Telegram delivery fails, worker MUST record failure and SHOULD retry according to controlled retry policy. It MUST NOT silently drop delivery.

---

## 18. Web, admin and external products

### 18.1. Public website

Public website SHOULD focus on:

- product explanation;
- demo quizzes;
- pricing;
- teacher/school onboarding;
- API documentation;
- account and billing entry;
- contact/support;
- Stanford/demo narrative.

Public website MUST NOT become the hidden source of truth for content.

### 18.2. Admin web

Admin web is critical infrastructure. It SHOULD support:

```text
source inventory
import batch reports
item list/filter/search
status workflow
metadata editing
approve/publish/block/retire
duplicate view
coverage reports
consumer rules
Telegram channel management
entitlement overrides
reports and quality flags
analytics dashboard
audit log
```

### 18.3. Teacher/school dashboard

Teacher/school dashboard SHOULD support:

```text
groups/classes
assigned levels/topics
quiz sessions
student progress
topic performance
exportable reports
quota/plan status
```

### 18.4. External API clients

External clients MUST receive only fields allowed by their entitlement and API scope. They MUST NOT receive admin notes, hidden quality details, private user data or raw source internals.

---

## 19. Billing and entitlements

### 19.1. Billing separation

Payment processing MUST be separated from access control. A payment provider may confirm payment, but QuizBank entitlements decide what the consumer can access.

### 19.2. Entitlement model

Entitlements SHOULD define:

```text
consumer_id or user_id or organization_id
feature
allowed_levels
allowed_themes
api_quota
telegram_channel_limit
daily_quiz_limit
monthly_quiz_limit
valid_from
valid_until
source: payment/manual/grant/promo/school_contract
status
```

### 19.3. Plans

Plans MAY include:

```text
Free
Student
Teacher
Channel
School
API Pro
Enterprise/Partner
```

### 19.4. Quota enforcement

Selection engine and API MUST enforce quotas before delivering paid or limited resources.

### 19.5. Manual override

Manual admin entitlements are allowed but MUST be logged with reason, operator and expiration.

### 19.6. Provider neutrality

The internal model SHOULD be payment-provider-neutral:

```text
provider
external_customer_id
external_subscription_id
external_invoice_id
status
entitlement_effect
```

### 19.7. Billing failures

Billing failure MUST NOT corrupt delivery history or content state. It only changes entitlement state.

---

## 20. Security, privacy and access control

### 20.1. Least privilege

Every user, admin, service and API client MUST have the minimum permissions necessary.

### 20.2. Role model

Recommended roles:

```text
owner
admin
content_manager
reviewer
developer
support
teacher
student
api_client
telegram_channel_owner
billing_admin
read_only_auditor
```

### 20.3. Object-level authorization

Every request for consumer, organization, user, delivery, attempt, billing, entitlement or report data MUST verify ownership/scope.

### 20.4. Sensitive fields

Sensitive data includes:

```text
API keys
hashed tokens
billing identifiers
user emails
school data
student progress
private reports
admin notes
source paths when private
internal quality flags
```

Sensitive data MUST NOT be exposed without authorization.

### 20.5. API keys

API keys MUST be generated securely, shown once, stored hashed and revocable.

### 20.6. Secrets

Secrets MUST NOT be committed to repository. Runtime secrets must be stored in approved secret management or environment configuration.

### 20.7. Audit log

Security-relevant and admin actions MUST be logged.

### 20.8. Backups and recovery

Production database MUST have backup and recovery plan before public paid launch.

### 20.9. Data deletion and retention

User and organization data SHOULD have retention/deletion policies consistent with applicable legal requirements and product needs.

### 20.10. Abuse prevention

The platform SHOULD include rate limits, anomaly detection, blocked consumers, abuse reports and emergency disable switches.

---

## 21. Repository and engineering governance

### 21.1. Repository structure

Recommended monorepo:

```text
quizbank-deutsch/
  README.md
  CONSTITUTION.md
  LICENSE
  SECURITY.md
  CONTRIBUTING.md
  CODEOWNERS
  CHANGELOG.md
  docs/
  data/
    raw/
    manifests/
    taxonomy/
    schemas/
    normalized/
  tools/
  services/
    api/
    admin-web/
    telegram-worker/
    scheduler/
    billing-worker/
  libs/
    quiz-selector/
    content-validator/
    importers/
    taxonomy-classifier/
  database/
    migrations/
    seeds/
    indexes.sql
  infra/
  tests/
```

### 21.2. Protected main branch

The `main` branch SHOULD be protected. Production-relevant changes SHOULD require passing checks and review.

### 21.3. CODEOWNERS

Critical areas SHOULD have code owners:

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
```

### 21.4. Changelog

Production-relevant changes MUST be recorded in CHANGELOG or release notes.

### 21.5. Required checks

Before merge to production branch, checks SHOULD include:

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

### 21.6. No silent breaking changes

Breaking changes to schema, API, database or status rules MUST have migration plan and documentation update.

### 21.7. Generated files

Generated files must be clearly marked. Manual editing of generated reports is prohibited.

---

## 22. Documentation constitution

### 22.1. Required documentation set

The project SHOULD maintain:

```text
docs/00_vision.md
docs/01_product_charter.md
docs/02_requirements_srs.md
docs/03_use_cases.md
docs/04_domain_model.md
docs/05_architecture.md
docs/06_data_standard.md
docs/07_api_standard.md
docs/08_security_threat_model.md
docs/09_quality_assurance.md
docs/10_operations.md
docs/11_billing_model.md
docs/12_analytics_model.md
docs/13_stanford_presentation_outline.md
```

### 22.2. SRS requirement IDs

Software requirements SHOULD have stable IDs:

```text
R-DATA-001
R-IMPORT-001
R-TAX-001
R-API-001
R-TG-001
R-BILL-001
R-SEC-001
R-OPS-001
R-ANALYTICS-001
NFR-PERF-001
NFR-SEC-001
```

### 22.3. Use cases

Use cases SHOULD include actors, preconditions, main flow, alternate flows, failure modes, postconditions and linked requirements.

Minimum use cases:

```text
UC-001 Admin imports source files
UC-002 System normalizes quiz items
UC-003 Admin approves item
UC-004 API consumer requests next quiz
UC-005 Telegram channel receives scheduled quiz
UC-006 User attempts quiz
UC-007 Teacher assigns topic pack
UC-008 Paid consumer exceeds quota
UC-009 User reports wrong answer
UC-010 Admin blocks item
UC-011 Billing webhook updates entitlements
UC-012 Analytics dashboard reports coverage and performance
```

### 22.4. Traceability matrix

The project SHOULD maintain traceability:

```text
Requirement → Use Case → Component → Test → Release
```

### 22.5. Documentation update rule

If code changes behavior, documentation must change. If documentation promises behavior, implementation must follow or issue must be tracked.

---

## 23. Operations constitution

### 23.1. Environments

The platform SHOULD have:

```text
local
dev
staging
production
```

### 23.2. Staging before production

No new import pipeline, schema change, selection rule, Telegram worker or billing workflow should go directly to production without staging validation.

### 23.3. Monitoring

Production SHOULD monitor:

```text
API uptime
API latency
error rates
selection failures
delivery failures
Telegram errors
quota failures
billing webhook failures
import failures
database health
background worker health
security anomalies
```

### 23.4. Logs

Logs MUST not expose secrets or sensitive user data. Logs SHOULD include correlation IDs.

### 23.5. Backups

Before paid or public scale launch, production database MUST have regular backups and restore testing.

### 23.6. Incident response

The project SHOULD have incident playbooks for:

```text
API down
Telegram delivery failure
bad item published
billing webhook failure
database issue
security incident
data import corruption
quota miscalculation
```

### 23.7. Emergency stop

The platform SHOULD support disabling:

```text
specific item
specific consumer
Telegram worker
API key
billing webhook processing
scheduled deliveries
entire publication flow
```

---

## 24. Analytics constitution

### 24.1. Analytics purpose

Analytics exists to improve product quality, coverage, learning outcomes, consumer reliability and monetization. It must not distort content governance.

### 24.2. Core metrics

The platform SHOULD track:

```text
active items by level/theme/objective/pattern
published items by level/theme/objective/pattern
delivery count
attempt count
correctness rate
response time
difficulty estimate
reports per item
blocked/retired rate
consumer activity
API usage
Telegram delivery success
quota usage
subscription/entitlement state
coverage gaps
import health
```

### 24.3. Item analytics

Each item SHOULD have analytics summary:

```text
times_delivered
times_attempted
correct_rate
median_response_time
report_count
last_delivered_at
last_reported_at
difficulty_calibrated
quality_flags
```

### 24.4. Consumer analytics

Each consumer SHOULD have:

```text
deliveries per day
attempts per day
active users when available
level/topic distribution
quota usage
repeat rate
failure rate
subscription status
```

### 24.5. Analytics privacy

Analytics must respect privacy, role limits and entitlement scope. Teachers may see their class/group data, not unrelated users.

---

## 25. Release and launch gates

### 25.1. Gate 0 — Governance foundation

Required:

```text
CONSTITUTION.md approved
README generated and current
file inventory created
import manifest created
taxonomy files created
canonical schema created
initial docs created
```

### 25.2. Gate 1 — Data foundation

Required:

```text
all active source files have source_id
all active source files have checksum
parser mapping exists for active source formats
canonical JSONL sample generated
schema validation passes for pilot subset
status lifecycle implemented
```

### 25.3. Gate 2 — Database foundation

Required:

```text
PostgreSQL schema or equivalent DB model
migrations
source_files table
quiz_items table
quiz_options table
statuses
taxonomy seed
delivery log table
audit log table
```

### 25.4. Gate 3 — API MVP

Required:

```text
OpenAPI contract
GET /health
GET /topics
GET /levels
GET /quiz-items/next
POST /attempts
auth mechanism
Problem Details-style errors
basic tests
```

### 25.5. Gate 4 — Selection MVP

Required:

```text
status-aware selection
level/theme filter
anti-repeat per consumer
quota check
delivery reservation/logging
fallback errors
```

### 25.6. Gate 5 — Telegram MVP

Required:

```text
one configured test channel
schedule rule
selection engine integration
Telegram send quiz/poll integration
delivery log
failure log
no-repeat policy
```

### 25.7. Gate 6 — Admin MVP

Required:

```text
item list/filter
source/import visibility
status change workflow
approve/publish/block/retire actions
audit log
coverage report
```

### 25.8. Gate 7 — Billing MVP

Required:

```text
plans
entitlements
quota enforcement
manual grant
billing provider webhook or simulated webhook
usage tracking
```

### 25.9. Gate 8 — Public/pilot launch

Required:

```text
security review
backup plan
monitoring
incident playbook
support/report flow
demo documentation
presentation-ready architecture narrative
```

---

## 26. Stanford-ready definition

### 26.1. Stanford-ready means engineering-ready

A project is Stanford-ready when it can be explained as a coherent engineered system with goals, constraints, requirements, data governance, architecture, demos, risks, operations and roadmap.

### 26.2. Required presentation artifacts

Before Stanford-style presentation, the project SHOULD have:

```text
1. Vision document
2. Product charter
3. Constitution
4. SRS with requirement IDs
5. Use case catalog
6. Domain model
7. Architecture diagram
8. Data standard
9. Canonical schema
10. File inventory
11. Import manifest
12. API OpenAPI contract
13. Security threat model
14. Operations plan
15. Billing/entitlement model
16. Analytics model
17. Telegram demo
18. API demo
19. Admin workflow demo
20. Roadmap and scale plan
```

### 26.3. Presentation narrative

The public narrative SHOULD be:

```text
Problem:
German-learning quiz content is fragmented, difficult to govern and difficult to distribute consistently.

Asset:
QuizBank contains a large verified German quiz corpus across CEFR levels, themes, objectives and patterns.

Solution:
A governed API-first QuizBank platform with canonical data, import pipeline, selection engine, Telegram delivery, analytics and paid access.

Differentiation:
The project is not just a quiz database. It is a governed learning-content infrastructure.

Demo:
Show import traceability, API request, selection logic, Telegram delivery, analytics and entitlement control.
```

### 26.4. Demo rules

A demo MUST NOT rely on hidden manual steps that contradict the architecture. Demo data may be a pilot subset, but it must follow the same governance rules as production.

---

## 27. Risk management

### 27.1. Core risks

The project recognizes these major risks:

```text
RISK-001: raw file chaos
RISK-002: unclear source of truth
RISK-003: direct Telegram/website access to CSV
RISK-004: missing metadata
RISK-005: duplicate/repeated delivery
RISK-006: weak API authorization
RISK-007: payment not mapped to entitlements
RISK-008: no delivery logs
RISK-009: no analytics feedback
RISK-010: overbuilding website before data core
RISK-011: no backup/recovery
RISK-012: undocumented changes
RISK-013: presentation shows content but not system
```

### 27.2. Risk treatment

Each risk SHOULD have:

```text
risk_id
severity
probability
owner
mitigation
detection signal
status
review date
```

### 27.3. Anti-chaos principle

Any proposed shortcut that increases source-of-truth ambiguity must be rejected unless owner explicitly approves a temporary exception with expiration date.

---

## 28. Governance roles

### 28.1. Owner

Owner has final authority over mission, product direction, constitution amendments, publication policy and public presentation.

### 28.2. Product maintainer

Maintains roadmap, requirements, use cases, documentation, release gates and product priorities.

### 28.3. Data steward

Owns source inventory, manifest, taxonomy, schema, import health and coverage reports.

### 28.4. Engineering maintainer

Owns API, database, services, CI/CD, tests, infrastructure and production reliability.

### 28.5. Content reviewer

Handles targeted item review, reports, status changes, metadata fixes and quality decisions.

### 28.6. Security owner

Owns threat model, authorization review, secret handling, incident response and vulnerability handling.

### 28.7. Billing owner

Owns plans, entitlements, quotas, payment provider mapping and billing incident handling.

### 28.8. Admin action rule

Any role with write permissions must be accountable through audit logs.

---

## 29. Change control

### 29.1. Change categories

Changes are categorized as:

```text
constitutional
schema
taxonomy
source/import
API
database
selection
Telegram
billing/security
operations
documentation
```

### 29.2. Pull request rule

Production-relevant changes SHOULD go through PR or equivalent approved change path.

### 29.3. Changelog rule

Changes affecting API behavior, schema, import results, publication rules, billing, permissions or production delivery MUST be documented in changelog/release notes.

### 29.4. Migration rule

Schema/database/API breaking changes MUST include migration strategy.

### 29.5. Rollback rule

Critical releases SHOULD define rollback steps.

### 29.6. Constitution amendments

Constitution amendments require:

```text
clear proposed text
reason
impact analysis
owner approval
version bump
changelog entry
```

---

## 30. Prohibited practices

The following are prohibited:

1. Public consumers reading raw CSV directly.
2. Telegram worker selecting random questions without central selection engine.
3. Publishing `draft`, `blocked` or `retired` items to public/paid users.
4. Editing generated README/inventory manually as source of truth.
5. Moving source files without inventory/manifest/checksum update.
6. Changing schema without versioning or documentation.
7. Changing API without updating OpenAPI contract.
8. Granting paid access without entitlement record.
9. Storing API keys in plain text.
10. Committing secrets to repository.
11. Silent admin changes without audit log.
12. Launching paid/public production without backups and monitoring.
13. Treating content volume alone as presentation readiness.
14. Repeating items to same consumer without repeat policy.
15. Ignoring user reports without status workflow.
16. Mixing raw source truth, generated reports and production database without clear precedence.
17. Building public website before data core, API and selection rules are stable enough for MVP.

---

## 31. Minimum viable production architecture

### 31.1. Required components

MVP production architecture SHOULD include:

```text
Content source storage
Import manifest
Importer/normalizer
Canonical schema validator
Production database
Selection engine
Versioned API
Telegram worker
Admin interface or admin scripts
Delivery log
Attempt/report capture
Entitlement/quota service
Monitoring/logging
Backup system
```

### 31.2. Architecture boundaries

```text
Raw CSV layer
  ↓ import only
Canonical data layer
  ↓ validation and migration
Production database
  ↓ service access
Selection engine
  ↓ controlled selection
API and workers
  ↓ consumers
Telegram / web / bot / app / school / API clients
```

### 31.3. Boundary rule

Each layer may read from the previous authorized layer, but consumer layers must not skip directly to raw source files.

---

## 32. Data contracts and examples

### 32.1. Canonical item example

```json
{
  "schema_version": "1.0.0",
  "public_id": "qi_000001",
  "stem_de": "Welche Antwort ist richtig?",
  "options": [
    {"id": "op_1", "text_de": "der"},
    {"id": "op_2", "text_de": "die"},
    {"id": "op_3", "text_de": "das"}
  ],
  "correct_option_ids": ["op_1"],
  "explanation_de": "Kurze Erklärung.",
  "explanation_uk": "Коротке пояснення.",
  "cefr_level": "A1",
  "theme_id": "T01",
  "objective_id": "O03",
  "pattern_id": "P01",
  "tags": ["artikel", "nominativ"],
  "status": "approved",
  "source": {
    "source_file_id": "src_0001",
    "source_locator": "row:128",
    "checksum_sha256": "..."
  },
  "content_hash": "..."
}
```

### 32.2. Consumer rule example

```json
{
  "consumer_id": "con_telegram_001",
  "type": "telegram_channel",
  "allowed_levels": ["A1", "A2"],
  "allowed_theme_ids": ["T01", "T02", "T03"],
  "daily_limit": 3,
  "repeat_policy": {
    "same_item_window_days": 120,
    "avoid_until_pool_exhausted": true
  },
  "schedule": {
    "timezone": "Europe/Kyiv",
    "times": ["09:00", "14:00", "19:00"]
  },
  "status": "active"
}
```

### 32.3. Delivery example

```json
{
  "delivery_id": "del_000001",
  "consumer_id": "con_telegram_001",
  "quiz_item_id": "qi_000001",
  "quiz_item_version": 1,
  "delivery_channel": "telegram",
  "delivered_at": "2026-04-27T09:00:00Z",
  "status": "sent",
  "external_message_id": "telegram:12345"
}
```

---

## 33. Implementation roadmap

### 33.1. Sprint 0 — Governance and launch foundation

Deliverables:

```text
CONSTITUTION.md
README.md policy confirmed
docs/00_vision.md
docs/01_product_charter.md
docs/02_requirements_srs.md
docs/03_use_cases.md
docs/04_domain_model.md
docs/06_data_standard.md
data/manifests/file_inventory.csv
data/manifests/import_manifest.yml
data/taxonomy/*.yml
data/schemas/quiz_item.schema.json
```

### 33.2. Sprint 1 — Corpus inventory and canonical schema

Deliverables:

```text
source_id for each active source
checksum for each source
parser map
canonical schema
sample normalized JSONL
validation report
```

### 33.3. Sprint 2 — Database and importer MVP

Deliverables:

```text
migrations
source_files table
quiz_items/options tables
taxonomy seed
import batch records
pilot import
```

### 33.4. Sprint 3 — API and selection MVP

Deliverables:

```text
OpenAPI contract
GET /health
GET /topics
GET /quiz-items/next
selection engine
anti-repeat
quota check
Problem Details-style errors
```

### 33.5. Sprint 4 — Telegram MVP

Deliverables:

```text
one test channel
scheduled delivery
Telegram quiz sending
delivery log
failure handling
```

### 33.6. Sprint 5 — Admin and publication workflow

Deliverables:

```text
admin item list
status workflow
approve/publish/block/retire
audit log
coverage dashboard
```

### 33.7. Sprint 6 — Billing, analytics and presentation

Deliverables:

```text
plans
entitlements
quota enforcement
analytics dashboard
Stanford presentation outline
live API demo
live Telegram demo
```

---

## 34. Acceptance criteria for the Constitution itself

This Constitution is accepted when:

```text
1. It is saved as CONSTITUTION.md in the repository.
2. It is referenced from README.md.
3. It is used to create docs/00_vision.md and docs/02_requirements_srs.md.
4. It defines source of truth, raw file policy, statuses, schema, API-first rule and launch gates.
5. It explicitly separates operational launch from unnecessary re-audit of already checked content.
6. It defines Stanford-ready criteria.
7. Future work is evaluated against it.
```

---

## 35. Executive summary for external presentation

QuizBank is a governed German-language quiz platform. It transforms a verified corpus of quiz items into a scalable data product through source traceability, canonical schemas, CEFR-aware taxonomy, import pipelines, controlled statuses, database-backed delivery, centralized selection, OpenAPI access, Telegram automation, entitlements, analytics and operations.

The project is not merely a website or a CSV archive. It is learning-content infrastructure designed for safe scaling across channels, teachers, schools, applications and external API consumers.

The constitutional thesis is simple:

```text
Content becomes a product only when it is governed, normalized, served through a contract, measured and operated.
```

---

## 36. Final constitutional rule

When in doubt, choose the path that preserves:

```text
source traceability
canonical data integrity
API-first architecture
status-controlled publication
repeat-safe delivery
entitlement-aware access
security
analytics
operational clarity
presentation readiness
```

If a shortcut breaks any of these, it is not a shortcut. It is technical debt and must be rejected or explicitly time-boxed with owner approval.
