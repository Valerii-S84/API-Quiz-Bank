from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.telegram_delivery import (  # noqa: E402
    build_telegram_poll_payload,
    shuffled_telegram_options,
)


class TelegramShuffleTests(unittest.TestCase):
    def test_shuffle_moves_source_first_answer_out_of_first_position(self) -> None:
        options = ["richtig", "falsch 1", "falsch 2", "falsch 3"]

        positions = [
            shuffled_telegram_options(options, "0", f"delivery_{index}")[1][0]
            for index in range(100)
        ]

        self.assertNotIn(0, positions)
        self.assertGreater(len(set(positions)), 1)

    def test_payload_recomputes_correct_option_after_shuffle(self) -> None:
        payload = build_telegram_poll_payload(
            "@test_channel",
            {
                "delivery_id": "deliv_929cefb8a50844b6",
                "consumer_id": "visual_test",
                "item_id": "item",
                "prompt": "Welche Antwort passt?",
                "stem_text": "Ich muss morgen einen Termin ___.",
                "options_json": '["buchen", "trinken", "lesen", "öffnen"]',
                "answer_key": "0",
                "explanation": "Hier passt buchen.",
            },
        )

        correct_id = payload["correct_option_ids"][0]
        self.assertNotEqual(correct_id, 0)
        self.assertEqual(payload["options"][correct_id], "buchen")

    def test_non_first_source_answer_still_keeps_correct_mapping(self) -> None:
        options = ["falsch 1", "richtig", "falsch 2", "falsch 3"]

        for index in range(50):
            shuffled, correct_ids = shuffled_telegram_options(options, "1", f"salt_{index}")
            self.assertEqual(shuffled[correct_ids[0]], "richtig")


if __name__ == "__main__":
    unittest.main()
