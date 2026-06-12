# Multilingual Content Bank Architecture Audit

Дата: 2026-06-12  
Scope: audit only, no deploy, no migrations, no business-logic changes.  
Baseline: current production content remains German-only, `de`.

## 1. Executive Summary

Факт: committed runtime already has a German-only content model with `quiz_items.language`, source traceability, status-gated delivery, consumer/entitlement level/theme scopes, quota usage, delivery logs, selection decision logs, Telegram delivery evidence, visual delivery tables, admin API/UI, and a PostgreSQL schema mirror.

Факт: no committed implementation contains `language_code`, `content_bank_id`, `bank_version_id`, `content_banks`, or `content_bank_versions`. Search for these identifiers returned no matches outside this audit.

Факт: current top-level `QuizBank/*.csv` corpus has `de 30974` rows in the `language` column. No non-`de` top-level corpus language was observed.

Висновок: current architecture can safely continue German-only delivery, but it is not ready to add `en`, `fr`, `es`, `nl` or to replace a full bank without schema/API/selection/import changes. The critical missing boundary is active content-bank version resolution.

Висновок: current `language` field is item metadata, not a selection boundary. Selection, quotas, deliveries, admin filters, schedules, import batches and tariffs do not scope by language or bank version.

Рекомендація: implement multilingual/bank support as an explicit content-bank versioning layer, not as mass deletion or overwrite of old quiz rows. Keep backward compatibility by defaulting missing `language_code` to `de`.

## 2. Evidence Base

Reviewed committed artifacts:

- DB schema: `database/migrations/*.sql`, `database/postgresql/*.sql`
- Runtime/API: `src/quizbank_mvp/app.py`, `admin_api.py`, `admin_service.py`, `selection*.py`, `trusted_delivery.py`, `telegram*.py`, `protected_beta*.py`, `visual*.py`, `database_*.py`
- Import tooling: `tools/quizbank_common.py`, `quizbank_import_sample.py`, `quizbank_postgresql_load_plan.py`, `import_production_corpus_to_runtime.py`
- Contracts/config: `api/openapi.yaml`, `schemas/canonical_quiz_item.schema.json`, `data/config/protected_beta_channels.json`, `data/billing/plan_catalog.json`, `data/taxonomy/*.csv`, `data/manifests/import_manifest.yml`
- Tests: `tests/test_mvp_runtime.py`, `tests/test_mvp_selection_contract.py`, `tests/test_mvp_selection_policy.py`, `tests/test_import_validation.py`, `tests/test_postgresql_contract.py`
- Normative/planned docs: `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/06_data_standard.md`, `docs/07_api_standard.md`, `docs/11_billing_model.md`, `docs/16_source_onboarding_playbook.md`, `docs/17_admin_workflow.md`, `docs/18_telegram_delivery_playbook.md`

Недоведено:

- No production/staging database was queried.
- No VPS runtime, scheduler, or production route was inspected.
- No deploy or runtime migration was executed.
- Current audit covers committed local repository state only.

## 3. Current Database Map

### 3.1 SQLite MVP Tables

| Table | Current role | Existing language/bank state | Required change |
|---|---|---|---|
| `sources` | Source registry for runtime items | no language/bank/version | add `language_code`, `content_bank_id`, `bank_version_id`; source belongs to one bank version |
| `quiz_items` | Canonical runtime item row | has `language`, no bank/version | add `language_code`, `content_bank_id`, `bank_version_id`; keep `language` temporarily as backward-compatible alias |
| `consumers` | API/channel/client scope and daily quota | allowed levels/themes only | add default `language_code`, default bank/version, allowed languages/banks or separate scope table |
| `api_credentials` | Consumer API keys | no content scope | no direct content field required; access still resolves through consumer |
| `entitlements` | Feature access plus allowed levels/themes | no language/bank scope | add allowed languages/banks or normalized entitlement scope table |
| `quota_usage` | Quota counters | unique by consumer/feature/date | add quota scope columns or normalized quota scope key including language/bank/version |
| `deliveries` | Delivery evidence | references `quiz_item_id`, no stored language/bank | add `language_code`, `content_bank_id`, `bank_version_id` snapshot at selection time |
| `audit_log` | Admin/system audit | generic entity ids only | add metadata JSON or explicit content scope fields for bank activation/import actions |
| `selection_decisions` | Selection evidence | filters JSON has level/theme/objective/pattern only | add language/bank/version in request filters and stored columns/context |
| `telegram_delivery_results` | Telegram send evidence | linked to delivery only | can inherit via delivery; direct denormalized scope optional for reporting |
| `admin_credentials` | Admin auth | no content scope | no direct content field required |
| `consumer_admin_profiles` | Consumer display/kind | no defaults | add visible defaults or join to consumer content scope |
| `scheduled_delivery_slots` | Telegram schedule idempotency | unique by consumer/channel/date/slot/theme/level | add language and bank/version to unique key and idempotency key |
| `consumer_visual_settings` | Per-consumer visual settings | no content scope | no direct content field required unless plans vary by content type |
| `visual_assets` | Generated/cached images | has `language`, no bank/version | rename/add `language_code`; add bank/version to cache key/table |
| `visual_prompt_audit` | Prompt evidence | item/consumer only | add language/bank/version or inherit via item/delivery |
| `visual_delivery_results` | Visual delivery evidence | linked to delivery | can inherit via delivery; direct denormalized scope optional |
| `visual_usage_events` | Visual quota/cost events | consumer/feature only | add language/bank/content-type scope if visual quota differs by bank/language |
| `quiz_item_image_quality_policy` | Item-level visual policy | item FK only | safe only if item ids remain globally unique; otherwise add bank/version-aware FK |

### 3.2 PostgreSQL Contract Tables

PostgreSQL mirrors the same runtime model and adds import contract tables:

| Table | Current role | Required change |
|---|---|---|
| `import_batches` | Batch metadata by `source_id` | add `language_code`, `content_bank_id`, `bank_version_id`; one batch must target exactly one bank version |
| `import_batch_items` | Batch item lineage | add `bank_version_id`; uniqueness must include bank/version for source item ids |
| `import_validation_results` | Import validation evidence | add or inherit batch language/bank/version; reports should include these fields |

Факт: PostgreSQL DDL currently has `quiz_items.language TEXT NOT NULL` and no `language_code` or bank tables.

Висновок: both SQLite MVP migrations and PostgreSQL migrations must be updated in lockstep, and `tests/test_postgresql_contract.py` must be extended.

## 4. Required New Data Model

Recommended minimum model:

```text
languages(
  code primary key,
  name,
  is_active,
  created_at
)

content_banks(
  id primary key,
  slug,
  language_code references languages(code),
  name,
  status,
  created_at
)

content_bank_versions(
  id primary key,
  content_bank_id references content_banks(id),
  version,
  status check draft/audit/active/archived,
  activated_at,
  created_at
)
```

Recommended additional operational table:

```text
content_bank_activation_events(
  activation_event_id primary key,
  content_bank_id,
  from_bank_version_id,
  to_bank_version_id,
  actor,
  reason,
  activated_at
)
```

Why the extra table matters:

- it preserves rollback evidence;
- it avoids losing history when `content_bank_versions.status` changes;
- it gives admin UI an activation timeline.

Critical constraints:

- `languages.code` allowed set for planned architecture: `de`, `en`, `fr`, `es`, `nl`.
- `content_banks` should enforce unique `(language_code, slug)`.
- `content_bank_versions` should enforce unique `(content_bank_id, version)`.
- PostgreSQL should enforce one active version per `content_bank_id` with a partial unique index where feasible.
- `quiz_items` should reference `content_bank_versions(id)` and store `language_code` for query/index speed and safety checks.

## 5. Current API Endpoint Map

Implemented FastAPI/OpenAPI endpoints:

| Endpoint | Current purpose | Required multilingual/bank change |
|---|---|---|
| `GET /health`, `GET /v1/health` | service health | no content change |
| `GET /ready`, `GET /v1/ready` | DB readiness | include required bank/version tables in readiness |
| `GET /v1/levels` | CEFR levels | optionally accept/return `language_code`; CEFR remains stable |
| `GET /v1/topics` | topic/theme list | add `language_code` query default `de`; return stable `theme_code` and localized labels |
| `POST /v1/quiz-items/next` | select next quiz | add optional `language_code`, `content_bank_id`, `bank_version_id`; default missing language to `de` |
| `GET /v1/quiz-items/{item_id}` | trusted item lookup | require active-bank visibility or explicit bank/version authorization |
| `GET /v1/deliveries/{delivery_id}` | delivery projection | return `language_code`, `content_bank_id`, `bank_version_id` |
| `POST /v1/deliveries/{delivery_id}/outcome` | trusted outcome write | preserve scope via delivery; no direct selector needed |
| `GET /admin` | HTML admin shell | add language/bank/version filters and activation UI |
| `GET /v1/admin/dashboard` | counts | group counts by language/bank/version |
| `GET /v1/admin/quiz-items` | item list | add filters `language_code`, `content_bank_id`, `bank_version_id` |
| `GET /v1/admin/quiz-items/{item_id}` | item detail | return language/bank/version |
| `POST /v1/admin/quiz-items/{item_id}/approve|publish|retire|block` | item status workflow | prevent status changes across wrong bank/version context |
| `GET /v1/admin/audit-log` | audit events | filter by language/bank/version where metadata exists |
| `GET /v1/admin/consumers` | consumer list | return default language/bank/version and allowed scopes |
| `POST /v1/admin/consumers` | create consumer | accept default/allowed language and bank scope, default `de` |
| `GET/PATCH /v1/admin/consumers/{consumer_id}/visual-settings` | visual config | no mandatory content selector, but responses may show default language/bank context |
| `POST /v1/admin/consumers/{consumer_id}/suspend|activate|block` | consumer status | no direct content selector |

No committed HTTP import endpoints were found. Import currently exists as local tooling and PostgreSQL load-plan artifacts.

Recommended new admin/API endpoints:

- `GET /v1/languages`
- `GET /v1/content-banks?language_code=de`
- `GET /v1/content-banks/{content_bank_id}/versions`
- `POST /v1/admin/content-banks`
- `POST /v1/admin/content-banks/{content_bank_id}/versions`
- `POST /v1/admin/content-bank-versions/{bank_version_id}/mark-audit`
- `POST /v1/admin/content-bank-versions/{bank_version_id}/activate`
- `POST /v1/admin/content-bank-versions/{bank_version_id}/archive`
- `POST /v1/admin/content-bank-versions/{bank_version_id}/rollback`
- `GET /v1/admin/import-batches?language_code=&content_bank_id=&bank_version_id=`

Backward compatibility rule:

- If request omits `language_code`, resolve `de`.
- If request omits bank/version, resolve consumer default; if absent, resolve active `de` bank version.
- API responses should always include `language_code`, `content_bank_id`, and `bank_version_id` once the schema exists.

## 6. Selection Logic Audit

Current path:

```text
POST /v1/quiz-items/next
  → NextQuizRequest(consumer_id, cefr_level, theme_ids, objective_ids, pattern_ids)
  → SelectionRequest/SelectionFilters
  → load active consumer
  → load active entitlement(feature='quiz_delivery')
  → intersect allowed CEFR/theme
  → fetch_candidate_pool()
  → status/sublevel/theme/objective/pattern/excluded-item filters
  → repeat-policy join by consumer_id + quiz_item_id
  → reserve quota
  → insert delivery and selection_decision
```

Current hot SQL filters:

- `qi.status IN approved/published`
- `qi.sublevel = ?`
- `qi.theme_id IN (...)`
- `qi.objective_id IN (...)`
- `qi.pattern_id IN (...)`
- `qi.item_id NOT IN (...)`
- repeat history by `deliveries.consumer_id` and `deliveries.quiz_item_id`

Missing filters:

- `qi.language_code = ?`
- `qi.content_bank_id = ?`
- `qi.bank_version_id = ?`

Correct future selection scope:

| Concern | Required scope |
|---|---|
| candidate pool | consumer/channel, `language_code`, `bank_version_id`, level, theme, objective, pattern, status |
| repeat policy | consumer/channel, `language_code`, content bank, bank version, item id or content hash |
| quota | consumer/channel/quota key, feature, period, `language_code`, content bank; `bank_version_id` only if tariff policy wants version-level quota |
| delivery evidence | exact selected `language_code`, `content_bank_id`, `bank_version_id`, level, theme, item id |
| no-candidate diagnostics | same filters as candidate pool |
| trusted item lookup | item must be in allowed language and active/authorized bank version unless explicitly requesting historical lookup |

Critical finding:

- New language rows added to current `quiz_items` table would be eligible if they match status/level/theme and consumer scope, because selection does not filter by language.
- New bank-version rows would mix with old rows if status remains approved/published, because selection does not filter by bank/version.

## 7. Import Pipeline Audit

Current import facts:

- `tools/quizbank_common.py` defines `EXPECTED_HEADER` with `language`.
- `tools/quizbank_import_sample.py` rejects canonical rows where `language != "de"`.
- `tools/quizbank_postgresql_load_plan.py` creates load plans for `sources`, `import_batches`, `import_batch_items`, `import_validation_results`.
- `tools/import_production_corpus_to_runtime.py` imports whole `QuizBank/` into runtime tables and can `--retire-non-corpus-items`.
- `data/manifests/import_manifest.yml` has source rows with `source_id`, path, parser profile, import mode, source state, default status, checksum and row count.

Missing import boundaries:

- no batch-level `language_code`;
- no batch-level `content_bank_id`;
- no batch-level `bank_version_id`;
- no one-bank-version-per-import invariant;
- no activation workflow after audit;
- no rollback workflow;
- no guarantee that future import cannot mix languages inside one bank/version.

Required import rule:

```text
One import batch targets exactly one language_code and exactly one content_bank_version.
Rows whose language differs from the batch language are rejected.
Rows cannot be committed to an active version directly.
```

Recommended bank replacement flow:

```text
old version: active
new version: draft
import rows into new draft version
run validation and audit
mark version audit
activate new version in a transaction
archive old version
API resolves new active version
rollback reactivates previous version using activation history
```

## 8. Admin Panel Audit

Current admin filters:

- item status;
- CEFR level;
- theme;
- source id;
- consumer list;
- item status actions;
- consumer status actions;
- visual settings.

Required filters and UI states:

- `language_code` filter for dashboard, item list, imports, audit log, consumers;
- `content_bank_id` filter;
- `bank_version_id` filter;
- bank/version status badges: draft, audit, active, archived;
- activation action visible only after audit status;
- rollback action using previous activation event;
- warning/blocker when import language differs from bank language;
- dashboard counts grouped by language and bank version.

Critical admin safety:

- Batch item publish/approve must not cross language or bank-version boundaries.
- Manual item lookup should show bank/version prominently.
- Trusted item lookup should not expose archived-version content unless explicitly allowed by historical/admin mode.

## 9. Tariffs, Subscriptions and Entitlements

Current implementation:

- `data/billing/plan_catalog.json` defines plan features and limits, mainly `quiz_delivery` and visual features.
- Runtime `entitlements` has `feature`, status, allowed levels/themes, valid_until.
- Runtime `quota_usage` counts by consumer, feature and period key.
- No runtime plans/subscriptions tables were found.

Required future tariff model:

- plan feature scope can include `language_codes`;
- plan feature scope can include `content_bank_ids` or `content_type`;
- entitlement scope must include allowed languages and banks;
- quota policy should support daily quiz count by consumer/channel/language/bank and optionally level/theme;
- first stage may seed all plans with only `["de"]`.

Recommended minimal extension:

```json
{
  "feature_code": "quiz_delivery",
  "is_enabled": true,
  "limit_value": 10,
  "limit_period": "day",
  "scope": {
    "language_codes": ["de"],
    "content_bank_slugs": ["german-core"],
    "content_types": ["text_quiz"]
  }
}
```

## 10. Channel and Client Configuration

Current channel config:

- `data/config/protected_beta_channels.json` defines `consumer_id`, `chat_id`, display name, timezone, daily quota, schedule batches, slots with CEFR/theme, and visual config.
- `ProtectedBetaTelegramChannel` derives allowed CEFR levels and themes from slots.
- No default language or bank version is configured.

Required fields:

- `default_language_code`, default `de`;
- `default_content_bank_id` or `default_bank_version_id`;
- allowed language codes;
- allowed content banks or version policy;
- existing allowed levels/themes;
- daily limits.

Scheduled delivery slots need language and bank/version in:

- table columns;
- uniqueness constraint;
- idempotency key;
- schedule config validation;
- no-item diagnostic context.

## 11. Taxonomy and Themes

Current facts:

- `src/quizbank_mvp/taxonomy.py` stores German labels in `TOPIC_TITLES`.
- `data/taxonomy/themes.csv` has `theme_id`, German title, counts, status.
- API `/v1/topics` returns `topic_id`, `theme_id`, `title`, status.

Required model:

- stable `theme_code` values `T01` to `T18`;
- localized labels/descriptions separated from theme identity;
- no selection logic based on German title;
- existing `theme_id` can be kept as backward-compatible alias for `theme_code`.

Recommended tables/files:

```text
themes(theme_code primary key, status, order_index)
theme_translations(theme_code, language_code, title, description, primary key(theme_code, language_code))
```

## 12. Files and Modules Requiring Change

Critical DB/schema:

- `database/migrations/001_create_mvp_runtime.sql`
- `database/migrations/004_add_selection_decisions.sql`
- `database/migrations/007_add_scheduled_delivery_slots.sql`
- `database/migrations/008_add_visual_delivery.sql`
- `database/migrations/009_add_image_quality_policy.sql`
- `database/migrations/010_add_next_route_selection_indexes.sql`
- `database/postgresql/001_create_runtime.sql`
- `database/postgresql/002_add_import_contract.sql`
- `database/postgresql/003_add_runtime_delivery_evidence.sql`
- `database/postgresql/006_add_scheduled_delivery_slots.sql`
- `database/postgresql/007_add_visual_delivery.sql`
- `database/postgresql/009_add_image_quality_policy.sql`
- `database/postgresql/011_add_next_route_selection_indexes.sql`

Critical runtime/API:

- `src/quizbank_mvp/app.py`
- `src/quizbank_mvp/selection_models.py`
- `src/quizbank_mvp/selection.py`
- `src/quizbank_mvp/selection_scope.py`
- `src/quizbank_mvp/selection_scope_enforcement.py`
- `src/quizbank_mvp/selection_eligibility.py`
- `src/quizbank_mvp/selection_diagnostics.py`
- `src/quizbank_mvp/selection_decision_log.py`
- `src/quizbank_mvp/selection_delivery.py`
- `src/quizbank_mvp/selection_quota.py`
- `src/quizbank_mvp/trusted_delivery.py`
- `src/quizbank_mvp/projections.py`
- `src/quizbank_mvp/taxonomy.py`
- `src/quizbank_mvp/database_runtime.py`
- `src/quizbank_mvp/database_seed.py`
- `src/quizbank_mvp/admin_api.py`
- `src/quizbank_mvp/admin_service.py`
- `src/quizbank_mvp/admin_panel.py`

Critical import/config:

- `tools/quizbank_common.py`
- `tools/quizbank_import_sample.py`
- `tools/quizbank_postgresql_load_plan.py`
- `tools/import_production_corpus_to_runtime.py`
- `tools/quizbank_emit_standards.py`
- `schemas/canonical_quiz_item.schema.json`
- `api/openapi.yaml`
- `api/openapi.template.yaml`
- `data/manifests/import_manifest.yml`
- `data/registry/source_registry.csv`
- `data/parser_profiles/parser_profiles.yml`
- `data/imports/control_sample_items.jsonl`

Telegram/channel/visual:

- `data/config/protected_beta_channels.json`
- `src/quizbank_mvp/protected_beta_config.py`
- `src/quizbank_mvp/protected_beta.py`
- `src/quizbank_mvp/protected_beta_slot_runs.py`
- `src/quizbank_mvp/telegram_models.py`
- `src/quizbank_mvp/telegram_delivery.py`
- `src/quizbank_mvp/telegram_result_repository.py`
- `src/quizbank_mvp/visual_cache.py`
- `src/quizbank_mvp/visual_delivery.py`
- `src/quizbank_mvp/visual_asset_repository.py`

Billing/tests/docs:

- `data/billing/plan_catalog.json`
- `tests/test_mvp_runtime.py`
- `tests/test_mvp_selection_contract.py`
- `tests/test_mvp_selection_policy.py`
- `tests/test_mvp_selection_decisions.py`
- `tests/test_import_validation.py`
- `tests/test_postgresql_contract.py`
- `tests/test_contract_schema_invariants.py`
- `tests/test_visual_cache.py`
- `tests/test_visual_database.py`
- `tests/test_protected_beta.py`
- `docs/04_domain_model.md`
- `docs/05_architecture.md`
- `docs/06_data_standard.md`
- `docs/07_api_standard.md`
- `docs/11_billing_model.md`
- `docs/16_source_onboarding_playbook.md`
- `docs/17_admin_workflow.md`
- `docs/18_telegram_delivery_playbook.md`

## 13. Critical vs Later

Critical before adding second language or second bank:

- add bank/version tables;
- backfill current German bank/version;
- add `language_code` and bank/version to `quiz_items`, `sources`, imports, deliveries, selection decisions;
- update selection SQL to filter language and active bank version;
- update import tooling to target one bank version;
- update API request/response schemas with backward-compatible default `de`;
- update admin filters and activation workflow;
- update tests proving no language/bank mixing.

Can be later after safe foundation:

- full billing provider integration;
- self-service subscription UI;
- fully normalized `quiz_item_versions` and `quiz_options` if bank-version row model is accepted short-term;
- localized topic descriptions beyond titles;
- rich analytics dashboards by bank version;
- organization-level entitlement management.

