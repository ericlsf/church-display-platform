import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from services import jobs


class FleetHistoryCleanupTests(unittest.TestCase):
    def test_acknowledged_and_resolved_are_one_state(self):
        record = jobs.normalize_job({
            "status": "failed",
            "acknowledged": True,
        })
        self.assertTrue(record["resolved"])
        self.assertFalse(jobs.job_is_unresolved_failure(record))

    def test_unresolved_failure_is_counted(self):
        record = jobs.normalize_job({
            "status": "timed_out",
            "acknowledged": False,
        })
        self.assertTrue(jobs.job_is_unresolved_failure(record))

    def test_retention_removes_old_resolved_but_keeps_unresolved(self):
        old = (datetime.now() - timedelta(days=120)).isoformat(timespec="seconds")
        records = {
            "jobs": [
                {
                    "id": "resolved-old",
                    "status": "failed",
                    "acknowledged": True,
                    "updated_at": old,
                },
                {
                    "id": "unresolved-old",
                    "status": "failed",
                    "acknowledged": False,
                    "updated_at": old,
                },
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "jobs.json"
            path.write_text(json.dumps(records), encoding="utf-8")
            with patch.object(jobs, "JOBS_FILE", path):
                result = jobs.list_jobs(100)

        self.assertEqual(
            [item["id"] for item in result],
            ["unresolved-old"],
        )

    def test_readable_time_hides_raw_iso_format(self):
        self.assertEqual(
            jobs.format_job_time("2026-07-24T08:15:00"),
            "Jul 24, 2026 8:15 AM",
        )


if __name__ == "__main__":
    unittest.main()
