#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"
STYLE = ROOT / "hub" / "static" / "style.css"
GITIGNORE = ROOT / ".gitignore"

NAV = '''<nav class="main-nav">
  <a class="{{ 'active' if active == 'dashboard' else '' }}" href="/">Dashboard</a>
  <a class="{{ 'active' if active == 'operations' else '' }}" href="/operations">Operations</a>
  <a class="{{ 'active' if active in ['content', 'media'] else '' }}" href="/content">Content</a>
  <a class="{{ 'active' if active == 'schedules' else '' }}" href="/schedules">Schedules</a>
  <details class="nav-menu" {% if active in ['displays','groups','sites','discovery','health'] %}open{% endif %}><summary>Fleet</summary><div class="nav-dropdown"><a class="{{ 'active' if active == 'displays' else '' }}" href="/displays">Displays</a><a class="{{ 'active' if active == 'groups' else '' }}" href="/groups">Groups</a><a class="{{ 'active' if active == 'sites' else '' }}" href="/sites">Sites</a><a class="{{ 'active' if active == 'discovery' else '' }}" href="/discovery">Enrollment</a><a class="{{ 'active' if active == 'health' else '' }}" href="/health">Health</a></div></details>
  <details class="nav-menu" {% if active in ['deployments','jobs','releases','system','users','audit','setup'] %}open{% endif %}><summary>Manage</summary><div class="nav-dropdown"><a class="{{ 'active' if active == 'deployments' else '' }}" href="/deployments">Deployments</a><a class="{{ 'active' if active == 'jobs' else '' }}" href="/jobs">Jobs</a><a class="{{ 'active' if active == 'releases' else '' }}" href="/releases">Releases</a>{% if not current_user or current_user.role == 'admin' %}<a class="{{ 'active' if active == 'system' else '' }}" href="/system">System</a><a class="{{ 'active' if active == 'users' else '' }}" href="/users">Users</a><a class="{{ 'active' if active == 'audit' else '' }}" href="/audit">Audit</a><a class="{{ 'active' if active == 'setup' else '' }}" href="/setup">Setup</a>{% endif %}</div></details>
</nav>'''

CSS = '''/* v3.0 simplified navigation and sites */
.main-nav{display:flex;align-items:center;gap:8px;overflow:visible;flex-wrap:wrap}.nav-menu{position:relative}.nav-menu>summary{list-style:none;cursor:pointer;color:#ddd;padding:9px 12px;border-radius:8px;background:#181818;border:1px solid #292929;white-space:nowrap}.nav-menu>summary::-webkit-details-marker{display:none}.nav-menu>summary::after{content:" ▾";color:#888}.nav-menu[open]>summary{background:#252525;border-color:#555}.nav-dropdown{position:absolute;top:calc(100% + 8px);left:0;min-width:190px;background:#101010;border:1px solid #3a3a3a;border-radius:10px;padding:8px;display:grid;gap:5px;box-shadow:0 14px 30px rgba(0,0,0,.45);z-index:100}.nav-dropdown a{display:block;width:100%}.site-heading{display:grid;grid-template-columns:minmax(220px,1fr) minmax(360px,1fr);gap:18px;align-items:start}.check-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin:10px 0 16px}.check-card{margin:0;padding:10px 12px;background:#121212;border:1px solid #333;border-radius:8px}.action-grid{display:flex;gap:8px;flex-wrap:wrap}.action-grid form{margin:0}details>summary{cursor:pointer;color:#9ec3ff;margin:10px 0}@media(max-width:760px){.site-heading{grid-template-columns:1fr}.nav-dropdown{position:fixed;left:14px;right:14px;top:110px;min-width:0}}'''

def main():
    text = APP.read_text()
    if "from routes.sites import sites_bp" not in text:
        lines=text.splitlines(); idx=max([i for i,l in enumerate(lines) if l.startswith("from routes.")], default=0); lines.insert(idx+1,"from routes.sites import sites_bp"); text="\n".join(lines)+"\n"
    if "app.register_blueprint(sites_bp)" not in text:
        lines=text.splitlines(); idx=max([i for i,l in enumerate(lines) if "app.register_blueprint(" in l], default=None)
        if idx is None: raise SystemExit("Could not find blueprint registrations")
        lines.insert(idx+1,"    app.register_blueprint(sites_bp)"); text="\n".join(lines)+"\n"
    APP.write_text(text)
    base=BASE.read_text(); base,count=re.subn(r"<nav(?:\s[^>]*)?>.*?</nav>",NAV,base,count=1,flags=re.DOTALL)
    if count != 1: raise SystemExit("Could not replace navigation")
    BASE.write_text(base)
    css=STYLE.read_text() if STYLE.exists() else ""
    if "/* v3.0 simplified navigation and sites */" not in css: STYLE.write_text(css.rstrip()+"\n\n"+CSS+"\n")
    lines=GITIGNORE.read_text().splitlines() if GITIGNORE.exists() else []
    if "hub/config/sites.json" not in lines: lines.append("hub/config/sites.json")
    GITIGNORE.write_text("\n".join(lines)+"\n")
    print("v3.0.0 multi-site and navigation update applied.")

if __name__ == "__main__": main()
