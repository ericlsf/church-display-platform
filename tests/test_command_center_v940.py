import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "hub/templates/command_center.html").read_text()
CSS = (ROOT / "hub/static/command-center-v940.css").read_text()
JS = (ROOT / "hub/static/command-center-v940.js").read_text()

class CommandCenterV940Tests(unittest.TestCase):
    def test_fleet_health_ring(self):
        self.assertIn("health-ring", TEMPLATE)
        self.assertIn('data-summary="health_percent"', TEMPLATE)
    def test_activity_timeline_and_map(self):
        self.assertIn("activity-timeline", TEMPLATE)
        self.assertIn("campus-map", TEMPLATE)
    def test_job_drawer(self):
        self.assertIn("data-job-drawer", TEMPLATE)
        self.assertIn("data-open-jobs", TEMPLATE)
    def test_command_palette(self):
        self.assertIn("data-command-palette", TEMPLATE)
        self.assertIn('event.key.toLowerCase() === "k"', JS)
    def test_assets_are_versioned(self):
        self.assertIn("command-center-v940.css", TEMPLATE)
        self.assertIn("command-center-v940.js", TEMPLATE)

if __name__ == "__main__": unittest.main()
