class_name RPGContentClient
extends Node

signal status_changed(message: String)
signal content_ready(payload: Dictionary)
signal asset_ready(slug: String, texture: Texture2D, payload: Dictionary)
signal request_failed(message: String)

var _generate_request: HTTPRequest
var _status_request: HTTPRequest
var _asset_request: HTTPRequest
var _pending_slug := ""
var _pending_payload: Dictionary = {}
var _poll_count := 0
var _busy := false

const KINDS := ["player", "weapon", "armor", "loot", "consumable"]

func _ready() -> void:
    _generate_request = HTTPRequest.new()
    _generate_request.timeout = 420.0
    add_child(_generate_request)
    _generate_request.request_completed.connect(_on_generate_completed)
    _status_request = HTTPRequest.new()
    _status_request.timeout = 20.0
    add_child(_status_request)
    _status_request.request_completed.connect(_on_status_completed)
    _asset_request = HTTPRequest.new()
    _asset_request.timeout = 60.0
    add_child(_asset_request)
    _asset_request.request_completed.connect(_on_asset_completed)

func is_busy() -> bool:
    return _busy

func request_content(kind: String, idea: String, seed: int) -> bool:
    if _busy:
        status_changed.emit("The grounded RPG forge is already working.")
        return false
    if not kind in KINDS:
        request_failed.emit("Unsupported RPG kind: %s" % kind)
        return false
    if idea.strip_edges().length() < 3:
        request_failed.emit("Describe the requested RPG content with at least three characters.")
        return false
    _busy = true
    _pending_slug = ""
    _pending_payload = {}
    _poll_count = 0
    status_changed.emit("Constrained LLM is writing grounded %s semantics..." % kind)
    var body := JSON.stringify({"kind": kind, "idea": idea.strip_edges().substr(0, 500), "seed": seed, "generate_asset": true})
    var error := _generate_request.request(_endpoint("rpg/generate"), ["Content-Type: application/json", "Accept: application/json"], HTTPClient.METHOD_POST, body)
    if error != OK:
        _fail("RPG generation request failed to start: %s" % error_string(error))
        return false
    return true

func _on_generate_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
        _fail("RPG generation failed: transport=%d status=%d %s" % [result, response_code, body.get_string_from_utf8().substr(0, 240)])
        return
    var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
    if not parsed is Dictionary:
        _fail("RPG service returned invalid JSON.")
        return
    var payload: Dictionary = parsed
    if not payload.get("ok", false) or not payload.get("content", {}) is Dictionary:
        _fail("RPG service rejected the request: %s" % str(payload.get("error", "unknown error")))
        return
    var content: Dictionary = payload["content"]
    var validation := validate_content(content)
    if not validation.is_empty():
        _fail("In-engine RPG validation failed: %s" % validation)
        return
    _pending_slug = str(payload.get("slug", ""))
    if _pending_slug.is_empty():
        _fail("RPG response omitted its slug.")
        return
    _pending_payload = payload
    content_ready.emit(payload)
    status_changed.emit("%s accepted; grounded canonical image and animation are rendering." % str(content.get("name", "RPG content")))
    if str(payload.get("asset_status", "")) == "ready":
        _request_sheet()
    else:
        _schedule_poll(1.5)

func _schedule_poll(seconds: float) -> void:
    await get_tree().create_timer(seconds).timeout
    if not _busy or _pending_slug.is_empty():
        return
    if _status_request.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
        _schedule_poll(0.75)
        return
    _poll_count += 1
    if _poll_count > 180:
        _fail("Grounded asset generation timed out.")
        return
    var error := _status_request.request(_endpoint("rpg/status/%s" % _pending_slug))
    if error != OK:
        _fail("RPG asset status request failed: %s" % error_string(error))

func _on_status_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
        _fail("RPG asset status failed: transport=%d status=%d" % [result, response_code])
        return
    var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
    if not parsed is Dictionary:
        _fail("RPG asset status returned invalid JSON.")
        return
    _pending_payload = parsed
    var status := str(_pending_payload.get("status", ""))
    if status == "ready":
        _request_sheet()
    elif status == "failed":
        _fail("Grounded asset review failed: %s" % str(_pending_payload.get("asset", {}).get("error", "unknown error")))
    else:
        status_changed.emit("SDXL is generating and visually reviewing a grounded asset...")
        _schedule_poll(2.0)

func _request_sheet() -> void:
    var asset: Dictionary = _pending_payload.get("asset", {})
    var sheet_url := str(asset.get("sheet_url", ""))
    if sheet_url.is_empty():
        _fail("Ready RPG asset omitted the sprite sheet URL.")
        return
    status_changed.emit("Downloading the identity-reviewed transparent animation...")
    var error := _asset_request.request(_resolve_url(sheet_url), ["Accept: image/png"])
    if error != OK:
        _fail("RPG sprite-sheet request failed: %s" % error_string(error))

func _on_asset_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
        _fail("RPG sprite-sheet download failed: transport=%d status=%d" % [result, response_code])
        return
    var image := Image.new()
    var error := image.load_png_from_buffer(body)
    if error != OK:
        _fail("RPG sprite sheet is not a valid PNG: %s" % error_string(error))
        return
    var asset: Dictionary = _pending_payload.get("asset", {})
    var frame_count := int(asset.get("frame_count", 0))
    var frame_width := int(asset.get("frame_width", 0))
    var frame_height := int(asset.get("frame_height", 0))
    if frame_count < 6 or frame_width < 64 or frame_height < 64:
        _fail("RPG asset metadata has invalid frame geometry.")
        return
    if image.get_width() != frame_count * frame_width or image.get_height() != frame_height:
        _fail("RPG sprite-sheet pixels do not match metadata.")
        return
    if image.detect_alpha() == Image.ALPHA_NONE:
        _fail("RPG sprite sheet lost transparency.")
        return
    var texture := ImageTexture.create_from_image(image)
    var slug := _pending_slug
    _busy = false
    _pending_slug = ""
    status_changed.emit("Grounded reviewed animation is ready in the world.")
    asset_ready.emit(slug, texture, _pending_payload)

func validate_content(content: Dictionary) -> String:
    var kind := str(content.get("kind", ""))
    if kind == "player_character":
        for key in ["name", "role", "experience_level", "stats", "equipment", "actions", "description", "asset"]:
            if not content.has(key): return "player is missing %s" % key
        return ""
    if not kind in ["weapon", "armor", "loot", "consumable"]:
        return "unsupported compiled kind %s" % kind
    for key in ["name", "description", "asset"]:
        if not content.has(key): return "%s is missing %s" % [kind, key]
    return ""

func _fail(message: String) -> void:
    _busy = false
    _pending_slug = ""
    status_changed.emit(message)
    request_failed.emit(message)

func _endpoint(path: String) -> String:
    if OS.has_feature("web"):
        var origin: Variant = JavaScriptBridge.eval("window.location.origin", true)
        return str(origin) + "/llm_game_object/" + path
    return "http://127.0.0.1:15303/object/" + path

func _resolve_url(path: String) -> String:
    if path.begins_with("http://") or path.begins_with("https://"):
        return path
    if OS.has_feature("web"):
        var origin: Variant = JavaScriptBridge.eval("window.location.origin", true)
        return str(origin) + path
    if path.begins_with("/llm_game_object_asset/"):
        return "http://127.0.0.1:15303/asset/" + path.trim_prefix("/llm_game_object_asset/")
    return "http://127.0.0.1:15303" + path
