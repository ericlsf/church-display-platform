import unittest
from unittest.mock import patch

from services.deployment_guard import (
    existing_deployment,
    unique_display_ids,
)


class DeploymentGuardTests(unittest.TestCase):
    def test_unique_display_ids_preserves_order(self):
        self.assertEqual(
            unique_display_ids(
                ["welcome-center", "welcome-center", "", "lobby"]
            ),
            ["welcome-center", "lobby"],
        )

    @patch("services.deployment_guard.list_jobs")
    def test_existing_active_deployment_is_reused(self, list_jobs):
        list_jobs.return_value = [{
            "id": "job-1",
            "type": "deploy_update",
            "display_id": "welcome-center",
            "status": "queued",
            "payload": {
                "target": "v4.6.0",
                "dry_run": False,
            },
        }]

        job = existing_deployment(
            "welcome-center",
            "v4.6.0",
            "false",
        )
        self.assertEqual(job["id"], "job-1")


if __name__ == "__main__":
    unittest.main()
