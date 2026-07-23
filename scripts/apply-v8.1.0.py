#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/"hub/templates/base.html"
CSS=ROOT/"hub/static/style.css"
APPEND=ROOT/"hub/static/style.css.append"

def main():
    text=BASE.read_text(encoding="utf-8")
    script='<script src="/static/layout-v8.1.js"></script>'
    if script not in text:
        anchor='<script src="/static/breadcrumb-v8.1.js"></script>'
        if anchor in text:
            text=text.replace(anchor,anchor+"\n"+script,1)
        else:
            anchor='<script src="/static/navigation-v8.js"></script>'
            if anchor in text:
                text=text.replace(anchor,anchor+"\n"+script,1)
            else:
                pos=text.lower().rfind("</body>")
                if pos<0: raise SystemExit("Could not find </body>")
                text=text[:pos]+"\n"+script+"\n"+text[pos:]
        BASE.write_text(text,encoding="utf-8")

    css=CSS.read_text(encoding="utf-8")
    marker="/* v8.1.0 layout refinement */"
    if marker not in css:
        css+="\n"+APPEND.read_text(encoding="utf-8")
        CSS.write_text(css,encoding="utf-8")
    if APPEND.exists(): APPEND.unlink()
    print("v8.1.0 layout refinement applied.")

if __name__=="__main__":
    main()
