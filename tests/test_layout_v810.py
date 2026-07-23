import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

class LayoutV810Tests(unittest.TestCase):
    def test_sidebar_and_breadcrumb(self):
        css=(ROOT/"hub/static/style.css").read_text(encoding="utf-8").replace(" ","")
        self.assertIn("--v8-sidebar-width:252px",css)
        self.assertIn("--v8-breadcrumb-height:34px",css)
        self.assertIn("top:var(--v8-topbar-height)!important",css)

    def test_runtime_refinement(self):
        js=(ROOT/"hub/static/layout-v8.1.js").read_text(encoding="utf-8")
        self.assertIn("simplifyTopbar",js)
        self.assertIn("improveDisplayRows",js)
        self.assertIn('"padding-top"', js)
        self.assertIn('"92px"', js)

if __name__=="__main__":
    unittest.main()
