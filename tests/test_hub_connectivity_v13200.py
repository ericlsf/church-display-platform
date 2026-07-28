import json
from unittest.mock import MagicMock, patch

from services.hub_connectivity import test_hub_url as check_hub_url


def test_hub_url_reports_reachable_with_latency():
    response = MagicMock()
    response.getcode.return_value = 200
    response.read.return_value = json.dumps({"ok": True}).encode()
    response.__enter__.return_value = response

    with patch("services.hub_connectivity.urlopen", return_value=response):
        result = check_hub_url("https://hub.example.org")

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["latency_ms"] >= 1


def test_hub_url_rejects_invalid_address_without_request():
    with patch("services.hub_connectivity.urlopen") as opener:
        result = check_hub_url("not a url")

    assert result["ok"] is False
    assert result["message"] == "No valid URL is configured."
    opener.assert_not_called()


def test_setup_page_has_separate_visual_url_indicators():
    template = open(
        "hub/templates/setup.html",
        encoding="utf-8",
    ).read()

    assert 'data-connectivity-status="local"' in template
    assert 'data-connectivity-status="public"' in template
    assert 'data-test-connectivity="all"' in template
