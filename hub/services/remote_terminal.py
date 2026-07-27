import json
import os
import platform
import queue
import signal
import subprocess
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from services.config import CONFIG_DIR

SESSIONS_DIR = CONFIG_DIR / "terminal_sessions"
MAX_OUTPUT_BYTES = 256 * 1024
MAX_COMMAND_SECONDS = 900


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _session_path(session_id):
    return SESSIONS_DIR / f"{session_id}.json"


def _output_path(session_id):
    return SESSIONS_DIR / f"{session_id}.log"


def _write_session(session):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    target = _session_path(session["id"])
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(session, indent=2), encoding="utf-8")
    temporary.replace(target)


def get_session(session_id):
    try:
        session = json.loads(_session_path(session_id).read_text(encoding="utf-8"))
    except Exception:
        return None
    try:
        output = _output_path(session_id).read_text(encoding="utf-8", errors="replace")
    except Exception:
        output = ""
    session["output"] = output[-MAX_OUTPUT_BYTES:]
    return session


def list_sessions(limit=20):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sessions = []
    paths = sorted(SESSIONS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for path in paths[:limit]:
        session = get_session(path.stem)
        if session:
            sessions.append(session)
    return sessions


def _command_argv(command):
    if platform.system().lower() == "windows":
        return ["powershell.exe", "-NoLogo", "-NonInteractive", "-Command", command]
    return ["/bin/bash", "-lc", command]


def _append_output(session_id, value):
    if not value:
        return
    path = _output_path(session_id)
    with path.open("a", encoding="utf-8", errors="replace") as stream:
        stream.write(value)
    if path.stat().st_size > MAX_OUTPUT_BYTES:
        path.write_bytes(path.read_bytes()[-MAX_OUTPUT_BYTES:])


def _run_session(session_id, command, cwd, timeout):
    session = get_session(session_id)
    if not session:
        return
    session.pop("output", None)
    session.update({"status": "running", "started_at": _now()})
    _write_session(session)
    _append_output(session_id, f"$ {command}\n")
    try:
        options = {
            "cwd": cwd,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
        }
        if os.name == "posix":
            options["start_new_session"] = True
        process = subprocess.Popen(_command_argv(command), **options)
        lines = queue.Queue()

        def read_output():
            for value in iter(process.stdout.readline, ""):
                lines.put(value)
            lines.put(None)

        threading.Thread(target=read_output, daemon=True).start()
        started = time.monotonic()
        reader_done = False
        while True:
            try:
                line = lines.get(timeout=0.2)
                if line is None:
                    reader_done = True
                else:
                    _append_output(session_id, line)
            except queue.Empty:
                pass
            if process.poll() is not None and reader_done:
                break
            if time.monotonic() - started > timeout:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGTERM)
                else:
                    process.terminate()
                raise subprocess.TimeoutExpired(command, timeout)
        if process.stdout:
            process.stdout.close()
        session = get_session(session_id) or session
        session.pop("output", None)
        session.update({
            "status": "success" if process.returncode == 0 else "failed",
            "exit_code": process.returncode,
            "completed_at": _now(),
        })
        _append_output(session_id, f"\n[process exited with code {process.returncode}]\n")
    except subprocess.TimeoutExpired:
        session = get_session(session_id) or session
        session.pop("output", None)
        session.update({"status": "timed_out", "exit_code": None, "completed_at": _now()})
        _append_output(session_id, f"\n[command stopped after {timeout} seconds]\n")
    except Exception as exc:
        session = get_session(session_id) or session
        session.pop("output", None)
        session.update({"status": "failed", "exit_code": None, "completed_at": _now()})
        _append_output(session_id, f"\n{type(exc).__name__}: {exc}\n")
    _write_session(session)


def start_hub_command(command, username, cwd=None, timeout=MAX_COMMAND_SECONDS):
    command = str(command or "").strip()
    if not command:
        raise ValueError("A command is required.")
    if "\x00" in command or len(command) > 8000:
        raise ValueError("The command is invalid or too long.")
    repo_root = Path(__file__).resolve().parents[2]
    requested_cwd = (Path(cwd).expanduser() if cwd else repo_root).resolve()
    if not requested_cwd.exists() or not requested_cwd.is_dir():
        raise ValueError("The working directory does not exist.")
    session = {
        "id": str(uuid.uuid4()),
        "target": "hub",
        "target_name": platform.node() or "Hub",
        "command": command,
        "cwd": str(requested_cwd),
        "username": username,
        "status": "queued",
        "exit_code": None,
        "created_at": _now(),
        "started_at": "",
        "completed_at": "",
    }
    _write_session(session)
    _output_path(session["id"]).write_text("", encoding="utf-8")
    threading.Thread(
        target=_run_session,
        args=(session["id"], command, str(requested_cwd), max(5, min(int(timeout), MAX_COMMAND_SECONDS))),
        daemon=True,
    ).start()
    return session
