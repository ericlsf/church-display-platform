#!/usr/bin/env python3
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/display_details.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def remove_preview_card(text: str) -> str:
    marker = '<div class="content-preview-card">'
    start = text.find(marker)

    if start < 0:
        return text

    depth = 0
    pos = start

    while pos < len(text):
        next_open = text.find("<div", pos)
        next_close = text.find("</div>", pos)

        if next_close < 0:
            raise SystemExit(
                "Could not isolate content preview card"
            )

        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            pos = next_close + len("</div>")

            if depth == 0:
                return text[:start] + text[pos:]

    raise SystemExit(
        "Could not isolate content preview card"
    )


def remove_preview_script(text: str) -> str:
    pattern = re.compile(
        r'\s*<script\s+src="/static/'
        r'content-overlay-editor\.js"\s*></script>\s*'
    )
    return pattern.sub("\n", text)


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")
    text = remove_preview_card(text)
    text = remove_preview_script(text)

    # The editor no longer needs a two-column wrapper.
    text = text.replace(
        '<div class="content-editor-grid">',
        '<div class="content-editor-simple">',
    )

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.9.3 simplified content editor */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += (
            "\n"
            + marker
            + "\n"
            + CSS_APPEND.read_text(encoding="utf-8")
        )
        CSS.write_text(text, encoding="utf-8")

    CSS_APPEND.unlink()


def main():
    patch_template()
    patch_css()
    print(
        "v5.9.3 simplified content editor applied."
    )


if __name__ == "__main__":
    main()
