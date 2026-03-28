#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $(basename "$0") <repo-path-or-subfolder> [output-zip]" >&2
  exit 1
fi

selection_input=$1
selection_root=$(python3 - <<'PY2' "$selection_input"
import os, sys
print(os.path.abspath(sys.argv[1]))
PY2
)

if [[ ! -d "$selection_root" ]]; then
  echo "Not a directory: $selection_input" >&2
  exit 1
fi

repo_root=$(git -C "$selection_root" rev-parse --show-toplevel 2>/dev/null) || {
  echo "Not inside a git repository: $selection_input" >&2
  exit 1
}

if [[ $# -eq 2 ]]; then
  output_path=$2
else
  output_path="$(dirname "$selection_root")/$(basename "$selection_root")_tracked.zip"
fi

output_path=$(python3 - <<'PY2' "$output_path"
import os, sys
print(os.path.abspath(sys.argv[1]))
PY2
)

mkdir -p "$(dirname "$output_path")"

python3 - <<'PY2' "$repo_root" "$selection_root" "$output_path"
import os
import subprocess
import sys
import zipfile
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
selection_root = Path(sys.argv[2]).resolve()
output_path = Path(sys.argv[3]).resolve()

try:
    common = Path(os.path.commonpath([str(repo_root), str(selection_root)]))
except ValueError:
    raise SystemExit(f"Selection is not inside repository: {selection_root}")
if common != repo_root:
    raise SystemExit(f"Selection is not inside repository: {selection_root}")

selection_rel = os.path.relpath(selection_root, repo_root)
if selection_rel == '.':
    selection_rel = ''

tracked = subprocess.run(
    ['git', '-C', str(repo_root), 'ls-files', '-z'],
    check=True,
    stdout=subprocess.PIPE,
).stdout.decode('utf-8', 'surrogateescape').split('\0')

selected = []
for rel_path in tracked:
    if not rel_path:
        continue
    if selection_rel and rel_path != selection_rel and not rel_path.startswith(selection_rel + os.sep):
        continue
    abs_path = repo_root / rel_path
    if not abs_path.is_file():
        continue
    arcname = rel_path if not selection_rel else os.path.relpath(rel_path, selection_rel)
    selected.append((abs_path, arcname))

if not selected:
    raise SystemExit(f"No tracked files under: {selection_root}")

with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for abs_path, arcname in selected:
        archive.write(abs_path, arcname=arcname)

print(output_path)
PY2
