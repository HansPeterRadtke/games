#!/usr/bin/env python3
from pathlib import Path
source=Path(__file__).with_name('thor_birefnet_matting_service.py').read_text()
for token in ['BiRefNet_lite-matting','/matte','birefnet_lite_matted_ltx','frames_png_b64','mid_frame_review','fallback_used']:
    assert token in source,token
assert 'LTXImageToVideoPipeline' not in source
assert 'StableDiffusionXLImg2ImgPipeline' not in source
print('thor BiRefNet matting service contracts passed')
assert '255.0 / alpha_max' in source
assert '255.0 / maximum' in source
assert 'alpha confidence' in source

assert 'return (288, 384)' in source
