import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class FleetOperationsControlGroupTests(unittest.TestCase):
    def test_script_groups_requested_controls(self):
        script = (
            ROOT
            / "hub/static/fleet-operations-layout.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "fleet-version-mode-row",
            script,
        )
        self.assertIn(
            "fleet-overlay-row",
            script,
        )
        self.assertIn(
            "fleet-checkbox-line",
            script,
        )

    def test_css_defines_two_column_rows(self):
        css = (
            ROOT
            / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v6.4.2 Fleet Operations grouped controls",
            css,
        )
        self.assertIn(
            ".fleet-version-mode-row",
            css,
        )
        self.assertIn(
            ".fleet-overlay-row",
            css,
        )


if __name__ == "__main__":
    unittest.main()
