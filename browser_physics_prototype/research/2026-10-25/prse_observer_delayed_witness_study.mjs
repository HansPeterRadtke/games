// Independent before/after event-time witness study: valid camera-side observer
// must receive a genuine physics event despite one-second text UI delay; an
// observer behind a real Rapier wall never receives that cause.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEPhysicalObserver} from './prse_physical_observer.mjs';
await initializePhysics();
const scene={id:'timed-event-occluded-vase',
 prose:'A solid stone partition hides a ceramic vessel from someone on the opposite side.',
 entities:[
  object('partition','wall',{x:-25,y:1.3,z:9},{x:.2,y:2.6,z:3},{material:'stone',body:'fixed'}),
  object('vase','vase',{x:-24,y:.22,z:9},{x:.45,y:.44,z:.44},{material:'ceramic',mass:.9})
 ]};
const w=new PRSELoop(scene);w.tick(25);
const hiddenEye={x:-26,y:1.5,z:9},openEye={x:-23,y:1.5,z:9},radius=5;
const pollOnly=new PRSEPhysicalObserver(w,{visibilityRadius:radius});
const captured=new PRSEPhysicalObserver(w,{visibilityRadius:radius});
for(const observer of [pollOnly,captured]){
 assert(!observer.observe('hidden-user',hiddenEye,{radius}).visibleIds.includes('vase'));
 assert(observer.observe('open-user',openEye,{radius}).visibleIds.includes('vase'));
}
assert(w.applyImpulse('vase',{x:0,y:.4,z:2.6}));
w.tick(1);
const rightCaptured=captured.captureFrame('open-user',openEye,{radius});
const leftCaptured=captured.captureFrame('hidden-user',hiddenEye,{radius});
assert(rightCaptured.queuedWitnessEvents===1);
assert(leftCaptured.queuedWitnessEvents===0);
w.tick(65);
const lateWithoutCapture=pollOnly.observe('open-user',openEye,{radius});
assert(lateWithoutCapture.witnessedEvents.length===0,
 'Original one-second UI polling unexpectedly preserved fast physical event');
const beforeObserverPersistence=captured.snapshot();
assert(beforeObserverPersistence.schema===2&&beforeObserverPersistence.observers.length===2);
const originalSave=JSON.parse(JSON.stringify(w.snapshot()));
const loaded=PRSELoop.restore(originalSave);assert(loaded.ok);
const newW=loaded.loop,restored=PRSEPhysicalObserver.restore(newW,
 JSON.parse(JSON.stringify(beforeObserverPersistence)));
const rightLater=restored.observe('open-user',openEye,{radius});
assert(rightLater.witnessedEvents.length===1&&rightLater.witnessedEvents[0].capturedAtEventTime);
assert(rightLater.witnessedEvents[0].text.includes('impulse'));
const repeated=restored.observe('open-user',openEye,{radius});
assert(repeated.witnessedEvents.length===0&&repeated.changedFacts.length===0);
const hiddenLater=restored.observe('hidden-user',hiddenEye,{radius});
assert(hiddenLater.witnessedEvents.length===0);
const revealLater=restored.observe('hidden-user',openEye,{radius});
assert(revealLater.visibleIds.includes('vase'));
assert(revealLater.witnessedEvents.length===0,
 'The hidden observer gained unjustified knowledge of an earlier unseen action');
assert(revealLater.changedFacts.some(f=>f.id==='vase'),'Current state did not become discoverable');
const corrupted=restored.snapshot();
corrupted.observers[0].queuedEvents.push(999999);
let tamperRejected=false;
try{PRSEPhysicalObserver.restore(newW,corrupted);}catch{tamperRejected=true;}
assert(tamperRejected);
const result={
 metadata:{scope:'Authoritative GameCore/Rapier physics and event-time raycast against a solid physical partition',
  input:'Two investigator-defined observer positions, one genuine GameCore impulse, and an intentional 1.08-second UI polling gap',
  nonHuman:true,noLLM:true,
  limits:'CaptureFrame must be invoked at the simulation tick; it has not been integrated into the production UI dispatcher'},
 comparison:{
  withoutTickCaptureWitnessedEvents:lateWithoutCapture.witnessedEvents.length,
  recordedTickImmediateWitnesses:rightCaptured.queuedWitnessEvents,
  hiddenTickWitnesses:leftCaptured.queuedWitnessEvents,
  savedAndDelayedDelivered:rightLater.witnessedEvents.length,
  deliveredOriginalEventSequence:rightLater.witnessedEvents[0].sequence,
  deliveredOnlyOnce:repeated.witnessedEvents.length===0,
  hiddenObserverNoRetroactiveCause:revealLater.witnessedEvents.length===0,
  currentVisibleStateDescribed:revealLater.changedFacts.some(f=>f.id==='vase'),
  tamperedSavedQueueRejected:tamperRejected,
  authoritativeWorldTime:newW.time},
 savedState:{observerSnapshotSchema:beforeObserverPersistence.schema,
  observerCount:beforeObserverPersistence.observers.length,
  persistedQueuedWitnesses:beforeObserverPersistence.observers.flatMap(e=>e.queuedEvents).length},
 recordedEvent:{sequence:w.events.find(e=>e.type==='external_impulse').sequence,
  origin:w.events.find(e=>e.type==='external_impulse').origin,
  worldObjectId:'vase'}};
const output=process.argv.find(x=>x.startsWith('--output='))?.slice(9)||'prse_observer_delayed_witness_v2.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(output))throw Error('Invalid output filename');
writeFileSync(new URL(output,import.meta.url),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result.comparison));
newW.dispose();w.dispose();
