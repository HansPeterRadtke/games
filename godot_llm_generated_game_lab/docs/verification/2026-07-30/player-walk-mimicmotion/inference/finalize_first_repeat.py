from __future__ import annotations
import json,math,sys,time,hashlib
from pathlib import Path
import cv2,numpy as np,torch
from PIL import Image,ImageDraw,ImageSequence
from scipy import ndimage
from scipy.signal import savgol_filter
sys.path.insert(0,'/data/src/external/RobustVideoMatting')
from model import MattingNetwork
ROOT=Path('/data/tmp/mimicmotion-walk-proof');OUT=ROOT/'first-repeat-final';OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.rglob('*'):
 if p.is_file():p.unlink()
files=sorted((ROOT/'raw-cyclic-frames').glob('frame_*.png'))[:24];rows=json.load(open(ROOT/'cyclic-dwpose.json'))[:24];assert len(files)==len(rows)==24
W,H=576,1024;OW,OH=512,768;TARGET_HEIGHT=500.;TARGET_CENTER=256.;TARGET_GROUND=680.
center=np.array([(r['bbox'][0]+r['bbox'][2])*.5*W for r in rows]);height=np.array([(r['bbox'][3]-r['bbox'][1])*H for r in rows]);left=np.array([[r['keypoints'][15][0]*W,r['keypoints'][15][1]*H] for r in rows]);right=np.array([[r['keypoints'][16][0]*W,r['keypoints'][16][1]*H] for r in rows])
center_s=savgol_filter(center,7,2,mode='wrap');height_s=np.maximum(savgol_filter(height,7,2,mode='wrap'),1);scale=TARGET_HEIGHT/height_s
base_l=scale*(left[:,0]-center_s)+TARGET_CENTER;base_r=scale*(right[:,0]-center_s)+TARGET_CENTER;target_l=float(np.median(base_l));target_r=float(np.median(base_r));diff=(left[:,1]-right[:,1])*scale;weight=1/(1+np.exp(-diff/4));dx=weight*(target_l-base_l)+(1-weight)*(target_r-base_r);ground=np.maximum(left[:,1],right[:,1])
model=MattingNetwork('mobilenetv3').eval();model.load_state_dict(torch.load('/data/models/matting/RobustVideoMatting/rvm_mobilenetv3.pth',map_location='cpu',weights_only=True),strict=True);rec=[None]*4;frames=[];trans=[];alpha_metrics=[];started=time.monotonic()
with torch.inference_mode():
 for i,p in enumerate(files):
  rgb=np.asarray(Image.open(p).convert('RGB'),dtype=np.float32)/255;src=torch.from_numpy(rgb).permute(2,0,1).unsqueeze(0).unsqueeze(0);fgr,pha,*rec=model(src,*rec,1.0);fg=np.clip(fgr[0,0].permute(1,2,0).numpy(),0,1);a=np.clip(pha[0,0,0].numpy(),0,1)
  labels,n=ndimage.label(a>.02,structure=np.ones((3,3),bool));areas=[int((labels==j).sum()) for j in range(1,n+1)];keep=labels==(int(np.argmax(areas))+1);a=np.where(keep,a,0).astype(np.float32);premul=fg*a[...,None]
  s=float(scale[i]);tx=float(TARGET_CENTER-s*center_s[i]+dx[i]);ty=float(TARGET_GROUND-s*ground[i]);M=np.float32([[s,0,tx],[0,s,ty]]);pw=cv2.warpAffine(premul,M,(OW,OH),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=0);aw=np.clip(cv2.warpAffine(a,M,(OW,OH),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=0),0,1);rgbw=np.zeros_like(pw);valid=aw>1e-6;rgbw[valid]=pw[valid]/aw[valid,None];rgba=np.dstack([np.round(np.clip(rgbw,0,1)*255).astype(np.uint8),np.round(aw*255).astype(np.uint8)]);frame=Image.fromarray(rgba,'RGBA');frame.save(OUT/f'frame_{i:02d}.png');frames.append(frame)
  lxy=[s*left[i,0]+tx,s*left[i,1]+ty];rxy=[s*right[i,0]+tx,s*right[i,1]+ty];trans.append({'frame':i,'support_left_weight':float(weight[i]),'left_ankle':lxy,'right_ankle':rxy,'body_center_x':float(s*center_s[i]+tx),'ground_y':float(max(lxy[1],rxy[1]))})
  mask=aw>.02;edge=np.concatenate([mask[:2].ravel(),mask[-2:].ravel(),mask[:,:2].ravel(),mask[:,-2:].ravel()]);labs,c=ndimage.label(mask,structure=np.ones((3,3),bool));ars=[int((labs==j).sum()) for j in range(1,c+1)];alpha_metrics.append({'coverage':float(mask.mean()),'soft':float(((aw>.01)&(aw<.99)).mean()),'border':float(edge.mean()),'largest':max(ars,default=0)/max(1,sum(ars))})
# Shared GIF palette.
thumbs=[f.convert('RGB').resize((80,160),Image.Resampling.BILINEAR) for f in frames];atlas=Image.new('RGB',(80*8,160*3),(0,0,0))
for i,im in enumerate(thumbs):atlas.paste(im,((i%8)*80,(i//8)*160))
q=atlas.quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);pal=(q.getpalette() or [])[:765];pal.extend([0]*(765-len(pal)));pi=Image.new('P',(1,1));pi.putpalette(pal+[0,0,0]);full=[0,0,0]+pal;full.extend([0]*(768-len(full)));encoded=[]
for f in frames:
 x=np.asarray(f);qq=Image.fromarray(x[:,:,:3],'RGB').quantize(palette=pi,dither=Image.Dither.NONE);idx=np.asarray(qq,dtype=np.uint8).astype(np.uint16)+1;idx[x[:,:,3]<=12]=0;im=Image.fromarray(idx.astype(np.uint8),'P');im.putpalette(full);encoded.append(im)
gif=OUT/'player-walk.gif';encoded[0].save(gif,format='GIF',save_all=True,append_images=encoded[1:],duration=70,transparency=0,disposal=2,optimize=False,background=0)
with Image.open(gif) as im:decoded=[f.copy().convert('RGBA') for f in ImageSequence.Iterator(im)];duration=im.info.get('duration');loop=im.info.get('loop')
a=[np.asarray(f,dtype=np.int16) for f in decoded];adj=[float(np.abs(a[i]-a[i-1]).mean()) for i in range(1,len(a))];seam=float(np.abs(a[-1]-a[0]).mean());strong_l=[x for x in trans if x['support_left_weight']>=.75];strong_r=[x for x in trans if x['support_left_weight']<=.25]
metrics={'engine':'Tencent MimicMotion 1.1','frame_count':24,'dimensions':[OW,OH],'duration_ms':duration,'loop':loop,'unique_frames':len({hashlib.sha256(x.tobytes()).hexdigest() for x in a}),'adjacent_min':min(adj),'adjacent_max':max(adj),'adjacent_median':float(np.median(adj)),'loop_transition':seam,'loop_ratio':seam/max(float(np.median(adj)),1e-6),'left_stance_x_std':float(np.std([x['left_ankle'][0] for x in strong_l])),'right_stance_x_std':float(np.std([x['right_ankle'][0] for x in strong_r])),'left_stance_y_std':float(np.std([x['left_ankle'][1] for x in strong_l])),'right_stance_y_std':float(np.std([x['right_ankle'][1] for x in strong_r])),'body_center_std':float(np.std([x['body_center_x'] for x in trans])),'ground_std':float(np.std([x['ground_y'] for x in trans])),'alpha_coverage_max':max(x['coverage'] for x in alpha_metrics),'alpha_soft_min':min(x['soft'] for x in alpha_metrics),'alpha_border_max':max(x['border'] for x in alpha_metrics),'largest_component_min':min(x['largest'] for x in alpha_metrics),'rvm_seconds':round(time.monotonic()-started,3),'shared_palette':True,'fallback_used':False}
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');(OUT/'transforms.json').write_text(json.dumps(trans,indent=2)+'\n');print(json.dumps(metrics,sort_keys=True))
assert len(decoded)==24 and duration==70 and loop is None and metrics['unique_frames']==24
assert metrics['left_stance_x_std']<4 and metrics['right_stance_x_std']<4 and metrics['left_stance_y_std']<2 and metrics['right_stance_y_std']<2
assert metrics['body_center_std']<8 and metrics['ground_std']<1
assert metrics['alpha_border_max']==0 and metrics['largest_component_min']>=.98 and metrics['alpha_soft_min']>=.005
# Contact.
indices=[round(i*23/11) for i in range(12)];cellw,cellh=340,690;contact=Image.new('RGB',(6*cellw,6*cellh),(40,40,40))
for ri,(name,color) in enumerate([('checker',None),('dark',(22,22,22,255)),('light',(238,238,238,255))]):
 for j,k in enumerate(indices):
  f=decoded[k]
  if color is None:
   bg=Image.new('RGBA',f.size,(210,210,210,255));d=ImageDraw.Draw(bg);step=20
   for y in range(0,f.height,step):
    for x in range(0,f.width,step):
     if (x//step+y//step)%2:d.rectangle((x,y,x+step-1,y+step-1),fill=(135,135,135,255))
  else:bg=Image.new('RGBA',f.size,color)
  bg.alpha_composite(f);tile=Image.new('RGB',(cellw,cellh),'white');tile.paste(bg,((cellw-f.width)//2,25));ImageDraw.Draw(tile).text((6,6),f'{name} frame {k}',fill='black');contact.paste(tile,((j%6)*cellw,(ri*2+j//6)*cellh))
contact.save(OUT/'contact.png')
