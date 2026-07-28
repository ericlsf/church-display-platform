from services.hub_version import current_hub_version


def test_hub_version_comes_from_authoritative_file(monkeypatch):
    monkeypatch.delenv("HUB_VERSION", raising=False)
    assert current_hub_version() == "v13.20.0"


def test_hub_version_can_be_overridden(monkeypatch):
    monkeypatch.setenv("HUB_VERSION", "13.14.1")
    assert current_hub_version() == "v13.14.1"
