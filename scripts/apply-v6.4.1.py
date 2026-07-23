#!/usr/bin/env python3
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/fleet_operations.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_template():
    if not TEMPLATE.exists():
        raise SystemExit(
            "Could not find hub/templates/fleet_operations.html"
        )

    text = TEMPLATE.read_text(encoding="utf-8")

    # Add stable classes without rewriting the form's functional markup.
    if "fleet-operations-form" not in text:
        form_pattern = re.compile(
            r'(<form\b[^>]*action="[^"]*fleet-operations[^"]*"[^>]*)>',
            re.IGNORECASE,
        )

        match = form_pattern.search(text)

        if match:
            opening = match.group(1)

            if 'class="' in opening:
                replacement = re.sub(
                    r'class="([^"]*)"',
                    lambda found: (
                        'class="'
                        + found.group(1)
                        + ' fleet-operations-form"'
                    ),
                    opening,
                    count=1,
                )
            else:
                replacement = opening + ' class="fleet-operations-form"'

            text = (
                text[:match.start()]
                + replacement
                + ">"
                + text[match.end():]
            )
        else:
            # The CSS includes an action-URL fallback, so don't corrupt
            # an unfamiliar form layout.
            print(
                "WARN  Fleet Operations form class was not added; "
                "URL-based CSS fallback will be used."
            )

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v6.4.1 fleet operations form layout */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")

    CSS_APPEND.unlink()


def main():
    patch_template()
    patch_css()
    print("v6.4.1 Fleet Operations form layout applied.")


if __name__ == "__main__":
    main()
