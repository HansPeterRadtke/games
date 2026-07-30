#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
root=ROOT/'docs/verification/2026-07-30'
evidence=json.loads((root/'verification.json').read_text())
manifest=json.loads((ROOT/'data/generated_world.json').read_text())
assert evidence['asset_engine']==manifest['asset_engine']=='sdxl-reviewed-scene-assets+stableanimator-pose-driven-player'
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
print('scene recognizability evidence passed')
