#!/usr/bin/env bash
set -euo pipefail
UNITY_VERSION="${UNITY_VERSION:-6000.4.0f1}"
UNITY_ROOT="${UNITY_ROOT:-/data/apps/Unity/Hub/Editor}"
UNITY_BIN="${UNITY_BIN:-$UNITY_ROOT/$UNITY_VERSION/Editor/Unity}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/data/src/github/games/unity}"
PROJECT_DIR="${PROJECT_DIR:-$WORKSPACE_ROOT/projects/fps_demo}"
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
deps['com.unity.ugui'] = '2.0.0'
for name in list(deps):
    if name.startswith('com.hpr.'):
        deps.pop(name, None)
p.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
PY

python3 - <<'PY' "$PROJECT_DIR/Packages" "$WORKSPACE_ROOT/packages"
from pathlib import Path
import os
import shutil
import sys

packages_dir = Path(sys.argv[1])
shared_packages = Path(sys.argv[2])
package_names = sorted(path.name for path in shared_packages.iterdir() if path.is_dir() and path.name.startswith("com.hpr."))
for name in package_names:
    source = shared_packages / name
    target = packages_dir / name
    relative_source = Path(os.path.relpath(source, packages_dir))
    if target.is_symlink() or target.exists():
        if target.is_symlink() and (packages_dir / Path(os.readlink(target))).resolve() == source.resolve():
            continue
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    target.symlink_to(relative_source)
PY

"$UNITY_BIN" -batchmode -nographics -quit -projectPath "$PROJECT_DIR" -executeMethod HPR.SceneBootstrap.EnsureProjectSetup -logFile -
mkdir -p "$BUILD_DIR"
"$UNITY_BIN" -batchmode -nographics -quit -projectPath "$PROJECT_DIR" -executeMethod HPR.SceneBootstrap.BuildLinux -logFile -

echo "Project ready: $PROJECT_DIR"
echo "Build output: $BUILD_DIR/FPSDemo.x86_64"
