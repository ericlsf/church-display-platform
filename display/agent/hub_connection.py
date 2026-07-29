"""HTTP helpers that automatically fail over between Hub endpoints."""

from __future__ import annotations

import urllib.error
import urllib.request
import json

from agent.config import APP_DIR, HUB_URLS


ENDPOINTS_FILE = APP_DIR / "config" / "hub_endpoints.json"


def _normalize(url):
    value = str(url or "").strip().rstrip("/")
    return value if value.startswith(("http://", "https://")) else ""


def _load_urls():
    urls = list(HUB_URLS)
    try:
        saved = json.loads(ENDPOINTS_FILE.read_text(encoding="utf-8"))
        urls.extend(saved.get("urls", []))
    except (OSError, ValueError, TypeError):
        pass
    return tuple(dict.fromkeys(filter(None, (_normalize(url) for url in urls))))


_hub_urls = _load_urls()
_active_hub_url = _hub_urls[0]


def hub_urls():
    """Try the last working endpoint first, then every configured fallback."""
    return (_active_hub_url,) + tuple(
        url for url in _hub_urls if url != _active_hub_url
    )


def active_hub_url():
    return _active_hub_url


def update_hub_urls(urls):
    """Remember Hub endpoints supplied by a successful heartbeat response."""
    global _hub_urls
    discovered = tuple(
        dict.fromkeys(filter(None, (_normalize(url) for url in (urls or []))))
    )
    if not discovered:
        return
    _hub_urls = tuple(
        dict.fromkeys((*discovered, *_hub_urls))
    )
    ENDPOINTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENDPOINTS_FILE.write_text(
        json.dumps({"urls": list(_hub_urls)}, indent=2),
        encoding="utf-8",
    )


def open_hub(
    path,
    *,
    data=None,
    headers=None,
    method=None,
    timeout=10,
    validate_response=None,
):
    global _active_hub_url
    last_error = None

    for base_url in hub_urls():
        request = urllib.request.Request(
            f"{base_url}{path}",
            data=data,
            headers=headers or {},
            method=method,
        )
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
            if validate_response and not validate_response(response):
                content_type = response.headers.get(
                    "Content-Type",
                    "unknown content type",
                )
                response.close()
                last_error = RuntimeError(
                    f"Hub endpoint returned an invalid response "
                    f"({content_type})"
                )
                continue
            _active_hub_url = base_url
            return response
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc

    if last_error:
        raise last_error
    raise RuntimeError("No Hub endpoint is configured")
