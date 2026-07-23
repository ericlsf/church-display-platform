#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
APP=ROOT/"hub/app.py"; BASE=ROOT/"hub/templates/base.html"; CSS=ROOT/"hub/static/style.css"; APPEND=ROOT/"hub/static/style.css.append"

def patch_app():
    text=APP.read_text()
    imp="from routes.operations_center import operations_center_bp"
    if imp not in text:
        lines=text.splitlines(); idx=[i for i,l in enumerate(lines) if l.startswith("from routes.")]
        lines.insert(max(idx,default=0)+1,imp); text="\n".join(lines)+"\n"
    reg="    app.register_blueprint(operations_center_bp)"
    if reg not in text:
        lines=text.splitlines(); idx=[i for i,l in enumerate(lines) if "app.register_blueprint(" in l]
        if not idx: raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(idx)+1,reg); text="\n".join(lines)+"\n"
    APP.write_text(text)

def patch_nav():
    text=BASE.read_text()
    if 'href="/operations-center"' in text: return
    link='<a href="/operations-center">Operations Center</a>'
    for marker in ['href="/fleet-operations"','href="/operations"','href="/dashboard"','href="/"']:
        i=text.find(marker)
        if i<0: continue
        end=text.find("</a>",i)
        if end>=0:
            end+=4; BASE.write_text(text[:end]+"\n"+link+text[end:]); return

def patch_css():
    if not APPEND.exists(): return
    marker="/* v4.6.0 operations center */"
    text=CSS.read_text()
    if marker not in text: CSS.write_text(text+"\n"+marker+"\n"+APPEND.read_text())
    APPEND.unlink()

patch_app(); patch_nav(); patch_css(); print("v4.6.0 Operations Center applied.")
