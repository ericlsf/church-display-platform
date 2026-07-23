#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEPLOYMENTS = ROOT / "hub" / "routes" / "deployments.py"


def patch_import(text):
    line = (
        "from services.deployment_guard import "
        "existing_deployment, unique_display_ids"
    )
    if line in text:
        return text

    lines = text.splitlines()
    indexes = [
        index
        for index, value in enumerate(lines)
        if value.startswith("from services.")
    ]
    lines.insert(max(indexes, default=0) + 1, line)
    return "\n".join(lines) + "\n"


def patch_queue_function(text):
    signature = "def queue_deploy_job(display_id, target, dry_run):"
    if signature not in text:
        raise SystemExit("Could not find queue_deploy_job()")

    guard = (
        "def queue_deploy_job(display_id, target, dry_run):\n"
        "    existing = existing_deployment(display_id, target, dry_run)\n"
        "    if existing:\n"
        "        return existing"
    )

    if "existing = existing_deployment(display_id, target, dry_run)" not in text:
        text = text.replace(signature, guard, 1)

    # Ensure the create_job result is returned.
    marker = "    create_job(\n        display_id,\n        \"deploy_update\","
    replacement = "    job = create_job(\n        display_id,\n        \"deploy_update\","
    if marker in text:
        text = text.replace(marker, replacement, 1)

    log_marker = (
        "    log_event(\n"
        "        f\"Queued"
    )
    if "    return job\n" not in text:
        start = text.find(log_marker, text.find(signature))
        if start >= 0:
            end = text.find("\n    )", start)
            if end >= 0:
                end += len("\n    )")
                text = text[:end] + "\n    return job" + text[end:]

    return text


def patch_routes(text):
    original = 'display_ids = request.form.getlist("display_ids")'
    replacement = (
        'display_ids = unique_display_ids('
        'request.form.getlist("display_ids"))'
    )
    text = text.replace(original, replacement)

    old_loop = """    state = build_fleet_state()
    outdated_rows = state.get("outdated_rows", [])

    try:
        for row in outdated_rows:
            display_id = row.get("id")
            if display_id:
                queue_deploy_job(display_id, target, dry_run)
        flash(
            f"Queued {target} for {len(outdated_rows)} outdated display(s).",
            "success",
        )"""

    new_loop = """    state = build_fleet_state()
    outdated_rows = state.get("outdated_rows", [])
    display_ids = unique_display_ids(
        row.get("id") for row in outdated_rows
    )

    try:
        for display_id in display_ids:
            queue_deploy_job(display_id, target, dry_run)
        flash(
            f"Queued {target} for {len(display_ids)} outdated display(s).",
            "success",
        )"""

    if old_loop in text:
        text = text.replace(old_loop, new_loop)
    elif "display_ids = unique_display_ids(" not in text[text.find("def queue_outdated_deployment"):]:
        raise SystemExit(
            "Could not safely patch queue_outdated_deployment(); "
            "review hub/routes/deployments.py"
        )

    return text


def main():
    text = DEPLOYMENTS.read_text(encoding="utf-8")
    text = patch_import(text)
    text = patch_queue_function(text)
    text = patch_routes(text)
    DEPLOYMENTS.write_text(text, encoding="utf-8")
    print("Deployment deduplication applied.")


if __name__ == "__main__":
    main()
