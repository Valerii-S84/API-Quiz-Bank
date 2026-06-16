from __future__ import annotations

import unittest

from tests.repository_test_support import ROOT


POSTGRESQL_RUNTIME_SQL = (
    ROOT / "database" / "postgresql" / "001_create_runtime.sql"
).read_text(encoding="utf-8")
POSTGRESQL_IMPORT_SQL = (
    ROOT / "database" / "postgresql" / "002_add_import_contract.sql"
).read_text(encoding="utf-8")
POSTGRESQL_RUNTIME_EVIDENCE_SQL = (
    ROOT / "database" / "postgresql" / "003_add_runtime_delivery_evidence.sql"
).read_text(encoding="utf-8")
POSTGRESQL_VISUAL_DELIVERY_SQL = (
    ROOT / "database" / "postgresql" / "007_add_visual_delivery.sql"
).read_text(encoding="utf-8")
POSTGRESQL_QUOTA_PERIOD_SQL = (
    ROOT / "database" / "postgresql" / "008_use_text_quota_usage_period_key.sql"
).read_text(encoding="utf-8")
POSTGRESQL_IMAGE_QUALITY_SQL = (
    ROOT / "database" / "postgresql" / "009_add_image_quality_policy.sql"
).read_text(encoding="utf-8")
POSTGRESQL_VISUAL_MODE_METADATA_SQL = (
    ROOT / "database" / "postgresql" / "010_add_visual_mode_policy_metadata.sql"
).read_text(encoding="utf-8")
POSTGRESQL_NEXT_ROUTE_INDEX_SQL = (
    ROOT / "database" / "postgresql" / "011_add_next_route_selection_indexes.sql"
).read_text(encoding="utf-8")
POSTGRESQL_MULTILINGUAL_BANK_SQL = (
    ROOT / "database" / "postgresql" / "012_add_multilingual_bank_foundation.sql"
).read_text(encoding="utf-8")
POSTGRESQL_CHANNEL_TARIFF_SCOPE_SQL = (
    ROOT / "database" / "postgresql" / "013_add_channel_tariff_scope.sql"
).read_text(encoding="utf-8")
POSTGRESQL_PRECOMPUTED_SELECTION_SQL = (
    ROOT / "database" / "postgresql" / "014_add_precomputed_selection_state.sql"
).read_text(encoding="utf-8")
POSTGRESQL_QUEUE_CLAIM_INDEX_SQL = (
    ROOT / "database" / "postgresql" / "015_optimize_selection_queue_claim_available_index.sql"
).read_text(encoding="utf-8")


class PostgreSQLContractTests(unittest.TestCase):
    def test_runtime_seed_keeps_delivery_traceability_columns(self) -> None:
        for required_fragment in [
            "source_id TEXT NOT NULL REFERENCES sources(source_id)",
            "quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id)",
            "item_status TEXT NOT NULL CHECK (item_status IN ('approved', 'published'))",
            "entitlement_id TEXT NOT NULL REFERENCES entitlements(entitlement_id)",
            "quota_usage_id TEXT NOT NULL REFERENCES quota_usage(quota_usage_id)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_RUNTIME_SQL)

    def test_quota_usage_period_key_supports_daily_and_monthly_windows(self) -> None:
        self.assertIn("usage_date TEXT NOT NULL", POSTGRESQL_RUNTIME_SQL)
        self.assertIn("ALTER COLUMN usage_date TYPE TEXT", POSTGRESQL_QUOTA_PERIOD_SQL)

    def test_runtime_seed_allows_unreviewed_draft_import_timestamps(self) -> None:
        self.assertIn("reviewed_at TIMESTAMPTZ,\n    level_locked", POSTGRESQL_RUNTIME_SQL)
        self.assertIn("locked_at TIMESTAMPTZ\n);", POSTGRESQL_RUNTIME_SQL)
        self.assertNotIn("reviewed_at TIMESTAMPTZ NOT NULL", POSTGRESQL_RUNTIME_SQL)
        self.assertNotIn("locked_at TIMESTAMPTZ NOT NULL", POSTGRESQL_RUNTIME_SQL)

    def test_import_contract_defines_batch_and_validation_tables(self) -> None:
        for required_table in [
            "CREATE TABLE import_batches",
            "CREATE TABLE import_batch_items",
            "CREATE TABLE import_validation_results",
        ]:
            self.assertIn(required_table, POSTGRESQL_IMPORT_SQL)

    def test_import_batches_preserve_source_and_report_lineage(self) -> None:
        for required_fragment in [
            "source_id TEXT NOT NULL REFERENCES sources(source_id)",
            "parser_profile_id TEXT NOT NULL CHECK (parser_profile_id <> '')",
            "import_mode TEXT NOT NULL CHECK (import_mode IN ('dry_run', 'commit'))",
            "source_checksum_sha256 ~ '^[0-9a-f]{64}$'",
            "report_uri TEXT NOT NULL CHECK (report_uri <> '')",
            "created_by TEXT NOT NULL CHECK (created_by <> '')",
            "UNIQUE (import_batch_id, source_id)",
            "accepted_candidate_count + rejected_candidate_count <= row_count_detected",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_IMPORT_SQL)

    def test_runtime_evidence_tables_support_selection_and_telegram_logs(self) -> None:
        for required_fragment in [
            "CREATE TABLE telegram_delivery_results",
            "CREATE TABLE selection_decisions",
            "filters_json JSONB NOT NULL",
            "selected_score_json JSONB NOT NULL",
            "blocked_reason_counts_json JSONB NOT NULL",
            "idx_selection_decisions_consumer_created",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_RUNTIME_EVIDENCE_SQL)

    def test_import_batch_items_link_batches_to_quiz_items(self) -> None:
        for required_fragment in [
            "import_batch_id TEXT NOT NULL REFERENCES import_batches(import_batch_id)",
            "item_id TEXT NOT NULL REFERENCES quiz_items(item_id)",
            "source_id TEXT NOT NULL REFERENCES sources(source_id)",
            "source_item_id TEXT NOT NULL CHECK (source_item_id <> '')",
            "source_row_number INTEGER NOT NULL CHECK (source_row_number >= 1)",
            "content_hash_sha256 ~ '^[0-9a-f]{64}$'",
            "PRIMARY KEY (import_batch_id, item_id)",
            "UNIQUE (import_batch_id, source_item_id)",
            "REFERENCES import_batches(import_batch_id, source_id)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_IMPORT_SQL)

    def test_import_contract_indexes_lineage_queries(self) -> None:
        for required_index in [
            "idx_import_batches_source_status",
            "idx_import_batch_items_item",
            "idx_import_batch_items_source",
            "idx_import_validation_results_batch_severity",
        ]:
            self.assertIn(required_index, POSTGRESQL_IMPORT_SQL)

    def test_validation_results_require_rule_and_message(self) -> None:
        for required_fragment in [
            "severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error'))",
            "rule_id TEXT NOT NULL CHECK (rule_id <> '')",
            "message TEXT NOT NULL CHECK (message <> '')",
            "source_row_number INTEGER CHECK (source_row_number IS NULL OR source_row_number >= 1)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_IMPORT_SQL)

    def test_visual_delivery_mirror_defines_runtime_tables(self) -> None:
        for required_table in [
            "CREATE TABLE IF NOT EXISTS consumer_visual_settings",
            "CREATE TABLE IF NOT EXISTS visual_assets",
            "CREATE TABLE IF NOT EXISTS visual_prompt_audit",
            "CREATE TABLE IF NOT EXISTS visual_delivery_results",
            "CREATE TABLE IF NOT EXISTS visual_usage_events",
        ]:
            self.assertIn(required_table, POSTGRESQL_VISUAL_DELIVERY_SQL)

    def test_visual_delivery_mirror_keeps_constraints_and_foreign_keys(self) -> None:
        for required_fragment in [
            "consumer_id TEXT PRIMARY KEY REFERENCES consumers(consumer_id)",
            "quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id)",
            "delivery_id TEXT PRIMARY KEY REFERENCES deliveries(delivery_id)",
            "asset_id TEXT REFERENCES visual_assets(asset_id)",
            "delivery_mode IN ('text_only', 'image_standard', 'image_branded')",
            "qa_status IN ('approved', 'rejected', 'fallback_used', 'needs_review')",
            "visual_status IN ('sent', 'skipped', 'failed', 'fallback_used')",
            "cache_key TEXT NOT NULL UNIQUE CHECK (cache_key <> '')",
            "visual_mode IN (",
            "visual_target TEXT NOT NULL DEFAULT 'unknown'",
            "visual_prompt_policy_version TEXT NOT NULL DEFAULT 'unknown'",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_VISUAL_DELIVERY_SQL)

    def test_visual_mode_metadata_migration_adds_asset_and_audit_columns(self) -> None:
        for required_fragment in [
            "ALTER TABLE visual_assets",
            "ALTER TABLE visual_prompt_audit",
            "ADD COLUMN IF NOT EXISTS visual_mode",
            "ADD COLUMN IF NOT EXISTS visual_target",
            "ADD COLUMN IF NOT EXISTS visual_context_hint",
            "ADD COLUMN IF NOT EXISTS visual_prompt_policy_version",
            "'target_action'",
            "'symbolic_abstract'",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_VISUAL_MODE_METADATA_SQL)

    def test_visual_usage_events_include_cost_and_generation_statuses(self) -> None:
        for required_fragment in [
            "'cache_hit'",
            "'cache_miss'",
            "'generation_requested'",
            "'generation_succeeded'",
            "'generation_failed'",
            "'qa_approved'",
            "'qa_rejected'",
            "'fallback_used'",
            "estimated_cost_minor INTEGER NOT NULL CHECK (estimated_cost_minor >= 0)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_VISUAL_DELIVERY_SQL)

    def test_image_quality_policy_mirror_requires_low_medium_only(self) -> None:
        for required_fragment in [
            "CREATE TABLE IF NOT EXISTS quiz_item_image_quality_policy",
            "item_id TEXT PRIMARY KEY REFERENCES quiz_items(item_id) ON DELETE CASCADE",
            "theme_group IN ('simple_visual', 'situational', 'abstract_complex')",
            "image_quality_recommended IN ('low', 'medium')",
            "image_quality_source IN ('policy', 'override')",
            "image_quality_override IS NULL OR image_quality_override IN ('low', 'medium')",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_IMAGE_QUALITY_SQL)
        self.assertNotIn("'high'", POSTGRESQL_IMAGE_QUALITY_SQL)
        self.assertNotIn("'auto'", POSTGRESQL_IMAGE_QUALITY_SQL)

    def test_next_route_selection_indexes_cover_hot_path(self) -> None:
        for required_fragment in [
            "idx_quiz_items_selection_pool",
            "ON quiz_items(status, sublevel, theme_id, objective_id, pattern_id, item_id)",
            "idx_quiz_items_cell_lookup",
            "ON quiz_items(theme_id, pattern_id, item_id)",
            "idx_deliveries_item",
            "ON deliveries(quiz_item_id)",
            "idx_deliveries_item_selected_at",
            "ON deliveries(quiz_item_id, selected_at DESC)",
            "idx_deliveries_consumer_status_item",
            "ON deliveries(consumer_id, delivery_status, quiz_item_id)",
            "idx_deliveries_consumer_item_selected_at",
            "ON deliveries(consumer_id, quiz_item_id, selected_at DESC)",
            "idx_entitlements_consumer_feature_status",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_NEXT_ROUTE_INDEX_SQL)


class PostgreSQLMultilingualBankContractTests(unittest.TestCase):
    def test_multilingual_bank_migration_defines_reference_tables(self) -> None:
        for required_fragment in [
            "CREATE TABLE IF NOT EXISTS languages",
            "code TEXT PRIMARY KEY CHECK (code IN ('de', 'en', 'fr', 'es', 'nl'))",
            "CREATE TABLE IF NOT EXISTS content_banks",
            "UNIQUE (language_code, slug)",
            "CREATE TABLE IF NOT EXISTS content_bank_versions",
            "UNIQUE (content_bank_id, version)",
            "CREATE TABLE IF NOT EXISTS content_bank_activation_events",
            "uq_content_bank_versions_one_active",
            "WHERE status = 'active'",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_MULTILINGUAL_BANK_SQL)

    def test_multilingual_bank_versions_support_draft_audit_activation_flow(self) -> None:
        for required_fragment in [
            "status TEXT NOT NULL CHECK (status IN ('draft', 'audit', 'active', 'archived'))",
            "from_bank_version_id TEXT REFERENCES content_bank_versions(id)",
            "to_bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id)",
            "actor TEXT NOT NULL CHECK (actor <> '')",
            "reason TEXT NOT NULL CHECK (reason <> '')",
            "activated_at TIMESTAMPTZ NOT NULL",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_MULTILINGUAL_BANK_SQL)

    def test_multilingual_bank_migration_seeds_default_german_bank(self) -> None:
        for required_fragment in [
            "('de', 'German', TRUE, '2026-06-12T00:00:00Z')",
            "'german-core'",
            "'2026-06-12-baseline'",
            "'german-core:2026-06-12-baseline'",
            "'Baseline German content bank activation'",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_MULTILINGUAL_BANK_SQL)

    def test_multilingual_bank_migration_scopes_critical_tables(self) -> None:
        for table_name in [
            "sources",
            "quiz_items",
            "deliveries",
            "selection_decisions",
            "import_batches",
            "import_batch_items",
            "scheduled_delivery_slots",
            "visual_assets",
            "visual_prompt_audit",
            "visual_usage_events",
        ]:
            with self.subTest(table_name=table_name):
                self.assertIn(f"ALTER TABLE {table_name}", POSTGRESQL_MULTILINGUAL_BANK_SQL)

        for required_fragment in [
            "language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code)",
            "content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id)",
            "bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'",
            "REFERENCES content_bank_versions(id)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_MULTILINGUAL_BANK_SQL)

    def test_multilingual_bank_migration_adds_scoped_indexes(self) -> None:
        for required_fragment in [
            "DROP INDEX IF EXISTS idx_quiz_items_selection_pool",
            "ON quiz_items(\n        language_code,\n        bank_version_id,",
            "DROP INDEX IF EXISTS idx_quiz_items_cell_lookup",
            "ON quiz_items(language_code, bank_version_id, theme_id, pattern_id, item_id)",
            "idx_deliveries_scope_item",
            "ON deliveries(\n        consumer_id,\n        language_code,\n        bank_version_id,",
            "idx_selection_decisions_scope_created",
            "ON selection_decisions(consumer_id, language_code, bank_version_id, created_at)",
            "idx_visual_prompt_audit_scope_created",
            "ON visual_prompt_audit(language_code, content_bank_id, bank_version_id, created_at)",
            "idx_visual_usage_events_scope_created",
            "ON visual_usage_events(consumer_id, language_code, content_bank_id, bank_version_id, created_at)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_MULTILINGUAL_BANK_SQL)

    def test_multilingual_bank_migration_scopes_import_item_uniqueness(self) -> None:
        for required_fragment in [
            "uq_import_batch_items_bank_source_item",
            "ON import_batch_items(bank_version_id, source_id, source_item_id)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_MULTILINGUAL_BANK_SQL)

    def test_channel_tariff_migration_scopes_consumers_entitlements_and_quota(self) -> None:
        for required_fragment in [
            "ALTER TABLE consumers",
            "default_language_code TEXT NOT NULL DEFAULT 'de'",
            "allowed_language_codes_json TEXT NOT NULL DEFAULT '[\"de\"]'",
            "allowed_content_bank_ids_json TEXT NOT NULL DEFAULT '[\"german-core\"]'",
            "ALTER TABLE entitlements",
            "allowed_content_types_json TEXT NOT NULL DEFAULT '[]'",
            "ALTER TABLE quota_usage",
            "DROP CONSTRAINT IF EXISTS quota_usage_consumer_id_feature_usage_date_key",
            "ADD CONSTRAINT quota_usage_content_scope_key UNIQUE",
            "language_code,\n        content_bank_id,\n        bank_version_id",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_CHANNEL_TARIFF_SCOPE_SQL)

    def test_channel_tariff_migration_scopes_scheduled_slot_uniqueness(self) -> None:
        for required_fragment in [
            "ALTER TABLE scheduled_delivery_slots",
            "DROP CONSTRAINT IF EXISTS scheduled_delivery_slots_content_scope_key",
            "ADD CONSTRAINT scheduled_delivery_slots_content_scope_key UNIQUE",
            "slot_id,\n        language_code,\n        content_bank_id,\n        bank_version_id,",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_CHANNEL_TARIFF_SCOPE_SQL)


class PostgreSQLPrecomputedSelectionContractTests(unittest.TestCase):
    def test_precomputed_selection_migration_defines_runtime_tables(self) -> None:
        for required_fragment in [
            "CREATE TABLE IF NOT EXISTS candidate_pools",
            "CREATE TABLE IF NOT EXISTS candidate_pool_items",
            "CREATE TABLE IF NOT EXISTS consumer_delivery_state",
            "CREATE TABLE IF NOT EXISTS selection_queues",
            "CREATE TABLE IF NOT EXISTS selection_queue_items",
            "CREATE TABLE IF NOT EXISTS selection_diagnostic_events",
            "CREATE TABLE IF NOT EXISTS selection_diagnostic_outbox",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_PRECOMPUTED_SELECTION_SQL)

    def test_precomputed_selection_tables_preserve_scope_keys(self) -> None:
        for required_fragment in [
            "language_code TEXT NOT NULL REFERENCES languages(code)",
            "content_bank_id TEXT NOT NULL REFERENCES content_banks(id)",
            "bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id)",
            "PRIMARY KEY (\n        consumer_id,\n        channel_id,\n        language_code,",
            "UNIQUE (\n        consumer_id,\n        channel_id,\n        language_code,",
            "cefr_level TEXT NOT NULL DEFAULT ''",
            "theme_id TEXT NOT NULL DEFAULT ''",
            "objective_id TEXT NOT NULL DEFAULT ''",
            "pattern_id TEXT NOT NULL DEFAULT ''",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_PRECOMPUTED_SELECTION_SQL)

    def test_precomputed_selection_queue_claims_and_outbox_are_indexed(self) -> None:
        for required_fragment in [
            "idx_candidate_pools_scope_ready",
            "idx_candidate_pool_items_pool_rank",
            "idx_consumer_delivery_state_recent",
            "idx_selection_queues_scope_status",
            "idx_selection_queue_items_claim",
            "ON selection_queue_items(queue_id, claim_status, position, queue_item_id)",
            "idx_selection_diagnostic_events_consumer_created",
            "idx_selection_diagnostic_outbox_pending",
            "WHERE status IN ('pending', 'failed')",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_PRECOMPUTED_SELECTION_SQL)

        for required_fragment in [
            "idx_selection_queue_items_available_claim",
            "ON selection_queue_items(queue_id, position, queue_item_id)",
            "INCLUDE (item_id)",
            "WHERE claim_status = 'available'",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_QUEUE_CLAIM_INDEX_SQL)

    def test_precomputed_selection_diagnostics_use_jsonb_outbox_payloads(self) -> None:
        for required_fragment in [
            "score_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb",
            "payload_json JSONB NOT NULL DEFAULT '{}'::jsonb",
            "event_type IN (",
            "'diagnostic_snapshot'",
            "status IN ('pending', 'processing', 'published', 'failed', 'discarded')",
            "attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0)",
        ]:
            self.assertIn(required_fragment, POSTGRESQL_PRECOMPUTED_SELECTION_SQL)


if __name__ == "__main__":
    unittest.main()
