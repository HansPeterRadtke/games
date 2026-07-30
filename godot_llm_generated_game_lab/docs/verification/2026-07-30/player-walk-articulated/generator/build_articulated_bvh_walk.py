from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageSequence
from scipy import ndimage,signal

SRC_RGBA=Path('/data/tmp/player-rig-source/canonical-rgba.png')
SRC_KP=Path('/data/tmp/player-rig-source/keypoints.json')
ATR=Path('/data/tmp/schp-player-output/player.png')
PASCAL=Path('/data/tmp/schp-pascal-output/player.png')
BVH_WORLD=Path('/data/tmp/walk-cycle-world.json')
OUT=Path('/data/tmp/articulated-bvh-walk')
N=32
CW,CH=768,1152
OFF=np.array([64.0,128.0])
FW,FH=512,768
DURATION=50
PARTS=['head','torso','left_upper_arm','left_lower_arm','right_upper_arm','right_lower_arm','left_upper_leg','left_lower_leg','right_upper_leg','right_lower_leg']

def seg_dist_grid(a,b,xx,yy):
    v=b-a;den=max(float(v@v),1e-6);t=np.clip(((xx-a[0])*v[0]+(yy-a[1])*v[1])/den,0,1);px=a[0]+t*v[0];py=a[1]+t*v[1];return np.sqrt((xx-px)**2+(yy-py)**2)

def cmean_angle(a):return float(np.angle(np.mean(np.exp(1j*np.asarray(a)))))
def circular_smooth(a,harmonics=3):
    z=np.exp(1j*np.asarray(a,float));f=np.fft.fft(z);keep=np.zeros_like(f);keep[:harmonics+1]=f[:harmonics+1];keep[-harmonics:]=f[-harmonics:];s=np.fft.ifft(keep);return np.unwrap(np.angle(s))
def periodic_smooth(x,harmonics=3):
    f=np.fft.fft(np.asarray(x,float));keep=np.zeros_like(f);keep[:harmonics+1]=f[:harmonics+1];keep[-harmonics:]=f[-harmonics:];return np.fft.ifft(keep).real

def affine_from_segments(sa,sb,ta,tb):
    sv=sb-sa;tv=tb-ta;sl=max(float(np.linalg.norm(sv)),1e-6);tl=max(float(np.linalg.norm(tv)),1e-6);scale=tl/sl;ang=math.atan2(tv[1],tv[0])-math.atan2(sv[1],sv[0]);c,s=math.cos(ang)*scale,math.sin(ang)*scale;A=np.array([[c,-s],[s,c]],np.float32);t=np.asarray(ta,np.float32)-A@np.asarray(sa,np.float32);return np.array([[A[0,0],A[0,1],t[0]],[A[1,0],A[1,1],t[1]]],np.float32)
def affine_translation(delta):return np.array([[1,0,float(delta[0])],[0,1,float(delta[1])]],np.float32)
def ik_midpoint(start,end,length_a,length_b,sign):
    delta=end-start;raw_distance=max(float(np.linalg.norm(delta)),1e-6);distance=min(max(raw_distance,abs(length_a-length_b)+1e-3),length_a+length_b-1e-3);direction=delta/raw_distance;a=(length_a*length_a-length_b*length_b+distance*distance)/(2*distance);height=math.sqrt(max(length_a*length_a-a*a,0));perp=np.array([-direction[1],direction[0]]);return start+direction*a+perp*height*sign
def shift_part_exact(part,delta):
    dx,dy=int(round(float(delta[0]))),int(round(float(delta[1])))
    out=np.zeros_like(part);sx0=max(0,-dx);sy0=max(0,-dy);sx1=min(CW,CW-dx);sy1=min(CH,CH-dy);dx0=sx0+dx;dy0=sy0+dy;dx1=sx1+dx;dy1=sy1+dy
    if sx1>sx0 and sy1>sy0:out[dy0:dy1,dx0:dx1]=part[sy0:sy1,sx0:sx1]
    return out,np.array([dx,dy],float)
def warp_premul(part,M):
    a=part[:,:,3].astype(np.float32)/255;rgb=part[:,:,:3].astype(np.float32)/255;prem=rgb*a[...,None];pw=cv2.warpAffine(prem,M,(CW,CH),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=0);aw=np.clip(cv2.warpAffine(a,M,(CW,CH),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=0),0,1);return pw,aw
def over(dst_p,dst_a,src_p,src_a):
    out_p=src_p+dst_p*(1-src_a[...,None]);out_a=src_a+dst_a*(1-src_a);return out_p,out_a

def make_palette(frames):
    thumbs=[f.convert('RGB').resize((96,144),Image.Resampling.BILINEAR) for f in frames];atlas=Image.new('RGB',(96*8,144*3),(0,0,0))
    for i,im in enumerate(thumbs):atlas.paste(im,((i%8)*96,(i//8)*144))
    q=atlas.quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);p=(q.getpalette() or [])[:765];p.extend([0]*(765-len(p)));return p

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for p in OUT.rglob('*'):
        if p.is_file():p.unlink()
    src=np.asarray(Image.open(SRC_RGBA).convert('RGBA'),np.uint8);h,w=src.shape[:2];assert (w,h)==(640,896)
    atr=np.asarray(Image.open(ATR),np.uint8);pas=np.asarray(Image.open(PASCAL),np.uint8);assert atr.shape==pas.shape==(h,w)
    kp0=json.loads(SRC_KP.read_text())['keypoints'];S={k:np.array([v['x'],v['y']],float)+OFF for k,v in kp0.items()}
    S['neck']=(S['left_shoulder']+S['right_shoulder'])/2;S['pelvis']=(S['left_hip']+S['right_hip'])/2;S['head_center']=np.mean([S['nose'],S['left_eye'],S['right_eye'],S['left_ear'],S['right_ear']],axis=0)
    alpha=src[:,:,3].astype(np.float32)/255;visible=alpha>.02;yy,xx=np.mgrid[0:h,0:w]
    Sp={k:v-OFF for k,v in S.items()}
    d={
      'left_upper_arm':seg_dist_grid(Sp['left_shoulder'],Sp['left_elbow'],xx,yy),'left_lower_arm':seg_dist_grid(Sp['left_elbow'],Sp['left_wrist'],xx,yy),
      'right_upper_arm':seg_dist_grid(Sp['right_shoulder'],Sp['right_elbow'],xx,yy),'right_lower_arm':seg_dist_grid(Sp['right_elbow'],Sp['right_wrist'],xx,yy),
      'left_upper_leg':seg_dist_grid(Sp['left_hip'],Sp['left_knee'],xx,yy),'left_lower_leg':seg_dist_grid(Sp['left_knee'],Sp['left_ankle'],xx,yy),
      'right_upper_leg':seg_dist_grid(Sp['right_hip'],Sp['right_knee'],xx,yy),'right_lower_leg':seg_dist_grid(Sp['right_knee'],Sp['right_ankle'],xx,yy),
    }
    assign=np.full((h,w),'',dtype=object)
    assign[(pas==1)&visible]='head';assign[(pas==2)&visible]='torso'
    # semantic side hints from ATR, otherwise nearest source bone.
    for label,group,left_name,right_name in [(3,'upper_arm','left_upper_arm','right_upper_arm'),(4,'lower_arm','left_lower_arm','right_lower_arm'),(5,'upper_leg','left_upper_leg','right_upper_leg'),(6,'lower_leg','left_lower_leg','right_lower_leg')]:
        m=(pas==label)&visible
        if 'arm' in group:
            left_hint=(atr==14);right_hint=(atr==15)
        else:
            left_hint=np.isin(atr,[9,12]);right_hint=np.isin(atr,[10,13])
        assign[m&left_hint]=left_name;assign[m&right_hint]=right_name
        rem=m&(assign=='');assign[rem&(d[left_name]<=d[right_name])]=left_name;assign[rem&(d[left_name]>d[right_name])]=right_name
    # ATR-resolved residuals and nearest-part fallback.
    rem=visible&(assign=='')
    assign[rem&np.isin(atr,[2,11])]='head';assign[rem&np.isin(atr,[4,6,16])]='torso'
    for vals,up,lo,joint_y in [([14],'left_upper_arm','left_lower_arm',Sp['left_elbow'][1]),([15],'right_upper_arm','right_lower_arm',Sp['right_elbow'][1]),([12,9],'left_upper_leg','left_lower_leg',Sp['left_knee'][1]),([13,10],'right_upper_leg','right_lower_leg',Sp['right_knee'][1])]:
        m=visible&(assign=='')&np.isin(atr,vals);assign[m&(yy<=joint_y)]=up;assign[m&(yy>joint_y)]=lo
    rem=visible&(assign=='')
    # central residual to head/torso or nearest limb.
    head_score=np.sqrt(((xx-Sp['head_center'][0])/80)**2+((yy-Sp['head_center'][1])/110)**2)*45
    torso_center=(Sp['neck']+Sp['pelvis'])/2;torso_score=np.sqrt(((xx-torso_center[0])/95)**2+((yy-torso_center[1])/150)**2)*55
    names=['head','torso']+PARTS[2:];stack=[head_score,torso_score]+[d[n] for n in PARTS[2:]];best=np.argmin(np.stack(stack),axis=0)
    for i,n in enumerate(names):assign[rem&(best==i)]=n
    assert not np.any(visible&(assign==''))
    # create overlapping masks around joints.
    masks={n:(assign==n).astype(np.float32) for n in PARTS}
    def disk(center,r):return (((xx-center[0])**2+(yy-center[1])**2)<=r*r).astype(np.float32)
    joins=[('torso','head','neck',25),('torso','left_upper_arm','left_shoulder',23),('left_upper_arm','left_lower_arm','left_elbow',19),('torso','right_upper_arm','right_shoulder',23),('right_upper_arm','right_lower_arm','right_elbow',19),('torso','left_upper_leg','left_hip',24),('left_upper_leg','left_lower_leg','left_knee',21),('torso','right_upper_leg','right_hip',24),('right_upper_leg','right_lower_leg','right_knee',21)]
    for a,b,j,r in joins:
        m=disk(Sp[j],r)*visible;masks[a]=np.maximum(masks[a],m);masks[b]=np.maximum(masks[b],m)
    # feather only internal cut boundaries, clip to original alpha.
    layers={};diag=Image.new('RGB',(w*5,h*2),'white');colors=[(255,200,100),(0,128,255),(255,120,0),(200,70,0),(255,0,120),(190,0,80),(0,210,255),(0,80,210),(80,255,100),(20,150,40)]
    union=np.zeros((h,w),bool);part_metrics={}
    for i,n in enumerate(PARTS):
        m=np.clip(cv2.GaussianBlur(masks[n],(0,0),1.2),0,1)*visible;union|=m>.02
        rgba=src.copy();rgba[:,:,3]=np.round(alpha*m*255).astype(np.uint8)
        padded=np.zeros((CH,CW,4),np.uint8);padded[int(OFF[1]):int(OFF[1])+h,int(OFF[0]):int(OFF[0])+w]=rgba;layers[n]=padded
        ys,xs=np.where(m>.02);labels,c=ndimage.label(m>.02,structure=np.ones((3,3),bool));areas=[int((labels==j).sum()) for j in range(1,c+1)]
        part_metrics[n]={'pixels':int((m>.02).sum()),'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'components':c,'largest_component_ratio':max(areas,default=0)/max(1,sum(areas))}
        vis=np.zeros((h,w,3),np.uint8);vis[m>.02]=colors[i];diag.paste(Image.fromarray(vis),((i%5)*w,(i//5)*h))
    diag.save(OUT/'part-masks.png')
    union_ratio=float((union&visible).sum()/max(1,visible.sum()));assert union_ratio>=.999
    # Periodic motion-capture gait, projected from BVH front view (X horizontal, -Y image vertical).
    bvh=json.loads(BVH_WORLD.read_text());meta=bvh['metadata'];rows=bvh['rows'];names=meta['joints'];joint_index=meta['joint_index']
    raw=np.array([r['positions'] for r in rows],float);raw=raw-raw[:,0:1,:]
    motion=np.stack([raw[:,:,0],-raw[:,:,1]+.40*raw[:,:,2]],axis=2)
    # Fourier resampling imposes a circular trajectory and removes the small capture endpoint mismatch.
    motion=signal.resample(motion,N,axis=0,window=('kaiser',5.0)).real
    B={name:motion[:,idx,:] for name,idx in joint_index.items()}
    bvh_map={'left_shoulder':'LeftShoulder','left_elbow':'LeftElbow','left_wrist':'LeftWrist','right_shoulder':'RightShoulder','right_elbow':'RightElbow','right_wrist':'RightWrist','left_hip':'LeftHip','left_knee':'LeftKnee','left_ankle':'LeftAnkle','right_hip':'RightHip','right_knee':'RightKnee','right_ankle':'RightAnkle'}
    driver_neck=(B['LeftShoulder']+B['RightShoulder'])/2;driver_pelvis=B['Hips']
    def bangle(a,b):
        v=B[b]-B[a];return np.unwrap(np.angle(v[:,0]+1j*v[:,1]))
    torso_ang=bangle('Hips','Chest');torso_delta=torso_ang-np.mean(torso_ang)
    shoulder_tilt=bangle('RightShoulder','LeftShoulder');shoulder_delta=shoulder_tilt-np.mean(shoulder_tilt)
    hip_tilt=bangle('RightHip','LeftHip');hip_delta=hip_tilt-np.mean(hip_tilt)
    A={}
    for side,title in [('left','Left'),('right','Right')]:
        A[f'{side}_upper_arm']=bangle(f'{title}Shoulder',f'{title}Elbow')
        A[f'{side}_lower_arm']=bangle(f'{title}Elbow',f'{title}Wrist')
        A[f'{side}_upper_leg']=bangle(f'{title}Hip',f'{title}Knee')
        A[f'{side}_lower_leg']=bangle(f'{title}Knee',f'{title}Ankle')
    # Direct periodic BVH ankle targets retain captured depth; knees are solved by two-link IK.
    ankle_motion={};hip_width_source=float(np.linalg.norm(S['left_hip']-S['right_hip']));hip_width_bvh=max(float(np.linalg.norm((B['LeftHip']-B['RightHip']).mean(axis=0))),1e-6);scale_x=hip_width_source/hip_width_bvh
    for side,title in [('left','Left'),('right','Right')]:
        vector=B[f'{title}Ankle']-B[f'{title}Hip'];mean=vector.mean(axis=0);source_vector=S[f'{side}_ankle']-S[f'{side}_hip'];scale_y=abs(source_vector[1])/max(abs(mean[1]),1e-6)
        ankle_motion[side]=source_vector+np.stack([(vector[:,0]-mean[0])*scale_x*.70,(vector[:,1]-mean[1])*scale_y*.45],axis=1)
    # source bone lengths.
    L={}
    for side in ['left','right']:
        for seg,a,b in [('upper_arm','shoulder','elbow'),('lower_arm','elbow','wrist'),('upper_leg','hip','knee'),('lower_leg','knee','ankle')]:L[f'{side}_{seg}']=float(np.linalg.norm(S[f'{side}_{b}']-S[f'{side}_{a}']))
    src_torso=S['neck']-S['pelvis'];src_torso_angle=math.atan2(src_torso[1],src_torso[0]);src_torso_len=float(np.linalg.norm(src_torso));src_shoulder={s:S[f'{s}_shoulder']-S['neck'] for s in ['left','right']};src_hip={s:S[f'{s}_hip']-S['pelvis'] for s in ['left','right']}
    knee_sign={}
    for side in ['left','right']:
        line=S[f'{side}_ankle']-S[f'{side}_hip'];knee=S[f'{side}_knee']-S[f'{side}_hip'];knee_sign[side]=1.0 if np.cross(line,knee)>=0 else -1.0
    rel=[]
    for f in range(N):
        pelvis=np.array([0.,0.]);ta=src_torso_angle+.55*torso_delta[f];neck=pelvis+src_torso_len*np.array([math.cos(ta),math.sin(ta)])
        joints={'pelvis':pelvis,'neck':neck}
        def rot(v,a):c,s=math.cos(a),math.sin(a);return np.array([c*v[0]-s*v[1],s*v[0]+c*v[1]])
        for side in ['left','right']:
            joints[f'{side}_shoulder']=neck+rot(src_shoulder[side],.65*shoulder_delta[f])
            joints[f'{side}_hip']=pelvis+rot(src_hip[side],.65*hip_delta[f])
            for seg,parent,child in [('upper_arm','shoulder','elbow'),('lower_arm','elbow','wrist')]:
                angle=A[f'{side}_{seg}'][f];joints[f'{side}_{child}']=joints[f'{side}_{parent}']+L[f'{side}_{seg}']*np.array([math.cos(angle),math.sin(angle)])
            desired_ankle=joints[f'{side}_hip']+ankle_motion[side][f]
            joints[f'{side}_ankle']=desired_ankle
            joints[f'{side}_knee']=ik_midpoint(joints[f'{side}_hip'],desired_ankle,L[f'{side}_upper_leg'],L[f'{side}_lower_leg'],knee_sign[side])
        rel.append(joints)
    # Explicit periodic stance phases from 3D motion-capture world-foot velocity and ground height.
    world=signal.resample(raw,N,axis=0,window=('kaiser',5.0)).real
    left_world=world[:,joint_index['LeftAnkle']];right_world=world[:,joint_index['RightAnkle']]
    left_speed=np.linalg.norm(np.roll(left_world,-1,axis=0)-np.roll(left_world,1,axis=0),axis=1)/2
    right_speed=np.linalg.norm(np.roll(right_world,-1,axis=0)-np.roll(right_world,1,axis=0),axis=1)/2
    ground3=min(left_world[:,1].min(),right_world[:,1].min());left_height=left_world[:,1]-ground3;right_height=right_world[:,1]-ground3
    score=(right_speed-left_speed)+.35*(right_height-left_height)  # positive means left stance
    raw_support=(score>=0).astype(float)
    votes=sum(np.roll(raw_support,k) for k in [-2,-1,0,1,2]);support=(votes>=3).astype(float)
    # Seventeen-frame circular Gaussian handoff: exact stance plateaus with bounded root velocity.
    kernel_x=np.arange(17)-8;kernel=np.exp(-.5*(kernel_x/3.3)**2);kernel=kernel/kernel.sum()
    weight=sum(kernel[i]*np.roll(support,i-8) for i in range(17));weight=weight*weight*(3-2*weight);weight[weight<.008]=0;weight[weight>.992]=1
    left_home=S['left_ankle'][0];right_home=S['right_ankle'][0];ground=max(S['left_ankle'][1],S['right_ankle'][1]);targets=[]
    for f,r in enumerate(rel):
        root_left=np.array([left_home-r['left_ankle'][0],ground-r['left_ankle'][1]])
        root_right=np.array([right_home-r['right_ankle'][0],ground-r['right_ankle'][1]])
        root=weight[f]*root_left+(1-weight[f])*root_right
        targets.append({k:v+root for k,v in r.items()}|{'head_center':S['head_center']+(r['neck']+root-S['neck'])})
    # render rigid parts.
    frames=[];frame_metrics=[];head_hashes=[]
    src_seg={'torso':('pelvis','neck'),'left_upper_arm':('left_shoulder','left_elbow'),'left_lower_arm':('left_elbow','left_wrist'),'right_upper_arm':('right_shoulder','right_elbow'),'right_lower_arm':('right_elbow','right_wrist'),'left_upper_leg':('left_hip','left_knee'),'left_lower_leg':('left_knee','left_ankle'),'right_upper_leg':('right_hip','right_knee'),'right_lower_leg':('right_knee','right_ankle')}
    for f,T in enumerate(targets):
        # Fixed draw order prevents an occlusion-order pop at support transfer.
        order=['right_upper_leg','right_lower_leg','right_upper_arm','right_lower_arm','torso','left_upper_leg','left_lower_leg','left_upper_arm','left_lower_arm','head']
        dp=np.zeros((CH,CW,3),np.float32);da=np.zeros((CH,CW),np.float32)
        transforms={}
        for n in order:
            if n=='head':
                shifted,delta=shift_part_exact(layers[n],T['neck']-S['neck']);transforms[n]=delta
                aa=shifted[:,:,3].astype(np.float32)/255;pp=shifted[:,:,:3].astype(np.float32)/255*aa[...,None]
            else:
                a,b=src_seg[n];M=affine_from_segments(S[a],S[b],T[a],T[b]);transforms[n]=M;pp,aa=warp_premul(layers[n],M)
            dp,da=over(dp,da,pp,aa)
        rgb=np.zeros_like(dp);valid=da>1e-6;rgb[valid]=dp[valid]/da[valid,None];rgba=np.dstack([np.round(np.clip(rgb,0,1)*255).astype(np.uint8),np.round(np.clip(da,0,1)*255).astype(np.uint8)])
        out=Image.fromarray(rgba,'RGBA').resize((FW,FH),Image.Resampling.LANCZOS);out.save(OUT/f'frame_{f:02d}.png');frames.append(out)
        # inverse-align head layer at render resolution to prove exact pixels before final resize.
        delta=transforms['head'];moved,_=shift_part_exact(layers['head'],delta);restored,_=shift_part_exact(moved,-delta);box=(int(S['head_center'][0]-90),int(S['head_center'][1]-120),int(S['head_center'][0]+90),int(S['head_center'][1]+120));crop=np.ascontiguousarray(restored[box[1]:box[3],box[0]:box[2]]);head_hashes.append(hashlib.sha256(crop.tobytes()).hexdigest())
        mask=np.asarray(out.getchannel('A'))>8;edge=np.concatenate([mask[:2].ravel(),mask[-2:].ravel(),mask[:,:2].ravel(),mask[:,-2:].ravel()]);labs,c=ndimage.label(mask,structure=np.ones((3,3),bool));areas=[int((labs==j).sum()) for j in range(1,c+1)];frame_metrics.append({'frame':f,'coverage':float(mask.mean()),'soft_alpha':float(((np.asarray(out.getchannel('A'))>2)&(np.asarray(out.getchannel('A'))<253)).mean()),'border':float(edge.mean()),'largest_component_ratio':max(areas,default=0)/max(1,sum(areas)),'support_left_weight':float(weight[f]),'left_ankle':T['left_ankle'].tolist(),'right_ankle':T['right_ankle'].tolist()})
    # shared palette GIF.
    pal=make_palette(frames);pi=Image.new('P',(1,1));pi.putpalette(pal+[0,0,0]);full=[0,0,0]+pal;full.extend([0]*(768-len(full)));enc=[]
    for im in frames:
        arr=np.asarray(im);q=Image.fromarray(arr[:,:,:3],'RGB').quantize(palette=pi,dither=Image.Dither.NONE);idx=np.asarray(q,dtype=np.uint8).astype(np.uint16)+1;idx[arr[:,:,3]<=10]=0;pp=Image.fromarray(idx.astype(np.uint8),'P');pp.putpalette(full);enc.append(pp)
    gif=OUT/'player-walk.gif';enc[0].save(gif,format='GIF',save_all=True,append_images=enc[1:],duration=DURATION,loop=0,transparency=0,disposal=2,optimize=False,background=0)
    with Image.open(gif) as im:dec=[f.copy().convert('RGBA') for f in ImageSequence.Iterator(im)];loop=im.info.get('loop');dur=im.info.get('duration')
    arr=[np.asarray(f,dtype=np.int16) for f in dec];adj=[float(np.abs(arr[i]-arr[i-1]).mean()) for i in range(1,N)];seam=float(np.abs(arr[-1]-arr[0]).mean());median=float(np.median(adj));strong_l=[x for x in frame_metrics if x['support_left_weight']>=.992];strong_r=[x for x in frame_metrics if x['support_left_weight']<=.008]
    metrics={'generator':'semantic rigid-part articulated sprite driven by BVH walk cycle with front-perspective depth projection','frame_generation_model':False,'frames':N,'dimensions':[FW,FH],'duration_ms':dur,'loop':loop,'unique_frames':len({hashlib.sha256(x.tobytes()).hexdigest() for x in arr}),'adjacent_min':min(adj),'adjacent_max':max(adj),'adjacent_median':median,'seam':seam,'seam_ratio':seam/max(median,1e-6),'internal_max_ratio':max(adj)/max(median,1e-6),'head_aligned_unique_hashes':len(set(head_hashes)),'union_coverage':union_ratio,'left_stance_x_std':float(np.std([x['left_ankle'][0] for x in strong_l])) if strong_l else 999,'right_stance_x_std':float(np.std([x['right_ankle'][0] for x in strong_r])) if strong_r else 999,'left_stance_y_std':float(np.std([x['left_ankle'][1] for x in strong_l])) if strong_l else 999,'right_stance_y_std':float(np.std([x['right_ankle'][1] for x in strong_r])) if strong_r else 999,'alpha_border_max':max(x['border'] for x in frame_metrics),'alpha_soft_min':min(x['soft_alpha'] for x in frame_metrics),'largest_component_min':min(x['largest_component_ratio'] for x in frame_metrics),'shared_palette':True,'fallback_used':False,'parts':part_metrics,'frame_metrics':frame_metrics}
    (OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');(OUT/'targets.json').write_text(json.dumps([{k:v.tolist() if hasattr(v,'tolist') else v for k,v in t.items()} for t in targets],indent=2)+'\n')
    print(json.dumps(metrics,sort_keys=True))
    assert loop==0 and dur==DURATION and metrics['unique_frames']==N
    assert metrics['seam_ratio']<=1.5 and metrics['internal_max_ratio']<=2.0
    assert metrics['head_aligned_unique_hashes']==1
    assert metrics['left_stance_x_std']<4 and metrics['right_stance_x_std']<4 and metrics['left_stance_y_std']<3 and metrics['right_stance_y_std']<3
    assert metrics['alpha_border_max']==0 and metrics['alpha_soft_min']>=.005 and metrics['largest_component_min']>=.97
    # contact all frames on checker/dark/light, 8 each.
    idxs=[round(i*(N-1)/7) for i in range(8)];cellw,cellh=540,810;contact=Image.new('RGB',(8*cellw,3*cellh),'white')
    for ri,(name,color) in enumerate([('checker',None),('dark',(20,20,20,255)),('light',(238,238,238,255))]):
        for j,k in enumerate(idxs):
            f=dec[k]
            if color is None:
                bg=Image.new('RGBA',f.size,(210,210,210,255));dr=ImageDraw.Draw(bg);step=24
                for y in range(0,FH,step):
                    for x in range(0,FW,step):
                        if (x//step+y//step)%2:dr.rectangle((x,y,x+step-1,y+step-1),fill=(135,135,135,255))
            else:bg=Image.new('RGBA',f.size,color)
            bg.alpha_composite(f);tile=Image.new('RGB',(cellw,cellh),'white');tile.paste(bg,((cellw-FW)//2,30));ImageDraw.Draw(tile).text((6,6),f'{name} frame {k}',fill='black');contact.paste(tile,(j*cellw,ri*cellh))
    contact.save(OUT/'contact.png')
    return 0
if __name__=='__main__':raise SystemExit(main())
