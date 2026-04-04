#!/usr/bin/env bash
set -euo pipefail

ROOT=/data/src/github/games
PROJECT=$ROOT/unity/projects/asset_basket_showcase
UNITY=/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity
CATALOG=$ROOT/unity/assetstore/metadata/my_assets.json
STATE=$ROOT/unity/assetstore/metadata/native_download_state.json
PACKAGE_LIST=$ROOT/unity/assetstore/metadata/showcase_package_paths.txt
STRIP_SCRIPT=$ROOT/unity/assetstore/strip_showcase_imported_code.sh
LOG_DIR=$ROOT/unity/assetstore/logs
SCENE_PATH=Assets/Scenes/AssetBasketShowcase.unity
REPORT_PATH=$ROOT/unity/assetstore/logs/asset_basket_showcase_build_report.txt
INVENTORY_PATH=$ROOT/unity/assetstore/logs/asset_basket_showcase_inventory.txt

mkdir -p "$LOG_DIR"

python3 - <<'PY' "$CATALOG" "$STATE" "$PACKAGE_LIST"
import json, sys
from pathlib import Path
catalog = json.loads(Path(sys.argv[1]).read_text())
state = json.loads(Path(sys.argv[2]).read_text())
out = Path(sys.argv[3])
missing = []
paths = []
for item in catalog:
    key = str(item['packageId'])
    entry = state.get(key, {})
    if entry.get('status') != 'downloaded' or not entry.get('path'):
        missing.append(f"{key}\t{item['displayName']}\t{entry.get('status')}")
    else:
        paths.append(entry['path'])
if missing:
    print('Missing downloads:', file=sys.stderr)
    print('\n'.join(missing), file=sys.stderr)
    raise SystemExit(1)
out.write_text('\n'.join(paths) + '\n')
print(out)
PY

run_unity() {
  local log_name="$1"
  shift
  sudo -u hans -H "$UNITY" -batchmode -nographics -quit -projectPath "$PROJECT" "$@" -logFile "$LOG_DIR/$log_name"
}

run_unity showcase_import_all.log \
  -executeMethod HPR.AssetBasketShowcase.AssetBasketShowcaseTools.ImportPackagesFromArgs \
  -packageList "$PACKAGE_LIST"

bash "$STRIP_SCRIPT" > "$LOG_DIR/showcase_strip_code.log"

run_unity showcase_repair_materials.log \
  -executeMethod HPR.AssetBasketShowcase.AssetBasketShowcaseTools.RepairUnsupportedMaterialsFromArgs

run_unity showcase_inventory.log \
  -executeMethod HPR.AssetBasketShowcase.AssetBasketShowcaseTools.InventoryReportFromArgs \
  -reportPath "$INVENTORY_PATH"

run_unity showcase_build_scene.log \
  -executeMethod HPR.AssetBasketShowcase.AssetBasketSceneBuilder.BuildShowcaseSceneFromArgs \
  -scenePath "$SCENE_PATH" \
  -reportPath "$REPORT_PATH"
