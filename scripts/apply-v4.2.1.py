#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "display" / "app" / "main.py"


def patch_player():
    text = MAIN.read_text(encoding="utf-8")

    import_line = "from app.cursor import hide_cursor"
    if import_line not in text:
        lines = text.splitlines()
        insert_at = 0
        for index, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = index + 1
        lines.insert(insert_at, import_line)
        text = "\n".join(lines) + "\n"

    if "hide_cursor(app)" not in text:
        candidates = [
            "app = QApplication(sys.argv)",
            "app = QApplication([])",
        ]
        for candidate in candidates:
            if candidate in text:
                text = text.replace(
                    candidate,
                    candidate + "\n    hide_cursor(app)"
                    if candidate.startswith("    ")
                    else candidate + "\nhide_cursor(app)",
                    1,
                )
                break
        else:
            raise SystemExit(
                "Could not find QApplication creation in display/app/main.py"
            )

    MAIN.write_text(text, encoding="utf-8")


def main():
    patch_player()
    print("v4.2.1 cursor hook applied.")


if __name__ == "__main__":
    main()
