import unittest
from unittest.mock import patch

from services.deployment_verification import (
    deployment_verification_state,
)


class DeploymentVerificationV562Tests(unittest.TestCase):
    @patch(
        "services.deployment_verification.exact_live_telemetry",
        return_value={
            "heartbeat_version": "5.6.2",
            "version": "5.6.2",
        },
    )
    @patch(
        "services.deployment_verification.list_jobs",
        return_value=[
            {
                "id": "job-1",
                "display_id": "welcome-center",
                "type": "deploy_update",
                "status": "success",
                "payload": {
                    "target": "v5.6.2",
                },
                "created_at": "2026-07-15T16:00:00",
            }
        ],
    )
    def test_prefixed_target_matches_plain_heartbeat(
        self,
        _jobs,
        _telemetry,
    ):
        result = deployment_verification_state(
            "welcome-center"
        )

        self.assertTrue(result["verified"])
        self.assertEqual(
            result["state"],
            "verified",
        )


if __name__ == "__main__":
    unittest.main()
