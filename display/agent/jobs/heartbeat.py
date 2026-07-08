import socket

from agent.api import post_heartbeat
from agent.config import APP_DIR, DISPLAY_ID, DISPLAY_PORT, DISPLAY_VERSION
from agent.utils import cpu_temp, disk_usage, memory_usage, now_iso, read_json, uptime
from agent.version import get_version_info


def local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "Unknown"


def build_heartbeat():
    ip = local_ip()
    return {
        "id": DISPLAY_ID,
        "hostname": socket.gethostname(),
        "ip": ip,
        "host": f"http://{ip}:{DISPLAY_PORT}",
        "version": DISPLAY_VERSION,
        "git": get_version_info(),
        "config_version": 1,
        "sent_at": now_iso(),
        "player": read_json(APP_DIR / "status" / "player.json", {}),
        "media": read_json(APP_DIR / "status" / "media.json", {}),
        "sync": read_json(APP_DIR / "status" / "sync.json", {}),
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
