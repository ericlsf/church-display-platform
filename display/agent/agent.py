import time
from datetime import datetime, timedelta

from agent.api import get_next_job, post_heartbeat
from agent.config import DISPLAY_ID, HUB_URL
from agent.dispatcher import dispatch
from agent.jobs.heartbeat import build_heartbeat
from agent.jobs.preview import upload_preview
from agent.resilience import evaluate_and_recover


HEARTBEAT_INTERVAL_SECONDS = 30
PREVIEW_INTERVAL_SECONDS = 60
JOB_POLL_INTERVAL_SECONDS = 5


def log(message):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {message}", flush=True)


def run_job_once():
    job = get_next_job()

    if not job:
        return False

    log(f"Running job {job.get('type')} {job.get('id')}")
    dispatch(job)
    return True


def send_heartbeat():
    heartbeat = build_heartbeat()
    response = post_heartbeat(heartbeat)
    state = evaluate_and_recover(heartbeat, response)
    action = state.get("last_action")
    if action and action not in {"recovery_disabled", "maintenance_suppressed"}:
        log(f"Recovery action: {action}")
    log("Heartbeat sent")


def send_preview():
    ok, message = upload_preview()
    if ok:
        log("Preview uploaded")
    else:
        log(f"Preview skipped/failed: {message}")


def run_forever():
    log(f"Display Agent started for {DISPLAY_ID}")
    log(f"Hub: {HUB_URL}")

    next_heartbeat = datetime.now()
    next_preview = datetime.now() + timedelta(seconds=10)

    while True:
        now = datetime.now()

        try:
            run_job_once()
        except Exception as exc:
            log(f"Job poll error: {type(exc).__name__}: {exc}")

        if now >= next_heartbeat:
            try:
                send_heartbeat()
            except Exception as exc:
                log(f"Heartbeat error: {type(exc).__name__}: {exc}")
            next_heartbeat = now + timedelta(seconds=HEARTBEAT_INTERVAL_SECONDS)

        if now >= next_preview:
            try:
                send_preview()
            except Exception as exc:
                log(f"Preview error: {type(exc).__name__}: {exc}")
            next_preview = now + timedelta(seconds=PREVIEW_INTERVAL_SECONDS)

        time.sleep(JOB_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
