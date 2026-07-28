import json
import urllib.parse

from agent.config import DISPLAY_ID
from agent.hub_connection import open_hub, update_hub_urls


def get_next_job():
    path = f"/api/v1/jobs/next?display_id={urllib.parse.quote(DISPLAY_ID)}"
    with open_hub(path, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("job")


def post_job_status(job_id, status, progress, message):
    payload = {
        "status": status,
        "progress": int(progress),
        "message": str(message),
    }

    body = json.dumps(payload).encode("utf-8")

    with open_hub(
        f"/api/v1/jobs/{job_id}/status",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
        timeout=10,
    ) as response:
        response.read()


def post_heartbeat(payload):
    body = json.dumps(payload).encode("utf-8")

    with open_hub(
        "/api/v1/heartbeat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
        timeout=10,
    ) as response:
        raw = response.read().decode("utf-8")
    try:
        result = json.loads(raw)
        update_hub_urls(result.get("hub_urls"))
        return result
    except Exception:
        return {}


def post_management_artifact(kind, payload):
    body = json.dumps(payload).encode("utf-8")
    with open_hub(
        f"/api/v1/management/artifact/{urllib.parse.quote(DISPLAY_ID)}/{urllib.parse.quote(kind)}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
        timeout=30,
    ) as response:
        response.read()
