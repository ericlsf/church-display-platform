#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
APP=ROOT/"hub/app.py"; BASE=ROOT/"hub/templates/base.html"

def main():
    text=APP.read_text(encoding="utf-8")
    imp="from routes.fleet_command_center import fleet_command_center_bp"
    if imp not in text:
        lines=text.splitlines(); idx=[i for i,l in enumerate(lines) if l.startswith("from routes.")]
        lines.insert(max(idx,default=0)+1,imp); text="\n".join(lines)+"\n"
    reg="    app.register_blueprint(fleet_command_center_bp)"
    if reg not in text:
        lines=text.splitlines(); idx=[i for i,l in enumerate(lines) if "app.register_blueprint(" in l]
        if not idx: raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(idx)+1,reg); text="\n".join(lines)+"\n"
    APP.write_text(text,encoding="utf-8")
    text=BASE.read_text(encoding="utf-8")
    link='<link rel="stylesheet" href="/static/fleet-command-center.css">'
    if link not in text:
        pos=text.lower().find("</head>")
        if pos<0: raise SystemExit("Could not find </head>")
        text=text[:pos]+"\n"+link+"\n"+text[pos:]
        BASE.write_text(text,encoding="utf-8")
    print("v9.1.0 Fleet Command Center applied.")

if __name__=="__main__": main()
