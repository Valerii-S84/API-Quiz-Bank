from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import translate_sqlite_placeholders  # noqa: E402


class DatabaseBackendContractTests(unittest.TestCase):
    def test_postgresql_adapter_translates_positional_placeholders(self) -> None:
        sql = "SELECT * FROM consumers WHERE consumer_id = ? AND status = ?"

        translated = translate_sqlite_placeholders(sql, ("consumer", "active"))

        self.assertEqual(
            translated,
            "SELECT * FROM consumers WHERE consumer_id = %s AND status = %s",
        )

    def test_postgresql_adapter_translates_named_placeholders(self) -> None:
        sql = "INSERT INTO consumers (consumer_id, status) VALUES (:consumer_id, :status)"

        translated = translate_sqlite_placeholders(
            sql,
            {"consumer_id": "consumer", "status": "active"},
        )

        self.assertEqual(
            translated,
            "INSERT INTO consumers (consumer_id, status) VALUES (%(consumer_id)s, %(status)s)",
        )


if __name__ == "__main__":
    unittest.main()
