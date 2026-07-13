import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class RequestQualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_job_lifecycle(self):
        import services.jobs as jobs

        path = Path(self.tmp.name) / "jobs.json"
        with patch.object(jobs, "JOBS_FILE", path), patch.object(jobs, "maintenance_enabled", return_value=False):
            created = jobs.create_job("display-one", "heartbeat", {"check": True})
            claimed = jobs.get_next_job("display-one")
            self.assertEqual(created["id"], claimed["id"])
            self.assertEqual("running", claimed["status"])
            updated = jobs.update_job(created["id"], "success", 100, "done")
            self.assertEqual("success", updated["status"])
            self.assertEqual(100, updated["progress"])

    def test_heartbeat_store_round_trip(self):
        import services.heartbeat_store as store

        path = Path(self.tmp.name) / "heartbeats.json"
        with patch.object(store, "HEARTBEATS_FILE", path):
            store.save_heartbeats({"heartbeats": {"one": {"online": True}}})
            data = store.load_heartbeats()
            self.assertTrue(data["heartbeats"]["one"]["online"])

    def test_error_template_exists(self):
        root = Path(__file__).resolve().parent.parent
        self.assertTrue((root / "hub/templates/error.html").exists())


if __name__ == "__main__":
    unittest.main()
