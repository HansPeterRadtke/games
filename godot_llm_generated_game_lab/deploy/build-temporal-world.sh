#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $(hostname -s) == nitro ]]
/data/venv/bin/python3 - <<'PY'
import json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
sys.path.insert(0,'server')
import world_generation as world
p=Path('data/generated_world.json')
v=json.loads(p.read_text())
assert v['version']==1 and v['complete'] is True and v['fallback_used'] is False
assert v['asset_engine']=='sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha'
assert v['gameplay_action_count']==30
plan=v['scene_plan']
assert len(plan['player']['actions'])==3
assert all(len(obj['actions'])==3 for obj in plan['objects'])
schema_errors=[error.message for error in Draft202012Validator(world.scene_plan_schema(v['user_prompt'])).iter_errors(plan)]
semantic_errors=world.validate_scene_plan(plan,v['user_prompt'])
assert not schema_errors,(schema_errors[:20])
assert not semantic_errors,(semantic_errors[:20])
player=v['assets']['player']
assert set(player['clips'])=={'idle','walk','player_interact','player_attack','player_use'}
for name,clip in player['clips'].items():
    assert clip['pose_driven'] is True and clip['engine'] == 'StableAnimator' and clip['fallback_used'] is False
    assert clip['review_pass'] is True and clip['distinct_gif_frames'] >= clip['frame_count'] - (1 if name in {'idle','walk'} else 0)
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
assert player['clips']['walk']['semantic_motion']['semantic_pass'] is True
assert player['clips']['walk']['semantic_motion']['body_joints_detected_each_frame'] == 17
assert player['clips']['walk']['semantic_motion']['ankle_separation_range'] >= 0.4
print(json.dumps({'manifest':'ok','engine':v['asset_engine'],'actions':v['gameplay_action_count'],'player_clips':list(player['clips'])}))
PY
/data/venv/bin/python3 tests/test_world_generation_contracts.py
/data/venv/bin/python3 tests/test_animation_quality.py
/data/venv/bin/python3 tests/test_temporal_player_clips.py
/data/venv/bin/python3 tests/test_player_walk_rig_evidence.py
/data/venv/bin/python3 tests/test_scene_recognizability_evidence.py
/data/venv/bin/python3 tests/test_generated_action_runtime.py
/data/venv/bin/python3 tests/test_generated_world_contract.py
/data/venv/bin/python3 tests/test_generated_world_layout.py
parse_log=$(mktemp)
trap 'rm -f "$parse_log"' EXIT
godot --headless --path . --editor --quit 2>&1 | tee "$parse_log"
if grep -Eq 'SCRIPT ERROR|Parse Error|Failed to load script' "$parse_log"; then exit 1; fi
runtime_log=$(mktemp)
timeout 30 godot --headless --path . --quit-after 20 2>&1 | tee "$runtime_log"
if grep -Eq 'SCRIPT ERROR|Parse Error|ERROR:|Invalid|Missing generated|Generated world manifest is missing' "$runtime_log"; then exit 1; fi
rm -f "$runtime_log"
bash deploy/build-web.sh
rm -rf web/generated_assets
mkdir -p web/generated_assets/player-clips
python3 - <<'PY'
import json,shutil,hashlib
from pathlib import Path
manifest=json.loads(Path('data/generated_world.json').read_text())
evidence_root=Path('docs/verification/2026-07-30')
recognizability=json.loads((evidence_root/'public-scene-recognizability.json').read_text())
defects=json.loads((evidence_root/'public-scene-defects.json').read_text())
verification=json.loads((evidence_root/'verification.json').read_text())
public={'complete':True,'fallback_used':False,'asset_engine':manifest['asset_engine'],'scene_name':manifest['scene_plan']['scene_name'],'gameplay_action_count':manifest['gameplay_action_count'],'build_id':'your-mom-stableanimator-rvm-alpha-v6','scene_review':{'recognizability':recognizability,'defects':defects,'screenshot_sha256':verification['screenshot_sha256'],'player_matte_review':verification['player_matte_review'],'player_boundary_metrics':verification['player_boundary_metrics'],'rvm_contact_review':verification['rvm_contact_review'],'evidence_sha256':hashlib.sha256((evidence_root/'verification.json').read_bytes()).hexdigest()},'assets':{}}
for asset_id,asset in manifest['assets'].items():
    safe=''.join(ch if ch.isalnum() or ch in '-_' else '-' for ch in asset_id).strip('-') or 'asset'
    gif_target=Path('web/generated_assets')/(safe+'.gif')
    png_target=Path('web/generated_assets')/(safe+'.png')
    sheet_target=Path('web/generated_assets')/(safe+'.sheet.png')
    shutil.copy2(asset['gif_path'],gif_target); shutil.copy2(asset['png_path'],png_target); shutil.copy2(asset['sheet_path'],sheet_target)
    item={'gif':'generated_assets/'+gif_target.name,'png':'generated_assets/'+png_target.name,'sheet':'generated_assets/'+sheet_target.name,'frames':asset['frame_count'],'engine':asset.get('engine'),'pose_driven':bool(asset.get('pose_driven',False)),'alpha_model':asset.get('alpha_model'),'alpha_temporal_model':bool(asset.get('alpha_temporal_model',False)),'alpha_resize':asset.get('alpha_resize'),'fallback_used':bool(asset.get('fallback_used',False))}
    if asset_id=='player':
        item['clips']={}
        for clip_name,clip in asset['clips'].items():
            base=Path('web/generated_assets/player-clips')/clip_name
            base.mkdir(parents=True,exist_ok=True)
            targets={'gif':base/'animation.gif','png':base/'canonical.png','sheet':base/'animation.sheet.png'}
            shutil.copy2(clip['gif_path'],targets['gif']); shutil.copy2(clip['png_path'],targets['png']); shutil.copy2(clip['sheet_path'],targets['sheet'])
            item['clips'][clip_name]={'gif':str(targets['gif'].relative_to('web')),'png':str(targets['png'].relative_to('web')),'sheet':str(targets['sheet'].relative_to('web')),'frames':clip['frame_count'],'engine':clip['engine'],'pose_driven':clip['pose_driven'],'motion_control':clip['motion_control'],'pose_driver':clip['pose_driver'],'identity_encoder':clip['identity_encoder'],'min_reference_cosine':clip['min_reference_cosine'],'min_adjacent_identity_cosine':clip['min_adjacent_identity_cosine'],'max_foreground_coverage':clip['max_foreground_coverage'],'max_border_visible_ratio':clip['max_border_visible_ratio'],'min_soft_alpha_ratio':clip['min_soft_alpha_ratio'],'max_soft_alpha_ratio':clip['max_soft_alpha_ratio'],'min_largest_component_ratio':clip['min_largest_component_ratio'],'alpha_model':clip['alpha_model'],'alpha_temporal_model':clip['alpha_temporal_model'],'alpha_resize':clip['alpha_resize'],'gif_sheet_mask_disagreement':clip['gif_sheet_mask_disagreement'],'contact_review':clip['contact_review'],'semantic_motion':clip.get('semantic_motion',{}),'fallback_used':clip['fallback_used'],'review_pass':clip['review_pass'],'distinct_gif_frames':clip['distinct_gif_frames']}
    public['assets'][asset_id]=item
Path('web/generated_assets/manifest.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
PY
/data/venv/bin/python3 scripts/build_gif_inspector.py
printf 'pose_driven_web_export=ok engine=%s time=%s\n' 'sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha' "$(date -Is)"
