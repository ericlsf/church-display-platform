import subprocess
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent.parent


def list_git_tags(limit=30):
    try:
        subprocess.run(
            ["git", "fetch", "--tags", "origin"],
            cwd=str(APP_DIR),
            capture_output=True,
            text=True,
            timeout=20,
        )

        result = subprocess.run(
            ["git", "tag", "--sort=-creatordate"],
            cwd=str(APP_DIR),
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return []

        tags = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return tags[:limit]
    except Exception:
        return []
