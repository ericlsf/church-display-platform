import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class FleetOperationsFormLayoutTests(unittest.TestCase):
    def test_one_column_layout_exists(self):
        css = (
            ROOT / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v6.4.1 fleet operations form layout",
            css,
        )
        self.assertIn(
            "grid-template-columns: minmax(0, 1fr)",
            css,
        )

    def test_checkbox_size_is_normal(self):
        css = (
            ROOT / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'input[type="checkbox"]',
            css,
        )
        self.assertIn(
            "width: 1rem !important",
            css,
        )


if __name__ == "__main__":
    unittest.main()
