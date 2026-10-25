import unittest

from app.workflows.rules import (
    parse_screening_response,
    relevance_route,
    screening_status,
)


class ScreeningScoreTests(unittest.TestCase):
    def test_parses_json_and_markdown_fenced_json(self):
        expected = {"score": 81, "reasoning": "Relevant experience."}
        self.assertEqual(
            parse_screening_response('{"score":81,"reasoning":"Relevant experience."}'),
            expected,
        )
        self.assertEqual(
            parse_screening_response(
                '```json\n{"score":81,"reasoning":"Relevant experience."}\n```'
            ),
            expected,
        )

    def test_rejects_invalid_or_incomplete_model_output(self):
        for response in (
            "not json",
            '["not", "an", "object"]',
            '{"score":101,"reasoning":"Too high."}',
            '{"score":50}',
            '{"score":"80","reasoning":"Not numeric."}',
        ):
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    parse_screening_response(response)

    def test_routes_exact_threshold_boundaries(self):
        expected_statuses = {
            81: "AUTO_ACCEPTED",
            80: "PENDING_HUMAN_REVIEW",
            60: "PENDING_HUMAN_REVIEW",
            59: "AUTO_REJECTED",
        }
        for score, expected in expected_statuses.items():
            with self.subTest(score=score):
                self.assertEqual(screening_status(score, 80, 60), expected)


class RagRoutingTests(unittest.TestCase):
    def test_irrelevant_context_uses_fallback_after_retry_limit(self):
        self.assertEqual(
            relevance_route(False, 2, 2),
            "fallback",
        )
        self.assertEqual(relevance_route(True, 0, 2), "generate")
        self.assertEqual(relevance_route(False, 0, 2), "rewrite")


if __name__ == "__main__":
    unittest.main()
