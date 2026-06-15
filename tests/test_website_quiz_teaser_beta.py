from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.candidate_pool_builder import rebuild_candidate_pools  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection_models import SelectionFilters, SelectionRequest  # noqa: E402
from quizbank_mvp.selection_queue_filler import refill_selection_queue_for_request  # noqa: E402
from quizbank_mvp.selection import QuizBankProblem  # noqa: E402
from quizbank_mvp.trusted_delivery import ensure_delivery_outcome_status  # noqa: E402
from tools.provision_website_quiz_teaser_consumer import (  # noqa: E402
    CONSUMER_ID,
    report_markdown,
    run_provisioning,
    write_report,
    write_secret_env,
)


BASE_ITEM = json.loads(
    (ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()[0]
)
APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class WebsiteQuizTeaserBetaTests(unittest.TestCase):
    def test_website_teaser_consumer_receives_scoped_answer_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.sqlite3"
            initialize_database(db_path)
            seed_control_fixture(
                db_path,
                ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl",
                "approved",
            )
            seed_consumer(db_path, CONSUMER_ID, 5, ["A2"], ["T10"])
            seed_api_credential(db_path, CONSUMER_ID, "website_key")
            seed_entitlement(db_path, CONSUMER_ID, ["A2"], ["T10"])
            warm_queue(db_path, CONSUMER_ID, "A2", ("T10",))

            response = TestClient(create_app(db_path)).post(
                "/v1/quiz-items/next",
                json={"consumer_id": CONSUMER_ID, "cefr_level": "A2", "theme_ids": ["T10"]},
                headers={
                    "X-Consumer-Id": CONSUMER_ID,
                    "X-QuizBank-API-Key": "website_key",
                    "X-QuizBank-Quota-Key": "test-session-feedback",
                },
            )

        self.assertEqual(response.status_code, 200)
        quiz = response.json()["quiz_item"]
        self.assertEqual(quiz["feedback"]["correctAnswerId"], "option_1")
        self.assertIn("explanation", quiz["feedback"])
        self.assertNotIn("answer_key", quiz)

    def test_website_teaser_requires_quota_scope_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.sqlite3"
            initialize_database(db_path)
            seed_control_fixture(
                db_path,
                ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl",
                "approved",
            )
            seed_consumer(db_path, CONSUMER_ID, 5, ["A2"], ["T10"])
            seed_api_credential(db_path, CONSUMER_ID, "website_key")
            seed_entitlement(db_path, CONSUMER_ID, ["A2"], ["T10"])

            response = TestClient(create_app(db_path)).post(
                "/v1/quiz-items/next",
                json={"consumer_id": CONSUMER_ID, "cefr_level": "A2", "theme_ids": ["T10"]},
                headers={"X-Consumer-Id": CONSUMER_ID, "X-QuizBank-API-Key": "website_key"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["reason_code"], "QUOTA_SCOPE_REQUIRED")

    def test_website_teaser_quota_is_scoped_per_session_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            db_path = workspace / "runtime.sqlite3"
            fixture_path = workspace / "items.jsonl"
            self.write_runtime_fixture(fixture_path, 3)
            initialize_database(db_path)
            seed_control_fixture(db_path, fixture_path, "approved")
            seed_consumer(db_path, CONSUMER_ID, 1, ["A2"], ["T10"])
            seed_api_credential(db_path, CONSUMER_ID, "website_key")
            seed_entitlement(db_path, CONSUMER_ID, ["A2"], ["T10"])
            warm_queue(db_path, CONSUMER_ID, "A2", ("T10",))
            client = TestClient(create_app(db_path))

            first_scope = self.next_item_for_scope(client, "session-a")
            same_scope = self.next_item_for_scope(client, "session-a")
            second_scope = self.next_item_for_scope(client, "session-b")

            with sqlite3.connect(db_path) as connection:
                connection.row_factory = sqlite3.Row
                quota_rows = connection.execute(
                    """
                    SELECT feature, used_count, quota_limit
                    FROM quota_usage
                    WHERE consumer_id = ?
                    ORDER BY feature
                    """,
                    (CONSUMER_ID,),
                ).fetchall()

        self.assertEqual(first_scope.status_code, 200)
        self.assertEqual(same_scope.status_code, 429)
        self.assertEqual(same_scope.json()["reason_code"], "QUOTA_EXCEEDED")
        self.assertEqual(second_scope.status_code, 200)
        self.assertEqual(len(quota_rows), 2)
        self.assertTrue(all(row["feature"].startswith("quiz_delivery:scope:") for row in quota_rows))
        self.assertFalse(any("session-a" in row["feature"] for row in quota_rows))
        self.assertEqual([row["used_count"] for row in quota_rows], [1, 1])
        self.assertEqual([row["quota_limit"] for row in quota_rows], [1, 1])

    def test_provisioning_report_masks_credentials_and_leaves_consumer_active(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            quizbank_dir = workspace / "QuizBank"
            db_path = workspace / "website.sqlite3"
            report_path = workspace / "report.md"
            secret_env_path = workspace / "website.env"
            self.write_quizbank_fixture(quizbank_dir)

            args = argparse.Namespace(
                quizbank_dir=quizbank_dir,
                db_path=db_path,
                report_out=report_path,
                secret_env_out=secret_env_path,
                api_base_url="https://api.example.test",
                consumer_api_key_env="TEST_WBQT_CONSUMER_KEY_NOT_SET",
                edge_api_key_env="TEST_WBQT_EDGE_KEY_NOT_SET",
            )
            evidence = run_provisioning(args)
            write_report(report_path, evidence)
            write_secret_env(secret_env_path, evidence["env_handoff"]["raw"])
            report = report_markdown(evidence)

            self.assertNotIn(evidence["env_handoff"]["raw"]["QUIZ_BANK_CONSUMER_API_KEY"], report)
            self.assertIn("QUIZ_BANK_CONSUMER_ID=website_quiz_teaser", report)
            self.assertEqual(evidence["flow"]["statuses"], [200, 200, 200, 200, 200])
            self.assertEqual(evidence["flow"]["quota_denial"]["reason_code"], "QUOTA_EXCEEDED")
            self.assertEqual(evidence["suspended"]["reason_code"], "CONSUMER_NOT_ACTIVE")
            self.assertEqual(evidence["revoked"]["reason_code"], "AUTH_CREDENTIAL_INACTIVE")

            consumer, deliveries, active_credentials = self.runtime_counts(db_path)
            self.assertEqual(consumer["status"], "active")
            self.assertEqual(deliveries, 5)
            self.assertEqual(active_credentials, 2)
            self.assertTrue(report_path.exists())
            self.assertTrue(secret_env_path.exists())

    def write_quizbank_fixture(self, quizbank_dir: Path) -> None:
        quizbank_dir.mkdir()
        self.write_source_file(
            quizbank_dir / "Artikel_Sprint_Bank_A1_B2_1000.csv",
            [self.item("artikel_1"), self.item("artikel_2"), self.item("alltag_1")],
        )
        self.write_source_file(
            quizbank_dir / "Modalverben_Bank_210.csv",
            [self.item("verben_1")],
        )
        self.write_source_file(
            quizbank_dir / "Preposition_Natural_Usage_Bank_A1_B1_70.csv",
            [self.item("praepositionen_1")],
        )

    def write_source_file(self, path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def write_runtime_fixture(self, path: Path, count: int) -> None:
        rows = []
        for index in range(count):
            row = dict(BASE_ITEM)
            row.update({"item_id": f"runtime_item_{index}", "status": "approved"})
            rows.append(json.dumps(row))
        path.write_text("\n".join(rows), encoding="utf-8")

    def next_item_for_scope(self, client: TestClient, quota_scope_key: str):
        return client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": CONSUMER_ID, "cefr_level": "A2", "theme_ids": ["T10"]},
            headers={
                "X-Consumer-Id": CONSUMER_ID,
                "X-QuizBank-API-Key": "website_key",
                "X-QuizBank-Quota-Key": quota_scope_key,
            },
        )

    def item(self, item_id: str) -> dict[str, str]:
        row = dict(BASE_ITEM)
        row.update(
            {
                "item_id": item_id,
                "status": "published",
                "sublevel": "A2",
                "theme_id": "T02",
                "subtheme_id": "alltag",
                "coverage_cell_id": f"A2::T02::O02::P01::{item_id}",
                "tags": "theme:t02;level:a2;objective:o02;pattern:p01",
            }
        )
        return row

    def runtime_counts(self, db_path: Path):
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        try:
            consumer = connection.execute(
                "SELECT * FROM consumers WHERE consumer_id = ?",
                (CONSUMER_ID,),
            ).fetchone()
            deliveries = connection.execute(
                "SELECT COUNT(*) AS count FROM deliveries WHERE consumer_id = ?",
                (CONSUMER_ID,),
            ).fetchone()["count"]
            active_credentials = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM api_credentials
                WHERE consumer_id LIKE 'website_quiz_teaser%' AND status = 'active'
                """,
            ).fetchone()["count"]
            return consumer, deliveries, active_credentials
        finally:
            connection.close()


class WebsiteTrustedDeliveryCoverageTests(unittest.TestCase):
    def test_trusted_item_lookup_returns_feedback_without_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.sqlite3"
            initialize_database(db_path)
            seed_control_fixture(db_path, APPROVED_FIXTURE, "approved")
            self.seed_website_access(db_path)

            response = TestClient(create_app(db_path)).get(
                "/v1/quiz-items/approved_traceable_001",
                headers={"X-Consumer-Id": CONSUMER_ID, "X-QuizBank-API-Key": "website_key"},
            )
            with sqlite3.connect(db_path) as connection:
                delivery_count = connection.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["quiz_item"]["feedback"]["correctAnswerId"], "option_1")
        self.assertTrue(response.json()["interaction"]["answer_key_included"])
        self.assertEqual(delivery_count, 0)

    def test_delivery_outcome_records_status_and_rejects_invalid_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.sqlite3"
            initialize_database(db_path)
            seed_control_fixture(db_path, APPROVED_FIXTURE, "approved")
            self.seed_website_access(db_path)
            warm_queue(db_path, CONSUMER_ID, "A2", ("T10",))
            client = TestClient(create_app(db_path))
            delivery_id = self.next_item_for_scope(client, "trusted-outcome").json()["delivery_id"]

            sent = client.post(
                f"/v1/deliveries/{delivery_id}/outcome",
                json={"status": "sent", "reason": "published to edge"},
                headers={"X-Consumer-Id": CONSUMER_ID, "X-QuizBank-API-Key": "website_key"},
            )
            missing = client.post(
                "/v1/deliveries/missing_delivery/outcome",
                json={"status": "sent"},
                headers={"X-Consumer-Id": CONSUMER_ID, "X-QuizBank-API-Key": "website_key"},
            )

        self.assertEqual(sent.status_code, 200)
        self.assertEqual(sent.json()["status"], "sent")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["reason_code"], "DELIVERY_NOT_FOUND")

        with self.assertRaises(QuizBankProblem) as problem:
            ensure_delivery_outcome_status("queued")
        self.assertEqual(problem.exception.reason_code, "DELIVERY_OUTCOME_INVALID")

    def test_trusted_item_lookup_rejects_missing_or_out_of_scope_item(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.sqlite3"
            initialize_database(db_path)
            seed_control_fixture(db_path, APPROVED_FIXTURE, "approved")
            self.seed_website_access(db_path, themes=["T11"])
            client = TestClient(create_app(db_path))

            missing = client.get(
                "/v1/quiz-items/missing_item",
                headers={"X-Consumer-Id": CONSUMER_ID, "X-QuizBank-API-Key": "website_key"},
            )
            denied = client.get(
                "/v1/quiz-items/approved_traceable_001",
                headers={"X-Consumer-Id": CONSUMER_ID, "X-QuizBank-API-Key": "website_key"},
            )

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["reason_code"], "QUIZ_ITEM_NOT_FOUND")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.json()["reason_code"], "CONSUMER_THEME_NOT_ALLOWED")

    def next_item_for_scope(self, client: TestClient, quota_scope_key: str):
        return client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": CONSUMER_ID, "cefr_level": "A2", "theme_ids": ["T10"]},
            headers={
                "X-Consumer-Id": CONSUMER_ID,
                "X-QuizBank-API-Key": "website_key",
                "X-QuizBank-Quota-Key": quota_scope_key,
            },
        )

    def seed_website_access(
        self,
        db_path: Path,
        levels: list[str] | None = None,
        themes: list[str] | None = None,
    ) -> None:
        resolved_levels = levels or ["A2"]
        resolved_themes = themes or ["T10"]
        seed_consumer(db_path, CONSUMER_ID, 5, resolved_levels, resolved_themes)
        seed_api_credential(db_path, CONSUMER_ID, "website_key")
        seed_entitlement(db_path, CONSUMER_ID, resolved_levels, resolved_themes)


def warm_queue(
    db_path: Path,
    consumer_id: str,
    cefr_level: str | None,
    theme_ids: tuple[str, ...],
) -> None:
    rebuild_candidate_pools(db_path)
    refill_selection_queue_for_request(
        db_path,
        SelectionRequest(
            consumer_id=consumer_id,
            filters=SelectionFilters(cefr_level=cefr_level, theme_ids=theme_ids),
        ),
    )


if __name__ == "__main__":
    unittest.main()
