from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import services.alert_acknowledgements as acknowledgements
from services.alert_policy import apply_alert_policy


class AlertHygieneTests(TestCase):
    def test_bulk_acknowledgement_records_each_alert(self):
        with TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "alert_acknowledgements.json"

            with patch.object(acknowledgements, "STATE_FILE", state_file):
                count = acknowledgements.acknowledge_alerts(
                    ["health:display-a", "job:failed-1", ""],
                    user="operator",
                    note="Reviewed together",
                )
                records = acknowledgements.list_acknowledgements()

        self.assertEqual(count, 2)
        self.assertEqual(
            set(records),
            {"health:display-a", "job:failed-1"},
        )
        self.assertTrue(
            all(
                record["acknowledged_by"] == "operator"
                for record in records.values()
            )
        )
        self.assertTrue(
            all(
                record["note"] == "Reviewed together"
                for record in records.values()
            )
        )

    def test_bulk_acknowledgement_deduplicates_keys(self):
        with TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "alert_acknowledgements.json"

            with patch.object(acknowledgements, "STATE_FILE", state_file):
                count = acknowledgements.acknowledge_alerts(
                    ["job:1", "job:1"],
                )

        self.assertEqual(count, 1)

    @patch(
        "services.alert_policy.load_alert_rules",
        return_value={
            "quiet_hours_enabled": False,
            "categories": {},
        },
    )
    def test_policy_recalculates_acknowledged_counts(self, _rules):
        acknowledged = {
            "key": "job:1",
            "severity": "warning",
            "acknowledged": True,
        }
        active = {
            "key": "health:1",
            "severity": "warning",
            "acknowledged": False,
        }

        result = apply_alert_policy({
            "alerts": [acknowledged, active],
            "active_alerts": [acknowledged, active],
            "acknowledged_alerts": [],
            "counts": {},
        })

        self.assertEqual(result["counts"]["active"], 1)
        self.assertEqual(result["counts"]["acknowledged"], 1)
        self.assertEqual(result["counts"]["warning"], 1)
        self.assertEqual(
            [item["key"] for item in result["active_alerts"]],
            ["health:1"],
        )
        self.assertEqual(
            [
                item["key"]
                for item in result["acknowledged_alerts"]
            ],
            ["job:1"],
        )
