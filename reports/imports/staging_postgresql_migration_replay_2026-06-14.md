# Staging PostgreSQL Migration Replay Evidence

Date: 2026-06-14.

Scope: isolated staging PostgreSQL migration replay for `database/postgresql/001...013`,
language/content-scope smoke checks and active bank version rollback proof.

Production database access: not used.

## Staging Target

| Field | Value |
|---|---|
| Runtime | Docker PostgreSQL |
| Image | `postgres:16-alpine` |
| PostgreSQL version | `PostgreSQL 16.12 on x86_64-pc-linux-musl` |
| Container | `api-quiz-bank-staging-migration-20260614` |
| Bind | random localhost port on `127.0.0.1` |
| Container status during proof | `running no-healthcheck` |

## Backup / Snapshot Evidence

| Artifact | Path | Size | SHA-256 |
|---|---|---:|---|
| Pre-migration snapshot | `var/staging-postgresql-migration-20260614/pre_migration_snapshot.dump` | 1032 bytes | `cf13c8c7c878cce09c984c5ac429266190ac99408d90fe0c4b3ccd1ba3784669` |
| Post-smoke snapshot | `var/staging-postgresql-migration-20260614/post_smoke_snapshot.dump` | 107369 bytes | `3544d40c73b81bb04e82d66f972fdfef23e5a0fd7972ed42aabba4203bf362b1` |

## Migration Replay

Command path: `docker exec ... psql -v ON_ERROR_STOP=1 -U postgres -d postgres -f /schema/<migration>`.

Migration log artifact:

| Path | Lines | Size | SHA-256 |
|---|---:|---:|---|
| `var/staging-postgresql-migration-20260614/migration_replay.log` | 128 | 4632 bytes | `0912c599ef936479987c6a62468f16bc9f43fa0dd3574ea0fd79447780d9ed33` |

Applied migrations:

| Migration | Result |
|---|---|
| `database/postgresql/001_create_runtime.sql` | OK |
| `database/postgresql/002_add_import_contract.sql` | OK |
| `database/postgresql/003_add_runtime_delivery_evidence.sql` | OK |
| `database/postgresql/004_add_admin_credentials.sql` | OK |
| `database/postgresql/005_add_consumer_admin_profiles.sql` | OK |
| `database/postgresql/006_add_scheduled_delivery_slots.sql` | OK |
| `database/postgresql/007_add_visual_delivery.sql` | OK |
| `database/postgresql/008_use_text_quota_usage_period_key.sql` | OK |
| `database/postgresql/009_add_image_quality_policy.sql` | OK |
| `database/postgresql/010_add_visual_mode_policy_metadata.sql` | OK |
| `database/postgresql/011_add_next_route_selection_indexes.sql` | OK |
| `database/postgresql/012_add_multilingual_bank_foundation.sql` | OK |
| `database/postgresql/013_add_channel_tariff_scope.sql` | OK |

Replay result: PASS.

## Smoke Test Result

Smoke result artifact:

| Path | Size | SHA-256 |
|---|---:|---|
| `var/staging-postgresql-migration-20260614/smoke_result.json` | 12171 bytes | `db3cf56ad63eb45b340fbb21910282d9b63023bdb5fca1fa8149dafd73df59e1` |

| Check | Result | Evidence |
|---|---|---|
| Default `de` | PASS | `languages.de.is_active = true` |
| Inactive `en/fr/es/nl` | PASS | all four language requests returned `403 LANGUAGE_NOT_ACTIVE` |
| Selection scope isolation | PASS | explicit side scope selected `staging_side_item_001` from `german-side:staging-active` |
| Active bank rollback | PASS | baseline restored to `active`, candidate became `archived`, one active German core version remained |
| Legacy API request without `language_code` | PASS | `/v1/quiz-items/next` returned `200`, `language_code=de`, `content_bank_id=german-core`, `bank_version_id=german-core:2026-06-12-baseline` |

Smoke row counts after proof:

| Table | Count |
|---|---:|
| `languages` | 5 |
| `content_banks` | 2 |
| `content_bank_versions` | 3 |
| `sources` | 2 |
| `quiz_items` | 2 |
| `consumers` | 2 |
| `entitlements` | 2 |
| `deliveries` | 2 |
| `selection_decisions` | 2 |
| `content_bank_activation_events` | 3 |

## Rollback Proof

Rollback flow:

1. Inserted `german-core:staging-rollout-candidate` as `audit`.
2. Activated `german-core:staging-rollout-candidate`.
3. Rolled back to `german-core:2026-06-12-baseline`.

Final German core bank versions:

| Bank version | Status |
|---|---|
| `german-core:2026-06-12-baseline` | `active` |
| `german-core:staging-rollout-candidate` | `archived` |

Rollback result: PASS.

## Decision

Final decision: GO for production rollout planning.

Production rollout execution remains NO-GO until a separate production rollout
plan is approved with fresh production backup, operator window, production
commands and rollback/restore owner.
