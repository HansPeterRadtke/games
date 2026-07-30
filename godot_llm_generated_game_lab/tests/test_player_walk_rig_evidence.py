#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/verification/2026-07-30/player-walk-rig'
m=json.loads((E/'manifest.json').read_text())
assert m['ok'] is True and m['benchmark']=='deterministic-player-walk' and m['model_used_for_frames'] is False
for relative,expected in m['files'].items():
    path=E/relative;assert path.is_file() and path.stat().st_size==expected['bytes'];assert hashlib.sha256(path.read_bytes()).hexdigest()==expected['sha256']
metrics=m['metrics'];pose=m['dwpose_metrics'];review=m['review']
assert metrics['aligned_head_unique_hashes']==1 and metrics['unique_frames']==32 and metrics['fallback_used'] is False
assert pose['frames']==32 and pose['min_body_confident']==17
assert review['overall_pass'] is True and review['confidence_percent']>=70
for key in ['red_face_noise','blurred_face','back_of_head_instead_of_face','mesh_tearing','limb_stretching','sparkling_border','black_rectangle','whole_body_position_jump','background_flicker']:assert review[key] is False,key
print('player-walk rig evidence passed')
