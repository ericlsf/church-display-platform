import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.audit as audit


class AuditTests(unittest.TestCase):
    def test_sensitive_fields_are_redacted(self):
        cleaned = audit.sanitize_details({
            "username": "admin",
            "password": "secret",
            "token": "abc",
        })
        self.assertEqual(cleaned["username"], "admin")
        self.assertEqual(cleaned["password"], "[REDACTED]")
        self.assertEqual(cleaned["token"], "[REDACTED]")

    def test_append_and_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audit.jsonl"
            with patch.object(audit, "AUDIT_FILE", path):
                audit.append_audit(
                    "test.action",
                    actor="admin",
                    category="test",
                    details={"value": "ok"},
                )
                rows = audit.read_audit(limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["actor"], "admin")


if __name__ == "__main__":
    unittest.main()
