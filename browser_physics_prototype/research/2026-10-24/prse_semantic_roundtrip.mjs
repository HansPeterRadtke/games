// General semantic/physical round-trip feasibility within EXISTING GameCore Rapier.
// Research adapter; not deployed to PRSE. The authoritative game physics world,
// not a text-only substitute or second physics solver, steps all bodies.
import RAPIER from '../../vendor/rapier.es.js';
import {GameCore} from '../../physics-core.js';

const clone=x=>structuredClone(x), finite=x=>typeof x==='number'&&Number.isFinite(x);
const vec=v=>v&&['x','y','z'].every(k=>finite(v[k])&&Math.abs(v[k])<1000);
const allowedMat=new Set(['wood','glass','stone','metal','paper','ceramic','plastic','fruit','unknown']);
const names=x=>typeof x==='string'&&/^[a-z][a-z0-9-]{2,80}$/.test(x);
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const quat=q=>q&&['x','y','z','w'].every(k=>finite(q[k]));
const identity=()=>({x:0,y:0,z:0,w:1});
const pose=e=>({position:clone(e.position),velocity:clone(e.velocity),rotation:clone(e.rotation),angular:clone(e.angular)});
const normalized={x:0,y:0,z:0};
export function validateScene(scene){
 if(!scene||!names(scene.id)||typeof scene.prose!=='string'||scene.prose.length<5||scene.prose.length>10000
  ||!Array.isArray(scene.entities)||scene.entities.length<1||scene.entities.length>320)return {ok:false,reason:'scene header/count'};
 const ids=new Set();
 for(const e of scene.entities){
  if(!e||!names(e.id)||ids.has(e.id)||typeof e.kind!=='string'||e.kind.length>80
   ||typeof e.name!=='string'||e.name.length>140||!e.name
   ||typeof e.description!=='string'||e.description.length>1000
   ||!vec(e.position)||!vec(e.size)||!['x','y','z'].every(k=>e.size[k]>=.002&&e.size[k]<=8)
   ||!allowedMat.has(e.material)||!['box','sphere','open_box'].includes(e.shape)
   ||!['dynamic','fixed'].includes(e.body)||e.body==='dynamic'&&e.shape==='open_box'
   ||e.mass!==undefined&&(!finite(e.mass)||e.mass<=0||e.mass>200)
   ||typeof e.source!=='string'||e.source.length>240
   ||e.supportId!==null&&e.supportId!==undefined&&e.supportId!=='floor'&&!names(e.supportId)
   ||typeof e.state!=='object'||e.state===null||Array.isArray(e.state)
   ||e.state.condition!==undefined&&!['intact','scorched','ashes','wet','broken'].includes(e.state.condition))
   return {ok:false,reason:'entity invalid'};
  ids.add(e.id);
 }
 for(const e of scene.entities){
  const seen=new Set([e.id]);let at=e;
  while(at.supportId&&at.supportId!=='floor'){
   if(!ids.has(at.supportId)||seen.has(at.supportId))return {ok:false,reason:'support graph missing/cycle'};
   seen.add(at.supportId);
   at=scene.entities.find(x=>x.id===at.supportId);
  }
 }
 return {ok:true};
}
function bounds(e){
 return {lo:{x:e.position.x-e.size.x/2,y:e.position.y-e.size.y/2,z:e.position.z-e.size.z/2},
  hi:{x:e.position.x+e.size.x/2,y:e.position.y+e.size.y/2,z:e.position.z+e.size.z/2}};
}
function overlap(a,b){
 const aa=bounds(a),bb=bounds(b);
 return ['x','y','z'].every(k=>Math.min(aa.hi[k],bb.hi[k])-Math.max(aa.lo[k],bb.lo[k])>1e-3);
}
export function geometryIssues(scene){
 const issues=[];
 for(let i=0;i<scene.entities.length;i++){
  const e=scene.entities[i];if(e.state.destroyed)continue;
  if(e.supportId==='floor'){const groundGap=e.position.y-e.size.y/2;
   if(groundGap<-.003)issues.push({id:e.id,type:'floor penetration'});
   if(groundGap>.05)issues.push({id:e.id,type:'floating despite declared floor support',gap:groundGap});}
  if(e.supportId&&e.supportId!=='floor'){
   const parent=scene.entities.find(z=>z.id===e.supportId);
   if(parent&&!parent.state.destroyed&&parent.shape!=='open_box'){
    const gap=e.position.y-e.size.y/2-parent.position.y-parent.size.y/2;
    if(Math.abs(gap)>.035)issues.push({id:e.id,type:'unsupported',gap});
    if(Math.abs(e.position.x-parent.position.x)+e.size.x/2>parent.size.x/2+.001
       ||Math.abs(e.position.z-parent.position.z)+e.size.z/2>parent.size.z/2+.001)
     issues.push({id:e.id,type:'outside support'});
   }
  }
  for(let j=0;j<i;j++){
   const b=scene.entities[j];
   if(b.state.destroyed||b.shape==='open_box'||e.shape==='open_box')continue;
   if(overlap(e,b))issues.push({id:e.id,other:b.id,type:'initial overlap'});
  }
 }
 return issues;
}
export function object(id,kind,location,size,options={}){
 return {id,kind,name:options.name||kind,description:options.description||kind,source:options.source||'explicit-scene-research',
  material:options.material||'wood',shape:options.shape||'box',body:options.body||'dynamic',
  mass:options.mass||1,size:clone(size),position:clone(location),velocity:{...normalized},
  rotation:identity(),angular:{...normalized},supportId:options.supportId||'floor',
  state:{condition:'intact',...options.state},revision:0,materialized:false};
}
export class PRSELoop{
 constructor(scene,{startMaterialized=true,checkGeometry=true}={}){
  const v=validateScene(scene);if(!v.ok)throw Error('invalid schema: '+v.reason);
  if(checkGeometry){
   const bad=geometryIssues(scene);if(bad.length)throw Error('invalid geometric proposal: '+JSON.stringify(bad.slice(0,3)));
  }
  this.scene=clone(scene);this.game=new GameCore();
  this.entities=new Map(this.scene.entities.map(e=>[e.id,e]));
  this.active=new Map();this.original=new Map(this.scene.entities.map(e=>[e.id,clone(e.position)]));
  this.events=[];this.nextSeq=1;this.time=0;this.offscreenRules=[];this.contactPairs=new Set();
  this.scene.currentProse=this.currentProse();
  const floor=this.game.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0,-.2,50));
  this.game.world.createCollider(RAPIER.ColliderDesc.cuboid(75,.2,75).setFriction(.85),floor);
  this.floor=floor;
  if(startMaterialized)this.materialize();
 }
 emit(type,ids,details={},origin='physics'){
  const ev={sequence:this.nextSeq++,time:Number(this.time.toFixed(3)),type,ids:[...ids],details:clone(details),origin};
  this.events.push(ev);this.scene.currentProse=this.currentProse();return ev;
 }
 materialize(){
  let count=0;
  for(const e of this.scene.entities){
   if(this.active.has(e.id)||e.state.destroyed||e.state.condition==='ashes')continue;
   const physics=e.body==='fixed'?RAPIER.RigidBodyDesc.fixed():RAPIER.RigidBodyDesc.dynamic();
   physics.setTranslation(e.position.x,e.position.y,e.position.z);
   if(e.body==='dynamic')physics.enabledTranslations(true,true,true).enabledRotations(true,true,true).setLinearDamping(.15).setAngularDamping(.15).setCanSleep(false);
   const body=this.game.world.createRigidBody(physics);
   let colliders=[];
   if(e.shape==='sphere')colliders=[RAPIER.ColliderDesc.ball(e.size.x/2)];
   if(e.shape==='box')colliders=[RAPIER.ColliderDesc.cuboid(e.size.x/2,e.size.y/2,e.size.z/2)];
   if(e.shape==='open_box'){
    const hx=e.size.x/2,hy=e.size.y/2,hz=e.size.z/2,w=.03;
    colliders=[RAPIER.ColliderDesc.cuboid(hx,w/2,hz).setTranslation(0,-hy+w/2,0),
     RAPIER.ColliderDesc.cuboid(w/2,hy,hz).setTranslation(-hx+w/2,0,0),
     RAPIER.ColliderDesc.cuboid(w/2,hy,hz).setTranslation(hx-w/2,0,0),
     RAPIER.ColliderDesc.cuboid(hx,hy,w/2).setTranslation(0,0,-hz+w/2),
     RAPIER.ColliderDesc.cuboid(hx,hy,w/2).setTranslation(0,0,hz-w/2)];
   }
   for(const c of colliders){
    c.setFriction(.72);
    if(e.body==='dynamic')c.setMass(e.mass/colliders.length);
    this.game.world.createCollider(c,body);
   }
   if(e.body==='dynamic'){
    body.setLinvel(e.velocity||normalized,true);
    body.setRotation(e.rotation||identity(),true);
    body.setAngvel(e.angular||normalized,true);
   }
   this.active.set(e.id,body);e.materialized=true;count++;
  }
  this.game.world.updateSceneQueries();return count;
 }
 capture(){
  for(const [id,body]of this.active){
   const e=this.entities.get(id);const p=body.translation(),v=body.linvel(),q=body.rotation(),a=body.angvel();
   if(dist(e.position,p)>.002)e.revision++;
   e.position={...p};e.velocity={...v};e.rotation={...q};e.angular={...a};
   if(!e.state.moved&&dist(this.original.get(id),p)>.1){
    e.state.moved=true;e.revision++;
    this.emit('displaced',[id],{before:this.original.get(id),after:clone(p)});
   }
   const tilted=2*Math.acos(Math.max(-1,Math.min(1,Math.abs(q.w))));
   if(!e.state.rotated&&e.shape==='sphere'&&tilted>.7){
    e.state.rotated=true;e.revision++;this.emit('rotated',[id],{angleRadians:Number(tilted.toFixed(3))});
   }
   if(!e.state.tipped&&e.shape!=='sphere'&&tilted>.7){
    e.state.tipped=true;e.revision++;this.emit('tipped',[id],{angleRadians:Number(tilted.toFixed(3))});
   }
   if(e.supportId&&e.supportId!=='floor'){
    const parent=this.entities.get(e.supportId);
    if(parent&&(Math.abs(p.x-parent.position.x)>parent.size.x/2+e.size.x/2
       ||Math.abs(p.z-parent.position.z)>parent.size.z/2+e.size.z/2)){
      const former=e.supportId;e.supportId=null;e.revision++;
      this.emit('lost_support',[id,former],{formerSupport:former});
    }
   }

  }
 }
 applyImpulse(id,value){
  if(!vec(value))return false;
  const body=this.active.get(id);
  if(!body||!body.isDynamic())return false;
  body.applyImpulse(value,true);this.emit('external_impulse',[id],{vector:value},'explicit_action');return true;
 }
 tick(n=1){
  if(!Number.isInteger(n)||n<0||n>1200)throw Error('invalid ticks');
  for(let i=0;i<n;i++){this.game.world.step();this.time+=this.game.world.timestep;this.capture();this.detectContacts();}
 }
 detectContacts(){
  // Actual Rapier contact manifolds; no event is inferred merely from a nearby location.
  // Bounded all-pairs for small scenes only; larger scenes need a collision-event dispatcher.
  if(this.active.size>40)return;
  const bodies=[...this.active],current=new Set();
  for(let i=0;i<bodies.length;i++)for(let j=0;j<i;j++){
   const [a,ba]=bodies[i],[b,bb]=bodies[j];
   if(!ba.numColliders()||!bb.numColliders())continue;
   let contact=false;
   this.game.world.contactPair(ba.collider(0),bb.collider(0),manifold=>{if(manifold.numContacts()>0)contact=true;});
   if(!contact)continue;
   const key=a<b?a+'|'+b:b+'|'+a;current.add(key);
   if(this.contactPairs.has(key))continue;
   const av=ba.linvel(),bv=bb.linvel(),speed=Math.hypot(av.x-bv.x,av.y-bv.y,av.z-bv.z);
   if(speed>.15)this.emit('impact',[a,b],{relativeSpeedMetersPerSecond:+speed.toFixed(3)});
  }
  this.contactPairs=current;
 }
 currentProse(){
  // Canonical NOW text is derived from observed authoritative entity state; the original
  // literary source is retained separately as historical provenance, not reused as truth.
  const clauses=[];
  for(const e of this.scene.entities){
   const suffix=e.state.condition==='ashes'?'was destroyed and only ash remains':
     e.state.tipped?'is tipped over':e.state.rotated?'rotated':
     e.state.moved?'has changed position':'is present';
   clauses.push(e.name+' '+suffix+'.');
  }
  return clauses.join(' ');
 }
 dematerialize(){
  this.capture();
  for(const [id,body]of this.active){
   this.game.world.removeRigidBody(body);this.entities.get(id).materialized=false;
  }
  const count=this.active.size;this.active.clear();this.contactPairs.clear();return count;
 }
 igniteOffscreen(id){
  if(this.active.size)throw Error('explicit rule may advance only offscreen');
  const e=this.entities.get(id);
  if(!e||!['wood','paper'].includes(e.material)||e.state.condition!=='intact')return false;
  e.state.condition='scorched';e.revision++;
  this.emit('scorched',[id],{cause:'explicit_offscreen_ignition'},'semantic_rule');
  this.offscreenRules.push({at:this.time+6,id,action:'ashes'});return true;
 }
 advanceOffscreen(seconds){
  if(this.active.size||!finite(seconds)||seconds<0||seconds>3600)throw Error('invalid offscreen interval');
  this.time+=seconds;
  for(const r of this.offscreenRules.filter(x=>x.at<=this.time)){
   const e=this.entities.get(r.id);
   if(e&&e.state.condition!=='ashes'){
    e.state.condition='ashes';e.state.destroyed=true;e.revision++;
    this.emit('reduced_to_ashes',[e.id],{cause:'scheduled_offscreen_combustion'},'semantic_rule');
   }
  }
  this.offscreenRules=this.offscreenRules.filter(x=>x.at>this.time);this.scene.currentProse=this.currentProse();
 }
 narrate(cursor=0,knownIds=null){
  const visible=new Set(knownIds||this.scene.entities.map(e=>e.id));
  const statements=[],used=[];
  for(const ev of this.events){
   if(ev.sequence<=cursor||!ev.ids.some(id=>visible.has(id)))continue;
   const e=this.entities.get(ev.ids[0]);if(!e)continue;
   const phrase={displaced:'has moved from its earlier position',tipped:'tipped over',rotated:'rotated',
    impact:'physically collided with '+(this.entities.get(ev.ids[1])?.name||'another object'),
    lost_support:'lost its former support',
    external_impulse:'was pushed by an external force',scorched:'was scorched while unobserved',
    reduced_to_ashes:'was reduced to ashes while unobserved'}[ev.type];
   if(phrase){statements.push(e.name+' '+phrase+'.');used.push(ev.sequence);}
  }
  return {text:statements.join(' '),usedSequences:used,cursor:this.nextSeq-1};
 }
 describe(ids=null){
  const wanted=new Set(ids||this.scene.entities.map(e=>e.id));
  return this.scene.entities.filter(e=>wanted.has(e.id)).map(e=>
   e.state.condition==='ashes'?'Ash remains where '+e.name+' used to be.':
   e.name+(e.state.tipped?' is tipped.':e.state.moved?' is displaced.':' is present.')).join(' ');
 }
 snapshot(){
  this.capture();
  return {version:1,game:this.game.snapshot(),scene:clone(this.scene),events:clone(this.events),
   time:this.time,nextSeq:this.nextSeq,original:[...this.original],offscreenRules:clone(this.offscreenRules),
   materialized:this.active.size>0};
 }
 static restore(s){
  if(!s||s.version!==1||!validateScene(s.scene).ok||!finite(s.time)||s.time<0
   ||!Array.isArray(s.events)||s.events.length>20000||!Array.isArray(s.offscreenRules))return {ok:false};
  const loop=new PRSELoop(s.scene,{startMaterialized:false,checkGeometry:false});
  if(!loop.game.restore(s.game)){loop.dispose();return {ok:false,reason:'invalid core save'};}
  loop.scene=clone(s.scene);loop.entities=new Map(loop.scene.entities.map(e=>[e.id,e]));
  loop.events=clone(s.events);loop.time=s.time;loop.nextSeq=s.nextSeq;
  loop.offscreenRules=clone(s.offscreenRules);loop.original=new Map(s.original);
  loop.scene.currentProse=loop.currentProse();
  if(s.materialized){for(const e of loop.scene.entities)e.materialized=false;loop.materialize();}
  return {ok:true,loop};
 }
 dispose(){for(const body of this.active.values())this.game.world.removeRigidBody(body);this.active.clear();this.game.world.free();}
}
