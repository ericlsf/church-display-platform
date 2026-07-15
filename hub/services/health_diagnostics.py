from services.jobs import create_job


CHECK_DEFINITIONS = {
    "online": {
        "label": "Hub connection",
        "good": "Display is communicating with the Hub.",
        "bad": "The Hub is not receiving heartbeats from this display.",
        "action": "reboot",
        "action_label": "Reboot Device",
        "guidance": (
            "Confirm the Pi has power and network access. "
            "If it is reachable but still offline, reboot it."
        ),
    },
    "player": {
        "label": "Display application",
        "good": "The display application is running.",
        "bad": "The display application is not running.",
        "action": "restart",
        "action_label": "Restart Player",
        "guidance": (
            "Restart the display application. If it fails again, "
            "collect logs and review the most recent player error."
        ),
    },
    "playlist": {
        "label": "Content folder",
        "good": "A content folder is assigned.",
        "bad": "No content folder is assigned.",
        "action": "settings",
        "action_label": "Assign Folder",
        "guidance": (
            "Choose a content folder on this display page and apply it."
        ),
    },
    "media": {
        "label": "Local media",
        "good": "Media is available locally.",
        "bad": "No playable media is available locally.",
        "action": "sync",
        "action_label": "Sync Now",
        "guidance": (
            "Run a sync. If the folder is empty, add media to the "
            "assigned Drive folder."
        ),
    },
    "sync": {
        "label": "Last sync",
        "good": "The most recent sync completed successfully.",
        "bad": "The most recent sync did not complete successfully.",
        "action": "sync",
        "action_label": "Retry Sync",
        "guidance": (
            "Retry the sync. If it fails again, open Jobs or Errors "
            "to review the exact failure message."
        ),
    },
}


def build_health_diagnostics(fleet):
    checks = fleet.get("checks", {}) or {}
    diagnostics = []

    for key, definition in CHECK_DEFINITIONS.items():
        passed = bool(checks.get(key, False))
        diagnostics.append({
            "key": key,
            "label": definition["label"],
            "passed": passed,
            "summary": (
                definition["good"]
                if passed
                else definition["bad"]
            ),
            "guidance": (
                ""
                if passed
                else definition["guidance"]
            ),
            "action": (
                ""
                if passed
                else definition["action"]
            ),
            "action_label": (
                ""
                if passed
                else definition["action_label"]
            ),
        })

    failed = [
        item
        for item in diagnostics
        if not item["passed"]
    ]

    return {
        "score": fleet.get("health_score", 0),
        "checks": diagnostics,
        "failed_checks": failed,
        "all_healthy": not failed,
        "failed_count": len(failed),
    }


def queue_health_action(display_id, action):
    if action == "sync":
        return create_job(display_id, "sync_now", {})
    if action == "restart":
        return create_job(display_id, "restart_display", {})
    if action == "reboot":
        return create_job(display_id, "reboot", {})
    if action == "collect_logs":
        return create_job(display_id, "collect_logs", {})
    raise ValueError("Unsupported health action")
