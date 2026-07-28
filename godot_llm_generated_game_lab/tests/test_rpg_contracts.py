#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
import rpg_content as rpg
import generated_object_service as service

assert sorted(rpg.SCHEMAS) == ["armor", "consumable", "loot", "player", "weapon"]
for kind, schema in rpg.SCHEMAS.items():
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])

player_idea = "beginner athletic warrior with short dark brown hair, steel-gray chainmail, muted red cloth accents, one sword, empty off hand, no shield, no cape, no backpack"
player_schema = rpg.schema_for_request("player", player_idea)
expected = {
    "role": "warrior", "experience_level": "beginner", "body_type": "athletic",
    "hair_color": "dark brown", "hair_style": "short", "armor_style": "chainmail",
    "armor_primary_color": "steel gray", "armor_secondary_color": "muted red",
    "main_hand": "sword", "off_hand": "none", "back_item": "none",
}
for field, value in expected.items():
    assert player_schema["properties"][field]["enum"] == [value]

valid_player = {
    "name": "Road Warden", "role": "warrior", "experience_level": "beginner", "presentation": "androgynous",
    "body_type": "athletic", "hair_color": "dark brown", "hair_style": "short",
    "face_description": "A square face with a calm and attentive expression",
    "armor_style": "chainmail", "armor_primary_color": "steel gray", "armor_secondary_color": "muted red",
    "main_hand": "sword", "off_hand": "none", "back_item": "none",
    "description": "A newly trained road warrior wears practical chainmail and carries one plain sword.",
    "visual_description": "An athletic adult with short dark brown hair wears steel-gray chainmail, muted red cloth, brown leather boots, and one plain steel sword.",
    "idle_style": "guarded", "movement_style": "steady",
}
Draft202012Validator(player_schema).validate(valid_player)
assert rpg.validate_plan_semantics("player", valid_player) == []
assert rpg.validate_request_adherence("player", valid_player, player_idea) == []
compiled_player = rpg.compile_player(valid_player)
assert compiled_player["stats"]["max_hp"] == 120
assert compiled_player["actions"] == {"basic_attack": "slash", "secondary_action": "parry", "mobility_action": "jump"}
assert compiled_player["equipment"]["off_hand"] == "none"
assert compiled_player["asset"]["structural_prompt"]
assert compiled_player["asset"]["review_requirements"]

bad_player = dict(valid_player)
bad_player["description"] = "A seasoned elite veteran warrior wears chainmail and carries one sword."
assert rpg.validate_plan_semantics("player", bad_player)
assert any("beginner" in error for error in rpg.validate_plan_semantics("player", bad_player))
extra = dict(valid_player)
extra["forbidden"] = True
try:
    Draft202012Validator(player_schema).validate(extra)
except ValidationError:
    pass
else:
    raise AssertionError("additionalProperties:false accepted an extra player field")

weapon_plan = {
    "name": "Road Sword", "weapon_type": "sword", "handedness": "one_handed", "material": "steel",
    "quality": "well_made", "description": "A reliable steel longsword for a newly trained warrior.",
    "visual_description": "A straight steel sword has a plain crossguard, brown leather grip, and small round pommel.",
    "display_style": "still",
}
assert rpg.validate_plan_semantics("weapon", weapon_plan) == []
weapon = rpg.compile_weapon(weapon_plan)
assert weapon["stats"] == {"damage": 12, "speed": 10, "range": 2}
assert weapon["actions"] == {"primary": "slash", "secondary": "parry"}
assert "No sheath" in weapon["asset"]["review_requirements"]

manifest = json.loads((ROOT / "data/rpg_content.json").read_text())
for entry in [manifest["player"], *manifest["world_items"]]:
    payload = service.rpg_thor_payload(entry["content"])
    assert set(payload) == {"kind", "name", "structural_prompt", "semantic_prompt", "negative_prompt", "animation_description", "expected_labels", "review_requirements"}
    assert payload["structural_prompt"] and payload["semantic_prompt"] and payload["review_requirements"]

assert service.validate_assets(
    (ROOT / manifest["world_items"][0]["asset"]["png_path"].removeprefix("res://")).read_bytes(),
    (ROOT / manifest["world_items"][0]["asset"]["gif_path"].removeprefix("res://")).read_bytes(),
    (ROOT / manifest["world_items"][0]["asset"]["sheet_path"].removeprefix("res://")).read_bytes(),
    {"frame_count": 6, "frame_width": 160, "frame_height": 160},
)["validated"] is True
print("grounded_rpg_contracts ok")
