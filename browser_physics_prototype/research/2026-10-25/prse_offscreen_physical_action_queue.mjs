// Research-only causal, timed physical action schedule for ONE unloaded PRSE
// region. All impulses come from a validated, explicit game-world action queue,
// not a model hallucinating consequences.
//
// For each future action, advance world time from last event until that time:
// physically simulate until verified stable or continue physical stepping,
// optionally dematerialize and keep semantic time, rematerialize at action time.
// Then run actual GameCore.applyImpulse on the same stable physical entity ID.
// This never invents trajectories, pauses time, or skips uncertain moving bodies.
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {physicallySettleThenUnload} from './prse_offscreen_motion_settling.mjs';
const vec=v=>v&&['x','y','z'].every(k=>typeof v[k]==='number'&&Number.isFinite(v[k])&&Math.abs(v[k])<=100);
export function playQueuedPhysicalActions(loop,actions,{
 totalTicks=360,maxPhysicalTicks=180,requiredQuietTicks=20,
 reloadAtEachEvent=true
}={}){
 if(!(loop instanceof PRSELoop)||!loop.active.size)throw Error('Expected one currently materialized authoritative world');
 if(!Array.isArray(actions)||actions.length>20||
    !Number.isInteger(totalTicks)||totalTicks<=0||totalTicks>7200)
  throw Error('Invalid bounded world-time schedule');
 const sorted=[...actions].sort((a,b)=>a.tick-b.tick);
 let previousTick=0;
 const originalTime=loop.time,originalSource=loop.scene.prose;
 const journal=[],eventRecords=[];
 for(const event of sorted){
  if(!Number.isInteger(event.tick)||event.tick<25||event.tick>totalTicks-25||
     event.tick-previousTick<25||typeof event.id!=='string'||!vec(event.impulse))
   throw Error('Bad/overlapping physical action schedule');
  const e=loop.entities.get(event.id);
  if(!e||e.body!=='dynamic'||e.state?.destroyed)throw Error('Event target absent or no longer dynamic');
  const advancing=event.tick-previousTick;
  const segment=physicallySettleThenUnload(loop,{
   totalTicks:advancing,maxPhysicalTicks:Math.min(maxPhysicalTicks,advancing),
   requiredQuietTicks:Math.min(requiredQuietTicks,Math.min(maxPhysicalTicks,advancing))
  });
  journal.push({segmentTicks:advancing,startedAt:originalTime+previousTick/60,
   finishedAt:loop.time,offloaded:segment.offloaded,
   physicalTicks:segment.physicalTicks,skippedPhysicsTicks:segment.skippedPhysicsTicks,
   cause:segment.reason});
  if(Math.abs(loop.time-(originalTime+event.tick/60))>1e-5)
   throw Error('Event action clock drift');
  if(reloadAtEachEvent){
   const saved=JSON.parse(JSON.stringify(loop.snapshot()));
   const restored=PRSELoop.restore(saved);
   if(!restored.ok)throw Error('GameCore save/reentry at action time rejected');
   const previous=loop;
   loop=restored.loop;
   previous.dispose();
  }
  const afterReload=loop.entities.get(event.id);
  if(!afterReload||!loop.active.has(event.id))throw Error('Physical target did not rematerialize by event time');
  const beforePose={...loop.active.get(event.id).translation()};
  if(!loop.applyImpulse(event.id,event.impulse))throw Error('Authoritative impulse application failed');
  const emitted=loop.events.at(-1);
  eventRecords.push({id:event.id,tick:event.tick,plannedTime:originalTime+event.tick/60,
   appliedTime:loop.time,source:'scheduled game action',
   vector:event.impulse,priorPosition:beforePose,sequence:emitted.sequence,
   kind:emitted.type,authoritativeOrigin:emitted.origin});
  previousTick=event.tick;
 }
 const remaining=totalTicks-previousTick;
 if(remaining>0){
  const segment=physicallySettleThenUnload(loop,{
   totalTicks:remaining,maxPhysicalTicks:Math.min(maxPhysicalTicks,remaining),
   requiredQuietTicks:Math.min(requiredQuietTicks,Math.min(maxPhysicalTicks,remaining))
  });
  journal.push({segmentTicks:remaining,startedAt:originalTime+previousTick/60,
   finishedAt:loop.time,offloaded:segment.offloaded,
   physicalTicks:segment.physicalTicks,skippedPhysicsTicks:segment.skippedPhysicsTicks,
   cause:segment.reason});
 }
 if(Math.abs(loop.time-(originalTime+totalTicks/60))>1e-5||
    loop.scene.prose!==originalSource)
  throw Error('Clock or original literary source was not preserved');
 return {loop,originalTime,finalWorldTime:loop.time,sourcePreserved:true,
  horizonTicks:totalTicks,actionRecords:eventRecords,segments:journal,
  offloadSegments:journal.filter(x=>x.offloaded).length,
  skippedPhysicsTicks:journal.reduce((n,x)=>n+x.skippedPhysicsTicks,0),
  physicsTicks:journal.reduce((n,x)=>n+x.physicalTicks,0)};
}
