from pathlib import Path
import time

from agent.config import APP_DIR
from agent.utils import run_command
from agent.version import get_version_info


BACKUP_DIR = APP_DIR.parent / "backups"
ROLLBACK_MARKER = BACKUP_DIR / "last-good-commit.txt"


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


def service_is_active(service_name):
    code, stdout, stderr = run_command(
        ["systemctl", "is-active", service_name],
        timeout=15,
    )
    return code == 0 and stdout.strip() == "active"


def ensure_clean(report):
    info = get_version_info()
    if info.get("dirty") == "yes":
        report("failed", 100, "Cannot deploy: working tree has uncommitted changes")
        return False
    return True


def validate_target(target, report):
    if not target:
        report("failed", 100, "Missing target tag/version")
        return None

    report("running", 20, "Fetching tags from origin")
    code, stdout, stderr = git(["fetch", "--tags", "origin"], timeout=90)
    if code != 0:
        report("failed", 100, f"git fetch failed: {(stderr or stdout).strip()[-500:]}")
        return None

    report("running", 35, f"Checking target {target}")
    code, stdout, stderr = git(["rev-parse", "--verify", f"{target}^{{commit}}"])
    if code != 0:
        report("failed", 100, f"Target not found: {target}")
        return None

    return stdout.strip()


def current_head(report):
    code, stdout, stderr = git(["rev-parse", "HEAD"])
    if code != 0:
        report("failed", 100, "Could not determine current HEAD")
        return None
    return stdout.strip()


def backup_current_state(current_commit, report):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ROLLBACK_MARKER.write_text(current_commit + "\n")
    report("running", 50, f"Rollback point saved: {current_commit[:8]}")


def checkout_ref(ref, report, progress=60):
    report("running", progress, f"Checking out {ref}")
    code, stdout, stderr = git(["checkout", "--force", ref], timeout=90)
    if code != 0:
        report("failed", 100, f"checkout failed: {(stderr or stdout).strip()[-500:]}")
        return False
    return True


def install_dependencies(report, progress=70):
    report("running", progress, "Installing dependencies")

    py_path = APP_DIR / "venv" / "bin" / "python"
    requirements = APP_DIR / "requirements.txt"

    if not py_path.exists():
        report("failed", 100, "venv python not found")
        return False

    if not requirements.exists():
        report("running", progress + 5, "No requirements.txt found; skipping dependency install")
        return True

    code, stdout, stderr = run_command(
        [str(py_path), "-m", "pip", "install", "-r", str(requirements)],
        cwd=str(APP_DIR),
        timeout=300,
    )

    if code != 0:
        report("failed", 100, f"dependency install failed: {(stderr or stdout).strip()[-500:]}")
        return False

    return True


def restart_display_and_verify(report):
    report("running", 82, "Restarting display service")
    code, stdout, stderr = run_command(
        ["sudo", "systemctl", "restart", "church-display.service"],
        timeout=45,
    )

    if code != 0:
        report("running", 86, f"display restart command failed: {(stderr or stdout).strip()[-300:]}")
        return False

    report("running", 88, "Verifying display service")
    time.sleep(6)

    if not service_is_active("church-display.service"):
        report("running", 89, "display service is not active")
        return False

    return True


def restart_agent_after_success(report):
    report("running", 96, "Restarting agent service")
    run_command(["sudo", "systemctl", "restart", "church-display-agent.service"], timeout=20)


def rollback_to(commit, report, reason):
    report("running", 90, f"Rolling back to {commit[:8]}")

    git(["checkout", "--force", commit], timeout=90)
    install_dependencies(report, progress=92)

    run_command(["sudo", "systemctl", "restart", "church-display.service"], timeout=45)

    time.sleep(6)

    if service_is_active("church-display.service"):
        report("failed", 100, f"{reason}; rolled back to {commit[:8]} and display is active")
    else:
        report("failed", 100, f"{reason}; rollback attempted to {commit[:8]} but display service is still not active")


def handle_deploy_update(job, report):
    payload = job.get("payload", {})
    target = payload.get("target") or payload.get("tag") or payload.get("version") or ""
    dry_run = str(payload.get("dry_run", "true")).lower() not in ["0", "false", "no"]

    if not target:
        report("failed", 100, "Missing target tag/version")
        return

    mode = "dry-run" if dry_run else "real"
    report("running", 10, f"{mode} deploy validation for {target}")

    if not ensure_clean(report):
        return

    target_commit = validate_target(target, report)
    if not target_commit:
        return

    current_commit = current_head(report)
    if not current_commit:
        return

    current_info = get_version_info()

    if dry_run:
        report("running", 75, "Validating rollback point")
        message = (
            f"DRY RUN OK. "
            f"Would deploy {target} ({target_commit[:8]}) "
            f"from {current_info.get('describe')} ({current_commit[:8]}). "
            f"Rollback point would be {current_commit[:8]}. "
            f"No files changed."
        )
        report("success", 100, message)
        return

    if current_commit == target_commit:
        report("success", 100, f"Already at {target} ({target_commit[:8]})")
        return

    backup_current_state(current_commit, report)

    if not checkout_ref(target, report, progress=60):
        rollback_to(current_commit, report, "Deploy failed during checkout")
        return

    if not install_dependencies(report, progress=72):
        rollback_to(current_commit, report, "Deploy failed during dependency install")
        return

    if not restart_display_and_verify(report):
        rollback_to(current_commit, report, "Deploy failed display-service verification")
        return

    final_info = get_version_info()
    final_commit = final_info.get("commit", "unknown")

    message = (
        f"Deploy verified. "
        f"Updated from {current_commit[:8]} to {target} ({target_commit[:8]}). "
        f"Current commit is {final_commit}. Agent will restart."
    )

    report("success", 100, message)

    restart_agent_after_success(report)
