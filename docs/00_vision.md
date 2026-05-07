# API Quiz Bank — Vision

**Документ:** `docs/00_vision.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.1.0  
**Статус:** foundational vision document; updated with future source onboarding vision  
**Дата:** 2026-04-27  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized product maintainer  
**Керівний документ:** `CONSTITUTION.md`  
**Наступні документи:** `01_product_charter.md`, `02_requirements_srs.md`, `03_use_cases.md`, `04_domain_model.md`, `05_architecture.md`, `06_data_standard.md`, `07_api_standard.md`

---

## 0. Executive Summary

**API Quiz Bank** — це керована, API-first платформа для німецьких вікторин.

Проєкт не є просто сайтом, Telegram-ботом або папкою з CSV-файлами. Проєкт є освітньо-технологічною інфраструктурою, де перевірений контент з німецької мови перетворюється на масштабований цифровий продукт через source governance, canonical data model, import pipeline, production database, selection engine, versioned API, Telegram/web/bot/app delivery, analytics, billing, security та operations.

Головна продуктова теза:

```text
Verified German quiz content becomes a scalable product only when it is governed,
normalized, served through a contract, measured, monetized, and operated.
```

Практично це означає:

```text
перевірені німецькі вікторини
  → керовані джерела
  → canonical quiz items
  → production database
  → selection engine
  → versioned API
  → Telegram / website / bots / apps / schools / external clients
  → analytics / billing / quality feedback / scale
```

Платформа також має бути спроєктована для **майбутнього контрольованого розширення корпусу**. Нові файли з вікторинами не повинні додаватися хаотично або напряму в delivery layer. Вони мають проходити source onboarding pipeline:

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

Отже, поточний corpus baseline є стартовим активом, а не верхньою межею продукту. API Quiz Bank має масштабуватися як content platform, яка може безпечно приймати нові source files, нові content packs, нові теми, нові формати та нові educational use cases без руйнування existing database, API contract, analytics або production delivery.

API Quiz Bank повинен стати не “місцем, де лежать питання”, а **центральним ядром**, яке може надійно видавати правильне питання правильному consumer у правильному контексті та фіксувати, що сталося після видачі.

Цей документ задає стратегічне бачення: що ми будуємо, навіщо, для кого, чим це відрізняється від звичайного quiz API, що означає Stanford-ready, які метрики успіху, які ризики, яка MVP-логіка і до яких майбутніх requirements має вести це бачення.

---

## 1. Роль документа

### 1.1. Що це за документ

`00_vision.md` — перший стратегічний документ після `CONSTITUTION.md`. Він фіксує спільне розуміння між product, engineering, data, operations, business і presentation layers.

Документ відповідає на питання:

```text
Що ми будуємо?
Чому це важливо?
Для кого це потрібно?
Чим API Quiz Bank відрізняється від папки файлів або простого бота?
Яка головна системна архітектурна ідея?
Що має бути правдою, щоб проєкт був професійним?
Як у майбутньому додаються нові quiz-файли без хаосу, дублювання і schema drift?
Що означає Stanford-ready для цього продукту?
До яких vision objectives мають привʼязуватися майбутні requirements?
```

### 1.2. Чим цей документ не є

Цей документ не є:

- повним Software Requirements Specification;
- database schema;
- OpenAPI contract;
- UI specification;
- Telegram bot implementation plan;
- повторним аудитом усіх відповідей;
- заміною Конституції;
- обіцянкою roadmap без engineering gates.

Vision визначає напрям. Product Charter визначить продуктову рамку. SRS перетворить напрям у requirements. Use Cases опишуть взаємодії. Architecture опише компоненти. Data/API Standards зададуть машинні контракти.

### 1.3. Stanford-style логіка

API Quiz Bank має будуватися за дисципліною, близькою до Stanford/SLAC-style engineering approach:

```text
goal → needs → features → system requirements → use cases → test cases → traceability → change control
```

Кожна серйозна функція у майбутньому повинна мати трасування:

```text
Vision objective
  → product requirement
  → system requirement
  → use case
  → implementation component
  → API/data contract
  → acceptance criterion / test
  → release note
```

Це означає, що проєкт має бути не тільки красивим у презентації, а й пояснюваним, перевірюваним, відтворюваним і керованим.

---

## 2. Однореченеве бачення

**API Quiz Bank — це керований API-шар для якісного контенту німецьких вікторин, який дозволяє надійно доставляти quiz items через Telegram, web, bots, schools, applications і external integrations.**

---

## 3. Назва та ідентичність продукту

### 3.1. Публічна назва

Публічна та стратегічна назва проєкту:

```text
API Quiz Bank
```

Цю назву слід використовувати у стратегічних документах, презентаціях, demo materials, architecture diagrams, pitch materials і future product descriptions.

### 3.2. Внутрішня історична назва

Назви `QuizBank` або `German QuizBank Platform` можуть залишатися у внутрішніх шляхах, скриптах, історичних файлах або технічних нотатках, якщо негайне перейменування створює ризик хаосу.

Але продуктова ідентичність має сходитися до:

```text
API Quiz Bank
```

### 3.3. Ідентичність в одному принципі

```text
API Quiz Bank is not a quiz collection.
API Quiz Bank is an educational content infrastructure product.
```

Ключові слова ідентичності:

```text
Governed. Canonical. API-first. Measured. Scalable.
```

---

## 4. Стратегічний контекст

### 4.1. Поточна реальність

Проєкт уже має значний корпус перевірених німецьких quiz items. Поточний operational snapshot фіксує:

- `115` active bank files;
- `30,974` active rows/items;
- top-level corpus у форматі CSV;
- canonical levels `A1`, `A2`, `B1`, `B2`, `C1`, `C2`;
- `18` theme areas;
- objective and pattern dimensions;
- усі active items зараз мають operational status `draft`;
- local constitution tooling показує `violations=0` для поточного snapshot.

Статус `draft` у цьому контексті не означає “поганий контент”. Він означає: item ще не введено у production workflow платформи, не має повного production metadata package і не пройшов publication gate.

### 4.2. Головний ризик

Головний ризик уже не в тому, що немає контенту. Контент є.

Головний ризик — що великий перевірений корпус залишиться у файловому стані та перетвориться на operational chaos:

```text
many files
  → unclear source of truth
  → inconsistent import rules
  → no stable item IDs
  → no production statuses
  → no API contract
  → no delivery history
  → no anti-repeat logic
  → no entitlement control
  → no analytics
  → no scalable product
```

Без governance навіть сильний контент важко продавати, масштабувати, пояснювати, інтегрувати й презентувати.

### 4.3. Головна можливість

Можливість полягає в тому, щоб перетворити corpus на infrastructure product.

Ринок і користувачі потребують не просто “ще більше питань”. Вони потребують:

- надійного доступу до якісного German quiz content;
- CEFR-aware delivery;
- topic-aware practice;
- repeat-safe scheduling;
- API access for external tools;
- teacher/school workflows;
- Telegram automation;
- usage analytics;
- paid access control;
- source traceability;
- scalable operations.

API Quiz Bank має стати цим ядром.

---

## 5. Problem Statement

### 5.1. Основна проблема

Контент для вивчення німецької часто фрагментований, керується вручну, важко масштабується і погано інтегрується між каналами.

Типовий quiz bank ламається, коли:

- питання лежать у різних файлах без stable source IDs;
- немає canonical item model;
- сайт, Telegram і бот самостійно вибирають питання;
- повтори не відстежуються;
- paid access контролюється вручну;
- користувачі не можуть покладатися на level/topic consistency;
- external developers не мають documented API;
- analytics відсутня або не повʼязана з delivery;
- масштабування вимагає переписування системи.

### 5.2. Освітня проблема

Learners потребують практики, яка є:

- level-appropriate;
- topic-aware;
- короткою для щоденного використання;
- достатньо повторюваною для навчання, але не хаотично повторюваною;
- структурованою для прогресу;
- пояснюваною й довіреною.

Teachers потребують контенту, який:

- швидко вибирається;
- привʼязаний до CEFR;
- організований за topic/objective/pattern;
- може використовуватися в групах;
- дає статистику помилок і прогресу.

### 5.3. Технічна проблема

Applications, Telegram channels, bots and external clients потребують доступу до контенту, який є:

- stable;
- documented;
- secure;
- versioned;
- rate-limited;
- permission-aware;
- traceable;
- resilient to source changes.

CSV-файли не можуть бути таким production contract. Versioned API може.

### 5.4. Бізнес-проблема

Корпус має комерційну цінність тільки тоді, коли доступ до нього можна контролювати.

Для монетизації потрібні:

- plans;
- quotas;
- entitlements;
- API keys;
- consumer-specific limits;
- billing events;
- analytics for value demonstration;
- delivery history;
- admin overrides;
- school/institutional licensing path.

Без цього продукт залишається архівом, а не бізнес-платформою.

---

## 6. Product Thesis

### 6.1. Головна теза

```text
The API is the product surface.
The governed content core is the product asset.
The selection engine is the product intelligence.
Analytics and entitlements are the product control layer.
```

### 6.2. Чому API-first

API-first — це не технічна мода. Це стратегія масштабування.

Якщо API є головним product contract, тоді один governed content core можуть використовувати:

- Telegram channel;
- Telegram bot;
- admin web;
- public website;
- teacher dashboard;
- school dashboard;
- mobile app;
- external partner app;
- scheduler;
- analytics pipeline;
- billing layer.

Без API-first кожен інтерфейс стає окремим mini-product. З API-first кожен інтерфейс стає consumer одного ядра.

### 6.3. Чому governance-first

Governance-first означає:

- кожен source file має identity;
- кожен item має source traceability;
- кожен item має status;
- кожен import відтворюваний;
- кожен production delivery логований;
- кожен external consumer працює через contract;
- кожен monetized access path керується entitlements.

Це відрізняє платформу від корисного, але крихкого скрипта.

---

## 7. Product Mission

Місія API Quiz Bank — зробити якісний German quiz content доступним як керовану, масштабовану, вимірювану й монетизовану платформу.

### 7.1. Для learners

Допомагати learners практикувати німецьку через короткі, targeted, level-aware quiz interactions у каналах, які зручно використовувати щодня.

### 7.2. Для teachers

Дати teachers структурований банк reusable quiz items, які можна відбирати за CEFR level, topic, objective, pattern and learning context.

### 7.3. Для developers

Надати documented API, через який German quiz content легко інтегрується в apps, bots, websites, dashboards and learning systems.

### 7.4. Для Telegram/channel owners

Дозволити каналам і спільнотам автоматично публікувати German quizzes без ручного хаосу й uncontrolled repetition.

### 7.5. Для project owner

Перетворити corpus на defensible educational technology product з governance, monetization, analytics and scale potential.

### 7.6. Для Stanford-style presentation

Показати не тільки велику кількість питань, а повну систему: asset, governance, requirements, architecture, API, delivery, analytics, monetization, operations and roadmap.

---

## 8. Target Users and Stakeholders

### 8.1. Основні user groups

| User group | Need | Product value |
|---|---|---|
| German learners | Daily practice by level/topic | Short, targeted, trackable quizzes |
| Teachers | Ready content for lessons/groups | Structured, reusable quiz bank |
| Language schools | Scalable practice infrastructure | Group access, reporting, controlled content |
| Telegram channel owners | Automated quiz publishing | Scheduled delivery and anti-repeat logic |
| Bot users | Interactive quiz flow | Level/topic personalization |
| Developers | Content API | Versioned, documented endpoints |
| Product owner/admin | Control and monetization | Governance, billing, analytics |
| Reviewers/investors/Stanford audience | Evidence of system quality | Traceable architecture and credible roadmap |

### 8.2. Stakeholder roles

```text
Owner / Product Maintainer
  Володіє strategy, constitution, release gates, monetization decisions.

Content Administrator
  Керує imports, metadata, statuses, review queues, issue reports.

Engineer
  Реалізує API, data pipeline, database, services, tests, infrastructure.

Teacher / Expert Reviewer
  Перевіряє flagged items, confirms levels, validates educational usefulness.

Consumer Owner
  Володіє channel, app, bot, school account або API integration.

Learner
  Отримує й проходить quizzes.

External Reviewer
  Оцінює platform quality, architecture and scalability.
```

---

## 9. Jobs To Be Done

### 9.1. Learner jobs

```text
Коли я хочу регулярно практикувати німецьку,
я хочу отримувати короткі вікторини на моєму рівні,
щоб покращувати мову без окремого планування великого заняття.
```

```text
Коли я помиляюся,
я хочу бачити пояснення або feedback path,
щоб навчатися, а не просто вгадувати.
```

### 9.2. Teacher jobs

```text
Коли я викладаю групі A2 або B1,
я хочу швидко вибрати релевантні quizzes за темою й рівнем,
щоб не створювати матеріал з нуля.
```

```text
Коли мої студенти практикуються,
я хочу бачити, які topics викликають найбільше помилок,
щоб коригувати навчання.
```

### 9.3. Telegram/channel jobs

```text
Коли я веду German-learning Telegram channel,
я хочу scheduled quiz delivery,
щоб аудиторія отримувала стабільну практику без ручного постингу.
```

```text
Коли quizzes публікуються автоматично,
я хочу no-repeat policy,
щоб канал не виглядав випадковим або недбалим.
```

### 9.4. Developer jobs

```text
Коли я створюю German-learning app,
я хочу endpoint для next suitable quiz,
щоб інтегрувати якісний контент без побудови власного bank.
```

```text
Коли я залежу від API,
я хочу OpenAPI documentation and stable versioning,
щоб інтеграція була безпечною.
```

### 9.5. Owner/admin jobs

```text
Коли я керую десятками тисяч items,
я хочу imports, statuses, metadata and analytics,
щоб bank залишався governable.
```

```text
Коли users платять за доступ,
я хочу entitlements and quotas,
щоб доступ був справедливим, auditable and monetizable.
```

---

## 10. Product Scope

### 10.1. In scope

У бачення входить:

- governed source file inventory;
- future source onboarding workflow for new quiz files;
- import manifest;
- canonical quiz item model;
- production database;
- status lifecycle;
- CEFR-aware taxonomy;
- theme/objective/pattern coverage;
- selection engine;
- versioned API;
- OpenAPI contract;
- Telegram delivery compatibility;
- admin review workflow;
- delivery logging;
- attempt tracking;
- analytics;
- billing and entitlements;
- security and access control;
- operational monitoring;
- documentation package;
- Stanford-ready presentation package.

### 10.2. Out of scope для першої execution phase

Перший execution phase не включає:

- перебудову всіх quiz items з нуля;
- повторний повний content audit усіх відповідей;
- polished public website до data/API core;
- Telegram як source of truth;
- raw CSV access для users або consumers;
- advanced adaptive testing до появи attempts data;
- full institutional LMS integration до стабілізації API;
- vanity UI замість operational correctness.

### 10.3. Future scope

Майбутній scope може включати:

- new quiz file formats and source content packs;
- adaptive learning paths;
- teacher dashboards;
- school dashboards;
- mobile app integrations;
- external SDKs;
- LMS connectors;
- item response modeling;
- AI-assisted metadata suggestion;
- multilingual explanations;
- certification-style practice paths;
- marketplace/licensing model;
- public developer portal.

---

## 11. Core Product Principles

### Principle 1 — API-first

Усі серйозні consumers повинні отримувати quiz content через API або через сервіси, які використовують той самий selection engine.

### Principle 2 — Governance before scale

Немає масштабування без source IDs, checksums, schema, statuses, manifests, access control and delivery logs.

### Principle 3 — Raw files are assets, not the product

CSV-файли доводять походження й підтримують reproducible import. Вони не є production delivery layer.

### Principle 4 — New files are onboarded, not dropped

Будь-який майбутній quiz-файл має проходити controlled source onboarding: source_id, checksum, inventory, manifest, parser assignment, dry-run import, validation, duplicate/conflict checks, import batch and status workflow. Новий файл не має права одразу потрапляти в API, Telegram або production database поза цим процесом.

### Principle 5 — One canonical item model

Усі quiz items мають бути приведені до єдиної canonical internal representation незалежно від того, з якого файлу, формату або content pack вони прийшли.

### Principle 6 — No publication without status

Item не може бути виданий production consumer без release-allowed status.

### Principle 7 — Selection is centralized

Telegram, website, bot and API clients не мають самостійно вигадувати quiz selection logic.

### Principle 8 — Traceability is mandatory

Кожен production item має бути traceable до source file, import batch, content hash and version.

### Principle 9 — Anti-repeat is product quality

Якісна система памʼятає, що вона вже видала.

### Principle 10 — Entitlements control monetization

Payment alone is not enough. Access must be expressed through explicit permissions, limits and quotas.

### Principle 11 — Documentation is infrastructure

Vision, SRS, use cases, architecture, data standards, API standards, operations and security documents є production infrastructure, а не decoration.

---

## 12. System Vision

### 12.1. High-level system model

```text
+------------------------------------------------------------+
|                        API Quiz Bank                       |
+------------------------------------------------------------+
|                                                            |
|  Source Governance                                         |
|  raw files → source onboarding → inventory → manifest → checksums              |
|                                                            |
|  Data Pipeline                                             |
|  parsers → normalization → canonical schema → validation   |
|                                                            |
|  Content Core                                              |
|  database → statuses → taxonomy → versions → source links  |
|                                                            |
|  Selection Intelligence                                    |
|  level/topic/objective/pattern → repeat policy → quotas    |
|                                                            |
|  Delivery Contract                                         |
|  OpenAPI REST API → errors → auth → versioning             |
|                                                            |
|  Consumers                                                 |
|  Telegram → bots → web → admin → schools → apps → API      |
|                                                            |
|  Control Layer                                             |
|  analytics → billing → entitlements → monitoring → ops     |
|                                                            |
+------------------------------------------------------------+
```

### 12.2. Product layers

#### Layer 1 — Source Governance

Визначає, які файли існують, звідки вони походять, як ідентифікуються, як додаються в майбутньому та чи є вони candidate, registered, active, archived, template, ignored або blocked.

#### Layer 2 — Import and Normalization

Перетворює raw files у canonical quiz items зі stable structure, source metadata and validation status.

#### Layer 3 — Content Core

Зберігає quiz items, options, themes, objectives, patterns, tags, statuses, versions, hashes and source references.

#### Layer 4 — Selection Engine

Обирає next appropriate item для consumer з урахуванням level, theme, objective, pattern, status, quota, repeat history and quality flags.

#### Layer 5 — API Contract

Надає versioned interface для всіх consumers і робить продукт зрозумілим без читання private code.

#### Layer 6 — Delivery Channels

Обслуговує Telegram, bots, website, applications, school dashboards and external integrations.

#### Layer 7 — Analytics and Control

Відстежує deliveries, attempts, correctness, usage, quality reports, quota consumption and operational health.

#### Layer 8 — Monetization

Перетворює plans and payment state у concrete entitlements and access rules.

---

## 13. Data Vision

### 13.1. Data as a product

Quiz corpus має розглядатися як data product.

Data product має:

- identity;
- schema;
- source traceability;
- versioning;
- validation;
- lifecycle status;
- usage rules;
- delivery history;
- quality signals;
- access control;
- documentation.

### 13.2. Canonical item concept

Кожен quiz item має стати canonical object:

```json
{
  "id": "qi_example",
  "schema_version": "1.0.0",
  "stem_de": "Welche Antwort ist richtig?",
  "options": [
    {"id": "op_1", "text_de": "Option A"},
    {"id": "op_2", "text_de": "Option B"}
  ],
  "correct_option_ids": ["op_1"],
  "cefr_level": "A2",
  "theme_id": "T01",
  "objective_id": "O09",
  "pattern_id": "P01",
  "status": "approved",
  "source": {
    "source_file_id": "src_0001",
    "source_locator": "row:128",
    "content_hash": "..."
  }
}
```

Це illustrative example. Остаточна schema буде визначена в `06_data_standard.md` і `data/schemas/quiz_item.schema.json`.

### 13.3. Required data dimensions

Платформа має зберігати щонайменше:

```text
item identity
source identity
content hash
stem/question text
options
correct answer reference
CEFR level
theme_id
objective_id
pattern_id
status
tags
explanation where available
Telegram compatibility fields
delivery constraints
quality flags
versioning metadata
created/imported/updated timestamps
```

### 13.4. Coverage matrix

Coverage має розумітися через:

```text
level × theme_id × objective_id × pattern_id
```

Ця matrix важливіша за загальну кількість питань. Total size має значення, але coverage quality визначає, чи може платформа обслуговувати різні levels, topics and learning goals.

### 13.5. Статус `draft`

Поточний `draft` слід тлумачити так:

```text
draft = not yet production-released through platform workflow
```

Це одночасно захищає дві речі:

- контент може бути вже перевіреним;
- production delivery все одно вимагає publication gates.

### 13.6. Future source expansion and file onboarding

API Quiz Bank має бути спроєктований так, щоб у майбутньому можна було регулярно додавати нові файли з вікторинами без хаосу, ручного дублювання, втрати traceability або ризику для production delivery.

Нові файли не є “просто ще одним CSV у папці”. Кожен новий файл є **source candidate**, який має пройти контрольований onboarding. Це дозволяє масштабувати банк від поточного corpus baseline до набагато більшого content catalog без зміни головної архітектури.

Canonical source onboarding flow:

```text
source candidate
  → intake location
  → source proposal / registration
  → stable source_id
  → filename, format, encoding and size capture
  → checksum
  → file_inventory.csv update
  → import_manifest.yml entry
  → parser profile or parser assignment
  → dry-run parse
  → canonical schema validation
  → metadata enrichment: level/theme/objective/pattern/tags
  → duplicate and conflict detection
  → import batch creation
  → draft/imported/normalized status assignment
  → review or auto-approval gate depending on policy
  → approved/published items
  → generated README/inventory/coverage update
```

Required source states:

```text
candidate
registered
parser_pending
parser_assigned
dry_run_passed
dry_run_failed
imported
normalized
needs_review
active
archived
rejected
blocked
```

Non-negotiable onboarding rules:

```text
1. A new file must never be consumed directly by API, Telegram, website, bot or paid consumer.
2. A new file must receive a stable source_id before import.
3. A filename is not identity; source_id is identity.
4. A file checksum is required before import.
5. Every imported item must retain source_file_id and source_locator.
6. Every import must belong to an import_batch.
7. Unsupported formats are not hacked into production; they receive parser_pending status.
8. New taxonomy needs require taxonomy change control.
9. Re-import must be idempotent or explicitly versioned.
10. New content enters lifecycle statuses before production publication.
```

Цей принцип має бути деталізований у `06_data_standard.md`, `03_use_cases.md`, `04_domain_model.md` and `10_operations.md`.

---

## 14. Educational Vision

### 14.1. CEFR alignment

API Quiz Bank має використовувати CEFR levels як зовнішній освітній стандарт:

```text
A1 → beginner / basic user
A2 → elementary / basic user
B1 → intermediate / independent user
B2 → upper-intermediate / independent user
C1 → advanced / proficient user
C2 → mastery / proficient user
```

Internal difficulty scores можуть бути додані, але вони не замінюють CEFR.

### 14.2. German-specific learning value

Платформа має підтримувати German learning across:

- grammar;
- vocabulary;
- everyday usage;
- administrative language;
- work and education;
- travel and city life;
- health and services;
- finance and banking;
- media and digital life;
- society and politics;
- reasoning and interpretation;
- advanced paraphrase and precision tasks.

### 14.3. Learning modes

Система має підтримувати кілька режимів:

```text
Daily micro-practice
  Short quiz delivery through Telegram/bot/app.

Topic practice
  Learner or teacher selects a theme.

Level practice
  Content is selected by CEFR level.

Mixed review
  System balances topics and avoids excessive repetition.

Teacher assignment
  Teacher creates a set or rule for a group.

API integration
  External client requests next suitable item.

Channel automation
  Scheduled quizzes are posted to a Telegram channel.
```

### 14.4. Quality feedback loop

Система має з часом навчатися з usage data:

- correctness rate;
- response time;
- repeated wrong answers;
- user reports;
- teacher flags;
- item difficulty calibration;
- topic weakness patterns;
- low-value item detection;
- overused item detection.

На launch етапі достатньо expert metadata and deterministic rules. Statistical calibration має зʼявитися після накопичення real attempts data.

---

## 15. API Vision

### 15.1. API як product contract

API має бути офіційним product contract.

Consumer не повинен знати:

- де лежать CSV files;
- як працює importer;
- як database structured internally;
- з якого source file прийшов item;
- як Telegram formatting derived;
- як реалізовано selection logic.

Consumer повинен знати:

- який endpoint викликати;
- яка authentication потрібна;
- які request parameters приймаються;
- яка response schema повертається;
- що означають errors;
- яка quota застосовується;
- яка API version використовується.

### 15.2. Initial API surfaces

Перші API surfaces:

```text
GET  /v1/health
GET  /v1/topics
GET  /v1/levels
GET  /v1/quiz-items/{id}
GET  /v1/quiz-items/next
POST /v1/attempts
GET  /v1/consumers/{id}/rules
GET  /v1/analytics/summary
```

Admin and billing endpoints мають зʼявитися пізніше з жорсткішими permissions.

### 15.3. API values

API має бути:

- versioned;
- documented;
- secure;
- predictable;
- testable;
- rate-limited;
- machine-readable;
- stable enough for external consumers;
- flexible enough for future channels.

### 15.4. API response philosophy

API має повертати достатньо інформації для rendering quiz, але не expose internal data unnecessarily.

```text
Public quiz response:
  item id, question, options, level, topic, allowed metadata.

Admin response:
  source file, source row, hash, status, warnings, review notes.
```

Це підтримує security and product control.

---

## 16. Consumer Vision

### 16.1. One core, many consumers

API Quiz Bank має дозволити багато consumers без дублювання logic.

```text
                +-------------------+
                |  API Quiz Bank    |
                |  Core + API       |
                +---------+---------+
                          |
     +--------------------+--------------------+
     |                    |                    |
 Telegram            Web/Admin              API Clients
 channels/bots       dashboards             apps/schools/tools
```

### 16.2. Telegram channels

Telegram channels мають використовувати scheduled delivery rules:

```text
consumer_id
telegram_chat_id
allowed_levels
allowed_topics
daily_count
posting_window
repeat_window
subscription_status
```

Telegram worker не має самостійно вирішувати, що постити. Він має request item from selection engine and record delivery.

### 16.3. Telegram bot

Telegram bot може підтримувати interactive learning:

```text
/start
select level
select topic
get quiz
submit answer
receive feedback
see progress
manage subscription
```

### 16.4. Public site

Public site не має бути першим technical core. Його майбутня роль:

- landing page;
- product explanation;
- pricing;
- demo quizzes;
- teacher/school onboarding;
- API documentation access;
- account management.

### 16.5. Admin site

Admin site критичніший на ранньому етапі, ніж public site.

Він має підтримувати:

- source inventory view;
- import reports;
- quiz item list;
- status management;
- metadata editing;
- review queues;
- duplicate/quality flags;
- consumer rules;
- channel scheduling;
- entitlement override;
- analytics dashboards.

### 16.6. External API consumers

External clients мають отримувати quiz content без доступу до внутрішньої implementation.

Можливі clients:

- mobile apps;
- language-learning tools;
- school dashboards;
- teacher platforms;
- Telegram automation tools;
- experimental learning interfaces;
- partner products.

---

## 17. Selection Engine Vision

### 17.1. Чому selection важливий

Quiz bank стає розумним, коли може вибрати правильний next item.

Random selection alone is not enough. Selection engine має враховувати:

- item status;
- CEFR level;
- theme;
- objective;
- pattern;
- consumer rules;
- user/channel history;
- repeat policy;
- quotas;
- quality flags;
- availability;
- delivery constraints.

### 17.2. Basic selection flow

```text
1. Consumer requests next quiz.
2. System loads consumer rules and entitlements.
3. System filters items by status, level, topic, objective, pattern.
4. System excludes blocked or recently delivered items.
5. System applies balancing and priority rules.
6. System reserves or selects item.
7. System returns item through API.
8. System logs delivery.
9. System records attempts or interactions.
10. System updates analytics.
```

### 17.3. Anti-repeat policy

Anti-repeat не є optional. Це частина user trust.

Мінімум система має знати:

```text
who received the item
through which consumer/channel
when it was delivered
whether it was answered
whether it should be eligible again
```

### 17.4. Future intelligence

Майбутні версії можуть підтримувати:

- spaced repetition;
- adaptive difficulty;
- weakness detection;
- topic balancing;
- personalized review;
- teacher-defined learning paths;
- item difficulty calibration from attempts.

Але перша вимога — reliable, traceable, non-chaotic selection.

---

## 18. Governance Vision

### 18.1. Чому governance центральний

Корпус уже достатньо великий, щоб manual memory перестала бути безпечною management system.

Governance має відповідати:

```text
Where did this item come from?
Which file produced it?
Which parser imported it?
Which version is published?
Who changed its status?
Can it be delivered?
Was it delivered before?
Which consumer has permission?
What happened after delivery?
```

### 18.2. Source governance

Кожен active source file повинен мати:

- stable `source_id`;
- filename;
- path;
- checksum;
- active/template/archived status;
- parser name;
- row count;
- item count;
- known level/theme metadata;
- import history;
- notes.

### 18.3. Item governance

Кожен production item повинен мати:

- stable item ID;
- source traceability;
- canonical metadata;
- status;
- content hash;
- version history;
- publication readiness;
- quality flags;
- delivery history.

### 18.4. Release governance

Release має вимагати:

- clear scope;
- passing validation;
- database migration if needed;
- OpenAPI update if needed;
- changelog entry;
- rollback path;
- production readiness check.

---

## 19. Monetization Vision

### 19.1. Monetization principle

Проєкт має monetizе controlled access, not raw possession of files.

Цінність не лише в тому, що questions exist. Цінність у тому, що вони:

- governed;
- searchable;
- deliverable;
- level-aware;
- repeat-safe;
- API-accessible;
- measurable;
- integrated;
- reliable.

### 19.2. Entitlements model

Access має визначатися через entitlements:

```text
feature access
level access
topic access
quiz-per-day quota
API request quota
Telegram scheduling rights
teacher dashboard rights
school group rights
analytics rights
admin rights
```

### 19.3. Possible product tiers

| Tier | Target | Possible value |
|---|---|---|
| Free / Demo | Individual learners | Limited daily quizzes, sample topics |
| Student | Learners | More topics, progress, practice modes |
| Teacher | Teachers | Class/group tools, topic packs, reporting |
| Channel | Telegram channel owners | Scheduled quiz delivery |
| School | Institutions | Multiple groups, dashboards, management |
| API Pro | Developers/partners | API quota, documentation, support |

### 19.4. Payment-provider neutrality

System не має hard-code business logic в один payment provider.

Внутрішня модель має трекати:

```text
customer
subscription
plan
entitlement
quota
usage
valid_until
provider
external_customer_id
external_subscription_id
```

Payment provider може змінюватися. Entitlement logic має залишатися internal.

---

## 20. Analytics Vision

### 20.1. Навіщо analytics

Analytics перетворює platform з content library на learning and business system.

Система має знати:

- які items delivered;
- які items answered correctly;
- які topics hardest;
- які levels used most;
- які consumers active;
- де delivery fails;
- які items reported;
- які quotas consumed;
- які paid plans create value;
- які content areas need expansion.

### 20.2. Core analytics categories

```text
Corpus analytics
  count by level, theme, objective, pattern, status.

Delivery analytics
  delivered items by consumer, time, channel, success/failure.

Attempt analytics
  correctness, response time, repeated errors, user progress.

Quality analytics
  reports, duplicate flags, low-performing items, metadata gaps.

Business analytics
  plan usage, quota consumption, conversion, retention.

Operational analytics
  API health, latency, error rate, import results, worker status.
```

### 20.3. North Star Metric

Сильна North Star Metric:

```text
governed quiz deliveries per week without policy violations
```

Ця метрика поєднує scale and discipline. Недостатньо просто видати багато quizzes. Вони мають видаватися через governed system.

---

## 21. Security and Trust Vision

### 21.1. Trust model

Users, teachers, channel owners, schools and API clients повинні довіряти, що:

- content access controlled;
- private data not exposed unnecessarily;
- API keys protected;
- users cannot access another consumer’s data;
- paid limits enforced;
- admin actions logged;
- delivery and attempt histories accurate;
- source data traceable.

### 21.2. Security priorities

Платформа має пріоритезувати:

- authentication;
- authorization;
- object-level access control;
- object-property access control;
- API key hashing;
- rate limiting;
- quota enforcement;
- secure billing webhooks;
- least-privilege admin roles;
- audit logs;
- monitoring;
- backup and recovery.

### 21.3. Data exposure principle

API має expose only what the consumer needs.

```text
Learner-facing response:
  question, options, allowed metadata.

Admin-facing response:
  source, status, review flags, import metadata.

Analytics response:
  aggregated metrics unless permission allows detail.
```

---

## 22. Operational Vision

### 22.1. Operations as product quality

Платформу треба operate, not merely build.

Operational quality включає:

- repeatable imports;
- migration discipline;
- CI checks;
- validation reports;
- monitoring;
- logs;
- backup;
- incident response;
- changelog;
- rollback path;
- documentation updates.

### 22.2. Launch discipline

Production delivery не має стартувати, поки система не доведе:

```text
source files are inventoried
manifest exists
canonical schema exists
production database exists
API contract exists
selection engine respects statuses
Telegram/API consumers cannot read raw CSV directly
approved/published status gates are enforced
delivery logs are written
basic monitoring exists
```

### 22.3. Production readiness gates

Production release має проходити gates у сферах:

```text
data
schema
API
security
consumer rules
billing/entitlements
Telegram compatibility
analytics
operations
documentation
```

---

## 23. Competitive Differentiation

### 23.1. Не просто ще один quiz API

Багато quiz APIs дають generic random questions, categories and CRUD operations. API Quiz Bank має іншу глибину: educational + operational + monetizable platform.

Differentiators:

- German-language focus;
- CEFR alignment;
- topic/objective/pattern coverage;
- governed source traceability;
- canonical data model;
- centralized selection engine;
- anti-repeat delivery;
- Telegram delivery support;
- paid entitlements;
- analytics feedback loop;
- Stanford-style documentation and traceability.

### 23.2. Не просто question bank

Question bank stores questions. API Quiz Bank operates them.

```text
Question bank:
  “Here are questions.”

API Quiz Bank:
  “Here is a governed system that can safely deliver the right question to the right consumer under the right rules and measure what happens.”
```

### 23.3. Не просто Telegram bot

Telegram bot — це delivery channel. Core product — API and content platform.

```text
Telegram is a consumer.
The API is the contract.
The selection engine is the intelligence.
The database is the production truth.
The corpus is the asset.
```

---

## 24. MVP Vision

### 24.1. MVP goal

Перший MVP має довести, що verified quiz content можна govern, import, store, select, deliver through API and post to a controlled Telegram consumer.

### 24.2. MVP scope

MVP має включати:

```text
1. Constitution adopted.
2. Vision document adopted.
3. File inventory created.
4. Source onboarding workflow for future quiz files defined.
5. Import manifest created.
6. Canonical quiz item schema created.
7. Taxonomy baseline created.
8. Pilot import implemented.
9. PostgreSQL schema created.
10. Selection engine MVP created.
11. OpenAPI contract created.
12. GET /v1/quiz-items/next implemented.
13. POST /v1/attempts implemented.
14. Delivery logging implemented.
15. Admin review/status workflow MVP implemented.
16. Telegram worker demo implemented.
17. Basic analytics implemented.
18. Launch gates documented.
```

### 24.3. MVP non-goals

MVP не має намагатися вирішити все одразу.

Non-goals:

- full adaptive learning;
- complete polished public website;
- full school dashboard;
- all payment providers;
- AI content generation;
- full LMS marketplace integration;
- re-auditing every quiz item;
- redesigning the entire corpus before import rules exist.

### 24.4. MVP success statement

MVP успішний, якщо reviewer може побачити:

```text
A source file produced canonical items.
A future-source onboarding path is defined for adding new quiz files.
Canonical items entered the database.
Only allowed statuses can be selected.
An API consumer requested a quiz.
The selection engine returned a suitable item.
Telegram received a quiz through controlled delivery.
The delivery was logged.
An attempt was recorded.
Analytics reflected the event.
The system can explain source, status, and access rules.
```

---

## 25. Stanford-Ready Vision

### 25.1. Що означає Stanford-ready

Stanford-ready не означає дорогий UI. Це означає, що проєкт витримує серйозні technical questions.

Reviewer має мати можливість запитати:

```text
What is the problem?
What is the asset?
What is the architecture?
What is the source of truth?
How do you validate data?
How do you add new source files without breaking the platform?
How do you prevent wrong delivery?
How do you expose the product through API?
How do you secure paid access?
How do you measure quality?
How do you scale?
What is the roadmap?
What are the risks?
What evidence proves this is real?
```

І проєкт має мати чіткі відповіді.

### 25.2. Stanford-ready artifacts

Presentation package має включати:

```text
1. Vision document.
2. Constitution.
3. Product charter.
4. SRS with requirement IDs.
5. Use cases.
6. Domain model.
7. Architecture diagram.
8. Data standard.
9. Source onboarding / import playbook.
10. API standard / OpenAPI contract.
11. Security threat model.
12. Operations plan.
13. Billing model.
14. Analytics model.
15. Demo script.
16. Roadmap.
17. Risk register.
```

### 25.3. Stanford-ready narrative

```text
Problem:
  German quiz content is fragmented and hard to deliver consistently.

Asset:
  API Quiz Bank starts from a verified corpus with thousands of level-aware items.

Insight:
  Content becomes valuable at scale only when governed and served through a contract.

Solution:
  A governed API-first quiz platform with canonical data, selection engine, Telegram delivery,
  analytics, and monetized access.

Proof:
  Import pipeline, database, API endpoint, delivery log, Telegram demo, analytics dashboard.

Scale:
  Additional consumers, school accounts, teacher workflows, paid API access, future adaptive learning.
```

### 25.4. Evidence-based presentation

Кожен сильний presentation claim має бути привʼязаний до evidence:

| Claim | Evidence |
|---|---|
| Corpus exists | Inventory report and active item count |
| Data is governed | Manifest, checksums, source IDs |
| Items are structured | Canonical schema and sample JSONL |
| Delivery is controlled | Selection engine and status gates |
| API is real | OpenAPI spec and working endpoint |
| Telegram works | Demo channel and delivery logs |
| Monetization is designed | Entitlements model |
| Quality is measurable | Analytics dashboard |
| Operations are credible | CI, backups, monitoring, incident plan |

---

## 26. Success Metrics

### 26.1. Corpus metrics

```text
active source files inventoried
source files with checksums
source files mapped to parser
items imported into canonical format
items with source traceability
items by status
items by CEFR level
items by theme/objective/pattern
metadata completeness
schema validation pass rate
```

### 26.2. API metrics

```text
API uptime
request latency
error rate
quota violations blocked
successful quiz item responses
OpenAPI contract coverage
contract test pass rate
consumer integration count
```

### 26.3. Delivery metrics

```text
quiz deliveries per day/week
successful Telegram posts
delivery failures
repeat policy violations
time-to-deliver
consumer-level delivery volume
```

### 26.4. Learning metrics

```text
attempts recorded
correctness rate by level/topic/item
response time
reported items
hardest topics
learner retention
practice streaks
```

### 26.5. Business metrics

```text
active consumers
free-to-paid conversion
API clients
paid plans
quota consumption
subscription retention
school/teacher accounts
revenue by plan
```

### 26.6. Operations metrics

```text
import success rate
CI pass rate
schema violations
incident count
recovery time
backup success
security alerts resolved
changelog completeness
```

---

## 27. Vision Objectives

Майбутні requirements повинні trace back до цих vision objectives.

### VOBJ-001 — Governed Corpus

Платформа повинна перетворити existing quiz corpus з files у governed source system with inventory, manifest, checksums, source IDs and traceability.

### VOBJ-002 — Canonical Data Model

Платформа повинна представляти всі quiz items через one canonical schema suitable for validation, database storage, API delivery, Telegram compatibility and analytics.

### VOBJ-003 — API-First Delivery

Платформа повинна expose quiz functionality through a versioned API contract rather than direct raw file access.

### VOBJ-004 — CEFR-Aware Learning

Платформа повинна preserve CEFR levels and support level-aware quiz delivery.

### VOBJ-005 — Topic/Objective/Pattern Coverage

Платформа повинна support content selection and analytics through theme, objective and pattern dimensions.

### VOBJ-006 — Centralized Selection

Платформа повинна choose items through a centralized selection engine that respects status, rules, history and quotas.

### VOBJ-007 — Multi-Consumer Support

Платформа повинна serve multiple consumer types from the same core: Telegram, bots, web, admin, schools, apps and external API clients.

### VOBJ-008 — Delivery Traceability

Платформа повинна log deliveries and attempts to support anti-repeat rules, analytics and quality feedback.

### VOBJ-009 — Monetized Access Control

Платформа повинна support plans, quotas and entitlements.

### VOBJ-010 — Operational Trust

Платформа повинна include security, monitoring, backup, CI, changelog and release discipline.

### VOBJ-011 — Presentation Readiness

Платформа повинна бути explainable through professional artifacts, diagrams, demos, metrics and traceable decisions.

### VOBJ-012 — Future Source Expansion

Платформа повинна підтримувати контрольоване додавання нових quiz-файлів через source onboarding pipeline, stable source IDs, checksums, parser profiles, dry-run imports, validation, import batches and status workflow.

---

## 28. Future Requirements Seed Matrix

Це не SRS. Це seed matrix для SRS.

| Vision objective | Future SRS area | Example requirement direction |
|---|---|---|
| VOBJ-001 | Data/source governance | Every active source file must have a stable source ID and checksum. |
| VOBJ-002 | Canonical schema | Every production quiz item must validate against canonical schema. |
| VOBJ-003 | API | All external consumers must request quiz items through `/v1` API. |
| VOBJ-004 | Education | Every approved item must have a CEFR level. |
| VOBJ-005 | Taxonomy | Every approved item must have theme/objective/pattern metadata. |
| VOBJ-006 | Selection | Selection engine must exclude non-publishable statuses. |
| VOBJ-007 | Consumers | Telegram, web and API clients must use the same selection rules. |
| VOBJ-008 | Analytics | Every delivered item must create a delivery record. |
| VOBJ-009 | Billing | Access must be governed by entitlements and quotas. |
| VOBJ-010 | Security/Ops | Admin actions and API access must be logged. |
| VOBJ-011 | Presentation | Demo must show corpus, API, selection, delivery, analytics and roadmap. |
| VOBJ-012 | Source expansion | Every new quiz file must pass source onboarding before import or delivery. |

---

## 29. Roadmap Vision

### Phase 0 — Governance foundation

```text
CONSTITUTION.md
00_vision.md
01_product_charter.md
02_requirements_srs.md
03_use_cases.md
repository structure
working documentation discipline
```

Purpose: зробити проєкт governable до хаотичного production coding.

### Phase 1 — Corpus inventory and taxonomy

```text
file_inventory.csv
import_manifest.yml
source onboarding workflow
source states
source IDs
checksums
topics.yml
levels.yml
objectives.yml
patterns.yml
coverage report
```

Purpose: точно знати, що існує і як це mapping to platform.

### Phase 2 — Canonical data and import pipeline

```text
quiz_item.schema.json
parser definitions
normalization rules
canonical JSONL sample
validation reports
import batch records
new file dry-run import
re-import/versioning rules
```

Purpose: перетворити raw files у structured platform data and make future quiz-file expansion safe.

### Phase 3 — Database and API MVP

```text
PostgreSQL schema
migrations
seed taxonomy
basic indexes
OpenAPI contract
GET /v1/quiz-items/next
POST /v1/attempts
health endpoint
contract tests
```

Purpose: довести API-first model.

### Phase 4 — Admin and Telegram MVP

```text
admin review/status interface
consumer rules
Telegram worker
scheduled quiz delivery
delivery logs
anti-repeat policy
```

Purpose: довести controlled multi-channel delivery.

### Phase 5 — Analytics and entitlements

```text
usage analytics
item analytics
consumer analytics
plans
quotas
entitlements
billing integration path
```

Purpose: довести learning value and business control.

### Phase 6 — Stanford-ready demo package

```text
architecture diagram
API demo
Telegram demo
analytics demo
security model
operations plan
roadmap
presentation deck
```

Purpose: презентувати проєкт як serious educational technology platform.

---

## 30. Risks and Mitigations

### Risk 1 — Treating files as the product

**Risk:** Проєкт залишається CSV archive.  
**Mitigation:** Enforce source governance, canonical schema, database import and API-only delivery.

### Risk 2 — Building UI before core

**Risk:** Public site or bot будується до data contracts.  
**Mitigation:** Prioritize inventory, schema, import, database, selection engine and API.

### Risk 3 — Duplicate selection logic

**Risk:** Telegram, website and API each choose items differently.  
**Mitigation:** Centralize selection engine.

### Risk 4 — No delivery memory

**Risk:** Users/channels receive repeated items unpredictably.  
**Mitigation:** Mandatory delivery logs and repeat policy.

### Risk 5 — Monetization chaos

**Risk:** Payment status handled manually or inconsistently.  
**Mitigation:** Build entitlements and quotas as core model.

### Risk 6 — Metadata gaps

**Risk:** Items cannot be selected reliably by level/topic/objective/pattern.  
**Mitigation:** Use coverage matrix and review workflow.

### Risk 7 — Overengineering too early

**Risk:** Проєкт намагається реалізувати adaptive AI, LMS integrations and full analytics before MVP.  
**Mitigation:** MVP focuses on governed import → database → API → selection → Telegram demo → analytics basics.

### Risk 8 — Presentation without system evidence

**Risk:** Stanford-style presentation стає claims without proof.  
**Mitigation:** Tie every major claim to artifact, metric, demo or traceable document.

### Risk 9 — Future source expansion becomes uncontrolled

**Risk:** У майбутньому нові quiz-файли додаються напряму в raw folder, обминають inventory, manifest, parser profiles, validation and status workflow. Це створює duplicate content, schema drift, unclear source truth and production risk.  
**Mitigation:** Treat every new file as a source candidate and require source onboarding gates before import, approval or delivery.

---

## 31. Non-Negotiable Decisions

Ці рішення locked by this vision unless the Constitution is amended.

```text
1. The project name is API Quiz Bank for strategic/public use.
2. The project is API-first.
3. Raw CSV files are not the production product.
4. A canonical quiz item model is required.
5. Production consumers must not read raw files directly.
6. Selection must be centralized.
7. Delivery history is mandatory.
8. CEFR levels remain canonical learning levels.
9. Entitlements, not vague payment state, control access.
10. Stanford-ready means system-ready, not slide-ready only.
11. New quiz files must enter through source onboarding, not by direct production use.
```

---

## 32. Open Questions

Ці питання будуть вирішені в наступних документах і не блокують adoption of this vision.

```text
1. What exact public domain/brand will be used?
2. Which payment provider will be integrated first?
3. Which backend framework will be selected?
4. Which database hosting approach will be used first?
5. Which admin UI framework will be used?
6. Which Telegram bot framework will be used?
7. Which subset of items will be imported in the first pilot?
8. Which pricing model will be tested first?
9. Which school/teacher workflows will be prioritized?
10. Which analytics dashboard will be implemented first?
11. Which file formats will be accepted as first-class import sources?
12. Which new-source approval policy will be used: manual review, automated gates, or hybrid?
```

Це implementation choices. Strategic direction remains stable.

---

## 33. Presentation Narrative

### 33.1. One-minute version

```text
API Quiz Bank turns a verified German quiz corpus into a governed educational API platform.
Instead of building one site or one Telegram bot, we build a central content core with source governance,
canonical quiz items, CEFR-aware taxonomy, selection logic, API delivery, analytics and monetized access.
Telegram, web, bots, schools and external apps become consumers of the same reliable system.
New quiz files can be added through controlled source onboarding instead of ad hoc file drops.
```

Українською:

```text
API Quiz Bank перетворює перевірений корпус німецьких вікторин на керовану освітню API-платформу.
Ми не будуємо окремо сайт або Telegram-бот. Ми будуємо центральне ядро контенту:
source governance, canonical items, CEFR taxonomy, selection engine, API delivery, analytics and monetization.
Усі канали — Telegram, web, bots, schools, external apps — стають consumers однієї системи.
Нові файли з вікторинами додаються через керований source onboarding, а не через хаотичне копіювання в папку.
```

### 33.2. Five-slide narrative

```text
Slide 1 — Problem
German quiz content is fragmented, manually managed and difficult to scale across channels.

Slide 2 — Asset
API Quiz Bank starts with a significant verified corpus across CEFR levels, themes, objectives and patterns.

Slide 3 — Insight
Content becomes a product only when it is governed, normalized, served through an API, measured and controlled.

Slide 4 — Solution
A governed API-first platform: source files → canonical data → database → selection engine → API → consumers.

Slide 5 — Proof and Roadmap
Inventory, schema, API endpoint, Telegram demo, delivery logs, analytics, entitlements and scale roadmap.
```

### 33.3. Technical demo narrative

```text
1. Show corpus inventory.
2. Show source file with source_id and checksum.
3. Show how a future new file would enter source onboarding.
4. Show canonical item schema.
5. Show imported database record.
6. Call GET /v1/quiz-items/next.
7. Show selection rules and no-repeat policy.
8. Post quiz to Telegram through worker.
9. Record delivery.
10. Submit attempt.
11. Show analytics update.
```

---

## 34. Acceptance Criteria for This Vision

Vision accepted, якщо:

```text
1. The project name API Quiz Bank is adopted in strategic documents.
2. API-first direction is agreed.
3. The product is understood as a platform, not a CSV folder.
4. The current corpus baseline is treated as an asset requiring operational workflow.
5. The next documents are clear: Product Charter, SRS, Use Cases, Domain Model, Architecture, Data Standard, API Standard.
6. MVP scope is clear.
7. Stanford-ready meaning is clear.
8. Future requirements can trace back to vision objectives.
9. Future quiz-file expansion is explicitly governed through source onboarding.
```

---

## 35. Reference Standards and Alignment

API Quiz Bank має align with:

- Stanford/SLAC-style requirements methodology: goal, features, requirements, use cases, traceability, test/QA, change control;
- CEFR A1–C2 for language levels;
- OpenAPI Specification for API contract;
- JSON Schema 2020-12 for canonical data validation;
- RFC 9110 for HTTP semantics;
- RFC 9457 for Problem Details in HTTP APIs;
- OWASP API Security Top 10 for API security risk awareness;
- Telegram Bot API for quiz/poll delivery compatibility.

Reference URLs повинні підтримуватися в наступних документах, особливо:

```text
06_data_standard.md
source_onboarding/import_playbook section in 06_data_standard.md or 10_operations.md
07_api_standard.md
08_security_threat_model.md
10_operations.md
```

---

## 36. Closing Statement

API Quiz Bank має стати системою, яка робить quiz corpus usable at scale.

Vision не в тому, щоб “мати багато питань”. Vision у тому, щоб operate a trusted educational content platform.

Фінальна стратегічна формула:

```text
Corpus is the asset.
Governance is the discipline.
Canonical data is the structure.
Selection is the intelligence.
API is the product surface.
Consumers are the channels.
Analytics is the feedback loop.
Entitlements are the business control.
Operations are the trust layer.
```

Якщо це бачення виконувати послідовно, API Quiz Bank може вирости з перевіреного корпусу німецьких вікторин у професійну, масштабовану, Stanford-ready educational technology platform.
