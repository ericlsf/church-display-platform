import json
from datetime import datetime, timezone
from pathlib import Path

from services.fleet_operations import fleet_rows
from services.jobs import list_jobs
from services.notifications import visible_notifications
from services.releases import latest_git_tag

ROOT = Path(__file__).resolve().parents[2]
PENDING_FILE = ROOT / "hub" / "config" / "pending_displays.json"
ACTIVE = {"queued", "pending", "running", "retrying", "in_progress"}
FAILED = {"failed", "timed_out", "cancelled"}

def _pending_displays():
    if not PENDING_FILE.exists():
        return []
    try:
        return json.loads(PENDING_FILE.read_text()).get("pending", [])
    except Exception:
        return []

def command_center_data():
    rows = fleet_rows()
    jobs = list_jobs(500)
    latest = latest_git_tag()
    active_jobs = [j for j in jobs if str(j.get("status", "")).lower() in ACTIVE]
    failed_jobs = [j for j in jobs if str(j.get("status", "")).lower() in FAILED and not j.get("resolved")]
    attention = [r for r in rows if r.get("readiness") in {"offline", "needs_attention", "needs_playlist", "provisioning"}]
    maintenance = [r for r in rows if r.get("readiness") == "maintenance"]
    outdated = [r for r in rows if latest and r.get("version") and str(r.get("version")) != str(latest)]
    pending = _pending_displays()
    return {
        "summary": {
            "total": len(rows),
            "healthy": sum(1 for r in rows if r.get("readiness") == "ready"),
            "attention": len(attention),
            "offline": sum(1 for r in rows if r.get("readiness") == "offline"),
            "maintenance": len(maintenance),
            "pending_enrollment": len(pending),
            "active_jobs": len(active_jobs),
            "failed_jobs": len(failed_jobs),
            "outdated": len(outdated),
        },
        "attention_rows": attention[:12],
        "maintenance_rows": maintenance[:12],
        "pending_displays": pending[:12],
        "active_jobs": active_jobs[:12],
        "failed_jobs": failed_jobs[:12],
        "outdated_rows": outdated[:12],
        "latest_tag": latest,
        "notifications": visible_notifications(12),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
