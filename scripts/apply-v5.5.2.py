#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/display_details.html"

UPDATE_CARD = '''
  <div class="stat-card update-stat-card">
    {% if upgrade.update_available and not upgrade.active_job %}
      <span class="update-available-label">Update Available</span>
      <strong>{{ upgrade.current_version }} &rarr; {{ upgrade.latest_version }}</strong>
      <form method="POST" action="/display/{{ display.id }}/upgrade">
        <input type="hidden" name="target" value="{{ upgrade.latest_version }}">
        <input type="hidden" name="mode" value="deploy">
        {% if maintenance.enabled %}
          <input type="hidden" name="override_maintenance" value="on">
        {% endif %}
        <button class="primary compact-upgrade-button" type="submit">Upgrade Now</button>
      </form>
    {% elif upgrade.active_job %}
      <strong>{{ upgrade.active_job.progress|default(0) }}%</strong>
      <span>Upgrade in progress</span>
    {% else %}
      <strong>{{ upgrade.current_version }}</strong>
      <span>Software Current</span>
    {% endif %}
  </div>
'''

def main():
    text = TEMPLATE.read_text(encoding="utf-8")
    if "update-stat-card" not in text:
        marker = "<span>Health</span>"
        pos = text.find(marker)
        if pos < 0:
            raise SystemExit("Could not find Health card")
        end = text.find("</div>", pos)
        if end < 0:
            raise SystemExit("Could not find end of Health card")
        end += len("</div>")
        text = text[:end] + "\n" + UPDATE_CARD + text[end:]

    heading = text.find("<h2>Software Upgrade</h2>")
    if heading >= 0:
        start = text.rfind('<div class="section"', 0, heading)
        if start >= 0:
            open_end = text.find(">", start)
            opening = text[start:open_end + 1]
            if 'id="software-upgrade"' not in opening:
                text = text[:open_end] + ' id="software-upgrade"' + text[open_end:]

    TEMPLATE.write_text(text, encoding="utf-8")
    print("v5.5.2 media count and update card applied.")

if __name__ == "__main__":
    main()
