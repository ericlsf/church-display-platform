import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "smoke-test-hub.py"


def load_script():
    spec = importlib.util.spec_from_file_location(
        "smoke_test_hub",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SmokeExpectationTests(unittest.TestCase):
    def test_jobs_next_allows_missing_parameter_response(self):
        module = load_script()
        allowed, reason = module.allowed_statuses(
            "/api/v1/jobs/next"
        )
        self.assertIn(400, allowed)
        self.assertIn("display_id", reason)

    def test_manifest_allows_backend_unavailable_response(self):
        module = load_script()
        allowed, reason = module.allowed_statuses(
            "/api/v1/content/manifest"
        )
        self.assertIn(502, allowed)
        self.assertIn("backend", reason)


if __name__ == "__main__":
    unittest.main()
