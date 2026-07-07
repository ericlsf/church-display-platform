import json
import urllib.parse
import urllib.request

from agent.config import DISPLAY_ID, HUB_URL


def get_next_job():
    url = f"{HUB_URL}/api/v1/jobs/next?display_id={urllib.parse.quote(DISPLAY_ID)}"

    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("job")


def post_job_status(job_id, status, progress, message):
    payload = {
        "status": status,
        "progress": int(progress),
        "message": str(message),
    }

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"{HUB_URL}/api/v1/jobs/{job_id}/status",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


def post_heartbeat(payload):
    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"{HUB_URL}/api/v1/heartbeat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


