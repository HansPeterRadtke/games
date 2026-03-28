#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
config_path="$script_dir/release_packages.json"
log_dir="${LOG_DIR:-$repo_root/doc/logs}"
mkdir -p "$log_dir"
timestamp="$(date +%Y%m%d_%H%M%S)"

mapfile -t package_entries < <(python3 - <<'PY' "$config_path"
import json, sys
config = json.loads(open(sys.argv[1], encoding='utf-8').read())
for entry in config["sellable_packages"]:
    print(f"{entry['name']}|{entry['execute_method']}")
PY
)

mapfile -t package_combinations < <(python3 - <<'PY' "$config_path"
import json, sys
config = json.loads(open(sys.argv[1], encoding='utf-8').read())
for combo in config.get("package_combinations", []):
    print("|".join(combo))
PY
)

run_as_hans() {
  if [[ "$(id -un)" == "hans" ]]; then
    "$@"
  else
    runuser -u hans -- "$@"
  fi
}

run_logged() {
  local name="$1"
  shift
  local log_file="$log_dir/${timestamp}_${name}.log"
  if run_as_hans "$@" >"$log_file" 2>&1; then
    echo "PASS $name -> $log_file"
  else
    echo "FAIL $name -> $log_file" >&2
    tail -n 50 "$log_file" >&2 || true
    exit 1
  fi
}

run_logged release_audit python3 "$repo_root/unity/tools/release/release_audit.py"
run_logged dependency_audit python3 "$repo_root/unity/tools/architecture/dependency_audit.py"
run_logged headless_phase1_validation bash "$repo_root/unity/tools/architecture/run_phase1_headless_validation.sh"

for entry in "${package_entries[@]}"; do
  package_name=${entry%%|*}
  execute_method=${entry#*|}
  run_logged "package_${package_name//./_}" env EXECUTE_METHOD="$execute_method" bash "$repo_root/unity/tools/packages/validate_local_packages.sh" "$package_name"
done

for combo in "${package_combinations[@]}"; do
  IFS='|' read -r -a combo_packages <<<"$combo"
  combo_name="$(printf '%s_' "${combo_packages[@]}" | tr '.-' '__')"
  run_logged "combo_${combo_name%_}" bash "$repo_root/unity/tools/packages/validate_local_packages.sh" "${combo_packages[@]}"
done
run_logged game_build bash "$repo_root/unity/tools/fps_demo/run_unity_batch.sh" SceneBootstrap.BuildLinux
run_logged game_smoke env NO_NOTICE=1 bash "$repo_root/unity/tools/fps_demo/smoke_test.sh"

echo "release candidate validation: OK"
