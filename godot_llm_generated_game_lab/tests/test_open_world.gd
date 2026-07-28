extends SceneTree

func _init() -> void:
    call_deferred("_run")

func _find_kind(objects: Node, kind: String) -> Area2D:
    for child in objects.get_children():
        if child is Area2D:
            var entry: Dictionary = child.get_meta("entry", {})
            if str(entry.get("kind", "")) == kind:
                return child
    return null

func _run() -> void:
    var failures := PackedStringArray()
    var scene: PackedScene = load("res://scenes/main.tscn")
    var instance := scene.instantiate()
    root.add_child(instance)
    await process_frame
    await physics_frame
    instance._ensure_world_ahead(10000.0)
    var terrain: Node = instance.get_node("OpenWorld/Terrain")
    if terrain.get_child_count() < 16: failures.append("terrain did not extend to ten thousand pixels")
    var objects: Node = instance.get_node("OpenWorld/RPGObjects")
    var camera: Camera2D = instance.get_node("WorldCamera")
    var first_weapon := _find_kind(objects, "weapon")
    var opening_edge: float = instance.player.position.x + maxf(360.0, instance.current_game_rect.size.x * 0.82)
    if first_weapon.position.x <= instance.player.position.x: failures.append("first weapon is not ahead of player")
    if first_weapon.position.x > opening_edge: failures.append("first weapon is not in opening route")
    var starting_inventory: int = instance.inventory.size()
    var weapon := _find_kind(objects, "weapon")
    instance._apply_rpg_interaction(weapon)
    if instance.weapon_damage != 12 or instance.actions["basic_attack"] != "slash": failures.append("weapon equip failed")
    if instance.inventory.size() != starting_inventory + 1: failures.append("weapon was not added to inventory")
    var armor := _find_kind(objects, "armor")
    instance._apply_rpg_interaction(armor)
    if instance._current_defense() != 20: failures.append("armor defense was not applied")
    var loot := _find_kind(objects, "loot")
    var score_before: int = instance.score
    instance._apply_rpg_interaction(loot)
    if instance.score != score_before + 25 or not bool(loot.get_meta("opened", false)): failures.append("chest open interaction failed")
    var potion := _find_kind(objects, "consumable")
    instance.health = 50
    instance._apply_rpg_interaction(potion)
    if instance.health != 75: failures.append("health potion did not restore 25 HP")
    var player: CharacterBody2D = instance.get_node("OpenWorld/Player")
    player.position.x = 3000.0
    for _index in range(16): await physics_frame
    if camera.position.x <= 576.0: failures.append("camera did not follow rightward progress")
    if failures.is_empty():
        print(JSON.stringify({"ok": true, "segments": terrain.get_child_count(), "weapon_damage": instance.weapon_damage, "defense": instance._current_defense(), "score": instance.score, "health": instance.health, "camera_x": camera.position.x}))
        quit(0)
    else:
        push_error("; ".join(failures))
        quit(1)
