#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/display_details.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def extract_section(text, heading):
    heading_pos = text.find(f"<h2>{heading}</h2>")
    if heading_pos < 0:
        raise SystemExit(f"Could not find section heading: {heading}")

    start = text.rfind('<div class="section"', 0, heading_pos)
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
                return text[start:pos], start, pos

    raise SystemExit(f"Could not isolate section: {heading}")


def move_before(text, moving_heading, target_heading):
    moving, start, end = extract_section(text, moving_heading)
    text = text[:start] + text[end:]

    target_pos = text.find(f"<h2>{target_heading}</h2>")
    if target_pos < 0:
        raise SystemExit(f"Could not find target heading: {target_heading}")

    target_start = text.rfind('<div class="section"', 0, target_pos)
    if target_start < 0:
        raise SystemExit(f"Could not find target section: {target_heading}")

    return text[:target_start] + moving + "\n\n" + text[target_start:]


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")

    # Put both high-value operational panels before Recent Jobs.
    for heading in ("Live Device Health", "Software Upgrade"):
        current = text.find(f"<h2>{heading}</h2>")
        recent = text.find("<h2>Recent Jobs</h2>")
        if current >= 0 and recent >= 0 and current > recent:
            text = move_before(text, heading, "Recent Jobs")

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.4.1 display page layout */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        text += "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")
    CSS_APPEND.unlink()


def main():
    patch_template()
    patch_css()
    print("v5.4.1 display page layout applied.")


if __name__ == "__main__":
    main()
