import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hub"))
sys.path.insert(0, str(ROOT / "display"))


class RemoteMaintenanceTests(unittest.TestCase):
    def test_hub_terminal_captures_stdout_and_exit_code(self):
        from services import remote_terminal

        with tempfile.TemporaryDirectory() as folder:
            sessions = Path(folder) / "sessions"
            argv = [sys.executable, "-c", "print('remote output')"]
            with patch.object(remote_terminal, "SESSIONS_DIR", sessions), patch.object(
                remote_terminal, "_command_argv", return_value=argv
            ):
                item = remote_terminal.start_hub_command("ignored", "admin", cwd=folder)
                for _ in range(100):
                    current = remote_terminal.get_session(item["id"])
                    if current["status"] not in {"queued", "running"}:
                        break
                    time.sleep(0.02)
                self.assertEqual(current["status"], "success")
                self.assertEqual(current["exit_code"], 0)
                self.assertIn("remote output", current["output"])

    def test_display_remote_command_reports_output(self):
        from agent.jobs import remote_command

        class Output:
            def __init__(self):
                self.lines = iter(["line one\n", "line two\n", ""])

            def readline(self):
                return next(self.lines, "")

        class Process:
            returncode = 0
            stdout = Output()

            def poll(self):
                return 0

        reports = []
        with patch.object(remote_command.subprocess, "Popen", return_value=Process()):
            remote_command.handle_remote_command(
                {"payload": {"command": "echo hello"}},
                lambda status, progress, message: reports.append((status, progress, message)),
            )
        self.assertEqual(reports[-1][0], "success")
        self.assertIn("line two", reports[-1][2])

    def test_route_and_navigation_are_admin_only(self):
        route = (ROOT / "hub/routes/maintenance.py").read_text(encoding="utf-8")
        app = (ROOT / "hub/app.py").read_text(encoding="utf-8")
        shell = (ROOT / "hub/templates/application_shell.html").read_text(encoding="utf-8")
        self.assertIn('@role_required("admin")', route)
        self.assertIn('"/maintenance"', app)
        self.assertIn('current_user.role == "admin"', shell)


if __name__ == "__main__":
    unittest.main()
