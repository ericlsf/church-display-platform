import unittest
from unittest.mock import patch
from services.deployment_timeline import deployment_timeline

class DeploymentTimelineTests(unittest.TestCase):
    @patch("services.deployment_timeline.deployment_verification_state", return_value={
        "state":"verified","job":{"status":"success","progress":100}
    })
    def test_verified_timeline_completes(self, _):
        result = deployment_timeline("welcome-center")
        self.assertEqual(result["current_stage"], "verified")
        self.assertTrue(all(stage["state"] == "complete" for stage in result["stages"]))

if __name__ == "__main__":
    unittest.main()
