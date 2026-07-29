#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
source=Path(__file__).with_name('thor_grounded_rpg_asset_service.py')
spec=importlib.util.spec_from_file_location('thor_canonical',source)
module=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
assert hasattr(module,'generate_canonical_only')
assert hasattr(module,'canonical_paths_for')
paths=module.canonical_paths_for('abc')
assert paths['png'].name=='abc.canonical-source.png'
assert paths['meta'].name=='abc.canonical-source.json'
text=source.read_text()
assert 'route not in {"/generate", "/canonical"}' in text
assert 'sdxl-base-reviewed-canonical' in text
assert 'fallback_used' in text
print('thor canonical endpoint contracts passed')
