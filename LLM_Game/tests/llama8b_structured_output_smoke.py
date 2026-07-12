#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import requests

PORTABLE_FIELD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["field"],
    "properties": {
        "field": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "name", "description", "objects", "exits"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "description", "affordances"],
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "affordances": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "exits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "direction", "description", "destination"],
                        "properties": {
                            "name": {"type": "string"},
                            "direction": {"type": "string"},
                            "description": {"type": "string"},
                            "destination": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        },
                    },
                },
            },
        }
    },
}

PROMPT = """Create one compact perception-oriented game field as JSON only.
The player stands at the boundary between known reality and an unknown semantic space.
Return a field with id field001, two objects, and two exits. One exit must have destination null.
"""


def call_completion(base_url: str, *, schema: dict[str, Any], seed: int) -> tuple[dict[str, Any], float]:
    payload = {
        "prompt": PROMPT,
        "n_predict": 360,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": seed,
        "json_schema": schema,
    }
    started = time.monotonic()
    response = requests.post(f"{base_url.rstrip('/')}/completion", json=payload, timeout=(10, 180))
    response.raise_for_status()
    return response.json(), time.monotonic() - started


def validate_shape(obj: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    field = obj.get("field")
    if not isinstance(field, dict):
        return ["top-level field is missing or not an object"]
    for key in ["id", "name", "description", "objects", "exits"]:
        if key not in field:
            errors.append(f"missing field.{key}")
    if field.get("id") != "field001":
        errors.append(f"expected field.id field001, got {field.get('id')!r}")
    if not isinstance(field.get("objects"), list) or len(field.get("objects", [])) != 2:
        errors.append("expected exactly two objects")
    if not isinstance(field.get("exits"), list) or len(field.get("exits", [])) != 2:
        errors.append("expected exactly two exits")
    exits = field.get("exits") if isinstance(field.get("exits"), list) else []
    if not any(isinstance(exit_item, dict) and exit_item.get("destination") is None for exit_item in exits):
        errors.append("expected at least one unresolved exit with destination null")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:14829")
    parser.add_argument("--output", default="")
    parser.add_argument("--seed", type=int, default=20260705)
    args = parser.parse_args()

    body, wall = call_completion(args.base_url, schema=PORTABLE_FIELD_SCHEMA, seed=args.seed)
    content = body.get("content", "")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        result = {
            "ok": False,
            "error": f"json parse failed: {exc}",
            "raw_content": content,
            "llama_body": body,
            "wall_seconds": round(wall, 3),
        }
    else:
        errors = validate_shape(parsed)
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
