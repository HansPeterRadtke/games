// Conservative research alternative for PRSE offscreen physical action streams.
// Contact solver remains resident while ANY known future physical action is due.
// Only after the final scheduled action and verified real-body settlement can
// a region unload for remaining semantic world time.
//
// This intentionally sacrifices physics-tick savings to preserve later contact
// history. It cannot guarantee what unknown future remote actors may do, and
// native full GameCore save/reload still lacks a complete Rapier solver snapshot.
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {physicallySettleThenUnload}from'./prse_offscreen_motion_settling.mjs';
const finite=v=>v&&['x','y','z'].every(k=>typeof v[k]==='number'&&Number.isFinite(v[k])&&Math.abs(v[k])<100);
export function playCausallyConservativeActions(loop,actions,{
 totalTicks=360,maxPhysicalTicks=120,requiredQuietTicks=20
}={}){
 if(!(loop instanceof PRSELoop)||!loop.active.size||!Array.isArray(actions)||
    actions.length>20||!Number.isInteger(totalTicks)||totalTicks<=0||totalTicks>7200)
  throw Error('Invalid active GameCore/schedule');
 const all=[...actions].sort((a,b)=>a.tick-b.tick),start=loop.time;
 let previous=0;
 const events=[],segments=[];
 // Preflight the ENTIRE known action plan before any physics effects.
 for(const e of all){
  if(!Number.isInteger(e.tick)||e.tick<1||e.tick>totalTicks||
     e.tick<=previous||!finite(e.impulse)||!loop.active.get(e.id)?.isDynamic())
   throw Error('Invalid future physical action or missing target');
  previous=e.tick;
 }
 previous=0;
 for(const e of all){
  const ticks=e.tick-previous;
  loop.tick(ticks); // preserve the living Rapier contact solver.
  segments.push({type:'contact_solver_kept_resident',physicalTicks:ticks,skippedTicks:0,
    endingWorldTime:loop.time});
  if(Math.abs(loop.time-start-e.tick/60)>1e-5)throw Error('Physical action time drift');
  if(!loop.applyImpulse(e.id,e.impulse))throw Error('Authoritative GameCore refused queued action');
  const ev=loop.events.at(-1);
  events.push({tick:e.tick,planned:start+e.tick/60,actual:loop.time,
   eventSequence:ev.sequence,source:ev.origin,physicalId:e.id,type:ev.type});
  previous=e.tick;
 }
 const rest=totalTicks-previous;
 let settled=null;
 if(rest>0){
  settled=physicallySettleThenUnload(loop,{
   totalTicks:rest,maxPhysicalTicks:Math.min(maxPhysicalTicks,rest),
   requiredQuietTicks:Math.min(requiredQuietTicks,Math.min(maxPhysicalTicks,rest))
  });
  segments.push({type:settled.offloaded?'late_contact_verified_offload':'full_native_physics_fallback',
   physicalTicks:settled.physicalTicks,skippedTicks:settled.skippedPhysicsTicks,
   endingWorldTime:loop.time,reason:settled.reason});
 }
 const skipped=settled?.skippedPhysicsTicks||0;
 if(Math.abs(loop.time-start-totalTicks/60)>1e-5)throw Error('Final authoritative clock discrepancy');
 return {loop,events,segments,skippedPhysicsTicks:skipped,offloadedAfterLastAction:!!settled?.offloaded,
  playerNeedsMayDiffer:true,finalWorldTime:loop.time,initialWorldTime:start,totalTicks};
}
