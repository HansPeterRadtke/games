#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import requests

SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["field"],
    "properties": {
        "field": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "name", "description", "primary_object", "secondary_object", "unknown_exit", "return_exit"],
            "properties": {
                "id": {"type": "string", "enum": ["field001"]},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "primary_object": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "description", "affordance"],
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "affordance": {"type": "string", "enum": ["observe", "touch", "move", "remember"]},
                    },
                },
                "secondary_object": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "description", "affordance"],
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "affordance": {"type": "string", "enum": ["observe", "touch", "move", "remember"]},
                    },
                },
                "unknown_exit": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "direction", "description", "destination"],
                    "properties": {
                        "name": {"type": "string"},
                        "direction": {"type": "string", "enum": ["north", "east", "south", "west", "inward", "outward"]},
                        "description": {"type": "string"},
                        "destination": {"type": "null"},
                    },
                },
                "return_exit": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "direction", "description", "destination"],
                    "properties": {
                        "name": {"type": "string"},
                        "direction": {"type": "string", "enum": ["north", "east", "south", "west", "inward", "outward"]},
                        "description": {"type": "string"},
                        "destination": {"type": "string", "enum": ["field000"]},
                    },
                },
            },
        }
    },
}

PROMPT = """Return JSON for one perception-oriented game field. The field is the player's semantic boundary between known reality and unknown possibility. Use id field001. Make the unknown exit unresolved and the return exit point to field000."""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:14829")
    parser.add_argument("--output", default="")
    parser.add_argument("--seed", type=int, default=2026070502)
    args = parser.parse_args()
    payload = {
        "prompt": PROMPT,
        "n_predict": 300,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": args.seed,
        "json_schema": SCHEMA,
    }
    started = time.monotonic()
    response = requests.post(f"{args.base_url.rstrip('/')}/completion", json=payload, timeout=(10, 180))
    response.raise_for_status()
    body = response.json()
    wall = time.monotonic() - started
    content = body.get("content", "")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        result = {"ok": False, "error": str(exc), "raw_content": content, "body": body, "wall_seconds": round(wall, 3)}
    else:
        field = parsed.get("field", {}) if isinstance(parsed, dict) else {}
        errors = []
        if field.get("id") != "field001": errors.append("id mismatch")
        if field.get("unknown_exit", {}).get("destination") is not None: errors.append("unknown_exit.destination is not null")
        if field.get("return_exit", {}).get("destination") != "field000": errors.append("return_exit.destination mismatch")
        for key in ("primary_object", "secondary_object"):
            if field.get(key, {}).get("affordance") not in {"observe", "touch", "move", "remember"}: errors.append(f"{key}.affordance invalid")
        result = {
            "ok": not errors,
            "errors": errors,
            "parsed": parsed,
            "tokens_predicted": body.get("tokens_predicted"),
            "tokens_evaluated": body.get("tokens_evaluated"),
            "tokens_per_second": round((body.get("tokens_predicted") or 0) / wall, 3) if wall > 0 else None,
            "wall_seconds": round(wall, 3),
        }
    raw = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(raw + "\n", encoding="utf-8")
    print(raw)
    return 0 if result.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
