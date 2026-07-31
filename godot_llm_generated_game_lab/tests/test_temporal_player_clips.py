#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image,ImageSequence
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
from animation_quality import analyze_animation,validate_animation
manifest=json.loads((ROOT/'data/generated_world.json').read_text())
assert manifest['asset_engine']=='sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha'
assert manifest['fallback_used'] is False
player=manifest['assets']['player']
assert player['pose_driven'] is True and player['engine'] == 'StableAnimator' and player['alpha_temporal_model'] is True and player['fallback_used'] is False
assert set(player['clips'])=={'idle','walk','player_interact','player_attack','player_use'}
for name,clip in player['clips'].items():
    assert clip['pose_driven'] is True and clip['engine'] == 'StableAnimator' and clip['fallback_used'] is False
    expected_gif_frames=clip['frame_count']-(1 if name in {'idle','walk'} else 0)
    assert clip['review_pass'] is True and clip['gif_frame_count']==expected_gif_frames and clip['distinct_gif_frames']==expected_gif_frames and clip['frame_count'] >= (12 if name in {'idle','walk'} else 16)
    assert clip['gif_looped'] is True and clip['gif_loop']==0 and clip['gif_duplicate_closure_frame'] is False
    assert clip['gif_palette_mode']=='single shared 254-color palette; index 0 transparent'
    assert len(clip['gif_frame_durations_ms'])==expected_gif_frames and set(clip['gif_frame_durations_ms'])=={120,130}
    assert sum(clip['gif_frame_durations_ms'])==expected_gif_frames*clip['frame_duration_ms']==clip['gif_total_duration_ms']
    assert clip['frame_width']==288 and clip['frame_height']==384
    assert clip['min_reference_cosine'] >= 0.60
    assert clip['min_adjacent_identity_cosine'] >= 0.94
    assert clip['max_foreground_coverage'] <= 0.65
    assert clip['max_border_visible_ratio'] == 0.0
    assert clip['alpha_model'] == 'RobustVideoMatting mobilenetv3 official v1.0.0'
    assert clip['alpha_temporal_model'] is True
    assert clip['min_soft_alpha_ratio'] >= 0.005
    assert clip['min_largest_component_ratio'] >= 0.98
    assert max(clip['gif_sheet_mask_disagreement']) <= 0.01
    assert clip['alpha_resize'] == 'premultiplied-alpha Lanczos4'
    assert clip['pose_driver'].startswith('explicit-openpose-')
    for key in ['png_path','gif_path','sheet_path']:
        path=ROOT/clip[key]
        assert path.is_file() and path.stat().st_size>0,(name,key,path)
    with Image.open(ROOT/clip['gif_path']) as image:
        looped=image.info.get('loop')==0
        durations=[];palette_tables=[]
        for index in range(image.n_frames):
            image.seek(index);durations.append(image.info.get('duration'))
            palette=image.getpalette()
            if palette:palette_tables.append(tuple(palette))
        assert image.n_frames==clip['gif_frame_count'] and looped is clip['gif_looped']
        assert durations==clip['gif_frame_durations_ms']
        assert len(palette_tables)==1 and len(set(palette_tables))==1
    quality=analyze_animation(ROOT/clip['sheet_path'],ROOT/clip['gif_path'],clip['frame_count'],clip['frame_width'],clip['frame_height'],gif_frame_count=clip['gif_frame_count'])
    errors=validate_animation(quality,transparent=True,loop_required=name in {'idle','walk'},action_clip=name not in {'idle','walk'},clip_name=name,require_soft_alpha=True)
    assert not errors,(name,errors,quality.to_dict())
assert player['clips']['walk']['semantic_motion']['semantic_pass'] is True
assert player['clips']['walk']['semantic_motion']['body_joints_detected_each_frame'] == 17
assert player['clips']['walk']['semantic_motion']['ankle_separation_range'] >= 0.4
script=(ROOT/'scripts/generated_world.gd').read_text()
for token in ['func _add_animation_clip','animation.animation_finished.connect','animation.play("idle")','func _update_player_locomotion_animation','return "walk"','StableAnimator pose-driven clips']:
    assert token in script,token
assert 'animation.play("generated")' not in script
print('temporal player clip contracts passed')
