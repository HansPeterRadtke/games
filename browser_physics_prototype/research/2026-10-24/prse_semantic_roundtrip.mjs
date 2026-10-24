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
const ashIdentity=sourceId=>{
 if(sourceId.length<=76)return 'ash-'+sourceId;
 let hash=2166136261;
 for(const character of sourceId){hash^=character.charCodeAt(0);hash=Math.imul(hash,16777619);}
 return 'ash-'+sourceId.slice(0,62)+'-'+(hash>>>0).toString(16).padStart(8,'0');
};
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
  if(e.originId!==undefined&&e.originId!==null){
   if(!names(e.originId)||!ids.has(e.originId)||e.originId===e.id)
    return {ok:false,reason:'invalid replacement lineage'};
  }
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
    if(parent){
     const gap=p.y-e.size.y/2-parent.position.y-parent.size.y/2;
     const outside=Math.abs(p.x-parent.position.x)>parent.size.x/2+e.size.x/2
       ||Math.abs(p.z-parent.position.z)>parent.size.z/2+e.size.z/2;
     // Vertical loss of support is just as real as leaving the X/Z footprint.
     // These are conservative axis-aligned bounds; rotated/compound platforms
     // require an actual contact-normal/support-geometry solver later.
     if(outside||gap>.12||gap<-.2){
      const former=e.supportId;e.supportId=null;e.revision++;
      e.state.dislodgedFrom=former;
      this.emit('lost_support',[id,former],{formerSupport:former,
       reason:outside?'outside_support_footprint':'separated_vertically',gapMeters:+gap.toFixed(4)});
     }
    }
   }
   if(!e.supportId&&e.state.dislodgedFrom&&body.numColliders()&&e.body==='dynamic'){
    for(const [otherId,parentBody] of this.active){
     if(otherId===id||!parentBody.numColliders())continue;
     const parent=this.entities.get(otherId);
     if(!parent||parent.kind==='wall'||parent.state?.destroyed||parent.body!=='fixed')continue;
     const gap=p.y-e.size.y/2-parent.position.y-parent.size.y/2;
     if(Math.abs(gap)>.045||Math.abs(v.y)>.45
      ||Math.abs(p.x-parent.position.x)+e.size.x/2>parent.size.x/2+.015
      ||Math.abs(p.z-parent.position.z)+e.size.z/2>parent.size.z/2+.015)continue;
     let contact=false;
     this.game.world.contactPair(body.collider(0),parentBody.collider(0),manifold=>{
      if(manifold.numContacts()>0)contact=true;
     });
     if(!contact)continue;
     const old=e.state.dislodgedFrom;e.supportId=parent.id;e.state.dislodgedFrom=null;e.revision++;
     this.emit('rested_on',[id,parent.id],{previousSupport:old,
       cause:'verified_rigid_body_contact',gapMeters:+gap.toFixed(4)});
     break;
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
  // The native GameCore owns the one world clock, physics ticks, coarse semantic
  // accumulator and pre-existing delayed consequences. Do not step its Rapier
  // World behind its back (the first research adapter did exactly that).
  for(let i=0;i<n;i++){
   this.game.step();
   this.time=this.game.time;
   this.capture();
   this.detectContacts();
  }
 }
 // Advance existing GameCore semantic timers WITHOUT advancing any rigid body,
 // ragdoll, player movement, or physics tick counter. This is only an unloaded
 // research region; it is not a global pause/resume implementation.
 #advanceNativeCoarsely(end){
  const core=this.game,epsilon=1e-8;
  if(core.goal)throw Error('Native player goal cannot be advanced as an offscreen scene rule');
  if(end<core.time-epsilon||!finite(end)||end>1e9)throw Error('Invalid world clock');
  while(core.time+epsilon<end){
   const next=.25-core.semanticAccumulator;
   const delta=Math.min(end-core.time,next>epsilon?next:.25);
   core.time+=delta;
   core.semanticAccumulator+=delta;
   if(core.semanticAccumulator>=.25-epsilon){
    core.semantic.step(.25);
    core.semanticAccumulator=Math.max(0,core.semanticAccumulator-.25);
    core.consequences.advance(core.time,core.semantic,()=>false,event=>{
     core.emit(event.type,event.message,{
      entityId:event.entityId,cause:event.cause,outcome:event.outcome,
      visibility:'offscreen',time:event.time
     });
    });
   }
  }
  // No simulation tick happened for offscreen time: stepCount is an actual
  // physics-step count, not a fake wall/game-time surrogate.
  this.time=core.time;
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
  // Internal all-knowing factual cache, NOT an observer description. Separate the
  // immutable literary source from current state; never duplicate one ash remnant
  // as if it were a second independent object.
  const clauses=[],described=new Set();
  for(const e of this.scene.entities){
   if(described.has(e.id)||e.source==='provisional_3D_room_boundary')continue;
   if(e.state.condition==='ashes'){
    const child=this.scene.entities.find(x=>x.originId===e.id&&!x.state.destroyed);
    if(child){clauses.push(e.name+' was destroyed; '+child.name+' remains.');
     described.add(child.id);}
    else clauses.push(e.name+' was destroyed; no physical remnant is represented.');
   }else if(e.kind==='ash')clauses.push(e.name+' remains.');
   else{
    const former=e.state.dislodgedFrom&&this.entities.get(e.state.dislodgedFrom);
    const supporter=e.supportId&&this.entities.get(e.supportId);
    const suffix=e.state.tipped?'is tipped over':e.state.rotated?'has rotated':
      e.state.moved?'has changed position':'is present';
    clauses.push(e.name+' '+suffix+(former?'; no longer supported by '+former.name: supporter?'; resting on '+supporter.name:'')+'.');
   }
  }
  return clauses.join(' ');
 }
 dematerialize(){
  // An airborne/fast rigid body cannot simply freeze for an unbounded offscreen
  // story interval. No ballistics/contact approximation is yet validated here:
  // refuse transition and leave physics active until all such bodies settle.
  for(const [id,body]of this.active){
   if(!body.isDynamic())continue;
   const v=body.linvel(),speed=Math.hypot(v.x,v.y,v.z);
   if(speed>.35)throw Error('Unresolved dynamic motion at materialization boundary: '+id);
  }
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
  if(this.active.size||!finite(seconds)||seconds<0||seconds>3600)
   throw Error('invalid offscreen interval');
  if(Math.abs(this.time-this.game.time)>1e-6)throw Error('World time already divergent');
  const end=this.time+seconds;
  if(end>1e9)throw Error('Offscreen world time out of bounds');
  const due=this.offscreenRules.filter(x=>x.at<=end+1e-8).sort((a,b)=>a.at-b.at);
  const needed=[];
  for(const rule of due){
   const item=this.entities.get(rule.id);
   if(!item||item.state.condition==='ashes')continue;
   const residueId=ashIdentity(item.id),exists=this.entities.get(residueId);
   if(exists&&exists.originId!==item.id)throw Error('Ash identity collision');
   if(!exists&&!needed.includes(residueId))needed.push(residueId);
  }
  if(this.scene.entities.length+needed.length>320)
   throw Error('Cannot record all physical remains within bounded scene capacity');
  for(const rule of due){
   // Each event becomes true AT its scheduled time, not retroactively after
   // returning; real GameCore offscreen semantic processes advance as well.
   this.#advanceNativeCoarsely(Math.max(this.time,rule.at));
   const entity=this.entities.get(rule.id);
   if(entity&&entity.state.condition!=='ashes'){
    entity.state.condition='ashes';entity.state.destroyed=true;entity.revision++;
    this.emit('reduced_to_ashes',[rule.id],{
     cause:'scheduled_offscreen_combustion',triggerTime:rule.at
    },'semantic_rule');
    // A destroyed object must NOT merely vanish in prose while the text
    // promises visible ash. Preserve the original ID as a tombstone and add a
    // simple, real, fixed Rapier ash patch with explicit source lineage.
    // This is a coarse game collider, NOT particulate combustion physics.
    const ashId=ashIdentity(entity.id);
    if(!this.entities.has(ashId)){
     const parent=this.entities.get(entity.supportId),supported=parent&&!parent.state.destroyed;
     const height=.012;
     const residue=object(ashId,'ash',{
      x:entity.position.x,
      y:supported?parent.position.y+parent.size.y/2+height/2:height/2,
      z:entity.position.z
     },{
      x:Math.min(.45,entity.size.x),y:height,z:Math.min(.45,entity.size.z)
     },{
      name:'ash from '+entity.name,description:'A thin remnant of ash from '+entity.name,
      material:'unknown',body:'fixed',mass:.01,
      source:'derived-from:'+entity.id, supportId:supported?parent.id:'floor',
      state:{condition:'intact',residue:true}
     });
     residue.originId=entity.id;
     this.scene.entities.push(residue);
     this.entities.set(ashId,residue);
     this.original.set(ashId,clone(residue.position));
     this.emit('ash_remains',[ashId,entity.id],{
      generatedFrom:entity.id,location:clone(residue.position),
      approximation:'fixed thin ash patch, not heat/fracture chemistry'
     },'semantic_rule');
    }
   }
  }
  this.#advanceNativeCoarsely(end);
  this.offscreenRules=this.offscreenRules.filter(x=>x.at>end+1e-8);
  this.scene.currentProse=this.currentProse();
 }
 visibleIds(observerPosition=this.game.player.translation(),radius=7.5){
  if(!vec(observerPosition)||!finite(radius)||radius<0||radius>50)throw Error('Invalid observer bounds');
  // Conservative distance-only perception. Occlusion and facing direction are
  // NOT implemented; visibility here is an upper bound, not proven line of sight.
  return this.scene.entities.filter(e=>dist(e.position,observerPosition)<=radius).map(e=>e.id);
 }
 narrate(cursor=0,knownIds=null){
  // Supplying no explicit observer no longer grants omniscient access to every
  // offscreen scene event (a real bug in the original research adapter).
  const visible=new Set(knownIds||this.visibleIds());
  const statements=[],used=[],announcedDestruction=new Set();
  for(const ev of this.events){
   if(ev.sequence<=cursor||!ev.ids.some(id=>visible.has(id)))continue;
   if(ev.type==='ash_remains'&&announcedDestruction.has(ev.ids[1]))continue;
   if(ev.type==='reduced_to_ashes')announcedDestruction.add(ev.ids[0]);
   const e=this.entities.get(ev.ids[0]);if(!e)continue;
   const phrase={displaced:'has moved from its earlier position',tipped:'tipped over',rotated:'rotated',
    impact:'physically collided with '+(this.entities.get(ev.ids[1])?.name||'another object'),
    lost_support:'is no longer supported by '+(this.entities.get(ev.ids[1])?.name||'its former support'),
    rested_on:'has settled on '+(this.entities.get(ev.ids[1])?.name||'a supporting surface'),
    external_impulse:'was pushed by an external force',scorched:'was scorched while unobserved',
    reduced_to_ashes:'was reduced to ashes while unobserved',
    ash_remains:'is a remnant of '+(this.entities.get(ev.ids[1])?.name||'a destroyed item')}[ev.type];
   if(phrase){statements.push(e.name+' '+phrase+'.');used.push(ev.sequence);}
  }
  return {text:statements.join(' '),usedSequences:used,cursor:this.nextSeq-1};
 }
 describe(ids=null){
  const wanted=new Set(ids||this.visibleIds()),described=new Set(),parts=[];
  for(const e of this.scene.entities){
   if(!wanted.has(e.id)||described.has(e.id)||e.source==='provisional_3D_room_boundary')continue;
   if(e.state.condition==='ashes'){
    const child=this.scene.entities.find(x=>x.originId===e.id&&!x.state.destroyed&&wanted.has(x.id));
    if(child){parts.push('Ash from '+e.name+' remains at the former location.');
     described.add(child.id);}
    else parts.push(e.name+' has been destroyed, with no remnant visible here.');
   }else if(e.kind==='ash')parts.push(e.name+' remains at this location.');
   else{
    const old=e.state.dislodgedFrom&&this.entities.get(e.state.dislodgedFrom);
    const support=e.supportId&&this.entities.get(e.supportId);
    parts.push(e.name+(e.state.tipped?' is tipped':e.state.moved?' is displaced':' is present')
      +(old?'; no longer on '+old.name:support?'; resting on '+support.name:'')+'.');
   }
  }
  return parts.join(' ');
 }
 snapshot(){
  this.capture();
  if(Math.abs(this.game.time-this.time)>1e-6)throw Error('World clocks disagree at save');
  return {version:2,game:this.game.snapshot(),scene:clone(this.scene),events:clone(this.events),
   time:this.time,nextSeq:this.nextSeq,original:[...this.original],offscreenRules:clone(this.offscreenRules),
   materialized:this.active.size>0};
 }
 static restore(s){
  if(!s||s.version!==2||!validateScene(s.scene).ok||!finite(s.time)||s.time<0
   ||!finite(s.game?.time)||Math.abs(s.game.time-s.time)>1e-6
   ||!Number.isSafeInteger(s.nextSeq)||s.nextSeq<1||s.nextSeq>20001
   ||!Array.isArray(s.events)||s.events.length>20000
   ||!s.events.every(e=>Number.isSafeInteger(e?.sequence)&&e.sequence>0&&e.sequence<s.nextSeq)
   ||!Array.isArray(s.offscreenRules)||s.offscreenRules.length>100
   ||!s.offscreenRules.every(e=>finite(e.at)&&e.at>=s.time-1e-6&&typeof e.id==='string'
       &&s.scene.entities.some(x=>x.id===e.id)&&e.action==='ashes')
   ||!Array.isArray(s.original)||s.original.length!==s.scene.entities.length
   )return {ok:false,reason:'Invalid or pre-fix unsynchronized snapshot'};
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
