#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'scripts/generated_world.gd').read_text()
for token in [
 'func _condition_passes(condition: Dictionary)',
 'func _apply_effect(effect: Dictionary)',
 'func _execute_action(owner: Dictionary, action: Dictionary)',
 'func _trigger_nearby_action(input_name: String)',
 'func _process_touch_actions()',
 '"change_stat"','"set_state"','"inventory_add"','"inventory_remove"','"move"',
 '"set_visibility"','"set_collision"','"remove_object"','"scene_transition"','"end_game"',
 'Missing required generated action clip',
]: assert token in script,token
assert '_interact()' not in script
print('generated action runtime contracts passed')
assert 'func _unhandled_key_input(event: InputEvent)' in script
assert '_trigger_player_action("hit")' in script
assert '_trigger_player_action("interact")' in script
assert 'key_event.physical_keycode == KEY_E' in script
assert 'key_event.physical_keycode == KEY_F' in script
assert 'key_event.physical_keycode == KEY_Q' in script
