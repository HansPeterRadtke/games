extends Node2D

const DATA_PATH := "res://data/generated_world.json"
const FALLBACK_VIEW_SIZE := Vector2(1152.0, 648.0)
const WORLD_MARGIN := Vector2(48.0, 48.0)
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
var generated_animations: Dictionary = {}
var generated_nodes: Dictionary = {}
var generated_collisions: Dictionary = {}
var game_stats: Dictionary = {}
var inventory: Dictionary = {}
var object_states: Dictionary = {}
var action_cooldowns: Dictionary = {}
var touched_objects: Dictionary = {}
var game_over := false
var game_outcome := ""
var last_action_id := ""
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
    _initialize_gameplay()
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
    direction += Vector2(
        float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)),
        float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W))
    )
    if direction.length() > 1.0:
        direction = direction.normalized()
    player.velocity = direction * PLAYER_SPEED
    player.move_and_slide()
    if player_sprite != null:
        if absf(direction.x) > 0.05:
            player_sprite.flip_h = direction.x < 0.0
        _update_player_locomotion_animation()
    _update_nearby_interaction()
    _process_touch_actions()
    if Input.is_action_just_pressed("ui_accept"):
        if not _trigger_nearby_action("interact"):
            _trigger_player_action("interact")
    _publish_web_state()

func _desired_locomotion_clip() -> String:
    if player != null and player.velocity.length() > 5.0:
        return "walk"
    return "idle"

func _update_player_locomotion_animation() -> void:
    if player_sprite == null or player_sprite.sprite_frames == null:
        return
    var current := str(player_sprite.animation)
    if current not in ["idle", "walk"]:
        return
    var target := _desired_locomotion_clip()
    if current != target and player_sprite.sprite_frames.has_animation(target):
        player_sprite.play(target)
    player_sprite.speed_scale = 1.0

func _unhandled_key_input(event: InputEvent) -> void:
    if not (event is InputEventKey):
        return
    var key_event := event as InputEventKey
    if not key_event.pressed or key_event.echo:
        return
    if key_event.physical_keycode == KEY_E:
        if not _trigger_nearby_action("interact"):
            _trigger_player_action("interact")
        get_viewport().set_input_as_handled()
    elif key_event.physical_keycode == KEY_F:
        if not _trigger_nearby_action("hit"):
            _trigger_player_action("hit")
        get_viewport().set_input_as_handled()
    elif key_event.physical_keycode == KEY_Q:
        _trigger_player_action("use")
        get_viewport().set_input_as_handled()

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
    var engine := str(manifest.get("asset_engine", ""))
    if engine != "sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha":
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

func _layout_view_size() -> Vector2:
    var size := get_viewport_rect().size
    if size.x < 100.0 or size.y < 100.0:
        return FALLBACK_VIEW_SIZE
    return size

func _configure_projection() -> void:
    var bounds: Dictionary = plan.get("bounds", {})
    var minimum: Array = bounds.get("min", [-5.0, 0.0, -5.0])
    var maximum: Array = bounds.get("max", [5.0, 4.0, 5.0])
    plan_min = Vector3(float(minimum[0]), float(minimum[1]), float(minimum[2]))
    plan_max = Vector3(float(maximum[0]), float(maximum[1]), float(maximum[2]))
    var span_x := maxf(1.0, plan_max.x - plan_min.x)
    var span_z := maxf(1.0, plan_max.z - plan_min.z)
    var view_size := _layout_view_size()
    var usable := Vector2(maxf(100.0, view_size.x - WORLD_MARGIN.x * 2.0), maxf(100.0, view_size.y - WORLD_MARGIN.y * 2.0))
    projection_scale = minf(usable.x / span_x, usable.y / span_z)
    var projected_size := Vector2(span_x, span_z) * projection_scale
    var centering := (usable - projected_size) * 0.5
    projection_origin = WORLD_MARGIN + centering - Vector2(plan_min.x, plan_min.z) * projection_scale

func _project(position_value: Variant) -> Vector2:
    var position: Array = position_value if position_value is Array else [0.0, 0.0, 0.0]
    return projection_origin + Vector2(float(position[0]), float(position[2])) * projection_scale

func _room_rect() -> Rect2:
    var top_left := _project([plan_min.x, 0.0, plan_min.z])
    var bottom_right := _project([plan_max.x, 0.0, plan_max.z])
    return Rect2(top_left, bottom_right - top_left)

func _entry_role(entry: Dictionary) -> String:
    var object_id := str(entry.get("id", "")).to_lower()
    var name := str(entry.get("name", "")).to_lower()
    var description := str(entry.get("description", "")).to_lower()
    var combined := object_id + " " + name + " " + description
    if "carpet" in combined or "rug" in combined:
        return "rug"
    if str(entry.get("visual_usage", "")) == "tileable_texture":
        return "wall" if "wall" in combined else "floor"
    if "curtain" in combined:
        return "wall_hanging"
    if "door" in combined:
        return "wall_object"
    if "chandelier" in combined or "ceiling" in combined:
        return "ceiling_fixture"
    if "sideboard" in combined or "buffet" in combined or "cabinet" in combined:
        return "wall_furniture"
    return "world_object"

func _screen_position(entry: Dictionary) -> Vector2:
    var role := _entry_role(entry)
    var room := _room_rect()
    var wall_height := room.size.y * 0.34
    var projected := _project(entry.get("position", [0.0, 0.0, 0.0]))
    if role == "wall":
        return Vector2(room.get_center().x, room.position.y + wall_height * 0.5)
    if role == "floor":
        return Vector2(room.get_center().x, room.position.y + wall_height + (room.size.y - wall_height) * 0.5)
    if role == "rug":
        return Vector2(room.get_center().x, room.position.y + wall_height + (room.size.y - wall_height) * 0.58)
    if role == "wall_hanging":
        return Vector2(room.position.x + room.size.x * 0.76, room.position.y + wall_height * 0.48)
    if role == "wall_object":
        return Vector2(room.position.x + room.size.x * 0.30, room.position.y + wall_height * 0.62)
    if role == "ceiling_fixture":
        return Vector2(room.get_center().x, room.position.y + wall_height * 0.22)
    if role == "wall_furniture":
        return Vector2(room.position.x + room.size.x * 0.77, room.position.y + wall_height * 0.96)
    return projected

func _build_room_background() -> void:
    world_layer = Node2D.new()
    world_layer.name = "GeneratedWorld"
    world_layer.y_sort_enabled = true
    add_child(world_layer)
    var background := ColorRect.new()
    background.name = "GeneratedRoomBackdrop"
    background.position = Vector2.ZERO
    background.size = _layout_view_size()
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
        holder.position = _screen_position(entry)
        holder.set_meta("entry", entry.duplicate(true))
        holder.set_meta("generated_asset", asset.duplicate(true))
        var role := _entry_role(entry)
        if role == "wall":
            holder.z_index = -140
        elif role == "floor":
            holder.z_index = -130
        elif role == "rug":
            holder.z_index = -115
        elif role == "wall_hanging":
            holder.z_index = -90
        elif role == "ceiling_fixture":
            holder.z_index = -65
        elif role == "wall_object":
            holder.z_index = -55
        elif role == "wall_furniture":
            holder.z_index = -35
        else:
            holder.z_index = int(holder.position.y)
        world_layer.add_child(holder)
        generated_nodes[object_id] = holder
        object_states[object_id] = {}
        var animation := _make_animation(asset, entry)
        animation.name = "GeneratedAnimation"
        holder.add_child(animation)
        _decorate_architectural_asset(holder, role, _display_size(entry))
        generated_animations[object_id] = {"node": animation, "entry": entry.duplicate(true)}
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
    generated_nodes[object_id] = player
    object_states[object_id] = {}
    player_sprite = _make_animation(asset, entry)
    player_sprite.name = "GeneratedPlayerAnimation"
    player.add_child(player_sprite)
    generated_animations[object_id] = {"node": player_sprite, "entry": entry.duplicate(true)}
    var collision := CollisionShape2D.new()
    collision.name = "GeneratedPlayerCollision"
    var shape := CapsuleShape2D.new()
    var size := _size_vector(entry)
    shape.radius = maxf(8.0, size.x * projection_scale * 0.34)
    shape.height = maxf(shape.radius * 2.0, size.z * projection_scale)
    collision.shape = shape
    player.add_child(collision)
    generated_collisions[object_id] = collision
    player.z_index = int(player.position.y) + 2

func _add_animation_clip(frames: SpriteFrames, clip_name: String, clip: Dictionary, looped: bool) -> Vector2i:
    var sheet_path := str(clip.get("sheet_resource", ""))
    var texture: Texture2D = load(sheet_path)
    var count := int(clip.get("frame_count", 0))
    var width := int(clip.get("frame_width", 0))
    var height := int(clip.get("frame_height", 0))
    if texture == null or count < 2 or width < 64 or height < 64 or texture.get_width() != count * width or texture.get_height() != height:
        push_error("Invalid reviewed animation clip %s at %s" % [clip_name, sheet_path])
        return Vector2i.ZERO
    if frames.has_animation(clip_name):
        frames.remove_animation(clip_name)
    frames.add_animation(clip_name)
    frames.set_animation_loop(clip_name, looped)
    frames.set_animation_speed(clip_name, maxf(6.0, 1000.0 / float(max(60, int(clip.get("frame_duration_ms", 125))))))
    for index in range(count):
        var atlas := AtlasTexture.new()
        atlas.atlas = texture
        atlas.region = Rect2(index * width, 0, width, height)
        frames.add_frame(clip_name, atlas)
    return Vector2i(width, height)

func _make_animation(asset: Dictionary, entry: Dictionary) -> AnimatedSprite2D:
    var frames := SpriteFrames.new()
    frames.remove_animation("default")
    var frame_size := Vector2i.ZERO
    var clips_value: Variant = asset.get("clips", {})
    if clips_value is Dictionary and not clips_value.is_empty():
        var clips: Dictionary = clips_value
        for clip_key in clips.keys():
            var clip_name := str(clip_key)
            var clip_value: Variant = clips[clip_key]
            if not (clip_value is Dictionary):
                continue
            var loaded_size := _add_animation_clip(frames, clip_name, clip_value, clip_name in ["idle", "walk"])
            if clip_name == str(asset.get("default_clip", "idle")) or frame_size == Vector2i.ZERO:
                frame_size = loaded_size
    else:
        var legacy_clip := {
            "sheet_resource": str(asset.get("sheet_resource", "")),
            "frame_count": int(asset.get("frame_count", 0)),
            "frame_width": int(asset.get("frame_width", 0)),
            "frame_height": int(asset.get("frame_height", 0)),
            "frame_duration_ms": int(asset.get("frame_duration_ms", 120)),
        }
        frame_size = _add_animation_clip(frames, "idle", legacy_clip, true)
    if frame_size == Vector2i.ZERO or not frames.has_animation("idle"):
        push_error("No valid idle animation for %s" % str(entry.get("id", "unknown")))
    var animation := AnimatedSprite2D.new()
    animation.sprite_frames = frames
    animation.centered = true
    animation.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
    var desired := _display_size(entry)
    animation.scale = Vector2(desired.x / maxf(1.0, float(frame_size.x)), desired.y / maxf(1.0, float(frame_size.y)))
    var role := _entry_role(entry)
    if role in ["wall", "floor", "rug", "wall_hanging", "ceiling_fixture"]:
        animation.position = Vector2.ZERO
    else:
        var model_position: Array = entry.get("position", [0.0, 0.0, 0.0])
        var vertical_offset := float(model_position[1]) * projection_scale * 0.45
        animation.position.y = -desired.y * 0.42 - vertical_offset
    var is_player_animation := str(entry.get("id", "")) == "player"
    animation.animation_finished.connect(func() -> void:
        if animation.animation in ["idle", "walk"]:
            return
        var return_clip := "idle"
        if is_player_animation:
            return_clip = _desired_locomotion_clip()
        if animation.sprite_frames.has_animation(return_clip):
            animation.play(return_clip)
        elif animation.sprite_frames.has_animation("idle"):
            animation.play("idle")
    )
    animation.play(str(asset.get("default_clip", "idle")))
    return animation


func _make_outline(points: PackedVector2Array, color: Color, width: float, closed: bool = false) -> Line2D:
    var line := Line2D.new()
    line.points = points
    line.default_color = color
    line.width = width
    line.closed = closed
    line.antialiased = true
    line.z_index = 3
    line.z_as_relative = true
    return line

func _decorate_architectural_asset(holder: Node2D, role: String, display_size: Vector2) -> void:
    if role == "wall_hanging":
        var top := -display_size.y * 0.5
        holder.add_child(_make_outline(PackedVector2Array([
            Vector2(-display_size.x * 0.56, top - 8.0),
            Vector2(display_size.x * 0.56, top - 8.0),
        ]), Color("9b7447"), 7.0))
        holder.add_child(_make_outline(PackedVector2Array([
            Vector2(0.0, top + 4.0),
            Vector2(0.0, display_size.y * 0.5 - 4.0),
        ]), Color(0.82, 0.70, 0.53, 0.78), 3.0))
    elif role == "rug":
        var half := display_size * 0.5
        holder.add_child(_make_outline(PackedVector2Array([
            Vector2(-half.x, -half.y),
            Vector2(half.x, -half.y),
            Vector2(half.x, half.y),
            Vector2(-half.x, half.y),
        ]), Color("b58b59"), 6.0, true))
        var inner := half - Vector2(12.0, 12.0)
        holder.add_child(_make_outline(PackedVector2Array([
            Vector2(-inner.x, -inner.y),
            Vector2(inner.x, -inner.y),
            Vector2(inner.x, inner.y),
            Vector2(-inner.x, inner.y),
        ]), Color(0.40, 0.25, 0.16, 0.72), 2.0, true))
    elif role == "ceiling_fixture":
        holder.add_child(_make_outline(PackedVector2Array([
            Vector2(0.0, -display_size.y * 0.92),
            Vector2(0.0, -display_size.y * 0.48),
        ]), Color("8a6b45"), 5.0))
    elif role == "wall_furniture":
        var half := display_size * 0.5
        holder.add_child(_make_outline(PackedVector2Array([
            Vector2(-half.x, half.y - 3.0),
            Vector2(half.x, half.y - 3.0),
        ]), Color(0.12, 0.08, 0.05, 0.82), 5.0))

func _size_vector(entry: Dictionary) -> Vector3:
    var values: Array = entry.get("size", [1.0, 1.0, 1.0])
    return Vector3(float(values[0]), float(values[1]), float(values[2]))

func _display_size(entry: Dictionary) -> Vector2:
    var size := _size_vector(entry)
    var usage := str(entry.get("visual_usage", "isolated_sprite"))
    var role := _entry_role(entry)
    var room := _room_rect()
    var wall_height := room.size.y * 0.34
    if role == "wall":
        return Vector2(room.size.x, wall_height)
    if role == "floor":
        return Vector2(room.size.x, room.size.y - wall_height)
    if role == "rug":
        return Vector2(room.size.x * 0.66, (room.size.y - wall_height) * 0.56)
    if role == "wall_hanging":
        return Vector2(room.size.x * 0.31, wall_height * 0.76)
    if role == "wall_object":
        return Vector2(maxf(92.0, size.x * projection_scale * 2.4), maxf(154.0, size.y * projection_scale * 3.0))
    if usage == "character_sprite":
        return Vector2(maxf(96.0, size.x * projection_scale * 2.0), maxf(158.0, size.y * projection_scale * 2.0))
    if role == "ceiling_fixture":
        return Vector2(maxf(112.0, size.x * projection_scale * 2.8), maxf(96.0, size.y * projection_scale * 2.4))
    if role == "wall_furniture":
        return Vector2(maxf(138.0, size.x * projection_scale * 2.3), maxf(88.0, size.y * projection_scale * 1.8))
    return Vector2(maxf(76.0, size.x * projection_scale * 1.65), maxf(76.0, size.y * projection_scale * 1.65))


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
    generated_collisions[str(entry.get("id", ""))] = collision

func _build_overlay() -> void:
    title_label = Label.new()
    title_label.name = "GeneratedTitleState"
    title_label.text = "%s · %s" % [str(manifest.get("user_prompt", "Generated Game")), str(plan.get("scene_name", "Generated Scene"))]
    title_label.visible = false
    add_child(title_label)
    status_label = Label.new()
    status_label.name = "GeneratedStatusState"
    status_label.text = "Player uses reviewed StableAnimator pose-driven clips. Move with WASD or arrows; E interacts, F attacks, Q uses."
    status_label.visible = false
    add_child(status_label)
    detail_label = Label.new()
    detail_label.name = "GeneratedDetailState"
    detail_label.text = str(plan.get("player", {}).get("interaction", "Explore the generated scene."))
    detail_label.visible = false
    add_child(detail_label)


func _initialize_gameplay() -> void:
    var gameplay: Dictionary = plan.get("gameplay", {})
    for stat_value in gameplay.get("stats", []):
        if not (stat_value is Dictionary):
            continue
        var stat: Dictionary = stat_value
        game_stats[str(stat.get("id", ""))] = float(stat.get("initial", 0.0))
    for item_value in gameplay.get("starting_inventory", []):
        var item_id := str(item_value)
        inventory[item_id] = int(inventory.get(item_id, 0)) + 1
    status_label = null

func _all_entries() -> Array:
    var result: Array = []
    if plan.get("player", {}) is Dictionary:
        result.append(plan["player"])
    for value in plan.get("objects", []):
        if value is Dictionary:
            result.append(value)
    return result

func _entry_by_id(object_id: String) -> Dictionary:
    for entry_value in _all_entries():
        var entry: Dictionary = entry_value
        if str(entry.get("id", "")) == object_id:
            return entry
    return {}

func _actions_for(entry: Dictionary, input_name: String) -> Array:
    var result: Array = []
    for action_value in entry.get("actions", []):
        if not (action_value is Dictionary):
            continue
        var action: Dictionary = action_value
        if str(action.get("input", "")) == input_name:
            result.append(action)
    return result

func _find_nearest_entry(input_name: String) -> Dictionary:
    if player == null:
        return {}
    var nearest_distance := INF
    var nearest: Dictionary = {}
    for entry_value in plan.get("objects", []):
        if not (entry_value is Dictionary):
            continue
        var entry: Dictionary = entry_value
        if _actions_for(entry, input_name).is_empty():
            continue
        var object_id := str(entry.get("id", ""))
        var node: Node2D = generated_nodes.get(object_id)
        if node == null or not node.visible:
            continue
        var distance := player.position.distance_to(node.position)
        var actions := _actions_for(entry, input_name)
        var allowed := float(actions[0].get("range_meters", 1.5)) * projection_scale
        if distance <= maxf(48.0, allowed) and distance < nearest_distance:
            nearest_distance = distance
            nearest = entry
    return nearest

func _update_nearby_interaction() -> void:
    nearby_entry = _find_nearest_entry("interact")
    if detail_label == null:
        return
    if nearby_entry.is_empty():
        detail_label.text = str(plan.get("gameplay", {}).get("objective", "Explore the generated scene."))
    else:
        var actions := _actions_for(nearby_entry, "interact")
        detail_label.text = "%s: %s" % [str(nearby_entry.get("name", "Object")), str(actions[0].get("label", "Interact"))]

func _condition_passes(condition: Dictionary) -> bool:
    var condition_type := str(condition.get("type", ""))
    if condition_type == "state_equals":
        var target_state: Dictionary = object_states.get(str(condition.get("target_id", "")), {})
        return str(target_state.get(str(condition.get("key", "")), "")) == str(condition.get("value", ""))
    if condition_type == "stat_at_least":
        return float(game_stats.get(str(condition.get("stat", "")), 0.0)) >= float(condition.get("minimum", 0.0))
    if condition_type == "inventory_contains":
        return int(inventory.get(str(condition.get("item_id", "")), 0)) >= int(condition.get("count", 1))
    if condition_type == "object_visible":
        var target_node: Node2D = generated_nodes.get(str(condition.get("target_id", "")))
        return target_node != null and target_node.visible == bool(condition.get("visible", true))
    return false

func _action_available(action: Dictionary) -> bool:
    var action_id := str(action.get("id", ""))
    if Time.get_ticks_msec() < int(action_cooldowns.get(action_id, 0)):
        return false
    for value in action.get("conditions", []):
        if value is Dictionary and not _condition_passes(value):
            return false
    return true

func _set_event(text: String) -> void:
    if status_label != null:
        status_label.text = text
    if detail_label != null:
        detail_label.text = text

func _set_collision_enabled(target_id: String, enabled: bool) -> void:
    var collision: CollisionShape2D = generated_collisions.get(target_id)
    if collision != null:
        collision.set_deferred("disabled", not enabled)

func _apply_effect(effect: Dictionary) -> void:
    var effect_type := str(effect.get("type", ""))
    if effect_type == "show_message":
        _set_event(str(effect.get("text", "")))
    elif effect_type == "change_stat":
        var stat_id := str(effect.get("stat", ""))
        var amount := float(effect.get("amount", 0.0))
        var minimum := -10000.0
        var maximum := 10000.0
        for stat_value in plan.get("gameplay", {}).get("stats", []):
            if stat_value is Dictionary and str(stat_value.get("id", "")) == stat_id:
                minimum = float(stat_value.get("minimum", minimum))
                maximum = float(stat_value.get("maximum", maximum))
                break
        game_stats[stat_id] = clampf(float(game_stats.get(stat_id, 0.0)) + amount, minimum, maximum)
    elif effect_type == "set_state":
        var target_id := str(effect.get("target_id", ""))
        var target_state: Dictionary = object_states.get(target_id, {})
        target_state[str(effect.get("key", ""))] = str(effect.get("value", ""))
        object_states[target_id] = target_state
    elif effect_type in ["inventory_add", "inventory_remove"]:
        var item_id := str(effect.get("item_id", ""))
        var delta := int(effect.get("count", 1)) * (1 if effect_type == "inventory_add" else -1)
        inventory[item_id] = maxi(0, int(inventory.get(item_id, 0)) + delta)
    elif effect_type == "move":
        var move_id := str(effect.get("target_id", ""))
        var move_node: Node2D = generated_nodes.get(move_id)
        var offset: Array = effect.get("offset", [0.0, 0.0, 0.0])
        if move_node != null:
            var target_position := move_node.position + Vector2(float(offset[0]), float(offset[2])) * projection_scale
            var duration := float(effect.get("duration_seconds", 0.0))
            if duration > 0.0:
                create_tween().tween_property(move_node, "position", target_position, duration)
            else:
                move_node.position = target_position
    elif effect_type == "set_visibility":
        var visible_node: Node2D = generated_nodes.get(str(effect.get("target_id", "")))
        if visible_node != null:
            visible_node.visible = bool(effect.get("visible", true))
    elif effect_type == "set_collision":
        _set_collision_enabled(str(effect.get("target_id", "")), bool(effect.get("enabled", true)))
    elif effect_type == "remove_object":
        var remove_id := str(effect.get("target_id", ""))
        var remove_node: Node2D = generated_nodes.get(remove_id)
        if remove_node != null:
            remove_node.visible = false
            _set_collision_enabled(remove_id, false)
            var state: Dictionary = object_states.get(remove_id, {})
            state["removed"] = "true"
            object_states[remove_id] = state
    elif effect_type == "scene_transition":
        _set_event("The generated exit %s opens toward the next model-authored environment." % str(effect.get("exit_id", "")))
        var state: Dictionary = object_states.get("player", {})
        state["pending_exit"] = str(effect.get("exit_id", ""))
        object_states["player"] = state
    elif effect_type == "end_game":
        game_over = true
        game_outcome = str(effect.get("outcome", ""))
        _set_event(str(effect.get("text", "The game ends.")))

func _animation_has_clip(animation: AnimatedSprite2D, clip_name: String) -> bool:
    return animation != null and animation.sprite_frames != null and animation.sprite_frames.has_animation(clip_name)

func _play_clip(object_id: String, clip_name: String) -> void:
    var record: Dictionary = generated_animations.get(object_id, {})
    var animation: AnimatedSprite2D = record.get("node")
    if animation == null:
        return
    if not _animation_has_clip(animation, clip_name):
        push_warning("Missing required generated action clip %s for %s" % [clip_name, object_id])
        return
    animation.play(clip_name)

func _execute_action(owner: Dictionary, action: Dictionary) -> bool:
    if game_over or not _action_available(action):
        return false
    var action_id := str(action.get("id", ""))
    var cooldown := float(action.get("cooldown_seconds", 0.0))
    action_cooldowns[action_id] = Time.get_ticks_msec() + int(cooldown * 1000.0)
    last_action_id = action_id
    _play_clip(str(plan.get("player", {}).get("id", "player")), str(action.get("actor_clip", "")))
    _play_clip(str(owner.get("id", "")), str(action.get("target_clip", "")))
    for effect_value in action.get("effects", []):
        if effect_value is Dictionary:
            _apply_effect(effect_value)
    _set_event(str(action.get("success_text", action.get("description", "Action complete."))))
    return true

func _trigger_nearby_action(input_name: String) -> bool:
    var target := _find_nearest_entry(input_name)
    if target.is_empty():
        _set_event("No generated %s action is in range." % input_name)
        return false
    for action_value in _actions_for(target, input_name):
        if action_value is Dictionary and _execute_action(target, action_value):
            return true
    _set_event("The generated conditions for this action are not met.")
    return false

func _trigger_player_action(input_name: String) -> bool:
    var player_entry: Dictionary = plan.get("player", {})
    for action_value in _actions_for(player_entry, input_name):
        if action_value is Dictionary and _execute_action(player_entry, action_value):
            return true
    return false

func _process_touch_actions() -> void:
    if player == null or game_over:
        return
    var now_touching: Dictionary = {}
    for entry_value in plan.get("objects", []):
        if not (entry_value is Dictionary):
            continue
        var entry: Dictionary = entry_value
        var actions := _actions_for(entry, "touch")
        if actions.is_empty():
            continue
        var object_id := str(entry.get("id", ""))
        var object_node: Node2D = generated_nodes.get(object_id)
        if object_node == null or not object_node.visible:
            continue
        var threshold := maxf(22.0, float(actions[0].get("range_meters", 0.5)) * projection_scale)
        if player.position.distance_to(object_node.position) <= threshold:
            now_touching[object_id] = true
            if not touched_objects.has(object_id):
                _execute_action(entry, actions[0])
    touched_objects = now_touching


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
    var input_name := str(args[0])
    if input_name in ["attack", "hit"]:
        if not _trigger_nearby_action("hit"):
            _trigger_player_action("hit")
    elif input_name in ["interact", "jump"]:
        if not _trigger_nearby_action("interact"):
            _trigger_player_action("interact")
    elif input_name in ["use", "potion", "parry"]:
        _trigger_player_action("use")

func _on_web_forge(_args: Array) -> void:
    if status_label != null:
        status_label.text = "This build displays the fully generated opening scene; runtime continuation generation is the next environment step."

func _visible_object_state() -> Array:
    var result: Array = []
    for object_id in generated_animations.keys():
        var record: Dictionary = generated_animations[object_id]
        var animation: AnimatedSprite2D = record.get("node")
        var entry: Dictionary = record.get("entry", {})
        if animation == null:
            continue
        var size := _display_size(entry)
        var center := animation.global_position
        var frame_count := 0
        var texture_loaded := false
        var current_clip := str(animation.animation)
        if animation.sprite_frames != null and animation.sprite_frames.has_animation(current_clip):
            frame_count = animation.sprite_frames.get_frame_count(current_clip)
            if frame_count > 0:
                texture_loaded = animation.sprite_frames.get_frame_texture(current_clip, clampi(animation.frame, 0, frame_count - 1)) != null
        var holder := animation.get_parent() as Node2D
        result.append({
            "id": str(object_id),
            "name": str(entry.get("name", object_id)),
            "x": center.x - size.x * 0.5,
            "y": center.y - size.y * 0.5,
            "width": size.x,
            "height": size.y,
            "node_x": holder.global_position.x if holder != null else center.x,
            "node_y": holder.global_position.y if holder != null else center.y,
            "frame": animation.frame,
            "frame_count": frame_count,
            "clip": str(animation.animation),
            "available_clips": Array(animation.sprite_frames.get_animation_names()) if animation.sprite_frames != null else [],
            "playing": animation.is_playing(),
            "visible": animation.visible and animation.modulate.a > 0.01,
            "texture_loaded": texture_loaded,
            "usage": str(entry.get("visual_usage", "")),
        })
    return result

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
        "health": int(game_stats.get("player_health", game_stats.get("health", 100))),
        "max_health": 100,
        "stamina": int(game_stats.get("player_stamina", game_stats.get("stamina", 100))),
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
        "inventory": inventory.duplicate(true),
        "event": status_label.text if status_label != null else "Generated scene ready.",
        "forge_status": "StableAnimator pose-driven clips with recurrent RVM soft alpha loaded, including a DWPose-validated walk cycle.",
        "content_name": str(plan.get("scene_name", "Generated Scene")),
        "content_detail": str(manifest.get("opening_scene", "")).substr(0, 500),
        "forge_busy": false,
        "viewport_width": int(get_viewport_rect().size.x),
        "viewport_height": int(get_viewport_rect().size.y),
        "player_x": player.position.x,
        "player_y": player.position.y,
        "animation_frame": player_sprite.frame if player_sprite != null else -1,
        "visible_objects": _visible_object_state(),
        "game_stats": game_stats.duplicate(true),
        "object_states": object_states.duplicate(true),
        "last_action_id": last_action_id,
        "game_over": game_over,
        "game_outcome": game_outcome,
        "asset_engine": str(manifest.get("asset_engine", "")),
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
