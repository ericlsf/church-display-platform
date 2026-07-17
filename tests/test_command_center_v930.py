from pathlib import Path
import unittest


class CommandCenterV930Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = Path("hub/templates/command_center.html").read_text(encoding="utf-8")
        cls.css = Path("hub/static/command-center-v930.css").read_text(encoding="utf-8")

    def test_single_shell_breadcrumb(self):
        self.assertNotIn('class="breadcrumbs"', self.template)
        self.assertIn('<h1>Command Center</h1>', self.template)

    def test_compact_attention_layout(self):
        self.assertIn("command-health-inline", self.template)
        self.assertIn("command-alert-actions", self.template)
        self.assertIn("Open</a>", self.template)
        self.assertIn("Fix</a>", self.template)

    def test_quick_actions_are_buttons(self):
        self.assertEqual(self.template.count("command-action-button"), 4)
        self.assertIn(".command-action-button", self.css)

    def test_visual_metrics(self):
        self.assertIn("command-metric-icon", self.template)
        self.assertIn(".command-metric-icon", self.css)


if __name__ == "__main__":
    unittest.main()
