#!/usr/bin/env python3
"""Locate the active deploy_update implementation without modifying it."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

SEARCH_ROOTS = [
    ROOT / "display" / "agent",
    ROOT / "display" / "scripts",
]

TERMS = (
    "deploy_update",
    "package_url",
    "rollback_on_failure",
    "restart church-display-agent.service",
    "church-display-agent.service",
)


def main():
    matches = []

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue

            try:
                text = path.read_text(
                    encoding="utf-8"
                )
            except Exception:
                continue

            score = sum(
                1
                for term in TERMS
                if term in text
            )

            if score:
                matches.append(
                    (score, path, text)
                )

    matches.sort(
        key=lambda item: (
            -item[0],
            str(item[1]),
        )
    )

    if not matches:
        print(
            "No deployment handler candidates found."
        )
        return 1

    print("Deployment handler candidates:")
    print()

    for score, path, text in matches:
        print(f"[score {score}] {path.relative_to(ROOT)}")

        for line_number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if any(term in line for term in TERMS):
                print(
                    f"  {line_number}: "
                    f"{line.strip()}"
                )

        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
