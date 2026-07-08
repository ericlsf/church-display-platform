import shutil
import subprocess
import urllib.request
from pathlib import Path

from agent.config import DISPLAY_ID, HUB_URL


TMP_FILE = Path("/tmp/church-display-preview.jpg")


def capture_preview():
    commands = []

    if shutil.which("grim"):
        commands.append(["grim", str(TMP_FILE)])

    if shutil.which("scrot"):
        commands.append(["scrot", str(TMP_FILE)])

    if shutil.which("gnome-screenshot"):
        commands.append(["gnome-screenshot", "-f", str(TMP_FILE)])

    if shutil.which("import"):
        commands.append(["import", "-window", "root", str(TMP_FILE)])

    if not commands:
        return False, "No screenshot tool found"

    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=20,
            )

            if result.returncode == 0 and TMP_FILE.exists():
                return True, "Preview captured"

        except Exception:
            continue

    return False, "Preview capture failed"


def upload_preview():
    ok, message = capture_preview()

    if not ok:
        return False, message

    boundary = "----ChurchDisplayPreviewBoundary"
    file_bytes = TMP_FILE.read_bytes()

    body = b""

    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="id"\r\n\r\n'
    body += DISPLAY_ID.encode()
    body += b"\r\n"

    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="preview"; filename="preview.jpg"\r\n'
    body += b"Content-Type: image/jpeg\r\n\r\n"
    body += file_bytes
    body += b"\r\n"

    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{HUB_URL}/api/v1/preview",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        response.read()

    return True, "Preview uploaded"


def handle(job, report):
    report("running", 25, "Uploading preview")

    ok, message = upload_preview()

    if ok:
        report("success", 100, message)
    else:
        report("failed", 100, message)
