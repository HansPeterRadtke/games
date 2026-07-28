#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
source=Path(__file__).with_name('thor_grounded_rpg_asset_service.py')
spec=importlib.util.spec_from_file_location('thor_alpha',source)
module=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
# White/noisy border, central colored subject, white interior detail that must survive.
rng=np.random.default_rng(7)
arr=np.full((256,192,3),248,dtype=np.int16)
arr+=rng.integers(-9,10,size=arr.shape,dtype=np.int16)
arr=np.clip(arr,0,255).astype(np.uint8)
im=Image.fromarray(arr,'RGB'); d=ImageDraw.Draw(im)
d.ellipse((55,25,137,105),fill=(185,120,80)); d.rectangle((62,90,130,232),fill=(40,80,150)); d.rectangle((82,115,110,175),fill=(250,250,250))
rgba,bbox,quality=module.alpha_for_frame(im,'player')
assert quality['border_visible_ratio'] <= 0.01, quality
assert quality['largest_component_ratio'] >= 0.94, quality
assert quality['boundary_matte_ratio'] <= 0.18, quality
assert rgba.getpixel((96,140))[3] > 240
assert rgba.getpixel((2,2))[3] == 0
# Opaque surfaces remain full-frame.
frames,meta=module.process_frames([im,Image.fromarray(np.roll(arr,1,axis=1),'RGB')],'surface','tileable_texture')
assert all(frame.getchannel('A').getextrema()==(255,255) for frame in frames)
assert meta['mode']=='opaque_full_frame'

# Actual rejected/accepted candidate regression when cache fixtures are available.
cache=Path('/data/var/llm_game/grounded_asset_cache')
dark=cache/'ec6bcd4c1e8b020148be7015.candidate-0.png'
good=cache/'ec6bcd4c1e8b020148be7015.candidate-4.png'
if dark.exists() and good.exists():
    try:
        module.alpha_for_frame(Image.open(dark),'player')
    except RuntimeError as exc:
        assert 'border is not bright and neutral' in str(exc)
    else:
        raise AssertionError('dark scene-like candidate was accepted')
    actual,bbox,actual_quality=module.alpha_for_frame(Image.open(good),'player')
    assert actual_quality['border_visible_ratio']==0.0,actual_quality
    assert actual_quality['largest_component_ratio']>=0.995,actual_quality
    assert actual_quality['boundary_matte_ratio']<=0.12,actual_quality
    assert actual_quality['bright_neutral_border_ratio']>=0.8,actual_quality
print('thor alpha cleanup tests passed',quality)
