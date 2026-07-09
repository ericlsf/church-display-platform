from agent.config import APP_DIR
from agent.utils import run_command
from agent.version import get_version_info


def handle_update_check(job, report):
    report("running", 25, "Checking installed version")
    info = get_version_info()
    message = (
        f"tag={info.get('tag')} "
        f"commit={info.get('commit')} "
        f"branch={info.get('branch')} "
        f"dirty={info.get('dirty')}"
    )
    report("success", 100, message)


def git(args, timeout=20):
    return run_command(["git"] + args, cwd=str(APP_DIR), timeout=timeout)


def handle_deploy_update(job, report):
    payload = job.get("payload", {})
    target = payload.get("target") or payload.get("tag") or payload.get("version") or ""

    if not target:
        report("failed", 100, "Missing target tag/version")
        return

    report("running", 10, f"Dry-run deploy validation for {target}")

    info = get_version_info()
    if info.get("dirty") == "yes":
        report("failed", 100, "Cannot deploy: working tree has uncommitted changes")
        return

    report("running", 25, "Fetching tags from origin")
    code, stdout, stderr = git(["fetch", "--tags", "origin"], timeout=60)
    if code != 0:
        report("failed", 100, f"git fetch failed: {(stderr or stdout).strip()[-500:]}")
        return

    report("running", 50, f"Checking target {target}")
    code, stdout, stderr = git(["rev-parse", "--verify", f"{target}^{{commit}}"])
    if code != 0:
        report("failed", 100, f"Target not found: {target}")
        return

    target_commit = stdout.strip()

    code, stdout, stderr = git(["rev-parse", "HEAD"])
    if code != 0:
        report("failed", 100, "Could not determine current HEAD")
        return

    current_commit = stdout.strip()

    report("running", 75, "Validating rollback point")
    current_info = get_version_info()

    message = (
        f"DRY RUN OK. "
        f"Would deploy {target} ({target_commit[:8]}) "
        f"from {current_info.get('describe')} ({current_commit[:8]}). "
        f"Rollback point would be {current_commit[:8]}. "
        f"No files changed."
    )

    report("success", 100, message)
