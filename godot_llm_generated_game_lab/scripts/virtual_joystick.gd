class_name VirtualJoystick
extends Control

signal vector_changed(value: Vector2)

@export_range(0.0, 0.8, 0.01) var deadzone := 0.14
@export var base_color := Color(0.09, 0.075, 0.055, 0.72)
@export var border_color := Color(0.88, 0.72, 0.42, 0.78)
@export var thumb_color := Color(0.94, 0.83, 0.62, 0.96)

var value := Vector2.ZERO
var _active_touch := -2
var _mouse_active := false

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_STOP
    focus_mode = Control.FOCUS_NONE
    clip_contents = false
    resized.connect(queue_redraw)
    queue_redraw()

func _gui_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        if event.pressed and _active_touch == -2:
            _active_touch = event.index
            _set_from_position(event.position)
            accept_event()
        elif not event.pressed and event.index == _active_touch:
            _active_touch = -2
            _reset()
            accept_event()
        return
    if event is InputEventScreenDrag and event.index == _active_touch:
        _set_from_position(event.position)
        accept_event()
        return
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        _mouse_active = event.pressed
        if event.pressed:
            _set_from_position(event.position)
        else:
            _reset()
        accept_event()
        return
    if event is InputEventMouseMotion and _mouse_active:
        _set_from_position(event.position)
        accept_event()

func _set_from_position(local_position: Vector2) -> void:
    var center := size * 0.5
    var maximum := maxf(1.0, minf(size.x, size.y) * 0.5 - 10.0)
    var delta := local_position - center
    if delta.length() > maximum:
        delta = delta.normalized() * maximum
    var next := delta / maximum
    var length := next.length()
    if length <= deadzone:
        next = Vector2.ZERO
    elif length > 0.0:
        next = next.normalized() * ((length - deadzone) / (1.0 - deadzone))
    _set_value(next)

func _set_value(next: Vector2) -> void:
    next = next.limit_length(1.0)
    if value.is_equal_approx(next):
        return
    value = next
    vector_changed.emit(value)
    queue_redraw()

func _reset() -> void:
    _set_value(Vector2.ZERO)

func set_vector_for_test(next: Vector2) -> void:
    _set_value(next)

func release_for_test() -> void:
    _active_touch = -2
    _mouse_active = false
    _reset()

func _draw() -> void:
    var center := size * 0.5
    var radius := maxf(1.0, minf(size.x, size.y) * 0.5 - 3.0)
    draw_circle(center, radius, base_color)
    draw_arc(center, radius - 1.0, 0.0, TAU, 64, border_color, 2.0, true)
    draw_circle(center, radius * 0.42, Color(border_color, 0.10))
    var thumb_radius := radius * 0.30
    var thumb_center := center + value * (radius - thumb_radius - 5.0)
    draw_circle(thumb_center + Vector2(0, 3), thumb_radius, Color(0, 0, 0, 0.28))
    draw_circle(thumb_center, thumb_radius, thumb_color)
    draw_arc(thumb_center, thumb_radius - 1.0, 0.0, TAU, 40, Color(1, 1, 1, 0.78), 2.0, true)
