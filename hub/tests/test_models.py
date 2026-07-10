import unittest
from services.models import DeployPayload, PlaylistRef, ValidationError


class ModelTests(unittest.TestCase):
    def test_playlist_ref_normalizes(self):
        ref = PlaylistRef.from_mapping({"remote": "", "folder": "/Weekly/"})
        self.assertEqual(ref.remote, "gdrive")
        self.assertEqual(ref.folder, "Weekly")

    def test_playlist_ref_requires_folder(self):
        with self.assertRaises(ValidationError):
            PlaylistRef.from_mapping({})

    def test_deploy_payload_deduplicates_order(self):
        payload = DeployPayload.from_mapping({"folder": "Weekly", "playlist_order": ["a.jpg", "a.jpg", "b.mp4"]})
        self.assertEqual(payload.playlist_order, ["a.jpg", "b.mp4"])


if __name__ == "__main__":
    unittest.main()
