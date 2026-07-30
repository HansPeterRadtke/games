#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import world_asset_pipeline as pipeline
player = {
    'id':'adult_child','name':'Adult Child','description':'An exhausted adult child in plain suburban clothing.',
    'asset_prompt':'full body anxious adult child wearing plain blue jeans and a gray shirt, complete figure visible',
    'animation':'restless breathing and small nervous weight shifts','visual_usage':'character_sprite'
}
payload = pipeline.build_asset_payload(player, is_player=True)
assert payload['kind'] == 'player'
assert payload['expected_labels'][0] == 'adult human'
assert 'full-body' in payload['structural_prompt']
prop = {
    'id':'dining_table','type':'static_prop','name':'Oak Dining Table','description':'A long heavy oak dining table.',
    'asset_prompt':'long polished oak dining table with sturdy legs and realistic wood grain, complete object visible',
    'animation':'subtle wood settling and a moving highlight','visual_usage':'isolated_sprite'
}
payload = pipeline.build_asset_payload(prop)
assert payload['kind'] == 'static_prop'
assert payload['expected_labels'][0] == 'Oak Dining Table'
assert 'isolated static prop' in payload['structural_prompt']
assert pipeline.safe_id('Your Mom!') == 'your-mom'
source = (ROOT / 'server/world_asset_pipeline.py').read_text()
assert 'fallback_used' in source
assert 'cached_local' in (ROOT / 'server/world_asset_pipeline.py').read_text()
assert 'key.replace("_path", "_resource")' in (ROOT / 'server/world_asset_pipeline.py').read_text()
print('world asset pipeline contracts passed')
assert 'compile_world_assets' not in (ROOT / 'deploy/build-generated-world.sh').read_text()
assert 'build-temporal-world.sh' in (ROOT / 'deploy/build-generated-world.sh').read_text()
