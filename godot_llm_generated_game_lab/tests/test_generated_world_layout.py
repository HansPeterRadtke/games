#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'scripts/generated_world.gd').read_text()
shell=(ROOT/'deploy/web_shell.html').read_text()
for token in [
 'Input.is_physical_key_pressed(KEY_W)',
 'Input.is_physical_key_pressed(KEY_A)',
 'Input.is_physical_key_pressed(KEY_S)',
 'Input.is_physical_key_pressed(KEY_D)',
 'var centering := (usable - projected_size) * 0.5',
 'return "wall" if "wall" in combined else "floor"',
 'role == "wall_hanging"',
 'maxf(96.0, size.x * projection_scale * 2.0)',
 'animation_frame',
]: assert token in script,token
for token in ['app.dataset.playerX','app.dataset.playerY','app.dataset.animationFrame']:
 assert token in shell,token
assert 'GeneratedLabel' not in script
assert 'generated_animations' in script, 'generated_animations'
assert 'func _visible_object_state()' in script, 'func _visible_object_state()'
assert '"texture_loaded": texture_loaded' in script, '"texture_loaded": texture_loaded'
assert '"visible_objects": _visible_object_state()' in script, '"visible_objects": _visible_object_state()'
assert 'app.dataset.visibleObjects' in shell, 'app.dataset.visibleObjects'
assert 'app.dataset.internalWidth' in shell, 'app.dataset.internalWidth'
assert 'FALLBACK_VIEW_SIZE' in script, 'FALLBACK_VIEW_SIZE'
assert 'func _layout_view_size()' in script, 'func _layout_view_size()'
assert 'var view_size := _layout_view_size()' in script, 'var view_size := _layout_view_size()'
assert 'background.size = _layout_view_size()' in script, 'background.size = _layout_view_size()'
assert 'title_label.visible = false' in script, 'title_label.visible = false'
assert 'status_label.visible = false' in script, 'status_label.visible = false'
assert 'const VIEW_SIZE :=' not in script
assert 'return "rug"' in script, 'return "rug"'
assert 'return "wall_furniture"' in script, 'return "wall_furniture"'
assert 'role == "ceiling_fixture"' in script, 'role == "ceiling_fixture"'
assert 'room.position.x + room.size.x * 0.76' in script, 'room.position.x + room.size.x * 0.76'
assert 'room.position.x + room.size.x * 0.77' in script, 'room.position.x + room.size.x * 0.77'
assert 'room.size.x * 0.66' in script, 'room.size.x * 0.66'
assert 'func _decorate_architectural_asset' in script, 'func _decorate_architectural_asset'
assert 'Color("9b7447")' in script, 'Color("9b7447")'
assert 'Color("b58b59")' in script, 'Color("b58b59")'
assert 'maxf(92.0, size.x * projection_scale * 2.4)' in script, 'maxf(92.0, size.x * projection_scale * 2.4)'
assert 'maxf(112.0, size.x * projection_scale * 2.8)' in script, 'maxf(112.0, size.x * projection_scale * 2.8)'
assert 'maxf(138.0, size.x * projection_scale * 2.3)' in script, 'maxf(138.0, size.x * projection_scale * 2.3)'
assert 'maxf(76.0, size.x * projection_scale * 1.65)' in script, 'maxf(76.0, size.x * projection_scale * 1.65)'
assert '"node_x": holder.global_position.x' in script, '"node_x": holder.global_position.x'
assert '"node_y": holder.global_position.y' in script, '"node_y": holder.global_position.y'
print('generated world layout contracts passed')
