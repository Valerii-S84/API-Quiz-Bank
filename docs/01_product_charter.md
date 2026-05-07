# API Quiz Bank — Product Charter

**Документ:** `docs/01_product_charter.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** binding product charter; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`  
**Дата:** 2026-04-27  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized product maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`  
**Наступні документи:** `02_requirements_srs.md`, `03_use_cases.md`, `04_domain_model.md`, `05_architecture.md`, `06_data_standard.md`, `07_api_standard.md`, `08_security_threat_model.md`, `09_quality_assurance.md`, `10_operations.md`, `11_billing_model.md`, `12_analytics_model.md`, `13_stanford_presentation_outline.md`

---

## 0. Executive Summary

**API Quiz Bank** — це керована API-first платформа для німецьких вікторин, яка перетворює перевірений corpus на масштабований освітньо-технологічний продукт.

Цей Product Charter визначає продуктову рамку: що саме ми будуємо, для кого, у якій послідовності, з якими межами, хто ухвалює рішення, як додаються нові файли, які launch gates обовʼязкові, які метрики означають успіх, які ризики контролюються і що потрібно для Stanford-style презентації.

Проєкт має стартовий operational baseline:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Цей baseline є **стартовим активом**, а не верхньою межею системи. Product Charter закріплює правило:

```text
New quiz files are onboarded, not dropped.
```

Тобто майбутні файли з вікторинами мають проходити source intake, stable `source_id`, checksum, inventory, import manifest, parser assignment, dry-run import, canonical validation, duplicate/conflict detection, import batch, status workflow, approval/publication і оновлення generated reports. Жоден новий файл не повинен напряму ставати production-контентом.

Головна продуктова формула:

```text
Verified German quiz content
  → source governance
  → canonical data
  → production database
  → selection engine
  → versioned API
  → Telegram / web / bots / schools / apps / external clients
  → analytics / billing / feedback / operations / scale
```

Product Charter не замінює SRS. Він задає product policy, product scope, MVP boundaries, roles, decision rights, launch gates and success criteria. SRS потім перетворить цю рамку в детальні functional/non-functional requirements.

---

## 1. Роль документа

### 1.1. Призначення

`01_product_charter.md` є другим стратегічним документом після `00_vision.md` і першим документом, який переводить бачення в продуктову операційну рамку.

Він відповідає на питання:

```text
Що є продуктом?
Що не є продуктом?
Хто користувачі та покупці?
Яку проблему ми вирішуємо?
Який MVP справді потрібен?
Які модулі входять у перший запуск?
Які модулі відкладаються?
Як додаються нові quiz-файли?
Як контент переходить від raw source до production delivery?
Хто ухвалює рішення?
Які gates не можна обійти?
Які метрики показують, що продукт працює?
Що потрібно, щоб проєкт можна було професійно презентувати?
```

### 1.2. Місце серед документів

Документаційна ієрархія:

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
implementation, tests, launch, operations
```

Якщо цей документ суперечить Конституції, пріоритет має `CONSTITUTION.md`. Якщо SRS або implementation суперечить цьому Product Charter, вони мають бути виправлені або Product Charter має бути офіційно оновлений через change control.

### 1.3. Чим цей документ не є

Цей документ не є:

- повним SRS;
- database schema;
- OpenAPI contract;
- UI specification;
- повним бізнес-планом;
- security threat model;
- повторним аудитом перевірених quiz items;
- implementation backlog у деталях задач;
- презентацією для зовнішньої аудиторії.

Він визначає рамку, у межах якої ці документи будуть створені.

### 1.4. Stanford-style interpretation

У межах цього проєкту **Stanford-style** означає не бренд і не формальне схвалення Stanford. Це означає інженерну зрілість:

```text
clear mission
explicit scope
traceable requirements
use-case driven design
testable acceptance criteria
change control
source traceability
security by design
operational readiness
reproducible demos
measurable success
```

Product Charter має зробити проєкт пояснюваним для технічної, освітньої, бізнесової та інвесторської аудиторії.

---

## 2. Product Identity

### 2.1. Назва

Публічна назва:

```text
API Quiz Bank
```

Цю назву треба використовувати в:

- product documents;
- architecture diagrams;
- API docs;
- demo scripts;
- pitch materials;
- Stanford-style presentation;
- external partner conversations.

Історичні назви `QuizBank` і `German QuizBank Platform` можуть залишатися у внутрішніх технічних шляхах, поки перейменування не буде безпечним.

### 2.2. Product category

API Quiz Bank належить до категорії:

```text
Educational Content Infrastructure / API-first Quiz Delivery Platform
```

Це не просто:

- question bank;
- static website;
- Telegram bot;
- CSV catalog;
- trivia API;
- LMS plugin;
- manual spreadsheet.

### 2.3. Product statement

```text
API Quiz Bank is a governed platform that transforms verified German quiz content
into reliable, traceable, level-aware, API-delivered educational experiences for
learners, teachers, Telegram channels, schools, applications and external API clients.
```

Українською:

```text
API Quiz Bank — це керована платформа, яка перетворює перевірений контент
німецьких вікторин на надійну, відстежувану, CEFR-aware, API-доставлену
освітню систему для учнів, викладачів, Telegram-каналів, шкіл, додатків
і зовнішніх API-клієнтів.
```

### 2.4. Product promise

API Quiz Bank має гарантувати:

```text
правильний контент
у правильному форматі
для правильного consumer
через контрольований API
з повною source traceability
і без хаотичного повторення
```

### 2.5. Strategic product sentence

```text
The corpus is the asset; the API is the product surface; governance is the trust layer.
```

---

## 3. Problem Statement

### 3.1. Основна проблема

Навчальні вікторини часто існують як розрізнені файли, таблиці, канали або боти. У такій формі вони не масштабуються професійно, тому що:

- важко знати, скільки якісного контенту реально є;
- важко гарантувати, що питання має правильний рівень, тему, source і статус;
- немає єдиного API-контракту для delivery;
- Telegram, сайт і зовнішні клієнти можуть почати працювати за різними правилами;
- повтори не контролюються централізовано;
- оплата й доступ часто привʼязуються до каналу, а не до entitlements;
- нові файли можуть ламати порядок;
- немає доказової операційної моделі для серйозної презентації.

### 3.2. Product problem

Проблема API Quiz Bank не в тому, що бракує quiz content. Проблема в тому, що перевірений content має бути перетворений у production-ready platform.

```text
Content exists.
Product system does not yet fully exist.
```

Product Charter вирішує саме цю проблему.

### 3.3. User problem

Користувачі й партнери потребують не просто “питання”, а:

```text
рівень → тема → якісне питання → зрозуміла відповідь → контроль повторів → статистика → доступ за правилами
```

### 3.4. Business problem

Без product governance неможливо надійно монетизувати банк, тому що:

- неясно, які пакети продаються;
- неясно, які levels/topics доступні за планом;
- неясно, скільки питань можна видавати;
- складно рахувати usage;
- немає стабільної API value proposition;
- немає proof of reliability для B2B/шкіл/API-клієнтів.

### 3.5. Engineering problem

Без product charter engineering може піти неправильним шляхом:

- зробити Telegram bot до data model;
- зробити сайт, який читає CSV напряму;
- зробити API без selection engine;
- зробити billing без entitlements;
- зробити import без source traceability;
- додавати нові файли без manifest;
- запускати production без launch gates.

Product Charter забороняє ці хибні маршрути.

---

## 4. Product Thesis

### 4.1. Основна теза

```text
Verified quiz content becomes a scalable product only when it is governed,
normalized, served through a versioned API, measured, monetized and operated.
```

### 4.2. Product value chain

```text
Raw files
  → source registry
  → import manifest
  → parser profile
  → canonical quiz item
  → validation
  → database
  → status lifecycle
  → selection engine
  → API
  → delivery channel
  → analytics
  → entitlement enforcement
  → quality feedback
```

### 4.3. Product differentiation

API Quiz Bank має відрізнятися від звичайного quiz API тим, що він має:

- CEFR-aware content model;
- source traceability;
- controlled import pipeline;
- future source onboarding;
- status lifecycle;
- coverage matrix;
- centralized selection engine;
- anti-repeat policy;
- Telegram-ready validation;
- API-first delivery;
- entitlements and quotas;
- analytics loop;
- Stanford-style traceability.

### 4.4. Product truth

```text
CSV files are the source asset.
Canonical data is the structure.
Database is the operational source of truth.
API is the delivery surface.
Selection engine is the intelligence.
Entitlements are the business control.
Analytics is the feedback loop.
Operations are the trust guarantee.
```

---

## 5. Product Goals

### 5.1. Primary goal

Створити production-ready API-first платформу, яка може безпечно видавати перевірені німецькі quiz items через API та підключені delivery channels.

### 5.2. Strategic goals

| ID | Goal | Meaning |
|---|---|---|
| PG-001 | Govern the corpus | Усі поточні й майбутні файли мають бути inventory-managed, traceable and importable. |
| PG-002 | Normalize content | Усі questions мають переходити у canonical quiz item model. |
| PG-003 | Serve through API | Усі consumers отримують content через versioned API, не напряму з files/database. |
| PG-004 | Control delivery | Selection engine визначає, що кому видавати, з anti-repeat and quota policy. |
| PG-005 | Enable channels | Telegram, web, bots, apps and schools підключаються як consumers. |
| PG-006 | Monetize responsibly | Access керується plans, quotas and entitlements. |
| PG-007 | Measure outcomes | Система збирає usage, delivery, correctness, difficulty and quality signals. |
| PG-008 | Scale content | Нові quiz files можна додавати без хаосу через source onboarding. |
| PG-009 | Prove readiness | Проєкт має бути демонстрований через working API, governed corpus, architecture and launch gates. |

### 5.3. North Star Metric

Основна North Star Metric для першого production етапу:

```text
Number of successfully delivered approved quiz items through the API without policy violations.
```

Розширене формулювання:

```text
API-delivered approved quiz items with valid source traceability,
no repeat-policy violation, valid entitlement check, and delivery/attempt logging.
```

### 5.4. Supporting metrics

| Area | Metric | Why it matters |
|---|---|---|
| Corpus | active source files registered | Показує, що файли керовані. |
| Corpus | items imported into canonical format | Показує реальний перехід від CSV до product data. |
| Quality | approved item ratio | Показує readiness до delivery. |
| Coverage | level × theme coverage | Показує освітню повноту. |
| API | successful `/v1/quiz-items/next` responses | Показує product usability. |
| Delivery | duplicate/repeat violation rate | Показує якість selection engine. |
| Usage | attempts recorded | Показує learning feedback loop. |
| Business | active consumers with entitlements | Показує монетизаційну готовність. |
| Ops | failed scheduled deliveries | Показує operational reliability. |
| Security | unauthorized access attempts blocked | Показує access control maturity. |

---

## 6. Target Users and Stakeholders

### 6.1. Primary users

| User | Description | Core need |
|---|---|---|
| Learner | Людина, яка вивчає німецьку | Отримувати питання за рівнем і темою, бачити правильну відповідь і прогрес. |
| Teacher | Викладач німецької | Підбирати quiz packs для студентів, груп, тем і рівнів. |
| Telegram Channel Owner | Власник освітнього каналу | Автоматично публікувати якісні quiz polls за розкладом. |
| School / Course Provider | Освітня організація | Підключити structured German quiz content до своїх груп або LMS. |
| API Client Developer | Розробник додатку | Отримувати quiz items через стабільний API-контракт. |
| Admin / Content Operator | Оператор системи | Імпортувати, класифікувати, ревʼювати, approve/publish контент. |

### 6.2. Secondary stakeholders

| Stakeholder | Interest |
|---|---|
| Project owner | Strategy, monetization, quality, launch. |
| Engineering lead | Architecture, API, database, reliability. |
| Data/content lead | Import, canonical schema, source traceability, taxonomy. |
| Security owner | API keys, auth, authorization, admin protection, privacy. |
| Business partner | Pricing, packages, B2B access, school/API deals. |
| Demo audience | Needs clear proof that the system is serious, scalable and governed. |

### 6.3. Buyer vs user distinction

У продукті треба розрізняти:

```text
User — той, хто відповідає на вікторини.
Buyer — той, хто платить за доступ.
Consumer — технічний або організаційний канал, який отримує content.
Admin — той, хто керує системою.
```

Приклади:

- Учень може бути user and buyer.
- Викладач може бути buyer for group users.
- Telegram channel може бути consumer, а його власник — buyer.
- School може бути buyer, а студенти — users.
- External app може бути API consumer, а кінцеві learners — downstream users.

Ця відмінність критична для billing, entitlements, analytics and privacy.

---

## 7. Jobs To Be Done

### 7.1. Learner jobs

```text
Коли я вивчаю німецьку, я хочу отримувати питання за моїм рівнем і темою,
щоб практикувати мову без хаотичного контенту.
```

```text
Коли я помиляюся, я хочу бачити правильну відповідь і пояснення,
щоб зрозуміти правило або вживання.
```

```text
Коли я повертаюся до практики, я не хочу постійно бачити ті самі питання,
щоб прогрес був реальним.
```

### 7.2. Teacher jobs

```text
Коли я готую урок, я хочу вибрати рівень, тему й тип завдання,
щоб швидко отримати релевантні quiz items для студентів.
```

```text
Коли я працюю з групою, я хочу бачити статистику правильності,
щоб зрозуміти, які теми треба повторити.
```

### 7.3. Telegram channel jobs

```text
Коли я веду освітній канал, я хочу автоматичну публікацію quiz polls,
щоб канал регулярно отримував якісний контент без ручного постингу.
```

```text
Коли канал уже отримав питання, я хочу уникати повторів,
щоб аудиторія не втрачала довіру.
```

### 7.4. API client jobs

```text
Коли я будую додаток, я хочу стабільний API,
щоб інтегрувати German quiz content без доступу до internal files or database.
```

```text
Коли API повертає помилку, я хочу machine-readable error format,
щоб мій клієнт міг правильно обробити quota, auth, not found або validation errors.
```

### 7.5. Admin jobs

```text
Коли зʼявляється новий quiz file, я хочу зареєструвати його, отримати checksum,
призначити parser і зробити dry-run import, щоб безпечно додати контент.
```

```text
Коли item має невизначені metadata або conflict, я хочу бачити review queue,
щоб привести його до production-ready status.
```

---

## 8. Product Scope

### 8.1. In scope for the platform

API Quiz Bank включає:

```text
source inventory
import manifest
parser profiles
canonical quiz item schema
production database
taxonomy and coverage model
status lifecycle
selection engine
versioned API
consumer management
Telegram delivery worker
admin workflow
billing and entitlements model
analytics and reporting
security and access control
operations and monitoring
future source onboarding
```

### 8.2. In scope for MVP

MVP має включати достатньо, щоб довести core thesis:

```text
governed corpus
canonical import path
database-backed quiz items
basic selection engine
/v1 API endpoint for next quiz
consumer rules
delivery logging
admin review/approval workflow or minimal admin operations
Telegram pilot delivery or API demo consumer
basic entitlements/quota enforcement
generated reports
Stanford-style demo narrative
```

### 8.3. Out of scope for MVP

Не входить у перший MVP:

- повноцінний adaptive learning engine;
- Item Response Theory / Computerized Adaptive Testing;
- AI-generated quiz content as production source;
- public marketplace;
- full LMS replacement;
- multi-language product beyond German;
- complex gamification;
- mobile native apps;
- full school CRM;
- advanced teacher dashboard;
- public community contribution without moderation;
- direct CSV access by consumers;
- production use of unapproved items;
- uncontrolled file drops.

### 8.4. Explicit non-goals

API Quiz Bank НЕ має на першому етапі:

```text
перевіряти заново кожну вже перевірену вікторину як content audit;
будувати бот раніше, ніж data/API foundation;
робити сайт головним джерелом логіки;
продавати доступ без entitlement enforcement;
видавати draft items у public delivery;
дозволяти Telegram worker читати raw CSV напряму;
```

### 8.5. Product boundary

Product boundary:

```text
Входить: весь шлях від source file governance до API/Telegram delivery and analytics.
Не входить: зовнішні освітні курси, ручна методика викладача, несанкціоновані downstream integrations.
```

---

## 9. Product Modules

### 9.1. Module map

| Module | Purpose | MVP role |
|---|---|---|
| Source Registry | Облік raw files and future files | Required |
| Import Manifest | Опис джерел, parsers, defaults, states | Required |
| Import Pipeline | Parse, normalize, validate, detect conflicts | Required |
| Canonical Data Core | Єдина структура quiz item | Required |
| Taxonomy Core | Themes, CEFR, objectives, patterns, tags | Required |
| Production Database | Operational source of truth | Required |
| Status Workflow | draft/imported/approved/published/retired/etc. | Required |
| Selection Engine | Вибір next quiz with constraints | Required |
| API Service | Versioned delivery surface | Required |
| Consumer Management | Telegram/web/API/school consumers | Required |
| Delivery Logging | Що кому видано і коли | Required |
| Attempt Logging | User answers and correctness | MVP-light |
| Admin Workflow | Review, approve, manage sources | MVP-light / Required for scale |
| Telegram Worker | Scheduled channel delivery | Pilot |
| Billing/Entitlements | Plans, quotas, feature access | MVP-light |
| Analytics | Usage, quality, coverage, performance | MVP-light |
| Operations | Monitoring, backup, incident control | Required before production |

### 9.2. Module dependency rule

Modules must not be built in an order that violates product dependency:

```text
source governance before import
import before database production use
database before API production use
API before external consumers
selection engine before Telegram scaling
entitlements before paid access
analytics before scale claims
operations before public launch
```

### 9.3. Forbidden coupling

Заборонено:

- Telegram worker directly reading raw CSV;
- public site selecting quiz items independently from selection engine;
- billing logic inside Telegram bot only;
- admin edits without audit log;
- source files modified without inventory/manifest updates;
- API returning items without status and entitlement checks.

---

## 10. Content Product Policy

### 10.1. Content status principle

Увесь поточний corpus може бути перевірений за змістом, але operationally він не стає production-ready автоматично.

```text
draft ≠ wrong
draft = not yet released through production workflow
```

### 10.2. Publication rule

Production consumers may receive only items in allowed delivery statuses:

```text
approved
published
```

Draft/imported/normalized/needs_review items не видаються через public API, Telegram, paid products or school integrations.

### 10.3. No re-audit principle

Перший етап API Quiz Bank не є повторним content audit. Його мета:

```text
упорядкувати файли
створити source governance
нормалізувати дані
побудувати import workflow
створити API/data contracts
налаштувати status and delivery controls
запустити platform workflow
```

Технічна validation не дорівнює педагогічному re-audit. Вона перевіряє structure, metadata, traceability, compatibility and launch safety.

### 10.4. Content dimensions

Кожен production item має бути керований щонайменше за такими dimensions:

```text
source_id
source_file
source_row_or_block
content_hash
status
CEFR level
theme_id
objective_id
pattern_id
item_type
options
correct answer reference
Telegram compatibility
delivery eligibility
version/revision
```

### 10.5. Educational alignment

CEFR levels `A1–C2` є основою learning level model. Internal difficulty може бути додатковим параметром, але не може замінити CEFR.

### 10.6. Multi-topic policy

Питання може мати:

```text
one primary_theme_id
zero or more secondary_theme_ids
zero or more tags
one or more objectives if supported by schema
one primary pattern_id
```

Primary theme потрібна для selection and reporting. Secondary tags потрібні для гнучкого пошуку, teacher packs and analytics.

---

## 11. Future Source Onboarding Policy

### 11.1. Core rule

```text
New files are onboarded, not dropped.
```

Жоден новий файл не може бути доданий як production source без source onboarding workflow.

### 11.2. Why this matters

Без цього правила масштабування зламає платформу:

- зʼявляться duplicate/conflicting items;
- parser assumptions стануть неконтрольованими;
- coverage reports втратять точність;
- source traceability стане неповною;
- API може видавати непідготовлені items;
- billing packages можуть включати неперевірений content;
- Stanford-style credibility буде втрачена.

### 11.3. Source lifecycle states

Кожен source file має один із станів:

| State | Meaning | Delivery allowed? |
|---|---|---|
| `candidate` | Файл запропоновано до додавання | No |
| `registered` | Є source_id, checksum, inventory record | No |
| `parser_pending` | Потрібен parser або parser profile | No |
| `parser_assigned` | Parser визначено | No |
| `dry_run_passed` | Dry-run import пройшов structural checks | No |
| `imported` | Items імпортовано в staging/canonical layer | No by default |
| `active` | Source дозволений для production workflow | Only approved/published items |
| `archived` | Source історично збережений, не активний | No new delivery |
| `rejected` | Source не прийнятий | No |
| `blocked` | Source заблокований через issue | No |

### 11.4. Source onboarding workflow

```text
1. Submit source file.
2. Assign stable source_id.
3. Record original filename, owner, date, purpose and expected content type.
4. Compute checksum.
5. Add to file_inventory.csv.
6. Add to import_manifest.yml as candidate/registered.
7. Identify format, encoding, delimiter, columns and parser needs.
8. Assign existing parser or create parser profile.
9. Run dry-run import.
10. Generate import report.
11. Validate canonical schema.
12. Detect duplicates and conflicts.
13. Assign default taxonomy or route to review.
14. Import into staging/canonical storage.
15. Move items through status workflow.
16. Approve/publish eligible items.
17. Update generated reports and coverage matrix.
18. Record release note if production corpus changes.
```

### 11.5. Source intake form

Кожен новий source submission має мати:

```text
proposed_source_name
submitted_by
submission_date
content_owner
intended_level_range
intended_theme_range
expected_item_count
file_format
language_scope
known_parser_if_any
known_quality_status
rights_to_use
notes
```

### 11.6. Required source metadata

```text
source_id
source_slug
original_filename
original_path
registered_at
registered_by
checksum_sha256
format
encoding
parser_profile
default_cefr_if_known
default_theme_if_known
source_status
expected_items
actual_imported_items
import_batch_id
latest_import_report
rights_status
```

### 11.7. Parser policy

A parser must define:

```text
accepted file extensions
required columns
optional columns
column mappings
encoding assumptions
delimiter assumptions
normalization steps
error categories
output canonical fields
test fixtures
```

Parser зміни є production-relevant і мають проходити change control.

### 11.8. Dry-run import policy

Dry-run import має генерувати report:

```text
total rows detected
rows parsed
rows skipped
schema errors
taxonomy missing
duplicate candidates
conflict candidates
Telegram compatibility issues
source metadata issues
recommendation: proceed / fix / reject
```

### 11.9. Duplicate/conflict handling

Новий source не повинен silently override existing content.

Possible outcomes:

```text
new_unique_item
exact_duplicate_existing
near_duplicate_review_required
conflicting_correct_answer
conflicting_metadata
source_version_update
blocked_until_resolved
```

### 11.10. Source release gate

Новий source can affect production only when:

```text
source_id exists
checksum recorded
manifest entry exists
parser assigned
dry-run report exists
schema validation passed for importable rows
conflicts classified
items have statuses
approved items have required metadata
coverage report updated
release note created if publication changes corpus
```

---

## 12. MVP Definition

### 12.1. MVP thesis

MVP має довести, що API Quiz Bank може:

```text
1. керувати corpus;
2. імпортувати/нормалізувати content;
3. зберігати production-ready quiz items;
4. видавати next quiz через API за правилами;
5. логувати delivery;
6. не повторювати хаотично;
7. поважати status and entitlement rules;
8. показати demo через API and/or Telegram;
9. приймати майбутні files через onboarding model.
```

### 12.2. MVP components

| Component | MVP requirement |
|---|---|
| Documentation | Constitution, Vision, Product Charter, SRS draft, Use Cases draft, Data Standard draft, API Standard draft |
| Source governance | inventory + manifest for current corpus; onboarding policy for future sources |
| Canonical schema | quiz item schema with required production fields |
| Import pipeline | at least one controlled import path and import reports |
| Database | normalized storage for quiz items, options, sources, consumers, deliveries |
| Selection engine | next quiz selection with status, level, theme, repeat and quota checks |
| API | versioned endpoint(s), OpenAPI draft, Problem Details errors |
| Admin workflow | minimal review/approval/source operations, even if command-line first |
| Telegram pilot | one controlled consumer or simulated Telegram delivery |
| Billing model | entitlement schema and quota checks; payment integration may be simulated/manual in MVP |
| Analytics | basic corpus, delivery and usage dashboards/reports |
| Operations | backup, logs, launch gates and rollback notes |

### 12.3. MVP acceptance summary

MVP is acceptable when:

```text
- no consumer reads raw CSV directly;
- at least one source/import path is reproducible;
- items have source traceability;
- API returns only approved/published eligible items;
- delivery is logged;
- repeat policy can be demonstrated;
- entitlement/quota denial can be demonstrated;
- future file onboarding can be demonstrated on a sample source;
- generated reports reflect corpus state;
- demo narrative can be executed without manual data tricks.
```

### 12.4. MVP anti-patterns

The MVP fails if it is only:

- a static website;
- a bot reading a CSV;
- a manually curated list of questions;
- a demo with hardcoded items;
- an API without source traceability;
- a database without import manifest;
- a paid channel without entitlements;
- a presentation without working system proof.

---

## 13. Product Phases

### 13.1. Phase 0 — Governance Foundation

Goal:

```text
Створити правила, документи, repository structure and product discipline.
```

Deliverables:

```text
CONSTITUTION.md
docs/00_vision.md
docs/01_product_charter.md
docs/02_requirements_srs.md draft
docs/03_use_cases.md draft
docs/06_data_standard.md draft
docs/07_api_standard.md draft
repository structure
change control rules
source onboarding policy
```

Exit criteria:

```text
core documents exist
product scope is explicit
MVP boundaries are approved
future source onboarding is defined
launch gates are known
```

### 13.2. Phase 1 — Corpus Inventory and Source Governance

Goal:

```text
Зробити поточні й майбутні files керованими.
```

Deliverables:

```text
data/manifests/file_inventory.csv
data/manifests/import_manifest.yml
source_id convention
checksum policy
source status lifecycle
parser registry
current corpus report
future source intake template
```

Exit criteria:

```text
all current active files have inventory records
all current active files have stable source IDs or migration plan to assign them
all files have checksum or checksum generation workflow
future source onboarding can be applied to a new sample file
```

### 13.3. Phase 2 — Canonical Data and Import Pipeline

Goal:

```text
Перетворити raw files into canonical quiz items.
```

Deliverables:

```text
quiz_item.schema.json
import_file.schema.json
parser profiles
normalization rules
import reports
sample JSONL
validation command
conflict categories
```

Exit criteria:

```text
importer generates canonical items
canonical items pass schema validation
source traceability is preserved
import report lists accepted/skipped/problem rows
```

### 13.4. Phase 3 — Database and API Core

Goal:

```text
Створити operational source of truth and versioned API.
```

Deliverables:

```text
PostgreSQL schema
migrations
seed taxonomy
quiz items table
options table
source files table
consumers table
deliveries table
basic API service
OpenAPI specification
Problem Details error model
```

Exit criteria:

```text
API can return next eligible quiz item
API enforces status checks
API can deny unauthorized/quota-exceeded requests
API contract is documented
```

### 13.5. Phase 4 — Selection, Delivery and Telegram Pilot

Goal:

```text
Довести controlled delivery to real or simulated consumer.
```

Deliverables:

```text
selection engine
consumer rules
repeat policy
delivery logging
Telegram worker or simulated delivery adapter
scheduler rules
delivery report
```

Exit criteria:

```text
one consumer can receive scheduled quiz
repeat policy is demonstrable
delivery log is recorded
failure handling exists
```

### 13.6. Phase 5 — Admin, Billing and Analytics MVP

Goal:

```text
Дати операторам контроль, бізнесу monetization logic and product team insight.
```

Deliverables:

```text
admin source view
admin item review/approval workflow
plan model
entitlement model
quota model
usage tracking
analytics reports
manual billing override
```

Exit criteria:

```text
admin can approve/publish/retire items
consumer access is entitlement-based
quota enforcement is testable
usage analytics are visible
```

### 13.7. Phase 6 — Stanford-Ready Demo

Goal:

```text
Підготувати професійну демонстрацію системи як платформи, не як набору файлів.
```

Deliverables:

```text
presentation outline
architecture diagram
data flow diagram
API demo script
Telegram demo script
admin workflow demo
source onboarding demo
analytics screenshot/report
security and operations summary
roadmap and business model
```

Exit criteria:

```text
demo can be executed end-to-end
system behavior matches documentation
claims are backed by artifacts
risks and next steps are explicit
```

---

## 14. Launch Modes

### 14.1. Internal prototype

Purpose:

```text
Перевірити import/schema/API assumptions без зовнішніх користувачів.
```

Allowed:

- command-line imports;
- local database;
- sample items;
- internal API tests;
- simulated consumers.

Not allowed:

- paid users;
- public Telegram channel;
- external API clients;
- production claims.

### 14.2. Closed pilot

Purpose:

```text
Перевірити controlled delivery на обмеженій групі consumers.
```

Allowed:

- selected Telegram channel;
- selected teacher/group;
- limited API consumer;
- manual billing/entitlement override;
- monitored usage.

Required:

- approved/published items only;
- delivery logs;
- repeat policy;
- rollback plan;
- issue reporting.

### 14.3. Public beta

Purpose:

```text
Показати продукт ширшій аудиторії з обмеженими планами й контролем ризику.
```

Required:

- stable API version;
- documented pricing/usage limits;
- admin workflow;
- monitoring;
- security baseline;
- backup plan;
- support contact/process.

### 14.4. Production launch

Purpose:

```text
Запустити продукт як платну або офіційно підтримувану платформу.
```

Required:

- production data store;
- schema migrations;
- CI/CD;
- authentication/authorization;
- entitlement enforcement;
- monitoring and alerts;
- backup and restore test;
- incident playbook;
- legal/privacy review appropriate to usage;
- launch approval.

### 14.5. Stanford-style presentation mode

Purpose:

```text
Демонстрація системної зрілості, scalability and product clarity.
```

Presentation mode may use a controlled dataset, but must not misrepresent capabilities. Claims must be traceable to working artifacts.

---

## 15. Release and Launch Gates

### 15.1. Gate hierarchy

```text
Document gate
Data gate
Import gate
Schema gate
Database gate
API gate
Consumer gate
Billing/entitlement gate
Security gate
Operations gate
Demo gate
Production gate
```

### 15.2. Document gate

Before serious implementation:

```text
CONSTITUTION.md exists
00_vision.md exists
01_product_charter.md exists
SRS draft exists or is planned with IDs
Use cases draft exists or is planned
Data/API standards have owners
```

### 15.3. Data gate

Before import at scale:

```text
inventory exists
manifest exists
source_id convention exists
checksum policy exists
taxonomy exists
canonical schema exists
```

### 15.4. Import gate

Before database publication:

```text
parser profile exists
dry-run report exists
validation report exists
duplicates/conflicts are classified
source traceability is preserved
import batch is reproducible
```

### 15.5. API gate

Before external consumer access:

```text
OpenAPI spec exists
API versioning exists
auth model exists
Problem Details errors exist
status filtering works
entitlement/quota checks work
rate limits or usage controls exist
```

### 15.6. Telegram gate

Before real channel posting:

```text
Telegram adapter uses API/selection engine, not raw CSV
only approved/published items are used
poll compatibility validation exists
delivery log exists
repeat policy exists
failure handling exists
posting schedule is controlled
```

### 15.7. Billing gate

Before paid launch:

```text
plan model exists
entitlement model exists
quota model exists
usage tracking exists
payment-provider-neutral identifiers exist
manual override policy exists
refund/cancellation/support policy is drafted
```

### 15.8. Security gate

Before public launch:

```text
admin authentication exists
API keys/tokens are not stored in plaintext
object-level authorization is checked
admin actions are logged
secrets are not committed
rate limits or abuse controls exist
basic threat model exists
```

### 15.9. Operations gate

Before production claim:

```text
logs exist
monitoring exists
backup exists
restore procedure exists
incident playbook exists
rollback path exists
maintenance owner exists
```

### 15.10. Demo gate

Before Stanford-style demo:

```text
clear demo script exists
architecture diagram exists
API demo works
source onboarding demo works
Telegram/API consumer demo works
analytics snapshot exists
risks and next steps are explicit
```

---

## 16. Decision Rights and Governance

### 16.1. Governance principle

Product decisions must be explicit, documented and traceable. Silent product changes are not allowed for production-relevant behavior.

### 16.2. Core roles

| Role | Responsibility |
|---|---|
| Project Owner | Final product direction, business priorities, external positioning. |
| Product Maintainer | Maintains Product Charter, roadmap, launch gates and scope discipline. |
| Technical Lead | Architecture, API, database, reliability, engineering standards. |
| Data/Content Lead | Source governance, import manifest, taxonomy, canonical schema, content states. |
| Security Owner | Auth, authorization, secrets, abuse prevention, threat model. |
| Operations Owner | Monitoring, backups, incidents, deployment readiness. |
| Billing Owner | Plans, entitlements, quotas, payment integration. |
| Demo Owner | Stanford-style narrative, demo scripts, presentation artifacts. |

For a small team, one person may hold multiple roles, but the decision domains remain separate.

### 16.3. RACI summary

| Decision | Owner | Consulted | Must be documented? |
|---|---|---|---|
| Product scope change | Product Maintainer | Project Owner, Tech Lead | Yes |
| Constitution change | Project Owner | Product, Tech, Data | Yes |
| New source accepted | Data/Content Lead | Product Maintainer | Yes |
| Parser change | Technical Lead | Data/Content Lead | Yes |
| Canonical schema change | Technical Lead | Data/Content Lead, Product | Yes |
| API breaking change | Technical Lead | Product, API consumers | Yes |
| Launch gate pass | Product Maintainer | Tech, Ops, Security | Yes |
| Paid plan change | Billing Owner | Product Owner | Yes |
| Security exception | Security Owner | Tech, Product | Yes |
| Public demo claim | Demo Owner | Project Owner, Product, Tech | Yes |

### 16.4. Decision log

Production-relevant decisions should be logged in:

```text
docs/decision_log.md
```

Minimum entry:

```text
date
decision_id
decision title
context
options considered
decision
owner
impact
follow-up requirements
```

### 16.5. Escalation rule

If speed conflicts with governance, governance wins unless the Project Owner explicitly approves a temporary exception with expiry and rollback.

---

## 17. Change Control

### 17.1. Change categories

| Category | Examples | Control level |
|---|---|---|
| Documentation-only | wording, explanation, formatting | Low |
| Product scope | MVP change, roadmap change, consumer type | Medium/High |
| Data schema | required fields, status lifecycle, taxonomy structure | High |
| Import behavior | parser mappings, normalization, dedupe | High |
| API contract | endpoint, response schema, auth, error model | High |
| Billing | plans, quotas, entitlements | High |
| Security | auth, secrets, access, admin actions | Critical |
| Production data | item publication, source activation | High |

### 17.2. Change request template

```text
change_id:
title:
requested_by:
date:
category:
problem:
proposed_change:
affected_documents:
affected_components:
affected_data:
affected_consumers:
risk:
rollback_plan:
acceptance_criteria:
decision:
```

### 17.3. Breaking change policy

Breaking changes require:

```text
explicit versioning
migration plan
consumer impact note
rollback plan
release note
approval by responsible owner
```

### 17.4. No silent schema drift

Canonical schema, API schemas and database schema must not diverge silently. Changes must be reflected in:

```text
schema file
SRS requirement IDs
OpenAPI contract
migration if needed
tests
changelog
```

---

## 18. Requirements Traceability Seed

### 18.1. Traceability principle

Every future requirement should be traceable:

```text
Vision Objective
  → Product Charter Goal
  → SRS Requirement
  → Use Case
  → Component
  → Data/API Contract
  → Test / Acceptance Criterion
  → Release Note
```

### 18.2. Product requirement seed matrix

| Product Requirement ID | Requirement seed | Future SRS area |
|---|---|---|
| PRD-CORPUS-001 | System must maintain inventory for all active and candidate source files. | Data / Import |
| PRD-CORPUS-002 | Every source file must have stable source_id and checksum before import. | Data / Import |
| PRD-CORPUS-003 | Future files must pass onboarding workflow before production use. | Data / Operations |
| PRD-DATA-001 | Every production quiz item must use canonical schema. | Data |
| PRD-DATA-002 | Every production quiz item must preserve source traceability. | Data |
| PRD-DATA-003 | Every approved item must have CEFR level and theme. | Data / Education |
| PRD-STATUS-001 | Only approved/published items may be delivered to consumers. | Delivery / API |
| PRD-API-001 | All external consumers must use versioned API. | API |
| PRD-API-002 | API errors must be machine-readable. | API |
| PRD-SEL-001 | Selection engine must enforce consumer rules. | Selection |
| PRD-SEL-002 | Selection engine must enforce repeat policy. | Selection |
| PRD-TG-001 | Telegram worker must use API/selection engine, not raw CSV. | Telegram |
| PRD-BILL-001 | Access must be controlled by entitlements and quotas. | Billing |
| PRD-AN-001 | Delivery and attempt events must be logged. | Analytics |
| PRD-SEC-001 | Admin and API access must enforce authorization. | Security |
| PRD-OPS-001 | Production must have backup, monitoring and rollback path. | Operations |

### 18.3. Use case seed list

Future `03_use_cases.md` should include at least:

```text
UC-001 Admin registers a new source file
UC-002 Admin runs dry-run import
UC-003 Admin resolves duplicate/conflict candidates
UC-004 Admin approves imported quiz item
UC-005 API consumer requests next quiz
UC-006 API consumer submits attempt
UC-007 Telegram channel receives scheduled quiz
UC-008 Consumer exceeds quota
UC-009 Teacher requests quiz pack by level/topic
UC-010 User reports item issue
UC-011 Admin retires problematic item
UC-012 Product owner reviews corpus coverage
UC-013 Billing webhook updates entitlement
UC-014 Operations owner restores backup
UC-015 Demo owner executes Stanford-style demo
```

---

## 19. Consumer Model

### 19.1. Consumer definition

Consumer is any entity that receives quiz content from API Quiz Bank.

Consumer types:

```text
web_app
telegram_channel
telegram_bot
mobile_app
teacher_dashboard
school_account
external_api_client
internal_demo_client
```

### 19.2. Consumer lifecycle

```text
created
configured
active
suspended
limited
archived
blocked
```

### 19.3. Consumer configuration

Each consumer should have:

```text
consumer_id
type
owner_id
status
allowed_levels
allowed_themes
allowed_objectives
allowed_patterns
daily/monthly quota
repeat_policy
delivery_mode
schedule if applicable
plan_id
entitlements
rate limit
created_at
updated_at
```

### 19.4. Consumer rule examples

Telegram channel:

```text
type: telegram_channel
levels: A1,A2,B1
themes: T01,T02,T03
schedule: 09:00 Europe/Berlin daily
count_per_day: 1
repeat_window_days: 90
status: active
```

Teacher dashboard:

```text
type: teacher_dashboard
levels: A1-C1
themes: selected by teacher
session_size: 10-30 items
repeat_policy: avoid within group session
status: active
```

External API client:

```text
type: external_api_client
quota: 10,000 requests/month
allowed_endpoints: next quiz, attempts, topics
rate_limit: configured
status: active
```

### 19.5. Consumer policy

Consumers must not:

- bypass API;
- access raw source files;
- receive draft items;
- exceed entitlements;
- disable delivery logging;
- override repeat policy unless explicitly allowed.

---

## 20. API Product Policy

### 20.1. API-first rule

API is the product surface. All delivery channels must use API or internal service contracts aligned with API rules.

### 20.2. API versioning

Initial public API namespace:

```text
/v1
```

Breaking changes require a new version or documented migration path.

### 20.3. Initial API capabilities

MVP API should include:

```text
GET /v1/topics
GET /v1/levels
GET /v1/quiz-items/next
POST /v1/attempts
GET /v1/consumer-rules
GET /v1/health
```

Admin/internal endpoints may include:

```text
POST /v1/admin/sources
POST /v1/admin/imports/dry-run
GET /v1/admin/imports/{id}
PATCH /v1/admin/quiz-items/{id}/status
GET /v1/admin/coverage
```

### 20.4. API response principle

API should return only what the consumer is entitled to receive. Admin fields must not leak into public responses.

### 20.5. API error model

API errors should use a consistent Problem Details-style shape:

```json
{
  "type": "https://api.quizbank.example/problems/quota-exceeded",
  "title": "Quota exceeded",
  "status": 429,
  "detail": "This consumer has reached today's quiz delivery limit.",
  "instance": "/v1/quiz-items/next"
}
```

### 20.6. API product metrics

```text
requests per endpoint
success rate
latency
quota denials
auth failures
repeat-policy denials
no-candidate responses
consumer growth
```

---

## 21. Telegram Product Policy

### 21.1. Telegram role

Telegram is a delivery consumer, not the product core.

```text
Telegram worker → calls selection/API layer → sends quiz → records delivery
```

### 21.2. Telegram delivery rules

Telegram worker must:

- use only eligible items;
- validate Telegram poll compatibility;
- respect schedule;
- record delivery;
- handle failures;
- avoid repeat violations;
- not contain independent content-selection logic that conflicts with selection engine.

### 21.3. Telegram MVP

Telegram MVP:

```text
one configured channel
one scheduled quiz/day or controlled demo schedule
approved/published items only
delivery log
repeat window
failure log
manual pause/resume
```

### 21.4. Telegram constraints to model

Canonical data should support:

```text
question text length compatibility
2-12 options
correct option mapping
quiz type
explanation length compatibility
scheduling metadata
delivery status
message/poll IDs if returned
```

### 21.5. Telegram non-goals for MVP

Not required in first MVP:

- full conversational bot;
- complex user progress inside Telegram;
- paid subscription management inside bot;
- multi-channel marketplace;
- AI-generated daily content.

---

## 22. Admin Product Policy

### 22.1. Admin is critical

Admin workflow is not optional for scale. Even if first version is command-line or minimal UI, the product must have an operational way to manage sources, items, statuses and consumers.

### 22.2. Admin capabilities

Minimum admin capabilities:

```text
view sources
register source
run/import dry-run
view import report
filter items by status/level/theme/source
approve item
publish item
retire item
block item
view duplicates/conflicts
view coverage report
manage consumers
manage entitlements manually
view delivery logs
```

### 22.3. Admin audit log

Admin actions should be logged:

```text
actor
action
target_type
target_id
before_state
after_state
timestamp
reason
```

### 22.4. Admin safety

Admin UI must not allow:

- publishing items without required metadata;
- deleting source traceability;
- bypassing status rules without explicit override;
- editing production content without revision history;
- exposing secrets or API keys.

---

## 23. Billing and Entitlements Product Policy

### 23.1. Billing principle

Payment status alone is not access control. Access is determined by entitlements.

```text
Payment → subscription/plan → entitlements → quota/feature access → API decision
```

### 23.2. Entitlement dimensions

Entitlements may control:

```text
allowed levels
allowed themes
allowed consumer types
API request quota
quiz delivery quota
Telegram scheduling
teacher dashboard access
school group count
analytics access
export access
support tier
```

### 23.3. Plan examples

| Plan | Target | Possible entitlements |
|---|---|---|
| Free | Demo users | limited daily quizzes, limited topics |
| Student | Individual learners | more levels/topics, progress tracking |
| Teacher | Educators | quiz packs, groups, classroom analytics |
| Channel | Telegram owners | scheduled delivery, channel quota |
| School | Organizations | multiple teachers/groups, dashboard |
| API Pro | Developers | API quota, webhooks, SLA-like support |

### 23.4. Billing MVP

Billing MVP may be manual/provider-light but must include internal model:

```text
customer
consumer
plan
entitlement
quota
usage
valid_until
manual_override
```

### 23.5. Billing non-negotiables

- Do not hardcode “paid=true means all access”.
- Do not put billing rules only inside Telegram bot.
- Do not expose premium content without entitlement check.
- Do not ignore usage records.

---

## 24. Analytics Product Policy

### 24.1. Analytics purpose

Analytics makes the product measurable and improves trust, quality and monetization.

### 24.2. Analytics layers

```text
corpus analytics
import analytics
delivery analytics
attempt analytics
consumer analytics
billing/usage analytics
quality feedback analytics
operations analytics
```

### 24.3. MVP analytics

Minimum analytics:

```text
items by status
items by CEFR level
items by theme
items by objective/pattern
delivery count by consumer
delivery success/failure
repeat-policy blocks
attempt correctness if attempts are collected
quota usage by consumer
```

### 24.4. Stanford-ready analytics

For presentation, show:

```text
corpus size and coverage
current status distribution
source governance flow
API delivery volume demo
consumer delivery log
coverage heatmap
future source onboarding report
```

### 24.5. Analytics integrity

Analytics should be derived from system records, not manually invented presentation numbers.

---

## 25. Security and Trust Product Policy

### 25.1. Security principle

Security is part of product trust, not a later add-on.

### 25.2. Security baseline

Before public or paid access:

```text
admin authentication
API authentication
object-level authorization
hashed/sealed API keys or tokens
secrets outside repository
rate limiting or abuse controls
admin audit log
safe error responses
backup policy
incident response path
```

### 25.3. Product trust commitments

API Quiz Bank should be able to say:

```text
We know where each item came from.
We know which items were delivered.
We know which consumer received what.
We enforce access rules.
We can disable a source/item/consumer.
We can recover from operational failure.
```

### 25.4. Privacy posture

MVP should minimize personal data. Store only what is needed for:

- authentication;
- usage/attempt tracking;
- billing/entitlement;
- abuse prevention;
- support;
- analytics.

### 25.5. Security non-goals for MVP

Not required at MVP unless needed by deployment context:

- enterprise SSO;
- advanced DLP;
- formal SOC 2;
- full compliance program;
- real-time fraud engine.

But architecture should not block future maturity.

---

## 26. Operations Product Policy

### 26.1. Operations principle

A product that cannot be operated reliably is not ready to scale.

### 26.2. Operational capabilities

Required before production claim:

```text
health checks
structured logs
error tracking
basic metrics
backup schedule
restore procedure
release checklist
rollback process
incident playbook
owner assignment
```

### 26.3. Failure categories

Track and handle:

```text
import failure
schema validation failure
API outage
database outage
Telegram send failure
quota calculation failure
billing webhook failure
auth failure
source conflict
bad item report
```

### 26.4. Incident severity

| Severity | Example | Response |
|---|---|---|
| SEV-1 | Paid/public API unavailable, data exposure | Immediate response, rollback/disable, incident note |
| SEV-2 | Telegram delivery broken, billing access wrong | Same-day response, fix and report |
| SEV-3 | Import issue, analytics bug | Scheduled fix |
| SEV-4 | Documentation/report mismatch | Routine correction |

### 26.5. Rollback principle

Every launch should have an explicit rollback or disable path:

```text
disable consumer
disable source
retire/block item
rollback deployment
revert manifest change
restore database backup
pause Telegram scheduler
```

---

## 27. Repository and Engineering Product Policy

### 27.1. Repository principle

The repository should make the product understandable and maintainable.

### 27.2. Recommended structure

```text
README.md
CONSTITUTION.md
CHANGELOG.md
SECURITY.md
CONTRIBUTING.md
CODEOWNERS

docs/
  00_vision.md
  01_product_charter.md
  02_requirements_srs.md
  03_use_cases.md
  04_domain_model.md
  05_architecture.md
  06_data_standard.md
  07_api_standard.md
  08_security_threat_model.md
  09_quality_assurance.md
  10_operations.md
  11_billing_model.md
  12_analytics_model.md
  13_stanford_presentation_outline.md

data/
  raw/
  manifests/
  taxonomy/
  schemas/
  normalized/

services/
  api/
  admin-web/
  telegram-worker/
  scheduler/
  billing-worker/

libs/
  importers/
  content-validator/
  quiz-selector/
  taxonomy-classifier/

database/
  migrations/
  seeds/
  indexes.sql

infra/
  docker/
  ci/
  deployment/

tests/
  unit/
  integration/
  contract/
  data-quality/
```

### 27.3. Engineering gates

Production-relevant branches should use:

```text
pull requests
required checks
code review
schema validation
API contract tests
import tests
security checks where possible
changelog for user/product relevant changes
```

### 27.4. Generated files

Generated reports such as README/inventory snapshots should be marked and regenerated through tooling, not manually edited.

### 27.5. Test categories

```text
unit tests
parser tests
schema validation tests
API contract tests
selection engine tests
entitlement tests
Telegram compatibility tests
migration tests
import regression tests
```

---

## 28. Data and Taxonomy Product Policy

### 28.1. Data principle

Data model must support both current corpus and future expansion.

### 28.2. Required taxonomy dimensions

```text
CEFR level
theme_id
objective_id
pattern_id
item_type
tags
source_id
status
```

### 28.3. Coverage matrix

Coverage should be measured by:

```text
level × theme_id × objective_id × pattern_id
```

This allows the product team to identify gaps and decide future content creation priorities.

### 28.4. Canonical item minimum

A production-eligible item should have:

```text
stable item id
source traceability
German stem/question
options
correct answer reference
CEFR level
theme_id
objective_id
pattern_id
status
content_hash
created/imported timestamp
updated timestamp
```

### 28.5. Versioning and revisions

When content changes materially, system should preserve:

```text
previous content hash
revision number
change reason
changed_by
changed_at
impact on delivery
```

---

## 29. Quality Product Policy

### 29.1. Quality scope

Quality in this charter means operational product quality, not a full repeated pedagogical audit of every existing item.

Operational quality includes:

```text
schema completeness
metadata completeness
source traceability
duplicate/conflict classification
Telegram compatibility
API delivery eligibility
status control
coverage reporting
analytics consistency
```

### 29.2. Quality signals

Collect or prepare for:

```text
wrong answer reports
low correctness outliers
high skip rate
duplicate reports
explanation missing
Telegram delivery issue
source conflict
teacher/admin feedback
```

### 29.3. Bad item handling

If item is reported problematic:

```text
mark flagged
stop future delivery if severity high
route to review
record reason
fix/approve or retire/block
keep delivery history
```

### 29.4. Quality metrics

```text
approved item count
published item count
flagged item count
retired item count
duplicate candidate count
missing metadata count
coverage gaps
user reports per 1,000 deliveries
correctness distribution
```

---

## 30. Business and Monetization Charter

### 30.1. Business thesis

API Quiz Bank can monetize because it offers structured, traceable, level-aware German quiz content through controlled delivery and API access.

### 30.2. Value propositions

| Segment | Value proposition |
|---|---|
| Learners | Practice German by level/topic with reliable quizzes. |
| Teachers | Save time preparing exercises and track topic weaknesses. |
| Telegram channels | Automated high-quality quiz content. |
| Schools | Structured content infrastructure for groups. |
| Developers | API access to German quiz content. |
| Partners | Scalable content layer without building a question bank from scratch. |

### 30.3. Revenue model options

```text
subscription plans
API usage plans
teacher/school licenses
Telegram channel automation plans
content pack licensing
B2B integration fees
manual institutional contracts
```

### 30.4. Monetization guardrails

Do not monetize before:

- entitlement model exists;
- quota enforcement exists;
- usage tracking exists;
- support path exists;
- terms/pricing are clear enough;
- access can be disabled safely.

### 30.5. Packaging logic

Content can be packaged by:

```text
CEFR level
theme/objective
consumer type
usage quota
feature access
analytics access
support tier
```

Avoid selling “all content forever” as the only model; it weakens future packaging and platform value.

---

## 31. Stanford-Ready Product Definition

### 31.1. Meaning

Stanford-ready means the project can be defended as a serious, scalable, governed engineering product.

It must show:

```text
strategic clarity
technical architecture
data governance
API contract
working demo
operational discipline
security awareness
business model
scaling roadmap
risk awareness
```

### 31.2. Required artifacts

```text
1. CONSTITUTION.md
2. docs/00_vision.md
3. docs/01_product_charter.md
4. docs/02_requirements_srs.md
5. docs/03_use_cases.md
6. docs/04_domain_model.md
7. docs/05_architecture.md
8. docs/06_data_standard.md
9. docs/07_api_standard.md
10. docs/08_security_threat_model.md
11. docs/10_operations.md
12. docs/11_billing_model.md
13. source inventory
14. import manifest
15. canonical schema
16. OpenAPI spec
17. architecture diagram
18. source onboarding demo
19. API demo
20. Telegram or consumer demo
21. analytics snapshot
22. launch gates checklist
23. roadmap
```

### 31.3. Demo narrative

```text
Problem: German learning quiz content is fragmented and hard to scale.
Asset: API Quiz Bank starts with a large verified corpus.
Insight: Content becomes product only through governance, canonical data and API delivery.
System: Sources → Import → Database → Selection → API → Consumers → Analytics.
Proof: Working next-quiz API, delivery log, source traceability and onboarding flow.
Scale: New files can be added through controlled onboarding.
Business: Entitlements, quotas and plans enable monetization.
Trust: Security, operations and launch gates reduce risk.
```

### 31.4. Demo must not hide

Presentation must be honest about:

- which parts are live;
- which parts are MVP/manual;
- which parts are roadmap;
- current item status distribution;
- risks and mitigations;
- next engineering gates.

### 31.5. Stanford-ready acceptance

A strong demo should be able to answer:

```text
Where did this quiz item come from?
Why is this item eligible for this consumer?
Why did the API choose this item?
Was it delivered before?
What happens if quota is exceeded?
How do we add a new file?
How do we prevent a bad item from being delivered?
How do we prove coverage?
How do we scale beyond Telegram?
How do we monetize without breaking access control?
How do we recover if a deployment fails?
```

---

## 32. Roadmap Charter

### 32.1. Roadmap principle

Roadmap must follow dependency order, not excitement order.

```text
Governance → Data → API → Delivery → Admin → Billing → Analytics → Scale
```

### 32.2. Recommended roadmap

| Phase | Name | Main deliverable |
|---|---|---|
| 0 | Governance | Constitution, Vision, Product Charter |
| 1 | Inventory | file_inventory, import_manifest, source onboarding |
| 2 | Schema | canonical quiz item schema, taxonomy |
| 3 | Import | parser profiles, dry-run, import reports |
| 4 | Database | PostgreSQL schema, migrations, seed data |
| 5 | API | `/v1` endpoints, OpenAPI, auth, error model |
| 6 | Selection | next quiz, anti-repeat, consumer rules |
| 7 | Admin | source/item/status management |
| 8 | Telegram | scheduled controlled pilot |
| 9 | Billing | entitlements, quotas, plans |
| 10 | Analytics | dashboards/reports |
| 11 | Operations | monitoring, backups, incident playbook |
| 12 | Stanford Demo | narrative, diagrams, demo scripts |

### 32.3. Roadmap rules

- Do not start paid public access before entitlement enforcement.
- Do not scale Telegram before selection engine and delivery logs.
- Do not add many new files before source onboarding works on one sample.
- Do not claim production readiness before operations gate.
- Do not claim API product readiness before OpenAPI contract and auth model.

---

## 33. Risk Register

### 33.1. High-level risks

| Risk ID | Risk | Impact | Mitigation |
|---|---|---|---|
| R-001 | Building bot/site before data governance | High | Enforce dependency order. |
| R-002 | New files added chaotically | High | Source onboarding gate. |
| R-003 | API serves draft/unapproved content | High | Status filtering and tests. |
| R-004 | Repeats reduce user trust | Medium/High | Delivery logs and repeat policy. |
| R-005 | Billing grants wrong access | High | Entitlements model. |
| R-006 | Source traceability incomplete | High | source_id + checksum + import batch. |
| R-007 | Schema drift | High | JSON Schema, SRS, tests, change control. |
| R-008 | Telegram constraints break delivery | Medium | Telegram compatibility validation. |
| R-009 | Overbuilding before MVP proof | Medium | Strict MVP boundaries. |
| R-010 | Demo overclaims readiness | High | Demo evidence checklist. |
| R-011 | Security weakness in API/admin | High | Security gate and threat model. |
| R-012 | No operational recovery | High | Backups, rollback, incident playbook. |
| R-013 | Coverage gaps hidden | Medium | Coverage matrix reporting. |
| R-014 | Manual processes become invisible | Medium | Document manual MVP steps and roadmap automation. |

### 33.2. Risk escalation

Any risk that can affect public delivery, paid access, data integrity or external demo credibility must be escalated to Product Maintainer and relevant owner before launch.

### 33.3. Risk acceptance

Risk acceptance must record:

```text
risk_id
accepted_by
reason
time limit
mitigation plan
review date
```

---

## 34. Product Acceptance Criteria

### 34.1. Product Charter acceptance

This document is accepted when it:

- clearly defines product identity;
- aligns with Constitution and Vision;
- defines users, scope, MVP and non-goals;
- defines future source onboarding;
- defines launch gates;
- defines governance and decision rights;
- defines monetization and entitlement principles;
- defines Stanford-ready expectations;
- seeds future SRS and use cases.

### 34.2. Platform MVP acceptance

Platform MVP is accepted when:

```text
AC-MVP-001: Existing corpus has an inventory/manifest workflow.
AC-MVP-002: A new sample source can be onboarded through the defined process.
AC-MVP-003: Canonical quiz item schema exists.
AC-MVP-004: Import pipeline preserves source traceability.
AC-MVP-005: Database stores quiz items, options, sources, consumers and deliveries.
AC-MVP-006: API can return next eligible quiz item.
AC-MVP-007: API returns no draft items to normal consumers.
AC-MVP-008: Delivery logs are created.
AC-MVP-009: Repeat policy is demonstrable.
AC-MVP-010: Entitlement/quota denial is demonstrable.
AC-MVP-011: Admin or operational workflow can approve/publish/retire items.
AC-MVP-012: Basic analytics report exists.
AC-MVP-013: Demo script works end-to-end.
```

### 34.3. Production acceptance

Production claim requires:

```text
AC-PROD-001: CI/CD or controlled deployment process exists.
AC-PROD-002: Backups and restore procedure exist.
AC-PROD-003: Monitoring and logs exist.
AC-PROD-004: Security baseline is implemented.
AC-PROD-005: Paid access uses entitlements.
AC-PROD-006: API contract is stable and documented.
AC-PROD-007: Incident and rollback plan exists.
AC-PROD-008: Public support/contact path exists.
AC-PROD-009: Launch gate approval is recorded.
```

---

## 35. Documentation Deliverables

### 35.1. Required document set

| Document | Purpose | Priority |
|---|---|---|
| `CONSTITUTION.md` | Binding operational law | Done/Required |
| `00_vision.md` | Strategic direction | Done/Required |
| `01_product_charter.md` | Product operating frame | Current |
| `02_requirements_srs.md` | Detailed requirements | Next |
| `03_use_cases.md` | User/system interaction scenarios | Next |
| `04_domain_model.md` | Entities and domain relationships | High |
| `05_architecture.md` | System architecture | High |
| `06_data_standard.md` | Source/canonical/data rules | High |
| `07_api_standard.md` | API rules and contract | High |
| `08_security_threat_model.md` | Security risks and mitigations | Medium/High |
| `09_quality_assurance.md` | Test strategy and QA gates | Medium/High |
| `10_operations.md` | Deployment, backups, incidents | Medium/High |
| `11_billing_model.md` | Plans, entitlements, quotas | Medium |
| `12_analytics_model.md` | Analytics model, reports and dashboards | Medium |
| `13_stanford_presentation_outline.md` | Demo and pitch narrative | Medium |

### 35.2. Documentation quality rules

Documents should have:

```text
title
version
status
owner
scope
relationship to other docs
clear acceptance criteria
traceability where relevant
change log or version note
```

### 35.3. Documentation update trigger

Update docs when:

- product scope changes;
- source onboarding changes;
- canonical schema changes;
- API behavior changes;
- launch gates change;
- billing model changes;
- security policy changes;
- demo claims change.

---

## 36. Naming and ID Conventions

### 36.1. Product-level IDs

Recommended prefixes:

```text
PG      Product Goal
PRD     Product Requirement seed
UC      Use Case
SR      System Requirement
NFR     Non-functional Requirement
SRC     Source
QI      Quiz Item
CON     Consumer
DEL     Delivery
ATT     Attempt
ENT     Entitlement
PLAN    Plan
DEC     Decision
RISK    Risk
AC      Acceptance Criterion
```

### 36.2. Source IDs

Source IDs should be stable and not depend only on filename.

Example:

```text
SRC-000001
SRC-000002
SRC-2026-0001
```

### 36.3. Public item IDs

Public item IDs should not expose internal database sequence if avoidable.

Examples:

```text
qi_01H...
QI-A1-T02-000123
```

### 36.4. Slug rules

Slugs should be:

```text
lowercase
ASCII where possible
hyphen or underscore consistent
stable after publication
```

---

## 37. Product Backlog Themes

### 37.1. Backlog structure

Backlog should be organized by themes:

```text
Governance
Source Onboarding
Import Pipeline
Canonical Data
Taxonomy
Database
API
Selection Engine
Admin
Telegram
Billing
Analytics
Security
Operations
Presentation
```

### 37.2. Backlog item requirements

Each major backlog item should include:

```text
title
problem
user/value
linked requirement or goal
acceptance criteria
owner
priority
risk
```

### 37.3. Priority logic

Prioritize by:

```text
1. unlocks dependent work
2. reduces systemic risk
3. proves core thesis
4. supports launch gate
5. improves demo credibility
6. creates revenue path
```

Do not prioritize visual polish before data/API trust.

---

## 38. Open Questions

These questions should be resolved in future documents, not by ad hoc implementation:

```text
1. What is the final canonical schema field set?
2. Which database naming convention will be used?
3. Will API consumers be authenticated by API keys, OAuth, session tokens or mixed model?
4. What exact pricing plans will launch first?
5. Which payment provider will be used first?
6. What is the first Telegram pilot channel configuration?
7. How much of admin workflow is UI vs CLI in MVP?
8. How are teacher groups modeled?
9. What exact item issue reporting flow is needed?
10. What deployment environment is used for demo and production?
11. What legal/privacy text is required for public beta?
12. What is the exact Stanford-style presentation audience and duration?
```

Open questions are not blockers for this Product Charter. They are inputs to SRS, architecture, billing and operations documents.

---

## 39. Reference Standards and Alignment

This Product Charter aligns the project with:

- Stanford/SLAC-style requirements discipline: goal → needs/features → requirements → use cases → traceability → tests → change control.
- CEFR A1–C2 level model for language proficiency.
- OpenAPI Specification for API contract and discoverability.
- JSON Schema Draft 2020-12 for canonical data validation.
- RFC 9457 Problem Details for HTTP API error format.
- OWASP API Security Top 10 for API risk awareness.
- GitHub protected branches / required checks for repository discipline.
- Telegram Bot API poll/quiz constraints for Telegram delivery compatibility.

Reference links:

```text
Stanford/SLAC Requirements Methodology:
https://www-group.slac.stanford.edu/cdsoft/nlc_arch/nlc_requirements/RequirementsMethod.pdf

CEFR level descriptions:
https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions

OpenAPI Specification 3.1.0:
https://spec.openapis.org/oas/v3.1.0.html

JSON Schema Draft 2020-12:
https://json-schema.org/draft/2020-12

RFC 9457 Problem Details:
https://www.rfc-editor.org/rfc/rfc9457.html

OWASP API Security Top 10 2023:
https://owasp.org/API-Security/editions/2023/en/0x11-t10/

GitHub protected branches:
https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches

Telegram Bot API:
https://core.telegram.org/bots/api
```

---

## 40. Final Product Charter Rule

API Quiz Bank must not be built as a collection of convenient shortcuts.

It must be built as a governed product system:

```text
source-controlled
schema-driven
API-first
status-aware
consumer-aware
entitlement-aware
repeat-aware
analytics-ready
operations-ready
presentation-ready
future-source-ready
```

The first duty of the product is trust.

The second duty is delivery.

The third duty is scale.

The fourth duty is monetization.

The fifth duty is presentation clarity.

All future product, engineering, data and business decisions must preserve this order.
