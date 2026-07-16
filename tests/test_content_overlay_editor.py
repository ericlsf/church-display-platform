import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ContentOverlayEditorTests(unittest.TestCase):
    def test_editor_asset_supports_dirty_state(self):
        path = (
            ROOT
            / "hub/static/content-overlay-editor.js"
        )
        text = path.read_text(encoding="utf-8")

        self.assertIn("Unsaved changes", text)
        self.assertIn("beforeunload", text)
        self.assertIn("data-preview-text", text)


if __name__ == "__main__":
    unittest.main()
