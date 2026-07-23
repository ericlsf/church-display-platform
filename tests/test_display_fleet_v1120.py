from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / 'hub/templates/displays.html').read_text()
css = (ROOT / 'hub/static/display-fleet-v1120.css').read_text()
js = (ROOT / 'hub/static/display-fleet-v1120.js').read_text()
assert 'display-fleet-v1120.css' in template
assert 'display-fleet-v1120.js' in template
assert 'display-inspector' in template
assert 'data-open-inspector' in template
assert 'Google Drive' in template
assert 'Sync remote' not in template
assert 'grid-template-columns:repeat(auto-fit,minmax(390px,1fr))' in css
assert 'aspect-ratio:16/7.7' in css
assert 'openInspector' in js and 'Escape' in js
print('v11.2 fleet workspace tests passed')
