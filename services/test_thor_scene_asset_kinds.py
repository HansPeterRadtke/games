#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
source = Path(__file__).with_name('thor_grounded_rpg_asset_service.py')
spec = importlib.util.spec_from_file_location('thor_assets_scene', source)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
for kind in ['player','npc','creature','enemy']:
    assert module.dimensions_for(kind) == (640,896,192,256,8)
for kind in ['terrain','surface','structure','static_prop','vegetation','water','collectible','loot','weapon','armor','consumable','vehicle','light','particle_emitter','hazard','portal']:
    assert kind in module.SUPPORTED_KINDS
    assert module.dimensions_for(kind) == (640,640,160,160,6)
assert len(module.animation_phases('npc','stern breathing',8)) == 8
assert len(module.animation_phases('static_prop','subtle settling',6)) == 6
assert len(module.animation_phases('light','flickering light',6)) == 6
print('thor scene asset kind tests passed')
