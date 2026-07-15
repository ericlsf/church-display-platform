#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "hub" / "templates" / "base.html"
DETAILS = ROOT / "hub" / "templates" / "display_details.html"
DETAILS_APPEND = (
    ROOT
    / "hub"
    / "templates"
    / "display_details.polish.append.html"
)


def patch_base():
    text = BASE.read_text(encoding="utf-8")
    tag = '<link rel="stylesheet" href="/static/operator-polish.css">'

    if tag not in text:
        head_end = text.find("</head>")
        if head_end < 0:
            raise SystemExit("Could not find </head> in base.html")
        text = text[:head_end] + tag + "\n" + text[head_end:]
        BASE.write_text(text, encoding="utf-8")


def patch_display_details():
    text = DETAILS.read_text(encoding="utf-8")

    if "data-live-display=" in text:
        return

    block = DETAILS_APPEND.read_text(encoding="utf-8")
    end = text.rfind("{% endblock %}")
    if end < 0:
        raise SystemExit(
            "Could not find content block ending in display_details.html"
        )

    DETAILS.write_text(
        text[:end] + block + "\n" + text[end:],
        encoding="utf-8",
    )
    DETAILS_APPEND.unlink()


def main():
    patch_base()
    patch_display_details()
    print("v5.2.0 visual polish applied.")


if __name__ == "__main__":
    main()
