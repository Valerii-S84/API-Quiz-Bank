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
from quizbank_mvp.database import (  # noqa: E402
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
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

            response = TestClient(create_app(db_path)).post(
                "/v1/quiz-items/next",
                json={"consumer_id": CONSUMER_ID, "cefr_level": "A2", "theme_ids": ["T10"]},
                headers={"X-Consumer-Id": CONSUMER_ID, "X-QuizBank-API-Key": "website_key"},
            )

        self.assertEqual(response.status_code, 200)
        quiz = response.json()["quiz_item"]
        self.assertEqual(quiz["feedback"]["correctAnswerId"], "option_1")
        self.assertIn("explanation", quiz["feedback"])
        self.assertNotIn("answer_key", quiz)

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


if __name__ == "__main__":
    unittest.main()
