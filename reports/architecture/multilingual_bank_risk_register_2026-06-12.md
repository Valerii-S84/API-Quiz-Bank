# Multilingual Content Bank Risk Register

Дата: 2026-06-12  
Scope: risks found during architecture audit. No mitigation implemented in this task.

## 1. Summary

| Severity | Count | Meaning |
|---|---:|---|
| Critical | 6 | Can mix languages/banks or block safe bank replacement |
| High | 9 | Can break auditability, rollback, quotas or admin safety |
| Medium | 6 | Can create operational friction or future rework |

## 2. Risks

### R-001: Selection Can Mix Languages

Severity: Critical  
Evidence: `selection_eligibility.fetch_candidate_pool()` filters status, source traceability, sublevel, theme, objective, pattern and exclusions, but not language.  
Impact: adding `en/fr/es/nl` rows with approved/published status can make them eligible for German clients.  
Mitigation: add resolved `language_code` to `SelectionRequest`, candidate SQL, diagnostics, decisions and deliveries. Default missing language to `de`.  
Owner area: selection/API.  
Phase: Stage 2.

### R-002: Selection Can Mix Bank Versions

Severity: Critical  
Evidence: no `content_bank_id` or `bank_version_id` exists in DB/runtime; selection reads all deliverable `quiz_items`.  
Impact: old and new replacement banks can be delivered together. Archived bank cannot be excluded structurally.  
Mitigation: add bank/version tables and require `qi.bank_version_id = resolved active version` in selection SQL.  
Owner area: DB/selection.  
Phase: Stage 1-2.

### R-003: Bank Replacement Currently Relies On Retire/Overwrite Behavior

Severity: Critical  
Evidence: `tools/import_production_corpus_to_runtime.py` imports whole corpus and can use `--retire-non-corpus-items`; no bank-version activation exists.  
Impact: replacing the German bank risks mass status changes instead of reversible version activation.  
Mitigation: import new content into draft/audit `content_bank_versions`, then activate transactionally; keep old version archived.  
Owner area: import/admin/DB.  
Phase: Stage 3.

### R-004: Trusted Item Lookup Can Bypass Active-Bank Scope

Severity: Critical  
Evidence: `trusted_delivery.load_deliverable_item()` looks up by `item_id` and deliverable status only, then enforces level/theme via item fields.  
Impact: archived or wrong-bank items could remain accessible if their item status is approved/published.  
Mitigation: require active/authorized bank-version check in trusted lookup; add historical lookup only for admin/trusted explicit mode.  
Owner area: trusted delivery/API.  
Phase: Stage 2.

### R-005: Delivery Evidence Does Not Snapshot Language/Bank

Severity: Critical  
Evidence: `deliveries` stores `quiz_item_id`, `source_id`, status, entitlement and quota ids, but no language or bank/version columns.  
Impact: after activation/rollback, delivery history cannot independently prove which bank version was used without joining mutable item metadata.  
Mitigation: add `language_code`, `content_bank_id`, `bank_version_id` to deliveries at selection time.  
Owner area: DB/selection/delivery.  
Phase: Stage 1-2.

### R-006: Import Batch Has No Language/Bank Boundary

Severity: Critical  
Evidence: PostgreSQL import tables store source/batch/item validation lineage but no language or bank version; sample import validates only row-level `language == de`.  
Impact: future imports could mix languages or write to the wrong bank/version.  
Mitigation: make `language_code`, `content_bank_id`, `bank_version_id` required on import batches and inherited by import items/results.  
Owner area: import/DB.  
Phase: Stage 3.

### R-007: Quota Scope Can Grant Or Deny Wrong Content Scope

Severity: High  
Evidence: `quota_usage` is unique by `(consumer_id, feature, usage_date)` and scoped quota digest is embedded in `feature`; no language/bank scope exists.  
Impact: usage in one language/bank can consume quota for another, or tariffs cannot express language/bank packages.  
Mitigation: add explicit quota scope columns or normalized scope hash including language/content bank; decide whether version-level quota is policy-specific.  
Owner area: billing/quota.  
Phase: Stage 5.

### R-008: Entitlements Cannot Express Language Or Bank Access

Severity: High  
Evidence: `entitlements` stores feature plus allowed CEFR/theme JSON only.  
Impact: a consumer entitled to German could accidentally receive future English/French content if selection is not separately scoped.  
Mitigation: add allowed language and bank scopes to entitlements or normalized entitlement scope table.  
Owner area: billing/access control.  
Phase: Stage 5.

### R-009: Consumer Defaults Do Not Include Language/Bank

Severity: High  
Evidence: `consumers` stores allowed CEFR/themes and daily quota only; channel config also lacks default language/bank.  
Impact: old clients cannot be safely defaulted per consumer except through global hard-coded behavior.  
Mitigation: add consumer default `language_code` and content bank/version resolution. Seed existing consumers with `de`.  
Owner area: API/client config.  
Phase: Stage 2 and Stage 5.

### R-010: Scheduled Slot Idempotency Will Collide Across Scopes

Severity: High  
Evidence: `scheduled_delivery_slots` unique key and idempotency key include consumer/channel/date/slot/theme/level, not language or bank version.  
Impact: same slot in another language or bank version can be incorrectly treated as existing or sent.  
Mitigation: add language/bank/version to scheduled slot columns, unique key and idempotency key.  
Owner area: Telegram scheduler.  
Phase: Stage 5.

### R-011: Visual Asset Cache Can Reuse Wrong Bank-Version Image

Severity: High  
Evidence: `visual_cache.compute_visual_cache_key()` includes quiz item id, mode, style, brand, image version, language and scope, but no content bank/version.  
Impact: if item ids are reused across bank versions, visual assets can be reused for changed content.  
Mitigation: include `content_bank_id` and `bank_version_id` in visual cache key and asset table.  
Owner area: visual delivery.  
Phase: Stage 5.

### R-012: Item ID Primary Key Blocks Natural Bank Version Reuse

Severity: High  
Evidence: `quiz_items.item_id` is the primary key and referenced by deliveries/assets/policies.  
Impact: importing a replacement bank with same source item ids can collide unless IDs are globally regenerated.  
Mitigation: choose Option A, generate global bank-version-prefixed item ids for first stage; or Option B, introduce internal row key and unique `(bank_version_id, source_item_id)`.  
Owner area: DB/import.  
Phase: Stage 1 and later item-version design.

### R-013: OpenAPI Hard-Codes German Public Projection

Severity: High  
Evidence: `api/openapi.yaml` uses `language const de` in public quiz projections; request schemas do not include language/bank fields.  
Impact: non-German banks would break contract or force undocumented behavior.  
Mitigation: add `language_code` enum/reference and optional request fields; retain default `de`.  
Owner area: API contract.  
Phase: Stage 2.

### R-014: Canonical JSON Schema Hard-Codes `language = de`

Severity: High  
Evidence: `schemas/canonical_quiz_item.schema.json` has `"language": {"type": "string", "const": "de"}`.  
Impact: future language imports are rejected by schema unless schema changes.  
Mitigation: replace with `language_code` enum or supported-language reference; keep German production gate in import config, not schema const.  
Owner area: schema/import.  
Phase: Stage 3.

### R-015: Admin UI Cannot See Or Control Bank Version Status

Severity: High  
Evidence: admin UI/API supports item filters by status/level/theme/source and consumer controls only.  
Impact: activation and rollback would need manual DB changes unless admin surface is added.  
Mitigation: add bank/version list, details, import reports, activation and rollback actions with audit reasons.  
Owner area: admin.  
Phase: Stage 4.

### R-016: Theme Labels Are German-Centric

Severity: Medium  
Evidence: `taxonomy.py` and `data/taxonomy/themes.csv` store German titles directly for `T01` to `T18`.  
Impact: multilingual topic responses either show German labels for all languages or require ad hoc branching later.  
Mitigation: keep stable `theme_code`; add `theme_translations(theme_code, language_code, title, description)`.  
Owner area: taxonomy/API.  
Phase: Stage 2 or later before first non-German public content.

### R-017: Readiness Checks Do Not Require Bank Tables

Severity: Medium  
Evidence: `database_runtime.RUNTIME_TABLES` checks fixed runtime tables only.  
Impact: a partially migrated database could report ready while content-bank tables are missing.  
Mitigation: update readiness table set and tests when schema foundation lands.  
Owner area: runtime DB.  
Phase: Stage 1.

### R-018: Billing Catalog Cannot Express Language/Bank Packages

Severity: Medium  
Evidence: `data/billing/plan_catalog.json` feature entries have feature code, enabled flag, limit and period only.  
Impact: future plans cannot distinguish one language, multiple languages, a specific bank, or content types.  
Mitigation: add `scope` object with language codes, bank slugs/ids and content types.  
Owner area: billing.  
Phase: Stage 5.

### R-019: Import Manifest Has No Bank Version

Severity: Medium  
Evidence: `data/manifests/import_manifest.yml` records source id/path/parser/import mode/source state/default status/checksum/count, but no language or bank version.  
Impact: source files cannot be grouped into a replaceable audited bank snapshot from manifest alone.  
Mitigation: add manifest-level and source-level language/bank/version fields.  
Owner area: import governance.  
Phase: Stage 3.

### R-020: Tests Do Not Prove Language Or Bank Isolation

Severity: Medium  
Evidence: current MVP tests cover German fixtures, status, quota, repeat, import validation and OpenAPI path presence; no mixed-language or multi-version fixtures were found.  
Impact: regressions can pass while selection mixes content scopes.  
Mitigation: add tests listed in migration plan before importing second language or replacement bank.  
Owner area: QA.  
Phase: Stage 1-5.

### R-021: Existing Docs Mention `quiz_item_version`, Runtime Does Not

Severity: Medium  
Evidence: `docs/04_domain_model.md` and `docs/05_architecture.md` describe `quiz_item_version`, while runtime stores a flat `quiz_items.version` string and deliveries reference `quiz_item_id`.  
Impact: bank versioning may be confused with item versioning unless the implementation plan explicitly distinguishes them.  
Mitigation: define bank-level versioning now; schedule item-version normalization later if needed.  
Owner area: architecture/data model.  
Phase: Stage 1 and later.

## 3. Blockers Before Adding `en/fr/es/nl`

The following risks must be mitigated first:

- R-001 selection can mix languages;
- R-002 selection can mix bank versions;
- R-006 import batch has no language/bank boundary;
- R-008 entitlements cannot express language/bank access;
- R-013 OpenAPI hard-codes German;
- R-014 canonical schema hard-codes German;
- R-020 tests do not prove isolation.

## 4. Blockers Before Replacing German Bank

The following risks must be mitigated first:

- R-002 selection can mix bank versions;
- R-003 replacement currently relies on retire/overwrite behavior;
- R-004 trusted lookup can bypass active-bank scope;
- R-005 delivery evidence lacks bank snapshot;
- R-010 scheduled slot idempotency collision;
- R-012 item id primary-key collision strategy unresolved;
- R-015 admin cannot activate/rollback bank version.

## 5. Residual Risk After Recommended Stage 1-3

Even after schema, selection and import activation are implemented, residual risks remain:

- quotas may need policy clarification on bank-level vs bank-version-level counting;
- visual asset cache migration may need cleanup or version bump;
- existing historical deliveries before migration will have backfilled `de` and baseline version, not original explicit bank evidence;
- current flat item model may still be less precise than full `quiz_item_versions`.

## 6. Not Verified

- Production DB contents and live migration feasibility were not verified.
- No performance benchmark was run after proposed index changes.
- No external billing provider integration exists in committed runtime and was not tested.
- No live Telegram delivery was run.
- No production/staging deploy was performed.

