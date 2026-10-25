// Research-only perception/narration adapter for existing PRSELoop and actual
// authoritative GameCore/Rapier collider geometry. No second physics world.
// World truth and observer's known/displayed facts are separate.
import RAPIER from '../../vendor/rapier.es.js';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';

const finite=n=>typeof n==='number'&&Number.isFinite(n);
const posOK=p=>p&&['x','y','z'].every(k=>finite(p[k])&&Math.abs(p[k])<1000);
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const validName=n=>typeof n==='string'&&/^[a-z][a-z0-9-]{2,60}$/.test(n);
const samples=e=>{
 const p=e.position,s=e.size||{x:.1,y:.1,z:.1};
 return [
  p,
  {x:p.x,y:p.y+s.y*.24,z:p.z},
  {x:p.x,y:p.y-s.y*.24,z:p.z},
  {x:p.x+s.x*.24,y:p.y,z:p.z},
  {x:p.x-s.x*.24,y:p.y,z:p.z},
  {x:p.x,y:p.y,z:p.z+s.z*.24},
  {x:p.x,y:p.y,z:p.z-s.z*.24}
 ];
};
function pointsTo(observer,point) {
 const dx=point.x-observer.x,dy=point.y-observer.y,dz=point.z-observer.z;
 const n=Math.hypot(dx,dy,dz);
 if(n<.00001)return null;
 return {len:n,dir:{x:dx/n,y:dy/n,z:dz/n}};
}
export class PRSEPhysicalObserver {
 constructor(loop,{maxObservers=8,visibilityRadius=7.5,immediateEventWindowSeconds=.18}={}){
  if(!(loop instanceof PRSELoop))throw Error('The actual PRSE GameCore wrapper is required');
  if(!finite(visibilityRadius)||visibilityRadius<.1||visibilityRadius>50)throw Error('Invalid visibility radius');
  this.loop=loop;
  this.maxObservers=maxObservers;
  this.radius=visibilityRadius;
  this.eventWindow=immediateEventWindowSeconds;
  this.records=new Map();
  this.attachments=new Map();
  this.occlusionQueries=0;
 }
 #observer(id){
  if(!validName(id))throw Error('Invalid observer ID');
  let e=this.records.get(id);
  if(!e){
   if(this.records.size>=this.maxObservers)throw Error('Observer budget exceeded');
   e={processed:new Set(),pending:[],facts:new Map(),lastVisible:new Set(),lastTime:0};
   this.records.set(id,e);
  }
  return e;
 }
 isVisible(objectId,eye,{radius=this.radius,mode='ray',facing=null,fovDegrees=360}={}){
  if(!posOK(eye)||!finite(radius)||radius<0||radius>50)throw Error('Invalid observation origin/radius');
  const e=this.loop.entities.get(objectId);
  if(!e)return {visible:false,reason:'unknown_id'};
  if(e.state?.destroyed)return {visible:false,reason:'destroyed_identity'};
  const body=this.loop.active.get(objectId);
  if(!body)return {visible:false,reason:'unmaterialized'};
  if(e.source==='provisional_3D_room_boundary')return {visible:false,reason:'structural_geometry_only'};
  const d=dist(eye,e.position);
  if(d>radius)return {visible:false,reason:'outside_radius'};
  if(facing && fovDegrees<360){
   if(!posOK(facing)||!finite(fovDegrees)||fovDegrees<=0||fovDegrees>360)
    throw Error('Invalid facing/FOV');
   const q=pointsTo(eye,e.position),norm=Math.hypot(facing.x,facing.y,facing.z);
   if(!q||norm<.01)return {visible:false,reason:'invalid_facing'};
   const cosine=(q.dir.x*facing.x+q.dir.y*facing.y+q.dir.z*facing.z)/norm;
   if(cosine<Math.cos(fovDegrees*Math.PI/360))return {visible:false,reason:'outside_fov'};
  }
  if(mode==='distance')return {visible:true,reason:'radius_only_unverified'};
  if(mode!=='ray')throw Error('Unknown perception mode');
  const colliders=[...this.loop.active];
  const bodyIdByHandle=new Map(colliders.map(([id,b])=>[b.handle,id]));
  let firstBlock=null;
  for(const target of samples(e)){
   const direction=pointsTo(eye,target);
   if(!direction)continue;
   const ray=new RAPIER.Ray(eye,direction.dir);
   this.occlusionQueries++;
   const hit=this.loop.game.world.castRay(ray,direction.len+.1,true,
     undefined,undefined,undefined,this.loop.game.player);
   if(!hit){continue;}
   const hitBody=hit.collider?.parent();
   if(hitBody?.handle===body.handle)return {visible:true,reason:'actual_physics_first_hit',rayDistance:hit.timeOfImpact};
   if(!firstBlock){
    firstBlock={by:bodyIdByHandle.get(hitBody?.handle)||'core_world_collider',
      hitDistance:hit.timeOfImpact};
   }
  }
  return {visible:false,reason:'occluded_by_physical_collision',blocking:firstBlock};
 }
 perceive(eye,{radius=this.radius,mode='ray',facing=null,fovDegrees=360}={}){
  const statuses=[],allVisible=new Set(),perceived=new Set();
  for(const [id]of this.loop.entities){
   const state=this.isVisible(id,eye,{radius,mode,facing,fovDegrees});
   statuses.push({id,...state});
   if(state.visible){
    allVisible.add(id);perceived.add(id);
    // Physical ashes visibly present are evidence of the original destroyed
    // object, but the observer still cannot know unseen cause from that alone.
    let from=this.loop.entities.get(id).originId,steps=0;
    while(from&&steps++<6){
     perceived.add(from);from=this.loop.entities.get(from)?.originId;
    }
   }
  }
  return {visible:allVisible,perceived,statuses};
 }
 #fingerprint(e){
  const s=e.state||{};
  return JSON.stringify({
   condition:s.condition||'intact',destroyed:s.destroyed||false,
   tipped:s.tipped||false,moved:s.moved||false,rotated:s.rotated||false,
   supportId:e.supportId||null,dislodgedFrom:s.dislodgedFrom||null,
   originId:e.originId||null
  });
 }
 #eventText(ev,visible){
  const [aId,bId]=ev.ids,entity=this.loop.entities.get(aId);
  if(!entity)return null;
  // Do not reveal an unseen second actor/object involved in physical contact.
  if(bId&&!visible.has(bId)&&!this.loop.entities.get(bId)?.state?.destroyed)return null;
  const e=entity.name;
  const other=this.loop.entities.get(bId)?.name||'another object';
  const phrase={
   displaced:'has moved from its earlier position',
   tipped:'tipped over',righted:'became upright again',rotated:'rotated',
   impact:'collided with '+other,
   lost_support:'is no longer supported by '+other,
   rested_on:'has settled on '+other,
   external_impulse:'received a physical impulse',
   scorched:'was scorched',
   reduced_to_ashes:'was reduced to ashes',
   ash_remains:'is the remaining ash from '+other
  }[ev.type];
  return phrase?e+' '+phrase+'.':null;
 }
 // Subscribe at the exact authoritative *event emission time* so a
 // high-speed object cannot appear/disappear behind an occluder during the
 // subsequent physics step. A reloaded observer must reattach its live camera
 // callback explicitly; only witnessed event IDs survive as serialized data.
 attach(id,getEye,opts={}){
  if(typeof getEye!=='function'||this.attachments.has(id))throw Error('Invalid or duplicate observer attachment');
  this.#observer(id);
  const listener=()=>this.captureFrame(id,getEye(),opts);
  const unsubscribe=this.loop.subscribeEvents(listener);
  this.attachments.set(id,unsubscribe);
  return ()=>{unsubscribe();this.attachments.delete(id);};
 }
 // Fallback for physical events only when the caller can guarantee this is
 // the actual event instant. Calling it after a later physics step is NOT an
 // adequate substitute for the subscription above.
 // Cache *witnessed event IDs* (not hallucination-prone prose), so they remain
 // deliverable after the object has moved away and can survive save/reload.
 captureFrame(id,eye,{radius=this.radius,mode='ray',facing=null,fovDegrees=360}={}){
  const state=this.#observer(id);
  if(!posOK(eye))throw Error('Observer position is missing');
  let queued=0,unseen=0;
  for(const ev of this.loop.events){
   if(state.processed.has(ev.sequence))continue;
   const age=this.loop.time-ev.time;
   const immediate=age>=-.001&&age<=this.eventWindow+1e-7;
   if(!immediate){state.processed.add(ev.sequence);unseen++;continue;}
   const visible=new Set();
   for(const name of ev.ids){
    if(this.isVisible(name,eye,{radius,mode,facing,fovDegrees}).visible)visible.add(name);
    else if(this.loop.entities.get(name)?.state?.destroyed)visible.add(name);
   }
   const primaryVisible=visible.has(ev.ids[0]);
   const text=primaryVisible?this.#eventText(ev,visible):null;
   state.processed.add(ev.sequence);
   if(text){
    if(state.pending.length>=1024)throw Error('Observer delivery queue full; do not silently lose witnessed event');
    state.pending.push(ev.sequence);queued++;
   }else unseen++;
  }
  return {observerId:id,worldTime:this.loop.time,queuedWitnessEvents:queued,
   unobservedEvents:unseen,deliveryQueueSize:state.pending.length};
 }
 observe(id,eye,{radius=this.radius,mode='ray',facing=null,fovDegrees=360}={}){
  const state=this.#observer(id);
  if(!finite(this.loop.time)||this.loop.time+1e-6<state.lastTime)
   throw Error('Observer time reversal');
  const {visible}=this.perceive(eye,{radius,mode,facing,fovDegrees});
  const events=[],newlyVisible=[...visible].filter(x=>!state.lastVisible.has(x));
  // Event names are regenerated from authoritative saved world events and
  // captured event IDs. A tick-observed event is witnessed even if UI output
  // comes a second later or the object has since departed.
  const eventMap=new Map(this.loop.events.map(ev=>[ev.sequence,ev]));
  for(const sequence of state.pending){
   const ev=eventMap.get(sequence);
   if(!ev)throw Error('Queued observer event no longer exists');
   const text=this.#eventText(ev,new Set(ev.ids));
   if(text)events.push({sequence,text,capturedAtEventTime:true});
  }
  state.pending=[];
  let missed=0;
  // A late UI request is NOT evidence that an event was observed at the time
  // it occurred. Only explicit per-physics-step captureFrame can create
  // witnessed events. All other events remain internally true but causally
  // private; player text can expose only currently observable effects.
  for(const ev of this.loop.events){
   if(state.processed.has(ev.sequence))continue;
   state.processed.add(ev.sequence);missed++;
  }
  const changed=[];
  for(const entityId of visible){
   const e=this.loop.entities.get(entityId);
   if(!e)continue;
   const f=this.#fingerprint(e);
   if(state.facts.get(entityId)!==f){
    const one=this.loop.describe([entityId]);
    if(one)changed.push({id:entityId,text:one,sourceRevision:e.revision});
    state.facts.set(entityId,f);
   }
  }
  // Leave previous knowledge in the map, but record visibility transitions so
  // a returning player sees the correct now-state, rather than event replay.
  state.lastVisible=new Set(visible);
  state.lastTime=this.loop.time;
  return {observerId:id,worldTime:this.loop.time,mode,
   visibleIds:[...visible],newlyVisible,
   witnessedEvents:events,changedFacts:changed,
   pastUnobservedEventsNotNarrated:missed,rayQueries:this.occlusionQueries,
   narration:[...events.map(e=>e.text),...changed.map(e=>e.text)].join(' ')};
 }
 snapshot(){
  return {schema:2,radius:this.radius,eventWindow:this.eventWindow,
   observers:[...this.records].map(([id,e])=>({
    id,processed:[...e.processed].sort((a,b)=>a-b),
    queuedEvents:[...e.pending],
    facts:[...e.facts],lastVisible:[...e.lastVisible],lastTime:e.lastTime
   }))};
 }
 static restore(loop,serialized){
  if(!serialized||![1,2].includes(serialized.schema)||!Array.isArray(serialized.observers)
    ||serialized.observers.length>8||!finite(serialized.radius)
    ||!finite(serialized.eventWindow)||serialized.eventWindow<0||serialized.eventWindow>2)
   throw Error('Invalid observer snapshot');
  const self=new PRSEPhysicalObserver(loop,{visibilityRadius:serialized.radius,
    immediateEventWindowSeconds:serialized.eventWindow});
  const ids=new Set(loop.scene.entities.map(e=>e.id));
  const seqs=new Set(loop.events.map(e=>e.sequence));
  for(const o of serialized.observers){
   if(!validName(o.id)||self.records.has(o.id)||!Array.isArray(o.processed)
    ||!Array.isArray(o.facts)||!Array.isArray(o.lastVisible)
    ||!finite(o.lastTime)||o.lastTime>loop.time+1e-6
    ||o.processed.length>20000||o.facts.length>320||o.lastVisible.length>320
    ||o.lastTime<0||(o.queuedEvents!==undefined&&(!Array.isArray(o.queuedEvents)||o.queuedEvents.length>1024)))
    throw Error('Invalid observer record');
   if(!o.processed.every(n=>seqs.has(n))||!o.facts.every(x=>Array.isArray(x)&&x.length===2&&ids.has(x[0])&&typeof x[1]==='string')
    ||!o.lastVisible.every(x=>ids.has(x)))throw Error('Observer mentions unknown world truth');
   const processed=new Set(o.processed),queued=o.queuedEvents||[];
   if(new Set(queued).size!==queued.length||!queued.every(seq=>seqs.has(seq)&&processed.has(seq)))
    throw Error('Invalid captured event queue');
   self.records.set(o.id,{processed,pending:[...queued],facts:new Map(o.facts),
    lastVisible:new Set(o.lastVisible),lastTime:o.lastTime});
  }
  return self;
 }
}
