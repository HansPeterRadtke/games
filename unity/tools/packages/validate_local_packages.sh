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
project_name="${PROJECT_NAME:-}"
log_dir="${LOG_DIR:-$repo_root/doc/logs/package_validation}"
mkdir -p "$temp_root" "$log_dir"

if [[ ! -x "$unity_bin" ]]; then
  echo "Unity editor not found: $unity_bin" >&2
  exit 1
fi

requested=("$@")
if [[ -z "$project_name" ]]; then
  sanitized_packages=$(printf '%s_' "${requested[@]}" | tr -c '[:alnum:]_-' '_')
  project_name="clean_package_project_${sanitized_packages}_$$"
fi
project_path="$temp_root/$project_name"

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
    shutil.copytree(source, target)
PY

log_file="$log_dir/$(date +%Y%m%d_%H%M%S)_$(printf '%s_' "${requested[@]}" | tr '/.' '__').log"
execute_method="${EXECUTE_METHOD:-}"
execute_log_file=""

run_editor() {
  "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -logFile "$log_file"
}

run_execute_method() {
  execute_log_file="${log_dir}/$(date +%Y%m%d_%H%M%S)_$(printf '%s_' "${requested[@]}" | tr '/.' '__')_${execute_method##*.}.log"
  "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -executeMethod "$execute_method" -logFile "$execute_log_file"
}

if [[ "$(id -un)" == "hans" ]]; then
  run_editor
  if [[ -n "$execute_method" ]]; then
    run_execute_method
  fi
else
  exec runuser -u hans -- env \
    HOME=/home/hans USER=hans LOGNAME=hans \
    DISPLAY="${DISPLAY:-:1}" \
    XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}" \
    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
    DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}" \
    UNITY_BIN="$unity_bin" TEMP_ROOT="$temp_root" PROJECT_NAME="$project_name" LOG_DIR="$log_dir" EXECUTE_METHOD="$execute_method" \
    bash "$0" "$@"
fi

if rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$log_file" >/dev/null 2>&1; then
  echo "Validation failed. See log: $log_file" >&2
  rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$log_file" >&2 || true
  exit 1
fi

if [[ -n "$execute_method" && -n "$execute_log_file" ]]; then
  if rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$execute_log_file" >/dev/null 2>&1; then
    echo "Validation failed during execute method. See log: $execute_log_file" >&2
    rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$execute_log_file" >&2 || true
    exit 1
  fi
fi

echo "Validated packages:"
printf ' - %s\n' "${resolved_packages[@]}"
echo "Log: $log_file"
if [[ -n "$execute_method" && -n "$execute_log_file" ]]; then
  echo "Execute log: $execute_log_file"
fi
