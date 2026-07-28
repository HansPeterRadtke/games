#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "data/rpg_content.json").read_text())
assert manifest["version"] == 2
assert "grounded medieval fantasy RPG" in manifest["game_description"]
assert not (ROOT / "assets/generated").exists()
assert not (ROOT / "assets/generated_objects").exists()
assert not (ROOT / "data/bootstrap_objects.json").exists()

player = manifest["player"]
assert player["kind"] == "player"
content = player["content"]
assert content["kind"] == "player_character"
assert content["name"] == "Eryndor Thorne"
assert content["role"] == "warrior"
assert content["experience_level"] == "beginner"
assert content["level"] == 1
assert content["stats"]["max_hp"] == 120 and content["stats"]["hp"] == 120
assert content["stats"]["max_stamina"] == 90 and content["stats"]["defense"] == 12
assert content["equipment"]["main_hand"] == "sword"
assert content["equipment"]["off_hand"] == "none"
assert content["equipment"]["chest"] == "chainmail"
assert content["actions"] == {"basic_attack": "slash", "secondary_action": "parry", "mobility_action": "jump"}
player_semantics = (content["description"] + " " + content["appearance"]["visual_description"]).casefold()
assert "chainmail" in player_semantics
assert "sword" in player_semantics

items = manifest["world_items"]
assert [entry["kind"] for entry in items] == ["weapon", "armor", "loot", "consumable"]
assert [entry["spawn_x"] for entry in items] == [620.0, 900.0, 1200.0, 1500.0]
by_kind = {entry["kind"]: entry for entry in items}
weapon = by_kind["weapon"]["content"]
assert weapon["weapon_type"] == "sword" and weapon["material"] == "steel"
assert weapon["handedness"] == "one_handed" and weapon["equip_slot"] == "main_hand"
assert weapon["actions"] == {"primary": "slash", "secondary": "parry"}
assert weapon["stats"] == {"damage": 12, "speed": 10, "range": 2}
assert "sheath" not in weapon["asset"]["review_requirements"].casefold().replace("no sheath", "")
armor = by_kind["armor"]["content"]
assert armor["armor_slot"] == "chest" and armor["material"] == "chainmail"
assert armor["armor_weight"] == "medium" and armor["equip_slot"] == "chest"
assert armor["stats"] == {"defense": 8, "weight": 7, "speed_modifier": 0}
loot = by_kind["loot"]["content"]
assert loot["loot_type"] == "treasure_chest" and loot["material"] == "oak"
assert loot["interaction"] == "open" and loot["rarity"] == "common"
consumable = by_kind["consumable"]["content"]
assert consumable["consumable_type"] == "health_potion"
assert consumable["container"] == "glass_bottle" and consumable["primary_color"] == "red"
assert consumable["effect"] == {"stat": "health", "amount": 25}

for entry in [player, *items]:
    kind = entry["kind"]
    asset = entry["asset"]
    expected_frames = 8 if kind == "player" else 6
    expected_size = (192, 256) if kind == "player" else (160, 160)
    assert asset["engine"] == "sdxl-base-canonical+sdxl-img2img-animation"
    assert asset["identity_anchored"] is True and asset["motion_generated"] is True
    assert asset["frame_count"] == expected_frames
    assert (asset["frame_width"], asset["frame_height"]) == expected_size
    assert asset["distinct_frames"] == expected_frames
    assert asset["canonical_review"]["deterministic_pass"] is True
    assert asset["canonical_review"]["critical_defects"] == []
    assert asset["mid_frame_review"]["deterministic_pass"] is True
    assert asset["mid_frame_review"]["critical_defects"] == []
    paths = {name: ROOT / asset[f"{name}_path"].removeprefix("res://") for name in ["png", "gif", "sheet"]}
    for path in paths.values():
        assert path.is_file() and path.stat().st_size > 0
    with Image.open(paths["png"]) as image:
        assert image.mode == "RGBA" and image.size == expected_size
        assert image.getchannel("A").getextrema() == (0, 255)
    gif_hashes: list[str] = []
    with Image.open(paths["gif"]) as image:
        assert image.n_frames == expected_frames and image.info.get("loop") == 0
        for index in range(image.n_frames):
            image.seek(index)
            frame = image.convert("RGBA")
            assert frame.getchannel("A").getextrema() == (0, 255)
            gif_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
    assert len(set(gif_hashes)) == expected_frames
    sheet_hashes: list[str] = []
    with Image.open(paths["sheet"]) as image:
        assert image.mode == "RGBA"
        assert image.size == (expected_size[0] * expected_frames, expected_size[1])
        assert image.getchannel("A").getextrema() == (0, 255)
        for index in range(expected_frames):
            frame = image.crop((index * expected_size[0], 0, (index + 1) * expected_size[0], expected_size[1]))
            sheet_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
    assert len(set(sheet_hashes)) == expected_frames

serialized = json.dumps(manifest, ensure_ascii=False).casefold()
for forbidden in ["nourishing ruby red apple", "glint", "trailguide", "wan2.1-t2v"]:
    assert forbidden not in serialized, forbidden
positive_semantics = " ".join([
    content["description"], content["appearance"]["visual_description"],
    *[entry["content"]["description"] for entry in items],
    *[entry["content"]["asset"]["semantic_prompt"] for entry in items],
]).casefold()
for forbidden in ["surreal", "whimsical", "psychedelic", "cosmic", "abstract creature"]:
    assert forbidden not in positive_semantics, forbidden
for entry in [player, *items]:
    assert "surreal" in entry["content"]["asset"]["negative_prompt"].casefold()
assert len(list((ROOT / "assets/rpg").glob("*.gif"))) == 6

walk_prefix = ROOT / "assets/rpg/player-eryndor-thorne-8eb300d6eb2c.walk"
for suffix in [".png", ".gif", ".sheet.png", ".json"]:
    assert Path(str(walk_prefix) + suffix).is_file(), suffix
walk_meta = json.loads(Path(str(walk_prefix) + ".json").read_text())
assert walk_meta["frame_count"] == 8
assert walk_meta["frame_width"] == 192 and walk_meta["frame_height"] == 256
assert walk_meta["adjacent_min"] >= 15.0
assert walk_meta["engine"] == "sdxl-controlnet-openpose-img2img-walk-v1"
assert len(list((ROOT / "assets/rpg").glob("*.sheet.png"))) == 6
print(json.dumps({"ok": True, "player": content["name"], "items": [entry["content"]["name"] for entry in items], "reviewed_frames": 32, "old_assets_absent": True}, sort_keys=True))
