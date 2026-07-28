extends Node2D

const VIEW_SIZE := Vector2(1152, 648)
const LANDSCAPE_LEFT_MAX := 230.0
const LANDSCAPE_RIGHT_MAX := 250.0
const PORTRAIT_TOP_MIN := 150.0
const PORTRAIT_BOTTOM_MIN := 210.0
const FLOOR_Y := 590.0
const SEGMENT_WIDTH := 640.0
const GRAVITY := 1450.0
const JUMP_VELOCITY := -700.0
const RPG_CONTENT_PATH := "res://data/rpg_content.json"
const FORGE_KINDS := ["weapon", "armor", "loot", "consumable"]
const AUTO_IDEAS := {
    "weapon": "A standard practical medieval weapon for a beginning adventurer, with realistic materials and no magic or ornament overload.",
    "armor": "A standard practical medieval armor piece for a beginning adventurer, with realistic construction and no magic or ornament overload.",
    "loot": "A standard recognizable medieval loot container or key item with practical construction and no magical glow.",
    "consumable": "A standard recognizable medieval RPG consumable in a practical container with no magical aura."
}

var manifest: Dictionary = {}
var player_entry: Dictionary = {}
var player_content: Dictionary = {}
var player_stats: Dictionary = {}
var equipment: Dictionary = {}
var actions: Dictionary = {}
var world_root: Node2D
var terrain_root: Node2D
var object_root: Node2D
var player: CharacterBody2D
var player_sprite: AnimatedSprite2D
var camera: Camera2D
var attack_area: Area2D
var attack_collision: CollisionShape2D
var rpg_client: RPGContentClient

var generated_segments: Dictionary = {}
var objects_by_slug: Dictionary = {}
var inventory: Array[String] = []
var score := 0
var distance_meters := 0
var health := 1
var stamina := 1.0
var mana := 0
var max_health := 1
var max_stamina := 1.0
var max_mana := 0
var base_defense := 0
var armor_bonus := 0
var weapon_damage := 1
var move_speed := 330.0
var jump_was_down := false
var attack_active := false
var attack_cooldown := 0.0
var parry_active := false
var parry_timer := 0.0
var potion_count := 0
var next_spawn_x := 1900.0
var pending_spawn_x := 1900.0
var generation_sequence := 0

var stats_label: Label
var equipment_label: Label
var touch_label: Label
var forge_status_label: Label
var content_name_label: Label
var content_detail_label: Label
var controls_label: Label
var idea_input: LineEdit
var kind_selector: OptionButton
var generate_button: Button
var interface_canvas: CanvasLayer
var left_panel: Panel
var right_panel: Panel
var left_edge: ColorRect
var right_edge: ColorRect
var left_title_label: Label
var player_name_label: Label
var last_event_heading: Label
var forge_title_label: Label
var generate_heading: Label
var mobile_controls_root: Control
var virtual_joystick: VirtualJoystick
var mobile_attack_button: Button
var mobile_parry_button: Button
var mobile_jump_button: Button
var mobile_potion_button: Button
var mobile_reset_button: Button
var current_viewport_size := VIEW_SIZE
var current_browser_size := VIEW_SIZE
var current_left_rect := Rect2(0, 0, 230, 648)
var current_game_rect := Rect2(230, 0, 672, 648)
var current_right_rect := Rect2(902, 0, 250, 648)
var layout_mode := "landscape"
var touch_controls_enabled := false
var touch_move := Vector2.ZERO
var touch_jump_requested := false
var joystick_jump_latched := false
var layout_poll_remaining := 0.0
var test_layout_override := false
var dom_shell_active := false
var web_state_timer := 0.0
var _web_move_callback
var _web_action_callback
var _web_forge_callback

func _ready() -> void:
    if not _load_manifest():
        push_error("Grounded RPG content failed to load.")
        return
    _initialize_player_state()
    _build_world_roots()
    _ensure_world_ahead(4200.0)
    _build_player()
    _build_camera()
    _build_interface()
    rpg_client = RPGContentClient.new()
    rpg_client.name = "RPGContentClient"
    add_child(rpg_client)
    rpg_client.status_changed.connect(_on_forge_status)
    rpg_client.content_ready.connect(_on_runtime_content_ready)
    rpg_client.asset_ready.connect(_on_runtime_asset_ready)
    rpg_client.request_failed.connect(_on_forge_failed)
    _load_bootstrap_rpg_items()
    get_viewport().size_changed.connect(_on_viewport_size_changed)
    dom_shell_active = OS.has_feature("web")
    if dom_shell_active:
        interface_canvas.visible = false
        touch_controls_enabled = false
        _configure_web_canvas()
        _setup_web_bridge()
    else:
        _refresh_browser_metrics(true)
    _update_interface()
    _publish_web_state()

func _process(delta: float) -> void:
    if dom_shell_active:
        web_state_timer -= delta
        if web_state_timer <= 0.0:
            web_state_timer = 0.10
            _publish_web_state()
        return
    layout_poll_remaining -= delta
    if layout_poll_remaining <= 0.0:
        layout_poll_remaining = 0.35
        _refresh_browser_metrics(false)

func _setup_web_bridge() -> void:
    if not OS.has_feature("web"):
        return
    _web_move_callback = JavaScriptBridge.create_callback(_on_web_move)
    _web_action_callback = JavaScriptBridge.create_callback(_on_web_action)
    _web_forge_callback = JavaScriptBridge.create_callback(_on_web_forge)
    var window = JavaScriptBridge.get_interface("window")
    window.llmGameGodotMove = _web_move_callback
    window.llmGameGodotAction = _web_action_callback
    window.llmGameGodotForge = _web_forge_callback
    var shell = JavaScriptBridge.get_interface("llmGameShell")
    if shell != null:
        shell.godotReady()

func _on_web_move(args: Array) -> void:
    if args.size() < 2:
        return
    var next := Vector2(clampf(float(args[0]), -1.0, 1.0), clampf(float(args[1]), -1.0, 1.0))
    touch_move = next
    if next.y < -0.58 and not joystick_jump_latched:
        touch_jump_requested = true
        joystick_jump_latched = true
    elif next.y > -0.30:
        joystick_jump_latched = false

func _on_web_action(args: Array) -> void:
    if args.is_empty():
        return
    match str(args[0]):
        "attack": _perform_attack()
        "jump": touch_jump_requested = true
        "parry": _perform_parry()
        "potion": _use_health_potion()
        "reset": _reset_player()
    _publish_web_state()

func _on_web_forge(args: Array) -> void:
    if args.is_empty():
        return
    var kind := str(args[0]).to_lower()
    var idea := str(args[1]) if args.size() > 1 else ""
    _request_forge_kind(kind, idea)
    _publish_web_state()

func _configure_web_canvas() -> void:
    var size := get_viewport().get_visible_rect().size
    if size.x < 1.0 or size.y < 1.0:
        size = VIEW_SIZE
    current_viewport_size = size
    current_browser_size = size
    current_left_rect = Rect2()
    current_game_rect = Rect2(Vector2.ZERO, size)
    current_right_rect = Rect2()
    layout_mode = "stage"
    camera.offset = Vector2.ZERO
    camera.position.y = FLOOR_Y - size.y * 0.5 + clampf(size.y * 0.10, 34.0, 56.0)

func _publish_web_state() -> void:
    if not dom_shell_active or not OS.has_feature("web"):
        return
    var shell = JavaScriptBridge.get_interface("llmGameShell")
    if shell == null:
        return
    var payload := {
        "player_name": str(player_content.get("name", "Player")),
        "role": str(player_content.get("role", "warrior")).capitalize(),
        "level": int(player_content.get("level", 1)),
        "health": health,
        "max_health": max_health,
        "stamina": stamina,
        "max_stamina": max_stamina,
        "mana": mana,
        "max_mana": max_mana,
        "strength": int(player_stats.get("strength", 0)),
        "dexterity": int(player_stats.get("dexterity", 0)),
        "defense": _current_defense(),
        "damage": weapon_damage,
        "score": score,
        "distance": distance_meters,
        "main_hand": str(equipment.get("main_hand", "none")).replace("_", " ").capitalize(),
        "chest": str(equipment.get("chest", "none")).replace("_", " ").capitalize(),
        "off_hand": str(equipment.get("off_hand", "none")).replace("_", " ").capitalize(),
        "inventory": inventory.duplicate(),
        "event": touch_label.text if touch_label != null else "Ready.",
        "forge_status": forge_status_label.text if forge_status_label != null else "Forge ready.",
        "content_name": content_name_label.text if content_name_label != null else "Player ready.",
        "content_detail": content_detail_label.text if content_detail_label != null else "",
        "forge_busy": rpg_client != null and rpg_client.is_busy(),
        "viewport_width": int(current_viewport_size.x),
        "viewport_height": int(current_viewport_size.y)
    }
    shell.updateState(JSON.stringify(payload))

func _load_manifest() -> bool:
    if not FileAccess.file_exists(RPG_CONTENT_PATH):
        return false
    var file := FileAccess.open(RPG_CONTENT_PATH, FileAccess.READ)
    if file == null:
        return false
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    if not parsed is Dictionary:
        return false
    manifest = parsed
    if int(manifest.get("version", 0)) != 2:
        return false
    if not manifest.get("player", {}) is Dictionary or not manifest.get("world_items", []) is Array:
        return false
    player_entry = manifest["player"]
    player_content = player_entry.get("content", {})
    return not player_content.is_empty()

func _initialize_player_state() -> void:
    player_stats = player_content.get("stats", {}).duplicate(true)
    equipment = player_content.get("equipment", {}).duplicate(true)
    actions = player_content.get("actions", {}).duplicate(true)
    max_health = int(player_stats.get("max_hp", 1))
    max_stamina = float(player_stats.get("max_stamina", 1))
    max_mana = int(player_stats.get("max_mana", 0))
    health = int(player_stats.get("hp", max_health))
    stamina = float(player_stats.get("stamina", max_stamina))
    mana = int(player_stats.get("mana", max_mana))
    base_defense = int(player_stats.get("defense", 0))
    move_speed = 285.0 + float(player_stats.get("speed", 8)) * 6.0
    for entry_value in manifest.get("world_items", []):
        if not entry_value is Dictionary:
            continue
        var entry: Dictionary = entry_value
        var content: Dictionary = entry.get("content", {})
        match str(entry.get("kind", "")):
            "weapon":
                if str(content.get("weapon_type", "")) == str(equipment.get("main_hand", "")):
                    weapon_damage = int(content.get("stats", {}).get("damage", 1))
            "armor":
                if str(content.get("material", "")) == str(equipment.get("chest", "")):
                    armor_bonus = int(content.get("stats", {}).get("defense", 0))

func _physics_process(delta: float) -> void:
    if player == null:
        return
    attack_cooldown = maxf(0.0, attack_cooldown - delta)
    if parry_active:
        parry_timer -= delta
        if parry_timer <= 0.0:
            parry_active = false
            player_sprite.modulate = Color.WHITE
    stamina = minf(max_stamina, stamina + 18.0 * delta)
    var axis := touch_move.x
    if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): axis -= 1.0
    if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): axis += 1.0
    axis = clampf(axis, -1.0, 1.0)
    player.velocity.x = move_toward(player.velocity.x, axis * move_speed, 1900.0 * delta)
    if not player.is_on_floor():
        player.velocity.y += GRAVITY * delta
    var jump_down := Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP) or touch_jump_requested
    if jump_down and not jump_was_down and player.is_on_floor():
        player.velocity.y = JUMP_VELOCITY
        touch_label.text = "%s jumps." % player_content.get("name", "The warrior")
    jump_was_down = jump_down
    touch_jump_requested = false
    player.move_and_slide()
    player.position.x = maxf(80.0, player.position.x)
    if player.position.y > FLOOR_Y + maxf(220.0, current_viewport_size.y * 0.5):
        _reset_player()
    if axis != 0.0 and not attack_active:
        player_sprite.play("walk")
        player_sprite.flip_h = axis < 0.0
        player_sprite.position.y = -8.0 + sin(Time.get_ticks_msec() * 0.012) * 1.5
    elif not attack_active:
        player_sprite.play("idle")
        player_sprite.position.y = -8.0
    var target_camera_x := maxf(current_game_rect.size.x * 0.5, player.position.x + 20.0)
    camera.position.x = lerpf(camera.position.x, target_camera_x, 1.0 - exp(-6.0 * delta))
    distance_meters = max(distance_meters, int(player.position.x / 10.0))
    _ensure_world_ahead(player.position.x + 3600.0)
    _remove_far_behind_items()
    _maybe_generate_ahead()
    _update_interface()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        if not current_game_rect.has_point(event.position):
            return
        if event.button_index == MOUSE_BUTTON_LEFT:
            _perform_attack()
        elif event.button_index == MOUSE_BUTTON_RIGHT:
            _perform_parry()
        get_viewport().set_input_as_handled()
        return
    if not event is InputEventKey or not event.pressed or event.echo:
        return
    match event.keycode:
        KEY_F: _perform_attack()
        KEY_Q: _perform_parry()
        KEY_H: _use_health_potion()
        KEY_R: _reset_player()

func _build_world_roots() -> void:
    world_root = Node2D.new()
    world_root.name = "OpenWorld"
    add_child(world_root)
    terrain_root = Node2D.new()
    terrain_root.name = "Terrain"
    world_root.add_child(terrain_root)
    object_root = Node2D.new()
    object_root.name = "RPGObjects"
    world_root.add_child(object_root)

func _build_player() -> void:
    player = CharacterBody2D.new()
    player.name = "Player"
    player.position = Vector2(360, 470)
    player.floor_snap_length = 12.0
    player.floor_stop_on_slope = true
    player.floor_max_angle = deg_to_rad(52.0)
    player.collision_layer = 1
    player.collision_mask = 1
    world_root.add_child(player)
    player_sprite = AnimatedSprite2D.new()
    player_sprite.name = "PlayerAnimation"
    player_sprite.sprite_frames = _load_player_frames()
    player_sprite.scale = Vector2(0.36, 0.36)
    player_sprite.position.y = -8.0
    player_sprite.play("idle")
    player.add_child(player_sprite)
    var collision := CollisionShape2D.new()
    collision.name = "PlayerCollision"
    var capsule := CapsuleShape2D.new()
    capsule.radius = 23.0
    capsule.height = 74.0
    collision.shape = capsule
    player.add_child(collision)
    attack_area = Area2D.new()
    attack_area.name = "AttackArea"
    attack_area.collision_layer = 0
    attack_area.collision_mask = 2
    attack_area.monitoring = true
    attack_area.area_entered.connect(_on_attack_area_entered)
    player.add_child(attack_area)
    attack_collision = CollisionShape2D.new()
    var attack_shape := RectangleShape2D.new()
    attack_shape.size = Vector2(76, 58)
    attack_collision.shape = attack_shape
    attack_collision.position = Vector2(50, -4)
    attack_collision.disabled = true
    attack_area.add_child(attack_collision)

func _build_camera() -> void:
    camera = Camera2D.new()
    camera.name = "WorldCamera"
    camera.position = Vector2(VIEW_SIZE.x * 0.5, FLOOR_Y - VIEW_SIZE.y * 0.5 + 58.0)
    camera.limit_left = 0
    camera.enabled = true
    add_child(camera)

func _build_interface() -> void:
    interface_canvas = CanvasLayer.new()
    interface_canvas.name = "Interface"
    interface_canvas.layer = 10
    add_child(interface_canvas)

    left_panel = Panel.new()
    left_panel.name = "LeftPanel"
    left_panel.clip_contents = true
    left_panel.add_theme_stylebox_override("panel", _panel_style(Color("17130f"), Color("806744")))
    interface_canvas.add_child(left_panel)
    left_title_label = _heading("GROUND RPG")
    left_title_label.name = "LeftTitle"
    left_panel.add_child(left_title_label)
    player_name_label = _body_label("%s · LV %d %s" % [player_content.get("name", "Player"), int(player_content.get("level", 1)), str(player_content.get("role", "warrior")).capitalize()], 15)
    player_name_label.name = "PlayerName"
    player_name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    left_panel.add_child(player_name_label)
    stats_label = _body_label("", 14)
    stats_label.name = "Stats"
    stats_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    left_panel.add_child(stats_label)
    equipment_label = _body_label("", 13)
    equipment_label.name = "Equipment"
    equipment_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    left_panel.add_child(equipment_label)
    last_event_heading = _section_label("LAST EVENT")
    last_event_heading.name = "LastEventHeading"
    left_panel.add_child(last_event_heading)
    touch_label = _body_label("Walk right to reach the reviewed medieval equipment.", 13)
    touch_label.name = "LastEvent"
    touch_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    left_panel.add_child(touch_label)

    right_panel = Panel.new()
    right_panel.name = "RightPanel"
    right_panel.clip_contents = true
    right_panel.add_theme_stylebox_override("panel", _panel_style(Color("17130f"), Color("806744")))
    interface_canvas.add_child(right_panel)
    forge_title_label = _heading("GROUNDED FORGE")
    forge_title_label.name = "ForgeTitle"
    right_panel.add_child(forge_title_label)
    forge_status_label = _body_label("Strict schemas and visual review are active.", 13)
    forge_status_label.name = "ForgeStatus"
    forge_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    right_panel.add_child(forge_status_label)
    content_name_label = _body_label("PLAYER: %s" % player_content.get("name", "Unknown"), 15)
    content_name_label.name = "ContentName"
    content_name_label.modulate = Color("e7c27d")
    content_name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    right_panel.add_child(content_name_label)
    content_detail_label = _body_label(str(player_content.get("description", "")), 12)
    content_detail_label.name = "ContentDetail"
    content_detail_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    right_panel.add_child(content_detail_label)
    generate_heading = _section_label("GENERATE AHEAD")
    generate_heading.name = "GenerateHeading"
    right_panel.add_child(generate_heading)
    kind_selector = OptionButton.new()
    kind_selector.name = "KindSelector"
    kind_selector.focus_mode = Control.FOCUS_ALL
    for kind in FORGE_KINDS:
        kind_selector.add_item(kind.capitalize())
    kind_selector.selected = 2
    right_panel.add_child(kind_selector)
    idea_input = LineEdit.new()
    idea_input.name = "IdeaInput"
    idea_input.placeholder_text = "plain sword, oak chest..."
    idea_input.max_length = 300
    idea_input.text_submitted.connect(_on_idea_submitted)
    right_panel.add_child(idea_input)
    generate_button = Button.new()
    generate_button.name = "GenerateButton"
    generate_button.text = "GENERATE REVIEWED ASSET"
    generate_button.pressed.connect(_on_generate_pressed)
    right_panel.add_child(generate_button)
    controls_label = _body_label("A/D or arrows · move\nSpace/W/Up · jump\nF or left click · slash\nQ or right click · parry\nH · drink stored potion\nR · reset", 12)
    controls_label.name = "Controls"
    controls_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    right_panel.add_child(controls_label)

    left_edge = ColorRect.new()
    left_edge.name = "FirstPanelBoundary"
    left_edge.color = Color("806744")
    interface_canvas.add_child(left_edge)
    right_edge = ColorRect.new()
    right_edge.name = "SecondPanelBoundary"
    right_edge.color = Color("806744")
    interface_canvas.add_child(right_edge)

    mobile_controls_root = Control.new()
    mobile_controls_root.name = "MobileControls"
    mobile_controls_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
    interface_canvas.add_child(mobile_controls_root)
    virtual_joystick = VirtualJoystick.new()
    virtual_joystick.name = "MovementJoystick"
    virtual_joystick.vector_changed.connect(_on_joystick_vector)
    mobile_controls_root.add_child(virtual_joystick)
    mobile_attack_button = _mobile_button("ATK", "AttackButton")
    mobile_attack_button.pressed.connect(_perform_attack)
    mobile_controls_root.add_child(mobile_attack_button)
    mobile_parry_button = _mobile_button("PARRY", "ParryButton")
    mobile_parry_button.pressed.connect(_perform_parry)
    mobile_controls_root.add_child(mobile_parry_button)
    mobile_jump_button = _mobile_button("JUMP", "JumpButton")
    mobile_jump_button.pressed.connect(_on_mobile_jump_pressed)
    mobile_controls_root.add_child(mobile_jump_button)
    mobile_potion_button = _mobile_button("POTION", "PotionButton")
    mobile_potion_button.pressed.connect(_use_health_potion)
    mobile_controls_root.add_child(mobile_potion_button)
    mobile_reset_button = _mobile_button("RESET", "ResetButton")
    mobile_reset_button.pressed.connect(_reset_player)
    mobile_controls_root.add_child(mobile_reset_button)

    _apply_responsive_layout()

func _browser_metrics() -> Dictionary:
    var test_width := OS.get_environment("LLM_GAME_TEST_BROWSER_WIDTH").to_float()
    var test_height := OS.get_environment("LLM_GAME_TEST_BROWSER_HEIGHT").to_float()
    if test_width > 0.0 and test_height > 0.0:
        return {"width": test_width, "height": test_height, "touch": OS.get_environment("LLM_GAME_FORCE_TOUCH") == "1", "android": false}
    if OS.has_feature("web"):
        var script := "JSON.stringify({width:(window.visualViewport?window.visualViewport.width:window.innerWidth),height:(window.visualViewport?window.visualViewport.height:window.innerHeight),touch:(navigator.maxTouchPoints>0||matchMedia('(pointer: coarse)').matches||new URLSearchParams(location.search).get('touch')==='1'),android:/Android/i.test(navigator.userAgent)})"
        var raw: Variant = JavaScriptBridge.eval(script, true)
        var parsed: Variant = JSON.parse_string(str(raw))
        if parsed is Dictionary:
            return parsed
    var viewport_size := get_viewport().get_visible_rect().size
    return {"width": viewport_size.x, "height": viewport_size.y, "touch": OS.get_environment("LLM_GAME_FORCE_TOUCH") == "1", "android": false}

func _refresh_browser_metrics(force: bool) -> void:
    if left_panel == null:
        return
    if test_layout_override and not force:
        return
    var metrics := _browser_metrics()
    var browser_size := Vector2(maxf(1.0, float(metrics.get("width", VIEW_SIZE.x))), maxf(1.0, float(metrics.get("height", VIEW_SIZE.y))))
    var viewport_size := get_viewport().get_visible_rect().size
    if viewport_size.x < 320.0 or viewport_size.y < 240.0:
        viewport_size = VIEW_SIZE
    var next_mode := "portrait" if browser_size.y > browser_size.x else "landscape"
    var next_touch := bool(metrics.get("touch", false)) or bool(metrics.get("android", false)) or next_mode == "portrait" or OS.get_environment("LLM_GAME_FORCE_TOUCH") == "1"
    var changed := force or not current_browser_size.is_equal_approx(browser_size) or not current_viewport_size.is_equal_approx(viewport_size) or layout_mode != next_mode or touch_controls_enabled != next_touch
    if not changed:
        return
    current_browser_size = browser_size
    current_viewport_size = viewport_size
    layout_mode = next_mode
    touch_controls_enabled = next_touch
    _update_interface()
    _apply_responsive_layout()

func _on_viewport_size_changed() -> void:
    if dom_shell_active:
        _configure_web_canvas()
        _publish_web_state()
    else:
        _refresh_browser_metrics(true)

func set_test_layout(browser_size: Vector2, touch: bool) -> void:
    test_layout_override = true
    current_browser_size = browser_size
    current_viewport_size = browser_size
    layout_mode = "portrait" if browser_size.y > browser_size.x else "landscape"
    touch_controls_enabled = touch or layout_mode == "portrait"
    _update_interface()
    _apply_responsive_layout()

func _apply_responsive_layout() -> void:
    if left_panel == null:
        return
    var surface := current_viewport_size
    if surface.x < 320.0 or surface.y < 240.0:
        surface = VIEW_SIZE
    if layout_mode == "portrait":
        _layout_portrait(surface)
    else:
        _layout_landscape(surface)
    mobile_controls_root.position = Vector2.ZERO
    mobile_controls_root.size = surface
    mobile_controls_root.visible = touch_controls_enabled
    _layout_mobile_controls()
    var viewport_center := surface * 0.5
    camera.offset = current_game_rect.get_center() - viewport_center
    var floor_margin := clampf(current_game_rect.size.y * 0.10, 36.0, 58.0)
    camera.position.y = FLOOR_Y - current_game_rect.size.y * 0.5 + floor_margin

func _layout_landscape(surface: Vector2) -> void:
    var compact := surface.y < 540.0 or surface.x < 900.0
    _set_responsive_fonts(compact, false)
    var left_min := 138.0 if compact else 170.0
    var right_min := 158.0 if compact else 190.0
    var left_width := clampf(surface.x * 0.20, left_min, LANDSCAPE_LEFT_MAX)
    var right_width := clampf(surface.x * 0.22, right_min, LANDSCAPE_RIGHT_MAX)
    if surface.x - left_width - right_width < 340.0:
        var shortage := 340.0 - (surface.x - left_width - right_width)
        left_width = maxf(118.0, left_width - shortage * 0.45)
        right_width = maxf(138.0, right_width - shortage * 0.55)
    current_left_rect = Rect2(0, 0, left_width, surface.y)
    current_game_rect = Rect2(left_width, 0, maxf(1.0, surface.x - left_width - right_width), surface.y)
    current_right_rect = Rect2(surface.x - right_width, 0, right_width, surface.y)
    _set_control_rect(left_panel, current_left_rect)
    _set_control_rect(right_panel, current_right_rect)
    _set_control_rect(left_edge, Rect2(current_game_rect.position.x - 2.0, 0, 2.0, surface.y))
    _set_control_rect(right_edge, Rect2(current_game_rect.end.x, 0, 2.0, surface.y))
    var pad := 9.0 if compact else 14.0
    var left_width_inner := left_width - pad * 2.0
    _set_control_rect(left_title_label, Rect2(pad, 8 if compact else 14, left_width_inner, 24))
    _set_control_rect(player_name_label, Rect2(pad, 31 if compact else 43, left_width_inner, 38))
    var stats_y := 62.0 if compact else 84.0
    var stats_height := maxf(82.0, surface.y * (0.23 if compact else 0.24))
    _set_control_rect(stats_label, Rect2(pad, stats_y, left_width_inner, stats_height))
    var equipment_y := stats_y + stats_height + 3.0
    var equipment_height := maxf(82.0, surface.y * (0.23 if compact else 0.27))
    _set_control_rect(equipment_label, Rect2(pad, equipment_y, left_width_inner, equipment_height))
    var event_y := equipment_y + equipment_height + 3.0
    _set_control_rect(last_event_heading, Rect2(pad, event_y, left_width_inner, 20))
    _set_control_rect(touch_label, Rect2(pad, event_y + 20.0, left_width_inner, maxf(20.0, surface.y - event_y - 28.0)))

    var right_width_inner := right_width - pad * 2.0
    _set_control_rect(forge_title_label, Rect2(pad, 8 if compact else 14, right_width_inner, 24))
    _set_control_rect(forge_status_label, Rect2(pad, 31 if compact else 43, right_width_inner, 48 if compact else 58))
    _set_control_rect(content_name_label, Rect2(pad, 82 if compact else 105, right_width_inner, 28))
    content_detail_label.visible = not compact
    if compact:
        _set_control_rect(content_detail_label, Rect2())
        _set_control_rect(generate_heading, Rect2(pad, 112, right_width_inner, 20))
        _set_control_rect(kind_selector, Rect2(pad, 135, right_width_inner, 32))
        _set_control_rect(idea_input, Rect2(pad, 171, right_width_inner, 34))
        _set_control_rect(generate_button, Rect2(pad, 209, right_width_inner, 38))
        _set_control_rect(controls_label, Rect2(pad, 253, right_width_inner, maxf(30.0, surface.y - 260.0)))
    else:
        _set_control_rect(content_detail_label, Rect2(pad, 136, right_width_inner, 112))
        _set_control_rect(generate_heading, Rect2(pad, 258, right_width_inner, 20))
        _set_control_rect(kind_selector, Rect2(pad, 283, right_width_inner, 36))
        _set_control_rect(idea_input, Rect2(pad, 325, right_width_inner, 36))
        _set_control_rect(generate_button, Rect2(pad, 367, right_width_inner, 42))
        _set_control_rect(controls_label, Rect2(pad, 421, right_width_inner, maxf(30.0, surface.y - 430.0)))
    last_event_heading.visible = true
    controls_label.visible = true

func _layout_portrait(surface: Vector2) -> void:
    _set_responsive_fonts(true, true)
    var top_height := clampf(surface.y * 0.22, PORTRAIT_TOP_MIN, minf(220.0, surface.y * 0.27))
    var bottom_height := clampf(surface.y * 0.28, PORTRAIT_BOTTOM_MIN, minf(300.0, surface.y * 0.34))
    if surface.y - top_height - bottom_height < 270.0:
        var shortage := 270.0 - (surface.y - top_height - bottom_height)
        top_height = maxf(128.0, top_height - shortage * 0.42)
        bottom_height = maxf(184.0, bottom_height - shortage * 0.58)
    current_left_rect = Rect2(0, 0, surface.x, top_height)
    current_game_rect = Rect2(0, top_height, surface.x, maxf(1.0, surface.y - top_height - bottom_height))
    current_right_rect = Rect2(0, surface.y - bottom_height, surface.x, bottom_height)
    _set_control_rect(left_panel, current_left_rect)
    _set_control_rect(right_panel, current_right_rect)
    _set_control_rect(left_edge, Rect2(0, current_game_rect.position.y - 2.0, surface.x, 2.0))
    _set_control_rect(right_edge, Rect2(0, current_game_rect.end.y, surface.x, 2.0))
    var pad := 10.0
    _set_control_rect(left_title_label, Rect2(pad, 7, surface.x - pad * 2.0, 22))
    _set_control_rect(player_name_label, Rect2(pad, 30, surface.x - pad * 2.0, 25))
    var half := (surface.x - pad * 3.0) * 0.5
    _set_control_rect(stats_label, Rect2(pad, 56, half, maxf(48.0, top_height - 112.0)))
    _set_control_rect(equipment_label, Rect2(pad * 2.0 + half, 56, half, maxf(48.0, top_height - 112.0)))
    last_event_heading.visible = false
    _set_control_rect(last_event_heading, Rect2())
    _set_control_rect(touch_label, Rect2(pad, maxf(108.0, top_height - 50.0), surface.x - pad * 2.0, 44))

    _set_control_rect(forge_title_label, Rect2(pad, 7, surface.x - pad * 2.0, 22))
    _set_control_rect(forge_status_label, Rect2(pad, 31, surface.x - pad * 2.0, 38))
    _set_control_rect(content_name_label, Rect2(pad, 71, surface.x - pad * 2.0, 24))
    content_detail_label.visible = false
    _set_control_rect(content_detail_label, Rect2())
    _set_control_rect(generate_heading, Rect2(pad, 97, surface.x - pad * 2.0, 18))
    var row_y := 118.0
    var gap := 6.0
    var selector_width := maxf(92.0, surface.x * 0.25)
    var button_width := maxf(98.0, surface.x * 0.27)
    var input_width := maxf(80.0, surface.x - pad * 2.0 - selector_width - button_width - gap * 2.0)
    _set_control_rect(kind_selector, Rect2(pad, row_y, selector_width, 42))
    _set_control_rect(idea_input, Rect2(pad + selector_width + gap, row_y, input_width, 42))
    _set_control_rect(generate_button, Rect2(surface.x - pad - button_width, row_y, button_width, 42))
    controls_label.visible = true
    _set_control_rect(controls_label, Rect2(pad, 166, surface.x - pad * 2.0, maxf(24.0, bottom_height - 174.0)))

func _layout_mobile_controls() -> void:
    if not touch_controls_enabled:
        touch_move = Vector2.ZERO
        virtual_joystick.release_for_test()
        return
    var game := current_game_rect
    var stick_size := clampf(minf(game.size.x * 0.29, game.size.y * 0.37), 92.0, 126.0)
    if game.size.y < 310.0:
        stick_size = minf(stick_size, 94.0)
    _set_control_rect(virtual_joystick, Rect2(game.position.x + 12.0, game.end.y - stick_size - 12.0, stick_size, stick_size))
    var button_size := clampf(minf(game.size.x * 0.14, game.size.y * 0.18), 50.0, 64.0)
    var gap := 7.0
    var grid_width := button_size * 2.0 + gap
    var grid_height := button_size * 2.0 + gap
    var grid_x := game.end.x - grid_width - 12.0
    var grid_y := game.end.y - grid_height - 12.0
    _set_control_rect(mobile_attack_button, Rect2(grid_x, grid_y, button_size, button_size))
    _set_control_rect(mobile_jump_button, Rect2(grid_x + button_size + gap, grid_y, button_size, button_size))
    _set_control_rect(mobile_parry_button, Rect2(grid_x, grid_y + button_size + gap, button_size, button_size))
    _set_control_rect(mobile_potion_button, Rect2(grid_x + button_size + gap, grid_y + button_size + gap, button_size, button_size))
    _set_control_rect(mobile_reset_button, Rect2(game.end.x - 66.0, game.position.y + 10.0, 56.0, 42.0))

func _set_responsive_fonts(compact: bool, portrait: bool) -> void:
    left_title_label.add_theme_font_size_override("font_size", 17 if compact else 19)
    forge_title_label.add_theme_font_size_override("font_size", 17 if compact else 19)
    player_name_label.add_theme_font_size_override("font_size", 13 if compact else 15)
    stats_label.add_theme_font_size_override("font_size", 11 if compact else 14)
    equipment_label.add_theme_font_size_override("font_size", 11 if compact else 13)
    touch_label.add_theme_font_size_override("font_size", 11 if compact else 13)
    forge_status_label.add_theme_font_size_override("font_size", 11 if compact else 13)
    content_name_label.add_theme_font_size_override("font_size", 12 if compact else 15)
    content_detail_label.add_theme_font_size_override("font_size", 11 if compact else 12)
    controls_label.add_theme_font_size_override("font_size", 10 if compact else 12)
    generate_button.text = "FORGE" if portrait or compact else "GENERATE REVIEWED ASSET"

func _set_control_rect(control: Control, rect: Rect2) -> void:
    control.position = rect.position
    control.size = rect.size

func _mobile_button(text: String, node_name: String) -> Button:
    var button := Button.new()
    button.name = node_name
    button.text = text
    button.focus_mode = Control.FOCUS_NONE
    button.mouse_filter = Control.MOUSE_FILTER_STOP
    button.add_theme_font_size_override("font_size", 12)
    var normal := StyleBoxFlat.new()
    normal.bg_color = Color(0.09, 0.075, 0.055, 0.78)
    normal.border_color = Color(0.88, 0.72, 0.42, 0.74)
    normal.set_border_width_all(2)
    normal.set_corner_radius_all(14)
    var pressed := normal.duplicate()
    pressed.bg_color = Color(0.36, 0.25, 0.12, 0.92)
    button.add_theme_stylebox_override("normal", normal)
    button.add_theme_stylebox_override("hover", normal)
    button.add_theme_stylebox_override("pressed", pressed)
    return button

func _on_joystick_vector(next: Vector2) -> void:
    touch_move = next
    if next.y < -0.58 and not joystick_jump_latched:
        touch_jump_requested = true
        joystick_jump_latched = true
    elif next.y > -0.30:
        joystick_jump_latched = false

func _on_mobile_jump_pressed() -> void:
    touch_jump_requested = true

func _margins(parent: Control) -> MarginContainer:
    var margins := MarginContainer.new()
    margins.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    margins.add_theme_constant_override("margin_left", 14)
    margins.add_theme_constant_override("margin_right", 14)
    margins.add_theme_constant_override("margin_top", 16)
    margins.add_theme_constant_override("margin_bottom", 16)
    parent.add_child(margins)
    return margins

func _ensure_world_ahead(target_x: float) -> void:
    var final_segment := int(ceil(target_x / SEGMENT_WIDTH))
    for index in range(final_segment + 1):
        if not generated_segments.has(index):
            _build_segment(index)

func _build_segment(index: int) -> void:
    generated_segments[index] = true
    var start_x := float(index) * SEGMENT_WIDTH
    var segment := Node2D.new()
    segment.name = "Segment_%d" % index
    terrain_root.add_child(segment)
    var sky := Polygon2D.new()
    sky.polygon = PackedVector2Array([Vector2(start_x, -300), Vector2(start_x + SEGMENT_WIDTH, -300), Vector2(start_x + SEGMENT_WIDTH, FLOOR_Y), Vector2(start_x, FLOOR_Y)])
    sky.color = Color("8fb8c6") if index % 2 == 0 else Color("94bdc9")
    segment.add_child(sky)
    var far_hill := Polygon2D.new()
    far_hill.polygon = PackedVector2Array([Vector2(start_x, FLOOR_Y - 120), Vector2(start_x + 170, FLOOR_Y - 230), Vector2(start_x + 360, FLOOR_Y - 145), Vector2(start_x + SEGMENT_WIDTH, FLOOR_Y - 210), Vector2(start_x + SEGMENT_WIDTH, FLOOR_Y), Vector2(start_x, FLOOR_Y)])
    far_hill.color = Color("6f8b67")
    segment.add_child(far_hill)
    _make_static_rect(segment, "Ground", Vector2(start_x + SEGMENT_WIDTH * 0.5, FLOOR_Y + 30), Vector2(SEGMENT_WIDTH + 4, 60), Color("5b4430"))
    var grass := Polygon2D.new()
    grass.polygon = PackedVector2Array([Vector2(start_x, FLOOR_Y - 5), Vector2(start_x + SEGMENT_WIDTH, FLOOR_Y - 5), Vector2(start_x + SEGMENT_WIDTH, FLOOR_Y + 5), Vector2(start_x, FLOOR_Y + 5)])
    grass.color = Color("526f3e")
    segment.add_child(grass)
    if index > 0:
        var platform_y := 440.0 - float((index * 37) % 70)
        var platform_width := 150.0 + float((index * 29) % 100)
        var platform_x := start_x + 180.0 + float((index * 79) % 260)
        _make_static_rect(segment, "StonePlatform", Vector2(platform_x, platform_y), Vector2(platform_width, 22), Color("746e63"), -0.06 if index % 3 == 0 else 0.0)
        if index % 2 == 1:
            _make_rigid_box(segment, "PhysicsCrate", Vector2(start_x + 500.0, 250.0), Vector2(48, 48), Color("806044"))

func _load_bootstrap_rpg_items() -> void:
    var loaded := 0
    var maximum := next_spawn_x
    for entry_value in manifest.get("world_items", []):
        if not entry_value is Dictionary:
            continue
        var entry: Dictionary = entry_value
        var spawn_x := float(entry.get("spawn_x", 0.0))
        if spawn_x <= 0.0:
            continue
        var area := _spawn_rpg_item(entry, spawn_x)
        if area != null:
            loaded += 1
            maximum = maxf(maximum, spawn_x)
    next_spawn_x = maximum + 420.0
    pending_spawn_x = next_spawn_x
    forge_status_label.text = "%d grounded reviewed items loaded; future items generate farther right." % loaded

func _spawn_rpg_item(entry: Dictionary, spawn_x: float) -> Area2D:
    var slug := str(entry.get("slug", ""))
    var kind := str(entry.get("kind", ""))
    var content: Dictionary = entry.get("content", {})
    var asset: Dictionary = entry.get("asset", {})
    if slug.is_empty() or not kind in FORGE_KINDS or content.is_empty():
        return null
    var area := Area2D.new()
    area.name = ("RPG_%s" % slug).validate_node_name()
    area.position = Vector2(spawn_x, _item_y(kind))
    area.collision_layer = 2
    area.collision_mask = 1
    area.set_meta("slug", slug)
    area.set_meta("entry", entry.duplicate(true))
    area.set_meta("consumed", false)
    area.set_meta("opened", false)
    object_root.add_child(area)
    var collision := CollisionShape2D.new()
    collision.name = "TouchCollision"
    var shape := CircleShape2D.new()
    shape.radius = _item_radius(kind)
    collision.shape = shape
    area.add_child(collision)
    var placeholder := Polygon2D.new()
    placeholder.name = "Placeholder"
    placeholder.polygon = _circle_points(_item_radius(kind), 24)
    placeholder.color = _kind_color(kind)
    area.add_child(placeholder)
    var animation := AnimatedSprite2D.new()
    animation.name = "GroundedAnimation"
    animation.visible = false
    area.add_child(animation)
    var sheet_path := str(asset.get("sheet_path", ""))
    if not sheet_path.is_empty():
        var texture: Texture2D = load(sheet_path)
        if texture != null:
            _apply_item_texture(area, texture, asset)
    area.body_entered.connect(_on_item_touched.bind(area))
    objects_by_slug[slug] = area
    return area

func _apply_item_texture(area: Area2D, texture: Texture2D, asset: Dictionary) -> bool:
    var frame_count := int(asset.get("frame_count", 0))
    var frame_width := int(asset.get("frame_width", 0))
    var frame_height := int(asset.get("frame_height", 0))
    if frame_count < 6 or texture.get_width() != frame_count * frame_width or texture.get_height() != frame_height:
        return false
    var frames := SpriteFrames.new()
    frames.remove_animation("default")
    frames.add_animation("idle")
    frames.set_animation_loop("idle", true)
    frames.set_animation_speed("idle", 1000.0 / float(max(60, int(asset.get("frame_duration_ms", 120)))))
    for index in range(frame_count):
        var atlas := AtlasTexture.new()
        atlas.atlas = texture
        atlas.region = Rect2(index * frame_width, 0, frame_width, frame_height)
        frames.add_frame("idle", atlas)
    var animation: AnimatedSprite2D = area.get_node("GroundedAnimation")
    animation.sprite_frames = frames
    animation.scale = Vector2.ONE * _item_scale(str(area.get_meta("entry").get("kind", "")))
    animation.visible = true
    animation.play("idle")
    area.get_node("Placeholder").visible = false
    area.set_meta("asset_ready", true)
    return true

func _on_item_touched(body: Node, area: Area2D) -> void:
    if body != player or bool(area.get_meta("consumed", false)):
        return
    _apply_rpg_interaction(area)

func _apply_rpg_interaction(area: Area2D) -> void:
    var entry: Dictionary = area.get_meta("entry")
    var kind := str(entry.get("kind", ""))
    var content: Dictionary = entry.get("content", {})
    var name := str(content.get("name", "Item"))
    match kind:
        "weapon":
            equipment[str(content.get("equip_slot", "main_hand"))] = str(content.get("weapon_type", "weapon"))
            weapon_damage = int(content.get("stats", {}).get("damage", weapon_damage))
            actions["basic_attack"] = str(content.get("actions", {}).get("primary", "attack"))
            actions["secondary_action"] = str(content.get("actions", {}).get("secondary", "guard"))
            _add_inventory(name)
            touch_label.text = "%s equipped. Damage %d; actions %s and %s." % [name, weapon_damage, actions["basic_attack"], actions["secondary_action"]]
            _consume_item(area)
        "armor":
            equipment[str(content.get("equip_slot", "chest"))] = str(content.get("material", "armor"))
            armor_bonus = int(content.get("stats", {}).get("defense", 0))
            _add_inventory(name)
            touch_label.text = "%s equipped on the chest. Defense is now %d." % [name, _current_defense()]
            _consume_item(area)
        "loot":
            if not bool(area.get_meta("opened", false)):
                area.set_meta("opened", true)
                area.set_meta("consumed", true)
                score += 25
                _add_inventory("Beginner chest loot")
                touch_label.text = "%s opened. Mixed beginner loot and 25 score gained." % name
                _animate_chest_open(area)
        "consumable":
            if health < max_health:
                health = mini(max_health, health + int(content.get("effect", {}).get("amount", 25)))
                touch_label.text = "%s used. Health restored to %d." % [name, health]
            else:
                potion_count += 1
                _add_inventory(name)
                touch_label.text = "%s stored. Press H after taking damage." % name
            _consume_item(area)
    content_name_label.text = "%s: %s" % [kind.to_upper(), name]
    content_detail_label.text = str(content.get("description", ""))
    _update_interface()

func _consume_item(area: Area2D) -> void:
    area.set_meta("consumed", true)
    objects_by_slug.erase(str(area.get_meta("slug")))
    var tween := create_tween()
    tween.tween_property(area, "scale", Vector2(0.15, 0.15), 0.18)
    tween.parallel().tween_property(area, "modulate:a", 0.0, 0.18)
    tween.tween_callback(area.queue_free)

func _animate_chest_open(area: Area2D) -> void:
    area.monitoring = false
    var animation: AnimatedSprite2D = area.get_node("GroundedAnimation")
    var tween := create_tween()
    tween.tween_property(animation, "rotation", -0.08, 0.18)
    tween.parallel().tween_property(animation, "position:y", -10.0, 0.18)
    tween.tween_property(animation, "modulate", Color(1.0, 0.9, 0.65, 1.0), 0.18)

func _perform_attack() -> void:
    if attack_cooldown > 0.0 or stamina < 8.0:
        return
    stamina -= 8.0
    attack_cooldown = 0.42
    attack_active = true
    attack_collision.position.x = -50.0 if player_sprite.flip_h else 50.0
    attack_collision.set_deferred("disabled", false)
    player_sprite.play("idle")
    var direction := -1.0 if player_sprite.flip_h else 1.0
    var tween := create_tween()
    tween.tween_property(player_sprite, "rotation", direction * 0.18, 0.08)
    tween.tween_property(player_sprite, "rotation", -direction * 0.08, 0.08)
    tween.tween_property(player_sprite, "rotation", 0.0, 0.08)
    tween.tween_callback(_finish_attack)
    touch_label.text = "%s uses %s for %d weapon damage." % [player_content.get("name", "Player"), actions.get("basic_attack", "attack"), weapon_damage]

func _finish_attack() -> void:
    attack_active = false
    attack_collision.set_deferred("disabled", true)

func _on_attack_area_entered(area: Area2D) -> void:
    if not attack_active:
        return
    var entry: Dictionary = area.get_meta("entry", {})
    if str(entry.get("kind", "")) == "loot" and not bool(area.get_meta("opened", false)):
        touch_label.text = "The sword strikes %s. Touch the chest to open it safely." % str(entry.get("content", {}).get("name", "the chest"))

func _perform_parry() -> void:
    if parry_active or stamina < 5.0:
        return
    stamina -= 5.0
    parry_active = true
    parry_timer = 0.45
    player_sprite.modulate = Color(0.85, 0.92, 1.0)
    touch_label.text = "%s assumes a %s stance." % [player_content.get("name", "Player"), actions.get("secondary_action", "guard")]

func _use_health_potion() -> void:
    if potion_count <= 0:
        touch_label.text = "No stored health potion."
        return
    if health >= max_health:
        touch_label.text = "Health is already full."
        return
    potion_count -= 1
    health = mini(max_health, health + 25)
    _remove_inventory_once("Red Health Potion")
    touch_label.text = "Stored health potion consumed. Health is %d." % health

func _reset_player() -> void:
    player.position = Vector2(maxf(360.0, camera.position.x - 180.0), 470.0)
    player.velocity = Vector2.ZERO
    touch_label.text = "%s returns to the road." % player_content.get("name", "Player")

func _add_inventory(name: String) -> void:
    inventory.append(name)
    while inventory.size() > 8:
        inventory.pop_front()

func _remove_inventory_once(name: String) -> void:
    var index := inventory.find(name)
    if index >= 0:
        inventory.remove_at(index)

func _on_generate_pressed() -> void:
    _request_forge(idea_input.text)

func _on_idea_submitted(text: String) -> void:
    _request_forge(text)

func _request_forge(text: String) -> void:
    var kind: String = FORGE_KINDS[kind_selector.selected]
    _request_forge_kind(kind, text)
    idea_input.clear()

func _request_forge_kind(kind: String, text: String) -> void:
    kind = kind.to_lower()
    if not kind in FORGE_KINDS:
        if forge_status_label != null:
            forge_status_label.text = "Unsupported forge type: %s" % kind
        return
    if rpg_client == null or rpg_client.is_busy():
        if forge_status_label != null:
            forge_status_label.text = "Wait for the current reviewed asset."
        return
    var idea := text.strip_edges()
    if idea.is_empty():
        idea = AUTO_IDEAS[kind]
    pending_spawn_x = maxf(next_spawn_x, player.position.x + maxf(360.0, current_game_rect.size.x * 0.82))
    generation_sequence += 1
    if generate_button != null:
        generate_button.disabled = true
    rpg_client.request_content(kind, idea, 128000 + distance_meters + generation_sequence)

func _maybe_generate_ahead() -> void:
    if OS.get_environment("LLM_GAME_DISABLE_LIVE_GENERATION") == "1":
        return
    if rpg_client == null or rpg_client.is_busy():
        return
    if next_spawn_x < player.position.x + maxf(2200.0, current_game_rect.size.x * 3.0):
        var kind: String = FORGE_KINDS[generation_sequence % FORGE_KINDS.size()]
        _request_forge_kind(kind, AUTO_IDEAS[kind])

func _on_runtime_content_ready(payload: Dictionary) -> void:
    var kind := str(payload.get("kind", ""))
    var content: Dictionary = payload.get("content", {})
    var slug := str(payload.get("slug", ""))
    var entry := {"slug": slug, "kind": kind, "content": content, "asset": {}}
    var spawn_x := maxf(pending_spawn_x, player.position.x + maxf(340.0, current_game_rect.size.x * 0.78))
    _spawn_rpg_item(entry, spawn_x)
    next_spawn_x = spawn_x + 560.0
    content_name_label.text = "FORGING: %s" % content.get("name", kind)
    content_detail_label.text = str(content.get("description", ""))

func _on_runtime_asset_ready(slug: String, texture: Texture2D, payload: Dictionary) -> void:
    if not objects_by_slug.has(slug) or not is_instance_valid(objects_by_slug[slug]):
        return
    var area: Area2D = objects_by_slug[slug]
    var asset: Dictionary = payload.get("asset", {})
    var entry: Dictionary = area.get_meta("entry")
    entry["asset"] = asset.duplicate(true)
    area.set_meta("entry", entry)
    if _apply_item_texture(area, texture, asset):
        forge_status_label.text = "%s passed canonical and animation review." % str(entry.get("content", {}).get("name", "Asset"))
    if generate_button != null:
        generate_button.disabled = false
    _publish_web_state()

func _on_forge_status(message: String) -> void:
    forge_status_label.text = message
    if rpg_client != null and generate_button != null:
        generate_button.disabled = rpg_client.is_busy()
    _publish_web_state()

func _on_forge_failed(message: String) -> void:
    forge_status_label.text = message
    if generate_button != null:
        generate_button.disabled = false
    _publish_web_state()

func _remove_far_behind_items() -> void:
    var stale: Array[String] = []
    for slug in objects_by_slug:
        var area: Area2D = objects_by_slug[slug]
        if not is_instance_valid(area):
            stale.append(slug)
        elif area.position.x < player.position.x - 1800.0 and not bool(area.get_meta("opened", false)):
            area.queue_free()
            stale.append(slug)
    for slug in stale:
        objects_by_slug.erase(slug)

func _update_interface() -> void:
    if stats_label == null:
        return
    var main_hand := str(equipment.get("main_hand", "none")).replace("_", " ").capitalize()
    var chest := str(equipment.get("chest", "none")).replace("_", " ").capitalize()
    var off_hand := str(equipment.get("off_hand", "none")).replace("_", " ").capitalize()
    var pack := ", ".join(inventory) if not inventory.is_empty() else "Empty"
    if layout_mode == "portrait":
        stats_label.text = "HP %d/%d  ST %d/%d\nMP %d/%d  DEF %d\nSTR %d  DEX %d  DMG %d" % [health, max_health, int(stamina), int(max_stamina), mana, max_mana, _current_defense(), int(player_stats.get("strength", 0)), int(player_stats.get("dexterity", 0)), weapon_damage]
        equipment_label.text = "MAIN %s\nCHEST %s\nPACK %s" % [main_hand, chest, pack]
    elif current_viewport_size.y < 540.0:
        stats_label.text = "HP %d/%d\nST %d/%d  MP %d/%d\nSTR %d DEX %d\nDEF %d DMG %d\nSCORE %d DIST %dm" % [health, max_health, int(stamina), int(max_stamina), mana, max_mana, int(player_stats.get("strength", 0)), int(player_stats.get("dexterity", 0)), _current_defense(), weapon_damage, score, distance_meters]
        equipment_label.text = "MAIN %s\nCHEST %s\nOFF %s\nPACK %s" % [main_hand, chest, off_hand, pack]
    else:
        stats_label.text = "HP  %d / %d\nST  %d / %d\nMP  %d / %d\nSTR %d  DEX %d\nDEF %d  DMG %d\nSCORE %d  DIST %d m" % [health, max_health, int(stamina), int(max_stamina), mana, max_mana, int(player_stats.get("strength", 0)), int(player_stats.get("dexterity", 0)), _current_defense(), weapon_damage, score, distance_meters]
        equipment_label.text = "EQUIPPED\nMain: %s\nChest: %s\nOff: %s\n\nPACK\n%s" % [main_hand, chest, off_hand, pack]
    generate_button.text = "FORGE" if layout_mode == "portrait" else "GENERATE REVIEWED ASSET"
    if touch_controls_enabled:
        controls_label.text = "STICK · move / push up to jump\nATK · slash   PARRY · guard\nPOTION · heal   RESET · return"
    else:
        controls_label.text = "A/D or arrows · move\nSpace/W/Up · jump\nF or left click · slash\nQ or right click · parry\nH · drink stored potion\nR · reset"

func _current_defense() -> int:
    return base_defense + armor_bonus

func _item_y(kind: String) -> float:
    return {"weapon": FLOOR_Y - 85.0, "armor": FLOOR_Y - 82.0, "loot": FLOOR_Y - 55.0, "consumable": FLOOR_Y - 58.0}.get(kind, FLOOR_Y - 60.0)

func _item_radius(kind: String) -> float:
    return {"weapon": 28.0, "armor": 36.0, "loot": 42.0, "consumable": 25.0}.get(kind, 30.0)

func _item_scale(kind: String) -> float:
    return {"weapon": 0.68, "armor": 0.65, "loot": 0.72, "consumable": 0.55}.get(kind, 0.65)

func _kind_color(kind: String) -> Color:
    return {"weapon": Color("a8b0b5"), "armor": Color("75808a"), "loot": Color("8a5b32"), "consumable": Color("a93232")}.get(kind, Color("8a7150"))

func _load_player_frames() -> SpriteFrames:
    var asset: Dictionary = player_entry.get("asset", {})
    var frames := SpriteFrames.new()
    frames.remove_animation("default")
    _add_player_animation(
        frames,
        "idle",
        str(asset.get("sheet_path", "")),
        int(asset.get("frame_count", 0)),
        int(asset.get("frame_width", 0)),
        int(asset.get("frame_height", 0)),
        1000.0 / float(max(60, int(asset.get("frame_duration_ms", 120))))
    )
    _add_player_animation(
        frames,
        "walk",
        str(asset.get("walk_sheet_path", asset.get("sheet_path", ""))),
        int(asset.get("walk_frame_count", asset.get("frame_count", 0))),
        int(asset.get("walk_frame_width", asset.get("frame_width", 0))),
        int(asset.get("walk_frame_height", asset.get("frame_height", 0))),
        1000.0 / float(max(60, int(asset.get("walk_frame_duration_ms", 120))))
    )
    return frames

func _add_player_animation(frames: SpriteFrames, animation_name: String, sheet_path: String, count: int, width: int, height: int, speed: float) -> void:
    var texture: Texture2D = load(sheet_path)
    if texture == null or count < 2 or width <= 0 or height <= 0:
        push_error("Invalid %s player animation asset: %s" % [animation_name, sheet_path])
        return
    if texture.get_width() != count * width or texture.get_height() != height:
        push_error("Unexpected %s player sheet dimensions: %s" % [animation_name, sheet_path])
        return
    frames.add_animation(animation_name)
    frames.set_animation_loop(animation_name, true)
    frames.set_animation_speed(animation_name, speed)
    for index in range(count):
        var atlas := AtlasTexture.new()
        atlas.atlas = texture
        atlas.region = Rect2(index * width, 0, width, height)
        frames.add_frame(animation_name, atlas)

func get_layout_metrics() -> Dictionary:
    return {"mode": layout_mode, "browser": current_browser_size, "viewport": current_viewport_size, "touch_controls": touch_controls_enabled, "left_panel": current_left_rect, "game": current_game_rect, "right_panel": current_right_rect}

func _panel_style(background: Color, border: Color) -> StyleBoxFlat:
    var style := StyleBoxFlat.new()
    style.bg_color = background
    style.border_color = border
    style.set_border_width_all(2)
    return style

func _heading(text: String) -> Label:
    var label := Label.new()
    label.text = text
    label.add_theme_font_size_override("font_size", 19)
    label.modulate = Color("f1dfbd")
    return label

func _section_label(text: String) -> Label:
    var label := _body_label(text, 12)
    label.modulate = Color("d8b675")
    return label

func _body_label(text: String, size: int) -> Label:
    var label := Label.new()
    label.text = text
    label.add_theme_font_size_override("font_size", size)
    label.modulate = Color("eadfc9")
    return label

func _make_static_rect(parent: Node, node_name: String, position: Vector2, size: Vector2, color: Color, rotation := 0.0) -> StaticBody2D:
    var body := StaticBody2D.new()
    body.name = node_name
    body.position = position
    body.rotation = rotation
    parent.add_child(body)
    var collision := CollisionShape2D.new()
    var shape := RectangleShape2D.new()
    shape.size = size
    collision.shape = shape
    body.add_child(collision)
    var visual := Polygon2D.new()
    visual.polygon = PackedVector2Array([Vector2(-size.x, -size.y) * 0.5, Vector2(size.x, -size.y) * 0.5, Vector2(size.x, size.y) * 0.5, Vector2(-size.x, size.y) * 0.5])
    visual.color = color
    body.add_child(visual)
    return body

func _make_rigid_box(parent: Node, node_name: String, position: Vector2, size: Vector2, color: Color) -> RigidBody2D:
    var body := RigidBody2D.new()
    body.name = node_name
    body.position = position
    body.mass = 1.4
    body.continuous_cd = RigidBody2D.CCD_MODE_CAST_RAY
    var material := PhysicsMaterial.new()
    material.bounce = 0.18
    material.friction = 0.82
    body.physics_material_override = material
    parent.add_child(body)
    var collision := CollisionShape2D.new()
    var shape := RectangleShape2D.new()
    shape.size = size
    collision.shape = shape
    body.add_child(collision)
    var visual := Polygon2D.new()
    visual.polygon = PackedVector2Array([Vector2(-size.x, -size.y) * 0.5, Vector2(size.x, -size.y) * 0.5, Vector2(size.x, size.y) * 0.5, Vector2(-size.x, size.y) * 0.5])
    visual.color = color
    body.add_child(visual)
    return body

func _circle_points(radius: float, count: int) -> PackedVector2Array:
    var points := PackedVector2Array()
    for index in range(count):
        points.append(Vector2.from_angle(TAU * float(index) / float(count)) * radius)
    return points
