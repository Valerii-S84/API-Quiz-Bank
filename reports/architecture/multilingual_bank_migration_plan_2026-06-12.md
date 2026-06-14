# Multilingual Content Bank Migration Plan

Дата: 2026-06-12  
Scope: implementation roadmap only. No migration executed.

## 1. Goal

Enable first-class support for:

- `language_code`;
- `content_bank_id`;
- `bank_version_id`;
- default German-only production content on phase 1;
- future `de`, `en`, `fr`, `es`, `nl`;
- complete content-bank replacement without deleting old questions;
- rollback to previous active bank version.

## 2. Migration Principles

1. No mass deletion of old quiz rows.
2. Existing clients remain compatible: missing `language_code` means `de`.
3. Existing German corpus is backfilled into a single default German content bank and active version.
4. Selection must never read from unscoped global `quiz_items` once bank/version fields exist.
5. Delivery and selection evidence must persist the exact bank version used.
6. Import writes only into draft or audit bank versions.
7. Activation is a transaction and is audited.
8. Rollback is activation of a previous version, not restore from backup.

## 3. Target First-Stage State

Seed rows:

```text
languages:
  de active
  en inactive
  fr inactive
  es inactive
  nl inactive

content_banks:
  german-core, language_code=de, status=active

content_bank_versions:
  german-core / 2026-06-12-baseline, status=active
```

Existing `QuizBank` rows:

```text
language_code = de
content_bank_id = german-core id
bank_version_id = german-core active baseline version id
```

## 4. Database Migration Plan

### Phase DB-1: Reference Tables

Add tables to both SQLite MVP and PostgreSQL contract:

```text
languages
content_banks
content_bank_versions
content_bank_activation_events
```

PostgreSQL indexes:

```text
UNIQUE (language_code, slug) on content_banks
UNIQUE (content_bank_id, version) on content_bank_versions
UNIQUE (content_bank_id) WHERE status = 'active' on content_bank_versions
INDEX content_bank_versions(content_bank_id, status, activated_at)
```

SQLite equivalent:

- normal unique indexes;
- active uniqueness enforced in service code or with SQLite partial unique index if supported by runtime version.

### Phase DB-2: Backfill German Defaults

Transactional steps:

1. Insert `languages` rows.
2. Insert default German content bank.
3. Insert baseline active version.
4. Add nullable scope columns to existing tables.
5. Backfill current rows to `de` and baseline version.
6. Validate no nulls remain in critical tables.
7. Add `NOT NULL` where safe.

Critical backfill targets:

```text
sources.language_code
sources.content_bank_id
sources.bank_version_id
quiz_items.language_code
quiz_items.content_bank_id
quiz_items.bank_version_id
deliveries.language_code
deliveries.content_bank_id
deliveries.bank_version_id
selection_decisions.language_code
selection_decisions.content_bank_id
selection_decisions.bank_version_id
import_batches.language_code
import_batches.content_bank_id
import_batches.bank_version_id
scheduled_delivery_slots.language_code
scheduled_delivery_slots.content_bank_id
scheduled_delivery_slots.bank_version_id
visual_assets.language_code
visual_assets.content_bank_id
visual_assets.bank_version_id
visual_prompt_audit.language_code
visual_prompt_audit.content_bank_id
visual_prompt_audit.bank_version_id
visual_usage_events.language_code
visual_usage_events.content_bank_id
visual_usage_events.bank_version_id
```

Optional or metadata-only targets:

```text
telegram_delivery_results: can inherit from deliveries
visual_delivery_results: can inherit from deliveries
quiz_item_image_quality_policy: add scope only if quiz item IDs become bank-local
audit_log: add metadata_json or scope columns for bank activation/import events
```

Validation SQL examples:

```sql
SELECT COUNT(*) FROM quiz_items WHERE language_code IS NULL OR bank_version_id IS NULL;
SELECT language_code, COUNT(*) FROM quiz_items GROUP BY language_code;
SELECT bank_version_id, COUNT(*) FROM quiz_items GROUP BY bank_version_id;
```

Expected first-stage result:

```text
quiz_items language_code distribution: de = current runtime item count
content_bank_versions active: exactly 1 for german-core
```

### Phase DB-3: Index Updates

Replace selection indexes:

Current:

```text
idx_quiz_items_selection_pool(status, sublevel, theme_id, objective_id, pattern_id, item_id)
idx_quiz_items_cell_lookup(theme_id, pattern_id, item_id)
```

Required:

```text
idx_quiz_items_selection_pool(
  language_code,
  bank_version_id,
  status,
  sublevel,
  theme_id,
  objective_id,
  pattern_id,
  item_id
)

idx_quiz_items_cell_lookup(
  language_code,
  bank_version_id,
  theme_id,
  pattern_id,
  item_id
)
```

Delivery/history indexes:

```text
idx_deliveries_scope_item(
  consumer_id,
  language_code,
  bank_version_id,
  delivery_status,
  quiz_item_id
)

idx_selection_decisions_scope_created(
  consumer_id,
  language_code,
  bank_version_id,
  created_at
)
```

Quota uniqueness:

Preferred long-term:

```text
quota_usage(
  consumer_id,
  feature,
  usage_date,
  language_code,
  content_bank_id,
  bank_version_id nullable,
  quota_scope_hash nullable
)
```

Unique key:

```text
UNIQUE (
  consumer_id,
  feature,
  usage_date,
  language_code,
  content_bank_id,
  COALESCE(bank_version_id, ''),
  COALESCE(quota_scope_hash, '')
)
```

SQLite note: if expression unique indexes are avoided, store normalized empty-string columns for nullable scope keys.

Scheduled slot uniqueness:

```text
UNIQUE (
  consumer_id,
  channel_id,
  delivery_date,
  slot_id,
  language_code,
  content_bank_id,
  bank_version_id,
  theme_id,
  cefr_level
)
```

Visual cache:

```text
cache_key must include language_code + content_bank_id + bank_version_id
```

### Phase DB-4: FK Strategy for Quiz Items

Current risk:

- `quiz_items.item_id` is a primary key.
- If a new bank version reuses source item IDs, direct import will collide.

Two viable strategies:

Option A, short-term:

- keep `item_id` globally unique;
- import generates bank-version-prefixed item IDs;
- add `source_item_id` for original row id.

Option B, cleaner long-term:

- introduce internal row key;
- make `(bank_version_id, source_item_id)` unique;
- update FKs from deliveries/assets/policies to internal key or composite reference.

Recommended path:

- Phase 1 uses Option A to reduce migration blast radius.
- Phase 2 designs full `quiz_item_versions` and `quiz_options` model if item-level edits need independent versioning beyond bank versioning.

## 5. Runtime Resolution Plan

Add a resolver:

```text
resolve_content_scope(request, consumer)
  → language_code
  → content_bank_id
  → bank_version_id
```

Resolution order:

1. Explicit request `language_code`, else consumer default, else `de`.
2. Explicit `bank_version_id` only if caller is authorized.
3. Explicit `content_bank_id` resolves active version for that bank.
4. Consumer default bank/version.
5. Active bank version for resolved language.

Failure modes:

- unknown language: `400 LANGUAGE_UNSUPPORTED`;
- inactive language: `403 LANGUAGE_NOT_ACTIVE`;
- no active bank version: `404 BANK_VERSION_NOT_AVAILABLE`;
- consumer not allowed for language/bank: `403 ENTITLEMENT_SCOPE_DENIED`.

## 6. Selection Logic Change Plan

Files:

- `src/quizbank_mvp/selection_models.py`
- `src/quizbank_mvp/selection_scope.py`
- `src/quizbank_mvp/selection_scope_enforcement.py`
- `src/quizbank_mvp/selection_eligibility.py`
- `src/quizbank_mvp/selection_diagnostics.py`
- `src/quizbank_mvp/selection_decision_log.py`
- `src/quizbank_mvp/selection_delivery.py`
- `src/quizbank_mvp/selection_quota.py`
- `src/quizbank_mvp/selection.py`

Steps:

1. Add scope fields to `SelectionFilters` or a separate `ContentScope` dataclass.
2. Resolve defaults before eligibility SQL.
3. Enforce consumer and entitlement language/bank scope.
4. Add `qi.language_code = ?` and `qi.bank_version_id = ?` to candidate SQL.
5. Add same scope to `candidate_count`, `non_deliverable_status_count`, `repeat_policy_block_count`.
6. Store scope in `selection_decisions`.
7. Store scope in `deliveries`.
8. Include scope in public selection metadata if safe.

Repeat policy:

- default: no repeat inside same `consumer_id + language_code + bank_version_id`;
- optional policy: no repeat across bank versions by content hash for channels that should not repeat replacement-bank duplicates.

## 7. API Change Plan

Files:

- `src/quizbank_mvp/app.py`
- `api/openapi.yaml`
- `api/openapi.template.yaml`
- `src/quizbank_mvp/projections.py`
- `src/quizbank_mvp/taxonomy.py`

Request additions:

```json
{
  "language_code": "de",
  "content_bank_id": "cb_...",
  "bank_version_id": "cbv_..."
}
```

Backward compatibility:

- fields optional;
- if missing, API behaves as today with `de` and active German bank;
- response always includes resolved scope once migration is complete.

Response additions:

```json
{
  "language_code": "de",
  "content_bank_id": "cb_...",
  "bank_version_id": "cbv_..."
}
```

Contract changes:

- replace `language const de` with enum/reference for `de/en/fr/es/nl`;
- keep legacy `language` in response for one compatibility window;
- add canonical `language_code`;
- expose `theme_code`; keep `theme_id` alias initially.

## 8. Import Pipeline Change Plan

Files:

- `tools/quizbank_common.py`
- `tools/quizbank_import_sample.py`
- `tools/quizbank_postgresql_load_plan.py`
- `tools/import_production_corpus_to_runtime.py`
- `tools/quizbank_emit_standards.py`
- `schemas/canonical_quiz_item.schema.json`
- `data/manifests/import_manifest.yml`
- `data/parser_profiles/parser_profiles.yml`

New CLI/import inputs:

```text
--language-code de
--content-bank-slug german-core
--bank-version 2026-06-12-baseline
--bank-version-status draft
```

Validation rules:

1. `language_code` is required on every import batch.
2. Batch language must match content bank language.
3. Row language must match batch `language_code`.
4. Import cannot write directly to active version unless a controlled repair mode is explicitly approved.
5. Mixed-language input in one batch is rejected.
6. Duplicate source item IDs are unique within bank version, not globally.
7. Activation requires zero blocker errors.

Activation workflow:

```text
create draft version
import source rows
write import_batches/import_batch_items/import_validation_results
run audit reports
mark version audit
activate version
archive previous active version
write content_bank_activation_events
```

Rollback workflow:

```text
load previous activation event
verify previous version still exists and status archived
transaction:
  current active → archived
  previous archived → active
  insert activation event with action rollback
API resolves previous version
```

## 9. Admin Change Plan

Files:

- `src/quizbank_mvp/admin_api.py`
- `src/quizbank_mvp/admin_service.py`
- `src/quizbank_mvp/admin_panel.py`
- `src/quizbank_mvp/database_status.py`

Add admin capabilities:

- list languages;
- list content banks by language;
- list versions by bank;
- show active/audit/draft/archived states;
- create draft bank version;
- review import batches for a version;
- activate audited version;
- rollback to previous version;
- filter quiz items by language/bank/version;
- filter dashboard by language/bank/version;
- prevent cross-language/bank batch status changes.

Admin activation checks:

- version status is `audit`;
- version language matches bank language;
- validation report has no blocker errors;
- item count by level/theme is visible;
- active version exists for rollback unless first activation;
- actor/reason required.

## 10. Channel and Client Config Change Plan

Files:

- `data/config/protected_beta_channels.json`
- `src/quizbank_mvp/protected_beta_config.py`
- `src/quizbank_mvp/protected_beta.py`
- `src/quizbank_mvp/protected_beta_slot_runs.py`
- `src/quizbank_mvp/telegram_models.py`
- `src/quizbank_mvp/telegram_delivery.py`

Config additions:

```json
{
  "default_language_code": "de",
  "default_content_bank_slug": "german-core",
  "allowed_language_codes": ["de"],
  "allowed_content_bank_slugs": ["german-core"]
}
```

Runtime additions:

- include language/bank in `TelegramDeliveryRequest`;
- include language/bank in scheduled slot idempotency;
- resolve active bank version before `select_next_item`;
- store scope in scheduled slot rows.

## 11. Tariff and Entitlement Change Plan

Files:

- `data/billing/plan_catalog.json`
- `src/quizbank_mvp/database_seed.py`
- `src/quizbank_mvp/selection_scope_enforcement.py`
- `src/quizbank_mvp/visual_access.py`

First-stage structure:

- all existing plans get `language_codes: ["de"]`;
- all existing entitlements get `allowed_language_codes_json: ["de"]`;
- all existing consumers get default `de`;
- bank scope can be `["german-core"]`.

Recommended entitlement fields:

```text
allowed_language_codes_json
allowed_content_bank_ids_json
allowed_bank_version_ids_json nullable
allowed_content_types_json nullable
```

Later normalized model:

```text
entitlement_scopes(
  entitlement_id,
  scope_type,
  scope_value
)
```

## 12. Test Plan

Database/schema:

- existing German rows backfill to `language_code = de`;
- default German content bank/version exists and is active;
- only one active version per content bank;
- FK from `quiz_items` to `content_bank_versions` is enforced;
- selection indexes include language and bank version.

API:

- `/v1/quiz-items/next` works without `language_code` and returns `de`;
- `/v1/quiz-items/next` works with explicit `language_code=de`;
- unsupported future language returns clear error, not a crash;
- responses include `language_code`, `content_bank_id`, `bank_version_id`;
- `/v1/topics?language_code=de` returns stable theme codes and German labels;
- old clients using only level/theme still pass.

Selection:

- German and English test rows with same level/theme never mix when requesting `de`;
- two bank versions with same level/theme never mix;
- archived bank version is not used for new next-quiz delivery;
- trusted item lookup rejects archived/wrong-bank item unless authorized historical mode is used;
- repeat policy applies inside correct language/bank/version scope;
- no-candidate diagnostics count only the resolved scope.

Import:

- import batch requires `language_code`;
- row language mismatch rejects batch;
- mixed-language input rejects batch;
- import writes to draft/audit version only;
- activation switches active version;
- rollback restores previous active version;
- activation event audit row is created.

Admin:

- item list filters by language, bank, version;
- dashboard counts by language/bank/version;
- activation action requires audited version and reason;
- cross-language batch publish is blocked;
- bank/version status display is correct.

Tariffs/entitlements/quota:

- consumer default language is `de`;
- entitlement without language scope is migrated to `de`;
- consumer without explicit bank gets default active German bank;
- quota cannot grant wrong language/bank;
- quota scope does not unexpectedly reset unless version-level quota is configured.

Telegram/channel/visual:

- protected beta config defaults to `de`;
- scheduled slot idempotency includes language/bank/version;
- Telegram delivery uses resolved bank version;
- visual cache key differs for different bank versions;
- visual usage events can be reported by language/bank.

Regression:

- current German MVP runtime tests still pass;
- OpenAPI contract test updated;
- PostgreSQL contract test updated;
- no raw CSV access path introduced.

## 13. Recommended Roadmap

### Stage 0: Audit Closure

Output:

- this audit set;
- no code change.

### Stage 1: Schema Foundation

Scope:

- add language and bank/version tables;
- backfill German default;
- add scope columns to critical tables;
- update readiness and contract tests.

Risk level: high, because schema touches selection/delivery.

### Stage 2: Runtime Scope Resolution

Scope:

- content scope resolver;
- selection filters;
- delivery and decision logging;
- API request/response defaults.

Risk level: high, because this controls content isolation.

### Stage 3: Import Draft/Audit/Active Flow

Scope:

- batch-level language/bank/version;
- draft version import;
- audit reports;
- activation/rollback service.

Risk level: high, because it controls bank replacement.

### Stage 4: Admin UI/API

Scope:

- bank/version screens;
- filters;
- activation and rollback actions;
- cross-language safeguards.

Risk level: medium-high.

### Stage 5: Channel/Tariff Scope

Scope:

- channel defaults and allowed scopes;
- plan catalog scopes;
- entitlement/quota scopes.

Risk level: medium.

### Stage 6: Future Language Onboarding

Scope:

- load `en` or another non-production bank as draft;
- validate mixed-language rejection;
- keep production active content `de` only until business approval.

Risk level: medium if previous stages pass.

## 14. Explicit Non-Goals For First Implementation

- No production/staging deploy.
- No paid launch changes.
- No mass deletion of old German questions.
- No full public multi-language launch.
- No change to existing German business behavior except adding explicit default scope.
- No direct raw CSV access by API clients.

