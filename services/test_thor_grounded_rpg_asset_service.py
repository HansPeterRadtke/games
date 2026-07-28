#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

source = Path(__file__).with_name('thor_grounded_rpg_asset_service.py')
spec = importlib.util.spec_from_file_location('thor_assets', source)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

base = {
    'recognizable': True,
    'single_subject': True,
    'full_subject': True,
    'correct_category': True,
    'required_elements_visible': True,
    'forbidden_elements_absent': True,
    'anatomy_or_geometry': 'normal',
    'grounded_materials': False,
    'clean_plain_background': True,
    'clear_silhouette': True,
    'recognized_subject': 'mother',
    'critical_defects': [],
    'description': 'A stern mother wearing a floral dress.',
}
player = module.finalize_review(copy.deepcopy(base), {'kind': 'player', 'expected_labels': ['mother', 'floral dress']})
assert player['materials_required'] is False
assert player['materials_pass'] is True
assert player['label_pass'] is True
assert player['deterministic_pass'] is True
weapon = module.finalize_review(copy.deepcopy(base), {'kind': 'weapon', 'expected_labels': ['mother']})
assert weapon['materials_required'] is True
assert weapon['materials_pass'] is False
assert weapon['deterministic_pass'] is False
print('thor grounded review tests passed')
