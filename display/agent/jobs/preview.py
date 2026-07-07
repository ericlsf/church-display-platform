from agent.config import APP_DIR
from agent.utils import run_command


def handle(job, report):
    script = APP_DIR / "scripts" / "upload_preview_to_hub.sh"

    report("running", 25, "Uploading preview")

    if not script.exists():
        report("failed", 100, "Preview script not found")
        return

    code, stdout, stderr = run_command([str(script)], cwd=str(APP_DIR), timeout=60)

    if code == 0:
        report("success", 100, "Preview uploaded")
    else:
        message = (stderr or stdout or "Preview upload failed").strip()[-500:]
        report("failed", 100, message)


