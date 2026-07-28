#!/usr/bin/env python3
from __future__ import annotations
import json,sys,tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
import world_asset_pipeline as pipeline
surface={'id':'floor','type':'surface','name':'Cream Carpet','description':'A cream carpet.','asset_prompt':'seamless cream woven carpet fibers edge to edge','animation':'subtle fibers shift under soft changing light','visual_usage':'tileable_texture'}
payload=pipeline.build_asset_payload(surface)
assert payload['asset_usage']=='tileable_texture'
assert 'seamless' in payload['structural_prompt']
assert 'No white border' in payload['review_requirements']
player={'id':'player','name':'Player','description':'An adult child.','asset_prompt':'full body adult child in casual clothes front three quarter view','animation':'breathes and shifts weight naturally','visual_usage':'character_sprite'}
payload=pipeline.build_asset_payload(player,is_player=True)
assert payload['asset_usage']=='character_sprite'
assert 'uniform pure-white extraction background' in payload['review_requirements']
source=(ROOT/'server/world_asset_pipeline.py').read_text()
assert 'transparent_isolated_clean' in source
assert 'opaque_full_frame' in source
assert 'boundary_matte_ratio' in source
assert 'existing_request == payload_text' in source
print('world asset quality contracts passed')
