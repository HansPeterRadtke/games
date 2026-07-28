extends SceneTree

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    var scene: PackedScene = load("res://scenes/main.tscn")
    var instance := scene.instantiate()
    root.add_child(instance)
    await physics_frame
    var crate: RigidBody2D = instance.get_node("OpenWorld/Terrain/Segment_1/PhysicsCrate")
    var crate_start := crate.position.y
    for _index in range(45): await physics_frame
    var crate_fall := crate.position.y - crate_start
    if crate_fall <= 20.0:
        push_error("rigid crate did not fall under gravity")
        quit(1); return
    var player: CharacterBody2D = instance.get_node("OpenWorld/Player")
    var start := player.position
    player.velocity = Vector2(260.0, -520.0)
    for _index in range(12): await physics_frame
    if player.position.x <= start.x or player.position.y >= start.y:
        push_error("player physics did not move upward and right")
        quit(1); return
    var stamina_before: float = instance.stamina
    instance._perform_attack()
    if not instance.attack_active or instance.stamina >= stamina_before:
        push_error("slash action did not activate or consume stamina")
        quit(1); return
    instance._finish_attack()
    instance.stamina = 50.0
    instance._perform_parry()
    if not instance.parry_active or instance.stamina >= 50.0:
        push_error("parry did not activate or consume stamina")
        quit(1); return
    print(JSON.stringify({"ok": true, "rigid_fall_pixels": crate_fall, "player_position": [player.position.x, player.position.y], "slash": true, "parry": true}))
    quit(0)
