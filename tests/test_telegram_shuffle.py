from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.telegram_delivery import (  # noqa: E402
    build_telegram_poll_payload,
    shuffled_telegram_options,
    telegram_api_payload,
)


class TelegramShuffleTests(unittest.TestCase):
    def test_shuffle_is_stable_for_same_delivery_salt(self) -> None:
        options = ["richtig", "falsch 1", "falsch 2", "falsch 3"]

        first_shuffle = shuffled_telegram_options(options, "0", "delivery_stable")
        second_shuffle = shuffled_telegram_options(options, "0", "delivery_stable")

        self.assertEqual(first_shuffle, second_shuffle)

    def test_shuffle_varies_across_delivery_salts(self) -> None:
        options = ["richtig", "falsch 1", "falsch 2", "falsch 3"]

        shuffled_orders = {
            tuple(shuffled_telegram_options(options, "0", f"delivery_{index}")[0])
            for index in range(30)
        }

        self.assertGreater(len(shuffled_orders), 1)

    def test_shuffle_moves_source_first_answer_out_of_first_position(self) -> None:
        options = ["richtig", "falsch 1", "falsch 2", "falsch 3"]

        positions = [
            shuffled_telegram_options(options, "0", f"delivery_{index}")[1][0]
            for index in range(100)
        ]

        self.assertNotIn(0, positions)
        self.assertGreater(len(set(positions)), 1)

    def test_two_option_quiz_moves_source_first_answer_to_second_position(self) -> None:
        options = ["richtig", "falsch"]

        for index in range(30):
            shuffled, correct_ids = shuffled_telegram_options(options, "0", f"salt_{index}")
            self.assertEqual(correct_ids, [1])
            self.assertEqual(shuffled[correct_ids[0]], "richtig")

    def test_maximum_option_quiz_preserves_all_options_and_correct_mapping(self) -> None:
        options = [f"option {index}" for index in range(12)]
        options[0] = "richtig"

        shuffled, correct_ids = shuffled_telegram_options(options, "0", "maximum_options")

        self.assertCountEqual(shuffled, options)
        self.assertNotEqual(correct_ids, [0])
        self.assertEqual(shuffled[correct_ids[0]], "richtig")

    def test_each_source_answer_position_keeps_correct_answer_off_first_position(self) -> None:
        for answer_index in range(4):
            options = [f"falsch {index}" for index in range(4)]
            options[answer_index] = "richtig"

            for salt_index in range(30):
                shuffled, correct_ids = shuffled_telegram_options(
                    options,
                    str(answer_index),
                    f"answer_{answer_index}_salt_{salt_index}",
                )
                self.assertNotEqual(correct_ids, [0])
                self.assertEqual(shuffled[correct_ids[0]], "richtig")

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
        self.assertEqual(telegram_api_payload(payload)["correct_option_id"], correct_id)

    def test_non_first_source_answer_still_keeps_correct_mapping(self) -> None:
        options = ["falsch 1", "richtig", "falsch 2", "falsch 3"]

        for index in range(50):
            shuffled, correct_ids = shuffled_telegram_options(options, "1", f"salt_{index}")
            self.assertEqual(shuffled[correct_ids[0]], "richtig")


if __name__ == "__main__":
    unittest.main()
