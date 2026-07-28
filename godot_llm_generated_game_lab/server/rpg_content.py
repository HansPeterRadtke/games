from __future__ import annotations

import json
import re
import time
from typing import Any, Callable

from jsonschema import Draft202012Validator

GAME_DESCRIPTION = (
    "A grounded medieval fantasy role-playing game with standard recognizable equipment, "
    "practical steel, iron, wood, leather, chainmail, cloth, stone, glass, and ceramic materials. "
    "Objects use realistic proportions and construction. No surreal forms, abstract creatures, "
    "ornamental overload, or magical effects unless the selected item type explicitly requires them."
)

PLAYER_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 2, "maxLength": 36},
        "role": {"type": "string", "enum": ["warrior", "ranger", "rogue", "mage", "cleric"]},
        "experience_level": {"type": "string", "enum": ["beginner", "trained", "veteran"]},
        "presentation": {"type": "string", "enum": ["masculine", "feminine", "androgynous"]},
        "body_type": {"type": "string", "enum": ["slim", "average", "athletic", "heavy"]},
        "hair_color": {"type": "string", "enum": ["black", "dark brown", "chestnut", "auburn", "blond", "gray"]},
        "hair_style": {"type": "string", "enum": ["short", "shoulder length", "braided", "cropped", "tied back"]},
        "face_description": {"type": "string", "minLength": 12, "maxLength": 90},
        "armor_style": {"type": "string", "enum": ["leather", "chainmail", "plate", "robe"]},
        "armor_primary_color": {"type": "string", "enum": ["dark brown", "black", "steel gray", "charcoal", "undyed linen", "navy"]},
        "armor_secondary_color": {"type": "string", "enum": ["muted red", "cream", "dark blue", "brown", "gray", "burgundy"]},
        "main_hand": {"type": "string", "enum": ["sword", "axe", "spear", "dagger", "bow", "mace", "staff"]},
        "off_hand": {"type": "string", "enum": ["round_shield", "kite_shield", "dagger", "none"]},
        "back_item": {"type": "string", "enum": ["cape", "quiver", "backpack", "none"]},
        "description": {"type": "string", "minLength": 80, "maxLength": 180, "pattern": "^.*[.!?]$"},
        "visual_description": {"type": "string", "minLength": 110, "maxLength": 240, "pattern": "^.*[.!?]$"},
        "idle_style": {"type": "string", "enum": ["relaxed", "guarded", "alert"]},
        "movement_style": {"type": "string", "enum": ["steady", "agile", "heavy"]}
    },
    "required": [
        "name", "role", "experience_level", "presentation", "body_type", "hair_color", "hair_style", "face_description",
        "armor_style", "armor_primary_color", "armor_secondary_color", "main_hand", "off_hand", "back_item",
        "description", "visual_description", "idle_style", "movement_style"
    ],
    "additionalProperties": False
}

WEAPON_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 2, "maxLength": 50},
        "weapon_type": {"type": "string", "enum": ["sword", "axe", "spear", "dagger", "bow", "mace", "staff"]},
        "handedness": {"type": "string", "enum": ["one_handed", "two_handed"]},
        "material": {"type": "string", "enum": ["steel", "iron", "bronze", "oak", "ash wood"]},
        "quality": {"type": "string", "enum": ["common", "well_made", "fine"]},
        "description": {"type": "string", "minLength": 30, "maxLength": 170, "pattern": "^.*[.!?]$"},
        "visual_description": {"type": "string", "minLength": 60, "maxLength": 230, "pattern": "^.*[.!?]$"},
        "display_style": {"type": "string", "enum": ["still", "restrained_highlight"]}
    },
    "required": ["name", "weapon_type", "handedness", "material", "quality", "description", "visual_description", "display_style"],
    "additionalProperties": False
}

ARMOR_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 2, "maxLength": 50},
        "armor_slot": {"type": "string", "enum": ["head", "chest", "hands", "legs", "feet", "back"]},
        "armor_weight": {"type": "string", "enum": ["light", "medium", "heavy"]},
        "material": {"type": "string", "enum": ["cloth", "leather", "chainmail", "steel_plate", "iron_plate"]},
        "primary_color": {"type": "string", "enum": ["dark brown", "black", "steel gray", "charcoal", "cream", "burgundy"]},
        "quality": {"type": "string", "enum": ["common", "well_made", "fine"]},
        "description": {"type": "string", "minLength": 30, "maxLength": 170, "pattern": "^.*[.!?]$"},
        "visual_description": {"type": "string", "minLength": 60, "maxLength": 230, "pattern": "^.*[.!?]$"},
        "display_style": {"type": "string", "enum": ["hanging", "laid_flat"]}
    },
    "required": ["name", "armor_slot", "armor_weight", "material", "primary_color", "quality", "description", "visual_description", "display_style"],
    "additionalProperties": False
}

LOOT_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 2, "maxLength": 50},
        "loot_type": {"type": "string", "enum": ["treasure_chest", "coin_pouch", "gem", "relic", "key_item"]},
        "material": {"type": "string", "enum": ["oak", "iron", "steel", "bronze", "leather", "velvet", "crystal"]},
        "rarity": {"type": "string", "enum": ["common", "uncommon", "rare"]},
        "contents_hint": {"type": "string", "enum": ["gold", "equipment", "potion", "key", "mixed"]},
        "description": {"type": "string", "minLength": 30, "maxLength": 170, "pattern": "^.*[.!?]$"},
        "visual_description": {"type": "string", "minLength": 60, "maxLength": 230, "pattern": "^.*[.!?]$"},
        "display_style": {"type": "string", "enum": ["still", "restrained_highlight"]},
        "open_style": {"type": "string", "enum": ["hinged_lid", "collect_vanish"]}
    },
    "required": ["name", "loot_type", "material", "rarity", "contents_hint", "description", "visual_description", "display_style", "open_style"],
    "additionalProperties": False
}

CONSUMABLE_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 2, "maxLength": 50},
        "consumable_type": {"type": "string", "enum": ["health_potion", "mana_potion", "antidote", "food"]},
        "container": {"type": "string", "enum": ["glass_bottle", "ceramic_flask", "cloth_wrap", "wooden_bowl"]},
        "primary_color": {"type": "string", "enum": ["red", "blue", "amber", "clear", "brown", "cream"]},
        "quality": {"type": "string", "enum": ["common", "well_made", "fine"]},
        "description": {"type": "string", "minLength": 30, "maxLength": 170, "pattern": "^.*[.!?]$"},
        "visual_description": {"type": "string", "minLength": 60, "maxLength": 230, "pattern": "^.*[.!?]$"},
        "display_style": {"type": "string", "enum": ["still", "restrained_highlight"]}
    },
    "required": ["name", "consumable_type", "container", "primary_color", "quality", "description", "visual_description", "display_style"],
    "additionalProperties": False
}

SCHEMAS = {
    "player": PLAYER_PLAN_SCHEMA,
    "weapon": WEAPON_PLAN_SCHEMA,
    "armor": ARMOR_PLAN_SCHEMA,
    "loot": LOOT_PLAN_SCHEMA,
    "consumable": CONSUMABLE_PLAN_SCHEMA,
}

ROLE_STATS = {
    "warrior": {"max_hp": 120, "max_stamina": 90, "max_mana": 10, "strength": 14, "dexterity": 9, "intelligence": 5, "defense": 12, "speed": 8},
    "ranger": {"max_hp": 90, "max_stamina": 110, "max_mana": 20, "strength": 9, "dexterity": 14, "intelligence": 7, "defense": 8, "speed": 12},
    "rogue": {"max_hp": 85, "max_stamina": 115, "max_mana": 15, "strength": 8, "dexterity": 15, "intelligence": 8, "defense": 7, "speed": 14},
    "mage": {"max_hp": 65, "max_stamina": 65, "max_mana": 120, "strength": 4, "dexterity": 7, "intelligence": 16, "defense": 4, "speed": 8},
    "cleric": {"max_hp": 95, "max_stamina": 75, "max_mana": 80, "strength": 9, "dexterity": 7, "intelligence": 12, "defense": 10, "speed": 7},
}

WEAPON_RULES = {
    "sword": {"damage_type": "slash", "primary": "slash", "secondary": "parry", "slot": "main_hand", "damage": 12, "speed": 10, "range": 2},
    "axe": {"damage_type": "slash", "primary": "chop", "secondary": "power_attack", "slot": "main_hand", "damage": 15, "speed": 7, "range": 2},
    "spear": {"damage_type": "pierce", "primary": "thrust", "secondary": "brace", "slot": "two_hands", "damage": 13, "speed": 8, "range": 4},
    "dagger": {"damage_type": "pierce", "primary": "stab", "secondary": "throw", "slot": "main_hand", "damage": 8, "speed": 15, "range": 1},
    "bow": {"damage_type": "ranged", "primary": "shoot", "secondary": "aim", "slot": "two_hands", "damage": 11, "speed": 9, "range": 8},
    "mace": {"damage_type": "blunt", "primary": "bash", "secondary": "power_attack", "slot": "main_hand", "damage": 14, "speed": 7, "range": 2},
    "staff": {"damage_type": "magic", "primary": "cast", "secondary": "focus", "slot": "two_hands", "damage": 10, "speed": 8, "range": 6},
}

ARMOR_RULES = {
    "light": {"defense": 4, "weight": 3, "speed_modifier": 1},
    "medium": {"defense": 8, "weight": 7, "speed_modifier": 0},
    "heavy": {"defense": 13, "weight": 12, "speed_modifier": -2},
}

FORBIDDEN_STYLE = re.compile(r"\b(?:surreal|abstract|dreamlike|whimsical|cosmic|psychedelic|impossible|eldritch|ornate magical|glowing aura)\b", re.I)

PLAYER_IDLE = {
    "relaxed": "The warrior breathes steadily with a balanced posture while the equipped weapon remains controlled and cloth settles naturally.",
    "guarded": "The warrior maintains a guarded stance with restrained breathing, stable footing, and the weapon held ready without exaggerated motion.",
    "alert": "The warrior stays alert with small head and weight shifts while keeping equipment stable and ready."
}
PLAYER_WALK = {
    "steady": "The warrior walks with measured heel-to-toe steps while chainmail, leather, and cloth respond naturally to each stride.",
    "agile": "The warrior advances with light controlled steps and compact arm movement while equipment remains close to the body.",
    "heavy": "The warrior advances with deliberate weighted steps while armor settles visibly after each footfall."
}
WEAPON_IDLE = {
    "still": "The weapon remains still in a neutral display position with no camera movement.",
    "restrained_highlight": "The weapon remains still while a restrained material highlight moves across its surface and fades."
}
ARMOR_IDLE = {
    "hanging": "The armor hangs naturally while rings, straps, or fabric settle with a small physically plausible movement.",
    "laid_flat": "The armor remains laid flat and still while its material catches a restrained change in light."
}
LOOT_IDLE = {
    "still": "The loot object remains closed and still in a neutral display position.",
    "restrained_highlight": "The loot object remains closed while a restrained highlight moves over its fittings and fades."
}
CONSUMABLE_IDLE = {
    "still": "The consumable remains upright and still in a neutral display position.",
    "liquid_settle": "The container remains upright while the liquid shifts slightly and settles without moving the bottle."
}


def _normalize_text_fields(plan: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = dict(plan)
    for key in result:
        if key == "face_description":
            continue
        if key == "description" or key == "visual_description" or key.endswith("_description"):
            value = str(result[key]).strip()
            maximum = int(schema.get("properties", {}).get(key, {}).get("maxLength", 10_000))
            if value and not value.endswith((".", "!", "?")) and len(value) < maximum:
                value += "."
            result[key] = value
    return result


def _complete_text_errors(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    text_fields = [key for key in plan if key != "face_description" and (key == "description" or key == "visual_description" or key.endswith("_description"))]
    dangling = re.compile(r"\b(?:a|an|the|and|or|with|at|to|of|for|from|in|on|over|under|his|her|its)\s*[.!?]?$", re.I)
    for key in text_fields:
        value = str(plan[key]).strip()
        if not value.endswith((".", "!", "?")):
            errors.append(f"{key} must end with complete sentence punctuation")
        if dangling.search(value):
            errors.append(f"{key} ends with a dangling word")
        if "..." in value:
            errors.append(f"{key} contains an ellipsis")
    return errors


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(term)}\b", text, re.I) for term in terms)


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _mentions(text: str, value: Any) -> bool:
    target = _norm(value)
    source = _norm(text)
    return bool(target) and re.search(rf"\b{re.escape(target)}\b", source) is not None


def schema_for_request(kind: str, idea: str) -> dict[str, Any]:
    schema = json.loads(json.dumps(SCHEMAS[kind]))
    source = _norm(idea)
    def constrain(field: str, value: str) -> None:
        schema["properties"][field]["enum"] = [value]
    simple: dict[str, dict[str, tuple[str, ...]]] = {
        "player": {
            "role": ("warrior", "ranger", "rogue", "mage", "cleric"),
            "experience_level": ("beginner", "trained", "veteran"),
            "body_type": ("slim", "average", "athletic", "heavy"),
            "main_hand": ("sword", "axe", "spear", "dagger", "bow", "mace", "staff"),
        },
        "weapon": {
            "weapon_type": ("sword", "axe", "spear", "dagger", "bow", "mace", "staff"),
            "material": ("steel", "iron", "bronze", "oak", "ash wood"),
            "quality": ("common", "well made", "fine"),
        },
        "armor": {
            "armor_slot": ("head", "chest", "hands", "legs", "feet", "back"),
            "armor_weight": ("light", "medium", "heavy"),
            "quality": ("common", "well made", "fine"),
        },
        "loot": {
            "loot_type": ("treasure chest", "coin pouch", "gem", "relic", "key item"),
            "material": ("oak", "iron", "steel", "bronze", "leather", "velvet", "crystal"),
            "rarity": ("common", "uncommon", "rare"),
            "contents_hint": ("gold", "equipment", "potion", "key", "mixed"),
        },
        "consumable": {
            "consumable_type": ("health potion", "mana potion", "antidote", "food"),
            "container": ("glass bottle", "ceramic flask", "cloth wrap", "wooden bowl"),
            "primary_color": ("red", "blue", "amber", "clear", "brown", "cream"),
            "quality": ("common", "well made", "fine"),
        },
    }
    for field, terms in simple[kind].items():
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", source):
                constrain(field, term.replace(" ", "_") if term in {"one handed", "two handed", "steel plate", "iron plate", "treasure chest", "coin pouch", "key item", "health potion", "mana potion", "glass bottle", "ceramic flask", "cloth wrap", "wooden bowl", "well made"} else term)
                break
    if kind == "player":
        for color in ("black", "dark brown", "chestnut", "auburn", "blond", "gray"):
            if re.search(rf"\b{re.escape(color)}\s+hair\b|\bhair[^. ,;]{{0,20}}{re.escape(color)}\b", source):
                constrain("hair_color", color); break
        for style in ("short", "shoulder length", "braided", "cropped", "tied back"):
            if re.search(rf"\b{re.escape(style)}(?:\s+[^,.;]{{0,20}})?\s+hair\b", source):
                constrain("hair_style", style); break
        for pattern, value in [(r"chainmail(?: armor| shirt| coat)?(?: over| with| backed by)?", "chainmail"), (r"plate(?: armor| cuirass| harness)", "plate"), (r"leather armor|leather cuirass|leather coat", "leather"), (r"robe|robes", "robe")]:
            if re.search(rf"\b(?:{pattern})\b", source): constrain("armor_style", value); break
        for pattern, value in [(r"steel gray chainmail|steel gray mail", "steel gray"), (r"charcoal chainmail|charcoal mail", "charcoal"), (r"black chainmail|black mail", "black"), (r"steel gray plate", "steel gray"), (r"dark brown leather armor", "dark brown"), (r"black leather armor", "black"), (r"undyed linen robe", "undyed linen"), (r"navy robe", "navy")]:
            if re.search(rf"\b(?:{pattern})\b", source): constrain("armor_primary_color", value); break
        for pattern, value in [(r"muted red (?:cloth|accent|accents|tabard)", "muted red"), (r"dark blue (?:cloth|accent|accents|tabard)", "dark blue"), (r"burgundy (?:cloth|accent|accents|tabard)", "burgundy"), (r"cream (?:cloth|accent|accents|tabard)", "cream"), (r"gray (?:cloth|accent|accents|tabard)", "gray")]:
            if re.search(rf"\b(?:{pattern})\b", source): constrain("armor_secondary_color", value); break
        if any(term in source for term in ("empty off hand", "no shield", "no off hand")): constrain("off_hand", "none")
        if any(term in source for term in ("no cape", "no backpack", "no back item")): constrain("back_item", "none")
    elif kind == "weapon":
        if "one handed" in source: constrain("handedness", "one_handed")
        elif "two handed" in source: constrain("handedness", "two_handed")
    elif kind == "armor":
        if "chest armor" in source or "chest piece" in source or "chainmail shirt" in source: constrain("armor_slot", "chest")
        material_patterns = [
            (r"chainmail(?: armor| shirt| coat| chest)?", "chainmail"),
            (r"steel plate(?: armor| chest| piece)?", "steel_plate"),
            (r"iron plate(?: armor| chest| piece)?", "iron_plate"),
            (r"leather armor|leather cuirass|leather chest", "leather"),
            (r"cloth armor|padded cloth|cloth gambeson", "cloth"),
        ]
        for pattern, value in material_patterns:
            if re.search(rf"\b(?:{pattern})\b", source):
                constrain("material", value)
                break
        color_patterns = [
            (r"steel gray(?: [a-z]+){0,3} (?:chainmail|mail|plate|rings)", "steel gray"),
            (r"charcoal(?: [a-z]+){0,3} (?:chainmail|mail|plate|rings)", "charcoal"),
            (r"black (?:chainmail|mail|plate|rings|leather armor)", "black"),
            (r"dark brown leather armor", "dark brown"),
            (r"cream cloth armor|cream gambeson", "cream"),
            (r"burgundy cloth armor|burgundy gambeson", "burgundy"),
        ]
        for pattern, value in color_patterns:
            if re.search(rf"\b(?:{pattern})\b", source):
                constrain("primary_color", value)
                break
    return schema


def validate_request_adherence(kind: str, plan: dict[str, Any], idea: str) -> list[str]:
    errors: list[str] = []
    source = _norm(idea)
    field_terms: dict[str, dict[str, tuple[str, ...]]] = {
        "player": {
            "role": ("warrior", "ranger", "rogue", "mage", "cleric"),
            "body_type": ("slim", "average", "athletic", "heavy"),
            "main_hand": ("sword", "axe", "spear", "dagger", "bow", "mace", "staff"),
        },
        "weapon": {
            "weapon_type": ("sword", "axe", "spear", "dagger", "bow", "mace", "staff"),
            "handedness": ("one handed", "two handed"),
            "material": ("steel", "iron", "bronze", "oak", "ash wood"),
            "quality": ("common", "well made", "fine"),
        },
        "armor": {
            "armor_slot": ("head", "chest", "hands", "legs", "feet", "back"),
            "armor_weight": ("light", "medium", "heavy"),
            "quality": ("common", "well made", "fine"),
        },
        "loot": {
            "loot_type": ("treasure chest", "coin pouch", "gem", "relic", "key item"),
            "material": ("oak", "iron", "steel", "bronze", "leather", "velvet", "crystal"),
            "rarity": ("common", "uncommon", "rare"),
            "contents_hint": ("gold", "equipment", "potion", "key", "mixed"),
        },
        "consumable": {
            "consumable_type": ("health potion", "mana potion", "antidote", "food"),
            "container": ("glass bottle", "ceramic flask", "cloth wrap", "wooden bowl"),
            "primary_color": ("red", "blue", "amber", "clear", "brown", "cream"),
            "quality": ("common", "well made", "fine"),
        },
    }
    for field, terms in field_terms[kind].items():
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", source):
                selected = _norm(plan[field])
                if selected != term:
                    errors.append(f"request explicitly requires {field}={term}, but model selected {selected}")
                break
    if kind == "player":
        hair_colors = ("black", "dark brown", "chestnut", "auburn", "blond", "gray")
        for color in hair_colors:
            if re.search(rf"\b{re.escape(color)}\s+hair\b|\bhair[^. ,;]{{0,20}}{re.escape(color)}\b", source):
                if _norm(plan["hair_color"]) != color:
                    errors.append(f"request explicitly requires hair_color={color}")
                break
        hair_styles = ("short", "shoulder length", "braided", "cropped", "tied back")
        for style in hair_styles:
            if re.search(rf"\b{re.escape(style)}(?:\s+[^,.;]{{0,20}})?\s+hair\b", source):
                if _norm(plan["hair_style"]) != style:
                    errors.append(f"request explicitly requires hair_style={style}")
                break
        contextual_armor = [
            (r"chainmail(?: armor| shirt| coat)?(?: over| with| backed by)?", "chainmail"),
            (r"plate(?: armor| cuirass| harness)", "plate"),
            (r"leather armor|leather cuirass|leather coat", "leather"),
            (r"robe|robes", "robe"),
        ]
        for pattern, value in contextual_armor:
            if re.search(rf"\b(?:{pattern})\b", source):
                if _norm(plan["armor_style"]) != value:
                    errors.append(f"request explicitly requires armor_style={value}")
                break
        contextual_primary = [
            (r"steel gray chainmail|steel gray mail", "steel gray"),
            (r"charcoal chainmail|charcoal mail", "charcoal"),
            (r"black chainmail|black mail", "black"),
            (r"steel gray plate", "steel gray"),
            (r"dark brown leather armor", "dark brown"),
            (r"black leather armor", "black"),
            (r"undyed linen robe", "undyed linen"),
            (r"navy robe", "navy"),
        ]
        for pattern, value in contextual_primary:
            if re.search(rf"\b(?:{pattern})\b", source):
                if _norm(plan["armor_primary_color"]) != value:
                    errors.append(f"request explicitly requires armor_primary_color={value}")
                break
        contextual_secondary = [
            (r"muted red (?:cloth|accent|accents|tabard)", "muted red"),
            (r"dark blue (?:cloth|accent|accents|tabard)", "dark blue"),
            (r"burgundy (?:cloth|accent|accents|tabard)", "burgundy"),
            (r"cream (?:cloth|accent|accents|tabard)", "cream"),
            (r"gray (?:cloth|accent|accents|tabard)", "gray"),
        ]
        for pattern, value in contextual_secondary:
            if re.search(rf"\b(?:{pattern})\b", source):
                if _norm(plan["armor_secondary_color"]) != value:
                    errors.append(f"request explicitly requires armor_secondary_color={value}")
                break
        if any(term in source for term in ("empty off hand", "no shield", "no off hand")) and plan["off_hand"] != "none":
            errors.append("request explicitly requires empty off_hand")
        if "no helmet" in source and plan.get("armor_style") == "plate" and _contains(str(plan.get("visual_description", "")), ("helmet",)):
            errors.append("request explicitly forbids a helmet")
        if any(term in source for term in ("no cape", "no backpack", "no back item")) and plan["back_item"] != "none":
            errors.append("request explicitly requires empty back slot")
        if plan.get("experience_level") == "beginner" and _contains(f"{plan.get('description','')} {plan.get('visual_description','')}", ("seasoned", "veteran", "master", "elite", "renowned", "legendary", "experienced")):
            errors.append("beginner character cannot be described as experienced or elite")
    return errors


def validate_plan_semantics(kind: str, plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    description = str(plan.get("description", ""))
    visual = str(plan.get("visual_description", ""))
    combined = f"{description} {visual}".casefold()
    if kind == "player":
        armor = str(plan["armor_style"])
        weapon = str(plan["main_hand"])
        off_hand = str(plan["off_hand"])
        if plan.get("experience_level") == "beginner" and _contains(combined, ("seasoned", "veteran", "master", "elite", "renowned", "legendary", "experienced")):
            errors.append("beginner character cannot be described as experienced or elite")
        if armor not in visual.casefold():
            errors.append(f"visual_description must explicitly mention selected armor_style {armor}")
        if not _mentions(visual, plan["armor_primary_color"]):
            errors.append(f"visual_description must explicitly mention selected armor_primary_color {plan['armor_primary_color']}")
        if not _mentions(visual, plan["armor_secondary_color"]):
            errors.append(f"visual_description must explicitly mention selected armor_secondary_color {plan['armor_secondary_color']}")
        if weapon not in visual.casefold():
            errors.append(f"visual_description must explicitly mention selected main_hand {weapon}")
        if _contains(visual, (f"no {weapon}", f"without {weapon}", f"missing {weapon}", f"no visible {weapon}")):
            errors.append(f"visual_description negates required main_hand {weapon}")
        if _contains(visual, (f"no {armor}", f"without {armor}", f"missing {armor}")):
            errors.append(f"visual_description negates required armor_style {armor}")
        if _contains(combined, ("shirtless", "bare chest", "without a shirt", "without armor", "unarmored", "naked", "barefoot")):
            errors.append("player description contradicts equipped clothing or armor")
        if off_hand == "none" and _contains(combined, ("shield", "second sword", "off-hand dagger", "off hand dagger")):
            errors.append("player description contradicts empty off_hand")
        if plan["back_item"] == "none" and _contains(combined, ("cape", "quiver", "backpack")):
            errors.append("player description contradicts empty back slot")
        if armor == "chainmail" and plan["armor_primary_color"] not in {"steel gray", "charcoal", "black"}:
            errors.append("chainmail primary color must be metallic steel gray, charcoal, or black")
        if armor == "plate" and plan["armor_primary_color"] not in {"steel gray", "charcoal", "black"}:
            errors.append("plate primary color must be metallic steel gray, charcoal, or black")
        if armor == "leather" and plan["armor_primary_color"] not in {"dark brown", "black", "charcoal"}:
            errors.append("leather armor primary color must be dark brown, black, or charcoal")
        if armor == "robe" and plan["armor_primary_color"] in {"steel gray", "charcoal"}:
            errors.append("robe primary color must read as cloth rather than metal")
        if WEAPON_RULES[weapon]["slot"] == "two_hands" and off_hand != "none":
            errors.append(f"{weapon} requires both hands and an empty off_hand")
    elif kind == "weapon":
        weapon = str(plan["weapon_type"])
        material = str(plan["material"])
        if weapon not in combined:
            errors.append(f"combined semantic description must mention weapon_type {weapon}")
        if material not in combined:
            errors.append(f"combined semantic description must mention material {material}")
        if weapon in {"sword", "axe", "dagger", "mace"} and material in {"oak", "ash wood"}:
            errors.append(f"{weapon} cannot use wood as its primary weapon material")
        if weapon in {"bow", "staff"} and material not in {"oak", "ash wood"}:
            errors.append(f"{weapon} requires a wood primary material")
        if weapon in {"bow", "spear", "staff"} and plan["handedness"] != "two_handed":
            errors.append(f"{weapon} must be two_handed")
        if weapon == "dagger" and plan["handedness"] != "one_handed":
            errors.append("dagger must be one_handed")
    elif kind == "armor":
        material = str(plan["material"])
        slot = str(plan["armor_slot"])
        if material.replace("_", " ") not in combined and material not in combined:
            errors.append(f"combined semantic description must mention armor material {material}")
        slot_words = {"head": ("helmet", "hood", "head"), "chest": ("shirt", "coat", "chest", "cuirass", "mail"), "hands": ("glove", "gauntlet", "hand"), "legs": ("legging", "greave", "leg", "trouser"), "feet": ("boot", "shoe", "foot"), "back": ("cape", "cloak", "back")}
        if not _contains(combined, slot_words[slot]):
            errors.append(f"combined semantic description must identify armor slot {slot}")
        compatible = {
            "cloth": {"light"}, "leather": {"light", "medium"}, "chainmail": {"medium"},
            "steel_plate": {"heavy"}, "iron_plate": {"heavy"}
        }
        if plan["armor_weight"] not in compatible[material]:
            errors.append(f"armor_weight {plan['armor_weight']} is incompatible with {material}")
    elif kind == "loot":
        loot_type = str(plan["loot_type"]).replace("_", " ")
        material = str(plan["material"])
        loot_aliases = {
            "treasure chest": ("treasure chest", "chest"),
            "coin pouch": ("coin pouch", "pouch"),
            "gem": ("gem", "jewel", "stone"),
            "relic": ("relic",),
            "key item": ("key", "key item"),
        }
        if not _contains(combined, loot_aliases[loot_type]):
            errors.append(f"combined semantic description must identify loot_type {loot_type}")
        if material not in combined:
            errors.append(f"combined semantic description must mention loot material {material}")
        if plan["loot_type"] == "treasure_chest" and material not in {"oak", "iron", "steel", "bronze"}:
            errors.append("treasure_chest requires oak or metal construction")
        if plan["loot_type"] == "coin_pouch" and material not in {"leather", "velvet"}:
            errors.append("coin_pouch requires leather or velvet")
    elif kind == "consumable":
        consumable = str(plan["consumable_type"]).replace("_", " ")
        container = str(plan["container"]).replace("_", " ")
        if consumable not in combined:
            errors.append(f"combined semantic description must mention consumable_type {consumable}")
        if container not in combined:
            errors.append(f"combined semantic description must mention container {container}")
        if plan["consumable_type"] in {"health_potion", "mana_potion", "antidote"} and plan["container"] not in {"glass_bottle", "ceramic_flask"}:
            errors.append("liquid consumable requires a bottle or flask")
        if plan["consumable_type"] == "health_potion" and plan["primary_color"] != "red":
            errors.append("health_potion must use red liquid")
        if plan["consumable_type"] == "mana_potion" and plan["primary_color"] != "blue":
            errors.append("mana_potion must use blue liquid")
        if plan["consumable_type"] == "food" and plan["container"] in {"glass_bottle", "ceramic_flask"}:
            errors.append("food cannot use a potion bottle or flask")
    return errors


def _request(request_json: Callable[[str, dict[str, Any], float], dict[str, Any]], llama_url: str, model: str, schema: dict[str, Any], system: str, user: str, seed: int, max_tokens: int = 430, semantic_validator: Callable[[dict[str, Any]], list[str]] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    feedback = ""
    for attempt in range(3):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user + (f" Previous output was rejected: {feedback}. Rewrite every text field as short complete sentences." if feedback else "")}]
        payload = {
            "model": model,
            "messages": messages,
            "json_schema": schema,
            "max_tokens": max_tokens,
            "temperature": 0.30 + attempt * 0.05,
            "top_p": 0.86,
            "seed": seed + attempt,
        }
        started = time.monotonic()
        try:
            response = request_json(llama_url, payload, 145.0)
            content = response["choices"][0]["message"]["content"]
            plan = _normalize_text_fields(json.loads(content), schema)
            errors = [e.message for e in Draft202012Validator(schema).iter_errors(plan)]
            errors.extend(_complete_text_errors(plan))
            if semantic_validator is not None:
                errors.extend(semantic_validator(plan))
            text = json.dumps(plan, ensure_ascii=False)
            if FORBIDDEN_STYLE.search(text):
                errors.append("generated content violated grounded visual style")
            attempts.append({"attempt": attempt + 1, "seconds": round(time.monotonic() - started, 3), "errors": errors})
            if not errors:
                return plan, {"provider": "nitro-llama.cpp-constrained", "model": model, "seconds": round(sum(a["seconds"] for a in attempts), 3), "strict_schema": schema, "attempts": attempts}
            feedback = "; ".join(errors)[:700]
        except Exception as exc:
            feedback = f"{type(exc).__name__}: {exc}"[:700]
            attempts.append({"attempt": attempt + 1, "seconds": round(time.monotonic() - started, 3), "exception": feedback})
    raise RuntimeError("grounded semantic generation failed: " + feedback + " attempts=" + json.dumps(attempts, ensure_ascii=False))


def _equipment_from_player(plan: dict[str, Any]) -> dict[str, str]:
    armor = plan["armor_style"]
    return {
        "head": "none",
        "chest": {"leather": "leather_armor", "chainmail": "chainmail", "plate": "plate_armor", "robe": "robe"}[armor],
        "hands": "leather_gloves" if armor != "plate" else "gauntlets",
        "legs": "trousers" if armor in {"leather", "chainmail"} else "greaves" if armor == "plate" else "robe_lower",
        "feet": "leather_boots",
        "main_hand": plan["main_hand"],
        "off_hand": plan["off_hand"],
        "back": plan["back_item"],
        "neck": "none",
        "ring_left": "none",
        "ring_right": "none",
    }


def compile_player(plan: dict[str, Any]) -> dict[str, Any]:
    stats = dict(ROLE_STATS[plan["role"]])
    stats.update({"hp": stats["max_hp"], "stamina": stats["max_stamina"], "mana": stats["max_mana"]})
    weapon = WEAPON_RULES[plan["main_hand"]]
    if weapon["slot"] == "two_hands":
        plan = dict(plan)
        plan["off_hand"] = "none"
    visual_prompt = (
        f"{plan['visual_description']} Full body strict side profile facing right. "
        f"One {plan['main_hand']} only. " + (f"One {plan['off_hand'].replace('_', ' ')} only. " if plan['off_hand'] != 'none' else "Empty off hand. ") +
        "Grounded medieval RPG character, realistic human anatomy and proportions, practical construction, steel leather chainmail cloth and wood only, clean readable silhouette, entire body and both feet visible, centered, solid bright chroma green background, no scenery."
    )
    return {
        "kind": "player_character",
        "game_description": GAME_DESCRIPTION,
        "name": plan["name"],
        "role": plan["role"],
        "presentation": plan["presentation"],
        "body_type": plan["body_type"],
        "level": {"beginner": 1, "trained": 5, "veteran": 10}[plan["experience_level"]],
        "experience_level": plan["experience_level"],
        "stats": stats,
        "equipment": _equipment_from_player(plan),
        "actions": {"basic_attack": weapon["primary"], "secondary_action": weapon["secondary"], "mobility_action": "jump"},
        "appearance": {
            "hair": f"{plan['hair_style']} {plan['hair_color']} hair",
            "face": plan["face_description"],
            "armor_style": plan["armor_style"],
            "armor_colors": [plan["armor_primary_color"], plan["armor_secondary_color"]],
            "silhouette": f"{plan['body_type']} {plan['role']} with {plan['main_hand']} and {plan['off_hand']}",
            "visual_description": plan["visual_description"],
        },
        "description": plan["description"],
        "asset": {
            "structural_prompt": f"full body strict side profile adult human {plan['role']} facing right, one plain steel {plan['main_hand']}, empty off hand" if plan["off_hand"] == "none" else f"full body strict side profile adult human {plan['role']} facing right, one plain steel {plan['main_hand']}, one {plan['off_hand'].replace('_', ' ')}",
            "semantic_prompt": plan["visual_description"],
            "visual_prompt": visual_prompt,
            "negative_prompt": "surreal, abstract, monster, extra limbs, extra weapons, duplicate equipment, cropped feet, front view, rear view, three quarter view, anime, chibi, cartoon, toy, icon, text, watermark, scenery, floor, shadow, green clothing",
            "idle_animation_description": PLAYER_IDLE[plan["idle_style"]],
            "walk_animation_description": PLAYER_WALK[plan["movement_style"]],
            "idle_style": plan["idle_style"],
            "movement_style": plan["movement_style"],
            "expected_labels": ["adult human", "medieval fighter", plan["main_hand"], plan["armor_style"]],
            "review_requirements": f"Exactly one recognizable adult human medieval {plan['role']} in a complete side profile facing right. The whole body and both feet are visible. Exactly one {plan['main_hand']} is visible. The off hand is {'empty' if plan['off_hand'] == 'none' else 'holding exactly one ' + plan['off_hand'].replace('_', ' ')}. Arms and legs are normal. Practical {plan['armor_style']}, leather, cloth, and metal equipment. No duplicate body, extra limb, extra weapon, scenery, text, or watermark. Clean plain solid white extraction background."
        }
    }


def compile_weapon(plan: dict[str, Any]) -> dict[str, Any]:
    rules = dict(WEAPON_RULES[plan["weapon_type"]])
    slot = "two_hands" if plan["handedness"] == "two_handed" else rules["slot"]
    if plan["handedness"] == "two_handed":
        rules["damage"] += 3
        rules["speed"] = max(3, rules["speed"] - 2)
    return {
        "kind": "weapon", "name": plan["name"], "weapon_type": plan["weapon_type"], "handedness": plan["handedness"],
        "damage_type": rules["damage_type"], "material": plan["material"], "quality": plan["quality"], "equip_slot": slot,
        "actions": {"primary": rules["primary"], "secondary": rules["secondary"]},
        "stats": {"damage": rules["damage"], "speed": rules["speed"], "range": rules["range"]},
        "description": plan["description"],
        "asset": {
            "structural_prompt": f"one standard medieval {plan['material']} {plan['weapon_type']}, full object, realistic proportions, practical construction",
            "semantic_prompt": plan["visual_description"],
            "visual_prompt": f"{plan['visual_description']} One standard recognizable medieval {plan['weapon_type']} made from {plan['material']}, realistic proportions and practical construction, full object visible, clean silhouette, centered on plain white background, no hands, no person, no scenery.",
            "negative_prompt": "surreal, abstract, magical glow, ornate hilt, decorative engraving, jewel, gem, sheath, scabbard, extra weapons, duplicate, bent blade, malformed, character, hands, scenery, floor, shadow, text, watermark, green object",
            "idle_animation_description": WEAPON_IDLE[plan["display_style"]],
            "use_animation_description": f"The {plan['weapon_type']} performs one controlled {rules['primary']} action and returns to its starting position.",
            "display_style": plan["display_style"],
            "expected_labels": [plan["weapon_type"], plan["material"], "medieval weapon"],
            "review_requirements": f"Exactly one recognizable medieval {plan['weapon_type']}. The complete object and every functional part are visible. Realistic {plan['material']} construction with a plain practical hilt or handle. No sheath, scabbard, ornate decoration, engraving, jewels, person, hand, second weapon, malformed geometry, magical glow, scenery, text, or watermark. Clean plain solid white extraction background."
        }
    }


def compile_armor(plan: dict[str, Any]) -> dict[str, Any]:
    rules = ARMOR_RULES[plan["armor_weight"]]
    return {
        "kind": "armor", "name": plan["name"], "armor_slot": plan["armor_slot"], "armor_weight": plan["armor_weight"],
        "material": plan["material"], "primary_color": plan["primary_color"], "quality": plan["quality"], "equip_slot": plan["armor_slot"],
        "stats": dict(rules), "description": plan["description"],
        "asset": {
            "structural_prompt": f"one standard medieval {plan['material']} {plan['armor_slot']} armor piece, {plan['primary_color']}, full object, realistic proportions, practical construction",
            "semantic_prompt": plan["visual_description"],
            "visual_prompt": f"{plan['visual_description']} One standard recognizable medieval {plan['armor_slot']} armor piece made from {plan['material']}, {plan['primary_color']}, practical construction, realistic proportions, full object visible, clean silhouette, centered on plain white background, no person, no mannequin, no scenery.",
            "negative_prompt": "surreal, abstract, magical glow, ornate fantasy, multiple armor pieces, person, mannequin, scenery, floor, shadow, text, watermark, green object",
            "idle_animation_description": ARMOR_IDLE[plan["display_style"]], "equip_description": f"The {plan['armor_slot']} armor is fitted to its matching body slot and secured using its practical straps or fastenings.",
            "display_style": plan["display_style"],
            "expected_labels": [plan["armor_slot"], plan["material"], "medieval armor"],
            "review_requirements": f"Exactly one recognizable medieval {plan['armor_slot']} armor piece made from {plan['material']}. The complete wearable piece is visible with normal practical geometry. No person, mannequin, extra armor pieces, magical glow, scenery, text, or watermark. Clean plain solid white extraction background."
        }
    }


def compile_loot(plan: dict[str, Any]) -> dict[str, Any]:
    interaction = "open" if plan["loot_type"] == "treasure_chest" else "collect"
    return {
        "kind": "loot", "name": plan["name"], "loot_type": plan["loot_type"], "interaction": interaction,
        "material": plan["material"], "rarity": plan["rarity"], "contents_hint": plan["contents_hint"], "description": plan["description"],
        "asset": {
            "structural_prompt": f"one standard medieval {plan['material']} {plan['loot_type'].replace('_', ' ')}, full object, realistic proportions, practical construction",
            "semantic_prompt": plan["visual_description"],
            "visual_prompt": f"{plan['visual_description']} One standard recognizable medieval {plan['loot_type'].replace('_', ' ')} made from {plan['material']}, practical construction, realistic proportions, full object visible, clean silhouette, centered on plain white background, no scenery.",
            "negative_prompt": "surreal, abstract, magical glow, excessive ornament, creature, person, extra objects, scenery, floor, shadow, text, watermark, green object",
            "idle_animation_description": LOOT_IDLE[plan["display_style"]], "open_animation_description": "The lid rotates upward on its hinges and stops in a stable open position." if plan["open_style"] == "hinged_lid" else "The collected item disappears cleanly after contact.",
            "display_style": plan["display_style"], "open_style": plan["open_style"],
            "expected_labels": [plan["loot_type"].replace("_", " "), plan["material"], "medieval loot"],
            "review_requirements": f"Exactly one recognizable medieval {plan['loot_type'].replace('_', ' ')} made from {plan['material']}. The complete object and practical construction are visible. No creature, person, extra object, magical glow, scenery, text, or watermark. Clean plain solid white extraction background."
        }
    }


def compile_consumable(plan: dict[str, Any]) -> dict[str, Any]:
    effects = {"health_potion": ("health", 25), "mana_potion": ("mana", 25), "antidote": ("poison", -1), "food": ("health", 10)}
    stat, amount = effects[plan["consumable_type"]]
    use_action = "eat" if plan["consumable_type"] == "food" else "drink"
    return {
        "kind": "consumable", "name": plan["name"], "consumable_type": plan["consumable_type"], "use_action": use_action,
        "container": plan["container"], "primary_color": plan["primary_color"], "quality": plan["quality"],
        "effect": {"stat": stat, "amount": amount}, "description": plan["description"],
        "asset": {
            "structural_prompt": f"one standard medieval RPG {plan['consumable_type'].replace('_', ' ')} in a {plan['container'].replace('_', ' ')}, {plan['primary_color']}, full object, practical construction",
            "semantic_prompt": plan["visual_description"],
            "visual_prompt": f"{plan['visual_description']} One standard recognizable medieval RPG {plan['consumable_type'].replace('_', ' ')} in a {plan['container'].replace('_', ' ')}, {plan['primary_color']}, practical construction, full object visible, clean silhouette, centered on plain white background, no scenery.",
            "negative_prompt": "surreal, abstract, magical aura, extra bottles, person, hands, scenery, floor, shadow, text, watermark, green object",
            "idle_animation_description": CONSUMABLE_IDLE[plan["display_style"]], "use_animation_description": f"The character {use_action}s the consumable and the container is removed after use.",
            "display_style": plan["display_style"],
            "expected_labels": [plan["consumable_type"].replace("_", " "), plan["container"].replace("_", " ")],
            "review_requirements": f"Exactly one recognizable medieval RPG {plan['consumable_type'].replace('_', ' ')} in one {plan['container'].replace('_', ' ')}. The complete container and closure are visible. No person, hand, extra bottle, magical aura, scenery, text, or watermark. Clean plain solid white extraction background."
        }
    }


COMPILERS = {"player": compile_player, "weapon": compile_weapon, "armor": compile_armor, "loot": compile_loot, "consumable": compile_consumable}


def generate(kind: str, idea: str, request_json: Callable[[str, dict[str, Any], float], dict[str, Any]], llama_url: str, model: str, seed: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if kind not in SCHEMAS:
        raise ValueError(f"unsupported RPG kind: {kind}")
    system = (
        "You generate semantic content for a grounded medieval fantasy RPG. The JSON structure and enums are fixed by the schema. "
        "Write concrete, literal, useful descriptions of recognizable historical-style people and equipment. "
        "Use practical materials and ordinary construction. Do not use surreal, abstract, whimsical, cosmic, or overloaded magical imagery. "
        "The visual description must state visible shape, proportions, materials, colors, condition, and distinguishing construction details. "
        "Use one or two short complete sentences for description and visual_description. Both must end with punctuation. Respect experience_level literally: a beginner is newly trained and must never be called seasoned, veteran, elite, renowned, legendary, master, or experienced. Select animation and movement enums according to the object type; deterministic game code will compile their motion. Return JSON only."
    )
    user = f"General game description: {GAME_DESCRIPTION}\nGenerate one {kind}. Player request: {idea or 'standard beginner equipment suitable for this game'}."
    request_schema = schema_for_request(kind, idea)
    plan, meta = _request(request_json, llama_url, model, request_schema, system, user, seed, semantic_validator=lambda candidate: validate_plan_semantics(kind, candidate) + validate_request_adherence(kind, candidate, idea))
    meta["base_schema"] = SCHEMAS[kind]
    compiled = COMPILERS[kind](plan)
    meta["plan"] = plan
    meta["kind"] = kind
    return compiled, meta
