extends SceneTree

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    var failures := PackedStringArray()
    var scene: PackedScene = load("res://scenes/main.tscn")
    var instance := scene.instantiate()
    root.add_child(instance)
    await process_frame
    await physics_frame

    instance.dom_shell_active = true
    instance.interface_canvas.visible = false
    instance._configure_web_canvas()
    if instance.current_game_rect.position != Vector2.ZERO:
        failures.append("web game rect does not begin at canvas origin")
    if instance.current_game_rect.size != instance.get_viewport().get_visible_rect().size:
        failures.append("web game rect does not fill canvas")

    while not instance.player.is_on_floor(): await physics_frame
    var start_x: float = instance.player.position.x
    instance._on_web_move([0.85, 0.0])
    for _index in range(12): await physics_frame
    if instance.touch_move.x < 0.84: failures.append("bridge did not accept normalized movement")
    if instance.player.position.x <= start_x: failures.append("bridge movement did not move player")
    instance._on_web_move([0.0, 0.0])
    if not instance.touch_move.is_zero_approx(): failures.append("bridge did not release movement")

    while not instance.player.is_on_floor(): await physics_frame
    instance._on_web_move([0.0, -1.0])
    if not instance.touch_jump_requested: failures.append("upward bridge movement did not request jump")
    await physics_frame
    if instance.player.velocity.y >= 0.0: failures.append("bridge jump did not apply upward velocity")
    instance._on_web_move([0.0, 0.0])

    instance.stamina = 50.0
    instance._on_web_action(["attack"])
    if not instance.attack_active or instance.stamina >= 50.0: failures.append("bridge attack failed")
    instance._finish_attack()
    instance.stamina = 50.0
    instance._on_web_action(["parry"])
    if not instance.parry_active or instance.stamina >= 50.0: failures.append("bridge parry failed")
    instance.touch_jump_requested = false
    instance._on_web_action(["jump"])
    if not instance.touch_jump_requested: failures.append("bridge jump button failed")
    instance.health = 50
    instance.potion_count = 1
    instance._on_web_action(["potion"])
    if instance.health != 75 or instance.potion_count != 0: failures.append("bridge potion failed")
    instance.player.position = Vector2(2000, 400)
    instance._on_web_action(["reset"])
    if instance.player.position.x >= 2000: failures.append("bridge reset failed")

    var sequence_before: int = instance.generation_sequence
    instance.rpg_client._busy = true
    instance._on_web_forge(["loot", "plain oak chest"])
    if instance.generation_sequence != sequence_before:
        failures.append("busy forge bridge incorrectly started another job")
    instance.rpg_client._busy = false
    instance._on_web_forge(["invalid", "bad"])
    if "Unsupported forge type" not in instance.forge_status_label.text:
        failures.append("bridge did not reject invalid forge kind")

    if failures.is_empty():
        print(JSON.stringify({"ok": true, "canvas": instance.current_game_rect, "movement": true, "jump": true, "actions": ["attack", "parry", "potion", "reset"], "forge_validation": true}))
        quit(0)
    else:
        push_error("; ".join(failures))
        quit(1)
