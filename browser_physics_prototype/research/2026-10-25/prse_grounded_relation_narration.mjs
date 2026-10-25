// PRSE research-only semantic fact projection from authoritative GameCore/Rapier
// bodies. Raw literary source remains immutable; only verified current relations
// are eligible to become player-facing factual statements.
//
// This is deliberately conservative: no guessed object-instance coreference,
// no prose claiming a cause without a witnessed event, no inferred 'inside'
// a solid collider, and no use of a source adjective as measured geometry.
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {createHash} from 'node:crypto';

const finite=x=>typeof x==='number'&&Number.isFinite(x);
const copy=x=>structuredClone(x);
// Exact Euclidean surface gap between axis-aligned physical bounding boxes
// on horizontal X/Z; combined with vertical separation to measure true 3D
// distance. Max-axis (Chebyshev) approximation overstates proximity diagonally.
const gap=(a,b)=>Math.hypot(
 Math.max(0,Math.abs(a.position.x-b.position.x)-(a.size.x+b.size.x)/2),
 Math.max(0,Math.abs(a.position.z-b.position.z)-(a.size.z+b.size.z)/2));
function bounds(e){
 return {min:{x:e.position.x-e.size.x/2,y:e.position.y-e.size.y/2,z:e.position.z-e.size.z/2},
  max:{x:e.position.x+e.size.x/2,y:e.position.y+e.size.y/2,z:e.position.z+e.size.z/2}};
}
function contacts(loop,a,b){
 const A=loop.active.get(a.id),B=loop.active.get(b.id);
 if(!A?.numColliders()||!B?.numColliders())return null;
 let touch=false;
 loop.game.world.contactPair(A.collider(0),B.collider(0),manifold=>{
  if(manifold.numContacts()>0)touch=true;
 });
 return touch;
}
function taggedEntity(e){
 return e && e.source!=='provisional_3D_room_boundary' && !e.state?.destroyed
  && e.state?.condition!=='ashes';
}
export function measureRelation(loop,relation){
 if(!(loop instanceof PRSELoop)||!relation||typeof relation!=='object')
  throw Error('Invalid world/relation');
 const mapped=(kind)=>loop.scene.entities.filter(e=>e.kind===kind&&taggedEntity(e));
 if(relation.kind==='room')return {truth:'unknown',reason:'room_anchor_geometry_not_verified',
   sourceKind:relation.kind,sourceType:relation.type};
 if(relation.kind!=='object'||typeof relation.type!=='string')
  return {truth:'unknown',reason:'unsupported_relation_kind'};
 const first=mapped(relation.a),second=mapped(relation.b);
 if(first.length!==1||second.length!==1||first[0]===second[0])
  return {truth:'unknown',reason:'unresolved_instance_identity',aCount:first.length,bCount:second.length};
 const a=first[0],b=second[0];
 const ids=[a.id,b.id],unknown=reason=>({truth:'unknown',reason,ids});
 if(!loop.active.has(a.id)||!loop.active.has(b.id))return unknown('unmaterialized_or_offscreen');
 const A=bounds(a),B=bounds(b),typ=relation.type;
 const horizontal=gap(a,b);
 const vertical=Math.max(0,A.min.y-B.max.y,B.min.y-A.max.y);
 const metricClearance=Math.hypot(horizontal,vertical);
 const dy=a.position.y-b.position.y;
 const known=(yes,method)=>({truth:yes?'true':'false',reason:method,ids,
   worldTime:loop.time,sourceSpan:relation.sourceText||null});
 const aBase=A.min.y,bTop=B.max.y;
 switch(typ){
  case 'on':{
   if(b.shape==='sphere')return unknown('round_surface_support_unmodeled');
   // Verify BOTH geometric support and real contact when a dynamic physics
   // collider exists. Fixed/fixed architectural props need exact plane fit;
   // merely having a stale semantic supportId is not sufficient.
   const footprint=A.min.x>=B.min.x-.015&&A.max.x<=B.max.x+.015
    &&A.min.z>=B.min.z-.015&&A.max.z<=B.max.z+.015;
   const vertical=Math.abs(aBase-bTop)<=.055;
   const collision=contacts(loop,a,b);
   const body=loop.active.get(a.id);
   if(collision===null)return unknown('collision_queries_unavailable');
   if(body.isDynamic() && !collision && vertical)return unknown('dynamic_contact_not_confirmed');
   return known(footprint&&vertical&&(collision||!body.isDynamic()),
     'Rapier_contact_and_top_surface_or_exact_fixed_geometry');
  }
  case 'inside':{
   // A solid cupboard/bookshelf collider is NOT an open interior. Saying 'inside'
   // requires an actually represented open physical container volume.
   if(b.shape!=='open_box')return unknown('missing_physical_interior_geometry');
   const eps=.07;
   const contained=A.min.x>B.min.x+eps&&A.max.x<B.max.x-eps&&
      A.min.z>B.min.z+eps&&A.max.z<B.max.z-eps&&
      A.min.y>B.min.y+eps&&A.max.y<B.max.y+eps;
   return known(contained,'actual_open_container_bounds');
  }
  case 'near':case 'next':case 'adjacent':
   return known(metricClearance<=(typ==='near'?1.5:1.1),
     'metric_three_dimensional_surface_clearance');
  case 'front':case 'behind':case 'left':case 'right':{
   // The axes are those of the world; this is not perspective-relative speech.
   if(!relation.frame||relation.frame!=='global-xyz')
    return unknown('unresolved_view_frame_for_direction');
   if(typ==='front')return known(a.position.z<b.position.z-.3,'declared_world_frame');
   if(typ==='behind')return known(a.position.z>b.position.z+.3,'declared_world_frame');
   if(typ==='left')return known(a.position.x<b.position.x-.3,'declared_world_frame');
   return known(a.position.x>b.position.x+.3,'declared_world_frame');
  }
  case 'above':return known(aBase>bTop-.05,'separated_vertical_aabb');
  case 'under':return known(A.max.y<B.min.y+.05,'separated_vertical_aabb');
  case 'across':case 'opposite':case 'surround':case 'between':
  case 'side_of':case 'face':case 'against':case 'in':
   return unknown('unresolved_topology_orientation_or_occlusion');
  default:return unknown('unsupported_relation_type');
 }
}
const posLabel=(kind)=>kind.replaceAll('_',' ').replace(/\s+/g,' ').trim();
const finiteId=id=>typeof id==='string'&&/^[a-z][a-z0-9-]{2,80}$/.test(id);
export class PRSEGroundedFacts{
 constructor(loop,sourceRelations,{maxClaims=512}={}){
  if(!(loop instanceof PRSELoop)||!Array.isArray(sourceRelations)||sourceRelations.length>maxClaims)
   throw Error('Unsupported evidence size');
  this.world=loop;this.sources=copy(sourceRelations);
  this.signature=new Map();this.delivered=new Map();
  this.maxClaims=maxClaims;
  this.savedProofs=new Map();this.proofWorldTime=null;
 }
 #fingerprintSource(){
  return createHash('sha256').update(JSON.stringify(this.sources)).digest('hex');
 }
 #pose(id){
  const e=this.world.entities.get(id),body=this.world.active.get(id);
  if(!e||!body)return null;
  // A previously verified contact may be carried through ONE instant of
  // restore with the exact same authoritative entity/velocity/rotation, but
  // it may not claim a newly simulated collision/contact manifold.
  return {id:e.id,kind:e.kind,shape:e.shape,revision:e.revision,
   supportId:e.supportId??null,
   position:copy(e.position),velocity:copy(e.velocity),rotation:copy(e.rotation)};
 }
 #matchesPose(old,current){
  if(!old||!current||old.id!==current.id||old.kind!==current.kind||
     old.shape!==current.shape||old.supportId!==current.supportId)return false;
  for(const k of ['position','velocity']){
   if(!old[k]||!current[k]||!['x','y','z'].every(axis=>
    finite(old[k][axis])&&finite(current[k][axis])&&
    Math.abs(old[k][axis]-current[k][axis])<.00005))return false;
  }
  if(!old.rotation||!current.rotation||
   !['x','y','z','w'].every(axis=>finite(old.rotation[axis])&&finite(current.rotation[axis])
    &&Math.abs(old.rotation[axis]-current.rotation[axis])<.00005))return false;
  return true;
 }
 current(){
  return this.sources.map((relation,i)=>{
   const actual=measureRelation(this.world,relation);
   const prior=this.savedProofs.get(i);
   // Source of truth remains the actual physical current state. This conditional
   // saved evidence is ONLY a temporary bridge over the Rapier contact query
   // rebuild that occurs on the first physics step after GameCore restore.
   if(actual.truth==='unknown'&&actual.reason==='dynamic_contact_not_confirmed'&&
      prior&&prior.truth==='true'&&this.proofWorldTime!==null&&
      Math.abs(this.world.time-this.proofWorldTime)<1e-7 &&
      prior.sourceHash===this.#fingerprintSource()&&
      prior.entities?.length===2&&
      this.#matchesPose(prior.entities[0],this.#pose(prior.ids[0]))&&
      this.#matchesPose(prior.entities[1],this.#pose(prior.ids[1]))){
    return {key:i,source:copy(relation),truth:'true',
     reason:'previously_verified_contact_at_unchanged_restored_pose',
     evidenceOriginallyMeasuredAt:prior.evidenceAt,
     temporallyInherited:true,ids:copy(prior.ids)};
   }
   return {key:i,source:copy(relation),...actual};
  });
 }
 verified(){
  return this.current().filter(x=>x.truth==='true');
 }
 render(row){
  if(row.truth!=='true')throw Error('Never narrate a claim lacking physical evidence');
  const ids=row.ids||[];
  if(ids.length!==2)throw Error('Requires two grounded identities');
  const a=this.world.entities.get(ids[0]),b=this.world.entities.get(ids[1]);
  if(!a||!b||a.state?.destroyed||b.state?.destroyed)throw Error('Missing actual world truth');
  const names=[posLabel(a.name),posLabel(b.name)];
  const phrasing={
   on:'rests on',inside:'is inside',near:'is near',next:'is next to',adjacent:'is adjacent to',
   front:'is in front of',behind:'is behind',left:'is to the left of',
   right:'is to the right of',above:'is above',under:'is below'
  }[row.source.type];
  if(!phrasing)throw Error('No authorized relation phrasing');
  return names[0]+' '+phrasing+' '+names[1]+'.';
 }
 // Observe typed claims only when *both physical objects* are visible under
 // the caller's separately verified PRSEPhysicalObserver eye/occlusion test.
 // We never infer who witnessed the *cause* of an old relation change.
 observe(observerId,visibleIds){
  if(!finiteId(observerId)||!Array.isArray(visibleIds)||visibleIds.length>320
    ||!visibleIds.every(finiteId))throw Error('Invalid observer input');
  const visible=new Set(visibleIds),past=this.delivered.get(observerId)||new Map();
  const changed=[],unverifiable=[];
  for(const row of this.current()){
   if(row.truth==='unknown'){unverifiable.push({key:row.key,reason:row.reason});continue;}
   if(!row.ids?.every(id=>visible.has(id)))continue;
   const old=past.get(row.key);
   // Only narrate meaningful transitions; never retroactively claim witnessing.
   const signature=row.truth+'|'+(row.ids||[]).join(',');
   if(old!==signature){
    if(row.truth==='true')changed.push({
     key:row.key,kind:'verified_now',text:this.render(row),sources:[...row.ids],evidence:row.reason
    });
    else if(old?.startsWith('true|')){
     const [a,b]=row.ids.map(id=>this.world.entities.get(id));
     // Name only the entities proved by the earlier report and physically
     // identified now. Do not claim the cause, witness, or timing of a loss.
     const aName=posLabel(a?.name||row.source.a),bName=posLabel(b?.name||row.source.b);
     const negative={
      on:'no longer rests on',inside:'is no longer inside',near:'is no longer near',
      next:'is no longer next to',adjacent:'is no longer adjacent to',
      front:'is no longer in front of',behind:'is no longer behind',
      left:'is no longer to the left of',right:'is no longer to the right of',
      above:'is no longer above',under:'is no longer below'
     }[row.source.type];
     if(!negative)throw Error('Missing exact factual retraction grammar');
     changed.push({key:row.key,kind:'no_longer_verified',
      text:aName+' '+negative+' '+bName+'.',sources:[...row.ids],evidence:row.reason});
    }
    past.set(row.key,signature);
   }
  }
  this.delivered.set(observerId,past);
  return {changed,unverifiable,worldTime:this.world.time,
   sourceProseUnchanged:this.world.scene.prose};
 }
 snapshot(){
  const proofs=[],now=this.current(),hash=this.#fingerprintSource();
  for(const row of now){
   if(row.truth!=='true'||row.source.type!=='on'||!row.ids||row.ids.length!==2)continue;
   const evidenceAt=row.temporallyInherited?row.evidenceOriginallyMeasuredAt:this.world.time;
   const pair=row.ids.map(id=>this.#pose(id));
   if(pair.some(x=>!x))continue;
   proofs.push({key:row.key,truth:'true',type:row.source.type,ids:copy(row.ids),
    sourceHash:hash,evidenceAt,entities:pair});
  }
  return {schema:2,sceneId:this.world.scene.id,sourceCount:this.sources.length,
   sourceHash:hash,worldTime:this.world.time,
   physicalProofs:proofs,
   delivered:[...this.delivered].map(([id,map])=>({id,facts:[...map]}))};
 }
 static restore(world,sources,save){
  const o=new PRSEGroundedFacts(world,sources);
  if(!save||![1,2].includes(save.schema)||save.sceneId!==world.scene.id||
     save.sourceCount!==sources.length||!Array.isArray(save.delivered)||save.delivered.length>8)
   throw Error('Invalid narrative truth journal');
  if(save.schema===2){
   if(!Array.isArray(save.physicalProofs)||save.physicalProofs.length>sources.length||
      save.sourceHash!==o.#fingerprintSource()||!finite(save.worldTime)||
      Math.abs(save.worldTime-world.time)>1e-7)
    throw Error('Inconsistent saved physical proof');
   const keys=new Set();
   for(const row of save.physicalProofs){
    if(!Number.isInteger(row.key)||keys.has(row.key)||row.key<0||row.key>=sources.length||
       row.type!=='on'||sources[row.key].type!=='on'||row.truth!=='true'||
       row.sourceHash!==save.sourceHash||!finite(row.evidenceAt)||
       row.evidenceAt>save.worldTime+1e-7||!Array.isArray(row.ids)||row.ids.length!==2||
       !Array.isArray(row.entities)||row.entities.length!==2||
       !row.ids.every((id,i)=>o.#matchesPose(row.entities[i],o.#pose(id))))
     throw Error('Invalid or forged physical evidence');
    keys.add(row.key);o.savedProofs.set(row.key,copy(row));
   }
   o.proofWorldTime=world.time;
  }
  for(const row of save.delivered){
   if(!finiteId(row.id)||!Array.isArray(row.facts)||row.facts.length>sources.length)
    throw Error('Invalid observer facts');
   const restored=new Map();
   for(const [k,v]of row.facts){
    if(!Number.isInteger(k)||k<0||k>=sources.length||typeof v!=='string'||
       !/^(true|false)\|[a-z0-9-]{3,80},[a-z0-9-]{3,80}$/.test(v)||restored.has(k))
     throw Error('Forged relation journal entry');
    restored.set(k,v);
   }
   if(o.delivered.has(row.id))throw Error('Duplicate observer');
   o.delivered.set(row.id,restored);
  }
  return o;
 }
}
