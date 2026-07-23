#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/display_details.html"
HEADER = ROOT / "hub/templates/display_details_v600_header.html"
HEALTH = ROOT / "hub/templates/display_details_v600_health.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def isolate_section(text, heading):
    heading_pos = text.find(f"<h2>{heading}</h2>")
    if heading_pos < 0:
        raise SystemExit(f"Could not find section heading: {heading}")

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


def patch_header(text):
    if 'class="display-hero"' in text:
        return text

    content_heading = text.find("<h2>Content & Overlay</h2>")
    if content_heading < 0:
        raise SystemExit("Could not locate Content & Overlay")

    insertion = text.rfind('<div class="display-settings-layout"', 0, content_heading)
    if insertion < 0:
        insertion = text.rfind('<div class="section', 0, content_heading)

    if insertion < 0:
        raise SystemExit("Could not locate display settings insertion point")

    block = HEADER.read_text(encoding="utf-8")
    return text[:insertion] + block + "\n" + text[insertion:]


def patch_health(text):
    if 'class="health-list-v600"' in text:
        return text

    start, end = isolate_section(text, "Health Diagnostics")
    block = HEALTH.read_text(encoding="utf-8")
    return text[:start] + block + text[end:]


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v6.0.0 display details UX refresh */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")

    CSS_APPEND.unlink()


def main():
    text = TEMPLATE.read_text(encoding="utf-8")
    text = patch_header(text)
    text = patch_health(text)
    TEMPLATE.write_text(text, encoding="utf-8")

    patch_css()

    for path in (HEADER, HEALTH):
        if path.exists():
            path.unlink()

    print("v6.0.0 display details UX refresh applied.")


if __name__ == "__main__":
    main()
