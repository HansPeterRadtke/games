from __future__ import annotations
import json,sys,time,math,hashlib
from pathlib import Path
import cv2
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
import torch
sys.path.insert(0,'/data/src/external/RobustVideoMatting')
from model import MattingNetwork
RAW=Path('/data/tmp/stableanimator-player-real-id')
OUT=Path('/data/tmp/stableanimator-rvm-player-accepted')
OUT.mkdir(parents=True,exist_ok=True)
WEIGHT='/data/models/matting/RobustVideoMatting/rvm_mobilenetv3.pth'
SPECS=[('idle',12,True),('walk',16,True),('player_interact',16,False),('player_attack',16,False),('player_use',16,False)]
TW,TH=288,384;MARGIN=14

def encode_gif(frames:list[Image.Image],path:Path,duration:int=125)->None:
    encoded=[]
    for frame in frames:
        arr=np.asarray(frame.convert('RGBA'),dtype=np.uint8);alpha=arr[:,:,3]
        quant=Image.fromarray(arr[:,:,:3],'RGB').quantize(colors=254,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
        idx=np.asarray(quant,dtype=np.uint8).astype(np.uint16)+1
        idx[alpha<=16]=0
        image=Image.fromarray(idx.astype(np.uint8),'P')
        pal=[0,0,0]+(quant.getpalette() or [])[:254*3];pal.extend([0]*(768-len(pal)));image.putpalette(pal);image.info['transparency']=0;image.info['disposal']=2;encoded.append(image)
    encoded[0].save(path,format='GIF',save_all=True,append_images=encoded[1:],duration=duration,loop=0,disposal=2,transparency=0,optimize=False)

def resize_premultiplied(fg:np.ndarray,alpha:np.ndarray,width:int,height:int)->np.ndarray:
    premul=fg*alpha[...,None]
    premul_r=cv2.resize(premul,(width,height),interpolation=cv2.INTER_LANCZOS4)
    alpha_r=cv2.resize(alpha,(width,height),interpolation=cv2.INTER_LANCZOS4)
    alpha_r=np.clip(alpha_r,0.0,1.0)
    rgb=np.zeros_like(premul_r)
    valid=alpha_r>1e-5
    rgb[valid]=premul_r[valid]/alpha_r[valid,None]
    rgb=np.clip(rgb,0.0,1.0)
    return np.dstack([np.round(rgb*255).astype(np.uint8),np.round(alpha_r*255).astype(np.uint8)])

model=MattingNetwork('mobilenetv3').eval().to('cpu')
model.load_state_dict(torch.load(WEIGHT,map_location='cpu',weights_only=True),strict=True)
summary={'engine':'StableAnimator','alpha_model':'RobustVideoMatting mobilenetv3 official v1.0.0','alpha_temporal_model':True,'resize':'premultiplied-alpha Lanczos4','fallback_used':False,'clips':{}}
started=time.monotonic()
for clip_name,source_count,looped in SPECS:
    files=sorted((RAW/clip_name).glob('frame_*.png'),key=lambda p:int(p.stem.split('_')[1]))
    assert len(files)==source_count,(clip_name,len(files),source_count)
    rec=[None]*4; raw=[]; frame_metrics=[]; infer_start=time.monotonic()
    with torch.inference_mode():
        for index,path in enumerate(files):
            src_np=np.asarray(Image.open(path).convert('RGB'),dtype=np.float32)/255.0
            src=torch.from_numpy(src_np).permute(2,0,1).unsqueeze(0).unsqueeze(0)
            fgr,pha,*rec=model(src,*rec,1.0)
            fg=np.clip(fgr[0,0].permute(1,2,0).numpy(),0,1)
            alpha=np.clip(pha[0,0,0].numpy(),0,1)
            labels,count=ndimage.label(alpha>0.02,structure=np.ones((3,3),dtype=bool))
            if count<1: raise RuntimeError(f'{clip_name} frame {index}: empty RVM matte')
            areas=[int((labels==i).sum()) for i in range(1,count+1)];keep=labels==(int(np.argmax(areas))+1)
            alpha=np.where(keep,alpha,0.0).astype(np.float32)
            ys,xs=np.where(alpha>0.02)
            bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
            edge=np.concatenate([(alpha[:2]>0.02).ravel(),(alpha[-2:]>0.02).ravel(),(alpha[:,:2]>0.02).ravel(),(alpha[:,-2:]>0.02).ravel()])
            partial=(alpha>0.01)&(alpha<0.99)
            core=alpha>0.95
            core_difference=float(np.abs(fg[core]-src_np[core]).mean()) if core.any() else 1.0
            frame_metrics.append({'frame':index,'bbox':bbox,'coverage_002':float((alpha>0.02).mean()),'coverage_050':float((alpha>0.5).mean()),'partial_ratio':float(partial.mean()),'alpha_mean':float(alpha.mean()),'alpha_max':float(alpha.max()),'border_002':float(edge.mean()),'components_before_cleanup':count,'largest_component_ratio':max(areas)/max(1,sum(areas)),'foreground_core_rgb_difference':core_difference})
            raw.append((fg,alpha,bbox))
    x0=max(0,min(item[2][0] for item in raw)-18);y0=max(0,min(item[2][1] for item in raw)-18);x1=min(512,max(item[2][2] for item in raw)+18);y1=min(512,max(item[2][3] for item in raw)+18)
    crop_w=x1-x0;crop_h=y1-y0;scale=min((TW-2*MARGIN)/crop_w,(TH-2*MARGIN)/crop_h);sw=max(1,int(round(crop_w*scale)));sh=max(1,int(round(crop_h*scale)))
    frames=[]
    for fg,alpha,_ in raw:
        rgba=resize_premultiplied(fg[y0:y1,x0:x1],alpha[y0:y1,x0:x1],sw,sh)
        canvas=np.zeros((TH,TW,4),dtype=np.uint8);ox=(TW-sw)//2;oy=TH-sh-MARGIN;canvas[oy:oy+sh,ox:ox+sw]=rgba
        frames.append(Image.fromarray(canvas,'RGBA'))
    if looped: frames.append(frames[0].copy())
    clip_dir=OUT/clip_name;clip_dir.mkdir(parents=True,exist_ok=True)
    for p in clip_dir.glob('*'):p.unlink()
    for i,frame in enumerate(frames):frame.save(clip_dir/f'frame_{i:02d}.png')
    sheet=Image.new('RGBA',(TW*len(frames),TH),(0,0,0,0))
    for i,frame in enumerate(frames):sheet.alpha_composite(frame,(i*TW,0))
    sheet.save(clip_dir/'animation.sheet.png');frames[0].save(clip_dir/'canonical.png');encode_gif(frames,clip_dir/'animation.gif')
    alphas=[np.asarray(f.getchannel('A'),dtype=np.float32)/255.0 for f in frames]
    coverage=[float((a>0.02).mean()) for a in alphas];partial=[float(((a>0.01)&(a<0.99)).mean()) for a in alphas];border=[];components=[];largest=[]
    for a in alphas:
        mask=a>0.02;edge=np.concatenate([mask[:2].ravel(),mask[-2:].ravel(),mask[:,:2].ravel(),mask[:,-2:].ravel()]);border.append(float(edge.mean()));labels,count=ndimage.label(mask,structure=np.ones((3,3),dtype=bool));areas=[int((labels==i).sum()) for i in range(1,count+1)];components.append(count);largest.append(max(areas,default=0)/max(1,sum(areas)))
    adj_alpha=[float(np.abs(alphas[i]-alphas[i-1]).mean()) for i in range(1,len(alphas))]
    meta={'name':clip_name,'engine':'StableAnimator','alpha_model':'RobustVideoMatting mobilenetv3 official v1.0.0','alpha_temporal_model':True,'alpha_checkpoint_sha256':hashlib.sha256(Path(WEIGHT).read_bytes()).hexdigest(),'alpha_device':'cpu','source_frame_count':source_count,'frame_count':len(frames),'frame_width':TW,'frame_height':TH,'frame_duration_ms':125,'looped':looped,'source_union_crop':[x0,y0,x1,y1],'resize':'premultiplied-alpha Lanczos4','foreground_coverage_002':[round(x,6) for x in coverage],'max_foreground_coverage':round(max(coverage),6),'soft_alpha_ratio':[round(x,6) for x in partial],'min_soft_alpha_ratio':round(min(partial),6),'max_soft_alpha_ratio':round(max(partial),6),'border_visible_ratio':[round(x,6) for x in border],'max_border_visible_ratio':round(max(border),6),'components':components,'min_largest_component_ratio':round(min(largest),6),'adjacent_alpha_difference':[round(x,6) for x in adj_alpha],'source_rvm_metrics':frame_metrics,'inference_seconds':round(time.monotonic()-infer_start,3),'exact_loop':frames[0].tobytes()==frames[-1].tobytes() if looped else None,'gif_alpha_mode':'binary preview; runtime sheet preserves soft alpha','fallback_used':False,'sha256':{'png':hashlib.sha256((clip_dir/'canonical.png').read_bytes()).hexdigest(),'gif':hashlib.sha256((clip_dir/'animation.gif').read_bytes()).hexdigest(),'sheet':hashlib.sha256((clip_dir/'animation.sheet.png').read_bytes()).hexdigest()}}
    assert meta['max_foreground_coverage']<=0.65,meta
    assert meta['max_border_visible_ratio']==0.0,meta
    assert meta['min_soft_alpha_ratio']>=0.005,meta
    assert meta['min_largest_component_ratio']>=0.98,meta
    if looped: assert meta['exact_loop'] is True,meta
    (clip_dir/'clip.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    summary['clips'][clip_name]={k:meta[k] for k in ['frame_count','max_foreground_coverage','min_soft_alpha_ratio','max_soft_alpha_ratio','max_border_visible_ratio','min_largest_component_ratio','inference_seconds','exact_loop','sha256']}
    print(json.dumps({'clip':clip_name,**summary['clips'][clip_name]},sort_keys=True),flush=True)
summary['total_seconds']=round(time.monotonic()-started,3)
(OUT/'accepted-manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# Combined contact sheet over split dark/light background.
clips=[]
for name,_,_ in SPECS:
    meta=json.loads((OUT/name/'clip.json').read_text());frames=[Image.open(OUT/name/f'frame_{i:02d}.png').convert('RGBA') for i in range(meta['frame_count'])]
    cols=8;cellw,cellh=180,220;rowsn=math.ceil(len(frames)/cols);panel=Image.new('RGB',(cols*cellw,rowsn*cellh+36),(60,60,60));ImageDraw.Draw(panel).text((8,10),name,fill='white')
    for i,frame in enumerate(frames):
        bg=Image.new('RGBA',frame.size,(25,25,25,255));d=ImageDraw.Draw(bg);d.rectangle((frame.width//2,0,frame.width,frame.height),fill=(235,235,235,255));bg.alpha_composite(frame);bg.thumbnail((cellw-10,cellh-25));tile=Image.new('RGB',(cellw,cellh),'white');tile.paste(bg,((cellw-bg.width)//2,20));ImageDraw.Draw(tile).text((5,3),str(i),fill='black');panel.paste(tile,((i%cols)*cellw,36+(i//cols)*cellh))
    clips.append(panel)
contact=Image.new('RGB',(max(x.width for x in clips),sum(x.height for x in clips)),(40,40,40));y=0
for panel in clips:contact.paste(panel,(0,y));y+=panel.height
contact.save(OUT/'all-clips-contact.png')
print(json.dumps({'ok':True,'output':str(OUT),'total_seconds':summary['total_seconds'],'clips':summary['clips']},sort_keys=True))
