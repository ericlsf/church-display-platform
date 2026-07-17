import unittest
from unittest.mock import patch
from services.fleet_command_center import build_fleet_command_center

class FleetCommandCenterTests(unittest.TestCase):
    @patch("services.fleet_command_center.build_alert_center_state",return_value={"counts":{"active":1}})
    @patch("services.fleet_command_center.list_jobs",return_value=[{"id":"job-1","display_id":"welcome-center","type":"deploy_update","status":"running","progress":50}])
    @patch("services.fleet_command_center.enrich_fleet_rows",side_effect=lambda rows:rows)
    @patch("services.fleet_command_center.fleet_rows",return_value=[
        {"id":"welcome-center","name":"Welcome Center","online":True,"health_score":100,"update_available":True,"version":"9.0.1","latest_tag":"v9.1.0","sync_state":"success","media_count":3,"sync_folder":"Missions","heartbeat_age_seconds":5},
        {"id":"lobby","name":"Lobby","online":False,"health_score":0,"sync_state":"unknown"},
    ])
    def test_metrics_and_recommendations(self,_rows,_enrich,_jobs,_alerts):
        result=build_fleet_command_center()
        self.assertEqual(result["metrics"]["online"],1)
        self.assertEqual(result["metrics"]["offline"],1)
        self.assertEqual(result["metrics"]["updating"],1)
        self.assertEqual(len(result["actions"]),2)

if __name__=="__main__": unittest.main()
