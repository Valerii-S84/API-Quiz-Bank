from __future__ import annotations

from tests.test_mvp_runtime import MvpRuntimeCase


class MvpTaxonomyRuntimeTests(MvpRuntimeCase):
    def test_taxonomy_endpoints_return_canonical_levels_and_topics(self) -> None:
        levels = self.client.get("/v1/levels")
        topics = self.client.get("/v1/topics?language_code=de")

        self.assertEqual(levels.status_code, 200)
        self.assertEqual(
            [level["cefr_level"] for level in levels.json()["data"]],
            ["A1", "A2", "B1", "B2", "C1", "C2"],
        )
        self.assertEqual(topics.status_code, 200)
        self.assertEqual(len(topics.json()["data"]), 18)
        self.assertEqual(topics.json()["data"][0]["topic_id"], "T01")
        self.assertEqual(topics.json()["data"][0]["theme_code"], "T01")
        self.assertEqual(topics.json()["data"][0]["theme_id"], "T01")
        self.assertEqual(topics.json()["data"][0]["language_code"], "de")
        self.assertEqual(topics.json()["data"][0]["label_status"], "canonical")

    def test_topics_reject_non_german_public_language_scope(self) -> None:
        response = self.client.get("/v1/topics?language_code=en")

        self.assertEqual(response.status_code, 422)
