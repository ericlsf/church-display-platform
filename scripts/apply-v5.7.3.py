#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/display_details.html"


def main():
    text = TEMPLATE.read_text(encoding="utf-8")
    script = '<script src="/static/live-deployment-status.js"></script>'

    if script not in text:
        end = text.rfind("{% endblock %}")
        if end < 0:
            raise SystemExit("Could not find display details block ending")
        text = text[:end] + script + "\n" + text[end:]
        TEMPLATE.write_text(text, encoding="utf-8")

    print("v5.7.3 live deployment status applied.")


if __name__ == "__main__":
    main()
