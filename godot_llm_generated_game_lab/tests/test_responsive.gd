extends SceneTree

func _init() -> void:
    call_deferred("_run")

func _rect_inside(inner: Rect2, outer: Rect2, tolerance := 0.2) -> bool:
    return inner.position.x >= outer.position.x - tolerance \
        and inner.position.y >= outer.position.y - tolerance \
        and inner.end.x <= outer.end.x + tolerance \
        and inner.end.y <= outer.end.y + tolerance

func _control_rect(control: Control) -> Rect2:
    return Rect2(control.position, control.size)

func _visible_children_inside(panel: Control) -> PackedStringArray:
    var failures := PackedStringArray()
    var bounds := Rect2(Vector2.ZERO, panel.size)
    for child in panel.get_children():
        if child is Control and child.visible:
            var rect := _control_rect(child)
            if not _rect_inside(rect, bounds):
                failures.append("%s escapes %s: %s outside %s" % [child.name, panel.name, rect, bounds])
    return failures

func _assert_touch_controls(instance: Node, failures: PackedStringArray) -> void:
    var game: Rect2 = instance.current_game_rect
    var controls := [
        instance.virtual_joystick,
        instance.mobile_attack_button,
        instance.mobile_parry_button,
        instance.mobile_jump_button,
        instance.mobile_potion_button,
        instance.mobile_reset_button,
    ]
    for control in controls:
        var rect := _control_rect(control)
        if not _rect_inside(rect, game):
            failures.append("%s is outside the game rect" % control.name)
        if control != instance.virtual_joystick and (control.size.x < 48.0 or control.size.y < 42.0):
            failures.append("%s is too small for touch" % control.name)
    if instance.virtual_joystick.size.x < 92.0 or instance.virtual_joystick.size.y < 92.0:
        failures.append("joystick is too small")
    var action_controls := [instance.mobile_attack_button, instance.mobile_parry_button, instance.mobile_jump_button, instance.mobile_potion_button, instance.mobile_reset_button]
    for index in range(action_controls.size()):
        for other_index in range(index + 1, action_controls.size()):
            if _control_rect(action_controls[index]).intersects(_control_rect(action_controls[other_index])):
                failures.append("%s overlaps %s" % [action_controls[index].name, action_controls[other_index].name])
    if _control_rect(instance.virtual_joystick).intersects(_control_rect(instance.mobile_attack_button)) or _control_rect(instance.virtual_joystick).intersects(_control_rect(instance.mobile_parry_button)):
        failures.append("joystick overlaps action buttons")

func _run() -> void:
    var failures := PackedStringArray()
    var scene: PackedScene = load("res://scenes/main.tscn")
    var instance := scene.instantiate()
    root.add_child(instance)
    await process_frame
    await physics_frame

    instance.set_test_layout(Vector2(1152, 648), false)
    var desktop: Dictionary = instance.get_layout_metrics()
    if desktop["mode"] != "landscape": failures.append("desktop is not landscape")
    if desktop["left_panel"] != Rect2(0, 0, 230, 648): failures.append("desktop left panel changed")
    if desktop["game"] != Rect2(230, 0, 672, 648): failures.append("desktop game rect changed")
    if desktop["right_panel"] != Rect2(902, 0, 250, 648): failures.append("desktop right panel changed")
    if instance.mobile_controls_root.visible: failures.append("desktop shows mobile controls")
    failures.append_array(_visible_children_inside(instance.left_panel))
    failures.append_array(_visible_children_inside(instance.right_panel))

    instance.set_test_layout(Vector2(412, 915), true)
    var portrait: Dictionary = instance.get_layout_metrics()
    var top: Rect2 = portrait["left_panel"]
    var game: Rect2 = portrait["game"]
    var bottom: Rect2 = portrait["right_panel"]
    if portrait["mode"] != "portrait": failures.append("portrait mode was not selected")
    if top.position != Vector2.ZERO or top.size.x != 412.0: failures.append("portrait top panel is wrong")
    if top.end.y != game.position.y: failures.append("portrait top panel gaps or overlaps game")
    if game.end.y != bottom.position.y: failures.append("portrait bottom panel gaps or overlaps game")
    if bottom.end != Vector2(412, 915): failures.append("portrait layout does not fill viewport")
    if game.size.y < 270.0: failures.append("portrait playfield is too short")
    if not instance.mobile_controls_root.visible: failures.append("portrait mobile controls are hidden")
    if instance.content_detail_label.visible: failures.append("portrait shows verbose detail block")
    if instance.last_event_heading.visible: failures.append("portrait shows redundant event heading")
    failures.append_array(_visible_children_inside(instance.left_panel))
    failures.append_array(_visible_children_inside(instance.right_panel))
    _assert_touch_controls(instance, failures)

    instance.set_test_layout(Vector2(915, 412), true)
    var landscape: Dictionary = instance.get_layout_metrics()
    var left: Rect2 = landscape["left_panel"]
    var middle: Rect2 = landscape["game"]
    var right: Rect2 = landscape["right_panel"]
    if landscape["mode"] != "landscape": failures.append("touch landscape mode was not selected")
    if left.end.x != middle.position.x or middle.end.x != right.position.x: failures.append("touch landscape panels overlap or gap game")
    if right.end != Vector2(915, 412): failures.append("touch landscape does not fill viewport")
    if middle.size.x < 500.0: failures.append("touch landscape playfield is too narrow")
    if not instance.mobile_controls_root.visible: failures.append("touch landscape controls are hidden")
    failures.append_array(_visible_children_inside(instance.left_panel))
    failures.append_array(_visible_children_inside(instance.right_panel))
    _assert_touch_controls(instance, failures)

    instance.set_test_layout(Vector2(412, 915), true)
    var start_x: float = instance.player.position.x
    instance.virtual_joystick.set_vector_for_test(Vector2(0.85, 0.0))
    for _index in range(12): await physics_frame
    if instance.touch_move.x < 0.8: failures.append("joystick did not emit normalized horizontal input")
    if instance.player.position.x <= start_x: failures.append("joystick did not move player right")
    instance.virtual_joystick.release_for_test()
    while not instance.player.is_on_floor(): await physics_frame
    instance.virtual_joystick.set_vector_for_test(Vector2(0.0, -1.0))
    if not instance.touch_jump_requested: failures.append("upward joystick did not request jump")
    await physics_frame
    if instance.player.velocity.y >= 0.0: failures.append("joystick jump did not apply upward velocity")
    instance.virtual_joystick.release_for_test()
    if not instance.touch_move.is_zero_approx(): failures.append("joystick did not return to zero")

    instance.stamina = 50.0
    instance.mobile_attack_button.emit_signal("pressed")
    if not instance.attack_active or instance.stamina >= 50.0: failures.append("mobile attack button failed")
    instance._finish_attack()
    instance.stamina = 50.0
    instance.mobile_parry_button.emit_signal("pressed")
    if not instance.parry_active or instance.stamina >= 50.0: failures.append("mobile parry button failed")
    instance.touch_jump_requested = false
    instance.mobile_jump_button.emit_signal("pressed")
    if not instance.touch_jump_requested: failures.append("mobile jump button failed")

    if failures.is_empty():
        print(JSON.stringify({"ok": true, "desktop": desktop, "portrait": portrait, "touch_landscape": landscape, "joystick": "normalized+return", "mobile_actions": ["attack", "parry", "jump"]}))
        quit(0)
    else:
        push_error("; ".join(failures))
        quit(1)
