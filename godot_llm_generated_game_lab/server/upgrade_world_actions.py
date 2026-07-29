from __future__ import annotations

import argparse
import copy
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

import world_generation as world

MODEL_URL = "http://10.8.0.7:14831/completion"
MODEL_ID = "qwen2.5-14b-world-author"
TIMEOUT = 300


def request_json(prompt: str, schema: dict[str, Any], seed: int, max_tokens: int) -> tuple[dict[str, Any], dict[str, Any]]:
    feedback = ""
    attempts: list[dict[str, Any]] = []
    for attempt in range(2):
        full_prompt = prompt
        if feedback:
            full_prompt += "\n\nThe previous output failed validation. Return the complete corrected JSON and fix every issue: " + feedback
        payload = {
            "prompt": full_prompt,
            "n_predict": max_tokens,
            "temperature": 0.48 if attempt == 0 else 0.25,
            "top_p": 0.9,
            "seed": seed + attempt,
            "json_schema": schema,
        }
        request = urllib.request.Request(
            MODEL_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = json.load(response)
            value = json.loads(body["content"])
            errors = [error.message for error in Draft202012Validator(schema).iter_errors(value)]
            if errors:
                raise ValueError("; ".join(errors[:20]))
            attempts.append({"attempt": attempt + 1, "ok": True, "seconds": round(time.monotonic() - started, 3)})
            return value, {
                "provider": "llama.cpp-native-constrained-completion",
                "endpoint": MODEL_URL,
                "model": body.get("model", MODEL_ID),
                "tokens_predicted": body.get("tokens_predicted"),
                "attempts": attempts,
                "fallback_used": False,
            }
        except Exception as exc:
            feedback = f"{type(exc).__name__}: {exc}"[:2400]
            attempts.append({"attempt": attempt + 1, "ok": False, "seconds": round(time.monotonic() - started, 3), "error": feedback})
    raise RuntimeError(json.dumps(attempts, ensure_ascii=False))


def restricted_action_schema(inputs: list[str], count: int) -> dict[str, Any]:
    action = copy.deepcopy(world.ACTION_SCHEMA)
    action["properties"]["input"]["enum"] = inputs
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["actions"],
        "properties": {
            "actions": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": action,
            }
        },
    }


def validate_trigger_set(actions: list[dict[str, Any]], expected: set[str]) -> None:
    actual = {str(action.get("input", "")) for action in actions}
    if actual != expected:
        raise ValueError(f"expected triggers {sorted(expected)}, got {sorted(actual)}")
    ids = [str(action.get("id", "")) for action in actions]
    if len(ids) != len(set(ids)):
        raise ValueError("action ids are not unique")
    for action in actions:
        effects = [effect for effect in action.get("effects", []) if isinstance(effect, dict)]
        if not any(effect.get("type") != "show_message" for effect in effects):
            raise ValueError(f"action {action.get('id')} has no state-changing effect")


def upgrade(bundle_path: Path) -> None:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    plan = bundle["scene_plan"]
    all_ids = [plan["player"]["id"]] + [obj["id"] for obj in plan["objects"]]
    exit_ids = [edge["id"] for edge in plan.get("exits", [])]
    context = {
        "game_description": bundle.get("game_description"),
        "opening_scene": bundle.get("opening_scene"),
        "scene_name": plan.get("scene_name"),
        "known_object_ids": all_ids,
        "known_exit_ids": exit_ids,
    }

    gameplay_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["gameplay", "actions"],
        "properties": {
            "gameplay": world.GAMEPLAY_SCHEMA,
            "actions": restricted_action_schema(["interact", "hit", "use"], 3)["properties"]["actions"],
        },
    }
    gameplay_prompt = f"""You are designing executable gameplay for this generated game. Return the gameplay rules and exactly three player actions with inputs interact, hit, and use, one of each. The player actions are default capabilities when no target-specific action overrides them. Use short reusable actor clip names player_interact, player_attack, and player_use. Every action requires a concrete state-changing effect, not only a message. Stats must include health and stamina plus at least one thematic stat. Available inputs must include move, touch, interact, attack, and use. Conditions must use only the structured condition schema. Effects may reference only these ids: {json.dumps(all_ids + exit_ids)}. Make the game playful, consequential, and consistent with the authored game.\n\nCONTEXT:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\nPLAYER:\n{json.dumps(plan['player'], ensure_ascii=False, indent=2)}"""
    gameplay_value, gameplay_meta = request_json(gameplay_prompt, gameplay_schema, 280001, 1800)
    validate_trigger_set(gameplay_value["actions"], {"interact", "hit", "use"})
    plan["gameplay"] = gameplay_value["gameplay"]
    plan["player"]["actions"] = gameplay_value["actions"]
    plan["player"].pop("interaction", None)
    plan["player"].pop("behavior", None)
    bundle.setdefault("generation", {})["gameplay_actions"] = gameplay_meta
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"event": "gameplay_ready", "actions": [a["id"] for a in gameplay_value["actions"]], "stats": [s["id"] for s in gameplay_value["gameplay"]["stats"]]}, ensure_ascii=False), flush=True)

    object_schema = restricted_action_schema(["touch", "interact", "hit"], 3)
    stats = [stat["id"] for stat in plan["gameplay"]["stats"]]
    for index, obj in enumerate(plan["objects"]):
        object_prompt = f"""Create exactly three executable actions for this generated game object: one touch action, one general interact action, and one hit action. They must be different, fun, and consistent with the object and game. Every action must contain at least one non-message effect that changes state, a stat, inventory, movement, visibility, collision, removes an object, changes scene, or ends the game. Use only known ids and stats. Conditions must be structured and should be empty unless genuinely needed. Actor clips should reuse player_touch, player_interact, or player_attack. Target clips must be unique to this object and trigger, such as {obj['id']}_touch, {obj['id']}_interact, and {obj['id']}_hit. Actor and target animation prompts must describe clearly visible physical motion suitable for a real image-to-video model. The hit action must visibly react to impact. The interact action must do something useful or narratively meaningful. The touch action must produce an immediate consequence.\n\nKNOWN OBJECT IDS: {json.dumps(all_ids)}\nKNOWN EXIT IDS: {json.dumps(exit_ids)}\nKNOWN STATS: {json.dumps(stats)}\nGAMEPLAY: {json.dumps(plan['gameplay'], ensure_ascii=False)}\nGAME CONTEXT: {json.dumps(context, ensure_ascii=False)}\nOBJECT: {json.dumps(obj, ensure_ascii=False, indent=2)}"""
        value, meta = request_json(object_prompt, object_schema, 280100 + index * 10, 1800)
        validate_trigger_set(value["actions"], {"touch", "interact", "hit"})
        obj["actions"] = value["actions"]
        obj.pop("interaction", None)
        obj.pop("behavior", None)
        bundle.setdefault("generation", {}).setdefault("object_actions", {})[obj["id"]] = meta
        bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"event": "object_actions_ready", "index": index + 1, "total": len(plan["objects"]), "id": obj["id"], "actions": [a["id"] for a in value["actions"]]}, ensure_ascii=False), flush=True)

    errors = world.validate_scene_plan(plan, bundle["user_prompt"])
    if errors:
        raise RuntimeError("upgraded action plan failed validation: " + json.dumps(errors, ensure_ascii=False))
    bundle.setdefault("generation", {})["action_upgrade_complete"] = {
        "model": MODEL_ID,
        "object_count": len(plan["objects"]),
        "action_count": len(plan["player"]["actions"]) + sum(len(obj["actions"]) for obj in plan["objects"]),
        "fallback_used": False,
    }
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"event": "complete", "actions": bundle["generation"]["action_upgrade_complete"]["action_count"], "fallback": False}, ensure_ascii=False), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    upgrade(args.bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
