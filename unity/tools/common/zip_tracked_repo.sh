#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: zip_tracked_repo.sh <repo-path> [output-zip]" >&2
  exit 1
fi

repo_input=$1
repo_root=$(git -C "$repo_input" rev-parse --show-toplevel 2>/dev/null) || {
  echo "Not a git repository: $repo_input" >&2
  exit 1
}

output_path=${2:-"$(dirname "$repo_root")/$(basename "$repo_root")_tracked.zip"}
output_path=$(python3 - <<'PY' "$output_path"
import os, sys
print(os.path.abspath(sys.argv[1]))
PY
)

mkdir -p "$(dirname "$output_path")"

python3 - <<'PY' "$repo_root" "$output_path"
import os
import subprocess
import sys
import zipfile

repo_root, output_path = sys.argv[1:3]
tracked = subprocess.run(
    ["git", "-C", repo_root, "ls-files", "-z"],
    check=True,
    stdout=subprocess.PIPE,
).stdout.decode("utf-8", "surrogateescape").split("\0")

with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for rel_path in tracked:
        if not rel_path:
            continue
        abs_path = os.path.join(repo_root, rel_path)
        if os.path.isfile(abs_path):
            archive.write(abs_path, arcname=rel_path)

print(output_path)
PY
