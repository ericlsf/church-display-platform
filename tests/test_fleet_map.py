import unittest

from services.fleet_map import summarize


class FleetMapTests(unittest.TestCase):
    def test_summary(self):
        rows = [
            {"readiness": "ready"},
            {"readiness": "offline"},
            {"readiness": "maintenance"},
            {"readiness": "needs_attention"},
        ]

        result = summarize(rows)

        self.assertEqual(result["total"], 4)
        self.assertEqual(result["ready"], 1)
        self.assertEqual(result["offline"], 1)
        self.assertEqual(result["maintenance"], 1)
        self.assertEqual(result["attention"], 1)


if __name__ == "__main__":
    unittest.main()
