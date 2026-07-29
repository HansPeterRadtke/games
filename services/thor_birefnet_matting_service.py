#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HOST = os.environ.get("LLM_GAME_MATTING_HOST", "10.8.0.7")
PORT = int(os.environ.get("LLM_GAME_MATTING_PORT", "15313"))
MAX_BODY_BYTES = int(os.environ.get("LLM_GAME_MATTING_MAX_BODY_BYTES", "16777216"))
MATTING_MODEL = os.environ.get("LLM_GAME_MATTING_MODEL", "/data/models/matting/BiRefNet_lite-matting")
CACHE = Path(os.environ.get("LLM_GAME_MATTING_CACHE", "/data/var/llm_game/birefnet_matting_cache"))
CACHE.mkdir(parents=True, exist_ok=True)
ENGINE_VERSION = "birefnet-lite-matting-v1"

model: Any = None
preprocess: Any = None
loaded_at = 0.0
load_error = ""
lock = threading.Lock()


def compact(value: Any, maximum: int) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())[:maximum]


def send_json(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def opaque_usage(usage: str) -> bool:
    return usage in {"tileable_texture", "background_layer"}


def output_dimensions(kind: str) -> tuple[int, int]:
    return (288, 384) if kind in {"player", "npc", "creature", "enemy"} else (240, 240)


def load_model() -> None:
    global model, preprocess, loaded_at, load_error
    if model is not None:
        return
    started = time.monotonic()
    try:
        import torch
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation
        matte = AutoModelForImageSegmentation.from_pretrained(
            MATTING_MODEL,
            trust_remote_code=True,
            local_files_only=True,
        ).to(device="cuda", dtype=torch.float16).eval()
        prep = transforms.Compose([
            transforms.Resize((1024, 1024)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        model = matte
        preprocess = prep
        loaded_at = time.time()
        load_error = ""
        print(json.dumps({"event": "matting_loaded", "seconds": round(time.monotonic() - started, 3), "engine": ENGINE_VERSION}), flush=True)
    except Exception as exc:
        load_error = f"{type(exc).__name__}: {exc}"
        raise


def request_key(payload: dict[str, Any]) -> str:
    frame_hashes = [hashlib.sha256(base64.b64decode(value, validate=True)).hexdigest() for value in payload.get("frames_png_b64", [])]
    content = {
        "version": ENGINE_VERSION,
        "frames": frame_hashes,
        "kind": payload.get("kind"),
        "asset_usage": payload.get("asset_usage"),
        "name": payload.get("name"),
        "clip_name": payload.get("clip_name"),
        "expected_labels": payload.get("expected_labels"),
        "review_requirements": payload.get("review_requirements"),
        "frame_rate": payload.get("frame_rate", 8),
    }
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


def cache_paths(key: str) -> dict[str, Path]:
    return {
        "png": CACHE / f"{key}.png",
        "gif": CACHE / f"{key}.gif",
        "sheet": CACHE / f"{key}.sheet.png",
        "meta": CACHE / f"{key}.json",
    }


def matte_frame(image: Any, kind: str) -> tuple[Any, dict[str, Any]]:
    import numpy as np
    import torch
    from PIL import Image
    from scipy import ndimage
    tensor = preprocess(image.convert("RGB")).unsqueeze(0).to(device="cuda", dtype=torch.float16)
    with torch.inference_mode():
        prediction = model(tensor)[-1].sigmoid().float().cpu()[0, 0]
    alpha = np.asarray(Image.fromarray(np.uint8(np.clip(prediction.numpy(), 0, 1) * 255)).resize(image.size, Image.Resampling.LANCZOS), dtype=np.uint8)
    visible = alpha > 12
    labels, count = ndimage.label(visible, structure=np.ones((3, 3), dtype=bool))
    if count < 1:
        raise RuntimeError("BiRefNet returned an empty matte")
    areas = [int(np.sum(labels == index)) for index in range(1, count + 1)]
    largest_index = int(np.argmax(areas)) + 1
    keep = labels == largest_index
    alpha = np.where(keep, alpha, 0).astype(np.uint8)
    alpha_max = int(alpha.max())
    if alpha_max < 32:
        raise RuntimeError(f"BiRefNet matte confidence is too low: max={alpha_max}")
    alpha = np.clip(np.round(alpha.astype(np.float32) * (255.0 / alpha_max)), 0, 255).astype(np.uint8)
    alpha[alpha < 2] = 0
    alpha[alpha > 253] = 255
    ys, xs = np.where(alpha > 12)
    if len(xs) == 0:
        raise RuntimeError("BiRefNet matte became empty after connected-component cleanup")
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    height_ratio = (bbox[3] - bbox[1]) / alpha.shape[0]
    width_ratio = (bbox[2] - bbox[0]) / alpha.shape[1]
    top_margin = bbox[1] / alpha.shape[0]
    bottom_margin = (alpha.shape[0] - bbox[3]) / alpha.shape[0]
    if kind in {"player", "npc", "creature", "enemy"}:
        if height_ratio < 0.55 or top_margin > 0.24 or bottom_margin > 0.24:
            raise RuntimeError(f"BiRefNet did not preserve a complete character: bbox={bbox}, height={height_ratio:.4f}, top={top_margin:.4f}, bottom={bottom_margin:.4f}")
    rgba = image.convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha, "L"))
    return rgba, {
        "bbox": bbox,
        "height_ratio": round(height_ratio, 5),
        "width_ratio": round(width_ratio, 5),
        "top_margin_ratio": round(top_margin, 5),
        "bottom_margin_ratio": round(bottom_margin, 5),
        "transparent_ratio": round(float(np.mean(alpha == 0)), 5),
        "partial_alpha_ratio": round(float(np.mean((alpha > 0) & (alpha < 255))), 5),
        "components_before_cleanup": count,
    }


def process_frames(frames: list[Any], payload: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    import numpy as np
    from PIL import Image
    kind = compact(payload.get("kind"), 30)
    usage = compact(payload.get("asset_usage"), 40)
    target_width, target_height = output_dimensions(kind)
    if opaque_usage(usage):
        output = [frame.convert("RGB").resize((target_width, target_height), Image.Resampling.LANCZOS).convert("RGBA") for frame in frames]
        return output, {"mode": "opaque_full_frame_ltx", "matting_model": None, "frame_metrics": []}
    matted: list[Any] = []
    metrics: list[dict[str, Any]] = []
    boxes: list[list[int]] = []
    for frame in frames:
        rgba, metric = matte_frame(frame, kind)
        matted.append(rgba)
        metrics.append(metric)
        boxes.append(metric["bbox"])
    x0 = max(0, min(box[0] for box in boxes) - 10)
    y0 = max(0, min(box[1] for box in boxes) - 10)
    x1 = min(frames[0].width, max(box[2] for box in boxes) + 10)
    y1 = min(frames[0].height, max(box[3] for box in boxes) + 10)
    crop_width, crop_height = max(1, x1 - x0), max(1, y1 - y0)
    margin = 12
    scale = min((target_width - margin * 2) / crop_width, (target_height - margin * 2) / crop_height)
    scaled_width = max(1, int(round(crop_width * scale)))
    scaled_height = max(1, int(round(crop_height * scale)))
    output: list[Any] = []
    for rgba in matted:
        crop = rgba.crop((x0, y0, x1, y1)).resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        canvas.alpha_composite(crop, ((target_width - scaled_width) // 2, target_height - scaled_height - margin))
        alpha_channel = canvas.getchannel("A")
        minimum, maximum = alpha_channel.getextrema()
        if maximum < 32:
            raise RuntimeError(f"processed BiRefNet frame has insufficient alpha confidence: {(minimum, maximum)}")
        if maximum != 255:
            import numpy as np
            alpha_array = np.asarray(alpha_channel, dtype=np.uint8)
            alpha_array = np.clip(np.round(alpha_array.astype(np.float32) * (255.0 / maximum)), 0, 255).astype(np.uint8)
            alpha_array[alpha_array < 2] = 0
            alpha_array[alpha_array > 253] = 255
            canvas.putalpha(Image.fromarray(alpha_array, "L"))
        if canvas.getchannel("A").getextrema() != (0, 255):
            raise RuntimeError(f"processed BiRefNet frame lost alpha range after normalization: {canvas.getchannel('A').getextrema()}")
        output.append(canvas)
    arrays = [np.asarray(frame, dtype=np.int16) for frame in output]
    adjacent = [float(np.abs(arrays[index] - arrays[index - 1]).mean()) for index in range(1, len(arrays))]
    if max(adjacent, default=0.0) < 0.2:
        raise RuntimeError(f"matted clip contains insufficient visible motion: {adjacent}")
    return output, {
        "mode": "birefnet_lite_matted_ltx",
        "matting_model": MATTING_MODEL,
        "source_crop": [x0, y0, x1, y1],
        "frame_metrics": metrics,
        "processed_adjacent_rgba_diff": [round(value, 4) for value in adjacent],
    }


def review_mid_frame(frame: Any, payload: dict[str, Any], key: str) -> dict[str, Any]:
    import thor_grounded_rpg_asset_service as assets
    from PIL import Image
    usage = compact(payload.get("asset_usage"), 40)
    if opaque_usage(usage):
        review_image = frame.convert("RGB")
    else:
        white = Image.new("RGBA", frame.size, (255, 255, 255, 255))
        white.alpha_composite(frame.convert("RGBA"))
        review_image = white.convert("RGB")
    review = assets.review_candidate(review_image, payload, key + "-matte", 200)
    if review.get("deterministic_pass") is not True:
        raise RuntimeError("matted mid-frame failed grounded review: " + json.dumps(review, ensure_ascii=False))
    return review


def matte(payload: dict[str, Any]) -> tuple[bytes, bytes, bytes, dict[str, Any]]:
    import thor_grounded_rpg_asset_service as assets
    from PIL import Image
    load_model()
    key = request_key(payload)
    paths = cache_paths(key)
    if all(path.exists() for path in paths.values()):
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        meta["cached"] = True
        return paths["png"].read_bytes(), paths["gif"].read_bytes(), paths["sheet"].read_bytes(), meta
    frames = [Image.open(io.BytesIO(base64.b64decode(value, validate=True))).convert("RGB") for value in payload["frames_png_b64"]]
    if not 2 <= len(frames) <= 33:
        raise ValueError("frames_png_b64 must contain between two and 33 frames")
    started = time.monotonic()
    with lock:
        processed, processing = process_frames(frames, payload)
        review = review_mid_frame(processed[len(processed) // 2], payload, key)
        usage = compact(payload.get("asset_usage"), 40)
        png, gif, sheet = assets.encode_assets(processed, usage)
        width, height = output_dimensions(compact(payload.get("kind"), 30))
        validation = assets.validate_encoded(gif, sheet, len(processed), width, height, usage)
    meta = {
        "ok": True,
        "cached": False,
        "key": key,
        "engine": ENGINE_VERSION,
        "fallback_used": False,
        "kind": compact(payload.get("kind"), 30),
        "asset_usage": usage,
        "name": compact(payload.get("name"), 100),
        "clip_name": compact(payload.get("clip_name"), 80),
        "frame_count": len(processed),
        "frame_width": width,
        "frame_height": height,
        "frame_duration_ms": int(round(1000 / int(payload.get("frame_rate", 8)))),
        "generation_seconds": round(time.monotonic() - started, 3),
        "processing": processing,
        "mid_frame_review": review,
        "validation": validation,
        "models": {"matting": MATTING_MODEL},
    }
    paths["png"].write_bytes(png)
    paths["gif"].write_bytes(gif)
    paths["sheet"].write_bytes(sheet)
    paths["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return png, gif, sheet, meta


class Handler(BaseHTTPRequestHandler):
    server_version = "ThorBiRefNetMatting/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(json.dumps({"event": "access", "path": self.path, "message": fmt % args}), flush=True)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/health":
            ready = model is not None
            send_json(self, 200 if ready else 503, {"ok": ready, "loaded": ready, "engine": ENGINE_VERSION, "model": MATTING_MODEL, "loaded_at": loaded_at, "load_error": load_error, "time": time.time()})
            return
        send_json(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/matte":
            send_json(self, 404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length < 1 or length > MAX_BODY_BYTES:
                send_json(self, 413, {"ok": False, "error": "invalid request size"})
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            required = ["frames_png_b64", "kind", "asset_usage", "name", "clip_name", "expected_labels", "review_requirements"]
            missing = [key for key in required if key not in payload]
            if missing:
                send_json(self, 400, {"ok": False, "error": "missing fields", "missing": missing})
                return
            png, gif, sheet, meta = matte(payload)
            send_json(self, 200, {"ok": True, "png_b64": base64.b64encode(png).decode("ascii"), "gif_b64": base64.b64encode(gif).decode("ascii"), "sheet_b64": base64.b64encode(sheet).decode("ascii"), **meta})
        except Exception as exc:
            trace = traceback.format_exc()[-7000:]
            print(json.dumps({"event": "error", "path": self.path, "error": f"{type(exc).__name__}: {exc}", "trace": trace}, ensure_ascii=False), flush=True)
            send_json(self, 500, {"ok": False, "error": f"{type(exc).__name__}: {exc}", "trace": trace})


def main() -> int:
    load_model()
    print(json.dumps({"event": "listening", "host": HOST, "port": PORT, "engine": ENGINE_VERSION}), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
