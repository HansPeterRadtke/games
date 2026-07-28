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
    var frames: SpriteFrames = instance.player_sprite.sprite_frames
    if not frames.has_animation("idle") or not frames.has_animation("walk"):
        failures.append("idle or walk animation missing")
    if frames.get_frame_count("idle") != 8 or frames.get_frame_count("walk") != 8:
        failures.append("idle/walk frame count is not 8")
    var idle_texture: AtlasTexture = frames.get_frame_texture("idle", 0)
    var walk_texture: AtlasTexture = frames.get_frame_texture("walk", 0)
    if idle_texture == null or walk_texture == null:
        failures.append("animation atlas texture missing")
    else:
        if idle_texture.atlas.resource_path == walk_texture.atlas.resource_path:
            failures.append("walk animation reuses idle sheet")
        if not walk_texture.atlas.resource_path.ends_with(".walk.sheet.png"):
            failures.append("walk animation did not load reviewed walk sheet")
    instance.player_sprite.play("walk")
    var start_frame: int = instance.player_sprite.frame
    for _index in range(12):
        await process_frame
    if instance.player_sprite.frame == start_frame:
        failures.append("walk animation frame did not advance")
    var asset: Dictionary = instance.player_entry.get("asset", {})
    if str(asset.get("walk_engine", "")) != "sdxl-controlnet-openpose-img2img-walk-v1":
        failures.append("walk engine provenance missing")
    if float(asset.get("walk_adjacent_mean_abs_min", 0.0)) < 15.0:
        failures.append("walk motion floor is too low")
    var review: Dictionary = asset.get("walk_review", {})
    if review.get("genuine_walk_cycle") != true or not review.get("any_bad_frame_indices", []).is_empty():
        failures.append("walk review did not pass")
    if failures.is_empty():
        print(JSON.stringify({"ok": true, "idle_sheet": idle_texture.atlas.resource_path, "walk_sheet": walk_texture.atlas.resource_path, "walk_frames": frames.get_frame_count("walk"), "motion_floor": asset.get("walk_adjacent_mean_abs_min")}))
        quit(0)
        return
    push_error("; ".join(failures))
    quit(1)
