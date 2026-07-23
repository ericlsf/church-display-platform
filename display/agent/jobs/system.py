from agent.utils import run_command


def handle_restart(job, report):
    report("running", 35, "Starting or restarting display app")
    code, stdout, stderr = run_command(
        ["sudo", "systemctl", "restart", "church-display.service"],
        timeout=30,
    )

    if code != 0:
        report(
            "failed",
            100,
            f"Display app restart failed: {(stderr or stdout).strip()[-500:]}",
        )
        return

    code, stdout, stderr = run_command(
        ["systemctl", "is-active", "church-display.service"],
        timeout=10,
    )

    if code == 0 and stdout.strip() == "active":
        report("success", 100, "Display app is running")
    else:
        report(
            "failed",
            100,
            f"Restart command completed but display app is not active: {(stderr or stdout).strip()[-300:]}",
        )


def handle_reboot(job, report):
    report("success", 100, "Reboot requested")
    run_command(["sudo", "reboot"], timeout=20)
