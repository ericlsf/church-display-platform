import base64
import os
from pathlib import Path

from agent.api import post_management_artifact
from agent.config import APP_DIR
from agent.utils import run_command


SAFE_ROOTS = [
    APP_DIR / "logs",
    APP_DIR / "status",
    APP_DIR / "config",
    APP_DIR / "media",
]
MAX_TEXT_BYTES = 1024 * 1024


def _inside_safe_root(path):
    resolved = Path(path).expanduser().resolve()
    return any(resolved == root.resolve() or root.resolve() in resolved.parents for root in SAFE_ROOTS)


def _safe_path(raw, default_root=None):
    if not raw:
        return (default_root or SAFE_ROOTS[0]).resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = APP_DIR / path
    path = path.resolve()
    if not _inside_safe_root(path):
        raise PermissionError("Path is outside approved display directories")
    return path


def handle_collect_logs(job, report):
    report("running", 30, "Collecting service logs")
    sections = {}
    for name, command in {
        "agent": ["journalctl", "-u", "church-display-agent.service", "-n", "250", "--no-pager"],
        "display": ["journalctl", "-u", "church-display.service", "-n", "250", "--no-pager"],
    }.items():
        code, stdout, stderr = run_command(command, timeout=30)
        sections[name] = stdout if code == 0 else (stderr or stdout or "Unavailable")

    for path in sorted((APP_DIR / "logs").glob("*.log")):
        try:
            sections[f"file:{path.name}"] = path.read_text(errors="replace")[-50000:]
        except Exception as exc:
            sections[f"file:{path.name}"] = f"Unable to read: {exc}"

    post_management_artifact("logs", {"sections": sections})
    report("success", 100, "Logs collected")


def handle_list_files(job, report):
    path = _safe_path(job.get("payload", {}).get("path"), APP_DIR / "logs")
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(str(path))

    report("running", 40, f"Listing {path}")
    entries = []
    for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        try:
            stat = child.stat()
            entries.append({
                "name": child.name,
                "path": str(child),
                "directory": child.is_dir(),
                "size": stat.st_size,
                "modified": int(stat.st_mtime),
            })
        except OSError:
            pass

    post_management_artifact("files", {"path": str(path), "entries": entries})
    report("success", 100, f"Listed {len(entries)} entries")


def handle_read_file(job, report):
    path = _safe_path(job.get("payload", {}).get("path"))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))
    size = path.stat().st_size
    if size > MAX_TEXT_BYTES:
        raise ValueError("File is larger than the 1 MB browser limit")

    report("running", 50, f"Reading {path.name}")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
        payload = {"path": str(path), "text": text, "binary": False, "size": size}
    except UnicodeDecodeError:
        payload = {
            "path": str(path),
            "content_base64": base64.b64encode(raw).decode("ascii"),
            "binary": True,
            "size": size,
        }
    post_management_artifact("file", payload)
    report("success", 100, f"Read {path.name}")


def handle_service_action(job, report):
    action = job.get("payload", {}).get("action", "")
    commands = {
        "start_display": ["sudo", "systemctl", "start", "church-display.service"],
        "restart_display": ["sudo", "systemctl", "restart", "church-display.service"],
        "restart_agent": ["sudo", "systemctl", "restart", "church-display-agent.service"],
        "reboot": ["sudo", "reboot"],
        "shutdown": ["sudo", "poweroff"],
    }
    command = commands.get(action)
    if not command:
        raise ValueError("Unsupported service action")

    report("success", 100, f"Requested {action.replace('_', ' ')}")
    run_command(command, timeout=25)
