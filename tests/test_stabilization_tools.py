import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class StabilizationToolTests(unittest.TestCase):
    def test_tools_exist(self):
        names = [
            "validate-runtime-imports.py",
            "smoke-test-hub.py",
            "verify-backup-restore.py",
            "build-production-release.py",
            "production-gate.sh",
        ]

        for name in names:
            self.assertTrue(
                (ROOT / "scripts" / name).exists(),
                name,
            )

    def test_python_tools_parse(self):
        names = [
            "validate-runtime-imports.py",
            "smoke-test-hub.py",
            "verify-backup-restore.py",
            "build-production-release.py",
        ]

        for name in names:
            path = ROOT / "scripts" / name
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")


if __name__ == "__main__":
    unittest.main()
