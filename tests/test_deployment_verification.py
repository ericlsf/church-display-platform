import unittest
from unittest.mock import patch

from services.deployment_verification import (
    deployment_verification_state,
)


class DeploymentVerificationTests(unittest.TestCase):
    @patch(
        "services.deployment_verification.exact_live_telemetry",
        return_value={
            "heartbeat_version": "v5.6.0",
            "version": "v5.6.0",
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
                    "target": "v5.6.0",
                },
                "created_at": "2026-07-15T16:00:00",
            }
        ],
    )
    def test_success_requires_matching_heartbeat(
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

    @patch(
        "services.deployment_verification.exact_live_telemetry",
        return_value={
            "heartbeat_version": "4.3.0",
            "version": "4.3.0",
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
                    "target": "v5.6.0",
                },
                "created_at": "2026-07-15T16:00:00",
            }
        ],
    )
    def test_mismatch_is_verification_failure(
        self,
        _jobs,
        _telemetry,
    ):
        result = deployment_verification_state(
            "welcome-center"
        )

        self.assertFalse(result["verified"])
        self.assertEqual(
            result["state"],
            "verification_failed",
        )


if __name__ == "__main__":
    unittest.main()
