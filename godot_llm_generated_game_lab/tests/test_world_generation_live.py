#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
import world_generation as world

CASES = [
    ("medieval-rpg", "RPG medieval game"),
    ("hostile-fragment", "fuck you"),
    ("your-mom", "Your Mom"),
    ("cyberpunk-mega-blaster", "An RPG game with cyberpunk elements. The player carries a super mega blaster weapon that is exactly 2.3 meters long and produces 32 gigawatts of power. The blaster has a matte black titanium body, three cyan cooling rings, a shoulder brace, and a dangerous overcharge mode. Keep all of these details."),
    ("odd-associations", "a broken umbrella, the smell of cinnamon, and Tuesday at 4:17 AM"),
    ("peaceful-constraint", "A quiet cooperative gardening game on floating islands with no combat, where rainwater is currency and every plant remembers who cared for it."),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=len(CASES))
    parser.add_argument("--full-pipeline", type=int, default=1)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/world_generation_samples/2026-07-27")
    parser.add_argument("--design-tokens", type=int, default=760)
    parser.add_argument("--scene-tokens", type=int, default=760)
    parser.add_argument("--plan-tokens", type=int, default=1800)
    args = parser.parse_args()
    summaries: list[dict[str, object]] = []
    failures = 0
    selected = CASES[args.start:args.start + args.limit]
    for offset, (label, user_prompt) in enumerate(selected):
        index = args.start + offset
        started = time.monotonic()
        try:
            game_description, design_meta = world.generate_game_description(user_prompt, seed=270727 + index * 10, max_tokens=args.design_tokens)
            opening_scene = None
            scene_plan = None
            metadata: dict[str, object] = {"game_description": design_meta}
            if offset < args.full_pipeline:
                opening_scene, scene_meta = world.generate_opening_scene(game_description, user_prompt, seed=270728 + index * 10, max_tokens=args.scene_tokens)
                scene_plan, plan_meta = world.generate_scene_plan(user_prompt, game_description, opening_scene, seed=270729 + index * 10, max_tokens=args.plan_tokens)
                metadata["opening_scene"] = scene_meta
                metadata["scene_plan"] = plan_meta
            target = world.save_generation_bundle(args.output, label, user_prompt, game_description, opening_scene, scene_plan, metadata)
            summary = {
                "label": label,
                "ok": True,
                "title": world.extract_title(game_description),
                "category": world.extract_category(game_description),
                "description_chars": len(game_description),
                "scene_chars": len(opening_scene) if opening_scene else None,
                "objects": len(scene_plan["objects"]) if scene_plan else None,
                "seconds": round(time.monotonic() - started, 3),
                "file": str(target.resolve().relative_to(ROOT.resolve())) if target.resolve().is_relative_to(ROOT.resolve()) else str(target.resolve()),
                "fallback": False,
            }
        except Exception as exc:
            failures += 1
            args.output.mkdir(parents=True, exist_ok=True)
            error_target = args.output / f"{label}.error.json"
            error_target.write_text(json.dumps({"label": label, "user_prompt": user_prompt, "error": f"{type(exc).__name__}: {exc}", "fallback": False}, ensure_ascii=False, indent=2) + "\n")
            summary = {
                "label": label,
                "ok": False,
                "seconds": round(time.monotonic() - started, 3),
                "error": f"{type(exc).__name__}: {exc}",
                "file": str(error_target),
                "fallback": False,
            }
        summaries.append(summary)
        print(json.dumps(summary, ensure_ascii=False), flush=True)
    print(json.dumps({"ok": failures == 0, "failures": failures, "cases": summaries, "author_model": world.AUTHOR_MODEL_ID, "structure_model": world.STRUCTURE_MODEL_ID}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
