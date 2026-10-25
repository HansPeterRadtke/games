// Source-derived previously failed visibility timing cases. Both are physical
// real PRSE Rapier objects, chosen from the *fixed* external SceneEval subset.
// Previous post-step capture negative records are preserved unmodified.
import assert from'node:assert/strict';
import{readFileSync,writeFileSync}from'node:fs';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSEPhysicalObserver}from'./prse_physical_observer.mjs';
await initializePhysics();
const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const prev=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility/prse_observer_event_batch_200_raw_v1.json'));
const viewers=[
 {x:-27,y:1.5,z:11.8},{x:-32.8,y:1.5,z:7.9},{x:-21,y:1.5,z:7.9},
 {x:-32.8,y:1.5,z:15.7},{x:-21,y:1.5,z:15.7}
];
const rows=[];
for(const id of [27,29]){
 const proposal=repairScene(p[id],{maxSweeps:2,maxAttemptsPerScene:150});
 const w=new PRSELoop(proposal.scene);w.tick(18);
 const prior=prev.rows.find(x=>+x.id===id);
 assert(prior.status==='evaluated');
 const obj=w.scene.entities.find(e=>e.kind===prior.chosenCategory&&e.body==='dynamic');
 assert(obj);
 const watcher=new PRSEPhysicalObserver(w,{visibilityRadius:9});
 const seen=[],hidden=[];
 for(let i=0;i<viewers.length;i++){
  const eye=viewers[i];let bad=false;
  w.game.world.intersectionsWithPoint(eye,()=>{bad=true;return false});
  if(bad)continue;
  if(!watcher.isVisible(obj.id,eye,{mode:'distance',radius:9}).visible)continue;
  if(watcher.isVisible(obj.id,eye,{mode:'ray',radius:9}).visible)seen.push(i);else hidden.push(i);
 }
 assert(seen.length&&hidden.length);
 watcher.observe('eye-visible',viewers[seen[0]],{radius:9});
 watcher.observe('eye-blocked',viewers[hidden[0]],{radius:9});
 watcher.attach('eye-visible',()=>viewers[seen[0]],{radius:9});
 watcher.attach('eye-blocked',()=>viewers[hidden[0]],{radius:9});
 assert(w.applyImpulse(obj.id,{x:.8,y:.3,z:1.4}));
 const sequence=w.events.findLast(e=>e.type==='external_impulse').sequence;
 const atEmission=watcher.snapshot().observers;
 assert(atEmission.find(x=>x.id==='eye-visible').queuedEvents.includes(sequence));
 assert(!atEmission.find(x=>x.id==='eye-blocked').queuedEvents.includes(sequence));
 w.tick(1);
 assert(!w.eventSubscriberErrors.length);
 const afterStep={
  visible:watcher.isVisible(obj.id,viewers[seen[0]],{radius:9}).visible,
  blocked:watcher.isVisible(obj.id,viewers[hidden[0]],{radius:9}).visible
 };
 w.tick(60);
 const world=PRSELoop.restore(JSON.parse(JSON.stringify(w.snapshot())));assert(world.ok);
 const rest=PRSEPhysicalObserver.restore(world.loop,JSON.parse(JSON.stringify(watcher.snapshot())));
 const rSeen=rest.observe('eye-visible',viewers[seen[0]],{radius:9});
 const rBlocked=rest.observe('eye-blocked',viewers[hidden[0]],{radius:9});
 assert(rSeen.witnessedEvents.some(e=>e.sequence===sequence&&e.capturedAtEventTime));
 assert(!rBlocked.witnessedEvents.some(e=>e.sequence===sequence));
 assert(!rest.observe('eye-visible',viewers[seen[0]],{radius:9}).witnessedEvents.length);
 rows.push({id,category:obj.kind,sequence,
  priorOneFrameLateCapture:{visible:prior.queuedVisible,blocked:prior.queuedOccluded},
  atEmitterCapture:{visible:1,blocked:0},
  afterStepVisibility:afterStep,
  persistedVisibleDelivered:rSeen.witnessedEvents.some(e=>e.sequence===sequence),
  persistedOccludedSuppressed:rBlocked.witnessedEvents.every(e=>e.sequence!==sequence),
  subscriberErrors:w.eventSubscriberErrors.length});
 world.loop.dispose();w.dispose();
}
const output=process.argv.find(x=>x.startsWith('--output='))?.slice(9)||'prse_event_emission_timing_fix_v2.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(output))throw Error('Invalid output filename');
writeFileSync(new URL(output,import.meta.url),JSON.stringify({metadata:{source:'Frozen external SceneEval IDs 27 and 29; GameCore Rapier',
  selectedBecause:'Documented first-batch post-step observer failures; this is a regression comparison not independent population score',
  method:'Capture observer LOS from actual physical geometry synchronously at event emission before the next physics step'},results:rows},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(rows));
