import assert from "node:assert/strict";
// Evidence-based PRSE narration comparison. A real Rapier partition occludes a
// real Rapier object and blocks event delivery. An observer on the open side
// can see a near-instant impulse; an observer behind the partition only gets
// verified changed facts when returning. Separate persisted observer journal
// prevents leaked historic causes or repeated visible events.
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEPhysicalObserver} from './prse_physical_observer.mjs';

await initializePhysics();
const scene={id:'physical-occluded-ceramics',
 prose:'Behind a solid stone partition is a movable pottery object.',
 entities:[
  object('stone-partition','partition',{x:-25,y:1.3,z:9},{x:.2,y:2.6,z:3},
   {body:'fixed',material:'stone'}),
  object('pottery-occluded','pot',{x:-24,y:.22,z:9},{x:.45,y:.44,z:.44},
   {body:'dynamic',material:'ceramic',mass:.75})
 ]};
const game=new PRSELoop(scene);
game.tick(25);
const observer=new PRSEPhysicalObserver(game,{visibilityRadius:5});
const hiddenEye={x:-26,y:1.5,z:9};
const seenEye={x:-23,y:1.5,z:9};
const initialHidden=observer.observe('left-player',hiddenEye,{radius:5});
const initialVisible=observer.observe('right-player',seenEye,{radius:5});
if(initialHidden.visibleIds.includes('pottery-occluded'))throw Error('Wall did not occlude pottery');
if(!initialVisible.visibleIds.includes('pottery-occluded'))throw Error('Open side cannot see pottery');
const old=game.scene.entities.find(e=>e.id==='pottery-occluded').position;
if(!game.applyImpulse('pottery-occluded',{x:0,y:.4,z:2.6}))throw Error('Actual physics impulse rejected');
game.tick(1);
const tickWitnessed=observer.captureFrame('right-player',seenEye,{radius:5});
const tickHidden=observer.captureFrame('left-player',hiddenEye,{radius:5});
assert(tickWitnessed.queuedWitnessEvents===1&&tickHidden.queuedWitnessEvents===0);
const witness=observer.observe('right-player',seenEye,{radius:5});
const hidden=observer.observe('left-player',hiddenEye,{radius:5});
if(!witness.witnessedEvents.some(e=>e.text.includes('impulse')))throw Error('Visible player missed immediate physical event');
if(hidden.witnessedEvents.length!==0)throw Error('Occluded player learned invisible physics cause');
game.tick(44);
const hiddenWait=observer.observe('left-player',hiddenEye,{radius:5});
if(hiddenWait.witnessedEvents.length!==0)throw Error('Historical occluded cause was leaked');
const before=game.snapshot(),journal=observer.snapshot();
const reopened=PRSELoop.restore(JSON.parse(JSON.stringify(before)));
if(!reopened.ok)throw Error('GameCore scene snapshot rejected');
const g2=reopened.loop;
const watcher=PRSEPhysicalObserver.restore(g2,JSON.parse(JSON.stringify(journal)));
const playerMovesAroundWall=watcher.observe('left-player',seenEye,{radius:5});
if(!playerMovesAroundWall.visibleIds.includes('pottery-occluded'))throw Error('Returned player cannot see physically present pottery');
if(playerMovesAroundWall.witnessedEvents.length!==0)throw Error('Unseen historic impulse retroactively narrated');
if(!playerMovesAroundWall.changedFacts.some(f=>f.id==='pottery-occluded'))throw Error('Changed physical object not described on reentry');
const sameNext=watcher.observe('left-player',seenEye,{radius:5});
if(sameNext.changedFacts.length||sameNext.witnessedEvents.length)throw Error('Repeated same facts or events after save');
const rightNext=watcher.observe('right-player',seenEye,{radius:5});
if(rightNext.witnessedEvents.length)throw Error('Already witnessed event repeated on restore');
const falsified=JSON.parse(JSON.stringify(watcher.snapshot()));
falsified.observers[0].processed.push(123456789);
let tamperRejected=false;
try{PRSEPhysicalObserver.restore(g2,falsified);}catch{tamperRejected=true;}
if(!tamperRejected)throw Error('Tampered delivered-event list accepted');
const output={
 metadata:{source:'Actual GameCore/Rapier physics partition and movable pottery; controlled observer viewpoints, no human playtest',
 limits:'Rays sample seven approximate shape points; no sound, lighting, FOV/camera actual player dynamics; current scene text remains deterministic'},
 before:{hidden:initialHidden.visibleIds,openSide:initialVisible.visibleIds},
 physicalEvent:{type:game.events.find(e=>e.type==='external_impulse')?.type,
  actualSourceAction:{x:0,y:.4,z:2.6},beginningPosition:old,
  finalPosition:game.entities.get('pottery-occluded').position},
 witnessed:{nearbyRightEvents:witness.witnessedEvents,
  hiddenLeftEvents:hidden.witnessedEvents,hiddenEvenAfterDelay:hiddenWait.witnessedEvents},
 savedReentry:{sourceUnchanged:g2.scene.prose===scene.prose,
  nowVisible:playerMovesAroundWall.visibleIds.includes('pottery-occluded'),
  formerUnseenCauseNotNarrated:playerMovesAroundWall.witnessedEvents.length===0,
  currentFactShown:playerMovesAroundWall.changedFacts.some(f=>f.id==='pottery-occluded'),
  duplicateOutput:sameNext.changedFacts.length+sameNext.witnessedEvents.length,
  previouslySeenEventNotRepeated:rightNext.witnessedEvents.length===0,
  tamperedObserverSequenceRejected:tamperRejected},
 observerMetadata:watcher.snapshot()
};
const outputName=process.argv.find(s=>s.startsWith('--output='))?.slice(9)||'prse_observer_perceptual_event_reentry_v1.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(outputName))throw Error('Unsafe observer study output');
writeFileSync(new URL(outputName,import.meta.url),JSON.stringify(output,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({
 verified:true,
 initialWrongDistanceVisible:game.visibleIds(hiddenEye,5).includes('pottery-occluded'),
 actualRayOccluded:!initialHidden.visibleIds.includes('pottery-occluded'),
 witnessedLiveEvent:witness.witnessedEvents.length,
 occludedEventLeakCount:hidden.witnessedEvents.length,
 reentryFactShown:playerMovesAroundWall.changedFacts.length,
 oldCauseSuppressed:playerMovesAroundWall.witnessedEvents.length===0,
 noRepetition:sameNext.changedFacts.length===0&&sameNext.witnessedEvents.length===0
}));
g2.dispose();game.dispose();
