from __future__ import annotations
import gc,hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torchvision.transforms.functional import to_pil_image
from omegaconf import OmegaConf
sys.path.insert(0,'/data/src/external/MimicMotion')
from mimicmotion.utils.geglu_patch import patch_geglu_inplace
patch_geglu_inplace()
from mimicmotion.utils.loader import MimicMotionModel
from mimicmotion.pipelines.pipeline_mimicmotion import MimicMotionPipeline

ROOT=Path('/data/tmp/mimicmotion-walk-proof')
CFG=OmegaConf.load(ROOT/'walk.yaml')
TASK=CFG.test_case[0]
OUT=ROOT/'raw-cyclic-frames';OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*.png'):p.unlink()
torch.set_default_dtype(torch.float16)
torch.manual_seed(int(TASK.seed));torch.cuda.manual_seed_all(int(TASK.seed));torch.set_float32_matmul_precision('high')
started=time.monotonic()
print(json.dumps({'event':'load_start','time':time.time()}),flush=True)
model=MimicMotionModel(CFG.base_model_path)
state=torch.load(CFG.ckpt_path,map_location='cpu',weights_only=True,mmap=True)
result=model.load_state_dict(state,strict=False)
missing=list(result.missing_keys);unexpected=list(result.unexpected_keys)
if any(k.startswith(('unet.','pose_net.')) for k in missing) or unexpected:
    raise RuntimeError({'missing':missing,'unexpected':unexpected})
pipe=MimicMotionPipeline(vae=model.vae,image_encoder=model.image_encoder,unet=model.unet,scheduler=model.noise_scheduler,feature_extractor=model.feature_extractor,pose_net=model.pose_net)
for module in [pipe.vae,pipe.image_encoder,pipe.unet,pipe.pose_net]:module.requires_grad_(False)
del state,model;gc.collect();torch.cuda.empty_cache()
print(json.dumps({'event':'models_ready','seconds':round(time.monotonic()-started,3),'cuda_allocated':torch.cuda.memory_allocated(),'cuda_reserved':torch.cuda.memory_reserved()}),flush=True)
pose=torch.load(ROOT/'pose-cyclic-x3.pt',map_location='cpu',weights_only=True).to(dtype=torch.float16)
image=torch.load(ROOT/'image.pt',map_location='cpu',weights_only=True).to(dtype=torch.float16)
image_pixels=[to_pil_image(img.to(torch.uint8)) for img in (image+1.0)*127.5]
generator=torch.Generator(device='cuda').manual_seed(int(TASK.seed))
steps=[]
def callback(_pipe,step,timestep,kwargs):
    row={'step':int(step),'timestep':float(timestep),'elapsed':round(time.monotonic()-started,3),'cuda_allocated':int(torch.cuda.memory_allocated()),'cuda_reserved':int(torch.cuda.memory_reserved())}
    steps.append(row);print(json.dumps({'event':'step',**row}),flush=True);return kwargs
infer_started=time.monotonic()
with torch.inference_mode():
    result=pipe(
        image_pixels,image_pose=pose,num_frames=pose.size(0),tile_size=int(TASK.num_frames),tile_overlap=int(TASK.frames_overlap),
        height=pose.shape[-2],width=pose.shape[-1],fps=7,noise_aug_strength=float(TASK.noise_aug_strength),
        num_inference_steps=int(TASK.num_inference_steps),generator=generator,min_guidance_scale=float(TASK.guidance_scale),
        max_guidance_scale=float(TASK.guidance_scale),decode_chunk_size=4,output_type='pt',device=torch.device('cuda'),
        callback_on_step_end=callback,
    )
frames=result.frames.cpu()
video=(frames*255.0).clamp(0,255).to(torch.uint8)[0,1:]
for i,frame in enumerate(video):
    to_pil_image(frame).save(OUT/f'frame_{i:02d}.png')
metrics={'ok':True,'engine':'Tencent MimicMotion 1.1','base':'Stable Video Diffusion XT 1.1','frames':int(video.shape[0]),'shape':list(video.shape),'load_seconds':round(infer_started-started,3),'inference_seconds':round(time.monotonic()-infer_started,3),'total_seconds':round(time.monotonic()-started,3),'seed':int(TASK.seed),'tile_size':int(TASK.num_frames),'tile_overlap':int(TASK.frames_overlap),'steps':int(TASK.num_inference_steps),'noise_aug_strength':float(TASK.noise_aug_strength),'guidance_scale':float(TASK.guidance_scale),'driver_sha256':hashlib.sha256(Path(TASK.ref_video_path).read_bytes()).hexdigest(),'cyclic_pose_sha256':hashlib.sha256((ROOT/'pose-cyclic-x3.pt').read_bytes()).hexdigest(),'cyclic_selection':json.loads((ROOT/'cyclic-pose-selection.json').read_text()),'reference_sha256':hashlib.sha256(Path(TASK.ref_image_path).read_bytes()).hexdigest(),'checkpoint_sha256':hashlib.sha256(Path(CFG.ckpt_path).read_bytes()).hexdigest(),'compatibility':{'architecture':platform.machine(),'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'diffusers':__import__('diffusers').__version__,'transformers':__import__('transformers').__version__,'video_reader':'OpenCV Decord API shim only','shim_sha256':hashlib.sha256(Path('/data/tmp/mimicmotion-compat/decord.py').read_bytes()).hexdigest()},'step_log':steps,'output':str(OUT)}
(ROOT/'inference-cyclic.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,sort_keys=True),flush=True)
