import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.display_artifacts as artifacts


class DisplayArtifactTests(unittest.TestCase):
    def test_job_checksum_matches_persisted_file(self):
        payload = b"exact-package-bytes"
        checksum = hashlib.sha256(payload).hexdigest()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(artifacts, "ARTIFACT_DIR", root), \
                 patch.object(artifacts, "INDEX_FILE", root / "index.json"), \
                 patch(
                     "services.display_artifacts.build_release_package",
                     return_value={
                         "target": "v-test",
                         "commit": "abc123",
                         "bytes": payload,
                         "sha256": checksum,
                         "size": len(payload),
                     },
                 ):
                metadata = artifacts.create_artifact("v-test")
                stored = artifacts.artifact_path(checksum).read_bytes()

        self.assertEqual(metadata["sha256"], checksum)
        self.assertEqual(stored, payload)
        self.assertEqual(hashlib.sha256(stored).hexdigest(), checksum)


if __name__ == "__main__":
    unittest.main()
