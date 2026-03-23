#!/usr/bin/env bash
set -euo pipefail
UNITY_VERSION="${UNITY_VERSION:-6000.4.0f1}"
UNITY_ROOT="${UNITY_ROOT:-/data/apps/Unity/Hub/Editor}"
UNITY_BIN="${UNITY_BIN:-$UNITY_ROOT/$UNITY_VERSION/Editor/Unity}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/data/src/github/games/unity}"
PROJECT_DIR="${PROJECT_DIR:-$WORKSPACE_ROOT/projects/fps_demo}"
PACKAGE_DIR="$WORKSPACE_ROOT/packages/com.hpr.foundation"
SRC_DIR="$(cd -- "$(dirname -- "$0")" && pwd)/Source"
BUILD_DIR="$PROJECT_DIR/Build/Linux"

if [[ ! -x "$UNITY_BIN" ]]; then
  echo "Unity editor not installed yet: $UNITY_BIN" >&2
  exit 1
fi

if [[ ! -d "$PROJECT_DIR/Assets" ]]; then
  mkdir -p "$(dirname "$PROJECT_DIR")"
  "$UNITY_BIN" -batchmode -nographics -quit -createProject "$PROJECT_DIR" -logFile -
fi

python3 - <<'PY' "$PROJECT_DIR/Packages/manifest.json"
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
obj = json.loads(p.read_text(encoding='utf-8'))
deps = obj.setdefault('dependencies', {})
deps['com.hpr.foundation'] = 'file:../../../packages/com.hpr.foundation'
deps['com.unity.ugui'] = '2.0.0'
p.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
PY

rm -rf "$PROJECT_DIR/Assets/Scripts" "$PROJECT_DIR/Assets/Editor"
mkdir -p "$PROJECT_DIR/Assets"
cp -R "$SRC_DIR/Scripts" "$PROJECT_DIR/Assets/"
cp -R "$SRC_DIR/Editor" "$PROJECT_DIR/Assets/"

"$UNITY_BIN" -batchmode -nographics -quit -projectPath "$PROJECT_DIR" -executeMethod SceneBootstrap.CreateScene -logFile -
mkdir -p "$BUILD_DIR"
"$UNITY_BIN" -batchmode -nographics -quit -projectPath "$PROJECT_DIR" -executeMethod SceneBootstrap.BuildLinux -logFile -

echo "Project ready: $PROJECT_DIR"
echo "Build output: $BUILD_DIR/FPSDemo.x86_64"
