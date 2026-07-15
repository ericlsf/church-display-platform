import unittest

from services.health_diagnostics import build_health_diagnostics


class HealthDiagnosticsTests(unittest.TestCase):
    def test_failed_check_has_action(self):
        result = build_health_diagnostics({
            "health_score": 80,
            "checks": {
                "online": True,
                "player": True,
                "playlist": True,
                "media": True,
                "sync": False,
            },
        })

        self.assertEqual(result["score"], 80)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["failed_checks"][0]["action"],
            "sync",
        )

    def test_all_healthy(self):
        result = build_health_diagnostics({
            "health_score": 100,
            "checks": {
                "online": True,
                "player": True,
                "playlist": True,
                "media": True,
                "sync": True,
            },
        })

        self.assertTrue(result["all_healthy"])
        self.assertEqual(result["failed_count"], 0)


if __name__ == "__main__":
    unittest.main()
