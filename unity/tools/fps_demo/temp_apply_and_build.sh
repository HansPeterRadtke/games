#!/usr/bin/env bash
set -euo pipefail

UNITY_BIN="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}"
MAIN_PROJECT="${MAIN_PROJECT:-/data/src/github/games/unity/projects/fps_demo}"
TEMP_ASSET_DIRS="${TEMP_ASSET_DIRS:-Free Wood Door Pack,Low Poly Weapons VOL.1,FurnishedCabin,Brick Project Studio,Furniture Mega Pack,nappin,npc_casual_set_00,Survivalist}"
TEMP_PROJECT="$(TEMP_ASSET_DIRS="$TEMP_ASSET_DIRS" /data/src/github/games/unity/tools/fps_demo/sync_temp_project.sh)"
TEMP_BUILD_DIR="$TEMP_PROJECT/Build/Linux"
MAIN_BUILD_DIR="$MAIN_PROJECT/Build/Linux"

run_unity() {
  local method="$1"
  sudo -u hans env HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:1 XAUTHORITY=/home/hans/.Xauthority \
    nice -n 15 "$UNITY_BIN" -batchmode -nographics -projectPath "$TEMP_PROJECT" -executeMethod "$method" -quit -logFile -
}

find "$TEMP_PROJECT/Library" -maxdepth 1 \( -name '*lock*' -o -name '*.pid' \) -delete 2>/dev/null || true
rm -f "$TEMP_PROJECT/Temp/UnityLockfile" || true

run_unity ThirdPartyAssetIntegrator.ApplySelectedLocalPacksFromBatch
run_unity SceneBootstrap.BuildLinux

install -d "$MAIN_PROJECT/Assets/Scenes" "$MAIN_BUILD_DIR"
cp -a "$TEMP_PROJECT/Assets/Scenes/Gameplay.unity" "$MAIN_PROJECT/Assets/Scenes/Gameplay.unity"
cp -a "$TEMP_PROJECT/Build/Linux/." "$MAIN_BUILD_DIR/"

echo "Temp project: $TEMP_PROJECT"
echo "Updated scene: $MAIN_PROJECT/Assets/Scenes/Gameplay.unity"
echo "Updated build: $MAIN_BUILD_DIR/FPSDemo.x86_64"
