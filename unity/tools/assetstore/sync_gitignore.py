#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path("/data/src/github/games")
SELECTIONS = ROOT / "unity/assetstore/selected_assets.json"
GITIGNORE = ROOT / ".gitignore"
BEGIN = "# BEGIN local Unity imported assets"
END = "# END local Unity imported assets"


def build_block() -> list[str]:
    data = json.loads(SELECTIONS.read_text(encoding="utf-8"))
    lines = [BEGIN]
    for item in data:
        folder = item["asset_folder"]
        lines.append(f"unity/projects/fps_demo/{folder}/")
        lines.append(f"unity/projects/fps_demo/{folder}.meta")
    lines.append("unity/assetstore/imported/")
    lines.append(END)
    return lines


def main() -> int:
    lines = GITIGNORE.read_text(encoding="utf-8").splitlines()
    block = build_block()
    if BEGIN in lines and END in lines:
        start = lines.index(BEGIN)
        end = lines.index(END)
        new_lines = lines[:start] + block + lines[end + 1 :]
    else:
        new_lines = lines + [""] + block
    GITIGNORE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
