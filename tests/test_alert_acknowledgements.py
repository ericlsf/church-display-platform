import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.alert_acknowledgements as acknowledgements


class AlertAcknowledgementTests(unittest.TestCase):
    def test_acknowledge_and_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "alerts.json"

            with patch.object(
                acknowledgements,
                "STATE_FILE",
                state,
            ):
                acknowledgements.acknowledge_alert(
                    "welcome-center:offline",
                    user="admin",
                )

                current = (
                    acknowledgements
                    .list_acknowledgements()
                )

                self.assertIn(
                    "welcome-center:offline",
                    current,
                )

                acknowledgements.clear_acknowledgement(
                    "welcome-center:offline"
                )

                current = (
                    acknowledgements
                    .list_acknowledgements()
                )

                self.assertNotIn(
                    "welcome-center:offline",
                    current,
                )


if __name__ == "__main__":
    unittest.main()
