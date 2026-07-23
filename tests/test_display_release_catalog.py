import unittest
from unittest.mock import patch

from services.display_release_catalog import (
    latest_display_tag,
    list_display_release_tags,
)


class DisplayReleaseCatalogTests(unittest.TestCase):
    @patch("services.display_release_catalog._git")
    def test_hub_only_tags_do_not_create_display_updates(self, git):
        values = {
            ("tag", "--sort=v:refname"): "v13.3.1\nv13.4.0\nv13.4.1\nv13.4.2",
            ("rev-parse", "v13.3.1:display"): "tree-a",
            ("rev-parse", "v13.4.0:display"): "tree-b",
            ("rev-parse", "v13.4.1:display"): "tree-b",
            ("rev-parse", "v13.4.2:display"): "tree-b",
        }
        git.side_effect = lambda *args: values.get(args, "")

        self.assertEqual(
            list_display_release_tags(),
            ["v13.4.0", "v13.3.1"],
        )
        self.assertEqual(latest_display_tag(), "v13.4.0")
