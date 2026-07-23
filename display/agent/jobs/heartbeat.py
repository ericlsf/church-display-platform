import socket

from agent.api import post_heartbeat
from agent.config import APP_DIR, DISPLAY_ID, DISPLAY_PORT
from agent.utils import cpu_temp, disk_usage, memory_usage, now_iso, read_json, run_command, uptime
from agent.version import get_version_info, installed_version


def local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "Unknown"


def service_state(service_name):
    """Return systemd state without raising if the service is absent."""
    code, stdout, stderr = run_command(
        ["systemctl", "show", service_name, "--property=LoadState,ActiveState,SubState,UnitFileState", "--no-pager"],
        timeout=10,
    )

    values = {
        "service": service_name,
        "load_state": "unknown",
        "active_state": "unknown",
        "sub_state": "unknown",
        "unit_file_state": "unknown",
        "running": False,
    }

    if code != 0:
        values["error"] = (stderr or stdout).strip()[-300:]
        return values

    for line in stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        mapping = {
            "LoadState": "load_state",
            "ActiveState": "active_state",
            "SubState": "sub_state",
            "UnitFileState": "unit_file_state",
        }
        if key in mapping:
            values[mapping[key]] = value or "unknown"

    values["running"] = (
        values["load_state"] == "loaded"
        and values["active_state"] == "active"
        and values["sub_state"] in {"running", "exited"}
    )
    return values


def build_heartbeat():
    ip = local_ip()
    return {
        "id": DISPLAY_ID,
        "hostname": socket.gethostname(),
        "ip": ip,
        "host": f"http://{ip}:{DISPLAY_PORT}",
        "version": installed_version(),
        "git": get_version_info(),
        "config_version": 1,
        "sent_at": now_iso(),
        "player": read_json(APP_DIR / "status" / "player.json", {}),
        "media": read_json(APP_DIR / "status" / "media.json", {}),
        "sync": read_json(APP_DIR / "status" / "sync.json", {}),
        "display_app": service_state("church-display.service"),
        "resilience": read_json(APP_DIR / "status" / "resilience.json", {}),
        "system": {
            "cpu_temp": cpu_temp(),
            "memory": memory_usage(),
            "disk": disk_usage(),
            "uptime": uptime(),
        },
    }


def handle(job, report):
    report("running", 25, "Sending heartbeat")
    post_heartbeat(build_heartbeat())
    report("success", 100, "Heartbeat sent")
