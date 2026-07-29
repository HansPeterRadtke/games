#!/usr/bin/env python3
from __future__ import annotations

import base64
import gc
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

HOST = os.environ.get("LLM_GAME_VIDEO_HOST", "10.8.0.7")
PORT = int(os.environ.get("LLM_GAME_VIDEO_PORT", "15311"))
MAX_BODY_BYTES = int(os.environ.get("LLM_GAME_VIDEO_MAX_BODY_BYTES", "8388608"))
BASE_MODEL = os.environ.get("LLM_GAME_LTX_BASE", "/data/models/video/LTX-Video-2B-diffusers")
CONFIG_MODEL = os.environ.get("LLM_GAME_LTX_CONFIG", "/data/models/video/LTX-Video-0.9.5-config")
DISTILLED_CHECKPOINT = os.environ.get("LLM_GAME_LTX_CHECKPOINT", "/data/models/video/LTX-Video-2B-distilled/ltxv-2b-0.9.6-distilled-04-25.safetensors")
MATTING_URL = os.environ.get("LLM_GAME_MATTING_URL", "http://10.8.0.7:15313/matte")
CACHE = Path(os.environ.get("LLM_GAME_VIDEO_CACHE", "/data/var/llm_game/ltx_video_cache"))
CACHE.mkdir(parents=True, exist_ok=True)
ENGINE_VERSION = "ltx-video-2b-distilled-0.9.6-temporal-v2"
MODEL_SIZE = int(os.environ.get("LLM_GAME_VIDEO_MODEL_SIZE", "384"))
FRAME_COUNT = int(os.environ.get("LLM_GAME_VIDEO_FRAMES", "9"))
FRAME_RATE = int(os.environ.get("LLM_GAME_VIDEO_FPS", "8"))
INFERENCE_STEPS = int(os.environ.get("LLM_GAME_VIDEO_STEPS", "8"))

pipeline: Any = None
prompt_text_encoder: Any = None
prompt_tokenizer: Any = None
ltx_on_cuda = False
loaded_at = 0.0
load_error = ""
generation_lock = threading.Lock()


def send_json(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def compact(value: Any, maximum: int) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())[:maximum]


def opaque_usage(usage: str) -> bool:
    return usage in {"tileable_texture", "background_layer"}


def output_dimensions(kind: str) -> tuple[int, int]:
    return (192, 256) if kind in {"player", "npc", "creature", "enemy"} else (160, 160)


def load_models() -> None:
    global pipeline, prompt_text_encoder, prompt_tokenizer, ltx_on_cuda, loaded_at, load_error
    if pipeline is not None:
        return
    started = time.monotonic()
    try:
        import torch
        from diffusers import AutoencoderKLLTXVideo, LTXImageToVideoPipeline, LTXVideoTransformer3DModel
        torch.set_float32_matmul_precision("high")
        transformer = LTXVideoTransformer3DModel.from_single_file(
            DISTILLED_CHECKPOINT,
            config=CONFIG_MODEL,
            subfolder="transformer",
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )
        vae = AutoencoderKLLTXVideo.from_single_file(
            DISTILLED_CHECKPOINT,
            config=CONFIG_MODEL,
            subfolder="vae",
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )
        pipe = LTXImageToVideoPipeline.from_pretrained(
            BASE_MODEL,
            transformer=transformer,
            vae=vae,
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )
        prompt_text_encoder = pipe.text_encoder
        prompt_tokenizer = pipe.tokenizer
        pipe.text_encoder = None
        pipe.tokenizer = None
        pipeline = pipe
        ltx_on_cuda = False
        loaded_at = time.time()
        load_error = ""
        gc.collect()
        print(json.dumps({
            "event": "ltx_loaded_cpu",
            "seconds": round(time.monotonic() - started, 3),
            "engine": ENGINE_VERSION,
            "base": BASE_MODEL,
            "checkpoint": DISTILLED_CHECKPOINT,
            "matting_url": MATTING_URL,
            "text_encoder_detached": True,
        }), flush=True)
    except Exception as exc:
        load_error = f"{type(exc).__name__}: {exc}"
        raise


def request_key(payload: dict[str, Any]) -> str:
    canonical = base64.b64decode(str(payload.get("canonical_png_b64", "")), validate=True)
    content = {
        "version": ENGINE_VERSION,
        "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
        "kind": payload.get("kind"),
        "asset_usage": payload.get("asset_usage"),
        "name": payload.get("name"),
        "clip_name": payload.get("clip_name"),
        "animation_prompt": payload.get("animation_prompt"),
        "negative_prompt": payload.get("negative_prompt"),
        "expected_labels": payload.get("expected_labels"),
        "review_requirements": payload.get("review_requirements"),
        "seed": payload.get("seed"),
        "frames": FRAME_COUNT,
        "fps": FRAME_RATE,
        "steps": INFERENCE_STEPS,
        "size": MODEL_SIZE,
        "matting_url": MATTING_URL,
    }
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def prepare_source(png: bytes) -> Any:
    from PIL import Image
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    background.alpha_composite(image)
    rgb = background.convert("RGB")
    rgb.thumbnail((MODEL_SIZE - 24, MODEL_SIZE - 24), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (MODEL_SIZE, MODEL_SIZE), (255, 255, 255))
    canvas.paste(rgb, ((MODEL_SIZE - rgb.width) // 2, (MODEL_SIZE - rgb.height) // 2))
    return canvas


def full_prompt(payload: dict[str, Any]) -> str:
    kind = compact(payload.get("kind"), 30)
    usage = compact(payload.get("asset_usage"), 40)
    prompt = compact(payload.get("animation_prompt"), 720)
    if kind in {"player", "npc", "creature", "enemy"}:
        suffix = " Fixed camera. Same identity, face, clothes, colors and proportions. One subject. Keep full head, hands, legs and feet visible in every frame. Plain white background."
    elif opaque_usage(usage):
        suffix = " Fixed camera. Preserve the same opaque edge-to-edge material or architectural layer, geometry, colors and borders."
    else:
        suffix = " Fixed camera. Same object identity, geometry, materials and colors. One complete object on plain white."
    return prompt + suffix


def encode_prompts(payloads: list[dict[str, Any]]) -> tuple[Any, Any, dict[str, Any]]:
    global ltx_on_cuda
    import torch
    if pipeline is None or prompt_text_encoder is None or prompt_tokenizer is None:
        raise RuntimeError("LTX prompt encoder is not loaded")
    prompts = [full_prompt(payload) for payload in payloads]
    started = time.monotonic()
    pipeline.text_encoder = prompt_text_encoder
    pipeline.tokenizer = prompt_tokenizer
    try:
        embeds, masks, _negative, _negative_masks = pipeline.encode_prompt(
            prompt=prompts,
            negative_prompt=None,
            do_classifier_free_guidance=False,
            num_videos_per_prompt=1,
            max_sequence_length=128,
            device=torch.device("cpu"),
            dtype=torch.bfloat16,
        )
    finally:
        pipeline.text_encoder = None
        pipeline.tokenizer = None
    gc.collect()
    if not ltx_on_cuda:
        pipeline.transformer.to("cuda")
        pipeline.vae.to("cuda")
        pipeline.vae.enable_tiling()
        ltx_on_cuda = True
    embeds = embeds.to("cuda")
    masks = masks.to("cuda") if masks is not None else None
    torch.cuda.empty_cache()
    execution_device = str(pipeline._execution_device)
    if not execution_device.startswith("cuda"):
        raise RuntimeError(f"LTX pipeline execution device is {execution_device}, expected CUDA after detaching T5")
    return embeds, masks, {
        "seconds": round(time.monotonic() - started, 3),
        "prompt_count": len(prompts),
        "prompts": prompts,
        "text_encoder_detached": pipeline.text_encoder is None,
        "execution_device": execution_device,
    }


def generate_video_from_embeddings(
    source: Any,
    payload: dict[str, Any],
    seed: int,
    embeds: Any,
    mask: Any,
    prompt_encode_meta: dict[str, Any],
) -> tuple[list[Any], dict[str, Any]]:
    import numpy as np
    import torch
    if pipeline is None:
        raise RuntimeError("LTX pipeline is not loaded")
    torch.cuda.empty_cache()
    infer_started = time.monotonic()
    result = pipeline(
        image=source,
        prompt=None,
        prompt_embeds=embeds,
        prompt_attention_mask=mask,
        height=MODEL_SIZE,
        width=MODEL_SIZE,
        num_frames=FRAME_COUNT,
        frame_rate=FRAME_RATE,
        num_inference_steps=INFERENCE_STEPS,
        guidance_scale=1.0,
        generator=torch.Generator(device="cuda").manual_seed(seed),
        output_type="pil",
    )
    frames = result.frames[0]
    arrays = [np.asarray(frame.convert("RGB"), dtype=np.int16) for frame in frames]
    adjacent = [float(np.abs(arrays[index] - arrays[index - 1]).mean()) for index in range(1, len(arrays))]
    if len(frames) != FRAME_COUNT:
        raise RuntimeError(f"LTX returned {len(frames)} frames, expected {FRAME_COUNT}")
    if max(adjacent, default=0.0) < 0.55:
        raise RuntimeError(f"LTX clip contains insufficient temporal motion: {adjacent}")
    return frames, {
        "prompt": full_prompt(payload),
        "prompt_encode": prompt_encode_meta,
        "inference_seconds": round(time.monotonic() - infer_started, 3),
        "adjacent_rgb_diff": [round(value, 4) for value in adjacent],
        "steps": INFERENCE_STEPS,
        "guidance_scale": 1.0,
        "frame_rate": FRAME_RATE,
    }


def generate_video(source: Any, payload: dict[str, Any], seed: int) -> tuple[list[Any], dict[str, Any]]:
    embeds, masks, encode_meta = encode_prompts([payload])
    return generate_video_from_embeddings(source, payload, seed, embeds[0:1], masks[0:1] if masks is not None else None, encode_meta)


def raw_paths(key: str) -> dict[str, Path]:
    directory = CACHE / f"{key}.raw"
    return {"dir": directory, "meta": directory / "video.json"}


def save_raw_frames(key: str, frames: list[Any], video_meta: dict[str, Any]) -> None:
    paths = raw_paths(key)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        frame.convert("RGB").save(paths["dir"] / f"frame-{index:02d}.png", format="PNG")
    paths["meta"].write_text(json.dumps(video_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_raw_frames(key: str) -> tuple[list[Any], dict[str, Any]] | None:
    from PIL import Image
    paths = raw_paths(key)
    if not paths["meta"].exists():
        return None
    frame_files = sorted(paths["dir"].glob("frame-*.png"))
    if len(frame_files) != FRAME_COUNT:
        return None
    frames = [Image.open(path).convert("RGB") for path in frame_files]
    meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
    meta["raw_cache_used"] = True
    return frames, meta


def cache_paths(key: str) -> dict[str, Path]:
    return {"png": CACHE / f"{key}.png", "gif": CACHE / f"{key}.gif", "sheet": CACHE / f"{key}.sheet.png", "meta": CACHE / f"{key}.json"}


def send_to_matting(raw_frames: list[Any], payload: dict[str, Any]) -> tuple[bytes, bytes, bytes, dict[str, Any]]:
    import urllib.error
    import urllib.request
    frame_values: list[str] = []
    for frame in raw_frames:
        buffer = io.BytesIO()
        frame.convert("RGB").save(buffer, format="PNG")
        frame_values.append(base64.b64encode(buffer.getvalue()).decode("ascii"))
    matting_payload = {
        "frames_png_b64": frame_values,
        "kind": compact(payload.get("kind"), 30),
        "asset_usage": compact(payload.get("asset_usage"), 40),
        "name": compact(payload.get("name"), 100),
        "clip_name": compact(payload.get("clip_name"), 80),
        "expected_labels": payload.get("expected_labels", []),
        "review_requirements": payload.get("review_requirements", ""),
        "frame_rate": FRAME_RATE,
    }
    request = urllib.request.Request(
        MATTING_URL,
        data=json.dumps(matting_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            value = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"matting service HTTP {exc.code}: {detail}") from exc
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise RuntimeError(f"matting service rejected LTX frames: {value!r}")
    return (
        base64.b64decode(value.pop("png_b64"), validate=True),
        base64.b64decode(value.pop("gif_b64"), validate=True),
        base64.b64decode(value.pop("sheet_b64"), validate=True),
        value,
    )


def finalize_clip(
    payload: dict[str, Any],
    key: str,
    seed: int,
    raw_frames: list[Any],
    video_meta: dict[str, Any],
    started: float,
) -> tuple[bytes, bytes, bytes, dict[str, Any]]:
    paths = cache_paths(key)
    save_raw_frames(key, raw_frames, video_meta)
    png, gif, sheet, matting_meta = send_to_matting(raw_frames, payload)
    meta = {
        "ok": True,
        "cached": False,
        "key": key,
        "engine": ENGINE_VERSION,
        "temporal_model": True,
        "native_video_frames": True,
        "fallback_used": False,
        "kind": compact(payload.get("kind"), 30),
        "asset_usage": compact(payload.get("asset_usage"), 40),
        "name": compact(payload.get("name"), 100),
        "clip_name": compact(payload.get("clip_name"), 80),
        "frame_count": int(matting_meta["frame_count"]),
        "frame_width": int(matting_meta["frame_width"]),
        "frame_height": int(matting_meta["frame_height"]),
        "frame_duration_ms": int(matting_meta["frame_duration_ms"]),
        "seed": seed,
        "generation_seconds": round(time.monotonic() - started, 3),
        "video": video_meta,
        "matting": matting_meta,
        "processing": matting_meta.get("processing", {}),
        "mid_frame_review": matting_meta.get("mid_frame_review", {}),
        "validation": matting_meta.get("validation", {}),
        "models": {"video": DISTILLED_CHECKPOINT, "base": BASE_MODEL, "matting_service": MATTING_URL},
        "png_path": str(paths["png"]),
        "gif_path": str(paths["gif"]),
        "sheet_path": str(paths["sheet"]),
    }
    paths["png"].write_bytes(png)
    paths["gif"].write_bytes(gif)
    paths["sheet"].write_bytes(sheet)
    paths["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return png, gif, sheet, meta


def cached_clip(payload: dict[str, Any]) -> tuple[bytes, bytes, bytes, dict[str, Any]] | None:
    key = request_key(payload)
    paths = cache_paths(key)
    if not all(path.exists() for path in paths.values()):
        return None
    meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
    meta["cached"] = True
    return paths["png"].read_bytes(), paths["gif"].read_bytes(), paths["sheet"].read_bytes(), meta


def animate(payload: dict[str, Any]) -> tuple[bytes, bytes, bytes, dict[str, Any]]:
    load_models()
    cached = cached_clip(payload)
    if cached is not None:
        return cached
    canonical_bytes = base64.b64decode(str(payload["canonical_png_b64"]), validate=True)
    source = prepare_source(canonical_bytes)
    key = request_key(payload)
    seed = int(payload.get("seed", int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)))
    started = time.monotonic()
    with generation_lock:
        raw_cached = load_raw_frames(key)
        if raw_cached is not None:
            raw_frames, video_meta = raw_cached
        else:
            raw_frames, video_meta = generate_video(source, payload, seed)
            save_raw_frames(key, raw_frames, video_meta)
        return finalize_clip(payload, key, seed, raw_frames, video_meta, started)


def animate_batch(payload: dict[str, Any]) -> dict[str, tuple[bytes, bytes, bytes, dict[str, Any]]]:
    load_models()
    clips = payload.get("clips", [])
    if not isinstance(clips, list) or not 1 <= len(clips) <= 8:
        raise ValueError("clips must contain between one and eight clip definitions")
    canonical_bytes = base64.b64decode(str(payload["canonical_png_b64"]), validate=True)
    source = prepare_source(canonical_bytes)
    common = {key: value for key, value in payload.items() if key != "clips"}
    results: dict[str, tuple[bytes, bytes, bytes, dict[str, Any]]] = {}
    uncached: list[dict[str, Any]] = []
    for clip in clips:
        if not isinstance(clip, dict):
            raise ValueError("every clip must be an object")
        merged = dict(common)
        merged.update(clip)
        clip_name = compact(merged.get("clip_name"), 80)
        if not clip_name or clip_name in results or any(compact(item.get("clip_name"), 80) == clip_name for item in uncached):
            raise ValueError(f"duplicate or empty clip name {clip_name!r}")
        if len(compact(merged.get("animation_prompt"), 1000).split()) < 8:
            raise ValueError(f"clip {clip_name} has an underspecified animation_prompt")
        cached = cached_clip(merged)
        if cached is not None:
            results[clip_name] = cached
        else:
            raw_cached = load_raw_frames(request_key(merged))
            if raw_cached is not None:
                raw_frames, video_meta = raw_cached
                key = request_key(merged)
                seed = int(merged.get("seed", int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)))
                results[clip_name] = finalize_clip(merged, key, seed, raw_frames, video_meta, time.monotonic())
            else:
                uncached.append(merged)
    if uncached:
        with generation_lock:
            embeds, masks, encode_meta = encode_prompts(uncached)
            for index, clip_payload in enumerate(uncached):
                key = request_key(clip_payload)
                seed = int(clip_payload.get("seed", int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)))
                started = time.monotonic()
                raw_frames, video_meta = generate_video_from_embeddings(
                    source,
                    clip_payload,
                    seed,
                    embeds[index:index + 1],
                    masks[index:index + 1] if masks is not None else None,
                    {**encode_meta, "batch_index": index, "batch_size": len(uncached)},
                )
                save_raw_frames(key, raw_frames, video_meta)
                results[compact(clip_payload.get("clip_name"), 80)] = finalize_clip(
                    clip_payload,
                    key,
                    seed,
                    raw_frames,
                    video_meta,
                    started,
                )
    return results


class Handler(BaseHTTPRequestHandler):
    server_version = "ThorLTXVideo/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(json.dumps({"event": "access", "path": self.path, "message": fmt % args}), flush=True)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/health":
            ready = pipeline is not None
            send_json(self, 200 if ready else 503, {
                "ok": ready,
                "loaded": ready,
                "engine": ENGINE_VERSION,
                "temporal_model": True,
                "matting_url": MATTING_URL,
                "frames": FRAME_COUNT,
                "fps": FRAME_RATE,
                "steps": INFERENCE_STEPS,
                "routes": ["/animate", "/animate-batch"],
                "loaded_at": loaded_at,
                "ltx_on_cuda": ltx_on_cuda,
                "execution_device": str(pipeline._execution_device) if pipeline is not None and ltx_on_cuda else "cpu-until-first-prompt",
                "load_error": load_error,
                "time": time.time(),
            })
            return
        send_json(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
        if route not in {"/animate", "/animate-batch"}:
            send_json(self, 404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length < 1 or length > MAX_BODY_BYTES:
                send_json(self, 413, {"ok": False, "error": "invalid request size"})
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            common_required = ["canonical_png_b64", "kind", "asset_usage", "name", "expected_labels", "review_requirements"]
            missing = [key for key in common_required if key not in payload]
            if missing:
                send_json(self, 400, {"ok": False, "error": "missing fields", "missing": missing})
                return
            if route == "/animate-batch":
                results = animate_batch(payload)
                response_clips: dict[str, Any] = {}
                for clip_name, (png, gif, sheet, meta) in results.items():
                    response_clips[clip_name] = {
                        "png_b64": base64.b64encode(png).decode("ascii"),
                        "gif_b64": base64.b64encode(gif).decode("ascii"),
                        "sheet_b64": base64.b64encode(sheet).decode("ascii"),
                        **meta,
                    }
                send_json(self, 200, {"ok": True, "engine": ENGINE_VERSION, "temporal_model": True, "clips": response_clips, "fallback_used": False})
                return
            for required_key in ["clip_name", "animation_prompt"]:
                if required_key not in payload:
                    send_json(self, 400, {"ok": False, "error": "missing field", "missing": [required_key]})
                    return
            png, gif, sheet, meta = animate(payload)
            send_json(self, 200, {"ok": True, "png_b64": base64.b64encode(png).decode("ascii"), "gif_b64": base64.b64encode(gif).decode("ascii"), "sheet_b64": base64.b64encode(sheet).decode("ascii"), **meta})
        except Exception as exc:
            trace = traceback.format_exc()[-7000:]
            print(json.dumps({"event": "error", "path": self.path, "error": f"{type(exc).__name__}: {exc}", "trace": trace}, ensure_ascii=False), flush=True)
            send_json(self, 500, {"ok": False, "error": f"{type(exc).__name__}: {exc}", "trace": trace})


def main() -> int:
    load_models()
    print(json.dumps({"event": "listening", "host": HOST, "port": PORT, "engine": ENGINE_VERSION}), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
