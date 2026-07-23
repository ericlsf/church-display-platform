from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = (ROOT / 'hub/templates/base.html').read_text()
displays = (ROOT / 'hub/templates/displays.html').read_text()
css = (ROOT / 'hub/static/display-fleet-v1120.css').read_text()
js = (ROOT / 'hub/static/display-fleet-v1120.js').read_text()

assert '{% block head %}{% endblock %}' in base
assert '/static/display-fleet-v1120.css?v=11.2.1' in displays
assert '/static/display-fleet-v1120.js?v=11.2.1' in displays
assert '.display-card-grid' in css
assert '.display-inspector' in css
assert 'data-open-inspector' in displays
assert 'openInspector' in js
print('v11.2.1 fleet stylesheet hotfix tests passed')
