import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from services.automatic_rollback import (
    automatic_rollback_state,
)


class AutomaticRollbackTests(unittest.TestCase):
    @patch(
        "services.automatic_rollback.create_job",
        return_value={"id": "rollback-1"},
    )
    @patch(
        "services.automatic_rollback._rollback_already_exists",
        return_value=None,
    )
    @patch(
        "services.automatic_rollback.deployment_verification_state",
        return_value={
            "state": "verification_failed",
            "target_version": "v5.8.0",
            "reported_version": "v5.7.4",
            "job": {
                "id": "deploy-1",
                "created_at": (
                    datetime.now(timezone.utc)
                    - timedelta(minutes=10)
                ).isoformat(),
            },
        },
    )
    def test_timeout_queues_rollback(
        self,
        _verification,
        _existing,
        create_job,
    ):
        result = automatic_rollback_state(
            "welcome-center",
            timeout_seconds=60,
        )

        self.assertTrue(result["queued"])
        create_job.assert_called_once()


if __name__ == "__main__":
    unittest.main()
