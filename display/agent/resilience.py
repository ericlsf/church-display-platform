import json
from datetime import datetime, timezone
from pathlib import Path

from agent.config import APP_DIR
from agent.utils import read_json, run_command, write_json

STATE_PATH = APP_DIR / "status" / "resilience.json"
POLICY_PATH = APP_DIR / "status" / "resilience-policy.json"

DEFAULT_STATE = {
    "display_failures": 0,
    "sync_failures": 0,
    "restart_attempts": 0,
    "last_restart_at": "",
    "last_sync_repair_at": "",
    "last_action": "",
    "last_error": "",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def save_policy(policy):
    write_json(POLICY_PATH, policy or {})


def load_policy():
    return read_json(POLICY_PATH, {})


def load_state():
    state = read_json(STATE_PATH, DEFAULT_STATE.copy())
    for key, value in DEFAULT_STATE.items():
        state.setdefault(key, value)
    return state


def save_state(state):
    write_json(STATE_PATH, state)


def cooldown_elapsed(last_value, seconds):
    last = parse_time(last_value)
    if not last:
        return True
    now = datetime.now(timezone.utc)
    if not last.tzinfo:
        last = last.replace(tzinfo=timezone.utc)
    return (now - last).total_seconds() >= seconds


def evaluate_and_recover(heartbeat, response):
    policy = (response or {}).get("agent_policy") or load_policy()
    if response and response.get("agent_policy"):
        save_policy(response["agent_policy"])

    maintenance = policy.get("maintenance", {})
    recovery = policy.get("recovery", {})
    state = load_state()

    if maintenance.get("enabled"):
        state.update({
            "display_failures": 0,
            "sync_failures": 0,
            "last_action": "maintenance_suppressed",
            "last_error": "",
        })
        save_state(state)
        return state

    if not recovery.get("enabled", True):
        state["last_action"] = "recovery_disabled"
        save_state(state)
        return state

    display_running = bool((heartbeat.get("display_app") or {}).get("running"))
    sync_state = str((heartbeat.get("sync") or {}).get("state", "")).lower()

    state["display_failures"] = 0 if display_running else state["display_failures"] + 1
    state["sync_failures"] = 0 if sync_state not in {"failed", "error"} else state["sync_failures"] + 1

    threshold = int(recovery.get("display_failure_threshold", 2))
    cooldown = int(recovery.get("restart_cooldown_seconds", 300))
    max_attempts = int(recovery.get("max_restart_attempts", 3))

    if not display_running and state["display_failures"] >= threshold:
        if cooldown_elapsed(state.get("last_restart_at"), cooldown):
            if state["restart_attempts"] < max_attempts:
                code, stdout, stderr = run_command(
                    ["sudo", "systemctl", "restart", "church-display.service"],
                    timeout=45,
                )
                state["last_restart_at"] = now_iso()
                state["restart_attempts"] += 1
                state["last_action"] = "restart_display"
                state["last_error"] = "" if code == 0 else (stderr or stdout).strip()[-500:]
            elif recovery.get("allow_reboot", False):
                state["last_action"] = "reboot_escalation"
                save_state(state)
                run_command(["sudo", "reboot"], timeout=10)
                return state
    elif display_running:
        state["restart_attempts"] = 0

    sync_threshold = int(recovery.get("sync_failure_threshold", 2))
    if recovery.get("sync_repair_enabled", True) and state["sync_failures"] >= sync_threshold:
        if cooldown_elapsed(state.get("last_sync_repair_at"), cooldown):
            script = APP_DIR / "scripts" / "sync_media.sh"
            code, stdout, stderr = run_command([str(script)], cwd=str(APP_DIR), timeout=300)
            state["last_sync_repair_at"] = now_iso()
            state["last_action"] = "sync_repair"
            state["last_error"] = "" if code == 0 else (stderr or stdout).strip()[-500:]
            if code == 0:
                state["sync_failures"] = 0

    save_state(state)
    return state
