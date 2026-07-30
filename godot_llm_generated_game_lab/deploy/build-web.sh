#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
[[ $(hostname -s) == nitro ]] || { echo 'build-web.sh is Nitro-only' >&2; exit 1; }
if [[ -d "$ROOT/web" ]]; then touch "$ROOT/web/.gdignore"; chmod 0644 "$ROOT/web/.gdignore"; fi
"$ROOT/tests/run_all.sh"
GODOT_WEB_BIN=${GODOT_WEB_BIN:-/data/src/external/godot/4.6.1-stable/standard/Godot_v4.6.1-stable_linux.x86_64}
[[ -x "$GODOT_WEB_BIN" ]] || { echo "missing standard Godot web exporter: $GODOT_WEB_BIN" >&2; exit 1; }
[[ $($GODOT_WEB_BIN --version) == 4.6.1.stable.official.14d19694e ]] || { echo "unexpected standard Godot version" >&2; exit 1; }
stage=$(mktemp -d /data/tmp/godot-llm-web.XXXXXX)
trap 'rm -rf "$stage"' EXIT
"$GODOT_WEB_BIN" --headless --path "$ROOT" --export-release Web "$stage/index.html"
for file in index.html index.js index.wasm index.pck; do [[ -s "$stage/$file" ]] || { echo "missing web export: $file" >&2; exit 1; }; done
grep -q 'your-mom-stableanimator-scene-v5' "$stage/index.html"
touch "$stage/.gdignore"
find "$stage" -type d -exec chmod 0755 {} +
find "$stage" -type f -exec chmod 0644 {} +
rm -rf "$ROOT/web.new"
mv "$stage" "$ROOT/web.new"
trap - EXIT
if [[ -d "$ROOT/web" ]]; then rm -rf "$ROOT/web.previous"; mv "$ROOT/web" "$ROOT/web.previous"; fi
mv "$ROOT/web.new" "$ROOT/web"
rm -rf "$ROOT/web.previous"
printf 'web_export=ok files=%s bytes=%s time=%s\n' "$(find "$ROOT/web" -type f | wc -l)" "$(du -sb "$ROOT/web" | cut -f1)" "$(date -Is)"
