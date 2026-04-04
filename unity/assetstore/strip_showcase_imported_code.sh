#!/usr/bin/env bash
set -euo pipefail

PROJECT=/data/src/github/games/unity/projects/asset_basket_showcase
ASSETS="$PROJECT/Assets"

if [[ ! -d "$ASSETS" ]]; then
  echo "Assets folder not found: $ASSETS" >&2
  exit 1
fi

find "$ASSETS" -type f \( \
  -name '*.cs' -o \
  -name '*.js' -o \
  -name '*.boo' -o \
  -name '*.dll' -o \
  -name '*.asmdef' -o \
  -name '*.asmref' -o \
  -name '*.rsp' \
\) ! -path "$ASSETS/Editor/*" ! -path "$ASSETS/Editor" -print -delete

find "$ASSETS" -type f \( -name '*.cs.meta' -o -name '*.js.meta' -o -name '*.boo.meta' -o -name '*.dll.meta' -o -name '*.asmdef.meta' -o -name '*.asmref.meta' -o -name '*.rsp.meta' \) ! -path "$ASSETS/Editor/*" ! -path "$ASSETS/Editor" -print -delete

find "$ASSETS" -type d \( -name Editor -o -name Tests -o -name Test \) ! -path "$ASSETS/Editor" ! -path "$ASSETS/Editor/*" -prune -print | while read -r dir; do
  rm -rf "$dir" "$dir.meta"
done
