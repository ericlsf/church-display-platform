import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.alert_rules as alert_rules


class AlertRulesTests(unittest.TestCase):
    def test_rules_are_persisted_and_clamped(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "rules.json"

            with patch.object(
                alert_rules,
                "RULES_FILE",
                state,
            ):
                saved = alert_rules.save_alert_rules({
                    "offline_delay_minutes": 2000,
                    "disk_warning_percent": 82,
                    "disk_critical_percent": 91,
                })

                self.assertEqual(
                    saved["offline_delay_minutes"],
                    1440,
                )
                self.assertTrue(state.exists())


if __name__ == "__main__":
    unittest.main()
