#!/usr/bin/env python3
from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import io
import json
import os
import re
import threading
import time
import traceback
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from jsonschema import Draft202012Validator
from PIL import Image

import rpg_content
import world_generation

HOST = os.environ.get("LLM_GAME_OBJECT_HOST", "127.0.0.1")
PORT = int(os.environ.get("LLM_GAME_OBJECT_PORT", "15303"))
LLAMA_CHAT_URL = os.environ.get("LLM_GAME_OBJECT_LLAMA_URL", "http://127.0.0.1:14829/v1/chat/completions")
LLAMA_MODEL = os.environ.get("LLM_GAME_OBJECT_LLAMA_MODEL", "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
THOR_GENERATE_URL = os.environ.get("LLM_GAME_OBJECT_THOR_URL", "http://10.8.0.7:15310/generate")
STORE = Path(os.environ.get("LLM_GAME_OBJECT_STORE", "/data/var/llm_game/generated_objects"))
MAX_BODY_BYTES = int(os.environ.get("LLM_GAME_OBJECT_MAX_BODY_BYTES", "65536"))
STORE.mkdir(parents=True, exist_ok=True)
RPG_STORE = Path(os.environ.get("LLM_GAME_RPG_STORE", "/data/var/llm_game/rpg_content"))
RPG_STORE.mkdir(parents=True, exist_ok=True)

OBJECT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 2, "maxLength": 50},
        "category": {"type": "string", "enum": ["food", "treasure", "hazard", "tool", "creature", "decoration"]},
        "description": {"type": "string", "minLength": 35, "maxLength": 180},
        "interaction": {"type": "string", "enum": ["collect", "open", "heal", "damage", "bounce", "push", "talk"]},
        "size": {"type": "string", "enum": ["small", "medium", "large"]},
        "placement_height": {"type": "string", "enum": ["ground", "low", "floating"]},
        "motion": {"type": "string", "enum": ["idle", "pulse", "hop", "flutter", "spin"]},
        "image_prompt": {"type": "string", "minLength": 55, "maxLength": 300},
        "effect": {
            "type": "object",
            "properties": {
                "stat": {"type": "string", "enum": ["health", "score", "inventory", "none"]},
                "amount": {"type": "string", "enum": ["plus_one", "plus_five", "minus_one", "minus_five", "none"]},
                "message": {"type": "string", "minLength": 12, "maxLength": 120},
            },
            "required": ["stat", "amount", "message"],
            "additionalProperties": False,
        },
    },
    "required": ["name", "category", "description", "interaction", "size", "placement_height", "motion", "image_prompt", "effect"],
    "additionalProperties": False,
}

# This is the external provider contract required by the infra constraint-decoding guideline.
# The local llama.cpp build accepts the same schema only through its top-level json_schema
# extension, so request_llm_object translates this contract and validates the result again.
OPENAI_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "generated_game_object",
        "strict": True,
        "schema": OBJECT_SCHEMA,
    },
}
VALIDATOR = Draft202012Validator(OBJECT_SCHEMA)

CATEGORY_INTERACTIONS = {
    "food": {"collect", "heal"},
    "treasure": {"collect", "open"},
    "hazard": {"damage", "bounce"},
    "tool": {"collect", "push"},
    "creature": {"talk", "damage", "bounce"},
    "decoration": {"talk", "bounce"},
}
INTERACTION_EFFECTS = {
    "collect": {("score", "plus_one"), ("score", "plus_five"), ("inventory", "plus_one"), ("health", "plus_one"), ("health", "plus_five")},
    "open": {("score", "plus_one"), ("score", "plus_five"), ("inventory", "plus_one"), ("health", "plus_one"), ("health", "plus_five")},
    "heal": {("health", "plus_one"), ("health", "plus_five")},
    "damage": {("health", "minus_one"), ("health", "minus_five")},
    "bounce": {("none", "none")},
    "push": {("none", "none")},
    "talk": {("none", "none")},
}
FORBIDDEN = re.compile(r"\b(?:gun|rifle|pistol|bomb|grenade|sexual|nude|porn|suicide|self-harm)\b", re.I)
AMOUNT_VALUE = {"plus_one": 1, "plus_five": 5, "minus_one": -1, "minus_five": -5, "none": 0}
NUMBER_WORD = re.compile(r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|twenty|thirty|forty|fifty|hundred|thousand|million)\b", re.I)

JOBS: dict[str, concurrent.futures.Future[dict[str, Any]]] = {}
JOBS_LOCK = threading.Lock()
EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="generated-object")
RPG_ASSET_JOBS: dict[str, concurrent.futures.Future[dict[str, Any]]] = {}
RPG_ASSET_LOCK = threading.Lock()
RPG_ASSET_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="grounded-rpg-asset")


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def request_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json_bytes(payload),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}: {raw[:800]!r}")
    except urllib.error.HTTPError as exc:
        detail = exc.read(1200).decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    result = json.loads(raw.decode("utf-8"))
    if not isinstance(result, dict):
        raise RuntimeError("provider response is not an object")
    return result


def clean_text(value: Any, maximum: int) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())[:maximum]


def validate_semantics(obj: dict[str, Any]) -> list[str]:
    errors = [error.message for error in VALIDATOR.iter_errors(obj)]
    if errors:
        return errors
    name = clean_text(obj["name"], 60)
    description = clean_text(obj["description"], 220)
    image_prompt = clean_text(obj["image_prompt"], 360)
    message = clean_text(obj["effect"]["message"], 160)
    if not 1 <= len(name.split()) <= 6 or not 2 <= len(name) <= 50:
        errors.append("name must contain one to six words and two to fifty characters")
    if not 7 <= len(description.split()) <= 32:
        errors.append("description must contain seven to thirty-two words")
    if not 9 <= len(image_prompt.split()) <= 45:
        errors.append("image_prompt must contain nine to forty-five words")
    if not 3 <= len(message.split()) <= 18:
        errors.append("effect.message must contain three to eighteen words")
    if re.search(r"\d", message) or NUMBER_WORD.search(message):
        errors.append("effect.message must not contain numeric claims")
    if obj["interaction"] not in CATEGORY_INTERACTIONS[obj["category"]]:
        errors.append(f"{obj['category']} cannot use interaction {obj['interaction']}")
    pair = (obj["effect"]["stat"], obj["effect"]["amount"])
    if pair not in INTERACTION_EFFECTS[obj["interaction"]]:
        errors.append(f"interaction {obj['interaction']} cannot use effect {pair}")
    combined = " ".join([name, description, image_prompt, message])
    if FORBIDDEN.search(combined):
        errors.append("generated text contains a forbidden unsafe term")
    if name.casefold() in {"object", "item", "thing", "unknown", "placeholder"}:
        errors.append("name is a placeholder")
    if len(set(image_prompt.casefold().split())) < 7:
        errors.append("image_prompt is not visually specific enough")
    return errors


def normalized_object(obj: dict[str, Any]) -> dict[str, Any]:
    result = {
        "name": clean_text(obj["name"], 50),
        "category": obj["category"],
        "description": clean_text(obj["description"], 180),
        "interaction": obj["interaction"],
        "size": obj["size"],
        "placement_height": obj["placement_height"],
        "motion": obj["motion"],
        "image_prompt": clean_text(obj["image_prompt"], 300),
        "effect": {
            "stat": obj["effect"]["stat"],
            "amount": obj["effect"]["amount"],
            "message": clean_text(obj["effect"]["message"], 140),
        },
    }
    return result



def contains_keyword(text: str, terms: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(term)}\b", text, re.I) for term in terms)


def constraint_profile(idea: str, distance: int, recent_categories: list[str]) -> dict[str, Any]:
    text = idea.casefold()
    if contains_keyword(text, ("food", "eat", "apple", "fruit", "meal", "snack", "heal", "pastry", "bread", "candy")):
        category = "food"
    elif contains_keyword(text, ("treasure", "chest", "gold", "reward", "gem", "coffer", "strongbox")):
        category = "treasure"
    elif contains_keyword(text, ("hazard", "danger", "trap", "damage", "spike", "mine", "thorn")):
        category = "hazard"
    elif contains_keyword(text, ("tool", "key", "hammer", "rope", "device", "gadget")):
        category = "tool"
    elif contains_keyword(text, ("creature", "animal", "friend", "monster", "talk", "companion")):
        category = "creature"
    elif contains_keyword(text, ("decoration", "statue", "plant", "sign", "fountain", "lantern")):
        category = "decoration"
    else:
        options = [value for value in ("food", "treasure", "tool", "creature", "hazard", "decoration") if value not in recent_categories[-4:]]
        category = options[distance % len(options)] if options else "treasure"
    if contains_keyword(text, ("bounce", "spring", "launch")):
        return {"category": "hazard" if category not in {"hazard", "decoration"} else category, "interaction": "bounce", "stats": ["none"], "amounts": ["none"], "messages": ["This object launches the explorer upward."]}
    if contains_keyword(text, ("push", "boost", "propel")):
        return {"category": "tool", "interaction": "push", "stats": ["none"], "amounts": ["none"], "messages": ["Touching this tool pushes the explorer forward."]}
    profiles = {
        "food": {"interaction": "heal", "stats": ["health"], "amounts": ["plus_one", "plus_five"], "messages": ["Touching this food restores health."]},
        "treasure": {"interaction": "open", "stats": ["score", "inventory"], "amounts": ["plus_one", "plus_five"], "messages": ["Opening this treasure grants a useful reward."]},
        "hazard": {"interaction": "damage", "stats": ["health"], "amounts": ["minus_one", "minus_five"], "messages": ["Touching this hazard reduces health."]},
        "tool": {"interaction": "collect", "stats": ["inventory"], "amounts": ["plus_one"], "messages": ["Collecting this tool adds it to inventory."]},
        "creature": {"interaction": "talk", "stats": ["none"], "amounts": ["none"], "messages": ["This creature shares a curious thought."]},
        "decoration": {"interaction": "talk", "stats": ["none"], "amounts": ["none"], "messages": ["This object reacts when the explorer touches it."]},
    }
    return {"category": category, **profiles[category]}


def schema_for_profile(profile: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads(json.dumps(OBJECT_SCHEMA))
    schema["properties"]["category"]["enum"] = [profile["category"]]
    schema["properties"]["interaction"]["enum"] = [profile["interaction"]]
    schema["properties"]["effect"]["properties"]["stat"]["enum"] = profile["stats"]
    schema["properties"]["effect"]["properties"]["amount"]["enum"] = profile["amounts"]
    schema["properties"]["effect"]["properties"]["message"]["enum"] = profile["messages"]
    return schema

def plan_schema_for_profile(profile: dict[str, Any]) -> dict[str, Any]:
    category = profile["category"]
    materials = {
        "food": ["glossy fruit skin", "baked pastry", "frosted dough", "wrapped candy", "golden crust"],
        "treasure": ["carved wood", "polished metal", "crystal", "stone", "painted leather"],
        "tool": ["polished metal", "carved wood", "crystal", "painted leather", "brass machinery"],
        "creature": ["soft fur", "smooth scales", "crystal feathers", "plush hide", "luminous jelly"],
        "hazard": ["black iron", "volcanic stone", "thorny wood", "crystal", "brass machinery"],
        "decoration": ["carved stone", "crystal", "painted wood", "polished metal", "glazed ceramic"],
    }
    shapes = {
        "food": ["rounded apple", "plump fruit", "layered pastry", "wrapped snack"],
        "treasure": ["arched chest", "square strongbox", "round coffer", "tall reliquary"],
        "tool": ["compact tool", "hooked device", "crystal key", "spiral gadget"],
        "creature": ["winged creature", "round creature", "long-eared creature", "floating jelly creature"],
        "hazard": ["spiked obstacle", "swinging thorn", "glowing mine", "snapping plant"],
        "decoration": ["ornate statue", "flowering lantern", "carved sign", "crystal fountain"],
    }
    details = {
        "food": ["golden leaf", "sugar crystals", "striped wrapper", "tiny stem", "frosting swirl"],
        "treasure": ["glowing lock", "winged hinges", "star carvings", "moon clasp", "gem studs"],
        "tool": ["spiral handle", "crystal core", "brass dial", "hooked tip", "rune buttons"],
        "creature": ["bright eye", "tiny wings", "striped markings", "curled antennae", "soft horns"],
        "hazard": ["warning glow", "sharp thorns", "pulsing core", "jagged teeth", "crackling sparks"],
        "decoration": ["star carvings", "moon clasp", "gem studs", "glowing petals", "spiral inlay"],
    }
    placements = {
        "food": ["ground", "low", "floating"], "treasure": ["ground", "low"],
        "tool": ["ground", "low", "floating"], "creature": ["ground", "low", "floating"],
        "hazard": ["ground", "low", "floating"], "decoration": ["ground", "low"],
    }
    motions = {
        "food": ["idle", "pulse", "hop"], "treasure": ["idle", "pulse"],
        "tool": ["idle", "pulse", "spin"], "creature": ["idle", "pulse", "hop", "flutter"],
        "hazard": ["pulse", "hop", "spin"], "decoration": ["idle", "pulse"],
    }
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 2, "maxLength": 36},
            "primary_color": {"type": "string", "enum": ["gold", "ruby red", "sapphire blue", "violet", "copper", "silver", "amber", "coral"]},
            "secondary_color": {"type": "string", "enum": ["cream", "black", "white", "gold", "silver", "navy", "violet", "coral"]},
            "material": {"type": "string", "enum": materials[category]},
            "shape": {"type": "string", "enum": shapes[category]},
            "detail": {"type": "string", "enum": details[category]},
            "size": {"type": "string", "enum": ["small", "medium", "large"]},
            "placement_height": {"type": "string", "enum": placements[category]},
            "motion": {"type": "string", "enum": motions[category]},
            "amount": {"type": "string", "enum": profile["amounts"]},
            "reward_stat": {"type": "string", "enum": profile["stats"]},
        },
        "required": ["name", "primary_color", "secondary_color", "material", "shape", "detail", "size", "placement_height", "motion", "amount", "reward_stat"],
        "additionalProperties": False,
    }


def compile_plan(plan: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    name = clean_text(plan["name"], 36)
    primary = plan["primary_color"]
    secondary = plan["secondary_color"]
    material = plan["material"]
    shape = plan["shape"]
    detail = plan["detail"]
    category = profile["category"]
    interaction = profile["interaction"]
    description = clean_text(
        f"A {primary} and {secondary} {material} {shape} with {detail} waits along the trail and reacts when the explorer touches it.",
        180,
    )
    image_prompt = clean_text(
        f"A single {primary} and {secondary} {material} {shape} with {detail}, bold readable silhouette, clean colorful 2D illustrated side-scroller game sprite, centered full object, no text or border",
        300,
    )
    obj = {
        "name": name,
        "category": category,
        "description": description,
        "interaction": interaction,
        "size": plan["size"],
        "placement_height": plan["placement_height"],
        "motion": plan["motion"],
        "image_prompt": image_prompt,
        "effect": {
            "stat": plan["reward_stat"],
            "amount": plan["amount"],
            "message": profile["messages"][0],
        },
    }
    schema_errors = [error.message for error in VALIDATOR.iter_errors(obj)]
    if schema_errors:
        raise ValueError("compiled object failed schema: " + "; ".join(schema_errors))
    semantic_errors = validate_semantics(obj)
    if semantic_errors:
        raise ValueError("compiled object failed semantics: " + "; ".join(semantic_errors))
    return normalized_object(obj)


def request_llm_object(idea: str, distance: int, recent_categories: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    idea = clean_text(idea, 240) or "a useful surprising object"
    recent = [value for value in recent_categories if value in CATEGORY_INTERACTIONS][-5:]
    profile = constraint_profile(idea, distance, recent)
    plan_schema = plan_schema_for_profile(profile)
    plan_response_format = {"type": "json_schema", "json_schema": {"name": "generated_game_object_plan", "strict": True, "schema": plan_schema}}
    attempts: list[dict[str, Any]] = []
    feedback = ""
    system = (
        "Return exactly one compact JSON object matching the supplied closed schema. No prose or markdown. "
        f"Design one safe {profile['category']} object for a colorful 2D side-scroller. "
        "Choose a distinctive short name and coherent visual attributes. Do not choose green as an object color."
    )
    for attempt in range(2):
        user = f"Player idea: {idea}. Distance: {distance} meters. Recently used categories: {recent or ['none']}."
        if feedback:
            user += f" Previous plan was rejected for: {feedback}. Correct it."
        payload = {
            "model": LLAMA_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "json_schema": plan_schema,
            "max_tokens": 136,
            "temperature": 0.32 + attempt * 0.08,
            "top_p": 0.86,
            "seed": 240724 + distance + attempt,
        }
        started = time.monotonic()
        try:
            response = request_json(LLAMA_CHAT_URL, payload, 62.0)
            content = response["choices"][0]["message"]["content"]
            plan = json.loads(content)
            if not isinstance(plan, dict):
                raise ValueError("model plan is not an object")
            plan_errors = [error.message for error in Draft202012Validator(plan_schema).iter_errors(plan)]
            if plan_errors:
                raise ValueError("plan schema failed: " + "; ".join(plan_errors))
            obj = compile_plan(plan, profile)
            attempts.append({
                "attempt": attempt + 1,
                "seconds": round(time.monotonic() - started, 3),
                "plan_schema_valid": True,
                "final_schema_valid": True,
                "semantic_valid": True,
            })
            return obj, {
                "provider": "nitro-llama.cpp-constrained-plan-adapter",
                "model": LLAMA_MODEL,
                "plan_response_format": plan_response_format,
                "public_object_response_format": OPENAI_RESPONSE_FORMAT,
                "constraint_profile": profile,
                "translation": "response_format.json_schema.schema -> local top-level json_schema; strict plan -> deterministic object compiler -> strict public object validation",
                "plan": plan,
                "attempts": attempts,
            }
        except Exception as exc:
            feedback = f"{type(exc).__name__}: {exc}"[:600]
            attempts.append({
                "attempt": attempt + 1,
                "seconds": round(time.monotonic() - started, 3),
                "exception": feedback,
            })
    raise RuntimeError("constrained object plan failed: " + feedback + " attempts=" + json.dumps(attempts, ensure_ascii=False))


def slug_for(spec: dict[str, Any]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", spec["name"].casefold()).strip("-")[:36] or "object"
    digest = hashlib.sha256(json_bytes(spec)).hexdigest()[:12]
    return f"{base}-{digest}"


def paths_for(slug: str) -> dict[str, Path]:
    return {
        "spec": STORE / f"{slug}.spec.json",
        "meta": STORE / f"{slug}.json",
        "png": STORE / f"{slug}.png",
        "gif": STORE / f"{slug}.gif",
        "sheet": STORE / f"{slug}.sheet.png",
        "error": STORE / f"{slug}.error.json",
    }


def validate_assets(png: bytes, gif: bytes, sheet: bytes, meta: dict[str, Any]) -> dict[str, Any]:
    expected_frames = int(meta.get("frame_count", 0))
    width = int(meta.get("frame_width", 0))
    height = int(meta.get("frame_height", 0))
    if expected_frames < 6 or width < 64 or height < 64:
        raise RuntimeError("Thor metadata has invalid frame geometry")
    with Image.open(io.BytesIO(png)) as image:
        if image.mode != "RGBA" or image.getchannel("A").getextrema() != (0, 255):
            raise RuntimeError("first PNG lacks transparent and opaque pixels")
    decoded: list[Image.Image] = []
    with Image.open(io.BytesIO(gif)) as image:
        if image.n_frames != expected_frames or image.info.get("loop") != 0:
            raise RuntimeError("GIF frame count or loop metadata is invalid")
        for index in range(image.n_frames):
            image.seek(index)
            frame = image.convert("RGBA")
            if frame.getchannel("A").getextrema() != (0, 255):
                raise RuntimeError(f"GIF frame {index} lacks transparent and opaque pixels")
            decoded.append(frame.copy())
    with Image.open(io.BytesIO(sheet)) as image:
        if image.mode != "RGBA" or image.size != (width * expected_frames, height):
            raise RuntimeError("sprite sheet geometry is invalid")
        if image.getchannel("A").getextrema() != (0, 255):
            raise RuntimeError("sprite sheet lacks transparent and opaque pixels")
        frame_hashes = []
        for index in range(expected_frames):
            crop = image.crop((index * width, 0, (index + 1) * width, height))
            frame_hashes.append(hashlib.sha256(crop.tobytes()).hexdigest())
        if len(set(frame_hashes)) < max(3, expected_frames // 3):
            raise RuntimeError("sprite sheet does not contain enough distinct frames")
    return {
        "validated": True,
        "distinct_sheet_frames": len(set(frame_hashes)),
        "gif_frames": len(decoded),
        "alpha": [0, 255],
    }


def generate_assets(slug: str, spec: dict[str, Any]) -> dict[str, Any]:
    paths = paths_for(slug)
    started = time.monotonic()
    try:
        payload = {
            "name": spec["name"],
            "category": spec["category"],
            "prompt": spec["image_prompt"],
            "motion": spec["motion"],
        }
        response = request_json(THOR_GENERATE_URL, payload, 240.0)
        if not response.get("ok"):
            raise RuntimeError(str(response.get("error") or "Thor generation failed"))
        png = base64.b64decode(response["png_b64"], validate=True)
        gif = base64.b64decode(response["gif_b64"], validate=True)
        sheet = base64.b64decode(response["sheet_b64"], validate=True)
        thor_meta = {key: value for key, value in response.items() if key not in {"png_b64", "gif_b64", "sheet_b64"}}
        validation = validate_assets(png, gif, sheet, thor_meta)
        paths["png"].write_bytes(png)
        paths["gif"].write_bytes(gif)
        paths["sheet"].write_bytes(sheet)
        result = {
            "ok": True,
            "status": "ready",
            "slug": slug,
            "engine": thor_meta.get("engine"),
            "motion_generated": bool(thor_meta.get("motion_generated")),
            "frame_count": int(thor_meta["frame_count"]),
            "frame_width": int(thor_meta["frame_width"]),
            "frame_height": int(thor_meta["frame_height"]),
            "frame_duration_ms": int(thor_meta.get("frame_duration_ms", 100)),
            "generation_seconds": thor_meta.get("generation_seconds"),
            "gateway_seconds": round(time.monotonic() - started, 3),
            "validation": validation,
            "thor": thor_meta,
        }
        paths["meta"].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths["error"].unlink(missing_ok=True)
        return result
    except Exception as exc:
        result = {
            "ok": False,
            "status": "failed",
            "slug": slug,
            "error": f"{type(exc).__name__}: {exc}",
            "trace": traceback.format_exc()[-3000:],
            "gateway_seconds": round(time.monotonic() - started, 3),
        }
        paths["error"].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise


def ensure_job(slug: str, spec: dict[str, Any]) -> str:
    paths = paths_for(slug)
    if paths["meta"].exists() and paths["sheet"].exists() and paths["gif"].exists():
        return "ready"
    with JOBS_LOCK:
        future = JOBS.get(slug)
        if future and not future.done():
            return "generating"
        paths["error"].unlink(missing_ok=True)
        JOBS[slug] = EXECUTOR.submit(generate_assets, slug, spec)
    return "generating"


def status_for(slug: str) -> dict[str, Any]:
    paths = paths_for(slug)
    spec: dict[str, Any] = {}
    if paths["spec"].exists():
        spec = json.loads(paths["spec"].read_text(encoding="utf-8"))
    if paths["meta"].exists() and paths["sheet"].exists() and paths["gif"].exists():
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        status = "ready"
    elif paths["error"].exists():
        meta = json.loads(paths["error"].read_text(encoding="utf-8"))
        status = "failed"
    else:
        with JOBS_LOCK:
            future = JOBS.get(slug)
            if future and future.done():
                try:
                    future.result()
                except Exception:
                    pass
            active = bool(future and not future.done())
        meta = {"ok": True, "status": "generating" if active else "queued", "slug": slug}
        status = meta["status"]
    return {
        "ok": status != "failed",
        "status": status,
        "slug": slug,
        "spec": spec.get("spec", spec),
        "generation": spec.get("generation", {}),
        "asset": {
            **meta,
            "sheet_url": f"/llm_game_object_asset/{slug}.sheet.png",
            "gif_url": f"/llm_game_object_asset/{slug}.gif",
            "png_url": f"/llm_game_object_asset/{slug}.png",
            "meta_url": f"/llm_game_object_asset/{slug}.json",
        },
    }


def send_json(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    try:
        handler.end_headers()
        handler.wfile.write(raw)
    except (BrokenPipeError, ConnectionResetError):
        return


def rpg_slug(kind: str, content: dict[str, Any]) -> str:
    name = re.sub(r"[^a-z0-9]+", "-", str(content.get("name", kind)).casefold()).strip("-")[:40] or kind
    digest = hashlib.sha256(json_bytes(content)).hexdigest()[:12]
    return f"{kind}-{name}-{digest}"


def store_rpg(kind: str, content: dict[str, Any], generation: dict[str, Any]) -> tuple[str, Path]:
    slug = rpg_slug(kind, content)
    target = RPG_STORE / f"{slug}.json"
    payload = {"ok": True, "slug": slug, "kind": kind, "content": content, "generation": generation, "created_at": time.time()}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest = RPG_STORE / f"latest-{kind}.json"
    latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return slug, target


def load_rpg_file(name: str) -> dict[str, Any] | None:
    safe = re.sub(r"[^a-z0-9-]", "", name.casefold())[:100]
    target = RPG_STORE / f"{safe}.json"
    if not target.exists():
        return None
    value = json.loads(target.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def rpg_asset_paths(slug: str) -> dict[str, Path]:
    return {
        "png": RPG_STORE / f"{slug}.png",
        "gif": RPG_STORE / f"{slug}.gif",
        "sheet": RPG_STORE / f"{slug}.sheet.png",
        "meta": RPG_STORE / f"{slug}.asset.json",
        "error": RPG_STORE / f"{slug}.asset.error.json",
    }


def rpg_animation_description(content: dict[str, Any]) -> str:
    asset = content.get("asset", {})
    kind = content.get("kind")
    if kind == "player_character":
        return clean_text(asset.get("idle_animation_description"), 500)
    if kind == "loot":
        return clean_text(asset.get("idle_animation_description"), 500)
    if kind in {"weapon", "armor", "consumable"}:
        return clean_text(asset.get("idle_animation_description"), 500)
    raise ValueError(f"unsupported RPG content kind: {kind}")


def rpg_thor_payload(content: dict[str, Any]) -> dict[str, Any]:
    asset = content.get("asset", {})
    public_kind = "player" if content.get("kind") == "player_character" else str(content.get("kind"))
    required = ["structural_prompt", "semantic_prompt", "negative_prompt", "expected_labels", "review_requirements"]
    missing = [key for key in required if not asset.get(key)]
    if missing:
        raise ValueError(f"RPG content asset compiler omitted fields: {missing}")
    return {
        "kind": public_kind,
        "name": content["name"],
        "structural_prompt": asset["structural_prompt"],
        "semantic_prompt": asset["semantic_prompt"],
        "negative_prompt": asset["negative_prompt"],
        "animation_description": rpg_animation_description(content),
        "expected_labels": asset["expected_labels"],
        "review_requirements": asset["review_requirements"],
    }


def generate_rpg_assets(slug: str, content: dict[str, Any]) -> dict[str, Any]:
    paths = rpg_asset_paths(slug)
    started = time.monotonic()
    try:
        response = request_json(THOR_GENERATE_URL, rpg_thor_payload(content), 720.0)
        if not response.get("ok"):
            raise RuntimeError(str(response.get("error") or "Thor grounded asset generation failed"))
        png = base64.b64decode(response["png_b64"], validate=True)
        gif = base64.b64decode(response["gif_b64"], validate=True)
        sheet = base64.b64decode(response["sheet_b64"], validate=True)
        thor_meta = {key: value for key, value in response.items() if key not in {"png_b64", "gif_b64", "sheet_b64"}}
        validation = validate_assets(png, gif, sheet, thor_meta)
        if thor_meta.get("identity_anchored") is not True:
            raise RuntimeError("Thor asset is not identity anchored")
        selected_review = thor_meta.get("canonical_review", {}).get("selected_review", {})
        if selected_review.get("deterministic_pass") is not True:
            raise RuntimeError("canonical visual review did not pass")
        mid_review = thor_meta.get("animation", {}).get("mid_frame_review", {})
        if mid_review.get("deterministic_pass") is not True:
            raise RuntimeError("animation identity review did not pass")
        paths["png"].write_bytes(png)
        paths["gif"].write_bytes(gif)
        paths["sheet"].write_bytes(sheet)
        result = {
            "ok": True, "status": "ready", "slug": slug,
            "engine": thor_meta.get("engine"), "identity_anchored": True, "motion_generated": True,
            "frame_count": int(thor_meta["frame_count"]), "frame_width": int(thor_meta["frame_width"]),
            "frame_height": int(thor_meta["frame_height"]), "frame_duration_ms": int(thor_meta.get("frame_duration_ms", 120)),
            "generation_seconds": thor_meta.get("generation_seconds"), "gateway_seconds": round(time.monotonic() - started, 3),
            "validation": validation, "thor": thor_meta,
        }
        paths["meta"].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths["error"].unlink(missing_ok=True)
        return result
    except Exception as exc:
        result = {"ok": False, "status": "failed", "slug": slug, "error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()[-5000:], "gateway_seconds": round(time.monotonic() - started, 3)}
        paths["error"].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise


def ensure_rpg_asset_job(slug: str, content: dict[str, Any]) -> str:
    paths = rpg_asset_paths(slug)
    if paths["meta"].exists() and paths["sheet"].exists() and paths["gif"].exists():
        return "ready"
    with RPG_ASSET_LOCK:
        future = RPG_ASSET_JOBS.get(slug)
        if future and not future.done():
            return "generating"
        paths["error"].unlink(missing_ok=True)
        RPG_ASSET_JOBS[slug] = RPG_ASSET_EXECUTOR.submit(generate_rpg_assets, slug, content)
    return "generating"


def rpg_status(slug: str) -> dict[str, Any]:
    record = load_rpg_file(slug)
    if record is None:
        return {"ok": False, "status": "missing", "slug": slug}
    paths = rpg_asset_paths(slug)
    if paths["meta"].exists() and paths["sheet"].exists() and paths["gif"].exists():
        asset = json.loads(paths["meta"].read_text(encoding="utf-8")); status = "ready"
    elif paths["error"].exists():
        asset = json.loads(paths["error"].read_text(encoding="utf-8")); status = "failed"
    else:
        with RPG_ASSET_LOCK:
            future = RPG_ASSET_JOBS.get(slug)
            if future and future.done():
                try: future.result()
                except Exception: pass
            active = bool(future and not future.done())
        asset = {"ok": True, "status": "generating" if active else "not_requested", "slug": slug}
        status = asset["status"]
    return {
        "ok": status != "failed", "status": status, "slug": slug,
        "kind": record["kind"], "content": record["content"], "generation": record["generation"],
        "asset": {**asset, "png_url": f"/llm_game_object_asset/{slug}.png", "gif_url": f"/llm_game_object_asset/{slug}.gif", "sheet_url": f"/llm_game_object_asset/{slug}.sheet.png", "meta_url": f"/llm_game_object_asset/{slug}.asset.json"},
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "GeneratedGameObjects/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(json.dumps({"event": "access", "path": self.path, "message": fmt % args}), flush=True)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in {"/object/world/design", "/object/world/scene", "/object/world/plan"}:
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length < 1 or length > MAX_BODY_BYTES:
                    send_json(self, 413, {"ok": False, "error": "invalid request size"})
                    return
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("request body must be an object")
                seed = max(0, min(2_147_483_647, int(body.get("seed", 270727) or 270727)))
                user_prompt = str(body.get("user_prompt", ""))
                if len(user_prompt.encode("utf-8")) > 8000:
                    raise ValueError("user_prompt is too large")
                if path == "/object/world/design":
                    content, generation = world_generation.generate_game_description(user_prompt, seed=seed)
                    send_json(self, 200, {"ok": True, "stage": "game_description", "content": content, "generation": generation})
                    return
                game_description = body.get("game_description")
                if not isinstance(game_description, str) or not game_description.strip():
                    raise ValueError("game_description must be text returned by /object/world/design")
                if len(game_description.encode("utf-8")) > 24000:
                    raise ValueError("game_description is too large")
                if path == "/object/world/scene":
                    content, generation = world_generation.generate_opening_scene(game_description, user_prompt, seed=seed)
                    send_json(self, 200, {"ok": True, "stage": "opening_scene", "content": content, "generation": generation})
                    return
                opening_scene = body.get("opening_scene")
                if not isinstance(opening_scene, str) or not opening_scene.strip():
                    raise ValueError("opening_scene must be text returned by /object/world/scene")
                if len(opening_scene.encode("utf-8")) > 24000:
                    raise ValueError("opening_scene is too large")
                content, generation = world_generation.generate_scene_plan(
                    user_prompt, game_description, opening_scene, seed=seed
                )
                send_json(self, 200, {"ok": True, "stage": "scene_plan", "content": content, "generation": generation})
            except Exception as exc:
                send_json(self, 503, {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "fallback_used": False,
                    "time": time.time(),
                })
            return
        if path == "/object/rpg/generate":
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length < 1 or length > MAX_BODY_BYTES:
                    send_json(self, 413, {"ok": False, "error": "invalid request size"})
                    return
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("request body must be an object")
                kind = clean_text(body.get("kind"), 24).casefold()
                idea = clean_text(body.get("idea"), 500)
                seed = max(0, min(2_147_483_647, int(body.get("seed", 240724) or 240724)))
                content, generation = rpg_content.generate(kind, idea, request_json, LLAMA_CHAT_URL, LLAMA_MODEL, seed)
                slug, _target = store_rpg(kind, content, generation)
                asset_status = ensure_rpg_asset_job(slug, content) if body.get("generate_asset", False) else "not_requested"
                send_json(self, 200, {"ok": True, "slug": slug, "kind": kind, "content": content, "generation": generation, "asset_status": asset_status})
            except Exception as exc:
                send_json(self, 503, {"ok": False, "error": f"{type(exc).__name__}: {exc}", "time": time.time()})
            return
        if path == "/object/rpg/asset":
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length < 1 or length > MAX_BODY_BYTES:
                    send_json(self, 413, {"ok": False, "error": "invalid request size"}); return
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                slug = re.sub(r"[^a-z0-9-]", "", str(body.get("slug", "")).casefold())[:100]
                record = load_rpg_file(slug)
                if record is None:
                    send_json(self, 404, {"ok": False, "error": "unknown RPG content"}); return
                status = ensure_rpg_asset_job(slug, record["content"])
                response = rpg_status(slug); response["status"] = status if status != "ready" else response["status"]
                send_json(self, 200, response)
            except Exception as exc:
                send_json(self, 503, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})
            return
        if path != "/object/generate":
            send_json(self, 404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length < 1 or length > MAX_BODY_BYTES:
                send_json(self, 413, {"ok": False, "error": "invalid request size"})
                return
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("request body must be an object")
            idea = clean_text(body.get("idea"), 240)
            distance = max(0, min(1_000_000, int(body.get("distance", 0) or 0)))
            recent = body.get("recent_categories", [])
            if not isinstance(recent, list):
                raise ValueError("recent_categories must be an array")
            spec, generation = request_llm_object(idea, distance, [str(value) for value in recent])
            slug = slug_for(spec)
            paths = paths_for(slug)
            paths["spec"].write_text(json.dumps({"spec": spec, "generation": generation}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            status = ensure_job(slug, spec)
            response = status_for(slug)
            response["status"] = status if status != "ready" else response["status"]
            send_json(self, 200, response)
        except Exception as exc:
            send_json(self, 503, {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "time": time.time(),
            })

    def do_HEAD(self) -> None:
        path = unquote(self.path.split("?", 1)[0])
        if path.startswith("/asset/"):
            filename = path.rsplit("/", 1)[-1]
            match = re.fullmatch(r"([a-z0-9-]{1,100})(\.sheet\.png|\.gif|\.png|\.asset\.json|\.json)", filename)
            if not match:
                self.send_response(404)
                self.end_headers()
                return
            slug, suffix = match.groups()
            paths = paths_for(slug)
            target = {
                ".sheet.png": paths["sheet"],
                ".gif": paths["gif"],
                ".png": paths["png"],
                ".json": paths["meta"],
                ".asset.json": paths["meta"],
            }[suffix]
            if not target.exists():
                rpg_paths = rpg_asset_paths(slug)
                target = {".sheet.png": rpg_paths["sheet"], ".gif": rpg_paths["gif"], ".png": rpg_paths["png"], ".asset.json": rpg_paths["meta"], ".json": rpg_paths["meta"]}[suffix]
            if not target.exists():
                self.send_response(404)
                self.end_headers()
                return
            content_type = "image/png" if suffix.endswith("png") else "image/gif" if suffix == ".gif" else "application/json; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(target.stat().st_size))
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return
        if path == "/object/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self) -> None:
        path = unquote(self.path.split("?", 1)[0])
        if path == "/object/health":
            send_json(self, 200, {
                "ok": True,
                "service": "generated-game-objects",
                "constraint_contract": OPENAI_RESPONSE_FORMAT,
                "local_translation": "top-level json_schema",
                "llama_url": LLAMA_CHAT_URL,
                "thor_url": THOR_GENERATE_URL,
                "store": str(STORE),
                "active_jobs": sum(1 for future in JOBS.values() if not future.done()),
                "rpg_kinds": sorted(rpg_content.SCHEMAS),
                "rpg_game_description": rpg_content.GAME_DESCRIPTION,
                "world_author_url": world_generation.AUTHOR_MODEL_URL,
                "world_author_model": world_generation.AUTHOR_MODEL_ID,
                "world_structure_url": world_generation.STRUCTURE_MODEL_URL,
                "world_structure_model": world_generation.STRUCTURE_MODEL_ID,
                "world_generation_fallback": False,
                "world_stages": ["game_description", "opening_scene", "scene_plan"],
                "rpg_store": str(RPG_STORE),
                "active_rpg_asset_jobs": sum(1 for future in RPG_ASSET_JOBS.values() if not future.done()),
                "time": time.time(),
            })
            return
        if path == "/object/world/contracts":
            send_json(self, 200, {
                "ok": True,
                "author_model_url": world_generation.AUTHOR_MODEL_URL,
                "author_model_id": world_generation.AUTHOR_MODEL_ID,
                "structure_model_url": world_generation.STRUCTURE_MODEL_URL,
                "structure_model_id": world_generation.STRUCTURE_MODEL_ID,
                "fallback_used": False,
                "game_description_format": "free authored prose; first line is the game title; every user fragment is preserved verbatim",
                "opening_scene_format": "free authored prose; first line is the scene name; every user fragment is preserved verbatim",
                "scene_plan_base_schema": world_generation.SCENE_PLAN_SCHEMA,
                "endpoints": ["/object/world/design", "/object/world/scene", "/object/world/plan"],
            })
            return
        if path == "/object/rpg/contracts":
            send_json(self, 200, {"ok": True, "game_description": rpg_content.GAME_DESCRIPTION, "schemas": rpg_content.SCHEMAS})
            return
        if path.startswith("/object/rpg/status/"):
            slug = re.sub(r"[^a-z0-9-]", "", path.rsplit("/", 1)[-1].casefold())[:100]
            response = rpg_status(slug)
            send_json(self, 200 if response.get("status") != "missing" else 404, response)
            return
        if path.startswith("/object/rpg/latest/"):
            kind = re.sub(r"[^a-z]", "", path.rsplit("/", 1)[-1].casefold())[:24]
            target = RPG_STORE / f"latest-{kind}.json"
            if not target.exists():
                send_json(self, 404, {"ok": False, "error": "no generated content for kind"})
                return
            send_json(self, 200, json.loads(target.read_text(encoding="utf-8")))
            return
        if path.startswith("/object/rpg/content/"):
            value = load_rpg_file(path.rsplit("/", 1)[-1])
            if value is None:
                send_json(self, 404, {"ok": False, "error": "unknown RPG content"})
                return
            send_json(self, 200, value)
            return
        if path.startswith("/object/status/"):
            slug = re.sub(r"[^a-z0-9-]", "", path.rsplit("/", 1)[-1].casefold())[:64]
            if not slug or not paths_for(slug)["spec"].exists():
                send_json(self, 404, {"ok": False, "error": "unknown object"})
                return
            send_json(self, 200, status_for(slug))
            return
        if path.startswith("/asset/"):
            filename = path.rsplit("/", 1)[-1]
            match = re.fullmatch(r"([a-z0-9-]{1,100})(\.sheet\.png|\.gif|\.png|\.asset\.json|\.json)", filename)
            if not match:
                send_json(self, 404, {"ok": False, "error": "invalid asset name"})
                return
            slug, suffix = match.groups()
            paths = paths_for(slug)
            target = {
                ".sheet.png": paths["sheet"],
                ".gif": paths["gif"],
                ".png": paths["png"],
                ".json": paths["meta"],
                ".asset.json": paths["meta"],
            }[suffix]
            if not target.exists():
                rpg_paths = rpg_asset_paths(slug)
                target = {".sheet.png": rpg_paths["sheet"], ".gif": rpg_paths["gif"], ".png": rpg_paths["png"], ".asset.json": rpg_paths["meta"], ".json": rpg_paths["meta"]}[suffix]
            if not target.exists():
                payload = status_for(slug) if paths["spec"].exists() else rpg_status(slug)
                send_json(self, 202 if payload.get("status") in {"queued", "generating"} else 404, payload)
                return
            content_type = "image/png" if suffix.endswith("png") else "image/gif" if suffix == ".gif" else "application/json; charset=utf-8"
            raw = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)
            return
        send_json(self, 404, {"ok": False, "error": "not found"})


def main() -> int:
    print(json.dumps({"event": "listening", "host": HOST, "port": PORT, "store": str(STORE)}), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
