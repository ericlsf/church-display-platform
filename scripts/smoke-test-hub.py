#!/usr/bin/env python3
"""Smoke-test every safe GET route with route-specific expectations."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "hub"
sys.path.insert(0, str(HUB))

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("CHURCH_DISPLAY_TESTING", "1")

import app as hub_app  # noqa: E402


SKIP_ENDPOINT_PREFIXES = ("static",)

SKIP_PATH_PARTS = (
    "<",
    "/api/v1/display-releases/",
)

DEFAULT_ALLOWED = {
    200,
    204,
    301,
    302,
    303,
    307,
    308,
    401,
    403,
    404,
}

ROUTE_EXPECTATIONS = {
    "/api/v1/jobs/next": {
        "allowed": {400},
        "reason": "requires display_id query parameter",
    },
    "/api/v1/content/manifest": {
        "allowed": {502},
        "reason": "content backend may be unavailable in generic test context",
    },
}


def get_flask_app():
    candidate = getattr(hub_app, "app", None)
    if candidate is not None:
        return candidate

    factory = getattr(hub_app, "create_app", None)
    if factory is not None:
        return factory()

    raise RuntimeError(
        "hub/app.py exposes neither `app` nor `create_app()`"
    )


def route_paths(app):
    rows = []

    for rule in app.url_map.iter_rules():
        if "GET" not in rule.methods:
            continue
        if rule.endpoint.startswith(SKIP_ENDPOINT_PREFIXES):
            continue

        path = str(rule)
        if any(part in path for part in SKIP_PATH_PARTS):
            continue

        rows.append((rule.endpoint, path))

    return sorted(set(rows))


def allowed_statuses(path):
    expectation = ROUTE_EXPECTATIONS.get(path)
    if not expectation:
        return DEFAULT_ALLOWED, ""

    return (
        DEFAULT_ALLOWED | set(expectation["allowed"]),
        expectation["reason"],
    )


def main() -> int:
    app = get_flask_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        PROPAGATE_EXCEPTIONS=True,
    )

    failures = []

    with app.test_client() as client:
        for endpoint, path in route_paths(app):
            try:
                response = client.get(
                    path,
                    follow_redirects=False,
                    headers={"X-Smoke-Test": "1"},
                )
                status = response.status_code
                allowed, reason = allowed_statuses(path)

                if status not in allowed:
                    failures.append(
                        (endpoint, path, f"HTTP {status}")
                    )
                    print(
                        f"FAIL  {status} {path} "
                        f"({endpoint})"
                    )
                else:
                    suffix = f" — {reason}" if reason and status not in DEFAULT_ALLOWED else ""
                    print(
                        f"PASS  {status} {path} "
                        f"({endpoint}){suffix}"
                    )

            except Exception as exc:
                failures.append(
                    (
                        endpoint,
                        path,
                        f"{type(exc).__name__}: {exc}",
                    )
                )
                print(
                    f"FAIL  {path} ({endpoint}): "
                    f"{type(exc).__name__}: {exc}"
                )

    print()
    if failures:
        print(f"Hub smoke test failed: {len(failures)} route(s)")
        return 1

    print("Hub smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
