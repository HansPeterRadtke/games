extends SceneTree

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    var failures := PackedStringArray()
    var scene: PackedScene = load("res://scenes/main.tscn")
    if scene == null:
        failures.append("main scene did not load")
    else:
        var instance := scene.instantiate()
        root.add_child(instance)
        await process_frame
        await physics_frame
        var player := instance.get_node_or_null("OpenWorld/Player")
        var terrain := instance.get_node_or_null("OpenWorld/Terrain")
        var objects := instance.get_node_or_null("OpenWorld/RPGObjects")
        var camera := instance.get_node_or_null("WorldCamera")
        var client := instance.get_node_or_null("RPGContentClient")
        if not player is CharacterBody2D: failures.append("grounded player is missing")
        if terrain == null or terrain.get_child_count() < 6: failures.append("open terrain did not generate")
        if objects == null or objects.get_child_count() != 4: failures.append("four grounded RPG items were not loaded")
        if not camera is Camera2D or not camera.enabled: failures.append("camera is missing")
        if client == null: failures.append("RPG content client is missing")
        if instance.find_child("RightWall", true, false) != null: failures.append("open world has a right wall")
        if instance.player_content.get("name", "") != "Eryndor Thorne": failures.append("wrong player record")
        if int(instance.player_stats.get("max_hp", 0)) != 120: failures.append("wrong player HP")
        if instance.equipment.get("main_hand", "") != "sword" or instance.equipment.get("off_hand", "") != "none": failures.append("wrong player equipment")
        if instance.actions != {"basic_attack": "slash", "secondary_action": "parry", "mobility_action": "jump"}: failures.append("wrong player actions")
        var player_animation := instance.get_node_or_null("OpenWorld/Player/PlayerAnimation")
        if not player_animation is AnimatedSprite2D or not player_animation.visible: failures.append("reviewed player animation is not visible")
        elif player_animation.sprite_frames.get_frame_count("idle") != 8: failures.append("player does not use eight reviewed frames")
        var expected_positions := [620.0, 900.0, 1200.0, 1500.0]
        var reviewed_items := 0
        if objects != null:
            for expected_x in expected_positions:
                var found := false
                for child in objects.get_children():
                    if child is Area2D and absf(child.position.x - expected_x) < 0.1:
                        found = true
                        var animation := child.get_node_or_null("GroundedAnimation")
                        if animation is AnimatedSprite2D and animation.visible and animation.sprite_frames.get_frame_count("idle") == 6:
                            reviewed_items += 1
                if not found: failures.append("missing grounded item at x=%f" % expected_x)
        if reviewed_items != 4: failures.append("not every item uses six reviewed frames")
        var attack := instance.get_node_or_null("OpenWorld/Player/AttackArea")
        if not attack is Area2D: failures.append("player attack area is missing")
        var left := instance.get_node_or_null("Interface/LeftPanel")
        var right := instance.get_node_or_null("Interface/RightPanel")
        if left == null or right == null: failures.append("fixed side panels are missing")
        else:
            if left.position != Vector2.ZERO or left.size != Vector2(230, 648): failures.append("left panel geometry is wrong")
            if right.position != Vector2(902, 0) or right.size != Vector2(250, 648): failures.append("right panel geometry is wrong")
        var metrics: Dictionary = instance.get_layout_metrics()
        if metrics["left_panel"].end.x != metrics["game"].position.x: failures.append("left panel overlaps game")
        if metrics["game"].end.x != metrics["right_panel"].position.x: failures.append("right panel overlaps game")
        if metrics["right_panel"].end.x != 1152.0: failures.append("layout does not fill viewport")
        instance.queue_free()
    if failures.is_empty():
        print(JSON.stringify({"ok": true, "player": "Eryndor Thorne", "player_frames": 8, "reviewed_items": 4, "layout": "230|672|250"}))
        quit(0)
    else:
        push_error("; ".join(failures))
        quit(1)
