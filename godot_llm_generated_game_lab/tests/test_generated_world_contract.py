#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
script = (ROOT / 'scripts/generated_world.gd').read_text()
scene = (ROOT / 'scenes/generated_world.tscn').read_text()
for token in ['res://data/generated_world.json','GeneratedPlayerAnimation','GeneratedAnimation','sheet_resource','fallback_used','llmGameGodotMove','llmGameGodotAction']:
    assert token in script, token
assert 'res://scripts/generated_world.gd' in scene
assert 'Placeholder' not in script
assert 'fallback scene' in script
assert 'holder.z_index = -140' in script
assert 'holder.z_index = -130' in script
assert 'vertical_offset' in script
print('generated world runtime contracts passed')

assert 'sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha' in script
assert 'thor-sdxl-reviewed-identity-anchored-animation' not in script
assert 'sdxl-reviewed-canonical+ltx-video-temporal+birefnet-matting' not in script
assert 'if engine != "sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha":' in script
assert 'if engine not in [' not in script
