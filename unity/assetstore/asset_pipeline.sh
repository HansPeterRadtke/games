#!/usr/bin/env bash
set -euo pipefail

ROOT=/data/src/github/games
PY=/data/venv/bin/python
RUNNER=$ROOT/unity/tools/assetstore/unity_native_asset.py
UNITY=/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity
PROJECT=$ROOT/unity/projects/fps_demo
BUILD_DIR=$PROJECT/Build/Linux
LOG_DIR=$ROOT/unity/assetstore/logs
STATE_DIR=$ROOT/unity/assetstore/metadata/pipeline

export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export XDG_RUNTIME_DIR=/run/user/1000

mkdir -p "$LOG_DIR" "$STATE_DIR"

log() {
  printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"
}

meta_path() {
  echo "$STATE_DIR/meta_$1.json"
}

fetch_meta() {
  local package_id="$1"
  local path
  path=$(meta_path "$package_id")
  if [[ ! -s "$path" ]]; then
    sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
      "$PY" "$RUNNER" metadata "$package_id" >"$path"
  fi
  echo "$path"
}

meta_field() {
  local meta_file="$1"
  local field="$2"
  python3 - "$meta_file" "$field" <<'PY'
import json, sys
meta = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
value = meta[sys.argv[2]]
print(value)
PY
}

is_valid_unitypackage() {
  local path="$1"
  [[ -f "$path" ]] || return 1
  python3 - "$path" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
data = p.read_bytes()[:2] if p.exists() and p.stat().st_size >= 2 else b''
raise SystemExit(0 if data == b'\x1f\x8b' else 1)
PY
}

wait_for_valid_package() {
  local path="$1"
  while ! is_valid_unitypackage "$path"; do
    sleep 20
  done
}

run_unity_method() {
  local log_name="$1"
  local method="$2"
  shift 2
  local args=()
  local quoted=()
  for arg in "$@"; do
    quoted+=("$(printf '%q' "$arg")")
  done
  local args_str="${quoted[*]}"
  sudo -u hans -H env UNITY="$UNITY" PROJECT="$PROJECT" LOG="$LOG_DIR/$log_name" \
    bash -lc "\"\$UNITY\" -batchmode -nographics -projectPath \"\$PROJECT\" -executeMethod $method $args_str -quit -logFile \"\$LOG\""
}

build_and_smoke() {
  local label="$1"
  run_unity_method "build_${label}.log" SceneBootstrap.BuildLinux
  sudo -u hans -H env DISPLAY=:1 XAUTHORITY=/home/hans/.Xauthority XDG_RUNTIME_DIR=/run/user/1000 \
    bash -lc "cd '$BUILD_DIR' && timeout 60 ./FPSDemo.x86_64 -logFile '$LOG_DIR/smoke_${label}.log' -smoketest"
}

import_package_once() {
  local package_id="$1"
  local package_path="$2"
  local marker="$STATE_DIR/imported_${package_id}.done"
  if [[ -f "$marker" ]]; then
    return 0
  fi

  log "Importing package $package_id from $package_path"
  sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    "$PY" "$RUNNER" import "$package_path"
  touch "$marker"
}

catalog_if_present() {
  local label="$1"
  local asset_folder="$2"
  if [[ -z "$asset_folder" ]]; then
    return 0
  fi
  local folder_path="$PROJECT/${asset_folder#Assets/}"
  if [[ ! -d "$folder_path" ]]; then
    log "Skipping catalog for missing folder $asset_folder"
    return 0
  fi
  run_unity_method "catalog_${label}.log" PrefabCatalogReporter.ReportPrefabCatalogFromArgs -assetFolder "$asset_folder"
}

integrate_group() {
  local label="$1"
  local method="$2"
  if [[ -z "$method" ]]; then
    build_and_smoke "$label"
    return 0
  fi
  run_unity_method "apply_${label}.log" "$method"
  build_and_smoke "$label"
}

download_if_needed() {
  local package_id="$1"
  local final_path="$2"
  if is_valid_unitypackage "$final_path"; then
    log "Package $package_id already downloaded"
    return 0
  fi

  log "Downloading package $package_id"
  sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    "$PY" "$RUNNER" download "$package_id" --timeout 3600 --stall-timeout 300
}

process_package() {
  local package_id="$1"
  local asset_folder="$2"
  local integration_label="$3"
  local integration_method="$4"

  local meta_file
  meta_file=$(fetch_meta "$package_id")
  local final_path display_name
  final_path=$(meta_field "$meta_file" final_path)
  display_name=$(meta_field "$meta_file" display_name)

  download_if_needed "$package_id" "$final_path"
  wait_for_valid_package "$final_path"
  import_package_once "$package_id" "$final_path"
  catalog_if_present "$integration_label" "$asset_folder"
  integrate_group "$integration_label" "$integration_method"
  log "Processed $package_id - $display_name"
}

main() {
  local furniture_meta furniture_path
  furniture_meta=$(fetch_meta 330002)
  furniture_path=$(meta_field "$furniture_meta" final_path)

  log "Waiting for the active furniture download to finish"
  wait_for_valid_package "$furniture_path"
  process_package 330002 "Assets/Furniture Mega Pack - Free" furniture ThirdPartyAssetIntegrator.ApplyFurniturePackFromBatch

  process_package 151980 "Assets/Low Poly Weapons VOL.1" weapons ThirdPartyAssetIntegrator.ApplyWeaponPackFromBatch
  process_package 258782 "Assets/House Interior - Free" house ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 71426 "Assets/Furnished Cabin" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 124055 "Assets/Apartment Kit" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 107224 "Assets/CITY package" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 326131 "Assets/npc_casual_set_00" characters ThirdPartyAssetIntegrator.ApplyCharacterPacksFromBatch
  process_package 181470 "Assets/Survivalist character" characters ThirdPartyAssetIntegrator.ApplyCharacterPacksFromBatch
  process_package 157920 "Assets/Human Crafting Animations FREE" animations ""
  process_package 288783 "Assets/RPG_Animations_Pack_FREE" animations ""
  process_package 52977 "Assets/Nature Starter Kit 2" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 138810 "Assets/Grass Flowers Pack Free" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 279940 "Assets/Realistic Terrain Textures FREE" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 48529 "Assets/Flooded Grounds" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 213197 "Assets/Unity Terrain - URP Demo Scene" environment ThirdPartyAssetIntegrator.ApplyHousePackFromBatch
  process_package 267961 "Assets/Starter Assets" starter_assets ""
}

main "$@"
