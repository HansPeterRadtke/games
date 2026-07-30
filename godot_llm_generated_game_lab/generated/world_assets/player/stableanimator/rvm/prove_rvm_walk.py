from __future__ import annotations
import json,sys,time,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import torch
sys.path.insert(0,'/data/src/external/RobustVideoMatting')
from model import MattingNetwork
RAW=Path('/data/tmp/stableanimator-player-real-id/walk')
OUT=Path('/data/tmp/rvm-walk-proof');OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*'): p.unlink()
files=sorted(RAW.glob('frame_*.png'),key=lambda p:int(p.stem.split('_')[1]))
assert len(files)==16,len(files)
model=MattingNetwork('mobilenetv3').eval().to('cpu')
state=torch.load('/data/models/matting/RobustVideoMatting/rvm_mobilenetv3.pth',map_location='cpu',weights_only=True)
model.load_state_dict(state,strict=True)
rec=[None]*4;rows=[];rgba_frames=[];started=time.monotonic()
with torch.inference_mode():
    for index,path in enumerate(files):
        rgb=np.asarray(Image.open(path).convert('RGB'),dtype=np.float32)/255.0
        src=torch.from_numpy(rgb).permute(2,0,1).unsqueeze(0).unsqueeze(0)
        fgr,pha,*rec=model(src,*rec,1.0)
        fg=np.clip(fgr[0,0].permute(1,2,0).numpy(),0,1)
        alpha=np.clip(pha[0,0,0].numpy(),0,1)
        rgba=np.concatenate([np.round(fg*255).astype(np.uint8),np.round(alpha[...,None]*255).astype(np.uint8)],axis=2)
        image=Image.fromarray(rgba,'RGBA'); image.save(OUT/f'frame_{index:02d}.png');rgba_frames.append(image)
        visible=alpha>0.02; edge=np.concatenate([visible[:2].ravel(),visible[-2:].ravel(),visible[:,:2].ravel(),visible[:,-2:].ravel()])
        partial=(alpha>0.01)&(alpha<0.99)
        rows.append({'frame':index,'coverage_002':float(visible.mean()),'coverage_050':float((alpha>0.5).mean()),'partial_ratio':float(partial.mean()),'alpha_mean':float(alpha.mean()),'alpha_min':float(alpha.min()),'alpha_max':float(alpha.max()),'border_002':float(edge.mean())})
# Temporal alpha flicker after motion-aligned full-frame comparison; report only, semantic motion means masks move.
alphas=[np.asarray(f.getchannel('A'),dtype=np.float32)/255.0 for f in rgba_frames]
adj_alpha=[float(np.abs(alphas[i]-alphas[i-1]).mean()) for i in range(1,len(alphas))]
# Exact loop copy for runtime loop closure after RVM pass.
rgba_frames.append(rgba_frames[0].copy());rgba_frames[-1].save(OUT/f'frame_{len(rgba_frames)-1:02d}.png')
# Contact sheet over dark/light split backgrounds to reveal halos.
cellw,cellh=220,300;cols=6;rowsn=math.ceil(len(rgba_frames)/cols);sheet=Image.new('RGB',(cols*cellw,rowsn*cellh),(60,60,60))
for i,rgba in enumerate(rgba_frames):
    bg=Image.new('RGBA',rgba.size,(28,28,28,255));d=ImageDraw.Draw(bg);d.rectangle((rgba.width//2,0,rgba.width,rgba.height),fill=(235,235,235,255));bg.alpha_composite(rgba);bg.thumbnail((cellw-10,cellh-30));tile=Image.new('RGB',(cellw,cellh),'white');tile.paste(bg,((cellw-bg.width)//2,25));ImageDraw.Draw(tile).text((5,5),f'walk {i}',fill='black');sheet.paste(tile,((i%cols)*cellw,(i//cols)*cellh))
sheet.save(OUT/'contact.png')
metrics={'model':'RobustVideoMatting mobilenetv3 official v1.0.0','device':'cpu','frames':len(rows),'seconds':round(time.monotonic()-started,3),'rows':rows,'adjacent_alpha_difference':[round(x,6) for x in adj_alpha],'max_coverage_002':max(r['coverage_002'] for r in rows),'max_coverage_050':max(r['coverage_050'] for r in rows),'min_partial_ratio':min(r['partial_ratio'] for r in rows),'max_partial_ratio':max(r['partial_ratio'] for r in rows),'max_border_002':max(r['border_002'] for r in rows),'loop_frame_count':len(rgba_frames),'output':str(OUT)}
Path(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,sort_keys=True))
if metrics['max_coverage_002']>0.65: raise RuntimeError('RVM foreground coverage too large')
if metrics['max_border_002']>0.0: raise RuntimeError('RVM alpha touches border')
if metrics['min_partial_ratio']<0.005: raise RuntimeError('RVM produced effectively binary alpha')
if min(r['alpha_max'] for r in rows)<0.95: raise RuntimeError('RVM never reaches opaque foreground')
print('rvm_walk_soft_alpha=ok')
