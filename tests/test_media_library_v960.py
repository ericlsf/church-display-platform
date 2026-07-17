from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MediaV960Tests(unittest.TestCase):
    def test_template_has_real_previews_and_drawer(self):
        text=(ROOT/'hub/templates/media.html').read_text()
        self.assertIn("media.media_preview", text)
        self.assertIn("data-details-drawer", text)
        self.assertIn("data-selected-display-count", text)
    def test_javascript_has_interactions(self):
        text=(ROOT/'hub/static/media-library-v960.js').read_text()
        self.assertIn("openDetails", text)
        self.assertIn("dragstart", text)
        self.assertIn("updateDisplayCount", text)
    def test_preview_route_is_restricted(self):
        text=(ROOT/'hub/routes/media.py').read_text()
        self.assertIn('@media_bp.route("/preview")', text)
        self.assertIn('if remote != configured_remote', text)
        self.assertIn('content_type.startswith("image/")', text)

if __name__ == '__main__': unittest.main()
