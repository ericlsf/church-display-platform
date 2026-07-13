#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"
GITIGNORE = ROOT / ".gitignore"


def patch_app():
    text = APP.read_text()
    for line in [
        "from routes.groups import groups_bp",
        "from routes.operations import operations_bp",
    ]:
        if line not in text:
            lines = text.splitlines()
            idx = max([i for i, v in enumerate(lines) if v.startswith("from routes.")], default=-1)
            lines.insert(idx + 1, line)
            text = "\n".join(lines) + "\n"

    for line in [
        "    app.register_blueprint(groups_bp)",
        "    app.register_blueprint(operations_bp)",
    ]:
        if line not in text:
            lines = text.splitlines()
            idx = max([i for i, v in enumerate(lines) if "app.register_blueprint(" in v], default=-1)
            if idx < 0:
                raise SystemExit("Could not find blueprint registrations")
            lines.insert(idx + 1, line)
            text = "\n".join(lines) + "\n"
    APP.write_text(text)


def patch_base():
    text = BASE.read_text()
    links = [
        ('href="/operations"', '<a class="{{ \'active\' if active == \'operations\' else \'\' }}" href="/operations">Operations</a>'),
        ('href="/groups"', '<a class="{{ \'active\' if active == \'groups\' else \'\' }}" href="/groups">Groups</a>'),
    ]
    for needle, link in links:
        if needle not in text:
            pos = text.find("</nav>")
            if pos < 0:
                raise SystemExit("Could not find </nav> in base.html")
            text = text[:pos] + "            " + link + "\n" + text[pos:]
    BASE.write_text(text)


def patch_gitignore():
    lines = GITIGNORE.read_text().splitlines() if GITIGNORE.exists() else []
    for item in ["hub/config/groups.json", "hub/config/groups.json.tmp"]:
        if item not in lines:
            lines.append(item)
    GITIGNORE.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    patch_app()
    patch_base()
    patch_gitignore()
    print("v2.7.0 live operations and groups applied.")
