#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: validate_local_packages.sh <com.hpr.package> [more packages...]" >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
packages_root="$repo_root/unity/packages"
unity_bin="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}"
temp_root="${TEMP_ROOT:-/data/tmp/hpr_package_validation}"
project_name="${PROJECT_NAME:-clean_package_project}"
project_path="$temp_root/$project_name"
log_dir="${LOG_DIR:-$repo_root/doc/logs/package_validation}"
mkdir -p "$temp_root" "$log_dir"

if [[ ! -x "$unity_bin" ]]; then
  echo "Unity editor not found: $unity_bin" >&2
  exit 1
fi

requested=("$@")
package_list=$(python3 - <<'PY' "$packages_root" "${requested[@]}"
import json, sys
from pathlib import Path

packages_root = Path(sys.argv[1])
requested = sys.argv[2:]
resolved = []
seen = set()

def visit(name):
    if name in seen:
        return
    seen.add(name)
    pkg_dir = packages_root / name
    if not pkg_dir.exists():
        raise SystemExit(f"missing package: {name}")
    manifest = json.loads((pkg_dir / "package.json").read_text())
    for dep_name, dep_value in manifest.get("dependencies", {}).items():
        if dep_name.startswith("com.hpr."):
            visit(dep_name)
    resolved.append(name)

for name in requested:
    visit(name)

print("\n".join(resolved))
PY
)

mapfile -t resolved_packages <<<"$package_list"

if [[ ! -d "$project_path/Assets" ]]; then
  "$unity_bin" -batchmode -nographics -quit -createProject "$project_path" -logFile -
fi

python3 - <<'PY' "$project_path/Packages/manifest.json"
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

python3 - <<'PY' "$project_path/Packages" "$packages_root" "${resolved_packages[@]}"
from pathlib import Path
import os
import shutil
import sys

packages_dir = Path(sys.argv[1])
packages_root = Path(sys.argv[2])
package_names = sys.argv[3:]

for target in packages_dir.glob("com.hpr.*"):
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

for name in package_names:
    source = packages_root / name
    target = packages_dir / name
    relative_source = Path(os.path.relpath(source, packages_dir))
    target.symlink_to(relative_source)
PY

log_file="$log_dir/$(date +%Y%m%d_%H%M%S)_$(printf '%s_' "${requested[@]}" | tr '/.' '__').log"

run_editor() {
  "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -logFile "$log_file"
}

if [[ "$(id -un)" == "hans" ]]; then
  run_editor
else
  sudo -u hans -H env \
    HOME=/home/hans USER=hans LOGNAME=hans \
    DISPLAY="${DISPLAY:-:1}" \
    XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}" \
    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
    DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}" \
    bash -lc "$(printf '%q ' "$unity_bin") -batchmode -nographics -quit -projectPath $(printf '%q' "$project_path") -logFile $(printf '%q' "$log_file")"
fi

if rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$log_file" >/dev/null 2>&1; then
  echo "Validation failed. See log: $log_file" >&2
  rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$log_file" >&2 || true
  exit 1
fi

echo "Validated packages:"
printf ' - %s\n' "${resolved_packages[@]}"
echo "Log: $log_file"
