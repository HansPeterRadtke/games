#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "web" / "gif_inspector"
manifest = json.loads((SITE / "manifest.json").read_text())
assert manifest["ok"] is True
assert manifest["count"] == len(manifest["gifs"]) >= 15
assert (SITE / "index.html").is_file()
html = (SITE / "index.html").read_text()
assert "No Godot, WebAssembly, workers or engine startup" in html
assert "Machine-readable manifest" in html
paths: set[str] = set()
for item in manifest["gifs"]:
    public = item["public_path"]
    assert public.startswith("gifs/") and public.endswith(".gif")
    assert public not in paths
    paths.add(public)
    path = SITE / public
    assert path.is_file() and path.stat().st_size == item["bytes"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    with Image.open(path) as image:
        frames = list(ImageSequence.Iterator(image))
        assert image.size == (item["width"], item["height"])
        assert len(frames) == item["frames"] >= 2
        assert image.info.get("loop") == item["loop"]
    assert public in html
expected_player = {"player--idle", "player--walk", "player--player_interact", "player--player_attack", "player--player_use"}
assert expected_player <= {item["slug"] for item in manifest["gifs"]}
print(f"GIF inspector contracts passed: {manifest['count']} GIFs")
