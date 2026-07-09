from agent.api import post_job_status
from agent.jobs import heartbeat, preview, sync, system, update


def dispatch(job):
    job_id = job["id"]
    job_type = job["type"]

    def report(status, progress, message):
        post_job_status(job_id, status, progress, message)

    report("running", 10, f"Started {job_type}")

    try:
        if job_type == "heartbeat":
            heartbeat.handle(job, report)
        elif job_type == "sync_now":
            sync.handle_sync_now(job, report)
        elif job_type == "set_sync_folder":
            sync.handle_set_sync_folder(job, report)
        elif job_type == "restart_display":
            system.handle_restart(job, report)
        elif job_type == "reboot":
            system.handle_reboot(job, report)
        elif job_type == "upload_preview":
            preview.handle(job, report)
        elif job_type == "update_check":
            update.handle_update_check(job, report)
        elif job_type == "deploy_update":
            update.handle_deploy_update(job, report)
        else:
            report("failed", 100, f"Unknown job type: {job_type}")
    except Exception as exc:
        report("failed", 100, f"{type(exc).__name__}: {exc}")
