#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
config_path="$script_dir/release_packages.json"
packages_root="$repo_root/unity/packages"
template_runner="$script_dir/HprPackageExportRunner.cs"
screenshot_runner="$script_dir/HprPackageScreenshotRunner.cs"
listing_generator="$script_dir/generate_sale_listing_drafts.py"
storefront_catalog="$script_dir/storefront_catalog.json"

unity_bin="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}"
work_root="${WORK_ROOT:-/data/tmp/hpr_assetstore_sale}"
projects_root="$work_root/projects"
artifacts_root="$work_root/artifacts"
dist_artifacts_root="${DIST_ARTIFACTS_ROOT:-$repo_root/dist/package_sale_artifacts}"
log_dir="${LOG_DIR:-$repo_root/doc/logs/package_sale_prep}"
report_path="${REPORT_PATH:-$repo_root/doc/package-sale-prep.md}"

mkdir -p "$projects_root" "$artifacts_root" "$dist_artifacts_root" "$log_dir"
if [[ "$(id -un)" != "hans" ]]; then
  chown -R hans:hans "$work_root"
  chown -R hans:hans "$log_dir"
  chown -R hans:hans "$dist_artifacts_root"
  chown hans:hans "$(dirname "$report_path")"
fi

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

if [[ $# -gt 0 ]]; then
  requested_packages=("$@")
else
  mapfile -t requested_packages < <(python3 - <<'PY' "$config_path"
import json, sys
config = json.loads(open(sys.argv[1], encoding='utf-8').read())
for entry in config["sellable_packages"]:
    print(entry["name"])
PY
  )
fi

mapfile -t package_specs < <(python3 - <<'PY' "$config_path" "$packages_root" "${requested_packages[@]}"
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
packages_root = Path(sys.argv[2])
requested = sys.argv[3:]
entry_map = {entry["name"]: entry for entry in config["sellable_packages"]}

if not requested:
    requested = [entry["name"] for entry in config["sellable_packages"]]

for name in requested:
    if name not in entry_map:
        raise SystemExit(f"requested package is not in the frozen sellable set: {name}")

def resolve(name: str):
    resolved = []
    seen = set()

    def visit(package_name: str):
        if package_name in seen:
            return
        seen.add(package_name)
        manifest = json.loads((packages_root / package_name / "package.json").read_text(encoding="utf-8"))
        for dep_name in manifest.get("dependencies", {}):
            if dep_name.startswith("com.hpr."):
                visit(dep_name)
        resolved.append(package_name)

    visit(name)
    return resolved

for name in requested:
    entry = entry_map[name]
    print(f"{name}|{entry['execute_method']}|{','.join(resolve(name))}")
PY
)

summary_lines=()
timestamp="$(date +%Y%m%d_%H%M%S)"

for spec in "${package_specs[@]}"; do
  package_name="${spec%%|*}"
  rest="${spec#*|}"
  execute_method="${rest%%|*}"
  resolved_csv="${rest#*|}"
  IFS=',' read -r -a resolved_packages <<<"$resolved_csv"

  project_name="sale_${package_name//./_}"
  project_path="$projects_root/$project_name"
  artifact_dir="$artifacts_root/$package_name"
  dist_artifact_dir="$dist_artifacts_root/$package_name"
  unitypackage_path="$artifact_dir/${package_name}.unitypackage"
  zip_path="$artifact_dir/${package_name}_upm.zip"
  info_path="$artifact_dir/${package_name}_info.txt"
  dist_unitypackage_path="$dist_artifact_dir/${package_name}.unitypackage"
  dist_zip_path="$dist_artifact_dir/${package_name}_upm.zip"
  dist_info_path="$dist_artifact_dir/${package_name}_info.txt"
  screenshot_dir="$artifact_dir/screenshots"
  dist_screenshot_dir="$dist_artifact_dir/screenshots"

  rm -rf "$artifact_dir" "$dist_artifact_dir"
  mkdir -p "$artifact_dir" "$dist_artifact_dir" "$screenshot_dir"
  if [[ "$(id -un)" != "hans" ]]; then
    chown -R hans:hans "$artifact_dir"
    chown -R hans:hans "$dist_artifact_dir"
  fi

  rm -rf "$project_path"

  validate_log="$log_dir/${timestamp}_${package_name//./_}_validate.log"
  if run_as_hans env \
      TEMP_ROOT="$projects_root" \
      PROJECT_NAME="$project_name" \
      LOG_DIR="$log_dir" \
      EXECUTE_METHOD="$execute_method" \
      RUN_TESTS=1 \
      bash "$repo_root/unity/tools/packages/validate_local_packages.sh" "$package_name" >"$validate_log" 2>&1; then
    :
  else
    echo "Validation failed for $package_name. See $validate_log" >&2
    tail -n 50 "$validate_log" >&2 || true
    exit 1
  fi

  run_as_hans python3 - <<'PY' "$project_path" "$packages_root" "$template_runner" "$screenshot_runner" "${resolved_packages[@]}"
from pathlib import Path
import shutil
import sys

project_path = Path(sys.argv[1])
packages_root = Path(sys.argv[2])
template_runner = Path(sys.argv[3])
screenshot_runner = Path(sys.argv[4])
resolved_packages = sys.argv[5:]

assets_dir = project_path / "Assets"
packages_dir = project_path / "Packages"
editor_dir = assets_dir / "Editor"
editor_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(template_runner, editor_dir / "HprPackageExportRunner.cs")
meta_template = template_runner.with_suffix(template_runner.suffix + ".meta")
if meta_template.exists():
    shutil.copy2(meta_template, editor_dir / "HprPackageExportRunner.cs.meta")
shutil.copy2(screenshot_runner, editor_dir / "HprPackageScreenshotRunner.cs")
screenshot_meta = screenshot_runner.with_suffix(screenshot_runner.suffix + ".meta")
if screenshot_meta.exists():
    shutil.copy2(screenshot_meta, editor_dir / "HprPackageScreenshotRunner.cs.meta")

for existing in assets_dir.glob("com.hpr.*"):
    if existing.is_dir():
        shutil.rmtree(existing)
    else:
        existing.unlink()
    meta = existing.with_suffix(existing.suffix + ".meta")
    if meta.exists():
        meta.unlink()

for package_name in resolved_packages:
    source = packages_root / package_name
    target = assets_dir / package_name
    shutil.copytree(source, target)

for existing in packages_dir.glob("com.hpr.*"):
    if existing.is_dir():
        shutil.rmtree(existing)
    elif existing.exists():
        existing.unlink()
PY

  refresh_log="$log_dir/${timestamp}_${package_name//./_}_refresh.log"
  if run_as_hans "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -logFile "$refresh_log" > /dev/null 2>&1; then
    :
  else
    echo "Refresh failed for $package_name. See $refresh_log" >&2
    tail -n 50 "$refresh_log" >&2 || true
    exit 1
  fi

  export_asset_paths=()
  for resolved_package in "${resolved_packages[@]}"; do
    export_asset_paths+=("Assets/${resolved_package}")
  done
  export_joined="$(IFS=';'; printf '%s' "${export_asset_paths[*]}")"
  export_log="$log_dir/${timestamp}_${package_name//./_}_export.log"

  if run_as_hans env \
      HPR_EXPORT_OUTPUT="$unitypackage_path" \
      HPR_EXPORT_ASSET_PATHS="$export_joined" \
      "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -executeMethod HprPackageExportRunner.ExportFromEnvironment -logFile "$export_log" > /dev/null 2>&1; then
    :
  else
    echo "Export failed for $package_name. See $export_log" >&2
    tail -n 50 "$export_log" >&2 || true
    exit 1
  fi

  if [[ ! -s "$unitypackage_path" ]]; then
    echo "Missing export artifact: $unitypackage_path" >&2
    exit 1
  fi

  screenshot_log="$log_dir/${timestamp}_${package_name//./_}_screenshot.log"

  if run_as_hans env \
      HPR_SCREENSHOT_PACKAGE="$package_name" \
      HPR_SCREENSHOT_OUTPUT_DIR="$screenshot_dir" \
      HPR_SCREENSHOT_WIDTH=1920 \
      HPR_SCREENSHOT_HEIGHT=1080 \
      "$unity_bin" -batchmode -quit -projectPath "$project_path" -executeMethod HPR.HprPackageScreenshotRunner.CapturePackageSetFromEnvironment -logFile "$screenshot_log" > /dev/null 2>&1; then
    :
  else
    echo "Screenshot capture failed for $package_name. See $screenshot_log" >&2
    tail -n 50 "$screenshot_log" >&2 || true
    exit 1
  fi

  for screenshot_name in 01_overview.png 02_workflow.png 03_details.png; do
    if [[ ! -s "$screenshot_dir/$screenshot_name" ]]; then
      echo "Missing screenshot artifact: $screenshot_dir/$screenshot_name" >&2
      exit 1
    fi
  done

  run_as_hans /data/bin/zip.sh "$packages_root/$package_name" "$zip_path" >/dev/null
  cp "$unitypackage_path" "$dist_unitypackage_path"
  cp "$zip_path" "$dist_zip_path"
  cp -R "$screenshot_dir" "$dist_artifact_dir/"

  {
    echo "package: $package_name"
    echo "project: $project_path"
    echo "unitypackage: $unitypackage_path"
    echo "unitypackage_size_bytes: $(stat -c %s "$unitypackage_path")"
    echo "upm_zip: $zip_path"
    echo "upm_zip_size_bytes: $(stat -c %s "$zip_path")"
    echo "resolved_packages: ${resolved_packages[*]}"
    echo "validator_method: $execute_method"
    echo "validate_log: $validate_log"
    echo "refresh_log: $refresh_log"
    echo "export_log: $export_log"
    echo "screenshots:"
    echo "  - $screenshot_dir/01_overview.png"
    echo "  - $screenshot_dir/02_workflow.png"
    echo "  - $screenshot_dir/03_details.png"
    echo "tracked_screenshots:"
    echo "  - $dist_screenshot_dir/01_overview.png"
    echo "  - $dist_screenshot_dir/02_workflow.png"
    echo "  - $dist_screenshot_dir/03_details.png"
    echo "screenshot_log: $screenshot_log"
  } >"$info_path"
  cp "$info_path" "$dist_info_path"

  summary_lines+=("- \`$package_name\`: project \`$project_path\`, unitypackage \`$dist_unitypackage_path\`, zip \`$dist_zip_path\`, dependencies \`${resolved_packages[*]}\`")
done

bash "$script_dir/run_official_asset_store_validator.sh" "${requested_packages[@]}"
python3 "$listing_generator" "$repo_root" "$config_path" "$dist_artifacts_root" "$storefront_catalog"

cat >"$report_path" <<EOF
# Package Sale Preparation

Generated on $(date --iso-8601=seconds)

## Prepared sellable packages
$(printf '%s\n' "${summary_lines[@]}")

## Artifact root
- \`$artifacts_root\`

## Tracked artifact root
- \`$dist_artifacts_root\`
- each package directory now contains the exported \`.unitypackage\`, UPM zip, three storefront screenshots, info file, and listing draft markdown

## Project root
- \`$projects_root\`

## Official Asset Store Tools validation
- Command: \`unity/tools/release/run_official_asset_store_validator.sh\`
- Logs: \`$repo_root/doc/logs/asset_store_tools_validation\`

## Human-only steps left
- See \`doc/human-only-final-steps.md\`.

## Not prepared for sale
- Packages outside the frozen sellable set in \`unity/tools/release/release_packages.json\` remain excluded for engineering reasons and are not included in these artifacts.
EOF

echo "Prepared sale artifacts:"
printf ' - %s\n' "${requested_packages[@]}"
echo "Projects: $projects_root"
echo "Artifacts: $artifacts_root"
echo "Report: $report_path"
