import R from '../vendor/rapier.es.js';import {ActiveRagdoll} from '../active-ragdoll.js';
await R.init();
for(const gain of [.2,1,5])for(const root of [0,15,40,100])for(const mode of ['balance','walk']){
 const w=new R.World({x:0,y:-19.6,z:0});w.timestep=1/60;let floor=w.createRigidBody(R.RigidBodyDesc.fixed().setTranslation(0,-.35,0));w.createCollider(R.ColliderDesc.cuboid(40,.35,2),floor);
 const a=new ActiveRagdoll(w,0,{motorStiffness:gain,motorDamping:gain*.33,balanceGain:.005,rootGain:root,rootDamping:12});a.setMode(mode);let min=100,max=-100,xmax=0,finite=true,contacts=0;
 for(let i=0;i<360;i++){a.update(1/60);w.step();const p=a.parts.torso.translation();contacts+=a.footContacts>0?1:0;min=Math.min(min,p.y);max=Math.max(max,p.y);xmax=Math.max(xmax,Math.abs(p.x));if(!Number.isFinite(p.x)||!Number.isFinite(p.y)){finite=false;break;}}
 console.log(gain,root,mode,JSON.stringify({min:+min.toFixed(2),max:+max.toFixed(2),xmax:+xmax.toFixed(2),finite,contacts,torso:a.parts.torso.translation()}));}
