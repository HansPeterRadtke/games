#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from PIL import Image, ImageSequence


def fetch(url: str) -> tuple[bytes, dict[str, str], int]:
    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "gif-inspector-verifier/1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read(), {key.lower(): value for key, value in response.headers.items()}, response.status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="https://nitro.jonnyontherun.org/llm_game/gif_inspector/")
    parser.add_argument("--local", type=Path, default=Path(__file__).resolve().parents[1] / "web" / "gif_inspector")
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"
    html_bytes, html_headers, status = fetch(base)
    assert status == 200
    assert "text/html" in html_headers.get("content-type", "")
    html = html_bytes.decode("utf-8")
    assert "Your Mom — GIF Inspector" in html
    assert "No Godot, WebAssembly, workers or engine startup" in html
    lowered = html.lower()
    for forbidden in [".wasm", ".pck", "new engine", "startgame(", "godotready"]:
        assert forbidden not in lowered, forbidden
    manifest_bytes, manifest_headers, status = fetch(base + "manifest.json")
    assert status == 200
    assert "application/json" in manifest_headers.get("content-type", "")
    public = json.loads(manifest_bytes)
    local = json.loads((args.local / "manifest.json").read_text())
    assert public == local
    verified: list[dict[str, object]] = []
    for item in public["gifs"]:
        payload, headers, status = fetch(base + item["public_path"])
        assert status == 200
        assert "image/gif" in headers.get("content-type", ""), (item["slug"], headers)
        assert len(payload) == item["bytes"]
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]
        local_path = args.local / item["public_path"]
        assert payload == local_path.read_bytes()
        temp = Path("/tmp") / f"verify-{item['slug']}.gif"
        temp.write_bytes(payload)
        with Image.open(temp) as image:
            frames = list(ImageSequence.Iterator(image))
            assert image.size == (item["width"], item["height"])
            assert len(frames) == item["frames"]
            assert image.info.get("loop") == item["loop"]
        temp.unlink(missing_ok=True)
        verified.append({"slug": item["slug"], "bytes": len(payload), "sha256": item["sha256"]})
    assert len(verified) == public["count"] >= 15
    print(json.dumps({"ok": True, "base": base, "count": len(verified), "gifs": verified}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
