#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BUNDLE="docs/world_generation_samples/2026-07-27/full-pipeline-your-mom.json"
ASSET_DIR="generated/world_assets"
MANIFEST="data/generated_world.json"
/data/venv/bin/python3 - <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,'server')
import world_generation as world
p=Path('docs/world_generation_samples/2026-07-27/full-pipeline-your-mom.json')
v=json.loads(p.read_text())
plan=v.get('scene_plan')
if not isinstance(plan,dict): raise SystemExit('missing scene plan')
errors=world.validate_scene_plan(plan,v['user_prompt'])
if errors: raise SystemExit('invalid scene plan: '+json.dumps(errors,ensure_ascii=False))
print(json.dumps({'scene_plan_valid':True,'objects':len(plan['objects']),'player':plan['player']['id']},ensure_ascii=False))
PY
/data/venv/bin/python3 - <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,'server')
from world_asset_pipeline import compile_world_assets
manifest=compile_world_assets(Path('docs/world_generation_samples/2026-07-27/full-pipeline-your-mom.json'),Path('generated/world_assets'),Path('data/generated_world.json'))
print(json.dumps({'assets_complete':manifest['complete'],'assets':len(manifest['assets']),'compiled_seconds':manifest['compiled_seconds']},ensure_ascii=False))
PY
/data/venv/bin/python3 tests/test_world_generation_contracts.py
/data/venv/bin/python3 tests/test_world_asset_pipeline.py
/data/venv/bin/python3 tests/test_generated_world_contract.py
parse_log=$(mktemp)
trap 'rm -f "$parse_log"' EXIT
godot --headless --path . --editor --quit 2>&1 | tee "$parse_log"
if grep -Eq 'SCRIPT ERROR|Parse Error|Failed to load script' "$parse_log"; then
    echo 'Godot script validation failed' >&2
    exit 1
fi
python3 - <<'PY'
from pathlib import Path
p=Path('project.godot')
s=p.read_text()
s=s.replace('run/main_scene="res://scenes/main.tscn"','run/main_scene="res://scenes/generated_world.tscn"')
p.write_text(s)
PY
grep -q 'run/main_scene="res://scenes/generated_world.tscn"' project.godot
bash deploy/build-web.sh

rm -rf web/generated_assets
mkdir -p web/generated_assets
python3 - <<'PY_ASSETS'
import json,shutil
from pathlib import Path
manifest=json.loads(Path('data/generated_world.json').read_text())
public={'complete':manifest['complete'],'fallback_used':manifest['fallback_used'],'asset_engine':manifest['asset_engine'],'scene_name':manifest['scene_plan']['scene_name'],'assets':{}}
for asset_id,asset in manifest['assets'].items():
    safe=''.join(ch if ch.isalnum() or ch in '-_' else '-' for ch in asset_id).strip('-') or 'asset'
    gif_target=Path('web/generated_assets')/(safe+'.gif')
    png_target=Path('web/generated_assets')/(safe+'.png')
    sheet_target=Path('web/generated_assets')/(safe+'.sheet.png')
    shutil.copy2(asset['gif_path'],gif_target)
    shutil.copy2(asset['png_path'],png_target)
    shutil.copy2(asset['sheet_path'],sheet_target)
    public['assets'][asset_id]={'gif':'generated_assets/'+gif_target.name,'png':'generated_assets/'+png_target.name,'sheet':'generated_assets/'+sheet_target.name,'frames':asset['frame_count'],'canonical_pass':asset['verification']['canonical_pass'],'animation_pass':asset['verification']['animation_pass']}
Path('web/generated_assets/manifest.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
PY_ASSETS
/data/venv/bin/python3 tests/test_world_asset_quality.py
/data/venv/bin/python3 tests/test_generated_world_layout.py
