#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "generated" / "world_assets"
OUTPUT_ROOT = ROOT / "web" / "gif_inspector"
GIF_ROOT = OUTPUT_ROOT / "gifs"


@dataclass(frozen=True)
class GifRecord:
    slug: str
    title: str
    category: str
    source: str
    public_path: str
    bytes: int
    width: int
    height: int
    frames: int
    duration_ms: int
    loop: int | None
    sha256: str


def title_from_slug(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()


def source_gifs() -> list[tuple[str, str, str, Path]]:
    rows: list[tuple[str, str, str, Path]] = []
    for asset_dir in sorted(path for path in SOURCE_ROOT.iterdir() if path.is_dir()):
        asset_id = asset_dir.name
        base = asset_dir / "animation.gif"
        if base.is_file():
            rows.append((asset_id, title_from_slug(asset_id), "Scene assets", base))
        clips_dir = asset_dir / "clips"
        if clips_dir.is_dir():
            for clip_dir in sorted(path for path in clips_dir.iterdir() if path.is_dir()):
                clip = clip_dir / "animation.gif"
                if clip.is_file():
                    slug = f"{asset_id}--{clip_dir.name}"
                    title = f"{title_from_slug(asset_id)} — {title_from_slug(clip_dir.name)}"
                    rows.append((slug, title, "Player clips" if asset_id == "player" else "Action clips", clip))
    return rows


def inspect_gif(slug: str, title: str, category: str, source: Path) -> GifRecord:
    destination = GIF_ROOT / f"{slug}.gif"
    shutil.copy2(source, destination)
    payload = destination.read_bytes()
    with Image.open(destination) as image:
        frames = list(ImageSequence.Iterator(image))
        duration = int(image.info.get("duration", 0) or 0)
        loop = image.info.get("loop")
        width, height = image.size
    return GifRecord(
        slug=slug,
        title=title,
        category=category,
        source=str(source.relative_to(ROOT)),
        public_path=f"gifs/{destination.name}",
        bytes=len(payload),
        width=width,
        height=height,
        frames=len(frames),
        duration_ms=duration,
        loop=int(loop) if loop is not None else None,
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def render(records: list[GifRecord]) -> str:
    grouped: dict[str, list[GifRecord]] = {}
    for record in records:
        grouped.setdefault(record.category, []).append(record)
    sections: list[str] = []
    for category in ["Player clips", "Scene assets", "Action clips"]:
        items = grouped.get(category, [])
        if not items:
            continue
        cards: list[str] = []
        for item in items:
            cards.append(f'''<article class="card" id="{html.escape(item.slug)}">
  <a class="image-link" href="{html.escape(item.public_path)}" target="_blank" rel="noreferrer">
    <div class="checker"><img src="{html.escape(item.public_path)}" alt="{html.escape(item.title)}"></div>
  </a>
  <h2>{html.escape(item.title)}</h2>
  <dl>
    <div><dt>File</dt><dd><a href="{html.escape(item.public_path)}" target="_blank" rel="noreferrer">{html.escape(Path(item.public_path).name)}</a></dd></div>
    <div><dt>Dimensions</dt><dd>{item.width} × {item.height}</dd></div>
    <div><dt>Frames</dt><dd>{item.frames}</dd></div>
    <div><dt>Frame duration</dt><dd>{item.duration_ms} ms</dd></div>
    <div><dt>Loop</dt><dd>{html.escape(str(item.loop))}</dd></div>
    <div><dt>Size</dt><dd>{item.bytes:,} bytes</dd></div>
    <div><dt>SHA-256</dt><dd><code>{item.sha256}</code></dd></div>
    <div><dt>Source</dt><dd><code>{html.escape(item.source)}</code></dd></div>
  </dl>
</article>''')
        sections.append(f'<section><h1>{html.escape(category)}</h1><div class="grid">{"".join(cards)}</div></section>')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Your Mom — GIF Inspector</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, sans-serif; background:#111; color:#eee; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:24px; }}
header {{ max-width:1100px; margin:0 auto 28px; }}
header h1 {{ margin:0 0 8px; font-size:clamp(28px,5vw,52px); }}
header p {{ margin:6px 0; color:#bbb; }}
header code {{ color:#fff; }}
section {{ max-width:1500px; margin:0 auto 36px; }}
section>h1 {{ border-bottom:1px solid #444; padding-bottom:8px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); gap:18px; align-items:start; }}
.card {{ background:#1d1d1d; border:1px solid #3c3c3c; border-radius:12px; overflow:hidden; box-shadow:0 10px 30px #0008; }}
.checker {{ min-height:280px; display:flex; align-items:center; justify-content:center; padding:14px; background-color:#aaa; background-image:linear-gradient(45deg,#777 25%,transparent 25%),linear-gradient(-45deg,#777 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#777 75%),linear-gradient(-45deg,transparent 75%,#777 75%); background-size:24px 24px; background-position:0 0,0 12px,12px -12px,-12px 0; }}
.checker img {{ display:block; max-width:100%; max-height:520px; image-rendering:auto; }}
.card h2 {{ margin:16px 16px 8px; font-size:21px; }}
dl {{ margin:0; padding:8px 16px 18px; }}
dl div {{ display:grid; grid-template-columns:110px 1fr; gap:10px; padding:6px 0; border-top:1px solid #333; }}
dt {{ color:#aaa; }} dd {{ margin:0; min-width:0; overflow-wrap:anywhere; }}
a {{ color:#8ecbff; }} code {{ font-size:12px; overflow-wrap:anywhere; }}
footer {{ max-width:1100px; margin:32px auto; color:#aaa; }}
</style>
</head>
<body>
<header>
  <h1>Your Mom — GIF Inspector</h1>
  <p>Static Apache subsite. No Godot, WebAssembly, workers or engine startup.</p>
  <p>{len(records)} copied GIF files. Generated from <code>generated/world_assets/</code>.</p>
  <p><a href="manifest.json">Machine-readable manifest</a></p>
</header>
{''.join(sections)}
<footer>Every image links directly to the copied GIF file.</footer>
</body>
</html>
'''


def main() -> int:
    if not SOURCE_ROOT.is_dir():
        raise SystemExit(f"missing source directory: {SOURCE_ROOT}")
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    GIF_ROOT.mkdir(parents=True)
    records = [inspect_gif(*row) for row in source_gifs()]
    if not records:
        raise SystemExit("no GIF files found")
    paths = [record.public_path for record in records]
    if len(paths) != len(set(paths)):
        raise SystemExit("duplicate public GIF paths")
    (OUTPUT_ROOT / "manifest.json").write_text(
        json.dumps({"ok": True, "count": len(records), "gifs": [asdict(record) for record in records]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "index.html").write_text(render(records), encoding="utf-8")
    print(json.dumps({"ok": True, "count": len(records), "output": str(OUTPUT_ROOT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
