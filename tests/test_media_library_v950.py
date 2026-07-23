import unittest
from pathlib import Path
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]

class MediaLibraryV950Tests(unittest.TestCase):
    def test_template_exists_and_parses(self):
        text = (ROOT / "hub/templates/media.html").read_text(encoding="utf-8")
        Environment().parse(text)
        self.assertIn("data-media-workspace", text)
        self.assertIn("Sync selected displays", text)

    def test_assets_exist(self):
        css = (ROOT / "hub/static/media-library-v950.css").read_text(encoding="utf-8")
        js = (ROOT / "hub/static/media-library-v950.js").read_text(encoding="utf-8")
        self.assertIn(".media-card-grid", css)
        self.assertIn("applyFilters", js)
        self.assertIn("syncOrder", js)

    def test_existing_endpoints_preserved(self):
        route = (ROOT / "hub/routes/media.py").read_text(encoding="utf-8")
        self.assertIn('@media_bp.route("/order", methods=["POST"])', route)
        self.assertIn('@media_bp.route("/sync", methods=["POST"])', route)

if __name__ == "__main__":
    unittest.main()
