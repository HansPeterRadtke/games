#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from PIL import Image,ImageSequence
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'web/gif_inspector'
manifest=json.loads((SITE/'manifest.json').read_text())
assert manifest['ok'] is True and manifest['count']==1 and manifest['all_previous_gifs_deleted'] is True
assert manifest['engine']=='Tencent MimicMotion 1.1' and manifest['model_used_for_frames'] is True and manifest['looping'] is False
item=manifest['gifs'][0]
assert item['slug']=='player-walk' and item['public_path']=='gifs/player-walk.gif'
assert item['frames']==24 and item['width']==512 and item['height']==768 and item['duration_ms']==70 and item['loop'] is None
path=SITE/item['public_path'];assert list((SITE/'gifs').glob('*.gif'))==[path]
assert path.stat().st_size==item['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
with Image.open(path) as image:assert len(list(ImageSequence.Iterator(image)))==24 and image.size==(512,768) and image.info.get('duration')==70 and image.info.get('loop') is None
assert item['metrics']['left_stance_x_std']<4 and item['metrics']['right_stance_x_std']<4 and item['metrics']['alpha_border_max']==0
assert item['review']['overall_pass'] is True and item['review']['confidence_percent']>=70
html=(SITE/'index.html').read_text()
assert 'Tencent MimicMotion 1.1' in html and 'intentionally one nonlooping walking pass' in html and 'no crossfade, reversal or fake loop' in html
assert html.count('gifs/player-walk.gif')==4
for retired in ['flag-in-the-wind.gif','player.gif','mom.gif','cookies.gif','chandelier.gif','sideboard.gif','dining-table.gif']:assert retired not in html
print('single MimicMotion player-walk GIF inspector contracts passed')
