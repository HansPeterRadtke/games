#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
import world_generation as world

CASES = {
    "sparse": "RPG medieval game",
    "hostile": "fuck you",
    "title": "Your Mom",
    "detailed": "An RPG game with cyberpunk elements, a super mega blaster exactly 2.3 meters long with 32 gigawatts of power, a matte black titanium body, three cyan cooling rings, a shoulder brace, and a dangerous overcharge mode.",
    "odd": "a broken umbrella, the smell of cinnamon, and Tuesday at 4:17 AM",
}
for name, prompt in CASES.items():
    fragments = world.required_source_fragments(prompt)
    assert fragments
    schema = world.scene_plan_schema(prompt)
    Draft202012Validator.check_schema(schema)
    trace = schema["properties"]["source_trace"]
    assert trace["minItems"] == trace["maxItems"] == len(fragments)
    assert trace["items"]["properties"]["detail"]["enum"] == fragments
    if name == "title":
        assert world.explicit_title_hint(prompt) == "Your Mom"
    if name == "detailed":
        assert fragments == [
            "An RPG game", "cyberpunk elements", "a super mega blaster exactly 2.3 meters long",
            "32 gigawatts of power", "a matte black titanium body", "three cyan cooling rings",
            "a shoulder brace", "a dangerous overcharge mode",
        ]


semantic_output = """An RPG game set in a city with cyberpunk elements. The hero uses a super mega blaster weapon. It is exactly 2.3 meters long and produces 32 gigawatts of power. The blaster has a matte black titanium body, three cyan cooling rings, a shoulder brace, and a dangerous overcharge mode."""
assert world.detail_preservation_errors(semantic_output, CASES["detailed"], "test") == []
assert "Keep all of these details" not in world.required_source_fragments(CASES["detailed"])
missing_output = semantic_output.replace("three cyan cooling rings", "cooling hardware")
missing_errors = world.detail_preservation_errors(missing_output, CASES["detailed"], "test")
assert any("cyan" in error and "ring" in error for error in missing_errors)
peaceful_paraphrase = "A quiet cooperative garden grows across float islands. There is no combat. Rainwater serves as currency, and every plant can remember the care it received."
assert world.detail_preservation_errors(peaceful_paraphrase, "A quiet cooperative gardening game on floating islands with no combat, where rainwater is currency and every plant remembers who cared for it.", "test") == []
assert world.detail_preservation_errors("Your mother waits in the dining room.", "Your Mom", "test") == []

sample_prompt = CASES["detailed"]
sample_description = """Neon Siege
A cyberpunk role-playing game.

The player enters a dense cyberpunk city and carries a super mega blaster exactly 2.3 meters long with 32 gigawatts of power. The weapon has a matte black titanium body, three cyan cooling rings, a shoulder brace, and a dangerous overcharge mode. The city changes as factions react to the weapon, and progression unlocks political alliances, safer cooling systems, and increasingly dangerous districts. The central conflict concerns control of an energy network that can either stabilize the city or turn every district into a weapon. Combat, investigation, traversal, equipment maintenance, dialogue, and faction reputation shape every mission. The visual identity combines wet black streets, cyan industrial light, brutal megastructures, and readable silhouettes, while the audio uses transformer hum, rain, distant public announcements, and the heavy mechanical report of the blaster.
The core gameplay loop works as follows.
Explore contested districts, investigate faction objectives, and locate routes through vertical infrastructure.
Use the blaster carefully, manage heat and overcharge risk, and survive reactive combat encounters.
Negotiate alliances, upgrade equipment, and change which factions control services and territory.
Return to transformed districts where prior choices produce new enemies, allies, hazards, and opportunities.
Source fidelity is explicit.
"An RPG game" is implemented through character progression, equipment, dialogue, quests, and faction reputation.
"cyberpunk elements" define the city, technology, corporations, lighting, social conflict, and augmentation systems.
"a super mega blaster exactly 2.3 meters long" is the player's signature weapon and its full measurement affects traversal and handling.
"32 gigawatts of power" is the weapon's dangerous peak output and the basis of its heat system.
"a matte black titanium body" defines the weapon material and image-generation requirements.
"three cyan cooling rings" are visible functional parts that animate as heat rises.
"a shoulder brace" is required for aiming and changes the player's silhouette.
"a dangerous overcharge mode" is a high-risk mechanic that can alter missions and damage the environment.
The description is complete."""
assert world.validate_game_description(sample_description, sample_prompt) == []
assert world.extract_title(sample_description) == "Neon Siege"
assert world.extract_category(sample_description) == ""

sample_scene = """Rainline Customs Yard

The player stands beneath a leaking customs canopy with a super mega blaster exactly 2.3 meters long locked into a shoulder brace.

Rain falls through cyan work lights onto a matte black titanium body of cargo machinery and flooded lanes. Three cyan cooling rings on the weapon pulse beside stacked containers, maintenance gantries, power conduits, and a customs tower. The wider city presents cyberpunk elements through vertical transit rails, corporate warning projections, crowded service balconies, and distant megastructures. A transformer station ahead carries 32 gigawatts of power and feeds unstable arcs into the yard. Steam moves across the ground, security drones sweep their lamps over the containers, and workers hide behind armored shutters while alarms echo between steel walls.

a dangerous overcharge mode has armed itself after the customs grid mistakes the player for an illegal power source, and a drone squad is closing from the eastern gate.

The north gantry reaches the customs tower, the western drainage tunnel leads below the yard, and the eastern gate opens toward the first inhabited district.
Source details remain visible in the scene.
An RPG game begins with a choice between negotiation, stealth, combat, and technical intervention. The cyberpunk elements are visible in every active system. The matte black titanium body, three cyan cooling rings, and a shoulder brace are all visible on the signature weapon.
The opening environment is ready for play."""
assert world.validate_opening_scene(sample_scene, sample_prompt) == []


def fixture_action(owner_id: str, trigger: str) -> dict:
    return {
        "id": f"{owner_id}_{trigger}",
        "input": trigger,
        "label": trigger.title(),
        "description": f"The generated {trigger} action changes executable object state.",
        "range_meters": 0.5 if trigger == "touch" else 1.5,
        "cooldown_seconds": 0.1,
        "conditions": [],
        "effects": [{"type": "set_state", "target_id": owner_id, "key": f"last_{trigger}", "value": "completed"}],
        "actor_clip": f"player_{trigger}",
        "actor_animation_prompt": f"The complete player performs a clearly visible {trigger} motion and returns to the starting pose.",
        "target_clip": f"{owner_id}_{trigger}",
        "target_animation_prompt": f"The complete target visibly reacts to {trigger} contact and returns to its starting pose.",
        "success_text": f"The {trigger} action succeeds.",
    }


compact_plan = {
    "scene_id": "test_room", "scene_name": "Test Room", "units": "meters", "visual_generator": "thor_sdxl",
    "bounds": {"min": [-5, 0, -5], "max": [5, 4, 5]},
    "gameplay": {
        "objective": "Interact with the generated room objects and complete the test objective.",
        "win_conditions": ["Complete at least one generated interaction successfully."],
        "lose_conditions": ["Health reaches zero before completing an interaction."],
        "available_inputs": ["move", "touch", "interact", "attack", "use"],
        "stats": [
            {"id": "health", "label": "Health", "initial": 100, "minimum": 0, "maximum": 100},
            {"id": "stamina", "label": "Stamina", "initial": 100, "minimum": 0, "maximum": 100},
        ],
        "starting_inventory": [],
    },
    "player": {
        "id": "adult_child", "name": "Adult Child", "description": "An exhausted adult child trying to escape the oppressive household routine.",
        "position": [0, 1, 3], "yaw_degrees": 0, "facing": "toward the table", "size": [0.6, 1.8, 0.6],
        "collision": "capsule", "visual_usage": "character_sprite",
        "asset_prompt": "full body exhausted adult child in plain suburban clothes, readable side view, clean white background",
        "animation": "restless breathing and small anxious weight shifts",
        "actions": [fixture_action("adult_child", trigger) for trigger in ["interact", "hit", "use"]],
    },
    "objects": [
        {
            "id": f"object_{i}", "type": "static_prop", "name": f"Object {i}",
            "description": "A visible test object in the room", "position": [i - 3, 0, 0], "yaw_degrees": 0,
            "size": [1, 1, 1], "collision": "box", "mobility": "static", "visual_usage": "isolated_sprite",
            "asset_prompt": "clean detailed household object front view", "animation": "subtle idle motion",
            "actions": [fixture_action(f"object_{i}", trigger) for trigger in ["touch", "interact", "hit"]],
        }
        for i in range(6)
    ],
    "exits": [{"id": "door_exit", "position": [4, 0, 0], "direction": "east", "next_environment": "A connected hallway beyond the room"}],
    "source_trace": [{"detail": "Your Mom", "object_ids": ["object_0"], "implementation": "The first object represents the mother-themed source detail clearly."}],
}
assert world.validate_scene_plan(compact_plan, "Your Mom") == []


invalid_plan = json.loads(json.dumps(compact_plan))
invalid_plan["objects"][0]["position"] = [99, 0, 0]
invalid_plan["objects"][1]["type"] = "light"
invalid_plan["objects"][1]["visual_usage"] = "none"
invalid_plan["objects"][1]["asset_prompt"] = "none"
invalid_plan["source_trace"][0]["implementation"] = "none}, {id:"
invalid_errors = world.validate_scene_plan(invalid_plan, "Your Mom")
assert any("outside scene bounds" in error for error in invalid_errors)
assert any("visible object object_1 has no visual usage" in error for error in invalid_errors)
assert any("malformed or incomplete implementation" in error for error in invalid_errors)


usage_plan = json.loads(json.dumps(compact_plan))
usage_plan["objects"][0]["type"] = "npc"
usage_plan["objects"][0]["visual_usage"] = "isolated_sprite"
usage_errors = world.validate_scene_plan(usage_plan, "Your Mom")
assert any("requires one of" in error and "character_sprite" in error for error in usage_errors)
overlap_plan = json.loads(json.dumps(compact_plan))
overlap_plan["player"]["position"] = overlap_plan["objects"][0]["position"]
overlap_errors = world.validate_scene_plan(overlap_plan, "Your Mom")
assert any("intersects collidable object" in error for error in overlap_errors)
incomplete_trace = json.loads(json.dumps(compact_plan))
incomplete_trace["source_trace"][0]["implementation"] = "The mother controls the"
trace_errors = world.validate_scene_plan(incomplete_trace, "Your Mom")
assert any("incomplete implementation" in error for error in trace_errors)


support_plan = json.loads(json.dumps(compact_plan))
support_plan["objects"][0]["type"] = "surface"
support_plan["objects"][0]["visual_usage"] = "tileable_texture"
support_plan["objects"][0]["position"] = support_plan["player"]["position"]
support_errors = world.validate_scene_plan(support_plan, "Your Mom")
assert not any("intersects collidable object object_0" in error for error in support_errors)


no_animation_plan = json.loads(json.dumps(compact_plan))
no_animation_plan["objects"][0]["animation"] = "none"
no_animation_errors = world.validate_scene_plan(no_animation_plan, "Your Mom")
assert any("lacks a concrete generated animation description" in error for error in no_animation_errors)


background_prop = json.loads(json.dumps(compact_plan))
background_prop["objects"][0]["visual_usage"] = "background_layer"
background_prop["objects"][0]["asset_prompt"] = "opaque full-frame curtain wall layer with stable dark fabric folds"
assert world.validate_scene_plan(background_prop, "Your Mom") == []

assert world.SCENE_PLAN_SCHEMA["additionalProperties"] is False
source = (ROOT / "server/world_generation.py").read_text()
assert "json_schema" in source
assert '"schema_constrained": False' in source
assert '"schema_constrained": True' in source
assert "real author-model generation failed; no fallback was used" in source
assert "real structure-model generation failed; no fallback was used" in source
assert '"fallback_used": False' in source
assert "freely invent every missing game detail" in world.GAME_DESCRIPTION_SYSTEM_PROMPT
assert "Do not reject" in world.GAME_DESCRIPTION_SYSTEM_PROMPT
assert "thor_sdxl" in world.SCENE_PLAN_SYSTEM_PROMPT

service_source = (ROOT / "server/generated_object_service.py").read_text()
for endpoint in ["/object/world/design", "/object/world/scene", "/object/world/plan", "/object/world/contracts"]:
    assert endpoint in service_source
print(json.dumps({"ok": True, "cases": list(CASES), "author_model": world.AUTHOR_MODEL_ID, "structure_model": world.STRUCTURE_MODEL_ID, "fallback": False}, sort_keys=True))
