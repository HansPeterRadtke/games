#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
projects_root="${PROJECTS_ROOT:-/data/tmp/hpr_assetstore_sale/projects}"
unity_bin="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}"
log_dir="${LOG_DIR:-$repo_root/doc/logs/asset_store_tools_upload}"
runner_template="$script_dir/HprAssetStoreUploaderRunner.cs"
credential_file="${HPR_UPLOAD_CREDENTIAL_FILE:-/data/infra/secrets/unity3d.txt}"
expected_login="${HPR_UPLOAD_EXPECTED_LOGIN:-}"
timeout_s="${HPR_UPLOAD_TIMEOUT_S:-600}"
execute=0
portal_id=""
display_name=""
package_name=""

usage() {
  cat <<'EOF'
Usage:
  upload_asset_store_package.sh [--execute] --portal-id ID --name DISPLAY_NAME [options] PACKAGE_NAME

Options:
  --execute                 Perform a real upload. Default is dry-run/status inspection.
  --portal-id ID            Publisher Portal package/version id to match exactly.
  --name DISPLAY_NAME       Exact Publisher Portal package name.
  --credential-file PATH    Local Unity credential file. Default: /data/infra/secrets/unity3d.txt
  --expected-login EMAIL    Require the local credential file to contain this Unity login.
  --timeout-seconds N       Unity process timeout. Default: 600.
  -h, --help                Show this help.

Environment overrides:
  UNITY_BIN, PROJECTS_ROOT, LOG_DIR, HPR_UPLOAD_CREDENTIAL_FILE,
  HPR_UPLOAD_EXPECTED_LOGIN, HPR_UPLOAD_TIMEOUT_S

The credential file is read only inside Unity. Its contents are never placed in command arguments
or output. Cloud authentication is preferred when available; otherwise the local credential file
is used. Real upload is allowed only when the matched Publisher Portal status is exactly 'draft'.
EOF
}

while (($#)); do
  case "$1" in
    --execute)
      execute=1
      shift
      ;;
    --portal-id)
      [[ $# -ge 2 ]] || { echo "Missing value for --portal-id" >&2; exit 2; }
      portal_id="$2"
      shift 2
      ;;
    --name)
      [[ $# -ge 2 ]] || { echo "Missing value for --name" >&2; exit 2; }
      display_name="$2"
      shift 2
      ;;
    --credential-file)
      [[ $# -ge 2 ]] || { echo "Missing value for --credential-file" >&2; exit 2; }
      credential_file="$2"
      shift 2
      ;;
    --expected-login)
      [[ $# -ge 2 ]] || { echo "Missing value for --expected-login" >&2; exit 2; }
      expected_login="$2"
      shift 2
      ;;
    --timeout-seconds)
      [[ $# -ge 2 ]] || { echo "Missing value for --timeout-seconds" >&2; exit 2; }
      timeout_s="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$package_name" ]]; then
        echo "Only one PACKAGE_NAME may be supplied" >&2
        exit 2
      fi
      package_name="$1"
      shift
      ;;
  esac
done

[[ -n "$package_name" ]] || { echo "PACKAGE_NAME is required" >&2; usage >&2; exit 2; }
[[ -n "$portal_id" ]] || { echo "--portal-id is required" >&2; exit 2; }
[[ -n "$display_name" ]] || { echo "--name is required" >&2; exit 2; }
[[ "$timeout_s" =~ ^[1-9][0-9]*$ ]] || { echo "--timeout-seconds must be a positive integer" >&2; exit 2; }
[[ -x "$unity_bin" ]] || { echo "Unity editor not found: $unity_bin" >&2; exit 1; }
[[ -f "$runner_template" ]] || { echo "Uploader runner template not found: $runner_template" >&2; exit 1; }

project_name="sale_${package_name//./_}"
project_path="$projects_root/$project_name"
package_path="$repo_root/dist/package_sale_artifacts/$package_name/$package_name.unitypackage"
[[ -d "$project_path" ]] || { echo "Sale project not found: $project_path" >&2; exit 1; }
[[ -f "$package_path" ]] || { echo "Unity package not found: $package_path" >&2; exit 1; }

if [[ -e "$project_path/Temp/UnityLockfile" ]]; then
  if fuser "$project_path/Temp/UnityLockfile" >/dev/null 2>&1; then
    echo "Sale project is already open in another Unity process: $project_path" >&2
    fuser -v "$project_path/Temp/UnityLockfile" >&2 || true
    exit 1
  fi
  rm -f "$project_path/Temp/UnityLockfile"
fi

if [[ ! -f "$credential_file" ]]; then
  echo "Unity credential file not found: $credential_file" >&2
  exit 1
fi

mkdir -p "$project_path/Assets/Editor" "$log_dir"
cp "$runner_template" "$project_path/Assets/Editor/HprAssetStoreUploaderRunner.cs"

timestamp=$(date +%Y%m%d_%H%M%S)
safe_name=${package_name//./_}
mode=dry_run
(( execute )) && mode=upload
result_path="$log_dir/${timestamp}_${safe_name}_${mode}_result.txt"
unity_log="$log_dir/${timestamp}_${safe_name}_${mode}.log"

runtime_env=(
  HOME=/home/hans USER=hans LOGNAME=hans
  DISPLAY="${DISPLAY:-:1}"
  XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}"
  XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"
  DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}"
  HPR_UPLOAD_RESULT="$result_path"
  HPR_UPLOAD_PACKAGE_PATH="$package_path"
  HPR_UPLOAD_EXPECTED_NAME="$display_name"
  HPR_UPLOAD_PORTAL_ID="$portal_id"
  HPR_UPLOAD_EXECUTE="$execute"
  HPR_UPLOAD_CREDENTIAL_FILE="$credential_file"
  HPR_UPLOAD_EXPECTED_LOGIN="$expected_login"
)

run_unity() {
  env "${runtime_env[@]}" timeout "$timeout_s" \
    "$unity_bin" -batchmode -nographics \
    -projectPath "$project_path" \
    -executeMethod HprAssetStoreUploaderRunner.RunFromEnvironment \
    -logFile "$unity_log"
}

set +e
if [[ "$(id -un)" == "hans" ]]; then
  run_unity >/dev/null 2>&1
  rc=$?
else
  runuser -u hans -- env "${runtime_env[@]}" timeout "$timeout_s" \
    "$unity_bin" -batchmode -nographics \
    -projectPath "$project_path" \
    -executeMethod HprAssetStoreUploaderRunner.RunFromEnvironment \
    -logFile "$unity_log" >/dev/null 2>&1
  rc=$?
fi
set -e

if [[ -f "$result_path" ]]; then
  cat "$result_path"
else
  echo "No uploader result file was produced." >&2
fi

echo "result_file=$result_path"
echo "unity_log=$unity_log"

if (( rc == 124 )); then
  echo "Unity upload command timed out after ${timeout_s}s" >&2
  exit 124
fi
exit "$rc"
