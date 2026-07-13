from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"


def backup(path):
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(path.read_text())


def patch_app():
    text = APP.read_text()
    backup(APP)

    import_line = "from routes.deployments import deployments_bp"

    if import_line not in text:
        lines = text.splitlines()
        insert_at = 0

        # Put it after the last routes.* import if possible.
        for idx, line in enumerate(lines):
            if line.startswith("from routes."):
                insert_at = idx + 1

        lines.insert(insert_at, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(deployments_bp)"

    if register_line not in text:
        marker = "app.register_blueprint("
        lines = text.splitlines()
        insert_at = None

        for idx, line in enumerate(lines):
            if marker in line:
                insert_at = idx + 1

        if insert_at is None:
            # Fallback: insert right after create_app definition.
            for idx, line in enumerate(lines):
                if line.startswith("def create_app"):
                    insert_at = idx + 1
                    break

        if insert_at is None:
            raise SystemExit("Could not find where to register deployments_bp in hub/app.py")

        lines.insert(insert_at, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text)


def patch_base():
    if not BASE.exists():
        return

    text = BASE.read_text()
    backup(BASE)

    if 'href="/deployments"' in text:
        return

    nav_link = '<a class="{{ \\'active\\' if active == \\'deployments\\' else \\'\\' }}" href="/deployments">Deployments</a>'

    # Insert after Jobs link if present.
    jobs_idx = text.find('href="/jobs"')
    if jobs_idx != -1:
        line_start = text.rfind("\n", 0, jobs_idx)
        line_end = text.find("\n", jobs_idx)
        if line_end == -1:
            line_end = len(text)
        text = text[:line_end] + "\n" + nav_link + text[line_end:]
        BASE.write_text(text)
        return

    # Insert before closing nav if present.
    nav_end = text.find("</nav>")
    if nav_end != -1:
        text = text[:nav_end] + nav_link + "\n" + text[nav_end:]
        BASE.write_text(text)
        return

    # Fallback: do nothing rather than corrupting layout.
    print("Could not find nav location in base.html; deployments route is still available at /deployments")


def main():
    if not APP.exists():
        raise SystemExit("hub/app.py not found. Run from inside ~/church-display-platform after unzipping.")

    patch_app()
    patch_base()

    print("Deployments page patch applied.")
    print("Backups created as .bak files if they did not already exist.")


if __name__ == "__main__":
    main()
