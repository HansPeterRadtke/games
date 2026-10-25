// Explicit deterministic local constraint repair on previous frozen text proposals.
// No SceneEval annotations and no language model calls. Physics stays GameCore/Rapier.
// This is an alternative to the prior greedy one-pass placement, not a new game.
import {compileProposal,validRelation} from '../2026-10-24/prse_constraint_layout.mjs';
import {geometryIssues} from '../2026-10-24/prse_semantic_roundtrip.mjs';

const clone=x=>structuredClone(x);
const ROOM={cx:-27,cz:11.8,hx:9.4,hz:6.6};
function score(relations,objects){
 const records=relations.map(r=>validRelation(r,objects));
 return {trueCount:records.filter(x=>x===true).length,
  falseCount:records.filter(x=>x===false).length,
  unsupported:records.filter(x=>x===null).length,
  states:records};
}
function candidatesFor(r,a,b){
 const out=[];
 if(r.kind==='room'){
  if(r.type==='corner'){
   for(const sx of [-1,1])for(const sz of [-1,1])for(const pad of [.45,1,1.7]){
    out.push({x:ROOM.cx+sx*(ROOM.hx-a.size.x/2-pad),
      y:a.position.y,z:ROOM.cz+sz*(ROOM.hz-a.size.z/2-pad)});
   }
  }else if(r.type==='against'&&r.b==='wall'){
   for(const pad of [.25,.5,.7])for(const z of [ROOM.cz-4,ROOM.cz,ROOM.cz+4]){
    out.push({x:ROOM.cx-ROOM.hx+a.size.x/2+pad,y:a.position.y,z});
    out.push({x:ROOM.cx+ROOM.hx-a.size.x/2-pad,y:a.position.y,z});
   }
   for(const x of [ROOM.cx-5,ROOM.cx,ROOM.cx+5]){
    out.push({x,y:a.position.y,z:ROOM.cz-ROOM.hz+a.size.z/2+.4});
    out.push({x,y:a.position.y,z:ROOM.cz+ROOM.hz-a.size.z/2-.4});
   }
  }else if(['middle','center'].includes(r.type)){
   for(const dx of [0,-.4,.4,-1.3,1.3])for(const dz of [0,-.4,.4]){
    out.push({x:ROOM.cx+dx,y:a.position.y,z:ROOM.cz+dz});
   }
  }
  return out;
 }
 if(!b)return [];
 const offX=(a.size.x+b.size.x)/2,offZ=(a.size.z+b.size.z)/2;
 if(r.type==='on'){
  const diffX=(b.size.x-a.size.x)/2,diffZ=(b.size.z-a.size.z)/2;
  if(diffX<.01||diffZ<.01)return [];
  for(const fx of [0,-.5,.5])for(const fz of [0,-.5,.5]){
   out.push({x:b.position.x+fx*diffX,
     y:b.position.y+b.size.y/2+a.size.y/2+.001,z:b.position.z+fz*diffZ,
     supportId:b.id});
  }
  return out;
 }
 if(['near','next','beside','adjacent'].includes(r.type)){
  for(const margin of [.12,.4,.7]){
   for(const dx of [-1,1])for(const z of [0,-1,1]){
    out.push({x:b.position.x+dx*(offX+margin),y:a.position.y,
     z:b.position.z+z*(offZ+margin)});
   }
   for(const dz of [-1,1])for(const x of [-1,0,1]){
    out.push({x:b.position.x+x*(offX+margin),y:a.position.y,
     z:b.position.z+dz*(offZ+margin)});
   }
  }
  return out;
 }
 if(['front','behind','left','right'].includes(r.type)){
  for(const gap of [.2,.5,1.1]){
   for(const lateral of [0,-1,1,-2.5,2.5]){
    if(r.type==='front')out.push({x:b.position.x+lateral,y:a.position.y,z:b.position.z-offZ-gap});
    if(r.type==='behind')out.push({x:b.position.x+lateral,y:a.position.y,z:b.position.z+offZ+gap});
    if(r.type==='left')out.push({x:b.position.x-offX-gap,y:a.position.y,z:b.position.z+lateral});
    if(r.type==='right')out.push({x:b.position.x+offX+gap,y:a.position.y,z:b.position.z+lateral});
   }
  }
  return out;
 }
 if(['across','opposite'].includes(r.type)){
  for(const dx of [-5,-3.5,0,3.5,5])for(const dz of [-4,0,4]){
   if(Math.hypot(dx,dz)>2.5)out.push({x:b.position.x+dx,y:a.position.y,z:b.position.z+dz});
  }
 }
 if(r.type==='above'){
  // Requires b to be a valid physical support, otherwise 'above' is an
  // unsupported floating relation and must NOT be implemented by levitation.
  return candidatesFor({...r,type:'on'},a,b);
 }
 return out;
}
function fitCandidate(scene,a,patch){
 const old={...a.position},oldSupport=a.supportId;
 a.position={x:patch.x,y:patch.y,z:patch.z};
 if(patch.supportId)a.supportId=patch.supportId;
 // Avoid moving support parents while their children would be stranded.
 const errors=geometryIssues(scene);
 const valid=errors.length===0;
 a.position=old;a.supportId=oldSupport;
 return valid;
}
export function repairScene(parsed,{maxSweeps=3,maxAttemptsPerScene=500}={}){
 const compiled=compileProposal(parsed);
 const baseline=clone(compiled.scene);
 const relations=parsed.relations||[];
 const before=score(relations,baseline.entities);
 const current=clone(baseline);
 const log=[];
 let attempted=0;
 for(let sweep=0;sweep<maxSweeps;sweep++){
  let improvement=false;
  for(let j=0;j<relations.length;j++){
   const r=relations[j],states=score(relations,current.entities);
   if(states.states[j]===true||states.states[j]===null)continue;
   const a=current.entities.find(x=>x.kind===r.a),b=current.entities.find(x=>x.kind===r.b);
   if(!a||a.kind==='wall'||current.entities.some(x=>x.supportId===a.id))continue;
   if(a.supportId&&a.supportId!=='floor'&&r.type!=='on')continue;
   const prior={position:{...a.position},supportId:a.supportId};
   let best=null,bestScore=states.trueCount;
   for(const patch of candidatesFor(r,a,b)){
    if(++attempted>maxAttemptsPerScene)break;
    if(!fitCandidate(current,a,patch))continue;
    const previous={...a.position},previousSupport=a.supportId;
    a.position={x:patch.x,y:patch.y,z:patch.z};
    if(patch.supportId)a.supportId=patch.supportId;
    const after=score(relations,current.entities);
    a.position=previous;a.supportId=previousSupport;
    if(after.states[j]!==true)continue;
    // Does not sacrifice other source constraints to optimize this one.
    if(after.trueCount>bestScore){
     bestScore=after.trueCount;best={patch,states:after};
    }
   }
   if(best){
    a.position={x:best.patch.x,y:best.patch.y,z:best.patch.z};
    if(best.patch.supportId)a.supportId=best.patch.supportId;
    improvement=true;
    log.push({sweep,sourceRelationIndex:j,type:r.type,a:r.a,b:r.b,
       from:prior,to:{position:{...a.position},supportId:a.supportId},
       totalGroundedBefore:states.trueCount,totalGroundedAfter:bestScore});
   }
  }
  if(!improvement||attempted>=maxAttemptsPerScene)break;
 }
 const after=score(relations,current.entities);
 const issues=geometryIssues(current);
 const candidates=current.entities.filter(x=>x.source!=='provisional_3D_room_boundary');
 const original=baseline.entities.filter(x=>x.source!=='provisional_3D_room_boundary');
 const geometricMovement=candidates.reduce((sum,x)=>{
  const former=original.find(e=>e.id===x.id);
  return sum+Math.hypot(x.position.x-former.position.x,x.position.y-former.position.y,x.position.z-former.position.z);
 },0);
 const accepted=issues.length===0&&after.trueCount>=before.trueCount;
 return {
  proposalId:parsed.sourceId,baselineValid:compiled.good,accepted,
  scene:accepted?current:baseline,
  before:{grounded:before.trueCount,violated:before.falseCount,unsupported:before.unsupported},
  after:{grounded:after.trueCount,violated:after.falseCount,unsupported:after.unsupported},
  sourceConstraints:relations.length,missing:compiled.missing,
  amended:log,attempts:attempted,provisionalObjects:candidates.length,
  summedPositionChangeMetres:geometricMovement,
  remainingInvalidIssues:issues,
  claims:'Repair uses only pre-extracted source constraints; cannot restore relations never extracted or infer exact natural-language meaning.'
 };
}
