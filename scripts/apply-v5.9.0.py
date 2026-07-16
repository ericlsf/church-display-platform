#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DETAILS = ROOT / "hub/templates/display_details.html"
EDITOR = ROOT / "hub/templates/content_overlay_editor.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def isolate_section(text, heading):
    heading_pos = text.find(f"<h2>{heading}</h2>")
    if heading_pos < 0:
        raise SystemExit(f"Could not find section: {heading}")

    start = text.rfind('<div class="section', 0, heading_pos)
    if start < 0:
        raise SystemExit(f"Could not find section start: {heading}")

    depth = 0
    pos = start

    while pos < len(text):
        next_open = text.find("<div", pos)
        next_close = text.find("</div>", pos)

        if next_close < 0:
            break

        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            pos = next_close + len("</div>")

            if depth == 0:
                return start, pos

    raise SystemExit(f"Could not isolate section: {heading}")


def patch_template():
    text = DETAILS.read_text(encoding="utf-8")

    if "data-content-overlay-editor" in text:
        return

    start, end = isolate_section(
        text,
        "Content & Overlay",
    )

    block = EDITOR.read_text(encoding="utf-8")

    DETAILS.write_text(
        text[:start] + block + text[end:],
        encoding="utf-8",
    )

    EDITOR.unlink()


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.9.0 content overlay editor */"
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
    print("v5.9.0 live content and overlay editor applied.")


if __name__ == "__main__":
    main()
