#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/verification/2026-07-30/player-walk-articulated';m=json.loads((E/'manifest.json').read_text())
assert m['ok'] is True and m['benchmark']=='articulated-bvh-player-walk' and m['frame_generation_model_used'] is False and m['looping'] is True
for relative,expected in m['files'].items():
 p=E/relative;assert p.is_file() and p.stat().st_size==expected['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==expected['sha256']
q=m['metrics'];p=m['dwpose_metrics'];motion=m['motion_review'];edge=m['edge_review']
assert q['frames']==32 and q['dimensions']==[512,768] and q['duration_ms']==50 and q['loop']==0 and q['unique_frames']==32
assert q['seam_ratio']<=1.5 and q['internal_max_ratio']<=2 and q['head_aligned_unique_hashes']==1
assert q['left_stance_x_std']<.001 and q['right_stance_x_std']<.001 and q['left_stance_y_std']<.001 and q['right_stance_y_std']<.001
assert q['alpha_border_max']==0 and q['alpha_soft_min']>=.005 and q['largest_component_min']>=.97 and q['union_coverage']>=.999 and q['fallback_used'] is False
assert p['frames']==32 and p['min_body_confident']==17 and p['max_people']==1 and p['support_crossings']>=2 and p['ankle_vertical_difference_range']>=.08
for key in ['natural_walk_cycle','two_support_exchanges','planted_stance_feet','natural_knees','natural_arms','stable_rigid_torso','seamless_loop','overall_pass']:assert motion[key] is True,key
for key in ['hidden_internal_jump','belly_wobble_or_stretch','limb_distortion','foot_sliding','body_position_jump','paper_doll_motion']:assert motion[key] is False,key
for key in ['face_clear','face_identical_appearance','head_complete','hair_complete','clean_joint_connections','clean_checkerboard_edges','clean_dark_edges','clean_light_edges','overall_pass']:assert edge[key] is True,key
for key in ['red_face_noise','blurred_face','missing_head','joint_gaps','double_limbs','wrong_occlusion_pop','sparkling_border','dark_halo','light_halo','black_rectangle','background_flicker']:assert edge[key] is False,key
assert motion['confidence_percent']>=90 and edge['confidence_percent']>=90
print('articulated BVH player-walk evidence passed')
