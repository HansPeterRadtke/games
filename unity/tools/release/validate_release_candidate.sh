#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
config_path="$script_dir/release_packages.json"

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

run_as_hans python3 "$repo_root/unity/tools/release/release_audit.py"
run_as_hans python3 "$repo_root/unity/tools/architecture/dependency_audit.py"
run_as_hans bash "$repo_root/unity/tools/architecture/run_phase1_headless_validation.sh"

for entry in "${package_entries[@]}"; do
  package_name=${entry%%|*}
  execute_method=${entry#*|}
  run_as_hans env EXECUTE_METHOD="$execute_method" bash "$repo_root/unity/tools/packages/validate_local_packages.sh" "$package_name"
done

for combo in "${package_combinations[@]}"; do
  IFS='|' read -r -a combo_packages <<<"$combo"
  run_as_hans bash "$repo_root/unity/tools/packages/validate_local_packages.sh" "${combo_packages[@]}"
done
run_as_hans bash "$repo_root/unity/tools/fps_demo/run_unity_batch.sh" SceneBootstrap.BuildLinux
run_as_hans env NO_NOTICE=1 bash "$repo_root/unity/tools/fps_demo/smoke_test.sh"

echo "release candidate validation: OK"
