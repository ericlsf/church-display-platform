from agent.version import get_version_info


def handle_update_check(job, report):
    report("running", 25, "Checking installed version")
    info = get_version_info()
    message = (
        f"tag={info.get('tag')} "
        f"commit={info.get('commit')} "
        f"branch={info.get('branch')} "
        f"dirty={info.get('dirty')}"
    )
    report("success", 100, message)
