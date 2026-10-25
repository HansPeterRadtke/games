// Investigate two *preserved observed* trajectory divergences in offscreen
// benchmark even though the settling policy REFUSED offloading. Compare
// independently restored, fully uninterrupted native GameCore baselines,
// one-tick-at-a-time stepping and the query-heavy conservative fallback.
//
// The original corpus result is retained untouched; do not reclassify its
// measured error as offscreen fidelity without this independent control.
import{readFileSync,writeFileSync}from'node:fs';
import{initializePhysics}from'../../physics-core.js';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{physicallySettleThenUnload}from'./prse_offscreen_motion_settling.mjs';
await initializePhysics();
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const previous=[
 ...JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-offscreen-motion/prse_offscreen_motion_human_raw_v1.json')).results,
 ...JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-offscreen-motion/prse_offscreen_motion_assisted_raw_v1.json')).results];
const out=[];
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
for(const id of [91,140]){
 const prior=previous.find(x=>Number(x.id)===id&&x.impulse==='strong');
 if(!prior||prior.offloaded)throw Error('Expected preserved non-unloaded negative result');
 const scene=repairScene(proposals[id],{maxSweeps:2,maxAttemptsPerScene:150}).scene;
 for(let trial=0;trial<3;trial++){
  let original=null;
  const clones=[];
  try{
   original=new PRSELoop(scene);original.tick(18);
   if(!original.applyImpulse(prior.entityId,prior.impulseVector))throw Error('Unable to apply original input');
   const snapshot=JSON.parse(JSON.stringify(original.snapshot()));
   for(let j=0;j<3;j++){
    const copy=PRSELoop.restore(snapshot);
    if(!copy.ok)throw Error('Unable to clone GameCore');
    clones.push(copy.loop);
   }
   const [full,individual,probe]=clones;
   full.tick(300);
   for(let i=0;i<300;i++)individual.tick(1);
   const result=physicallySettleThenUnload(probe,{totalTicks:300,maxPhysicalTicks:150,requiredQuietTicks:20});
   const x=full.active.get(prior.entityId).translation(),
    y=individual.active.get(prior.entityId).translation(),
    z=probe.active.get(prior.entityId).translation();
   const e={id,trial,offloaded:result.offloaded,skippedTicks:result.skippedPhysicsTicks,
    continuousVsOneTickReplayMeters:dist(x,y),
    continuousVsContactProbeReplayMeters:dist(x,z),
    oneTickVsContactProbeReplayMeters:dist(y,z),
    originalCorpusSavedDifferenceMeters:prior.poseAfterOneTick.maxPositionMeters,
    allWorldTimes:[full.time,individual.time,probe.time]};
   out.push(e);
  }finally{for(const l of clones)l.dispose();original?.dispose();}
 }
}
const file=new URL('prse_full_physics_outlier_controls_v1.json',import.meta.url);
writeFileSync(file,JSON.stringify({metadata:{source:'Prior preserved SceneEval source IDs 91 and 140, fixed strong impulses',
  purpose:'Control for full-physics intrinsic trajectory variability and extra contact queries; no reinterpretation of original data'},results:out},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(out));
