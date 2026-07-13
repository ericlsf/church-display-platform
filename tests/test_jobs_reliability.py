import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.jobs as jobs


class JobReliabilityTests(unittest.TestCase):
    def test_cancel_and_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            with patch.object(jobs, "JOBS_FILE", path), patch.object(jobs, "maintenance_enabled", return_value=False):
                job = jobs.create_job("display-1", "sync_now")
                cancelled = jobs.request_cancel(job["id"])
                self.assertEqual(cancelled["status"], "cancelled")
                retried = jobs.retry_job(job["id"])
                self.assertEqual(retried["status"], "queued")
                claimed = jobs.get_next_job("display-1")
                self.assertEqual(claimed["status"], "running")
                self.assertEqual(claimed["attempt"], 1)

    def test_maintenance_blocks_disruptive_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            with patch.object(jobs, "JOBS_FILE", path), patch.object(jobs, "maintenance_enabled", return_value=True):
                jobs.create_job("display-1", "sync_now")
                self.assertIsNone(jobs.get_next_job("display-1"))


if __name__ == "__main__":
    unittest.main()
