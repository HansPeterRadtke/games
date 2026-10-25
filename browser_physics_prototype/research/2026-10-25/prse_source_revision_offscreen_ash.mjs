// Original owner's PRSE offscreen-paper/fire example through the SAME
// authoritative world plus observer-specific semantic source revision and
// trusted native whole-GameCore/physics transaction.
//
// A source-linked real ash remnant is materialized after an explicitly
// authored offscreen process. The visitor sees the present remnant after
// re-entry, not the unwitnessed ignition cause; the original prose is archived.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSESourceRevision} from './prse_source_revision_story.mjs';
await initializePhysics();
const scene={
 id:'original-prse-paper-revision',
 prose:'An old written warning rests on a wooden desk. The room is quiet while its visitor is away.',
 entities:[
  object('old-wooden-desk','desk',{x:-25,y:.45,z:9},{x:2,y:.9,z:1.2},
   {body:'fixed',material:'wood',description:'A wooden desk'}),
  object('paper-original','note',{x:-25,y:.91,z:9},{x:.25,y:.02,z:.2},
   {body:'dynamic',material:'paper',mass:.04,
    name:'old warning paper',supportId:'old-wooden-desk'})
 ]};
const relations=[{kind:'object',type:'on',a:'note',b:'desk',
 sourceText:'An old written warning rests on a wooden desk.'}];
const a=new PRSELoop(scene);a.tick(70);
let story=new PRSESourceRevision(a,relations,{observerRadius:8});
const remote={x:0,y:1.4,z:0};
const near={x:-23.6,y:1.45,z:9.15};
const first=story.read('traveler-one',near,{radius:8});
const known=first.visibleEntityIDs;
assert(known.includes('paper-original')&&known.includes('old-wooden-desk'));
const away=story.read('traveler-one',remote,{radius:8});
assert(!away.text);
const retired=story.loop.dematerialize();
assert(retired===2);
assert(story.loop.igniteOffscreen('paper-original'));
story.loop.advanceOffscreen(12);
const ash=[...story.loop.entities.values()].find(e=>e.originId==='paper-original');
assert(ash);
const original=story.sourceArchive();
assert.equal(original.originalText,scene.prose);
assert(!story.loop.active.size);
const afterBurn=story.read('traveler-one',remote,{radius:8});
assert.equal(afterBurn.text,'');
const save=JSON.parse(JSON.stringify(story.snapshot()));
const restored=PRSESourceRevision.restore(save);
assert(restored.ok,restored.reason||'Native transaction failed');
const b=restored.story;
assert(!b.loop.active.size);
assert.equal(b.loop.scene.prose,scene.prose);
assert.equal(b.loop.time,a.time);
const materialized=b.loop.materialize();
assert.equal(materialized,2);
assert(b.loop.active.has(ash.id)&&!b.loop.active.has('paper-original'));
assert(b.loop.active.get(ash.id).numColliders()===1);
const returnVisit=b.read('traveler-one',near,{radius:8});
assert(returnVisit.visibleEntityIDs.includes(ash.id));
assert(returnVisit.currentSentences.some(s=>s.toLowerCase().includes('ash')));
assert(!returnVisit.witnessedEvents.length);
assert(!returnVisit.text.toLowerCase().includes('ignite'));
const again=b.read('traveler-one',near,{radius:8});
assert.equal(again.text,'');
const secondSave=b.snapshot();
const another=PRSESourceRevision.restore(JSON.parse(JSON.stringify(secondSave)));
assert(another.ok);
const afterSecond=another.story.read('traveler-one',near,{radius:8});
assert.equal(afterSecond.text,'');
const outcome={
 metadata:{
  source:'Original recorded PRSE story-world/offscreen-fire hypothesis (author-described, not SceneEval)',
  physicalAuthority:'Actual GameCore/Rapier original note, wooden desk, separate ash remnant collider',
  semanticCause:'An explicitly authored offscreen paper-burning process, NOT physical combustion chemistry',
  scope:'One constructed source-preserving scenario, not a general-world or literary-language benchmark'},
 earlier:{originalLiteraryArchiveUnchanged:original.originalText===scene.prose,
  physicallyRepresentedPaperAndDesk:retired,
  initialSourceRelation:first.relationRevisions.map(x=>x.text),
  observerGenuinelyMovedOutOfSensingRange:away.visibleEntityIDs.length===0},
 unloaded:{
  worldClockSeconds:b.loop.time,
  physicalBodiesDuringOffscreen:0,
  stableNoteSemanticTombstone:b.loop.entities.has('paper-original'),
  physicallyDistinctAshId:ash.id,
  ashLineageId:b.loop.entities.get(ash.id).originId,
  noPreviousIgnitionRevealed:!afterBurn.text},
 afterReturn:{
  rematerializedPhysicalBodies:materialized,
  ashHasRealCollider:b.loop.active.get(ash.id).numColliders()===1,
  ashSeen: returnVisit.visibleEntityIDs.includes(ash.id),
  currentSourceLinkedText:returnVisit.text,
  unwitnessedIgnitionNotClaimed:returnVisit.witnessedEvents.length===0,
  duplicateContentAfterRead:again.text.length,
  duplicateContentAfterSecondSave:afterSecond.text.length,
  originalSourceDocumentUnchanged:b.sourceArchive().originalText===scene.prose}};
writeFileSync(new URL('prse_story_revision_offscreen_ash_reentry_v1.json',import.meta.url),
 JSON.stringify(outcome,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({pass:true,sourceTextPreserved:true,
 actualAshCollider:outcome.afterReturn.ashHasRealCollider,
 text:outcome.afterReturn.currentSourceLinkedText,
 unwitnessedCauseLeaks:0,duplicateOutputs:0,
 sameHistoricalIdentity:outcome.unloaded.stableNoteSemanticTombstone}));
another.story.dispose();b.dispose();story.dispose();
