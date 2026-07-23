#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
DISPATCHER = ROOT / "display/agent/dispatcher.py"
DETAILS = ROOT / "hub/templates/display_details.html"
APPEND = ROOT / "hub/templates/display_details.timeline.append.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"

def patch_app():
    text = APP.read_text(encoding="utf-8")
    imp = "from routes.deployment_timeline import deployment_timeline_bp"
    if imp not in text:
        lines = text.splitlines()
        idx = [i for i,l in enumerate(lines) if l.startswith("from routes.")]
        lines.insert(max(idx, default=0)+1, imp)
        text = "\n".join(lines) + "\n"
    reg = "    app.register_blueprint(deployment_timeline_bp)"
    if reg not in text:
        lines = text.splitlines()
        idx = [i for i,l in enumerate(lines) if "app.register_blueprint(" in l]
        if not idx:
            raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(idx)+1, reg)
        text = "\n".join(lines) + "\n"
    APP.write_text(text, encoding="utf-8")

def patch_dispatcher():
    text = DISPATCHER.read_text(encoding="utf-8")
    old = "from agent.jobs import heartbeat, management, preview, settings, sync, system, update"
    new = "from agent.jobs import heartbeat, management, preview, rollback, settings, sync, system, update"
    if old in text:
        text = text.replace(old, new, 1)
    elif "rollback" not in text:
        raise SystemExit("Could not patch dispatcher import")
    marker = '    elif job_type == "deploy_update":\n        update.handle_deploy_update(job, report)'
    addition = marker + '\n    elif job_type == "rollback_update":\n        rollback.handle_rollback_update(job, report)'
    if 'job_type == "rollback_update"' not in text:
        if marker not in text:
            raise SystemExit("Could not find deploy_update branch")
        text = text.replace(marker, addition, 1)
    DISPATCHER.write_text(text, encoding="utf-8")

def patch_template():
    text = DETAILS.read_text(encoding="utf-8")
    if "data-deployment-timeline" not in text:
        heading = text.find("<h2>Software Upgrade</h2>")
        if heading < 0:
            raise SystemExit("Could not find Software Upgrade")
        start = text.rfind('<div class="section', 0, heading)
        if start < 0:
            raise SystemExit("Could not find Software Upgrade section")
        block = APPEND.read_text(encoding="utf-8")
        DETAILS.write_text(text[:start] + block + "\n\n" + text[start:], encoding="utf-8")
        APPEND.unlink()

def patch_css():
    if not CSS_APPEND.exists():
        return
    marker = "/* v5.7.0 deployment timeline */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        CSS.write_text(text + "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8"), encoding="utf-8")
    CSS_APPEND.unlink()

patch_app()
patch_dispatcher()
patch_template()
patch_css()
print("v5.7.0 rollback and deployment timeline applied.")
