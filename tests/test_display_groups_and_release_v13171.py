from pathlib import Path


def test_display_editor_uses_saved_group_assignments_only():
    template = Path("hub/templates/displays.html").read_text(encoding="utf-8")

    assert 'name="group_ids"' in template
    assert 'name="group"' not in template


def test_release_marks_both_hub_and_display_as_v13171():
    assert Path("hub/VERSION").read_text(encoding="utf-8").strip() == "v13.17.1"
    assert Path("display/VERSION").read_text(encoding="utf-8").strip() == "13.17.1"
