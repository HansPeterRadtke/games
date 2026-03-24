#!/usr/bin/env bash
set -euo pipefail
PKG='/home/hans/.local/share/unity3d/Asset Store-5.x/nappin/3D ModelsPropsInterior/House Interior - Free.unitypackage'
while true; do
  if [[ -f "$PKG" ]]; then
    MAGIC=$(python3 - <<'PY'
from pathlib import Path
p = Path('/home/hans/.local/share/unity3d/Asset Store-5.x/nappin/3D ModelsPropsInterior/House Interior - Free.unitypackage')
print(p.read_bytes()[:2].hex() if p.exists() and p.stat().st_size >= 2 else '')
PY
)
    if [[ "$MAGIC" == '1f8b' ]]; then
      break
    fi
  fi
  sleep 20
done
sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000 /data/venv/bin/python /data/src/github/games/unity/tools/assetstore/unity_native_asset.py import "$PKG"
sudo -u hans -H env UNITY=/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity PROJECT=/data/src/github/games/unity/projects/fps_demo LOG=/data/src/github/games/unity/assetstore/logs/catalog_house_pack.log bash -lc '"$UNITY" -batchmode -nographics -projectPath "$PROJECT" -executeMethod PrefabCatalogReporter.ReportPrefabCatalogFromArgs -assetFolder "Assets/House Interior - Free" -quit -logFile "$LOG"'
