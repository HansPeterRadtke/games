#!/usr/bin/env bash
set -euo pipefail

MAIN_PROJECT="${MAIN_PROJECT:-/data/src/github/games/unity/projects/fps_demo}"
TEMP_ROOT="${TEMP_ROOT:-/data/tmp/games_unity_temp}"
TEMP_PROJECT="${TEMP_PROJECT:-$TEMP_ROOT/fps_demo}"
PACKAGE_ROOT="${PACKAGE_ROOT:-/data/src/github/games/unity/packages}"
RESET_TEMP_ROOT="${RESET_TEMP_ROOT:-0}"
SEED_LIBRARY="${SEED_LIBRARY:-1}"

ALL_LOCAL_ASSET_DIRS=(
  "ALP_Assets"
  "Brick Project Studio"
  "Flooded_Grounds"
  "Free Wood Door Pack"
  "FurnishedCabin"
  "Furniture Mega Pack"
  "Low Poly Weapons VOL.1"
  "NatureStarterKit2"
  "POLYGON city pack"
  "Survivalist"
  "_TerrainAutoUpgrade"
  "nappin"
  "npc_casual_set_00"
)

LOCAL_ASSET_DIRS=("${ALL_LOCAL_ASSET_DIRS[@]}")
if [[ -n "${TEMP_ASSET_DIRS:-}" ]]; then
  IFS=',' read -r -a LOCAL_ASSET_DIRS <<<"$TEMP_ASSET_DIRS"
fi

if [[ "$RESET_TEMP_ROOT" == "1" ]]; then
  rm -rf "$TEMP_ROOT"
fi

mkdir -p "$TEMP_PROJECT"

if [[ "$SEED_LIBRARY" == "1" && ! -d "$TEMP_PROJECT/Library" && -d "$MAIN_PROJECT/Library" ]]; then
  mkdir -p "$TEMP_PROJECT/Library"
  rsync -a \
    --delete \
    --exclude='ArtifactDB-lock' \
    --exclude='SourceAssetDB-lock' \
    --exclude='*.pid' \
    --exclude='UnityShaderCompiler-*' \
    "$MAIN_PROJECT/Library/" "$TEMP_PROJECT/Library/"
fi

rsync_args=(
  -a
  --delete
  --exclude=Library
  --exclude=Temp
  --exclude=Logs
  --exclude=obj
  --exclude=Build
)

for asset_dir in "${ALL_LOCAL_ASSET_DIRS[@]}"; do
  rsync_args+=("--exclude=/Assets/$asset_dir/***")
  rsync_args+=("--exclude=/Assets/$asset_dir.meta")
done

rsync "${rsync_args[@]}" "$MAIN_PROJECT/" "$TEMP_PROJECT/"

mkdir -p "$TEMP_PROJECT/Assets" "$TEMP_PROJECT/Packages"

for asset_dir in "${ALL_LOCAL_ASSET_DIRS[@]}"; do
  rm -rf "$TEMP_PROJECT/Assets/$asset_dir"
  rm -f "$TEMP_PROJECT/Assets/$asset_dir.meta"
done

for asset_dir in "${LOCAL_ASSET_DIRS[@]}"; do
  ln -s "$MAIN_PROJECT/Assets/$asset_dir" "$TEMP_PROJECT/Assets/$asset_dir"
  cp -a "$MAIN_PROJECT/Assets/$asset_dir.meta" "$TEMP_PROJECT/Assets/$asset_dir.meta"
done

find "$TEMP_PROJECT/Packages" -maxdepth 1 -type l -name 'com.hpr.*' -delete 2>/dev/null || true
while IFS= read -r package_dir; do
  package_name=$(basename "$package_dir")
  ln -s "$package_dir" "$TEMP_PROJECT/Packages/$package_name"
done < <(find "$PACKAGE_ROOT" -maxdepth 1 -mindepth 1 -type d -name 'com.hpr.*' | sort)

find "$TEMP_PROJECT/Library" -maxdepth 1 \( -name '*lock*' -o -name '*.pid' \) -delete 2>/dev/null || true
rm -f "$TEMP_PROJECT/Temp/UnityLockfile" 2>/dev/null || true

echo "$TEMP_PROJECT"
