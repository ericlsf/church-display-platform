#!/usr/bin/env python3
from pathlib import Path
import re, shutil
from datetime import datetime
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'hub/templates/base.html'
BACKUPS=ROOT/'backups'
CSS='<link rel="stylesheet" href="/static/application-shell.css">'
INCLUDE='{% include "application_shell.html" %}'
SCRIPT='<script src="/static/application-shell.js"></script>'
OLD_INCLUDES=('{% include "navigation_shell.html" %}',)
OLD_SCRIPTS=('navigation-v7.js','navigation-v7.1.js','navigation-v8.js','breadcrumb-v8.1.js','layout-v8.1.js')

def main():
    BACKUPS.mkdir(parents=True,exist_ok=True)
    target=BACKUPS/f"base.html.pre-v9-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(BASE,target)
    text=BASE.read_text(encoding='utf-8')
    for item in OLD_INCLUDES: text=text.replace(item,'')
    for name in OLD_SCRIPTS:
        text=re.sub(rf'\s*<script[^>]+src="/static/{re.escape(name)}"[^>]*></script>\s*','\n',text,flags=re.I)
    for item in (INCLUDE,SCRIPT,CSS): text=text.replace(item,'')
    body=re.search(r'<body\b[^>]*>',text,re.I)
    if not body: raise SystemExit('Could not find <body>')
    text=text[:body.end()]+'\n'+INCLUDE+'\n'+text[body.end():]
    h=text.lower().find('</head>')
    if h<0: raise SystemExit('Could not find </head>')
    text=text[:h]+'\n'+CSS+'\n'+text[h:]
    b=text.lower().rfind('</body>')
    if b<0: raise SystemExit('Could not find </body>')
    text=text[:b]+'\n'+SCRIPT+'\n'+text[b:]
    BASE.write_text(text,encoding='utf-8')
    check=BASE.read_text(encoding='utf-8')
    assert check.count(INCLUDE)==1 and check.count(CSS)==1 and check.count(SCRIPT)==1
    for name in OLD_SCRIPTS: assert name not in check
    print(f'Backup created: {target}')
    print('v9.0.0 single application shell applied.')
if __name__=='__main__': main()
