#!/usr/bin/env python3
from __future__ import annotations
import base64,importlib.util,io
from pathlib import Path
from PIL import Image
source=Path(__file__).with_name('thor_ltx_video_service.py')
spec=importlib.util.spec_from_file_location('thor_ltx',source)
module=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
image=Image.new('RGBA',(96,192),(0,0,0,0))
for y in range(15,180):
    for x in range(28,68): image.putpixel((x,y),(120,80,50,255))
buf=io.BytesIO(); image.save(buf,format='PNG')
payload={'canonical_png_b64':base64.b64encode(buf.getvalue()).decode(),'kind':'player','asset_usage':'character_sprite','name':'Player','clip_name':'player_test','animation_prompt':'The complete player raises one hand clearly and returns to the same full body pose.','expected_labels':['adult human'],'review_requirements':'Exactly one complete adult human.'}
key1=module.request_key(payload); payload2=dict(payload); payload2['clip_name']='player_test_two'; key2=module.request_key(payload2)
assert key1!=key2
prepared=module.prepare_source(buf.getvalue()); assert prepared.size==(module.MODEL_SIZE,module.MODEL_SIZE)
assert module.output_dimensions('player')==(192,256)
assert module.output_dimensions('static_prop')==(160,160)
assert module.opaque_usage('tileable_texture')
assert not module.opaque_usage('character_sprite')
text=source.read_text()
for token in ['LTXImageToVideoPipeline','matting_url','native_video_frames','temporal_model','fallback_used','/animate','/animate-batch']:
    assert token in text,token
assert 'StableDiffusionXLImg2ImgPipeline' not in text
print('thor LTX video service contracts passed')

assert 'embeds, masks, encode_meta = encode_prompts(uncached)' in text

assert 'AutoModelForImageSegmentation' not in text
assert 'send_to_matting' in text
assert 'prompt_text_encoder' in text
assert 'pipeline.text_encoder = None' in text
assert 'pipeline.tokenizer = None' in text
assert 'pipeline._execution_device' in text
assert 'expected CUDA after detaching T5' in text
assert 'save_raw_frames' in text
assert 'load_raw_frames' in text
assert 'raw_cache_used' in text
assert 'batch_size' in text
assert 'batch_index' in text
assert 'embeds[index:index + 1]' in text
