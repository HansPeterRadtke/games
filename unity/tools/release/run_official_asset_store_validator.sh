#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
config_path="$script_dir/release_packages.json"
template_runner="$script_dir/HprAssetStoreToolsValidatorRunner.cs"
ast_repo="${AST_REPO:-/data/src/external/com.unity.asset-store-tools}"
ast_package_dir="$ast_repo/com.unity.asset-store-tools"
projects_root="${PROJECTS_ROOT:-/data/tmp/hpr_assetstore_sale/projects}"
unity_bin="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}"
log_dir="${LOG_DIR:-$repo_root/doc/logs/asset_store_tools_validation}"

mkdir -p "$log_dir"

if [[ ! -x "$unity_bin" ]]; then
  echo "Unity editor not found: $unity_bin" >&2
  exit 1
fi

run_as_hans() {
  if [[ "$(id -un)" == "hans" ]]; then
    "$@"
  else
    runuser -u hans -- env \
      HOME=/home/hans USER=hans LOGNAME=hans \
      DISPLAY="${DISPLAY:-:1}" \
      XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}" \
      XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
      DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}" \
      "$@"
  fi
}

ensure_ast_tools() {
  if [[ ! -d "$ast_repo/.git" ]]; then
    git clone --depth 1 https://github.com/Unity-Technologies/com.unity.asset-store-tools.git "$ast_repo"
  else
    git -C "$ast_repo" pull --ff-only
  fi

  if [[ ! -d "$ast_package_dir" ]]; then
    echo "Missing official Asset Store Tools package dir: $ast_package_dir" >&2
    exit 1
  fi

  python3 - <<'PY' "$ast_package_dir/Editor/Exporter/Abstractions/PackageExporterBase.cs"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
text = text.replace('return GUID.Generate().ToString();', 'return Guid.NewGuid().ToString("N");')
text = text.replace('return UnityEditor.GUID.Generate().ToString();', 'return Guid.NewGuid().ToString("N");')
path.write_text(text, encoding='utf-8')
PY
}

resolve_packages() {
  python3 - <<'PY' "$config_path" "$repo_root/unity/packages" "$1"
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
packages_root = Path(sys.argv[2])
target = sys.argv[3]
entries = {entry["name"]: entry for entry in config["sellable_packages"]}
if target not in entries:
    raise SystemExit(f"package is not in frozen sellable set: {target}")

resolved = []
seen = set()

def visit(name: str) -> None:
    if name in seen:
        return
    seen.add(name)
    manifest = json.loads((packages_root / name / "package.json").read_text(encoding="utf-8"))
    for dep_name in manifest.get("dependencies", {}):
        if dep_name.startswith("com.hpr."):
            visit(dep_name)
    resolved.append(name)

visit(target)
print(";".join(f"Assets/{name}" for name in resolved))
PY
}

mapfile -t requested_packages < <(python3 - <<'PY' "$config_path" "$@"
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
requested = sys.argv[2:]
allowed = {entry["name"] for entry in config["sellable_packages"]}
if requested:
    for package in requested:
        if package not in allowed:
            raise SystemExit(f"package is not in frozen sellable set: {package}")
    packages = requested
else:
    packages = [entry["name"] for entry in config["sellable_packages"]]
for package in packages:
    print(package)
PY
)

ensure_ast_tools
timestamp="$(date +%Y%m%d_%H%M%S)"

for package_name in "${requested_packages[@]}"; do
  project_name="sale_${package_name//./_}"
  project_path="$projects_root/$project_name"
  if [[ ! -d "$project_path" ]]; then
    echo "Sale project not found: $project_path" >&2
    echo "Run unity/tools/release/prepare_sale_packages.sh first." >&2
    exit 1
  fi

  python3 - <<'PY' "$project_path/Packages/manifest.json" "$ast_package_dir"
from pathlib import Path
import json
import sys

manifest_path = Path(sys.argv[1])
ast_package_dir = Path(sys.argv[2])
data = json.loads(manifest_path.read_text(encoding='utf-8'))
deps = data.setdefault("dependencies", {})
deps["com.unity.asset-store-tools"] = f"file:{ast_package_dir}"
manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding='utf-8')
PY

  mkdir -p "$project_path/Assets/Editor"
  cp "$template_runner" "$project_path/Assets/Editor/HprAssetStoreToolsValidatorRunner.cs"

  validate_paths="$(resolve_packages "$package_name")"
  unity_log="$log_dir/${timestamp}_${package_name//./_}_asset_store_tools.log"
  results_path="$log_dir/${timestamp}_${package_name//./_}_asset_store_tools_results.txt"

  if run_as_hans env \
      HPR_AST_RESULTS="$results_path" \
      HPR_AST_PATHS="$validate_paths" \
      "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" \
      -executeMethod HprAssetStoreToolsValidatorRunner.ValidateFromEnvironment \
      -logFile "$unity_log" > /dev/null 2>&1; then
    echo "PASS $package_name -> $unity_log"
  else
    echo "FAIL $package_name -> $unity_log" >&2
    tail -n 80 "$unity_log" >&2 || true
    exit 1
  fi
done

echo "official asset store validation: OK"
