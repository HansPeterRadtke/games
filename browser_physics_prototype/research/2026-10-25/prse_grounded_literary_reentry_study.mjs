// A source-derived human-authored SceneEval room with a physically supported
// lamp; verify that a genuine source-linked relation can be expressed, changed
// only by actual Rapier 3D contact/motion, withheld while out of perception,
// and accurately retracted after save, offscreen time and rematerialization.
// This is one selected illustrative case, NOT a representative blind sample.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEPhysicalObserver} from './prse_physical_observer.mjs';
import {PRSEGroundedFacts} from './prse_grounded_relation_narration.mjs';
await initializePhysics();
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[22];
const candidate=repairScene(source,{maxSweeps:2,maxAttemptsPerScene:150});
assert(candidate.accepted);
const w=new PRSELoop(candidate.scene);w.tick(40);
const paper=new PRSEGroundedFacts(w,source.relations);
const witness=new PRSEPhysicalObserver(w,{visibilityRadius:10});
const lamps=w.scene.entities.filter(x=>x.kind==='lamp'),nightstands=w.scene.entities.filter(x=>x.kind==='nightstand');
assert(lamps.length===1&&nightstands.length===1);
const lamp=lamps[0],stand=nightstands[0];
const eyeCandidates=[
 {x:lamp.position.x+1.6,y:1.5,z:lamp.position.z+.4},
 {x:lamp.position.x-1.6,y:1.5,z:lamp.position.z-.4},
 {x:lamp.position.x,y:1.8,z:lamp.position.z+1.8},
 {x:lamp.position.x,y:1.8,z:lamp.position.z-1.8}
];
const eye=eyeCandidates.find(eye=>
 witness.isVisible(lamp.id,eye,{radius:10}).visible&&
 witness.isVisible(stand.id,eye,{radius:10}).visible);
if(!eye)throw Error('No physical line-of-sight to lamp AND support');
const seen=[lamp.id,stand.id];
const initially=paper.observe('reader-one',seen);
assert(initially.changed.some(x=>x.text.includes('rests on nightstand 1')));
assert(!paper.observe('reader-one',seen).changed.length);
const textHistorical=source.text;
const invisible=paper.observe('reader-one',[]);
assert(!invisible.changed.length);
const originalClock=w.time;
assert(w.applyImpulse(lamp.id,{x:6,y:1,z:0}));
w.tick(115);
assert(w.entities.get(lamp.id).supportId===null);
const factualNow=paper.current().find(x=>x.source.type==='on');
assert(factualNow.truth==='false');
assert(!paper.observe('reader-one',[]).changed.length);
const save=JSON.parse(JSON.stringify(w.snapshot()));
const journal=JSON.parse(JSON.stringify(paper.snapshot()));
const fromSave=PRSELoop.restore(save);
assert(fromSave.ok);
const w2=fromSave.loop,paper2=PRSEGroundedFacts.restore(w2,source.relations,journal);
assert(w2.scene.prose===textHistorical);
assert(!paper2.observe('reader-one',[]).changed.length);
const loadedLamp=w2.entities.get(lamp.id);
assert(loadedLamp.supportId===null);
const unloaded=w2.dematerialize();
assert(unloaded>0);
const beforeOffscreen=w2.time;w2.advanceOffscreen(7);
assert(Math.abs(w2.time-beforeOffscreen-7)<1e-6&&w2.time===w2.game.time);
const worldAfter=PRSELoop.restore(JSON.parse(JSON.stringify(w2.snapshot())));
assert(worldAfter.ok);
const w3=worldAfter.loop;
const knowledge=PRSEGroundedFacts.restore(w3,source.relations,JSON.parse(JSON.stringify(paper2.snapshot())));
const rematerialized=w3.materialize();assert(rematerialized>0);
const nativePlayer=w3.game.player.translation();
const observerRay=new PRSEPhysicalObserver(w3,{visibilityRadius:10});
const physicallyVisible=[lamp.id,stand.id].filter(id=>observerRay.isVisible(id,eye,{radius:10}).visible);
assert(physicallyVisible.length===2,'Physical relation was not visible on reentry');
const reported=knowledge.observe('reader-one',physicallyVisible);
const retraction=reported.changed.find(x=>x.kind==='no_longer_verified');
assert(retraction&&retraction.text==='lamp 1 no longer rests on nightstand 1.');
assert(!reported.changed.some(x=>x.text.includes('impulse')||x.text.includes('knocked')));
assert(!knowledge.observe('reader-one',physicallyVisible).changed.length);
const result={
 provenance:{source:'SceneEval-500 original human-authored description ID 22',
  afterEvent:'Source-specific Rapier 3D physical impulse, NOT an authored after-scene',
  status:'Illustrative selected example with genuine source-annotated on-relation; not blind corpus science',
  limitations:'No generated literary style or exact visual material proof, no player-human perceptual test'},
 initial:{
  originalLiteraryInputWasPreserved:w.scene.prose===textHistorical,
  rigidBodyIdentity:lamp.id,supportIdentity:stand.id,
  authenticatedRayVisibility:physicallyVisible,
  verifiedNarration:initially.changed.map(x=>x.text)},
 changed:{
  actualPhysicsEventCount:w.events.filter(x=>x.ids.includes(lamp.id)).length,
  physicallyLostSourceSupport:w.entities.get(lamp.id).supportId===null,
  sourceLiteraryTextStillHistorical:w.scene.prose===textHistorical,
  narratorDidNotRevealHiddenChange:invisible.changed.length===0},
 savedReentry:{
  originalClock,elapsedUnloadedSeconds:7,
  rematerializedBodies:rematerialized,sameEntityIdentity:w3.entities.has(lamp.id),
  currentFact:'no longer on nightstand',
  noInventedCause:!retraction.text.includes('impulse'),
  observableCorrectRetraction:retraction.text,
  noDuplicateNextRead:knowledge.observe('reader-one',physicallyVisible).changed.length===0,
  keptOriginalProse:w3.scene.prose===textHistorical}
};
writeFileSync(new URL('prse_grounded_literary_reentry_source22.json',import.meta.url),
 JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({pass:true,initial:result.initial.verifiedNarration,
 afterReturn:result.savedReentry.observableCorrectRetraction,
 samePhysicalIdentity:result.savedReentry.sameEntityIdentity,
 offscreenClockConsistency:w3.time===w3.game.time,duplicates:result.savedReentry.noDuplicateNextRead}));
w3.dispose();w2.dispose();w.dispose();
