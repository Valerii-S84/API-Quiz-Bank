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


if __name__ == "__main__":
    unittest.main()
