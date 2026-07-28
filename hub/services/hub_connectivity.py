import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def test_hub_url(base_url, timeout=5):
    """Check a configured Hub URL against its lightweight public health probe."""
    base_url = (base_url or "").strip().rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {
            "ok": False,
            "url": base_url,
            "message": "No valid URL is configured.",
        }

    probe_url = f"{base_url}/setup/connectivity-health"
    started = time.monotonic()
    try:
        request = Request(
            probe_url,
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            payload = json.loads(response.read().decode("utf-8"))

        latency_ms = max(1, round((time.monotonic() - started) * 1000))
        reachable = status_code == 200 and payload.get("ok") is True
        return {
            "ok": reachable,
            "url": base_url,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "message": (
                "Reachable"
                if reachable
                else "The address responded, but it was not this Hub."
            ),
        }
    except HTTPError as exc:
        message = f"HTTP {exc.code}"
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        message = str(getattr(exc, "reason", exc)) or "Connection failed"

    return {
        "ok": False,
        "url": base_url,
        "message": message,
    }
