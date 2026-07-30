#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
root=ROOT/'docs/verification/2026-07-30'
evidence=json.loads((root/'verification.json').read_text())
manifest=json.loads((ROOT/'data/generated_world.json').read_text())
assert evidence['asset_engine']==manifest['asset_engine']=='sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha'
assert evidence['fallback_used'] is False and manifest['fallback_used'] is False
assert evidence['screenshot_sha256']==hashlib.sha256((root/'public-scene.png').read_bytes()).hexdigest()
assert evidence['recognizability_sha256']==hashlib.sha256((root/'public-scene-recognizability.json').read_bytes()).hexdigest()
assert evidence['defects_sha256']==hashlib.sha256((root/'public-scene-defects.json').read_bytes()).hexdigest()
expected={'player','mother','dining_table','chandelier','sideboard','curtains','wall_surface','carpet','kitchen_door','cookies'}
assert set(evidence['objects'])==expected
assert all(value['visible'] and value['recognizable'] and value['confidence']>=0.7 for value in evidence['objects'].values())
defects=evidence['defects']
for key in ['large_white_bars','rectangular_source_backgrounds','character_halos','severe_overlap','objects_too_small']:
    assert defects[key] is False,key
assert defects['scene_coherent'] is True
assert defects['player_complete'] is True
assert defects['mother_complete'] is True

assert evidence['build_id']=='your-mom-stableanimator-rvm-alpha-v6'
assert evidence['player_alpha_model']=='RobustVideoMatting mobilenetv3 official v1.0.0'
assert evidence['player_alpha_temporal_model'] is True
assert evidence['player_alpha_resize']=='premultiplied-alpha Lanczos4'
for filename,key in [
    ('public-player-roi.png','player_roi_sha256'),
    ('public-player-context.png','player_context_sha256'),
    ('public-player-matte-review.json','player_matte_review_sha256'),
    ('public-player-boundary-metrics.json','player_boundary_metrics_sha256'),
    ('rvm-dark-light-contact-review.json','rvm_contact_review_sha256'),
]:
    assert evidence[key]==hashlib.sha256((root/filename).read_bytes()).hexdigest(),(filename,key)
matte=evidence['player_matte_review']
assert matte['complete_head'] and matte['complete_hands'] and matte['complete_feet']
for key in ['white_halo','dark_halo','uniform_rectangular_background','visible_box_boundary','background_contamination']:
    assert matte[key] is False,key
assert matte['edge_quality']=='clean' and matte['confidence_percent']>=70 and matte['pass'] is True
boundary=evidence['player_boundary_metrics']
assert boundary['rectangular_matte_boundary_detected'] is False
assert boundary['fraction_gt_20']<0.35
contact=evidence['rvm_contact_review']
assert contact['overall_pass'] is True
for key in ['white_fringes','dark_fringes','missing_body_parts','background_rectangles','edge_flicker_visible']:
    assert contact[key] is False,key

final_vlm=json.loads((root/'final-public-scene-vlm.json').read_text())
assert final_vlm['screenshot_sha256']==hashlib.sha256((root/'public-scene.png').read_bytes()).hexdigest()
assert final_vlm['screenshot_bytes']==(root/'public-scene.png').stat().st_size
assert final_vlm['reviewed_public_url']=='https://nitro.jonnyontherun.org/llm_game/'
assert 'CPU-only' in final_vlm['review_runtime'] and 'GPU layers 0' in final_vlm['review_runtime']
review=final_vlm['review']
for key in ['overall_pass','player_complete_normal_adult','mom_recognizable','dining_table_recognizable','chandelier_recognizable','sideboard_recognizable','curtains_recognizable','cookies_recognizable']:
    assert review[key] is True,key
for key in ['opaque_white_rectangles','severe_halos_or_clipping','broken_anatomy_or_duplicate_limbs','major_overlap_or_unreadable_clutter']:
    assert review[key] is False,key

print('scene recognizability evidence passed')
