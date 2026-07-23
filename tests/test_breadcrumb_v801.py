import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class BreadcrumbV801Tests(unittest.TestCase):
    def test_breadcrumb_height_is_corrected(self):
        css = (
            ROOT
            / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "--v8-breadcrumb-height: 36px",
            css,
        )
        self.assertIn(
            "overflow: visible !important",
            css,
        )

    def test_runtime_enforcement_exists(self):
        script = (
            ROOT
            / "hub/static/breadcrumb-v8.1.js"
        )

        self.assertTrue(script.is_file())

        text = script.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "enforceBreadcrumbLayout",
            text,
        )
        self.assertIn(
            "MutationObserver",
            text,
        )


if __name__ == "__main__":
    unittest.main()
