# API Quiz Bank — API Standard

**Документ:** `docs/07_api_standard.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational API contract standard; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`, `01_product_charter.md`, `02_requirements_srs.md`, `03_use_cases.md`, `04_domain_model.md`, `05_architecture.md`, `06_data_standard.md`  
**Дата:** 2026-04-30  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized product maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/06_data_standard.md`  
**Наступні документи:** `08_security_threat_model.md`, `09_quality_assurance.md`, `10_operations.md`, `11_billing_model.md`, `12_analytics_model.md`, `13_stanford_presentation_outline.md`  
**Майбутній машинний контракт:** `api/openapi.yaml` або `services/api/openapi.yaml`

---

## 0. Executive Summary

`07_api_standard.md` визначає API contract discipline для **API Quiz Bank**.

API Quiz Bank не повинен бути просто набором endpointів. API є **product surface** — головним контрактом між governed quiz corpus і всіма consumers:

```text
source files
  → source onboarding
  → import manifest
  → canonical quiz items
  → production database
  → selection engine
  → versioned API
  → Telegram / web / bots / apps / schools / external clients
  → delivery logs / attempts / analytics / entitlements / operations
```

Головна API-теза:

```text
The API is not a convenient wrapper around files.
The API is the governed delivery contract of the product.
```

API Standard фіксує:

```text
API-first rule;
OpenAPI contract rule;
versioning policy;
endpoint groups;
authentication and authorization model;
consumer context;
entitlement and quota enforcement;
selection and delivery endpoint semantics;
public-safe projections;
correct-answer exposure policy;
Problem Details error model;
reason codes;
idempotency;
pagination, filtering and sorting;
webhooks;
admin/source onboarding endpoints;
analytics endpoints;
Telegram worker/API relationship;
API contract tests;
launch gates;
Stanford-style demo path.
```

Поточний operational baseline, який API має підтримати:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Цей baseline є стартовим активом, а не обмеженням. API Standard також підтримує правило:

```text
New quiz files are onboarded, not dropped.
```

Тобто API не повинен відкривати хаотичний шлях “upload file → public delivery”. Нові source files мають проходити source registry, checksum, manifest, parser assignment, dry-run import, validation, duplicate/conflict handling, import batch, status workflow і тільки потім approved/published items можуть бути delivered через API.

---

## 1. Role of This Document

### 1.1. Purpose

`07_api_standard.md` визначає, як API Quiz Bank має проектувати, документувати, тестувати, запускати й змінювати HTTP API.

Документ відповідає на питання:

```text
Які API принципи є обовʼязковими?
Яка версія OpenAPI є contract baseline?
Які endpoint groups потрібні для MVP/Pilot/Production?
Які endpoint-и створюють delivery records?
Як API захищає correct answers?
Як API блокує draft/blocked items?
Як API застосовує entitlement/quota rules?
Як API відрізняє learner/public/admin/Telegram/internal projections?
Як API повертає machine-readable errors?
Як API має поводитися при no eligible item, quota exceeded, auth failure, validation failure?
Як API підтримує source onboarding для майбутніх файлів?
Як API буде демонструватися у Stanford-style review?
```

### 1.2. Place in documentation hierarchy

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
api/openapi.yaml + services/api + contract tests + implementation
```

If implementation conflicts with this API Standard, implementation must be fixed or the standard must be changed through change control.

If this API Standard conflicts with the Constitution, the Constitution wins.

### 1.3. What this document does

This document:

- defines API design rules;
- chooses API versioning approach;
- chooses OpenAPI baseline;
- defines route groups;
- defines request/response patterns;
- defines public-safe projections;
- defines authentication and authorization expectations;
- defines entitlement/quota enforcement expectations;
- defines error model and reason codes;
- defines idempotency and reservation expectations;
- defines API launch gates;
- defines contract test expectations;
- provides a seed OpenAPI structure.

### 1.4. What this document does not do

This document does not:

- implement the API;
- replace `06_data_standard.md`;
- replace database migrations;
- replace full security threat model;
- replace billing provider integration guide;
- define final pricing;
- define all UI screens;
- repeat audit of quiz content;
- allow consumers to access raw CSV files;
- allow draft items to be publicly delivered.

---

## 2. Stanford-Style API Discipline

For this project, **Stanford-style** does not mean formal Stanford approval. It means professional engineering discipline:

```text
vision
  → requirements
  → use cases
  → domain model
  → data standard
  → API contract
  → implementation
  → tests
  → operations
  → demo evidence
```

An API decision is acceptable only if it is:

| Attribute | Meaning |
|---|---|
| Traceable | Linked to SRS, use case, domain model or data standard. |
| Testable | Can be verified by contract test, integration test, security test or demo. |
| Consumer-safe | Does not expose internal data by accident. |
| Status-aware | Does not deliver non-production items. |
| Entitlement-aware | Does not bypass paid/limited access rules. |
| Version-aware | Can evolve without breaking consumers unexpectedly. |
| Demo-ready | Can be explained and shown through evidence. |

Core API discipline:

```text
No serious external access without OpenAPI.
No production delivery without status filtering.
No monetized access without entitlements.
No consumer-specific data without object-level authorization.
No correct-answer leakage outside allowed modes.
No direct raw CSV access.
No API claim without test or demo evidence.
```

---

## 3. Normative Language

This document uses:

- **MUST / SHALL / ОБОВʼЯЗКОВО** — binding requirement.
- **MUST NOT / ЗАБОРОНЕНО** — prohibited behavior.
- **SHOULD / РЕКОМЕНДОВАНО** — default required unless justified.
- **MAY / ДОЗВОЛЕНО** — allowed option.
- **MVP** — required for first serious API demo or controlled pilot unless explicitly deferred.
- **Pilot** — required before real limited consumers.
- **Production** — required before public/paid/broad access.

---

## 4. API Product Thesis

### 4.1. API as product surface

API Quiz Bank is API-first. Therefore:

```text
API is the product surface.
Database is the operational truth.
Canonical data is the structure.
Selection engine is the intelligence.
Entitlements are the access control.
Analytics is the feedback loop.
```

External clients must understand the product through API contract, not through source code, database tables or raw file access.

### 4.2. API value chain

```text
consumer request
  → authentication
  → object-level authorization
  → consumer context
  → entitlement/quota check
  → request validation
  → selection or domain operation
  → public-safe projection
  → delivery/attempt/audit log
  → response
```

### 4.3. Non-negotiable API rules

```text
1. All external consumers use versioned API.
2. API must not serve raw CSV files as product content.
3. API must not deliver draft/imported/normalized/needs_review/retired/blocked items to normal consumers.
4. API must not expose internal database IDs to normal consumers.
5. API must not expose raw source paths to normal consumers.
6. API must not expose correct answers before allowed interaction mode.
7. API must verify consumer authorization for consumer-scoped operations.
8. API must enforce entitlement and quota rules before protected delivery.
9. API must use machine-readable errors.
10. API contract must be represented in OpenAPI before external access.
```

---

## 5. Standards Baseline

### 5.1. Chosen API contract standard

The API contract SHALL be described using:

```text
OpenAPI Specification 3.2.0
```

Rationale:

```text
OpenAPI is the external API contract language.
OpenAPI lets humans and machines understand API capabilities without reading source code.
OpenAPI 3.2.0 is the current target for this document.
```

Implementation note:

```text
If production tooling cannot yet fully support OpenAPI 3.2.0,
the implementation MAY temporarily generate OpenAPI 3.1.x for tooling compatibility,
but docs/07_api_standard.md remains the strategic target and must record the waiver.
```

### 5.2. JSON Schema alignment

Canonical data validation remains aligned with:

```text
JSON Schema Draft 2020-12
```

OpenAPI schemas should reuse or mirror canonical JSON Schema concepts from `06_data_standard.md`, while exposing **API projections**, not internal database tables.

### 5.3. HTTP semantics

HTTP behavior SHALL align with:

```text
RFC 9110 HTTP Semantics
```

Important implication:

```text
GET should be read-only.
Delivery-producing selection should use POST.
```

This document resolves an important route ambiguity from earlier planning documents:

```text
Earlier docs mention GET /v1/quiz-items/next as the next-quiz demo endpoint.
For production-grade semantics, any request that creates delivery/reservation/usage state SHOULD be POST.
GET /v1/quiz-items/next MAY exist only as read-only preview or backwards-compatible demo shorthand.
POST /v1/quiz-items/next is the normative delivery-producing endpoint.
```

### 5.4. Error standard

Errors SHALL use RFC 9457-style Problem Details:

```text
application/problem+json
```

Every client-relevant error should include a stable `reason_code` extension.

### 5.5. Security baseline

API security SHALL align with OWASP API Security risk model, especially:

```text
object-level authorization;
object-property authorization;
broken authentication prevention;
unrestricted resource consumption prevention;
input validation;
logging and abuse detection;
safe consumption of third-party APIs and webhooks.
```

### 5.6. Telegram compatibility

Telegram worker and Telegram-facing projections SHALL respect Telegram Bot API poll/quiz constraints.

Telegram compatibility belongs in validation/projection logic, not in raw source files.

---

## 6. API Boundary

### 6.1. API exposes product operations

The API SHOULD expose:

```text
quiz delivery;
attempt submission;
consumer management;
consumer rules;
entitlements and quota views;
source onboarding/admin operations;
import dry-run/commit operations;
review/status operations;
analytics/report operations;
health/readiness operations;
webhook receivers;
Telegram/internal worker support where needed.
```

### 6.2. API must not expose raw internals

Normal API consumers MUST NOT receive:

```text
raw CSV contents;
raw source file paths;
source checksums;
admin notes;
audit logs;
internal database IDs;
other consumersʼ data;
import internals;
unpublished status history;
correct answer keys before allowed mode.
```

### 6.3. API projection principle

```text
API response = authorized projection of canonical/domain data.
API response ≠ raw database table.
API response ≠ raw canonical item.
API response ≠ raw file row.
```

---

## 7. API Environments

The API contract SHOULD define these environments:

| Environment | Purpose | External users? | Notes |
|---|---|---:|---|
| `local` | Local development | No | Sample data only. |
| `dev` | Internal development | No | May reset data. |
| `staging` | Pre-production integration | Limited | Mirrors production rules. |
| `demo` | Stanford-style demo | Controlled | Deterministic demo consumer allowed. |
| `pilot` | Closed pilot | Selected | Real consumers with strict monitoring. |
| `production` | Public/paid service | Yes | Requires full gates. |

Example OpenAPI server entries:

```yaml
servers:
  - url: https://api-staging.example.com/v1
    description: Staging API
  - url: https://api-demo.example.com/v1
    description: Controlled demo API
  - url: https://api.example.com/v1
    description: Production API
```

Real URLs are implementation-specific and should not be invented in production docs until decided.

---

## 8. API Versioning Policy

### 8.1. URI versioning

MVP namespace:

```text
/v1
```

Examples:

```text
POST /v1/quiz-items/next
POST /v1/attempts
GET  /v1/themes
GET  /v1/admin/sources
```

### 8.2. Breaking changes

Breaking changes include:

```text
removing endpoint;
renaming required field;
changing field type;
changing auth requirement in a way that breaks existing clients;
changing response semantics;
removing reason_code;
changing correct-answer exposure behavior;
changing delivery logging semantics;
changing pagination contract;
changing status eligibility contract.
```

Breaking changes require:

```text
new version such as /v2 OR explicit migration plan;
changelog;
OpenAPI update;
contract test update;
consumer notice when relevant;
SRS/API standard update if policy changes.
```

### 8.3. Non-breaking changes

Allowed within same version:

```text
adding optional response fields;
adding new optional query parameters;
adding new endpoint;
adding new enum values only if clients are warned to tolerate unknowns;
adding new reason_code only if documented;
adding new projection mode where unauthorized clients are unaffected.
```

### 8.4. Deprecation policy

Deprecation MUST include:

```text
Deprecated header when feasible;
OpenAPI deprecated flag;
changelog entry;
replacement endpoint;
minimum migration window for external consumers;
removal date or policy.
```

Recommended response header:

```http
Deprecation: true
Sunset: 2027-01-31T00:00:00Z
Link: <https://docs.example.com/changelog>; rel="deprecation"
```

---

## 9. URI, Naming and Field Conventions

### 9.1. URI rules

Use plural resource names:

```text
/v1/quiz-items
/v1/attempts
/v1/consumers
/v1/deliveries
/v1/admin/sources
```

Use hyphenated path segments:

```text
quiz-items
consumer-rules
import-batches
issue-reports
```

Avoid verbs when resource modeling is clear. Use action endpoints only for domain transitions where resource semantics would be less clear.

Acceptable action endpoints:

```text
POST /v1/admin/sources/{source_id}/assign-parser
POST /v1/admin/imports/{import_batch_id}/commit
POST /v1/admin/quiz-items/{quiz_item_id}/approve
POST /v1/admin/quiz-items/{quiz_item_id}/publish
POST /v1/admin/quiz-items/{quiz_item_id}/retire
POST /v1/admin/quiz-items/{quiz_item_id}/block
```

### 9.2. JSON field naming

API JSON fields SHALL use `snake_case` to align with project data standards:

```json
{
  "quiz_item_id": "qi_01J...",
  "cefr_level": "A2",
  "theme_id": "T09",
  "delivery_id": "deliv_01J..."
}
```

### 9.3. Public IDs

API responses SHOULD use public IDs:

```text
qi_       quiz item
qiv_      quiz item version
qopt_     quiz option
cons_     consumer
deliv_    delivery
att_      attempt
src_      source file, admin only by default
ib_       import batch, admin only by default
```

Internal database IDs MUST NOT be exposed to normal consumers.

### 9.4. Timestamps

Use ISO 8601 / RFC 3339-compatible UTC timestamps:

```json
{
  "created_at": "2026-04-30T18:00:00Z"
}
```

### 9.5. Null and missing fields

Rules:

```text
Required fields must be present.
Unavailable optional fields may be omitted.
Known-empty optional fields may be null if meaningful.
Do not use empty string to mean null.
Do not use magic values such as "unknown" unless explicitly part of enum.
```

---

## 10. HTTP Method Semantics

### 10.1. Method rules

| Method | Use | State change? |
|---|---|---:|
| `GET` | Read resource or preview | No |
| `POST` | Create resource, submit command, perform selection/delivery | Yes or possible |
| `PATCH` | Partial update | Yes |
| `PUT` | Replace resource where appropriate | Yes |
| `DELETE` | Rare; prefer status transitions for domain records | Yes |

### 10.2. Delivery-producing next quiz

Because delivery-producing selection may create delivery/reservation/quota records, the normative endpoint is:

```http
POST /v1/quiz-items/next
```

Earlier shorthand:

```http
GET /v1/quiz-items/next
```

MAY be implemented only as:

```text
read-only preview;
internal deterministic demo route;
or compatibility alias explicitly documented as non-safe.
```

Recommended production path:

```text
client calls POST /v1/quiz-items/next
API authenticates/authorizes
API checks entitlements/quota
selection engine selects eligible item
system creates delivery/reservation
API returns QuizItemDeliveryView with delivery_id
```

---

## 11. Media Types and Encoding

### 11.1. JSON

Requests and responses SHOULD use:

```http
Content-Type: application/json; charset=utf-8
Accept: application/json
```

### 11.2. Errors

Problem Details responses SHOULD use:

```http
Content-Type: application/problem+json
```

### 11.3. CSV and exports

Public delivery endpoints MUST NOT expose raw CSV.

Admin/report endpoints MAY expose generated CSV only for reports, not as source-of-truth content:

```text
text/csv; charset=utf-8
```

### 11.4. OpenAPI

OpenAPI contract may be served as:

```text
application/vnd.oai.openapi+json
application/vnd.oai.openapi+yaml
application/json
application/yaml
```

Recommended endpoints:

```text
GET /v1/openapi.json
GET /v1/openapi.yaml
```

These may be disabled or access-controlled in production if security policy requires, but external API consumers need documented access to the contract.

---

## 12. Request and Response Design

### 12.1. Response envelope policy

API Quiz Bank SHOULD avoid unnecessary universal wrappers for simple resources.

For single resource responses:

```json
{
  "quiz_item_id": "qi_01J...",
  "stem": {"de": "Welche Antwort ist richtig?"}
}
```

For operations that create traceable events, include operation/event IDs:

```json
{
  "delivery_id": "deliv_01J...",
  "quiz_item": {...},
  "selection": {
    "mode": "standard",
    "repeat_policy_applied": true
  }
}
```

For lists, use standard pagination object:

```json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "next_cursor": "eyJ...",
    "has_more": true
  }
}
```

### 12.2. Request metadata

Client MAY provide:

```http
X-Request-Id: req_client_generated
Idempotency-Key: unique-key-for-retry-sensitive-post
```

Server SHOULD return:

```http
X-Request-Id: req_server_or_client_id
```

### 12.3. Safe response rule

API response MUST be shaped by:

```text
caller identity;
consumer identity;
endpoint purpose;
projection mode;
entitlement;
correct-answer exposure policy;
privacy policy;
admin/security permissions.
```

---

## 13. Authentication Model

### 13.1. Authentication types

MVP may support multiple authentication types:

| Context | Authentication | MVP priority |
|---|---|---:|
| External API client | API key / bearer token | P0 |
| Telegram worker | Internal service token | P0/P1 |
| Admin | Session/JWT or admin bearer token | P0 |
| Billing webhook | Provider signature validation | P1 |
| Public metadata | Optional no-auth for selected endpoints | P1 |

### 13.2. Authorization header

Preferred header:

```http
Authorization: Bearer <token>
```

API keys may be implemented as bearer credentials while internally stored hashed/sealed.

### 13.3. API key safety

API keys/tokens MUST:

```text
not be committed to repository;
not be logged in plaintext;
not be shown after creation except once if using key style;
be revocable;
have owner/consumer scope;
have created_at/last_used_at metadata;
be stored hashed or protected;
support rotation.
```

### 13.4. Admin authentication

Admin endpoints MUST require authenticated admin identity.

Admin credentials MUST NOT be reused as public API client credentials.

### 13.5. Demo authentication

Demo credentials MUST be clearly marked:

```text
internal_demo_client
limited scope
demo environment only
safe quota
no production secrets shown
```

---

## 14. Authorization Model

### 14.1. Object-level authorization

Every endpoint that accepts an object ID MUST verify that the caller has permission to access that object.

Examples:

```text
consumer_id
quiz_item_id
delivery_id
attempt_id
source_id
import_batch_id
entitlement_id
report_id
```

Required check:

```text
caller identity
  → role/scope
  → requested object
  → relationship to consumer/tenant/project
  → operation
  → entitlement/quota if needed
```

### 14.2. Object-property authorization

Even when caller may access an object, caller may not access every property.

Example:

```text
Learner may see quiz stem/options.
Learner may not see source checksum.
Learner may not see correct answer before allowed mode.
Teacher may see answer key only if entitlement allows.
Admin may see source traceability.
```

### 14.3. Roles

Suggested roles:

```text
anonymous
learner
teacher
consumer_owner
api_client
telegram_worker
content_admin
taxonomy_admin
billing_admin
security_admin
operations_admin
project_owner
internal_demo
```

### 14.4. Scopes

Suggested scopes:

```text
quiz:read
quiz:deliver
attempt:create
delivery:read
consumer:read
consumer:write
consumer_rules:write
entitlement:read
entitlement:write
analytics:read
source:read
source:write
import:run
import:commit
review:write
admin:read
admin:write
webhook:receive
telegram:deliver
```

Scope alone is not enough. Object-level authorization still applies.

---

## 15. Consumer Context

### 15.1. Consumer as first-class API context

A consumer is not just a token. A consumer has:

```text
consumer_id
consumer_type
owner
status
allowed levels/themes
repeat policy
quota
entitlements
channel/app configuration
delivery history
```

Consumer types:

```text
telegram_channel
telegram_bot
web_app
school_account
teacher_account
external_api_client
internal_demo_client
```

### 15.2. Consumer identity in requests

Recommended patterns:

For a token bound to one consumer:

```http
POST /v1/quiz-items/next
Authorization: Bearer <consumer_bound_token>
```

For multi-consumer owner token:

```json
{
  "consumer_id": "cons_01J...",
  "filters": {...}
}
```

Server MUST verify the caller can operate on the requested `consumer_id`.

### 15.3. Consumer statuses

Allowed consumer statuses:

```text
draft
active
suspended
blocked
archived
internal_demo
```

Only active or explicitly internal-demo consumers may receive delivery.

### 15.4. Consumer-safe defaults

If consumer rules are not fully configured, API MUST fail closed or apply safe defaults.

Safe defaults example:

```text
limited levels
limited themes
low daily quota
no paid/premium features
draft delivery disabled
repeat policy enabled
```

---

## 16. Entitlements, Quotas and Usage

### 16.1. Entitlement rule

Payment status is not access truth.

Access decision:

```text
caller → consumer → plan/manual override → entitlements → quota → API operation allowed/denied
```

### 16.2. Entitlement dimensions

Entitlements may control:

```text
allowed CEFR levels;
allowed themes/objectives/patterns;
API request quota;
quiz delivery quota;
Telegram scheduling;
teacher pack export;
analytics access;
admin capabilities;
school group count;
webhooks;
support tier.
```

### 16.3. Quota check timing

For delivery-producing endpoint:

```text
validate request
  → authenticate
  → authorize consumer
  → check entitlement
  → check quota
  → select item
  → create delivery/reservation
  → increment usage according to policy
```

### 16.4. Quota failure

Quota denial MUST return Problem Details:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/problem+json
Retry-After: 3600
```

```json
{
  "type": "https://api.quizbank.example/problems/quota-exceeded",
  "title": "Quota exceeded",
  "status": 429,
  "detail": "This consumer has reached the configured delivery quota.",
  "instance": "/v1/quiz-items/next",
  "reason_code": "QUOTA_EXCEEDED",
  "consumer_id": "cons_01J...",
  "quota": {
    "limit": 100,
    "window": "day",
    "reset_at": "2026-05-01T00:00:00Z"
  }
}
```

### 16.5. Usage records

Delivery usage SHOULD be derived from delivery records or quota_usage records, not manually invented counters.

---

## 17. Rate Limiting and Abuse Controls

### 17.1. Public beta requirement

Before public beta, API SHALL implement rate limiting or equivalent usage controls.

### 17.2. Rate limit dimensions

Rate limits MAY apply by:

```text
API key;
consumer_id;
IP address;
user account;
endpoint group;
plan;
admin action category.
```

### 17.3. Recommended headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 932
X-RateLimit-Reset: 1714521600
Retry-After: 120
```

### 17.4. Abuse-safe responses

Rate-limit errors use:

```text
reason_code = RATE_LIMIT_EXCEEDED
HTTP status = 429
```

---

## 18. Idempotency and Reservations

### 18.1. Idempotency purpose

Idempotency protects against duplicate operations during retries, network failures and worker crashes.

Use idempotency keys for:

```text
POST /v1/quiz-items/next
POST /v1/attempts
POST /v1/admin/imports/{id}/commit
POST /v1/admin/quiz-items/{id}/publish
POST /v1/billing/webhooks/{provider}
Telegram worker send operations
```

### 18.2. Header

Recommended header:

```http
Idempotency-Key: client-generated-unique-key
```

### 18.3. Idempotency behavior

For the same caller + endpoint + idempotency key + compatible payload:

```text
first request executes;
server stores result or operation reference;
retry returns same outcome or safe reference;
conflicting payload with same key returns error.
```

Reason code for conflict:

```text
IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD
```

### 18.4. Delivery reservation

Delivery-producing selection SHOULD create either:

```text
delivery record with pending/reserved status;
or item_reservation record followed by delivery record;
```

Minimum reservation fields:

```text
reservation_id
consumer_id
quiz_item_id
quiz_item_version_id
expires_at
status
idempotency_key
selection_request_id
```

### 18.5. Reservation failure

If reservation expires or cannot be fulfilled, the system MUST not silently count it as successful delivery.

---

## 19. Pagination, Filtering and Sorting

### 19.1. Pagination style

Use cursor pagination for high-volume resources:

```text
GET /v1/admin/quiz-items?limit=50&cursor=...
```

Response:

```json
{
  "data": [],
  "pagination": {
    "limit": 50,
    "next_cursor": "eyJ...",
    "has_more": false
  }
}
```

### 19.2. Limit rules

```text
default limit: 50
maximum normal limit: 100
admin/report endpoints may define higher limits only if safe
```

### 19.3. Filtering rules

Common filters:

```text
status
cefr_level
theme_id
objective_id
pattern_id
item_type
source_id
consumer_id
from/to timestamp
```

Unknown filters MUST NOT be silently ignored in admin/critical endpoints.

### 19.4. Sorting rules

Use explicit sort parameter:

```text
sort=created_at:desc
sort=updated_at:asc
```

Unsupported sort fields return validation error.

### 19.5. Search

Search endpoint MAY be added later:

```text
GET /v1/admin/quiz-items/search?q=artikel&cefr_level=A2
```

Search must respect authorization and projection rules.

---

## 20. Error Model

### 20.1. Problem Details base object

All machine-readable errors SHOULD follow:

```json
{
  "type": "https://api.quizbank.example/problems/validation-invalid-payload",
  "title": "Invalid request payload",
  "status": 422,
  "detail": "The request body failed validation.",
  "instance": "/v1/attempts",
  "reason_code": "VALIDATION_INVALID_PAYLOAD"
}
```

### 20.2. Required fields

API error responses SHOULD include:

```text
type
title
status
instance
reason_code
```

`detail` MAY be omitted or made generic when security policy requires.

### 20.3. Validation errors

Validation errors SHOULD include field-level errors:

```json
{
  "type": "https://api.quizbank.example/problems/validation-invalid-payload",
  "title": "Invalid request payload",
  "status": 422,
  "instance": "/v1/attempts",
  "reason_code": "VALIDATION_INVALID_PAYLOAD",
  "errors": [
    {
      "path": "/selected_option_ids/0",
      "message": "Unknown option id for this quiz item.",
      "rule_id": "attempt.option_known"
    }
  ]
}
```

### 20.4. Security-safe errors

Authentication and authorization errors MUST avoid leaking sensitive state.

Example:

```text
Do not reveal whether another consumer_id exists if caller lacks access.
```

### 20.5. Human text vs reason codes

Human-readable fields may change:

```text
title
detail
message
```

Stable fields should not change without versioning/change control:

```text
reason_code
type
HTTP status semantics
schema shape
```

---

## 21. Reason Code Catalog

### 21.1. Reason code categories

```text
AUTH_*
AUTHZ_*
VALIDATION_*
SOURCE_*
IMPORT_*
DUPLICATE_*
STATUS_*
TAXONOMY_*
SELECTION_*
ENTITLEMENT_*
QUOTA_*
DELIVERY_*
ATTEMPT_*
TELEGRAM_*
BILLING_*
RATE_LIMIT_*
IDEMPOTENCY_*
OPS_*
```

### 21.2. Core reason codes

| Reason code | HTTP status | Meaning |
|---|---:|---|
| `AUTH_MISSING_CREDENTIALS` | 401 | No valid credentials provided. |
| `AUTH_INVALID_TOKEN` | 401 | Token/key invalid or expired. |
| `AUTHZ_CONSUMER_ACCESS_DENIED` | 403 | Caller cannot access requested consumer. |
| `AUTHZ_SCOPE_MISSING` | 403 | Token lacks required scope. |
| `VALIDATION_INVALID_PAYLOAD` | 422 | Body/query/path failed validation. |
| `VALIDATION_UNSUPPORTED_FILTER` | 422 | Unsupported filter or sort field. |
| `STATUS_NOT_DELIVERABLE` | 409 | Item/source/consumer status blocks operation. |
| `TAXONOMY_INVALID_LEVEL` | 422 | Invalid CEFR level. |
| `TAXONOMY_INVALID_THEME` | 422 | Invalid theme. |
| `SELECTION_NO_ELIGIBLE_ITEM` | 404 or 409 | No item satisfies constraints. |
| `ENTITLEMENT_MISSING_FEATURE` | 403 | Consumer lacks required feature. |
| `QUOTA_EXCEEDED` | 429 | Usage limit reached. |
| `DELIVERY_RESERVATION_CONFLICT` | 409 | Delivery reservation conflict. |
| `ATTEMPT_INVALID_OPTION` | 422 | Submitted option does not belong to item/version. |
| `TELEGRAM_COMPATIBILITY_FAILED` | 422 | Item cannot be projected to Telegram payload. |
| `BILLING_WEBHOOK_SIGNATURE_INVALID` | 401 | Invalid webhook signature. |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded. |
| `IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD` | 409 | Idempotency key conflict. |
| `OPS_SERVICE_UNAVAILABLE` | 503 | Dependency unavailable. |

### 21.3. No eligible item response

When no item can be selected:

```json
{
  "type": "https://api.quizbank.example/problems/no-eligible-item",
  "title": "No eligible quiz item",
  "status": 409,
  "instance": "/v1/quiz-items/next",
  "reason_code": "SELECTION_NO_ELIGIBLE_ITEM",
  "selection_context": {
    "consumer_id": "cons_01J...",
    "cefr_levels": ["A2"],
    "theme_ids": ["T03"],
    "filters_applied": [
      "status",
      "consumer_rules",
      "repeat_policy",
      "entitlements"
    ]
  }
}
```

Use `409` when constraints conflict with availability. Use `404` only if the product decision is that “no candidate resource exists” is more appropriate for that endpoint. Be consistent and document in OpenAPI.

---

## 22. Public-Safe Projection Standard

### 22.1. Projection types

API projections:

```text
QuizItemPublicView
QuizItemDeliveryView
QuizItemAdminView
QuizItemAnswerKeyView
QuizItemTraceabilityView
ConsumerRuleView
EntitlementView
DeliveryView
AttemptResultView
CoverageReportView
ImportReportView
SourceAdminView
ProblemDetails
```

### 22.2. Public quiz delivery projection

Normal delivery response:

```json
{
  "delivery_id": "deliv_01J...",
  "quiz_item": {
    "quiz_item_id": "qi_01J...",
    "version_id": "qiv_01J...",
    "stem": {
      "de": "Welche Antwort ist richtig?"
    },
    "options": [
      {
        "option_id": "qopt_01J_A",
        "position": 1,
        "text": {"de": "Option A"}
      },
      {
        "option_id": "qopt_01J_B",
        "position": 2,
        "text": {"de": "Option B"}
      }
    ],
    "cefr_level": "A2",
    "theme_id": "T03",
    "objective_id": "O09",
    "pattern_id": "P01",
    "item_type": "single_choice"
  },
  "interaction": {
    "mode": "practice_reveal_after_attempt",
    "answer_key_included": false
  }
}
```

### 22.3. Public projection MUST NOT include

```text
raw source path;
source checksum;
content hash;
admin notes;
validation internals;
duplicate/conflict internals;
audit logs;
other consumer data;
hidden correct answer;
internal database IDs.
```

### 22.4. Admin projection MAY include

```text
source_id;
source filename;
source locator;
import_batch_id;
status;
validation results;
duplicate/conflict flags;
content_hash;
status history;
audit trail;
quality flags.
```

### 22.5. Traceability projection

Traceability endpoint MUST be admin-only or permissioned.

Example:

```json
{
  "quiz_item_id": "qi_01J...",
  "source": {
    "source_id": "src_000001",
    "source_locator": {"row_number": 128},
    "import_batch_id": "ib_20260430_0001"
  },
  "status_history": [...]
}
```

---

## 23. Correct Answer Exposure Policy

### 23.1. Core rule

Correct answer data is sensitive product data.

API MUST expose correct answers only in allowed contexts.

### 23.2. Exposure modes

| Mode | Endpoint context | Exposure |
|---|---|---|
| `hidden_before_attempt` | Learner delivery | No answer key in initial response. |
| `practice_reveal_after_attempt` | Attempt flow | Reveal after valid attempt. |
| `teacher_answer_key` | Teacher/export with entitlement | Allowed. |
| `telegram_worker_payload` | Internal Telegram worker | Worker needs correct option positions to send quiz. |
| `admin_full` | Admin review | Allowed. |
| `assessment_hidden` | Assessment-like use | Hidden until configured release. |
| `demo_controlled` | Demo | Allowed only if clearly labeled. |

### 23.3. Attempt response with feedback

After attempt:

```json
{
  "attempt_id": "att_01J...",
  "delivery_id": "deliv_01J...",
  "quiz_item_id": "qi_01J...",
  "is_correct": true,
  "selected_option_ids": ["qopt_01J_B"],
  "feedback": {
    "correct_option_ids": ["qopt_01J_B"],
    "explanation": {
      "de": "Kurze Erklärung."
    }
  }
}
```

### 23.4. Telegram worker exception

Telegram worker may receive correct option positions because Telegram quiz delivery requires them.

This is not a public learner projection. It is an authorized internal/worker projection.

---

## 24. Endpoint Group Overview

### 24.1. MVP endpoint groups

| Group | Purpose | MVP priority |
|---|---|---:|
| Health | Service readiness | P0/P1 |
| Taxonomy | Levels/themes/objectives/patterns | P1 |
| Quiz delivery | Next eligible quiz item | P0 |
| Attempts | Submit answer/attempt | P1 |
| Deliveries | Delivery records | P0/P1 |
| Consumers | Consumer context/rules | P0/P1 |
| Entitlements/quota | Access control | P0/P1 |
| Admin sources | Source onboarding | P0/P1 |
| Admin imports | Dry-run/import reports | P0/P1 |
| Admin reviews | Approve/publish/retire/block | P0/P1 |
| Analytics | Coverage/usage reports | P1 |
| Billing webhooks | Payment-provider events | P1/Beta |
| OpenAPI | Contract access | P0 |

### 24.2. Endpoint catalog summary

```text
GET  /v1/health
GET  /v1/readiness
GET  /v1/openapi.json
GET  /v1/openapi.yaml

GET  /v1/levels
GET  /v1/themes
GET  /v1/objectives
GET  /v1/patterns

POST /v1/quiz-items/next
GET  /v1/quiz-items/{quiz_item_id}
POST /v1/attempts
GET  /v1/attempts/{attempt_id}
GET  /v1/deliveries/{delivery_id}

GET  /v1/consumers/{consumer_id}
GET  /v1/consumers/{consumer_id}/usage
GET  /v1/consumers/{consumer_id}/rules
PATCH /v1/consumers/{consumer_id}/rules
GET  /v1/consumers/{consumer_id}/entitlements

GET  /v1/analytics/coverage
GET  /v1/analytics/usage
GET  /v1/analytics/deliveries

GET  /v1/admin/sources
POST /v1/admin/sources
GET  /v1/admin/sources/{source_id}
PATCH /v1/admin/sources/{source_id}
POST /v1/admin/sources/{source_id}/assign-parser
POST /v1/admin/sources/{source_id}/reject
POST /v1/admin/sources/{source_id}/block

POST /v1/admin/imports/dry-run
GET  /v1/admin/imports/{import_batch_id}
POST /v1/admin/imports/{import_batch_id}/commit

GET  /v1/admin/quiz-items
GET  /v1/admin/quiz-items/{quiz_item_id}
POST /v1/admin/quiz-items/{quiz_item_id}/approve
POST /v1/admin/quiz-items/{quiz_item_id}/publish
POST /v1/admin/quiz-items/{quiz_item_id}/retire
POST /v1/admin/quiz-items/{quiz_item_id}/block

GET  /v1/admin/reports/inventory
GET  /v1/admin/reports/coverage
GET  /v1/admin/reports/imports

POST /v1/billing/webhooks/{provider}
```

---

## 25. Health and Readiness Endpoints

### 25.1. Health

```http
GET /v1/health
```

Purpose:

```text
Basic liveness check.
```

Response:

```json
{
  "status": "ok",
  "service": "api-quiz-bank",
  "version": "1.0.0",
  "time": "2026-04-30T18:00:00Z"
}
```

### 25.2. Readiness

```http
GET /v1/readiness
```

Purpose:

```text
Check whether API can serve real requests.
```

Response:

```json
{
  "status": "ready",
  "checks": [
    {"name": "database", "status": "ok"},
    {"name": "selection_engine", "status": "ok"},
    {"name": "entitlement_engine", "status": "ok"}
  ]
}
```

### 25.3. Safety

Readiness endpoint MUST NOT expose secrets, credentials or private infrastructure details.

---

## 26. Taxonomy Endpoints

### 26.1. Levels

```http
GET /v1/levels
```

Response:

```json
{
  "data": [
    {"cefr_level": "A1", "title": "Beginner"},
    {"cefr_level": "A2", "title": "Elementary"},
    {"cefr_level": "B1", "title": "Intermediate"},
    {"cefr_level": "B2", "title": "Upper intermediate"},
    {"cefr_level": "C1", "title": "Advanced"},
    {"cefr_level": "C2", "title": "Mastery"}
  ]
}
```

### 26.2. Themes

```http
GET /v1/themes
```

Query parameters:

```text
include_counts=false|true
cefr_level=A2
```

Response:

```json
{
  "data": [
    {
      "theme_id": "T03",
      "slug": "example-theme",
      "title": {
        "uk": "Приклад теми",
        "de": "Beispielthema"
      },
      "is_active": true
    }
  ]
}
```

### 26.3. Objectives and patterns

```http
GET /v1/objectives
GET /v1/patterns
```

These endpoints expose stable taxonomy metadata for filtering and integration.

---

## 27. Quiz Item Delivery API

### 27.1. Next quiz endpoint

Normative endpoint:

```http
POST /v1/quiz-items/next
```

Purpose:

```text
Return next eligible quiz item for a consumer and create delivery/reservation according to policy.
```

### 27.2. Request

```json
{
  "consumer_id": "cons_01J...",
  "filters": {
    "cefr_levels": ["A2"],
    "theme_ids": ["T03"],
    "objective_ids": ["O09"],
    "pattern_ids": ["P01"],
    "item_types": ["single_choice"]
  },
  "delivery_mode": "practice_reveal_after_attempt",
  "idempotency_context": {
    "client_delivery_key": "lesson-2026-04-30-item-1"
  },
  "demo": {
    "deterministic": false
  }
}
```

### 27.3. Selection rules

Endpoint MUST apply:

```text
authentication;
object-level authorization for consumer_id;
consumer status check;
entitlement check;
quota check;
status filter: approved/published only;
CEFR/theme/objective/pattern filters;
consumer compatibility filters;
repeat policy;
blocked/retired exclusion;
Telegram compatibility if requested by Telegram consumer;
delivery/reservation logging.
```

### 27.4. Response

```json
{
  "delivery_id": "deliv_01J...",
  "reservation_id": "res_01J...",
  "consumer_id": "cons_01J...",
  "quiz_item": {
    "quiz_item_id": "qi_01J...",
    "version_id": "qiv_01J...",
    "stem": {
      "de": "Welche Antwort ist richtig?"
    },
    "options": [
      {
        "option_id": "qopt_01J_A",
        "position": 1,
        "text": {"de": "Option A"}
      },
      {
        "option_id": "qopt_01J_B",
        "position": 2,
        "text": {"de": "Option B"}
      }
    ],
    "cefr_level": "A2",
    "theme_id": "T03",
    "objective_id": "O09",
    "pattern_id": "P01",
    "item_type": "single_choice"
  },
  "interaction": {
    "mode": "practice_reveal_after_attempt",
    "answer_key_included": false,
    "attempt_required_for_feedback": true
  },
  "selection": {
    "repeat_policy_applied": true,
    "entitlement_checked": true,
    "quota_checked": true
  }
}
```

### 27.5. Delivery logging

A successful response MUST create or enable traceable delivery record.

Minimum delivery record:

```text
delivery_id
consumer_id
quiz_item_id
version_id
channel
status
selected_at/delivered_at
selection_reason_summary
entitlement_decision_id or equivalent
quota_usage_id or equivalent
```

### 27.6. Read quiz item by ID

```http
GET /v1/quiz-items/{quiz_item_id}
```

Normal consumer response MUST be public-safe. It MUST NOT expose admin-only traceability or hidden answer keys.

---

## 28. Attempts API

### 28.1. Submit attempt

```http
POST /v1/attempts
```

Purpose:

```text
Record selected answer(s), determine correctness when allowed, and support analytics.
```

### 28.2. Request

```json
{
  "delivery_id": "deliv_01J...",
  "quiz_item_id": "qi_01J...",
  "version_id": "qiv_01J...",
  "selected_option_ids": ["qopt_01J_B"],
  "response_time_ms": 4200,
  "client_context": {
    "session_id": "sess_01J..."
  }
}
```

### 28.3. Validation

API MUST verify:

```text
delivery exists or attempt context is allowed;
quiz_item_id matches delivery;
version_id matches delivery or policy allows latest;
selected_option_ids belong to that item version;
caller is authorized for consumer/user context;
idempotency if key supplied;
attempt not expired if window configured.
```

### 28.4. Response

```json
{
  "attempt_id": "att_01J...",
  "delivery_id": "deliv_01J...",
  "quiz_item_id": "qi_01J...",
  "is_correct": true,
  "selected_option_ids": ["qopt_01J_B"],
  "feedback": {
    "answer_key_included": true,
    "correct_option_ids": ["qopt_01J_B"],
    "explanation": {
      "de": "Kurze Erklärung."
    }
  }
}
```

### 28.5. Attempt idempotency

If duplicate attempt submission occurs with same idempotency key, API SHOULD return the original attempt result or documented duplicate response.

---

## 29. Deliveries API

### 29.1. Get delivery

```http
GET /v1/deliveries/{delivery_id}
```

Normal consumer can only read own consumer delivery.

Admin may read full delivery detail.

### 29.2. Delivery view

```json
{
  "delivery_id": "deliv_01J...",
  "consumer_id": "cons_01J...",
  "quiz_item_id": "qi_01J...",
  "version_id": "qiv_01J...",
  "channel": "api",
  "status": "delivered",
  "delivered_at": "2026-04-30T18:00:00Z"
}
```

### 29.3. Delivery statuses

```text
reserved
delivered
sent
failed
skipped
expired
cancelled
```

### 29.4. Failure details

Failure reason MAY be exposed to consumer owner. Internal details remain admin-only.

---

## 30. Consumer and Consumer Rules API

### 30.1. Get consumer

```http
GET /v1/consumers/{consumer_id}
```

### 30.2. Consumer view

```json
{
  "consumer_id": "cons_01J...",
  "type": "telegram_channel",
  "status": "active",
  "display_name": "German Daily Quiz",
  "created_at": "2026-04-30T18:00:00Z"
}
```

### 30.3. Get rules

```http
GET /v1/consumers/{consumer_id}/rules
```

Response:

```json
{
  "consumer_id": "cons_01J...",
  "allowed_cefr_levels": ["A1", "A2"],
  "allowed_theme_ids": ["T01", "T02", "T03"],
  "daily_delivery_limit": 10,
  "repeat_policy": {
    "type": "window_days",
    "days": 30
  },
  "is_active": true
}
```

### 30.4. Update rules

```http
PATCH /v1/consumers/{consumer_id}/rules
```

Admin/consumer owner only.

API MUST validate taxonomy values and plan limits.

---

## 31. Entitlements and Usage API

### 31.1. Get entitlements

```http
GET /v1/consumers/{consumer_id}/entitlements
```

Response:

```json
{
  "consumer_id": "cons_01J...",
  "entitlements": [
    {
      "entitlement_id": "ent_01J...",
      "feature": "quiz_delivery",
      "scope": {
        "cefr_levels": ["A1", "A2"],
        "theme_ids": ["T01", "T02"]
      },
      "valid_until": "2026-05-31T23:59:59Z"
    }
  ]
}
```

### 31.2. Get usage

```http
GET /v1/consumers/{consumer_id}/usage
```

Response:

```json
{
  "consumer_id": "cons_01J...",
  "usage": [
    {
      "metric": "quiz_deliveries",
      "window": "day",
      "used": 7,
      "limit": 10,
      "reset_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

### 31.3. Manual overrides

Manual entitlement updates are admin operations and MUST be audited.

---

## 32. Admin Source API

### 32.1. List sources

```http
GET /v1/admin/sources?state=registered&limit=50
```

Admin only.

### 32.2. Register source

```http
POST /v1/admin/sources
```

Request:

```json
{
  "proposed_source_name": "New A2 Grammar Pack",
  "original_filename": "new_a2_grammar_pack.csv",
  "current_path": "data/raw/intake/new_a2_grammar_pack.csv",
  "format": "csv",
  "encoding": "utf-8",
  "intended_level_range": ["A2"],
  "intended_theme_ids": ["T01"],
  "expected_item_count": 300,
  "rights_status": "owned",
  "notes": "Candidate source for future onboarding."
}
```

Response:

```json
{
  "source_id": "src_000085",
  "source_state": "registered",
  "checksum_sha256": "sha256:...",
  "registered_at": "2026-04-30T18:00:00Z"
}
```

### 32.3. Source states

API must support source states from data/domain model:

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

### 32.4. Assign parser

```http
POST /v1/admin/sources/{source_id}/assign-parser
```

Request:

```json
{
  "parser_profile_id": "pp_csv_mcq_v1",
  "defaults": {
    "cefr_level": "A2",
    "theme_id": "T01",
    "objective_id": "O09",
    "pattern_id": "P01"
  }
}
```

### 32.5. Reject or block source

```http
POST /v1/admin/sources/{source_id}/reject
POST /v1/admin/sources/{source_id}/block
```

Request MUST include reason:

```json
{
  "reason_code": "SOURCE_RIGHTS_UNCLEAR",
  "note": "Rights status could not be confirmed."
}
```

---

## 33. Admin Import API

### 33.1. Dry-run import

```http
POST /v1/admin/imports/dry-run
```

Request:

```json
{
  "source_id": "src_000085",
  "manifest_entry_id": "ime_01J...",
  "parser_profile_id": "pp_csv_mcq_v1",
  "options": {
    "sample_normalized_output": true,
    "detect_duplicates": true,
    "validate_telegram_compatibility": true
  }
}
```

Response:

```json
{
  "import_batch_id": "ib_20260430_0001",
  "mode": "dry_run",
  "status": "dry_run_completed",
  "counts": {
    "rows_seen": 300,
    "candidates_created": 298,
    "validation_failures": 2,
    "duplicate_candidates": 4
  },
  "report_url": "/v1/admin/imports/ib_20260430_0001"
}
```

### 33.2. Get import report

```http
GET /v1/admin/imports/{import_batch_id}
```

Response SHOULD include:

```text
source_id;
parser_profile_id;
input checksum;
rows seen;
accepted/skipped/error counts;
validation errors;
duplicate/conflict candidates;
Telegram compatibility issues;
recommendation;
created items if committed.
```

### 33.3. Commit import

```http
POST /v1/admin/imports/{import_batch_id}/commit
```

Rules:

```text
Admin only.
Dry-run or ready_to_commit batch only.
Idempotency key required or strongly recommended.
Conflicts must be resolved or explicitly allowed.
Import commit must preserve source traceability.
Commit must not publish items automatically unless policy explicitly allows.
```

---

## 34. Admin Review and Status API

### 34.1. List review items

```http
GET /v1/admin/quiz-items?status=needs_review&source_id=src_000085&limit=50
```

### 34.2. Get admin item

```http
GET /v1/admin/quiz-items/{quiz_item_id}
```

Admin projection may include source traceability, validation results, content hash, duplicate flags and status history.

### 34.3. Approve item

```http
POST /v1/admin/quiz-items/{quiz_item_id}/approve
```

Request:

```json
{
  "reason": "Validated metadata and schema; ready for controlled delivery."
}
```

Rules:

```text
Item must pass required schema rules.
Item must have CEFR level and primary theme.
Item must have correct answer references.
Item must have source traceability.
Status transition must be logged.
```

### 34.4. Publish item

```http
POST /v1/admin/quiz-items/{quiz_item_id}/publish
```

Publishing may mean broader availability beyond approved internal delivery.

### 34.5. Retire/block item

```http
POST /v1/admin/quiz-items/{quiz_item_id}/retire
POST /v1/admin/quiz-items/{quiz_item_id}/block
```

Reason required:

```json
{
  "reason_code": "ITEM_REPORTED_INCORRECT",
  "note": "Reported by teacher; blocked until review."
}
```

Retire/block MUST preserve historical deliveries and attempts.

---

## 35. Analytics API

### 35.1. Coverage analytics

```http
GET /v1/analytics/coverage
```

Query:

```text
level=A2
theme_id=T03
include_empty=true
```

Response:

```json
{
  "coverage_axis": ["cefr_level", "theme_id", "objective_id", "pattern_id"],
  "data": [
    {
      "cefr_level": "A2",
      "theme_id": "T03",
      "objective_id": "O09",
      "pattern_id": "P01",
      "item_count": 120,
      "approved_count": 80,
      "published_count": 50
    }
  ]
}
```

### 35.2. Usage analytics

```http
GET /v1/analytics/usage?consumer_id=cons_01J&from=2026-04-01&to=2026-04-30
```

Must enforce authorization.

### 35.3. Delivery analytics

```http
GET /v1/analytics/deliveries
```

Metrics:

```text
delivery count;
delivery success/failure;
repeat-policy blocks;
quota denials;
no-eligible-item events;
Telegram failures.
```

### 35.4. Privacy

Analytics responses MUST be aggregated unless caller has permission for detailed records.

---

## 36. Telegram Worker API Relationship

### 36.1. Core rule

Telegram worker is a consumer/adapter, not the product core.

Telegram worker MUST NOT:

```text
read raw CSV;
select items independently from selection engine;
bypass status filtering;
bypass entitlement/quota;
bypass delivery logging;
expose correct answers outside Telegram payload needs.
```

### 36.2. Recommended flow

```text
scheduler triggers worker
  → worker calls POST /v1/quiz-items/next with telegram consumer_id
  → API/selection returns delivery projection or internal Telegram projection
  → worker validates Telegram compatibility
  → worker sends via Telegram Bot API
  → worker updates delivery status
```

### 36.3. Telegram projection endpoint

Optional internal endpoint:

```http
POST /v1/internal/telegram/deliveries/simulate
```

or:

```http
POST /v1/internal/telegram/payloads
```

Internal endpoints MUST require service authentication and must not be public.

### 36.4. Telegram send result update

Optional endpoint:

```http
PATCH /v1/internal/telegram/deliveries/{delivery_id}
```

Request:

```json
{
  "status": "sent",
  "telegram_message_id": "12345",
  "sent_at": "2026-04-30T18:00:00Z"
}
```

Failure:

```json
{
  "status": "failed",
  "reason_code": "TELEGRAM_SEND_FAILED",
  "provider_error_summary": "Forbidden: bot is not admin in channel"
}
```

---

## 37. Billing Webhook API

### 37.1. Webhook endpoint

```http
POST /v1/billing/webhooks/{provider}
```

Examples:

```text
/v1/billing/webhooks/stripe
/v1/billing/webhooks/liqpay
/v1/billing/webhooks/wayforpay
```

Actual provider list is future implementation decision.

### 37.2. Webhook rules

Webhook endpoint MUST:

```text
verify provider signature;
store provider event ID;
be idempotent;
not grant access directly without internal entitlement update;
create billing_event record;
log failure safely;
avoid exposing secrets in logs.
```

### 37.3. Webhook response

Provider webhook response should be minimal:

```json
{
  "received": true
}
```

### 37.4. Billing truth

External payment provider is not access truth.

Internal entitlement state controls API access.

---

## 38. Webhooks and External Events

Future outbound webhooks MAY notify external consumers about:

```text
delivery.created;
attempt.submitted;
quota.exceeded;
entitlement.updated;
report.generated;
```

Outbound webhooks are NOT MVP-critical unless a pilot consumer requires them.

If added, they MUST include:

```text
signature;
event_id;
event_type;
created_at;
idempotency/retry policy;
minimal payload;
subscription management;
secret rotation.
```

---

## 39. OpenAPI Contract Rules

### 39.1. Location

Recommended file:

```text
api/openapi.yaml
```

Alternative:

```text
services/api/openapi.yaml
```

### 39.2. Contract ownership

OpenAPI contract is a production artifact.

Changes must pass:

```text
review;
contract tests;
implementation alignment;
changelog if external behavior changes.
```

### 39.3. Required OpenAPI sections

OpenAPI file MUST include:

```text
openapi version;
info;
servers;
tags;
security schemes;
paths;
components/schemas;
components/responses;
components/parameters;
components/headers;
components/securitySchemes;
ProblemDetails schema;
examples for critical endpoints.
```

### 39.4. Tags

Recommended tags:

```text
Health
Taxonomy
Quiz Delivery
Attempts
Deliveries
Consumers
Entitlements
Analytics
Admin Sources
Admin Imports
Admin Reviews
Billing Webhooks
Internal Telegram
```

### 39.5. OpenAPI must match implementation

Any endpoint implemented but missing from OpenAPI is not externally supported.

Any endpoint in OpenAPI but not implemented must be marked planned/stub/internal, or removed from external contract.

### 39.6. OpenAPI external vs internal

There MAY be two contracts:

```text
openapi.public.yaml
openapi.admin.yaml
```

or one contract with internal/admin endpoints clearly tagged and secured.

---

## 40. Seed OpenAPI Structure

This is a seed, not final generated contract.

```yaml
openapi: 3.2.0
info:
  title: API Quiz Bank API
  version: 1.0.0
  summary: Governed API-first quiz delivery platform for German quiz content.
  description: >-
    API Quiz Bank exposes governed, source-traceable, CEFR-aware German quiz
    content through versioned API endpoints. The API enforces status,
    consumer rules, entitlements, quota, repeat policy and delivery logging.
jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema
servers:
  - url: https://api.example.com/v1
    description: Production API placeholder
  - url: https://api-demo.example.com/v1
    description: Controlled demo API placeholder
security:
  - bearerAuth: []
tags:
  - name: Health
  - name: Taxonomy
  - name: Quiz Delivery
  - name: Attempts
  - name: Deliveries
  - name: Consumers
  - name: Admin Sources
  - name: Admin Imports
  - name: Admin Reviews
  - name: Analytics
  - name: Billing Webhooks
paths:
  /health:
    get:
      tags: [Health]
      summary: Liveness check
      security: []
      responses:
        '200':
          description: Service is alive
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
  /readiness:
    get:
      tags: [Health]
      summary: Readiness check
      responses:
        '200':
          description: Service is ready
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReadinessResponse'
        '503':
          $ref: '#/components/responses/ServiceUnavailableProblem'
  /levels:
    get:
      tags: [Taxonomy]
      summary: List CEFR levels
      security: []
      responses:
        '200':
          description: CEFR levels
          content:
            application/json:
              schema:
                type: object
                required: [data]
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/CefrLevel'
  /quiz-items/next:
    post:
      tags: [Quiz Delivery]
      summary: Select and deliver next eligible quiz item
      description: >-
        Creates a delivery/reservation according to policy. This endpoint
        enforces authentication, object-level authorization, consumer rules,
        entitlements, quotas, status filtering, repeat policy and public-safe
        projection rules.
      parameters:
        - $ref: '#/components/parameters/IdempotencyKey'
        - $ref: '#/components/parameters/RequestId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NextQuizRequest'
      responses:
        '200':
          description: Next quiz selected and delivery/reservation created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NextQuizResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedProblem'
        '403':
          $ref: '#/components/responses/ForbiddenProblem'
        '409':
          $ref: '#/components/responses/NoEligibleItemProblem'
        '422':
          $ref: '#/components/responses/ValidationProblem'
        '429':
          $ref: '#/components/responses/QuotaExceededProblem'
  /attempts:
    post:
      tags: [Attempts]
      summary: Submit quiz attempt
      parameters:
        - $ref: '#/components/parameters/IdempotencyKey'
        - $ref: '#/components/parameters/RequestId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AttemptSubmission'
      responses:
        '201':
          description: Attempt recorded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AttemptResult'
        '422':
          $ref: '#/components/responses/ValidationProblem'
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      description: Bearer token or API key represented as bearer credential.
  parameters:
    RequestId:
      name: X-Request-Id
      in: header
      required: false
      schema:
        type: string
      description: Client-provided request correlation ID.
    IdempotencyKey:
      name: Idempotency-Key
      in: header
      required: false
      schema:
        type: string
      description: Idempotency key for retry-safe mutating operations.
  responses:
    UnauthorizedProblem:
      description: Missing or invalid credentials
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    ForbiddenProblem:
      description: Authorization denied
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    ValidationProblem:
      description: Invalid request payload
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    QuotaExceededProblem:
      description: Consumer quota exceeded
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    NoEligibleItemProblem:
      description: No eligible quiz item could be selected
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    ServiceUnavailableProblem:
      description: Service unavailable
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
  schemas:
    HealthResponse:
      type: object
      required: [status, service, time]
      properties:
        status:
          type: string
          enum: [ok]
        service:
          type: string
        version:
          type: string
        time:
          type: string
          format: date-time
    ReadinessResponse:
      type: object
      required: [status, checks]
      properties:
        status:
          type: string
          enum: [ready, not_ready]
        checks:
          type: array
          items:
            type: object
            required: [name, status]
            properties:
              name:
                type: string
              status:
                type: string
                enum: [ok, degraded, failed]
    CefrLevel:
      type: object
      required: [cefr_level]
      properties:
        cefr_level:
          type: string
          enum: [A1, A2, B1, B2, C1, C2]
        title:
          type: string
    NextQuizRequest:
      type: object
      required: [consumer_id]
      properties:
        consumer_id:
          type: string
          pattern: '^cons_'
        filters:
          $ref: '#/components/schemas/QuizSelectionFilters'
        delivery_mode:
          type: string
          enum:
            - hidden_before_attempt
            - practice_reveal_after_attempt
            - quiz_poll
            - assessment_hidden
            - demo_controlled
    QuizSelectionFilters:
      type: object
      properties:
        cefr_levels:
          type: array
          items:
            type: string
            enum: [A1, A2, B1, B2, C1, C2]
        theme_ids:
          type: array
          items:
            type: string
        objective_ids:
          type: array
          items:
            type: string
        pattern_ids:
          type: array
          items:
            type: string
        item_types:
          type: array
          items:
            type: string
            enum: [single_choice, multiple_choice]
    NextQuizResponse:
      type: object
      required: [delivery_id, consumer_id, quiz_item, interaction]
      properties:
        delivery_id:
          type: string
          pattern: '^deliv_'
        reservation_id:
          type: string
        consumer_id:
          type: string
          pattern: '^cons_'
        quiz_item:
          $ref: '#/components/schemas/QuizItemDeliveryView'
        interaction:
          $ref: '#/components/schemas/InteractionPolicy'
    QuizItemDeliveryView:
      type: object
      required:
        - quiz_item_id
        - version_id
        - stem
        - options
        - cefr_level
        - theme_id
        - item_type
      properties:
        quiz_item_id:
          type: string
          pattern: '^qi_'
        version_id:
          type: string
          pattern: '^qiv_'
        stem:
          $ref: '#/components/schemas/LocalizedText'
        options:
          type: array
          minItems: 2
          items:
            $ref: '#/components/schemas/QuizOptionPublicView'
        cefr_level:
          type: string
          enum: [A1, A2, B1, B2, C1, C2]
        theme_id:
          type: string
        objective_id:
          type: string
        pattern_id:
          type: string
        item_type:
          type: string
          enum: [single_choice, multiple_choice]
    QuizOptionPublicView:
      type: object
      required: [option_id, position, text]
      properties:
        option_id:
          type: string
          pattern: '^qopt_'
        position:
          type: integer
          minimum: 1
        text:
          $ref: '#/components/schemas/LocalizedText'
    LocalizedText:
      type: object
      properties:
        de:
          type: string
        uk:
          type: string
      additionalProperties: false
    InteractionPolicy:
      type: object
      required: [mode, answer_key_included]
      properties:
        mode:
          type: string
        answer_key_included:
          type: boolean
        attempt_required_for_feedback:
          type: boolean
    AttemptSubmission:
      type: object
      required: [delivery_id, quiz_item_id, selected_option_ids]
      properties:
        delivery_id:
          type: string
          pattern: '^deliv_'
        quiz_item_id:
          type: string
          pattern: '^qi_'
        version_id:
          type: string
          pattern: '^qiv_'
        selected_option_ids:
          type: array
          minItems: 1
          items:
            type: string
            pattern: '^qopt_'
        response_time_ms:
          type: integer
          minimum: 0
    AttemptResult:
      type: object
      required: [attempt_id, delivery_id, quiz_item_id, is_correct]
      properties:
        attempt_id:
          type: string
          pattern: '^att_'
        delivery_id:
          type: string
          pattern: '^deliv_'
        quiz_item_id:
          type: string
          pattern: '^qi_'
        is_correct:
          type: boolean
        selected_option_ids:
          type: array
          items:
            type: string
        feedback:
          type: object
          properties:
            answer_key_included:
              type: boolean
            correct_option_ids:
              type: array
              items:
                type: string
            explanation:
              $ref: '#/components/schemas/LocalizedText'
    ProblemDetails:
      type: object
      required: [type, title, status, reason_code]
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string
        reason_code:
          type: string
        errors:
          type: array
          items:
            type: object
            properties:
              path:
                type: string
              message:
                type: string
              rule_id:
                type: string
```

---

## 41. API Security Requirements

### 41.1. Security controls

API MUST implement or plan these controls before public/paid launch:

```text
authentication for non-public endpoints;
object-level authorization;
object-property authorization;
admin role authorization;
API key/token hashing or sealing;
secret redaction in logs;
rate limiting/abuse controls;
input validation;
safe error responses;
webhook signature verification;
audit logging for admin and security actions;
least-privilege internal service tokens.
```

### 41.2. Fail closed

If auth/entitlement/selection status is uncertain, API MUST fail closed.

Examples:

```text
unknown consumer → deny;
missing entitlement → deny;
unrecognized item status → not deliverable;
ambiguous correct answer reference → not deliverable;
unknown source state → admin review required;
Telegram compatibility unknown → do not send.
```

### 41.3. Admin safety

Admin endpoints MUST protect:

```text
source metadata;
import reports;
validation internals;
correct answers;
content hashes;
admin notes;
audit logs;
consumer secrets;
entitlements and billing state.
```

---

## 42. Privacy and Data Exposure Standard

### 42.1. Data minimization

API should store and expose only what is needed for:

```text
delivery;
attempt tracking;
entitlements/quota;
analytics;
security;
support;
operations.
```

### 42.2. Learner data

Learner-facing API SHOULD avoid requiring personal identity for MVP unless product flow demands it.

If learner identity is introduced, privacy/legal posture must be reviewed before public use.

### 42.3. Analytics exposure

Analytics endpoints must default to aggregate data unless caller has explicit permission for detailed records.

### 42.4. Logs

Logs MUST NOT contain:

```text
API tokens;
secrets;
full payment payloads if sensitive;
unnecessary personal data;
raw source file content;
private correct-answer keys in public contexts.
```

---

## 43. Caching and Freshness

### 43.1. Cacheable endpoints

Potentially cacheable:

```text
GET /v1/levels
GET /v1/themes
GET /v1/objectives
GET /v1/patterns
GET /v1/openapi.json
```

### 43.2. Non-cacheable endpoints

Do not cache by default:

```text
POST /v1/quiz-items/next
POST /v1/attempts
consumer-specific usage;
entitlements;
admin/import/review endpoints;
correct-answer projections.
```

### 43.3. Headers

Consumer-specific responses SHOULD use:

```http
Cache-Control: no-store
```

Public taxonomy may use:

```http
Cache-Control: public, max-age=3600
```

---

## 44. Performance and Reliability Baseline

### 44.1. MVP performance targets

MVP target values may be adjusted after implementation, but initial targets:

| Endpoint class | Target |
|---|---:|
| Health | < 100 ms local/staging typical |
| Taxonomy list | < 300 ms typical |
| Next quiz selection | < 1000 ms typical for pilot dataset |
| Attempt submission | < 500 ms typical |
| Admin import dry-run | async or long-running job |

### 44.2. Async operations

Long-running operations SHOULD be asynchronous:

```text
source import dry-run;
large import commit;
coverage report generation;
bulk status changes;
large export generation.
```

Pattern:

```text
POST starts job → returns job/import_batch/report ID → GET status endpoint polls result.
```

### 44.3. Reliability rules

API SHOULD:

```text
return explicit errors rather than silent failures;
log delivery failures;
make retries safe through idempotency;
not duplicate Telegram posts on retry;
preserve delivery and attempt history;
support maintenance/rollback process.
```

---

## 45. Observability Standard

### 45.1. Request logging

Log per request:

```text
request_id;
method;
path template, not raw sensitive URL;
status_code;
latency_ms;
consumer_id if safe;
actor_id if admin;
reason_code for errors;
```

### 45.2. Metrics

API metrics:

```text
request count by endpoint/status;
latency p50/p95/p99;
error rate by reason_code;
quota denials;
no eligible item events;
successful next quiz responses;
attempt submissions;
delivery failures;
admin status changes;
webhook failures.
```

### 45.3. Tracing

Recommended trace chain:

```text
request_id
  → selection_request_id
  → delivery_id
  → attempt_id
  → analytics event
```

### 45.4. Demo observability

Stanford-style demo should show at least:

```text
API request;
selected item;
delivery_id;
delivery log;
quota/entitlement decision or simulated denial;
analytics update.
```

---

## 46. API Testing Standard

### 46.1. Test categories

Required API test categories:

```text
contract tests;
request validation tests;
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
Telegram projection compatibility tests;
analytics authorization tests.
```

### 46.2. P0 tests for MVP

MVP MUST test:

```text
POST /v1/quiz-items/next returns approved/published item only;
draft item is never delivered to normal consumer;
blocked item is never delivered;
unauthorized consumer access is denied;
quota exceeded returns 429 Problem Details;
no eligible item returns machine-readable reason;
correct answer not exposed in hidden mode;
POST /v1/attempts validates option IDs;
admin source registration requires authorization;
OpenAPI contract exists and validates.
```

### 46.3. Contract testing

Contract tests MUST ensure:

```text
implementation responses conform to OpenAPI schemas;
OpenAPI paths match implemented routes;
ProblemDetails schema is used for errors;
examples remain valid;
security requirements are declared;
internal endpoints are not accidentally public.
```

### 46.4. Regression tests

Any bug involving draft delivery, answer leakage, authorization bypass or quota bypass MUST produce regression test.

---

## 47. CI and Release Gates

### 47.1. API gate before external access

Before external API access:

```text
OpenAPI spec exists;
/v1 versioning exists;
auth model exists;
Problem Details errors exist;
status filtering works;
entitlement/quota checks work;
object-level authorization tests pass;
rate limits or usage controls exist;
correct-answer exposure policy is tested;
contract tests pass.
```

### 47.2. OpenAPI CI checks

CI SHOULD validate:

```text
OpenAPI syntax;
schema references;
examples;
operationId uniqueness;
security scheme presence;
ProblemDetails responses for error statuses;
no undocumented public endpoints;
no accidental admin/internal exposure.
```

### 47.3. Release checklist

Every API release should include:

```text
OpenAPI diff;
changelog;
contract tests;
security-sensitive change review;
SRS/API standard update if behavior changed;
known limitations;
rollback plan.
```

---

## 48. Stanford-Style API Demo Script

Minimum API demo path:

```text
1. Show OpenAPI contract exists.
2. Show current corpus baseline/inventory report.
3. Show source onboarding endpoint or artifact for future file.
4. Show canonical quiz item schema/projection.
5. Call POST /v1/quiz-items/next with demo consumer.
6. Show response includes delivery_id and public-safe quiz item.
7. Show correct answer is hidden in initial learner-facing response.
8. Show delivery log for delivery_id.
9. Submit POST /v1/attempts.
10. Show feedback/answer exposure after attempt.
11. Simulate quota exceeded and show 429 Problem Details.
12. Show draft item is not deliverable.
13. Show analytics/usage update.
```

Demo must not claim planned features as implemented.

---

## 49. Traceability Matrix

| API standard area | SRS / use case / domain alignment |
|---|---|
| Versioned `/v1` API | `SRS-API-001`, `SRS-API-002` |
| Health/readiness | `SRS-API-003`, operations requirements |
| Taxonomy endpoints | `SRS-API-004`, `SRS-TAX` |
| Next quiz delivery | `SRS-API-005`, `UC-005`, selection domain |
| Attempt submission | `SRS-API-006`, `UC-006` |
| No draft delivery | `SRS-API-007`, `UC-019`, status lifecycle |
| Authentication | `SRS-API-008`, `NFR-SEC` |
| Object-level authorization | `SRS-API-009`, `NFR-SEC-005`, OWASP alignment |
| Entitlement/quota | `SRS-API-010`, `SRS-BILL`, `UC-008` |
| Problem Details | `SRS-API-011`, error architecture |
| OpenAPI contract | `SRS-API-012`, `SRS-DOC-006` |
| Public-safe metadata | `SRS-API-016`, `SRS-API-017`, domain projections |
| Admin endpoints | `SRS-API-018`, `UC-001`–`UC-004`, `UC-016`–`UC-018` |
| Source onboarding API | `SRS-ONB`, `UC-001`, `UC-030` |
| Delivery logging | `SRS-SEL-008`, `UC-005`, delivery domain |
| Telegram worker support | `SRS-TG`, `UC-007`, `UC-021`, `UC-022` |
| Stanford demo | `SRS-DEMO-004`, `SRS-DEMO-006`, `UC-015` |

---

## 50. API Risk Register

| Risk | API control |
|---|---|
| Draft items delivered | Status filter in selection/API; contract and integration tests. |
| Correct answers leak | Projection mode rules; object-property authorization; tests. |
| Consumer accesses another consumer | Object-level authorization; token/consumer binding; tests. |
| Quota bypass | Entitlement/quota check before delivery; usage records. |
| Telegram bypasses API | Worker uses API/selection; no raw CSV access. |
| GET mutates state | Use POST for delivery-producing next quiz; keep GET only for read-only preview. |
| New source files bypass governance | Admin source/import endpoints require source_id/checksum/manifest/dry-run. |
| Problem errors inconsistent | ProblemDetails schema + reason_code catalog. |
| Duplicate delivery on retry | Idempotency keys and reservations. |
| OpenAPI drifts from implementation | Contract tests in CI. |
| Admin endpoint exposed | Security schemes, route separation and access tests. |
| Demo overclaims | Demo script tied to endpoints/logs/artifacts. |

---

## 51. API Acceptance Criteria

`07_api_standard.md` is accepted when it satisfies:

```text
AC-APISTD-001: Aligns with Constitution, Vision, Product Charter, SRS, Use Cases, Domain Model, Architecture and Data Standard.
AC-APISTD-002: Defines OpenAPI baseline and contract location.
AC-APISTD-003: Defines /v1 versioning policy.
AC-APISTD-004: Defines endpoint groups for MVP/Pilot/Production.
AC-APISTD-005: Resolves next-quiz GET vs POST semantics.
AC-APISTD-006: Defines authentication and authorization model.
AC-APISTD-007: Defines object-level and object-property authorization rules.
AC-APISTD-008: Defines entitlement/quota enforcement rules.
AC-APISTD-009: Defines public-safe quiz item projection.
AC-APISTD-010: Defines correct-answer exposure modes.
AC-APISTD-011: Defines Problem Details error model and reason codes.
AC-APISTD-012: Defines idempotency and delivery reservation rules.
AC-APISTD-013: Defines source onboarding/admin API surface.
AC-APISTD-014: Defines API testing and launch gates.
AC-APISTD-015: Provides Stanford-style demo API script.
```

---

## 52. Open Questions

These questions do not block this standard but must be resolved during implementation planning:

```text
OQ-API-001: What exact API framework will implement /v1?
OQ-API-002: Will external API keys be opaque bearer tokens, JWTs, or mixed?
OQ-API-003: Will OAuth/OIDC be deferred until school/enterprise phase?
OQ-API-004: What exact rate limits apply to Free, Student, Teacher, Channel, School and API Pro plans?
OQ-API-005: Should GET /v1/quiz-items/next exist at all, or should it be fully replaced by POST?
OQ-API-006: What exact public theme slugs/titles will be frozen in taxonomy files?
OQ-API-007: Which admin operations are implemented through API in MVP vs CLI-only?
OQ-API-008: How much source traceability is visible to teacher exports?
OQ-API-009: What is the exact Telegram pilot flow: internal endpoint or worker calls public delivery endpoint?
OQ-API-010: Which payment provider webhook is first?
OQ-API-011: What exact OpenAPI tooling supports 3.2.0 in the selected stack?
OQ-API-012: What privacy/legal constraints apply to learner attempts in EU public beta?
```

---

## 53. Reference Standards and Alignment

This API Standard aligns with:

```text
Stanford/SLAC-style requirements discipline:
- goal → requirements → use cases → tests → traceability → change control

OpenAPI Specification 3.2.0:
- formal HTTP API contract

JSON Schema Draft 2020-12:
- canonical data validation and schema vocabulary alignment

RFC 9110 HTTP Semantics:
- method semantics, status behavior and HTTP architecture

RFC 9457 Problem Details:
- machine-readable HTTP API errors

OAuth 2.0 / Bearer Token concepts:
- optional future authorization framework and bearer credential handling

OWASP API Security Top 10 2023:
- object-level authorization, object-property authorization, auth and resource abuse controls

Telegram Bot API:
- poll/quiz delivery compatibility

Git/GitHub-style engineering governance:
- contract tests, protected branches, CI checks and changelog discipline
```

Reference URLs:

```text
Stanford/SLAC Requirements Methodology:
https://www-group.slac.stanford.edu/cdsoft/nlc_arch/nlc_requirements/RequirementsMethod.pdf

OpenAPI Specification 3.2.0:
https://spec.openapis.org/oas/v3.2.0.html

OpenAPI latest:
https://spec.openapis.org/oas/latest.html

JSON Schema Draft 2020-12:
https://json-schema.org/draft/2020-12

RFC 9110 HTTP Semantics:
https://www.rfc-editor.org/rfc/rfc9110.html

RFC 9457 Problem Details:
https://www.rfc-editor.org/rfc/rfc9457.html

RFC 6749 OAuth 2.0 Authorization Framework:
https://www.rfc-editor.org/rfc/rfc6749.html

RFC 6750 OAuth 2.0 Bearer Token Usage:
https://www.rfc-editor.org/rfc/rfc6750.html

OWASP API Security Top 10 2023:
https://owasp.org/API-Security/editions/2023/en/0x11-t10/

Telegram Bot API:
https://core.telegram.org/bots/api
```

---

## 54. Final API Rule

API Quiz Bank is not API-ready because an endpoint returns a question.

API Quiz Bank is API-ready when the API can prove:

```text
what consumer made the request;
what that consumer is allowed to access;
which entitlement and quota decision applied;
which statuses were allowed;
which selection rules were applied;
why the item was eligible;
which delivery record was created;
what answer exposure policy applied;
what happened after the attempt;
which analytics changed;
which errors are machine-readable;
which contract describes the behavior;
which tests prove the behavior;
and how the next new source file can eventually produce the same governed API delivery path.
```

Final binding rule:

```text
No external consumer may receive quiz content unless the API can enforce status,
consumer authorization, entitlement/quota, projection safety, delivery traceability,
and contract-tested behavior.
```
