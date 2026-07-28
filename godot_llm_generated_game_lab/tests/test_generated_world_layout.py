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
 'maxf(68.0, size.x * projection_scale * 1.45)',
 'maxf(82.0, size.x * projection_scale * 2.2)',
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
print('generated world layout contracts passed')
