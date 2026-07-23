import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
class ApplicationShellV900Tests(unittest.TestCase):
    def test_base_has_one_shell(self):
        base=(ROOT/'hub/templates/base.html').read_text(encoding='utf-8')
        self.assertEqual(base.count('{% include "application_shell.html" %}'),1)
        self.assertEqual(base.count('/static/application-shell.js'),1)
        self.assertEqual(base.count('/static/application-shell.css'),1)
    def test_old_shell_scripts_removed(self):
        base=(ROOT/'hub/templates/base.html').read_text(encoding='utf-8')
        for old in ('navigation-v7.js','navigation-v7.1.js','navigation-v8.js','breadcrumb-v8.1.js','layout-v8.1.js'):
            self.assertNotIn(old,base)
    def test_shell_has_single_chrome(self):
        shell=(ROOT/'hub/templates/application_shell.html').read_text(encoding='utf-8')
        self.assertEqual(shell.count('class="app-sidebar"'),1)
        self.assertEqual(shell.count('class="app-topbar"'),1)
        self.assertEqual(shell.count('class="app-breadcrumbs"'),1)
if __name__=='__main__': unittest.main()
