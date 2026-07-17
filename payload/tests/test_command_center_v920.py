from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class CommandCenterV920Tests(unittest.TestCase):
 def setUp(self): self.text=(ROOT/'hub/templates/command_center.html').read_text()
 def test_operational_hierarchy_exists(self): self.assertLess(self.text.index('id="action-required"'),self.text.index('command-metrics'))
 def test_empty_sections_are_conditional(self):
  self.assertIn('data-job-drawer',self.text); self.assertIn('{% for job in active_jobs %}',self.text); self.assertIn('No active jobs.',self.text); self.assertIn('{% if not active_jobs and not outdated_rows and not pending_displays and not maintenance_rows %}',self.text)
 def test_live_refresh_and_toasts_exist(self): self.assertIn('command-toast-stack',self.text); self.assertIn('command-center-v940.js',self.text)
if __name__=='__main__': unittest.main()
