from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'hub').exists():
    ROOT = ROOT / 'payload'


class MediaV971Tests(unittest.TestCase):
    def test_template_uses_v971_assets_and_accessible_drawer(self):
        text = (ROOT / 'hub/templates/media.html').read_text()
        self.assertIn('media-library-v971.css', text)
        self.assertIn('media-library-v971.js', text)
        self.assertIn('aria-modal="true"', text)
        self.assertIn('id="media-details-title"', text)

    def test_drawer_polish_styles(self):
        text = (ROOT / 'hub/static/media-library-v971.css').read_text()
        self.assertIn('width:min(360px,92vw)', text)
        self.assertIn('background:rgba(3,8,14,.26)', text)
        self.assertIn('.is-status-pill', text)
        self.assertIn('overflow-wrap:anywhere', text)

    def test_drawer_interactions_and_metadata_formatting(self):
        text = (ROOT / 'hub/static/media-library-v971.js').read_text()
        self.assertIn('formatModified', text)
        self.assertIn("activeCard === item", text)
        self.assertIn("event.key === 'Escape'", text)
        self.assertIn("event.key === 'ArrowRight'", text)
        self.assertIn("event.key === ' '", text)
        self.assertIn('Pending sync', text)

    def test_v970_workflow_is_preserved(self):
        text = (ROOT / 'hub/static/media-library-v971.js').read_text()
        self.assertIn('text/media-path', text)
        self.assertIn('data-remove-playlist', text)
        self.assertIn('addCard', text)
        self.assertIn('updateDisplayCount', text)


if __name__ == '__main__':
    unittest.main()
