#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image,ImageSequence
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/generated_world.json').read_text())
assert manifest['asset_engine']=='sdxl-reviewed-canonical+ltx-video-temporal+birefnet-matting'
assert manifest['fallback_used'] is False
player=manifest['assets']['player']
assert player['temporal_model'] is True and player['native_video_frames'] is True and player['fallback_used'] is False
assert set(player['clips'])=={'idle','player_interact','player_attack','player_use'}
for name,clip in player['clips'].items():
    assert clip['temporal_model'] is True and clip['native_video_frames'] is True and clip['fallback_used'] is False
    assert clip['review_pass'] is True and clip['distinct_gif_frames']==9 and clip['frame_count']==9
    assert clip['frame_width']==288 and clip['frame_height']==384
    for key in ['png_path','gif_path','sheet_path']:
        path=ROOT/clip[key]
        assert path.is_file() and path.stat().st_size>0,(name,key,path)
    with Image.open(ROOT/clip['gif_path']) as image:
        frames=list(ImageSequence.Iterator(image))
        assert len(frames)==9 and image.info.get('loop')==0
script=(ROOT/'scripts/generated_world.gd').read_text()
for token in ['func _add_animation_clip','animation.animation_finished.connect','animation.play("idle")','LTX temporal player clips']:
    assert token in script,token
assert 'animation.play("generated")' not in script
print('temporal player clip contracts passed')
