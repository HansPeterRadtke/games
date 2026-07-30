#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from PIL import Image,ImageSequence
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'web/gif_inspector';m=json.loads((SITE/'manifest.json').read_text())
assert m['ok'] is True and m['count']==1 and m['all_previous_gifs_deleted'] is True and m['frame_generation_model_used'] is False and m['looping'] is True
item=m['gifs'][0];assert item['slug']=='player-walk' and item['public_path']=='gifs/player-walk.gif' and item['frames']==32 and item['width']==512 and item['height']==768 and item['duration_ms']==50 and item['loop']==0
path=SITE/item['public_path'];assert list((SITE/'gifs').glob('*.gif'))==[path];assert path.stat().st_size==item['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
with Image.open(path) as im:assert len(list(ImageSequence.Iterator(im)))==32 and im.size==(512,768) and im.info.get('duration')==50 and im.info.get('loop')==0
assert item['metrics']['seam_ratio']<=1.5 and item['metrics']['internal_max_ratio']<=2 and item['metrics']['head_aligned_unique_hashes']==1
assert item['motion_review']['overall_pass'] is True and item['edge_review']['overall_pass'] is True
html=(SITE/'index.html').read_text();assert 'Articulated BVH' in html and 'Exactly one looping GIF' in html and 'No model generates these frames' in html and 'infinite' in html and html.count('gifs/player-walk.gif')==4
for retired in ['flag-in-the-wind.gif','player.gif','mom.gif','cookies.gif','chandelier.gif','sideboard.gif','dining-table.gif','MimicMotion']:assert retired not in html
print('single articulated looping player-walk inspector contracts passed')
