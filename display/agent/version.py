from agent.config import APP_DIR
from agent.utils import run_command


def git_value(args, default="Unknown"):
    code, stdout, stderr = run_command(["git"] + args, cwd=str(APP_DIR), timeout=5)
    if code != 0:
        return default
    return stdout.strip() or default


def is_dirty():
    code, stdout, stderr = run_command(["git", "status", "--porcelain"], cwd=str(APP_DIR), timeout=5)
    if code != 0:
        return "Unknown"
    return "yes" if stdout.strip() else "no"


def get_version_info():
    return {
        "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": git_value(["rev-parse", "--short", "HEAD"]),
        "tag": git_value(["describe", "--tags", "--abbrev=0"], "untagged"),
        "describe": git_value(["describe", "--tags", "--always", "--dirty"], "Unknown"),
        "dirty": is_dirty(),
    }
