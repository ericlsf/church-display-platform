#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/display_details.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def extract_section(text: str, heading: str):
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
                return {
                    "heading": heading,
                    "start": start,
                    "end": pos,
                    "html": text[start:pos],
                }

    raise SystemExit(f"Could not isolate section: {heading}")


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")

    if 'class="display-settings-layout"' in text:
        print("Display settings layout already present.")
        return

    sections = [
        extract_section(text, "Content & Overlay"),
        extract_section(text, "Display Profile"),
        extract_section(text, "Maintenance"),
    ]

    insertion_point = min(section["start"] for section in sections)

    # Remove from the end backward so offsets stay valid.
    for section in sorted(
        sections,
        key=lambda item: item["start"],
        reverse=True,
    ):
        text = (
            text[:section["start"]]
            + text[section["end"]:]
        )

    content = next(
        item["html"]
        for item in sections
        if item["heading"] == "Content & Overlay"
    )
    profile = next(
        item["html"]
        for item in sections
        if item["heading"] == "Display Profile"
    )
    maintenance = next(
        item["html"]
        for item in sections
        if item["heading"] == "Maintenance"
    )

    layout = (
        '<div class="display-settings-layout">\n'
        '  <div class="display-settings-content-row">\n'
        f'{content}\n'
        '  </div>\n'
        '  <div class="display-settings-secondary-row">\n'
        f'{profile}\n'
        f'{maintenance}\n'
        '  </div>\n'
        '</div>\n'
    )

    text = (
        text[:insertion_point]
        + layout
        + text[insertion_point:]
    )

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.9.2 display settings layout */"
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
    print("v5.9.2 display settings layout applied.")


if __name__ == "__main__":
    main()
