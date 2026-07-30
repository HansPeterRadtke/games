#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from PIL import Image,ImageSequence
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'web/gif_inspector'
manifest=json.loads((SITE/'manifest.json').read_text())
assert manifest['ok'] is True and manifest['count']==1 and manifest['all_previous_gifs_deleted'] is True
assert manifest['model_used_for_frames'] is False and len(manifest['gifs'])==1
item=manifest['gifs'][0]
assert item['slug']=='player-walk' and item['public_path']=='gifs/player-walk.gif'
assert item['frames']==32 and item['width']==320 and item['height']==640 and item['duration_ms']==60 and item['loop']==0
path=SITE/item['public_path']
assert list((SITE/'gifs').glob('*.gif'))==[path]
assert path.stat().st_size==item['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
with Image.open(path) as image:
    assert len(list(ImageSequence.Iterator(image)))==32 and image.size==(320,640) and image.info.get('duration')==60 and image.info.get('loop')==0
metrics=item['metrics'];pose=item['dwpose_metrics'];review=item['review']
assert item['model_used_for_frames'] is False
assert metrics['aligned_head_unique_hashes']==1 and metrics['unique_frames']==32 and metrics['shared_palette'] is True
assert metrics['left_foot_vertical_range_px']>=30 and metrics['right_foot_vertical_range_px']>=30
assert metrics['border_visible_max']==0.0 and metrics['largest_component_ratio_min']>=0.975
assert pose['frames']==32 and pose['min_body_confident']==17
for key in ['same_person','head_complete','face_visible','face_stable','hands_complete','feet_complete','coherent_walk','alternating_steps','planted_stance_foot','natural_knees','natural_arms','stable_torso','stable_colors','overall_pass']:
    assert review[key] is True,key
for key in ['red_face_noise','blurred_face','back_of_head_instead_of_face','mesh_tearing','limb_stretching','sparkling_border','black_rectangle','whole_body_position_jump','background_flicker']:
    assert review[key] is False,key
assert review['confidence_percent']>=70
html=(SITE/'index.html').read_text()
assert 'Exactly one GIF' in html and 'No image-generation or video model' in html
assert html.count('gifs/player-walk.gif')==4
for retired in ['flag-in-the-wind.gif','player.gif','mom.gif','cookies.gif','chandelier.gif','sideboard.gif','dining-table.gif']:
    assert retired not in html
print('single deterministic player-walk GIF inspector contracts passed')
