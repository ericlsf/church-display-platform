import os
import queue
import signal
import subprocess
import time

MAX_OUTPUT = 64 * 1024
TIMEOUT_SECONDS = 900


def handle_remote_command(job, report):
    command = str((job.get("payload") or {}).get("command") or "").strip()
    if not command:
        raise ValueError("A command is required")
    if "\x00" in command or len(command) > 8000:
        raise ValueError("The command is invalid or too long")
    output = f"$ {command}\n"
    report("running", 10, output)
    process = subprocess.Popen(
        ["/bin/bash", "-lc", command],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, start_new_session=True,
    )
    lines = queue.Queue()

    def read_output():
        for value in iter(process.stdout.readline, ""):
            lines.put(value)
        lines.put(None)

    import threading
    threading.Thread(target=read_output, daemon=True).start()
    started = time.monotonic()
    reader_done = False
    while True:
        try:
            line = lines.get(timeout=0.2)
            if line is None:
                reader_done = True
            else:
                output = (output + line)[-MAX_OUTPUT:]
                report("running", 50, output)
        except queue.Empty:
            pass
        if process.poll() is not None and reader_done:
            break
        if time.monotonic() - started > TIMEOUT_SECONDS:
            os.killpg(process.pid, signal.SIGTERM)
            raise TimeoutError(f"Command stopped after {TIMEOUT_SECONDS} seconds")
    close_output = getattr(process.stdout, "close", None)
    if close_output:
        close_output()
    output = (output + f"\n[process exited with code {process.returncode}]\n")[-MAX_OUTPUT:]
    report("success" if process.returncode == 0 else "failed", 100, output)
