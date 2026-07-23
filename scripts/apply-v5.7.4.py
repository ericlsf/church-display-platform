#!/usr/bin/env python3
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/display_details.html"


def remove_legacy_scripts(text):
    legacy = (
        "/static/deployment-verification.js",
        "/static/deployment-timeline.js",
    )

    for source in legacy:
        pattern = re.compile(
            r'\s*<script\s+src="'
            + re.escape(source)
            + r'"\s*></script>\s*'
        )
        text = pattern.sub("\n", text)

    return text


def ensure_controller(text):
    script = (
        '<script src="/static/'
        'live-deployment-status.js"></script>'
    )

    # Deduplicate the controller if an older installer inserted it twice.
    text = text.replace(script, "")
    end = text.rfind("{% endblock %}")

    if end < 0:
        raise SystemExit(
            "Could not find display-details block ending"
        )

    return (
        text[:end]
        + script
        + "\n"
        + text[end:]
    )


def main():
    text = TEMPLATE.read_text(encoding="utf-8")
    text = remove_legacy_scripts(text)
    text = ensure_controller(text)
    TEMPLATE.write_text(text, encoding="utf-8")

    print(
        "v5.7.4 stable upgrade-card controller applied."
    )


if __name__ == "__main__":
    main()
