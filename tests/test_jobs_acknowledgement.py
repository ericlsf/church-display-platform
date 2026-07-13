import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services import jobs

class JobAcknowledgementTests(unittest.TestCase):
    def test_acknowledge_preserves_failed_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"jobs.json"
            with patch.object(jobs,"JOBS_FILE",file):
                job=jobs.create_job("one","sync_now")
                jobs.update_job(job["id"],status="failed",message="bad")
                result=jobs.acknowledge_job(job["id"],"known issue")
                self.assertEqual(result["status"],"failed")
                self.assertTrue(result["acknowledged"] )
                self.assertEqual(result["acknowledged_note"],"known issue")

if __name__ == "__main__": unittest.main()
