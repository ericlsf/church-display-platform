from agent.utils import run_command


def handle_restart(job, report):
    report("success", 100, "Restart requested")
    run_command(["sudo", "systemctl", "restart", "church-display.service"], timeout=20)


def handle_reboot(job, report):
    report("success", 100, "Reboot requested")
    run_command(["sudo", "reboot"], timeout=20)


