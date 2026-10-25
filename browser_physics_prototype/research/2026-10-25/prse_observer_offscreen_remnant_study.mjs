// Actual offscreen process rule → distinct physical ash-remnant collider on reentry
// → observer gets current changed fact, not unwitnessed past ignition. Original
// source narrative and destroyed note ID remain part of the world ledger.
import assert from 'node:assert/strict';
import {writeFileSync}from'node:fs';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,object}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEPhysicalObserver}from'./prse_physical_observer.mjs';
await initializePhysics();
const scene={id:'offscreen-causal-residue-room',
 prose:'A paper note rests on a wooden desk in a room the traveler has left.',
 entities:[
  object('desk-old','desk',{x:-25,y:.45,z:9},{x:2,y:.9,z:1.2},{material:'wood',body:'fixed'}),
  object('paper-original','note',{x:-25,y:.91,z:9},{x:.25,y:.02,z:.2},
   {material:'paper',mass:.04,supportId:'desk-old'})
 ]};
const w=new PRSELoop(scene);
w.tick(55);
const obs=new PRSEPhysicalObserver(w,{visibilityRadius:6});
const remote={x:0,y:1.5,z:0},returned={x:-24,y:1.5,z:9};
const prior=obs.observe('player-test',remote,{radius:6});
assert.equal(prior.visibleIds.length,0);
w.dematerialize();
assert(w.igniteOffscreen('paper-original'));
w.advanceOffscreen(12);
const originalNote=w.entities.get('paper-original');
const ash=[...w.entities.values()].find(x=>x.originId==='paper-original');
assert(originalNote.state.destroyed&&ash);
assert(!w.active.size,'offscreen is semantic state, not continuous remote physics');
const worldState=JSON.parse(JSON.stringify(w.snapshot()));
const observerState=JSON.parse(JSON.stringify(obs.snapshot()));
const recovered=PRSELoop.restore(worldState);assert(recovered.ok);
const loaded=recovered.loop,restored=PRSEPhysicalObserver.restore(loaded,observerState);
const created=loaded.materialize();
assert(created===2&&loaded.active.has(ash.id)&&!loaded.active.has('paper-original'));
const visible=restored.observe('player-test',returned,{radius:6});
assert(visible.visibleIds.includes(ash.id));
assert(visible.witnessedEvents.length===0,'Player heard unseen ignition and ash formation');
assert(visible.changedFacts.some(f=>f.id===ash.id&&f.text.toLowerCase().includes('ash')));
assert.equal(restored.observe('player-test',returned,{radius:6}).changedFacts.length,0);
assert.equal(loaded.scene.prose,scene.prose);
assert(loaded.entities.has('paper-original'));
const reenterSnapshot=restored.snapshot();
const reopened=PRSELoop.restore(JSON.parse(JSON.stringify(loaded.snapshot())));assert(reopened.ok);
const watcher=PRSEPhysicalObserver.restore(reopened.loop,
 JSON.parse(JSON.stringify(reenterSnapshot)));
const secondVisit=watcher.observe('player-test',returned,{radius:6});
assert(secondVisit.witnessedEvents.length===0&&secondVisit.changedFacts.length===0);
const r={metadata:{source:'Original PRSE August 13 semantic fire/reentry question, performed in research-only GameCore/Rapier',
  cause:'Explicit offscreen authored semantic ignition/process rule, NOT physics-simulated chemistry',
  observerPolicy:'physical seven-ray occlusion check and event-time-only witness ledger'},
 simulation:{nativeTime:loaded.game.time,semanticTime:loaded.time,
  physicalObjectsAfterReturn:created,ashColliderCount:loaded.active.get(ash.id).numColliders(),
  stableNoteId:loaded.entities.has('paper-original'),ashOrigin:loaded.entities.get(ash.id).originId,
  originalSourceIntact:loaded.scene.prose===scene.prose},
 perception:{visibleIds:visible.visibleIds,reportedChangedState:visible.changedFacts,
  previouslyUnseenCausesRevealed:visible.witnessedEvents.length,
  duplicateFactOnNextPoll:secondVisit.changedFacts.length,
  duplicateEventOnNextPoll:secondVisit.witnessedEvents.length}};
const file=process.argv.find(x=>x.startsWith('--output='))?.slice(9)||'prse_observer_offscreen_remnant_reentry_v1.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(file))throw Error('unsafe output name');
writeFileSync(new URL(file,import.meta.url),JSON.stringify(r,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,remnantVisible:visible.visibleIds.includes(ash.id),
 ashCollider:r.simulation.ashColliderCount,
 oldCauseLeakCount:r.perception.previouslyUnseenCausesRevealed,
 originalStorySaved:r.simulation.originalSourceIntact,duplicates:r.perception.duplicateFactOnNextPoll}));
reopened.loop.dispose();loaded.dispose();w.dispose();
