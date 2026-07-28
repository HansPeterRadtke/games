extends Node2D

const DATA_PATH := "res://data/generated_world.json"
const VIEW_SIZE := Vector2(1152.0, 648.0)
const WORLD_MARGIN := Vector2(72.0, 82.0)
const PLAYER_SPEED := 220.0

var manifest: Dictionary = {}
var plan: Dictionary = {}
var assets: Dictionary = {}
var world_layer: Node2D
var player: CharacterBody2D
var player_sprite: AnimatedSprite2D
var projection_scale := 1.0
var projection_origin := Vector2.ZERO
var plan_min := Vector3.ZERO
var plan_max := Vector3.ONE
var touch_move := Vector2.ZERO
var nearby_entry: Dictionary = {}
var title_label: Label
var status_label: Label
var detail_label: Label
var _web_move_callback
var _web_action_callback
var _web_forge_callback

func _ready() -> void:
    if not _load_generated_manifest():
        _show_failure("Generated world manifest is missing, incomplete, or invalid. No fallback scene was loaded.")
        return
    _configure_projection()
    _build_room_background()
    _build_generated_objects()
    _build_generated_player()
    _build_overlay()
    if OS.has_feature("web"):
        _setup_web_bridge()
    _update_nearby_interaction()
    _publish_web_state()

func _physics_process(_delta: float) -> void:
    if player == null:
        return
    var direction := touch_move
    direction += Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    if direction.length() > 1.0:
        direction = direction.normalized()
    player.velocity = direction * PLAYER_SPEED
    player.move_and_slide()
    if player_sprite != null:
        if absf(direction.x) > 0.05:
            player_sprite.flip_h = direction.x < 0.0
        if direction.length() > 0.05:
            player_sprite.speed_scale = 1.3
        else:
            player_sprite.speed_scale = 1.0
    _update_nearby_interaction()
    if Input.is_action_just_pressed("ui_accept"):
        _interact()
    _publish_web_state()

func _load_generated_manifest() -> bool:
    if not FileAccess.file_exists(DATA_PATH):
        return false
    var file := FileAccess.open(DATA_PATH, FileAccess.READ)
    if file == null:
        return false
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    if not (parsed is Dictionary):
        return false
    manifest = parsed
    if int(manifest.get("version", 0)) != 1:
        return false
    if manifest.get("complete", false) != true or manifest.get("fallback_used", true) != false:
        return false
    if str(manifest.get("asset_engine", "")) != "thor-sdxl-reviewed-identity-anchored-animation":
        return false
    if not (manifest.get("scene_plan", {}) is Dictionary) or not (manifest.get("assets", {}) is Dictionary):
        return false
    plan = manifest["scene_plan"]
    assets = manifest["assets"]
    if str(plan.get("visual_generator", "")) != "thor_sdxl":
        return false
    var player_entry: Variant = plan.get("player", {})
    if not (player_entry is Dictionary) or not assets.has(str(player_entry.get("id", ""))):
        return false
    for value in plan.get("objects", []):
        if not (value is Dictionary):
            return false
        var entry: Dictionary = value
        if str(entry.get("visual_usage", "none")) != "none" and not assets.has(str(entry.get("id", ""))):
            return false
    return true

func _configure_projection() -> void:
    var bounds: Dictionary = plan.get("bounds", {})
    var minimum: Array = bounds.get("min", [-5.0, 0.0, -5.0])
    var maximum: Array = bounds.get("max", [5.0, 4.0, 5.0])
    plan_min = Vector3(float(minimum[0]), float(minimum[1]), float(minimum[2]))
    plan_max = Vector3(float(maximum[0]), float(maximum[1]), float(maximum[2]))
    var span_x := maxf(1.0, plan_max.x - plan_min.x)
    var span_z := maxf(1.0, plan_max.z - plan_min.z)
    var usable := VIEW_SIZE - WORLD_MARGIN * 2.0
    projection_scale = minf(usable.x / span_x, usable.y / span_z)
    projection_origin = WORLD_MARGIN - Vector2(plan_min.x, plan_min.z) * projection_scale

func _project(position_value: Variant) -> Vector2:
    var position: Array = position_value if position_value is Array else [0.0, 0.0, 0.0]
    return projection_origin + Vector2(float(position[0]), float(position[2])) * projection_scale

func _build_room_background() -> void:
    world_layer = Node2D.new()
    world_layer.name = "GeneratedWorld"
    world_layer.y_sort_enabled = true
    add_child(world_layer)
    var background := ColorRect.new()
    background.name = "GeneratedRoomBackdrop"
    background.position = Vector2.ZERO
    background.size = VIEW_SIZE
    background.color = Color("151112")
    background.mouse_filter = Control.MOUSE_FILTER_IGNORE
    add_child(background)
    move_child(background, 0)
    var border := Line2D.new()
    border.name = "GeneratedBounds"
    border.width = 3.0
    border.default_color = Color("b99b76")
    border.closed = true
    border.points = PackedVector2Array([
        _project([plan_min.x, 0.0, plan_min.z]),
        _project([plan_max.x, 0.0, plan_min.z]),
        _project([plan_max.x, 0.0, plan_max.z]),
        _project([plan_min.x, 0.0, plan_max.z]),
    ])
    add_child(border)

func _build_generated_objects() -> void:
    for value in plan.get("objects", []):
        if not (value is Dictionary):
            continue
        var entry: Dictionary = value
        var object_id := str(entry.get("id", ""))
        if str(entry.get("visual_usage", "none")) == "none":
            continue
        var asset: Dictionary = assets.get(object_id, {})
        var holder := Node2D.new()
        holder.name = ("Generated_%s" % object_id).validate_node_name()
        holder.position = _project(entry.get("position", [0.0, 0.0, 0.0]))
        holder.set_meta("entry", entry.duplicate(true))
        holder.set_meta("generated_asset", asset.duplicate(true))
        if str(entry.get("visual_usage", "")) == "tileable_texture":
            holder.z_index = -100
        else:
            holder.z_index = int(holder.position.y)
        world_layer.add_child(holder)
        var animation := _make_animation(asset, entry)
        animation.name = "GeneratedAnimation"
        holder.add_child(animation)
        var label := Label.new()
        label.name = "GeneratedLabel"
        label.text = str(entry.get("name", object_id))
        label.position = Vector2(-80.0, -_display_height(entry) * 0.55 - 20.0)
        label.size = Vector2(160.0, 22.0)
        label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
        label.add_theme_font_size_override("font_size", 12)
        label.modulate = Color("f6e8cf")
        holder.add_child(label)
        var blocking_type := str(entry.get("type", "")) not in ["terrain", "surface", "water"]
        if str(entry.get("collision", "none")) != "none" and blocking_type:
            _add_static_collision(holder, entry)

func _build_generated_player() -> void:
    var entry: Dictionary = plan.get("player", {})
    var object_id := str(entry.get("id", "player"))
    var asset: Dictionary = assets.get(object_id, {})
    player = CharacterBody2D.new()
    player.name = "GeneratedPlayer"
    player.position = _project(entry.get("position", [0.0, 0.0, 0.0]))
    player.collision_layer = 1
    player.collision_mask = 1
    player.set_meta("entry", entry.duplicate(true))
    player.set_meta("generated_asset", asset.duplicate(true))
    world_layer.add_child(player)
    player_sprite = _make_animation(asset, entry)
    player_sprite.name = "GeneratedPlayerAnimation"
    player.add_child(player_sprite)
    var collision := CollisionShape2D.new()
    collision.name = "GeneratedPlayerCollision"
    var shape := CapsuleShape2D.new()
    var size := _size_vector(entry)
    shape.radius = maxf(8.0, size.x * projection_scale * 0.34)
    shape.height = maxf(shape.radius * 2.0, size.z * projection_scale)
    collision.shape = shape
    player.add_child(collision)
    player.z_index = int(player.position.y) + 2

func _make_animation(asset: Dictionary, entry: Dictionary) -> AnimatedSprite2D:
    var sheet_path := str(asset.get("sheet_resource", ""))
    var texture: Texture2D = load(sheet_path)
    if texture == null:
        push_error("Missing generated sprite sheet: %s" % sheet_path)
    var count := int(asset.get("frame_count", 0))
    var width := int(asset.get("frame_width", 0))
    var height := int(asset.get("frame_height", 0))
    if texture == null or count < 6 or width < 64 or height < 64 or texture.get_width() != count * width or texture.get_height() != height:
        push_error("Invalid reviewed generated animation for %s" % str(entry.get("id", "unknown")))
    var frames := SpriteFrames.new()
    frames.remove_animation("default")
    frames.add_animation("generated")
    frames.set_animation_loop("generated", true)
    frames.set_animation_speed("generated", 1000.0 / float(max(60, int(asset.get("frame_duration_ms", 120)))))
    if texture != null:
        for index in range(count):
            var atlas := AtlasTexture.new()
            atlas.atlas = texture
            atlas.region = Rect2(index * width, 0, width, height)
            frames.add_frame("generated", atlas)
    var animation := AnimatedSprite2D.new()
    animation.sprite_frames = frames
    animation.centered = true
    var desired := _display_size(entry)
    animation.scale = Vector2(desired.x / maxf(1.0, float(width)), desired.y / maxf(1.0, float(height)))
    var model_position: Array = entry.get("position", [0.0, 0.0, 0.0])
    var vertical_offset := float(model_position[1]) * projection_scale * 0.45
    animation.position.y = -desired.y * 0.42 - vertical_offset
    animation.play("generated")
    return animation

func _size_vector(entry: Dictionary) -> Vector3:
    var values: Array = entry.get("size", [1.0, 1.0, 1.0])
    return Vector3(float(values[0]), float(values[1]), float(values[2]))

func _display_size(entry: Dictionary) -> Vector2:
    var size := _size_vector(entry)
    var usage := str(entry.get("visual_usage", "isolated_sprite"))
    if usage == "character_sprite":
        return Vector2(maxf(44.0, size.x * projection_scale), maxf(78.0, size.y * projection_scale))
    if usage == "tileable_texture":
        return Vector2(maxf(72.0, size.x * projection_scale), maxf(54.0, size.z * projection_scale))
    return Vector2(maxf(46.0, size.x * projection_scale), maxf(46.0, maxf(size.y, size.z) * projection_scale))

func _display_height(entry: Dictionary) -> float:
    return _display_size(entry).y

func _add_static_collision(holder: Node2D, entry: Dictionary) -> void:
    var body := StaticBody2D.new()
    body.name = "GeneratedCollisionBody"
    body.collision_layer = 1
    body.collision_mask = 1
    holder.add_child(body)
    var collision := CollisionShape2D.new()
    var shape := RectangleShape2D.new()
    var size := _size_vector(entry)
    shape.size = Vector2(maxf(12.0, size.x * projection_scale), maxf(12.0, size.z * projection_scale))
    collision.shape = shape
    body.add_child(collision)

func _build_overlay() -> void:
    var canvas := CanvasLayer.new()
    canvas.name = "GeneratedWorldInterface"
    canvas.layer = 20
    add_child(canvas)
    var panel := ColorRect.new()
    panel.position = Vector2(16.0, 14.0)
    panel.size = Vector2(490.0, 116.0)
    panel.color = Color(0.04, 0.03, 0.035, 0.88)
    canvas.add_child(panel)
    title_label = Label.new()
    title_label.position = Vector2(16.0, 10.0)
    title_label.size = Vector2(458.0, 26.0)
    title_label.text = "%s · %s" % [str(manifest.get("user_prompt", "Generated Game")), str(plan.get("scene_name", "Generated Scene"))]
    title_label.add_theme_font_size_override("font_size", 20)
    title_label.modulate = Color("f1c782")
    panel.add_child(title_label)
    status_label = Label.new()
    status_label.position = Vector2(16.0, 42.0)
    status_label.size = Vector2(458.0, 24.0)
    status_label.text = "All visible assets are reviewed Thor SDXL animations. Move with WASD or arrows; Enter interacts."
    status_label.add_theme_font_size_override("font_size", 13)
    panel.add_child(status_label)
    detail_label = Label.new()
    detail_label.position = Vector2(16.0, 70.0)
    detail_label.size = Vector2(458.0, 38.0)
    detail_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    detail_label.text = str(plan.get("player", {}).get("interaction", "Explore the generated scene."))
    detail_label.add_theme_font_size_override("font_size", 12)
    detail_label.modulate = Color("d8cbb8")
    panel.add_child(detail_label)

func _update_nearby_interaction() -> void:
    if player == null:
        return
    var nearest_distance := 96.0
    var nearest: Dictionary = {}
    for child in world_layer.get_children():
        if not (child is Node2D) or child == player or not child.has_meta("entry"):
            continue
        var entry: Dictionary = child.get_meta("entry")
        var interaction := str(entry.get("interaction", "none"))
        if interaction.strip_edges().to_lower() in ["", "none", "n/a", "no interaction"]:
            continue
        var distance := player.position.distance_to(child.position)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest = entry
    nearby_entry = nearest
    if detail_label != null:
        if nearby_entry.is_empty():
            detail_label.text = str(plan.get("player", {}).get("interaction", "Explore the generated scene."))
        else:
            detail_label.text = "%s: %s" % [str(nearby_entry.get("name", "Object")), str(nearby_entry.get("interaction", "Interact")).replace("_", " ")]

func _interact() -> void:
    if nearby_entry.is_empty():
        if status_label != null:
            status_label.text = "Nothing interactive is close enough."
        return
    if status_label != null:
        status_label.text = "%s · %s" % [str(nearby_entry.get("name", "Object")), str(nearby_entry.get("behavior", "The generated object responds.")).replace("_", " ")]

func _setup_web_bridge() -> void:
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
    touch_move = Vector2(clampf(float(args[0]), -1.0, 1.0), clampf(float(args[1]), -1.0, 1.0))

func _on_web_action(args: Array) -> void:
    if args.is_empty():
        return
    if str(args[0]) in ["attack", "jump", "parry", "potion"]:
        _interact()

func _on_web_forge(_args: Array) -> void:
    if status_label != null:
        status_label.text = "This build displays the fully generated opening scene; runtime continuation generation is the next environment step."

func _publish_web_state() -> void:
    if not OS.has_feature("web") or player == null:
        return
    var shell = JavaScriptBridge.get_interface("llmGameShell")
    if shell == null:
        return
    var player_entry: Dictionary = plan.get("player", {})
    var payload := {
        "player_name": str(player_entry.get("name", "Generated Player")),
        "role": "Generated adult child",
        "level": 1,
        "health": 100,
        "max_health": 100,
        "stamina": 100,
        "max_stamina": 100,
        "mana": 0,
        "max_mana": 0,
        "strength": 1,
        "dexterity": 1,
        "defense": 1,
        "damage": 0,
        "score": 0,
        "distance": int(player.position.length() / maxf(1.0, projection_scale)),
        "main_hand": "none",
        "chest": "generated clothes",
        "off_hand": "none",
        "inventory": [],
        "event": status_label.text if status_label != null else "Generated scene ready.",
        "forge_status": "Thor SDXL reviewed animations loaded.",
        "content_name": str(plan.get("scene_name", "Generated Scene")),
        "content_detail": str(manifest.get("opening_scene", "")).substr(0, 500),
        "forge_busy": false,
        "viewport_width": int(get_viewport_rect().size.x),
        "viewport_height": int(get_viewport_rect().size.y),
    }
    shell.updateState(JSON.stringify(payload))

func _show_failure(message: String) -> void:
    push_error(message)
    var label := Label.new()
    label.name = "GeneratedWorldFailure"
    label.position = Vector2(40.0, 40.0)
    label.size = Vector2(1000.0, 160.0)
    label.text = message
    label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    label.add_theme_font_size_override("font_size", 24)
    label.modulate = Color("ff6b6b")
    add_child(label)
