#!/usr/bin/env python3
from pathlib import Path
import re
root = Path(__file__).resolve().parents[1] / 'web'
required = ['index.html', 'styles.css', 'app.js', 'manifest.webmanifest']
missing = [name for name in required if not (root / name).exists()]
if missing:
    raise SystemExit('missing: ' + ', '.join(missing))
html = (root / 'index.html').read_text()
js = (root / 'app.js').read_text()
css = (root / 'styles.css').read_text()
assert '<canvas id="game"' in html
assert 'requestFullscreen' in js
assert 'requestAnimationFrame' in js
assert 'downsampleTo16k' in js
assert 'WebSocket' in js
assert 'getUserMedia' in js
assert 'pointerdown' in js
assert 'selectstart' in js
assert 'stick-base' in html
assert 'mic-panel' in html
assert 'touch-action:none' in css
assert 'user-select:none' in css
assert '-webkit-touch-callout:none' in css
assert re.search(r'context 8192', js)
print('web_static_check ok')

assert 'wss://nitro.jonnyontherun.org/llm_game_stt' not in js
assert 'browserSttLanguage' in js
assert 'stt_processing' in js
assert 'wh-ch710n' not in js.lower()
assert 'bluetooth' not in js.lower()
