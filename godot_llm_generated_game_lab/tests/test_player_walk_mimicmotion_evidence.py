#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/verification/2026-07-30/player-walk-mimicmotion'
m=json.loads((E/'manifest.json').read_text())
assert m['ok'] is True and m['benchmark']=='mimicmotion-player-walk'
assert m['engine']=='Tencent MimicMotion 1.1' and m['model_used_for_frames'] is True and m['looping'] is False
for relative,expected in m['files'].items():
    path=E/relative;assert path.is_file() and path.stat().st_size==expected['bytes'];assert hashlib.sha256(path.read_bytes()).hexdigest()==expected['sha256']
metrics=m['metrics'];pose=m['dwpose_metrics'];identity=m['identity'];review=m['review'];coverage=m['provenance']['checkpoint_coverage'];compat=m['provenance']['compatibility']
assert metrics['frame_count']==24 and metrics['dimensions']==[512,768] and metrics['duration_ms']==70 and metrics['loop'] is None and metrics['unique_frames']==24
assert metrics['left_stance_x_std']<4 and metrics['right_stance_x_std']<4 and metrics['left_stance_y_std']<2 and metrics['right_stance_y_std']<2
assert metrics['ground_std']<1 and metrics['body_center_std']<8 and metrics['alpha_border_max']==0 and metrics['alpha_soft_min']>=.005 and metrics['largest_component_min']>=.98 and metrics['fallback_used'] is False
assert pose['frames']==24 and pose['min_body_confident']==17 and pose['support_crossings']>=1 and pose['left_ankle_y_range']>=.08 and pose['right_ankle_y_range']>=.04
assert identity['min_reference_cosine']>=.60 and identity['min_adjacent_cosine']>=.90
assert coverage=={'unet_keys':1428,'pose_net_keys':19,'missing_unet':0,'missing_pose_net':0,'unexpected':0}
for key in ['network_code_changed','weights_changed','pose_preprocessing_changed','denoising_changed','tile_fusion_changed']:assert compat[key] is False,key
for key in ['same_person','complete_head','face_visible','face_stable','face_sharp_enough','complete_hands','complete_feet','natural_walk_pass','support_transfers_once','planted_stance_foot','natural_knees','natural_arms','stable_torso_shape','stable_body_position','stable_colors','overall_pass']:assert review[key] is True,key
for key in ['red_face_noise','blurred_face','back_of_head_substitution','belly_wobble_or_stretch','limb_distortion','foot_sliding','body_position_jump','sparkling_border','black_rectangle','background_flicker']:assert review[key] is False,key
assert review['confidence_percent']>=70
print('MimicMotion player-walk evidence passed')
