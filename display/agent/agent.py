import time

from agent.api import get_next_job
from agent.config import DISPLAY_ID, HUB_URL
from agent.dispatcher import dispatch


def run_once():
    job = get_next_job()

    if not job:
        return False

    dispatch(job)
    return True


def run_forever(interval=10):
    print(f"Display Agent started for {DISPLAY_ID}")
    print(f"Hub: {HUB_URL}")

    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"Agent error: {type(exc).__name__}: {exc}")

        time.sleep(interval)


if __name__ == "__main__":
    run_forever()

