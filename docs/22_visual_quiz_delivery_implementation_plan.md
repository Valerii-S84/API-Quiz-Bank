# API Quiz Bank — Visual Quiz Delivery Implementation Audit and Plan

**Документ:** `docs/22_visual_quiz_delivery_implementation_plan.md`  
**Назва проєкту:** API Quiz Bank  
**Модуль:** Visual Quiz Delivery  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** implementation audit, execution plan, test plan and readiness checklist; subordinate to `CONSTITUTION.md`; derived from `docs/20_visual_quiz_delivery.md` and `docs/21_visual_quiz_delivery_product_charter.md`  
**Дата:** 2026-05-17  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized implementation maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/07_api_standard.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/11_billing_model.md`, `docs/18_telegram_delivery_playbook.md`, `docs/19_privacy_compliance.md`, `docs/20_visual_quiz_delivery.md`, `docs/21_visual_quiz_delivery_product_charter.md`  
**Наступні документи:** implementation PRs, migration plans, runbook updates and release evidence

---

## 0. Executive Summary

Visual Quiz Delivery треба реалізовувати як керований extension layer над існуючим MVP runtime, а не як окремий сервіс, який сам вибирає питання або напряму читає raw CSV.

Правильна implementation thesis:

```text
selection/API core stays the source of delivery truth
  -> visual settings and entitlement decide visual mode
  -> cache is checked before generation
  -> generation is bounded by quota and budget controls
  -> QA gates every image before publish
  -> Telegram sends image separately from quiz poll
  -> fallback to text_only is safe, logged and testable
```

Перший production-safe implementation target:

- зберегти поточний `text_only` flow без regressions;
- додати `image_standard` через deterministic prompt builder, cache, fake provider and QA;
- інтегрувати Telegram image + poll delivery тільки після того, як cache/QA/fallback працюють локально;
- додати OpenAI provider тільки behind explicit configuration, with no network calls in tests;
- не відкривати public self-service visual endpoints до появи auth, entitlement, quota and audit coverage.

---

## 1. Scope of This Document

### 1.1. Що цей документ робить

Цей документ визначає:

- audit поточного стану репозиторію щодо Visual Quiz Delivery;
- цільову runtime architecture;
- exact files/modules to create or change;
- database migration plan;
- API and internal service boundaries;
- Telegram delivery changes;
- billing, entitlement, quota and cache behavior;
- prompt builder, image generation provider and QA gates;
- test plan by phase;
- Definition of Done for each phase;
- final readiness checklist.

### 1.2. Що цей документ не робить

Цей документ не є:

- готовою migration або runtime implementation;
- дозволом на real OpenAI calls;
- дозволом на real Telegram send;
- public pricing page;
- legal/tax decision for paid launch;
- replacement for `CONSTITUTION.md`.

---

## 2. Constitutional Audit

### 2.1. Must Preserve

Visual Quiz Delivery MUST preserve these constitutional rules:

| Rule | Source | Implementation impact |
|---|---|---|
| API-first delivery | `CONSTITUTION.md`, section 4.1 | Visual module must call platform selection/API/service layer, not raw CSV. |
| Raw CSV is source asset, not product | `CONSTITUTION.md`, sections 4.2 and 7 | Prompt builder uses canonical quiz records, never `QuizBank/*.csv`. |
| No publication without status | `CONSTITUTION.md`, section 4.5 | Visual delivery inherits existing approved/published filtering. |
| Centralized selection | `CONSTITUTION.md`, section 4.6 | Visual module does not select items independently. |
| Entitlements, not vague payment | `CONSTITUTION.md`, section 4.8 | `image_standard` and `image_branded` require explicit entitlement/features. |
| Telegram compatibility | `CONSTITUTION.md`, section 5.8 | Image must remain separate from Telegram quiz poll mechanics. |
| Security and privacy boundaries | `docs/08_security_threat_model.md`, `docs/19_privacy_compliance.md` | Prompt, asset, target and branding data must be access-controlled and logged without leaking secrets. |

### 2.2. Conflicts Avoided

The implementation MUST NOT:

- add any path where website, bot, worker or visual provider reads raw CSV directly;
- let OpenAI output become trusted without local validation and QA state;
- publish generated images that reveal correct answer text when the policy says it is forbidden;
- treat cache hit as permission to bypass status, entitlement or consumer scope;
- reuse branded assets across consumers unless explicitly scoped and allowed;
- count failed generation as successful visual delivery;
- let visual generation failure block text quiz delivery when fallback policy allows `text_only`;
- log raw API keys, Telegram tokens, full target IDs or private branding payloads in public reports.

### 2.3. Current Compatibility Verdict

The product vision in `docs/20_visual_quiz_delivery.md` and `docs/21_visual_quiz_delivery_product_charter.md` is compatible with the main Constitution if implementation follows this plan.

The biggest risk is not product conflict; it is implementation drift. The module becomes non-compliant if it is implemented as:

```text
Telegram worker -> raw CSV -> OpenAI -> Telegram
```

The compliant path is:

```text
consumer/schedule
  -> existing selection and entitlement path
  -> visual mode decision
  -> cache/generation/QA
  -> Telegram adapter
  -> delivery, asset and cost logs
```

---

## 3. Current Repository Audit

### 3.1. Current Runtime Assets

| Area | Current files | Current state |
|---|---|---|
| FastAPI runtime | `src/quizbank_mvp/app.py` | Versioned `/v1/quiz-items/next`, `/v1/deliveries/{delivery_id}`, trusted item lookup and admin registration exist. |
| Selection core | `src/quizbank_mvp/selection.py`, `selection_quota.py`, `selection_eligibility.py`, `selection_scope_enforcement.py`, `selection_delivery.py` | Central selection enforces active consumer, `quiz_delivery` entitlement, quota, repeat policy and approved/published status through focused modules. |
| Projections | `src/quizbank_mvp/projections.py` | Public learner and Telegram quiz projections exist; answer key is hidden from public projection. |
| Telegram worker | `src/quizbank_mvp/telegram_delivery.py`, `telegram_payload.py`, `telegram_poll_validation.py`, `telegram_result_repository.py`, `telegram_visual_integration.py` | Orchestrates text or visual Telegram delivery; records Telegram and visual delivery results. |
| Database | `database/migrations/001_create_mvp_runtime.sql` through `009_add_image_quality_policy.sql`; `src/quizbank_mvp/database.py`, `database_connection.py`, `database_runtime.py`, `database_seed.py`, `database_status.py` | SQLite MVP schema and helpers are split by connection/runtime/seed/status responsibility; `database.py` remains a compatibility facade. |
| PostgreSQL target | `database/postgresql/*.sql` | Production-oriented schema path exists separately with runtime, import, delivery evidence, schedule, visual and image-quality mirror migrations. |
| Billing catalog | `data/billing/plan_catalog.json` | Seed catalog only includes `quiz_delivery`; no visual feature keys yet. |
| OpenAPI | `api/openapi.yaml` | Committed contract covers current runtime/admin paths; no visual endpoints yet. |
| Tests | `tests/test_mvp_runtime.py`, `tests/test_telegram_shuffle.py`, `tests/test_mvp_admin.py`, `tests/test_contract_schema_invariants.py`, others | Runtime, selection, Telegram and governance tests exist and should be extended, not replaced. |

### 3.2. Current Gaps

| Gap | Impact |
|---|---|
| No visual OpenAPI/admin contract | Cannot configure visual mode through governed admin/API surfaces. |
| No visual metrics/reporting | Cannot prove cost control, cache hit rate, fallback rate or quality rate. |

---

## 4. Target Architecture

### 4.1. Runtime Flow

```text
scheduled job or API request
  -> authenticate consumer
  -> existing quiz selection and quiz_delivery quota
  -> load visual settings
  -> evaluate visual entitlement and fallback policy
  -> if text_only: existing poll delivery
  -> if visual mode:
       build visual context from canonical quiz projection
       compute cache key
       return approved cached asset if present
       if no cache:
          check generation entitlement/quota/budget
          build prompt
          call image provider
          store asset candidate and prompt audit
          run QA
          approve or reject
       if approved asset:
          send image, then Telegram quiz poll
       else:
          use text_only fallback if policy allows
  -> record delivery, visual asset link, fallback state and metrics
```

### 4.2. Component Map

| Component | New or changed file | Responsibility |
|---|---|---|
| Visual types/contracts | `src/quizbank_mvp/visual_models.py` | Dataclasses/enums for delivery mode, QA status, fallback policy, visual settings and asset projection. |
| Visual settings service | `src/quizbank_mvp/visual_settings.py` | Load and validate consumer visual settings; default missing settings to `text_only`. |
| Visual entitlement/quota | `src/quizbank_mvp/visual_access.py` | Check `visual_delivery.standard`, `visual_delivery.branded`, `visual_generation` and visual quota limits. |
| Prompt builder | `src/quizbank_mvp/visual_prompt_builder.py` | Convert canonical quiz item into generation prompt without forbidden answer leakage. |
| Cache service | `src/quizbank_mvp/visual_cache.py` | Compute cache key, find approved asset, store candidates and mark QA status. |
| Provider interface | `src/quizbank_mvp/visual_provider.py` | Define `ImageGenerationProvider`, fake provider and later OpenAI provider. |
| QA service | `src/quizbank_mvp/visual_qa.py` | Deterministic checks and optional provider/vision QA decision wrapper. |
| Visual orchestration | `src/quizbank_mvp/visual_delivery.py` | Main service that resolves asset or fallback for a selected delivery. |
| Telegram integration | `src/quizbank_mvp/telegram_delivery.py` | Add image send path, media result recording and fallback logging. |
| API routes | `src/quizbank_mvp/app.py`, `src/quizbank_mvp/admin_api.py` | Add internal/admin visual settings and optional internal asset generation routes. |
| CLI/smoke | `src/quizbank_mvp/cli.py`, `tools/run_telegram_delivery_smoke.py`, new `tools/run_visual_delivery_smoke.py` | Seed visual settings and run dry-run visual delivery proof. |
| SQLite migrations | `database/migrations/008_add_visual_delivery.sql` | Add visual settings, assets, prompts, links and metrics tables. |
| PostgreSQL migrations | `database/postgresql/007_add_visual_delivery.sql` | Mirror visual runtime schema for target production DB. |
| OpenAPI seed | `api/openapi.yaml` | Add only the endpoints actually implemented. |
| Billing catalog | `data/billing/plan_catalog.json` | Add visual feature keys and limits as seed data. |

### 4.3. OpenAI Boundary

OpenAI image generation is an external provider behind `ImageGenerationProvider`.

Current official OpenAI docs describe two relevant choices:

- Image API for single prompt image generation or editing.
- Responses API image generation tool for conversational or multi-step image flows.

For this module, the first implementation SHOULD use the simpler Image API provider boundary for single prompt generation. Responses API MAY be added later if iterative editing or multimodal QA workflows are needed.

Implementation rules:

- tests use `FakeImageProvider`, never real OpenAI calls;
- real provider is disabled unless `VISUAL_IMAGE_PROVIDER=openai` and a secret source is configured;
- model/provider name is config, not hard-coded in business logic;
- `prompt_text`, provider response ID, output format, generated byte hash and usage/cost metadata are logged;
- API keys are never stored in DB and never printed;
- exact OpenAI model choice is verified against official docs during provider implementation.

References checked for this plan:

- OpenAI image generation guide: `https://developers.openai.com/api/docs/guides/image-generation`
- OpenAI Responses image generation tool guide: `https://developers.openai.com/api/docs/guides/tools-image-generation`
- OpenAI Images API reference: `https://developers.openai.com/api/reference/resources/images`

---

## 5. Data Model Plan

### 5.1. SQLite Migration

Create:

```text
database/migrations/008_add_visual_delivery.sql
```

Tables:

```text
consumer_visual_settings
visual_assets
visual_prompt_audit
visual_delivery_results
visual_usage_events
```

### 5.2. `consumer_visual_settings`

Purpose: consumer-scoped visual delivery configuration.

Fields:

```text
consumer_id TEXT PRIMARY KEY REFERENCES consumers(consumer_id)
delivery_mode TEXT NOT NULL CHECK (delivery_mode IN ('text_only', 'image_standard', 'image_branded'))
visual_style TEXT NOT NULL
branding_preset TEXT NOT NULL
fallback_policy TEXT NOT NULL CHECK (fallback_policy IN ('text_only', 'cache_only', 'block_visual_delivery'))
daily_visual_delivery_limit INTEGER NOT NULL
daily_generation_limit INTEGER NOT NULL
monthly_generation_limit INTEGER NOT NULL
is_active INTEGER NOT NULL CHECK (is_active IN (0, 1))
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

Done when:

- missing row means `text_only`;
- invalid mode/style/fallback is rejected by DB and service validation;
- setting is consumer-scoped and cannot be read or changed by another consumer.

### 5.3. `visual_assets`

Purpose: cache and lifecycle record for generated or imported visual assets.

Fields:

```text
asset_id TEXT PRIMARY KEY
quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id)
consumer_id TEXT REFERENCES consumers(consumer_id)
delivery_mode TEXT NOT NULL
visual_style TEXT NOT NULL
branding_preset TEXT NOT NULL
image_version TEXT NOT NULL
language TEXT NOT NULL
cache_key TEXT NOT NULL
image_path TEXT NOT NULL
image_sha256 TEXT NOT NULL
mime_type TEXT NOT NULL
width INTEGER NOT NULL
height INTEGER NOT NULL
qa_status TEXT NOT NULL CHECK (qa_status IN ('approved', 'rejected', 'fallback_used', 'needs_review'))
provider_name TEXT NOT NULL
provider_model TEXT NOT NULL
provider_asset_ref TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
UNIQUE(cache_key)
```

Cache key MUST include:

```text
quiz_item_id
delivery_mode
visual_style
branding_preset
image_version
language
consumer_scope_marker
```

For `image_branded`, `consumer_scope_marker` MUST include `consumer_id`.

### 5.4. `visual_prompt_audit`

Purpose: trace prompt generation without exposing secrets.

Fields:

```text
prompt_id TEXT PRIMARY KEY
asset_id TEXT REFERENCES visual_assets(asset_id)
quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id)
consumer_id TEXT REFERENCES consumers(consumer_id)
prompt_type TEXT NOT NULL
generated_prompt TEXT NOT NULL
negative_prompt TEXT NOT NULL
prompt_policy_version TEXT NOT NULL
provider_name TEXT NOT NULL
provider_model TEXT NOT NULL
provider_response_id TEXT
provider_revised_prompt TEXT
created_at TEXT NOT NULL
```

Done when:

- prompt can be traced to item, style and provider;
- no API key, token, chat ID or private customer credential is stored;
- prompt logs can be redacted for public reports.

### 5.5. `visual_delivery_results`

Purpose: link selected quiz delivery to visual asset and fallback state.

Fields:

```text
delivery_id TEXT PRIMARY KEY REFERENCES deliveries(delivery_id)
consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id)
asset_id TEXT REFERENCES visual_assets(asset_id)
requested_delivery_mode TEXT NOT NULL
resolved_delivery_mode TEXT NOT NULL
visual_status TEXT NOT NULL CHECK (visual_status IN ('sent', 'skipped', 'failed', 'fallback_used'))
fallback_used INTEGER NOT NULL CHECK (fallback_used IN (0, 1))
fallback_reason TEXT
telegram_image_message_id TEXT
recorded_at TEXT NOT NULL
```

Done when:

- every visual-mode delivery has exactly one visual delivery result;
- fallback is explicit and machine-readable;
- failed image send does not hide poll delivery outcome.

### 5.6. `visual_usage_events`

Purpose: cost, cache and quota metrics.

Fields:

```text
usage_event_id TEXT PRIMARY KEY
consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id)
delivery_id TEXT REFERENCES deliveries(delivery_id)
asset_id TEXT REFERENCES visual_assets(asset_id)
event_type TEXT NOT NULL CHECK (
    event_type IN (
        'cache_hit',
        'cache_miss',
        'generation_requested',
        'generation_succeeded',
        'generation_failed',
        'qa_approved',
        'qa_rejected',
        'fallback_used'
    )
)
feature TEXT NOT NULL
quantity INTEGER NOT NULL
estimated_cost_minor INTEGER NOT NULL
provider_name TEXT NOT NULL
created_at TEXT NOT NULL
```

Done when:

- cache hit rate can be calculated;
- generation count can be audited per consumer;
- cost estimate can be shown without external billing provider integration.

### 5.7. PostgreSQL Mirror

Create:

```text
database/postgresql/007_add_visual_delivery.sql
```

Done when:

- PostgreSQL schema mirrors SQLite semantics;
- tests or smoke tooling can validate table existence and key constraints;
- no production migration is applied without explicit deploy scope.

---

## 6. Entitlement, Quota and Billing Plan

### 6.1. Feature Keys

Add feature keys to billing catalog and entitlement checks:

```text
quiz_delivery
visual_delivery.standard
visual_delivery.branded
visual_generation.standard
visual_generation.branded
```

Rules:

- `text_only` requires only existing `quiz_delivery`;
- `image_standard` requires `quiz_delivery` plus `visual_delivery.standard`;
- `image_branded` requires `quiz_delivery` plus `visual_delivery.branded`;
- cache hit may require visual delivery entitlement but should not consume generation quota;
- cache miss requiring generation consumes visual generation quota if generation is attempted;
- no entitlement means fallback to `text_only` only if fallback policy explicitly allows it.

### 6.2. Quota Policy

Keep existing `quota_usage` for base quiz delivery. Add visual quota through either:

1. `quota_usage.feature` values such as `visual_generation.standard`; and
2. limits from `consumer_visual_settings`.

Do not overload `consumers.daily_quota_limit` for visual generation. It remains the base quiz delivery quota.

### 6.3. Billing Catalog Update

Update:

```text
data/billing/plan_catalog.json
```

Add seed plans/features:

```text
manual_visual_demo:
  quiz_delivery: 2/day
  visual_delivery.standard: 2/day
  visual_generation.standard: 2/day

visual_pilot:
  quiz_delivery: configured/day
  visual_delivery.standard: configured/day
  visual_generation.standard: configured/day or month

pro_visual_pilot:
  visual_delivery.branded
  visual_generation.branded
  branding_preset access
```

Done when:

- tests confirm existing plans still include `quiz_delivery`;
- new visual plans include explicit feature codes and limit periods;
- no pricing claim is made as implemented revenue without billing runtime support.

---

## 7. Prompt Builder Plan

### 7.1. Inputs

Prompt builder receives canonical, governed item data:

```text
quiz_item_id
question text
options
correct answer metadata
cefr_level
theme_id/title
objective_id/title
pattern_id/title
visual_style
branding_preset
delivery_mode
language
```

It MUST NOT read raw CSV.

### 7.2. Output

Prompt builder emits:

```text
generated_prompt
negative_prompt
visualization_type
answer_leak_risk
prompt_policy_version
fallback_recommendation
```

### 7.3. Answer-Leak Policy

Rules:

- If prompt contains exact correct answer text and question type forbids visual clue, mark `needs_review` or fallback.
- If vocabulary item intentionally visualizes the concept, allow only when visualization policy says direct object image is safe.
- Do not ask image provider to render option labels, answer letters or full answer text unless explicitly approved for a learning-card format.
- Prefer scenes without embedded text.
- For grammar, sentence building and abstract questions, prefer contextual or neutral scenes.

### 7.4. Tests

Create:

```text
tests/test_visual_prompt_builder.py
```

Required tests:

- direct vocabulary prompt does not include option labels;
- grammar prompt avoids exact answer text;
- branded prompt includes style preset marker but not private customer secrets;
- unsupported abstract prompt returns fallback recommendation;
- prompt builder is deterministic for the same item/settings;
- prompt policy version is present.

Done when all prompt builder tests pass without OpenAI/network.

---

## 8. Cache and Asset Plan

### 8.1. Storage

Initial local storage:

```text
var/visual-assets/{asset_id}.{png|webp|jpeg}
```

Rules:

- DB stores path, hash, dimensions, mime type and status;
- DB does not store large base64 image payloads;
- path must remain under configured visual asset root;
- path traversal is rejected;
- asset file is written only after provider result passes basic validation.

### 8.2. Cache Lookup

Cache lookup order:

```text
1. Compute cache key from quiz item + visual settings.
2. Query visual_assets where cache_key matches and qa_status = approved.
3. Confirm image file exists and hash matches DB.
4. Return asset.
5. If missing/corrupt, mark event and treat as cache miss.
```

### 8.3. Tests

Create:

```text
tests/test_visual_cache.py
```

Required tests:

- same settings produce same cache key;
- different branding preset changes cache key;
- `image_branded` includes consumer scope;
- approved asset is reused;
- rejected or needs_review asset is not reused;
- missing file invalidates cache hit;
- image path outside asset root is rejected.

---

## 9. Provider Plan

### 9.1. Provider Interface

Create:

```text
class ImageGenerationProvider:
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        ...
```

Request fields:

```text
prompt
negative_prompt
size
quality
output_format
style_context
idempotency_key
```

Result fields:

```text
provider_name
provider_model
provider_response_id
revised_prompt
image_bytes
mime_type
usage
```

### 9.2. Fake Provider First

Implement `FakeImageProvider` first.

Done when:

- visual pipeline can run end-to-end without network;
- tests assert all DB records, cache events and fallback paths;
- no secret configuration is required for tests.

### 9.3. OpenAI Provider Later

Implement `OpenAIImageProvider` only after fake-provider pipeline is green.

Files:

```text
src/quizbank_mvp/visual_provider_openai.py
```

Rules:

- no real call unless `VISUAL_IMAGE_PROVIDER=openai`;
- API key from environment or approved secret file path only;
- never print API key;
- timeout and error mapping are explicit;
- provider errors return structured failure for fallback;
- exact model and endpoint are config-driven and checked against official OpenAI docs at implementation time.

Dependency decision:

- If using the official Python SDK, update `pyproject.toml` in that implementation PR and run dependency-aware checks.
- If avoiding new dependency, implement narrow HTTP client with `urllib.request`, explicit timeout and JSON schema validation.

The recommended implementation route is official SDK if dependency change is approved, because it reduces hand-written API surface and response parsing risk.

### 9.4. Tests

Create:

```text
tests/test_visual_provider.py
```

Required tests:

- fake provider returns deterministic image bytes;
- provider failure maps to `generation_failed`;
- OpenAI provider is not constructed without explicit config;
- secret values do not appear in exception text;
- image result with unsupported mime type is rejected;
- provider timeout triggers fallback path.

No test may call the real OpenAI API.

---

## 10. Visual QA Plan

### 10.1. MVP QA

MVP QA is deterministic and conservative:

- prompt policy check;
- image bytes and mime type check;
- dimensions check;
- cache hash check;
- answer-leak text policy check on prompt and revised prompt;
- style preset presence check;
- manual `needs_review` option for uncertain categories.

### 10.2. Later QA

Later phases MAY add vision-based QA with a model/provider, but that is not required for first MVP.

If model-based QA is added:

- output is treated as untrusted;
- decision schema is validated;
- uncertain result becomes `needs_review` or fallback;
- no generated image is published solely because a model says it is good.

### 10.3. Tests

Create:

```text
tests/test_visual_qa.py
```

Required tests:

- approved image passes deterministic checks;
- empty bytes rejected;
- wrong mime type rejected;
- prompt with forbidden exact answer text rejected for grammar mode;
- revised prompt containing forbidden option text is rejected;
- uncertain result becomes `needs_review`;
- fallback reason is machine-readable.

---

## 11. Visual Orchestration Plan

### 11.1. Service Contract

Create:

```text
src/quizbank_mvp/visual_delivery.py
```

Main function:

```text
resolve_visual_delivery(
    db_path,
    delivery,
    quiz_item,
    consumer_id,
    provider,
) -> VisualDeliveryResolution
```

Resolution states:

```text
text_only
cache_hit
generated_approved
fallback_used
blocked
needs_review
generation_failed
qa_rejected
```

### 11.2. Decision Order

```text
1. Load settings.
2. If inactive or missing -> text_only.
3. If delivery_mode is text_only -> text_only.
4. Check visual entitlement.
5. If entitlement missing -> fallback or blocked.
6. Compute cache key.
7. If approved cache hit -> cache_hit.
8. If fallback policy is cache_only -> fallback.
9. Check visual generation quota.
10. Build prompt.
11. Generate image through provider.
12. Store candidate asset and prompt audit.
13. Run QA.
14. If approved -> generated_approved.
15. If rejected/failed -> fallback or blocked.
16. Record visual_usage_events.
```

### 11.3. Tests

Create:

```text
tests/test_visual_delivery.py
```

Required tests:

- missing visual settings returns text_only;
- `image_standard` with cache hit does not call provider;
- cache miss calls provider once and stores approved asset;
- generation failure falls back to text_only;
- QA rejection falls back and records fallback reason;
- `cache_only` policy does not call provider;
- no visual entitlement blocks visual generation;
- branded mode requires branded entitlement;
- visual generation quota exhausted uses fallback;
- base `quiz_delivery` quota still controls selection before visual pipeline.

---

## 12. API and Admin Plan

### 12.1. Admin Settings First

Initial settings must be admin-only.

Add routes:

```text
GET   /v1/admin/consumers/{consumer_id}/visual-settings
PATCH /v1/admin/consumers/{consumer_id}/visual-settings
```

Files:

```text
src/quizbank_mvp/admin_api.py
src/quizbank_mvp/admin_service.py
api/openapi.yaml
tests/test_mvp_admin.py
```

Rules:

- owner can change visual settings;
- read-only reviewer can read only if current admin read policy allows consumer reads;
- content admin cannot change visual settings unless explicitly allowed;
- PATCH validates enum values and numeric limits;
- all changes write `audit_log`.

### 12.2. Internal Generation Endpoint

Do not add public generation endpoint first.

If needed for internal worker:

```text
POST /v1/internal/visual-assets/generate
```

Requirements:

- internal/admin auth only;
- idempotency key required;
- no public unauthenticated access;
- must not select quiz item directly from raw input;
- must reference an existing delivery or approved/published quiz item visible to consumer.

### 12.3. Public API Later

Public endpoints MAY be added only after:

- auth model is clear;
- visual quota and entitlement are proven;
- OpenAPI has request/response schemas;
- abuse/rate-limit rules exist;
- tests prove cross-consumer isolation.

### 12.4. Tests

Extend:

```text
tests/test_mvp_admin.py
tests/test_contract_schema_invariants.py
```

Required tests:

- app route exists and is reflected in `api/openapi.yaml`;
- owner can set `image_standard`;
- invalid `delivery_mode` rejected;
- non-owner cannot modify settings;
- cross-consumer access denied;
- audit row written for settings change.

---

## 13. Telegram Integration Plan

### 13.1. Current State

Current Telegram delivery modules:

- selects item through `select_next_item`;
- builds quiz poll payload through `telegram_payload.py`;
- validates poll constraints through `telegram_poll_validation.py`;
- resolves visual/image delivery through `telegram_visual_integration.py`;
- supports `dry_run` and `real`;
- adapter supports poll and image send paths;
- records `telegram_delivery_results` and visual delivery results.

### 13.2. Implemented Direction

The current implementation uses the integrated delivery path:

```text
TelegramAdapter.send_photo(payload)
TelegramImageSendResult
build_telegram_image_payload(...)
visual_delivery_result recording
```

`run_telegram_delivery` consults visual settings and keeps `text_only`
behavior as the default/fallback-compatible path.

### 13.3. Send Order

```text
1. Select delivery.
2. Resolve visual asset.
3. If approved asset:
   - send image as separate Telegram message;
   - send quiz poll;
   - record image message ID and poll message ID.
4. If image send fails:
   - record visual failure;
   - send quiz poll if fallback policy allows.
5. If poll send fails:
   - record poll failure;
   - do not count visual delivery as successful.
```

### 13.4. Telegram Payload Rules

- image contains no answer options as embedded text unless future policy explicitly allows it;
- quiz mechanics remain in Telegram poll;
- correct option remains hidden from public API but available to Telegram worker because Telegram quiz requires it;
- Telegram target is redacted in logs as today;
- fallback is visible in `visual_delivery_results`.

### 13.5. Tests

Extend:

```text
tests/test_mvp_runtime.py
tests/test_telegram_shuffle.py
```

Create if needed:

```text
tests/test_visual_telegram_delivery.py
```

Required tests:

- text-only consumer uses existing poll path;
- image_standard dry-run records skipped image and skipped poll without network;
- approved cache asset sends image before poll in fake adapter;
- image send failure falls back to poll;
- poll failure records failed delivery;
- correct answer still not in image payload;
- target redaction still works;
- repeat policy still blocks same item for same Telegram target after successful send.

---

## 14. OpenAPI and Contract Plan

### 14.1. Update OpenAPI Only for Implemented Routes

Update:

```text
api/openapi.yaml
```

Add schemas:

```text
VisualDeliveryMode
VisualFallbackPolicy
VisualSettings
VisualSettingsUpdateRequest
VisualAssetProjection
VisualDeliveryResult
```

Add paths only when route exists:

```text
/v1/admin/consumers/{consumer_id}/visual-settings
/v1/internal/visual-assets/generate
```

Do not document public visual generation as available until implemented and protected.

### 14.2. Tests

Extend:

```text
tests/test_contract_schema_invariants.py
tests/test_mvp_runtime.py
tests/test_mvp_admin.py
```

Done when:

- every new app path appears in committed OpenAPI;
- public projection still does not expose `answer_key`;
- visual asset projection does not expose provider secrets or raw prompt logs unless admin/internal.

---

## 15. CLI, Tools and Smoke Plan

### 15.1. CLI

Extend:

```text
src/quizbank_mvp/cli.py
```

Commands:

```text
seed-visual-settings
show-visual-settings
visual-cache-report
```

Rules:

- no real OpenAI call from CLI unless explicit `--approve-real-generation`;
- no real Telegram send unless existing `--approve-real-send`;
- generated local files go under `var/visual-assets/`.

### 15.2. Smoke Tool

Create:

```text
tools/run_visual_delivery_smoke.py
```

Modes:

```text
dry_run_text_only
dry_run_cache_miss_fake_provider
dry_run_cache_hit
dry_run_provider_failure_fallback
```

Done when:

- smoke output is JSON;
- output includes delivery ID, requested/resolved visual mode, asset ID or fallback reason;
- output redacts target and secrets;
- report can be committed later under `reports/` only when requested.

---

## 16. Observability and Metrics Plan

### 16.1. Required Metrics

Track through DB first:

```text
visual_cache_hits_total
visual_cache_misses_total
visual_generation_requests_total
visual_generation_failures_total
visual_qa_rejections_total
visual_fallback_used_total
visual_delivery_sent_total
visual_estimated_cost_minor_total
```

### 16.2. Admin Dashboard Later

Extend admin dashboard after core runtime is green:

- visual settings count by mode;
- cache hit rate;
- fallback rate;
- generation count by consumer;
- QA rejection count;
- estimated cost by consumer.

### 16.3. Tests

Required tests:

- metrics events are written for cache hit;
- metrics events are written for generation failure;
- fallback event includes reason code;
- no secrets in metric payload.

---

## 17. Step-by-Step Execution Plan

### Phase 0 — Pre-Implementation Gate

Files:

```text
docs/22_visual_quiz_delivery_implementation_plan.md
```

Actions:

1. Confirm this plan is accepted.
2. Create a feature branch for implementation if not already on an appropriate branch.
3. Run baseline tests:
   - `python3 -m unittest discover -s tests -p "test_*.py"`
4. Do not add OpenAI dependency or real secret wiring in Phase 0.

Done:

- baseline test status known;
- no runtime code changed;
- implementation scope split into PR-sized phases.

### Phase 1 — Data Contracts and Migrations

Files:

```text
database/migrations/008_add_visual_delivery.sql
database/postgresql/007_add_visual_delivery.sql
src/quizbank_mvp/database.py
src/quizbank_mvp/database_connection.py
src/quizbank_mvp/database_runtime.py
src/quizbank_mvp/database_seed.py
tests/test_visual_database.py
tests/test_postgresql_contract.py
```

Actions:

1. Add SQLite visual tables.
2. Add PostgreSQL mirror migration.
3. Update `database_is_ready` only if visual tables are required for runtime startup; otherwise add a separate visual readiness check.
4. Add seed/helper functions for visual settings and visual assets.
5. Add DB tests for constraints, defaults and foreign keys.

Done:

- migrations are idempotent;
- invalid visual mode rejected;
- `image_branded` cache key can be consumer-scoped;
- SQLite and PostgreSQL schemas align.

### Phase 2 — Visual Settings and Access

Files:

```text
src/quizbank_mvp/visual_models.py
src/quizbank_mvp/visual_settings.py
src/quizbank_mvp/visual_access.py
src/quizbank_mvp/database.py
data/billing/plan_catalog.json
tests/test_visual_settings.py
tests/test_visual_access.py
tests/test_contract_schema_invariants.py
```

Actions:

1. Define enums and validation.
2. Implement missing settings -> `text_only`.
3. Implement admin/seed helper for settings.
4. Add visual feature keys to billing catalog.
5. Implement visual entitlement checks separate from base `quiz_delivery`.
6. Implement visual quota checks using `quota_usage.feature`.

Done:

- text-only behavior preserved without visual settings;
- standard and branded modes require correct entitlements;
- generation quota and visual delivery quota can be checked independently;
- tests cover missing, invalid, allowed and denied states.

### Phase 3 — Prompt Builder, Cache and QA Without Network

Files:

```text
src/quizbank_mvp/visual_prompt_builder.py
src/quizbank_mvp/visual_cache.py
src/quizbank_mvp/visual_provider.py
src/quizbank_mvp/visual_qa.py
src/quizbank_mvp/visual_delivery.py
tests/test_visual_prompt_builder.py
tests/test_visual_cache.py
tests/test_visual_provider.py
tests/test_visual_qa.py
tests/test_visual_delivery.py
```

Actions:

1. Implement deterministic prompt builder.
2. Implement cache key and approved-asset lookup.
3. Implement fake provider.
4. Implement deterministic QA.
5. Implement visual orchestration function.
6. Store prompt audit, asset and usage events.

Done:

- full visual pipeline runs with fake provider only;
- cache hit prevents provider call;
- provider failure falls back;
- QA rejection falls back;
- no network or external secrets needed.

### Phase 4 — Admin API and OpenAPI

Files:

```text
src/quizbank_mvp/admin_api.py
src/quizbank_mvp/admin_service.py
api/openapi.yaml
tests/test_mvp_admin.py
tests/test_contract_schema_invariants.py
```

Actions:

1. Add admin visual settings GET/PATCH.
2. Add request/response schemas.
3. Add audit log writes.
4. Update committed OpenAPI.
5. Add tests for route reflection, auth and validation.

Done:

- owner can configure visual settings;
- unauthorized/admin-limited actors cannot mutate settings;
- committed OpenAPI matches app routes;
- settings changes are audited.

### Phase 5 — Telegram Visual Delivery

Files:

```text
src/quizbank_mvp/telegram_delivery.py
src/quizbank_mvp/visual_delivery.py
tools/run_telegram_delivery_smoke.py
tools/run_visual_delivery_smoke.py
tests/test_visual_telegram_delivery.py
tests/test_mvp_runtime.py
```

Actions:

1. Add adapter support for image send.
2. Add visual resolution to Telegram delivery path.
3. Preserve existing text-only behavior.
4. Record `visual_delivery_results`.
5. Make image failure fall back to poll when allowed.
6. Update smoke tooling for visual dry-run.

Done:

- text-only Telegram tests still pass;
- image_standard fake dry-run produces visual result;
- image send failure does not lose quiz poll;
- fallback state is recorded;
- repeat guard still works.

### Phase 6 — OpenAI Provider Behind Feature Flag

Files:

```text
src/quizbank_mvp/visual_provider_openai.py
pyproject.toml
tools/run_visual_delivery_smoke.py
tests/test_visual_provider.py
```

Actions:

1. Decide SDK vs narrow HTTP client.
2. Add dependency only if approved for the implementation PR.
3. Implement provider with timeout and structured errors.
4. Add env/file secret loading without printing secrets.
5. Add dry-run protection and `--approve-real-generation`.
6. Add tests with mocked provider client only.

Done:

- no unit test performs real network call;
- real generation requires explicit config and approval flag;
- provider failures trigger fallback;
- generated bytes are stored and hashed.

### Phase 7 — Reports, Metrics and Readiness Evidence

Files:

```text
src/quizbank_mvp/admin_service.py
tools/run_visual_delivery_smoke.py
reports/...
docs/10_operations.md
docs/18_telegram_delivery_playbook.md
docs/22_visual_quiz_delivery_implementation_plan.md
```

Actions:

1. Add visual summary to admin dashboard or report tooling.
2. Add visual delivery dry-run evidence report only when requested.
3. Update operations/runbook docs when runtime behavior exists.
4. Run full suite and smoke commands.

Done:

- cache hit rate, fallback rate and generation count visible;
- dry-run evidence exists;
- no production claim without real controlled evidence.

---

## 18. Test Coverage Matrix

| Area | Test file | Required coverage |
|---|---|---|
| DB migrations | `tests/test_visual_database.py` | tables, constraints, idempotency, foreign keys |
| Visual settings | `tests/test_visual_settings.py` | defaults, validation, consumer scope |
| Entitlement/quota | `tests/test_visual_access.py` | standard/branded features, quota exhausted, cache-only |
| Prompt builder | `tests/test_visual_prompt_builder.py` | no answer leak, deterministic prompts, style policy |
| Cache | `tests/test_visual_cache.py` | key composition, approved-only reuse, file hash validation |
| Provider | `tests/test_visual_provider.py` | fake provider, failure mapping, no secret leakage |
| QA | `tests/test_visual_qa.py` | approve/reject/needs_review/fallback decisions |
| Orchestration | `tests/test_visual_delivery.py` | cache hit, cache miss, generation, fallback, quota |
| Telegram | `tests/test_visual_telegram_delivery.py` | image + poll, image failure fallback, text-only unchanged |
| Admin API | `tests/test_mvp_admin.py` | settings read/write auth and audit |
| Runtime API | `tests/test_mvp_runtime.py` | current endpoints remain green |
| OpenAPI | `tests/test_contract_schema_invariants.py` | route/schema reflection, no answer key exposure |
| Full regression | `python3 -m unittest discover -s tests -p "test_*.py"` | entire repo remains green |

---

## 19. Global Definition of Done

Visual Quiz Delivery is implementation-done only when all items below are true:

- `text_only` delivery remains unchanged and tested.
- `image_standard` works end-to-end with fake provider and dry-run Telegram.
- `image_branded` is supported as settings/entitlement/cache-scope even if public sales remain disabled.
- approved/published item status filtering is inherited from selection core.
- no raw CSV access exists in visual modules.
- cache is mandatory and uses a deterministic key.
- branded cache is consumer-scoped.
- visual generation quota is separate from base quiz delivery quota.
- fallback to `text_only` is logged and tested.
- prompt audit exists.
- visual asset QA state exists.
- Telegram image and poll are separate payloads.
- all new endpoints are versioned and auth-protected.
- OpenAPI matches implemented routes.
- no unit test calls OpenAI or Telegram network.
- full `unittest discover` passes.
- operations docs/runbooks are updated before external pilot.

---

## 20. Readiness Checklist

### 20.1. Code Readiness

- [ ] Visual DB migrations exist for SQLite.
- [ ] Visual DB migrations exist for PostgreSQL target.
- [ ] Visual settings service exists.
- [ ] Visual access service exists.
- [ ] Visual prompt builder exists.
- [ ] Visual cache service exists.
- [ ] Visual provider interface exists.
- [ ] Fake image provider exists.
- [ ] Visual QA service exists.
- [ ] Visual orchestration service exists.
- [ ] Telegram adapter supports image + poll.
- [ ] Admin settings routes exist.
- [ ] OpenAPI is updated.
- [ ] CLI/smoke tool exists.

### 20.2. Safety Readiness

- [ ] No visual module reads raw CSV.
- [ ] No visual module bypasses selection engine.
- [ ] No generated image publishes without QA status.
- [ ] No branded asset can leak across consumers.
- [ ] No correct answer is embedded in image unless policy explicitly allows it.
- [ ] No OpenAI secret is stored in DB or logs.
- [ ] No Telegram token is logged.
- [ ] Provider failures produce fallback, not crash.
- [ ] Quota exhausted produces fallback or denial per policy.
- [ ] Public endpoints are not added before auth and quota tests.

### 20.3. Test Readiness

- [ ] Visual database tests pass.
- [ ] Visual settings tests pass.
- [ ] Visual access/quota tests pass.
- [ ] Prompt builder tests pass.
- [ ] Cache tests pass.
- [ ] Provider tests pass without network.
- [ ] QA tests pass.
- [ ] Visual orchestration tests pass.
- [ ] Telegram visual tests pass.
- [ ] Admin route tests pass.
- [ ] OpenAPI invariant tests pass.
- [ ] Full unittest suite passes.

### 20.4. Pilot Readiness

- [ ] Dry-run visual delivery proof exists.
- [ ] Cache hit proof exists.
- [ ] Fallback proof exists.
- [ ] One controlled real image generation is approved and documented.
- [ ] One controlled Telegram visual delivery is approved and documented.
- [ ] Cost estimate is recorded.
- [ ] Visual quota behavior is demonstrated.
- [ ] Operator knows how to disable visual generation.
- [ ] Rollback path is documented.

### 20.5. Production Readiness

- [ ] Legal/privacy review covers visual prompts, assets and branded styles.
- [ ] Billing plan/entitlement mapping is reviewed.
- [ ] Monitoring covers failures, cache rate and cost.
- [ ] Backup/restore includes visual tables and asset storage.
- [ ] Incident runbook covers wrong image, answer leak, customer branding leak and provider outage.
- [ ] Public claims match implemented behavior.
- [ ] No production deployment happens without explicit release gate.

---

## 21. First Implementation PR Recommendation

The first implementation PR should be deliberately narrow:

```text
Add visual DB schema + settings service + fake-provider visual delivery service.
Do not add OpenAI.
Do not change real Telegram send.
Do not expose public endpoints.
```

Recommended first PR files:

```text
database/migrations/008_add_visual_delivery.sql
src/quizbank_mvp/visual_models.py
src/quizbank_mvp/visual_settings.py
src/quizbank_mvp/visual_cache.py
src/quizbank_mvp/visual_prompt_builder.py
src/quizbank_mvp/visual_provider.py
src/quizbank_mvp/visual_qa.py
src/quizbank_mvp/visual_delivery.py
tests/test_visual_settings.py
tests/test_visual_cache.py
tests/test_visual_prompt_builder.py
tests/test_visual_provider.py
tests/test_visual_qa.py
tests/test_visual_delivery.py
```

First PR done criteria:

- fake visual delivery can produce an approved local asset;
- cache hit prevents second generation;
- QA rejection and provider failure fall back;
- no existing MVP runtime tests regress.
