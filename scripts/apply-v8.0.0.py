#!/usr/bin/env python3
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "hub/templates/base.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"
PARTIAL = ROOT / "hub/templates/navigation_shell.html"


def patch_base():
    text = BASE.read_text(encoding="utf-8")

    include = (
        '{% include "navigation_shell.html" %}'
    )

    # Keep the existing include, since this release replaces the partial.
    if include not in text:
        body = re.search(
            r"<body\b[^>]*>",
            text,
            re.IGNORECASE,
        )

        if not body:
            raise SystemExit(
                "Could not find <body> in base.html"
            )

        text = (
            text[:body.end()]
            + "\n"
            + include
            + "\n"
            + text[body.end():]
        )

    script = (
        '<script src="/static/'
        'navigation-v8.js"></script>'
    )

    if script not in text:
        close = text.lower().rfind("</body>")

        if close < 0:
            raise SystemExit(
                "Could not find </body> in base.html"
            )

        text = (
            text[:close]
            + "\n"
            + script
            + "\n"
            + text[close:]
        )

    BASE.write_text(
        text,
        encoding="utf-8",
    )


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = (
        "/* v8.0.0 operator UI polish */"
    )

    text = CSS.read_text(
        encoding="utf-8"
    )

    if marker not in text:
        text += (
            "\n"
            + CSS_APPEND.read_text(
                encoding="utf-8"
            )
        )

        CSS.write_text(
            text,
            encoding="utf-8",
        )

    CSS_APPEND.unlink()


def validate_partial():
    text = PARTIAL.read_text(
        encoding="utf-8"
    )

    required = (
        "v8-sidebar-search",
        "data-v8-section",
        "data-nav-group-toggle",
        "data-command-button",
        "data-user-menu-toggle",
    )

    missing = [
        item
        for item in required
        if item not in text
    ]

    if missing:
        raise SystemExit(
            "Navigation partial missing: "
            + ", ".join(missing)
        )


def main():
    validate_partial()
    patch_base()
    patch_css()

    print(
        "v8.0.0 operator UI polish applied."
    )


if __name__ == "__main__":
    main()
