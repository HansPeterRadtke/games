// Transactional truth consistency and mutation/cross-snapshot refusal tests.
// Real source-derived SceneEval 3D world, real Rapier impulse, observer-visible
// event at the exact emission instant, single trusted native world transaction.
//
// All failure scenarios are intentionally mutated COPIES of one saved research
// state; the live game and original source fixtures are never touched.
import assert from'node:assert/strict';
import{createHash}from'node:crypto';
import{writeFileSync}from'node:fs';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';

await initializePhysics();
const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[22];
const scenario=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
assert(scenario.accepted);
const loop=new PRSELoop(scenario.scene);
loop.tick(34);
let story=new PRSESourceRevision(loop,p.relations,{observerRadius:9});
const lamp=loop.scene.entities.find(e=>e.kind==='lamp'),stand=loop.scene.entities.find(e=>e.kind==='nightstand');
const eye={x:lamp.position.x+1.6,y:1.5,z:lamp.position.z+.4};
assert(story.perception.isVisible(lamp.id,eye,{radius:9}).visible);
const first=story.read('visible-person',eye);
assert(first.currentSentences.some(x=>x.includes('rests on nightstand')));
const afar={x:0,y:1.5,z:0};
story.read('remote-person',afar);
const detached=story.attachObserver('visible-person',()=>eye,{radius:9});
story.attachObserver('remote-person',()=>afar,{radius:9});
assert(loop.applyImpulse(lamp.id,{x:3,y:.7,z:.4}));
loop.tick(20);
const witnessed=story.read('visible-person',eye);
assert(witnessed.witnessedEvents.some(e=>e.text.includes('impulse')));
assert(!story.read('remote-person',afar).witnessedEvents.length);
detached();
const unmodified=JSON.parse(JSON.stringify(story.snapshot()));
const good=PRSESourceRevision.restore(unmodified);
assert(good.ok,'Trustworthy transaction could not restore');
assert(!good.story.read('visible-person',eye).witnessedEvents.length);
good.story.dispose();

const digest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const copy=()=>JSON.parse(JSON.stringify(unmodified));
const variants=[
 {name:'original_literary_prose_modified',change:s=>s.semanticBundle.originalSourceDocument+=' An invented disaster.'},
 {name:'source_relation_invalidation',change:s=>s.semanticBundle.sourceRelations[0].a='fake-entity'},
 {name:'incoherent_world_timestamp',change:s=>s.semanticBundle.worldClock+=7},
 {name:'missing_physical_source_entity',change:s=>s.physical.structured.scene.entities.pop()},
 {name:'broken_native_rapier_binary',change:s=>s.physical.nativeBase64='QUJD'},
 {name:'wrong_native_build',change:s=>s.physical.rapierVendoredSha256='f'.repeat(64)},
 {name:'historical_event_forgery',change:s=>s.semanticBundle.revisions.push({
  type:'witnessed_physical_event',observer:'visible-person',eventSequence:999999,
  source:'authoritative_gamecore_event_at_observation_time',worldTime:loop.time,text:'An invented impact.'
 })},
 {name:'narrative_future_timestamp',change:s=>{if(s.semanticBundle.revisions.length)s.semanticBundle.revisions[0].worldTime=loop.time+100;}},
 {name:'unlinked_observer_identity',change:s=>s.semanticBundle.lastReadTime.push(['invalid-identity',loop.time+40])}
];
const rejected=[];
for(const c of variants){
 const object=copy();c.change(object);
 const r=PRSESourceRevision.restore(object);
 assert(!r.ok,'Altered and mismatched serialized evidence must be rejected: '+c.name);
 rejected.push({name:c.name,reason:r.reason});
}
// A checksummed same-origin narrative corruption is still structurally invalid
// when it cites a never-existing authoritative event ID.
const rehash=copy();
rehash.semanticBundle.revisions.push({
 type:'witnessed_physical_event',observer:'visible-person',eventSequence:123456,
 source:'authoritative_gamecore_event_at_observation_time',worldTime:loop.time,
 text:'An invented physical event.'});
rehash.semanticBundleSHA256=digest(rehash.semanticBundle);
const liar=PRSESourceRevision.restore(rehash);
assert(!liar.ok);
rejected.push({name:'rehashed_authoritative_event_forgery',reason:liar.reason});
// A technically valid rehashed mutually coordinated lie would require an
// external trust/authentication boundary; this study does not claim that.
const savedAndReplayed=PRSESourceRevision.restore(unmodified);
assert(savedAndReplayed.ok);
const originalEvents=story.loop.events.map(x=>x.sequence);
assert.deepEqual(savedAndReplayed.loop.events.map(x=>x.sequence),originalEvents);
const action={x:-1.4,y:.4,z:1.1};
assert(loop.applyImpulse(lamp.id,action));
assert(savedAndReplayed.loop.applyImpulse(lamp.id,action));
loop.tick(90);savedAndReplayed.loop.tick(90);
const a=loop.active.get(lamp.id).translation();
const b=savedAndReplayed.loop.active.get(lamp.id).translation();
const diff=Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
assert(diff<.02);
assert(Math.abs(loop.time-savedAndReplayed.loop.time)<1e-5);
const data={metadata:{
 source:'Original SceneEval human-authored row 22, no training labels read',
 actualWorld:'One PRSE GameCore/Rapier authoritative scene and events',
 integrity:'Trusted saved world: joint native physics, historical prose, observer facts and witnessed-event IDs',
 limitation:'Checksums are for accidental/mixed corruption and inconsistent references, not maliciously authored fully consistent signed saves'},
 test:{
  nativeSaveAccepted:true,initialPhysicallyWitnessedEvent:witnessed.witnessedEvents.length,
  remoteWitnesses:0,
  postSaveEventIDsStable:originalEvents.length,
  noRepeatedVisibleImpulses:true,
  unsafeMutationsRejected:rejected.length,
  rejected,
  nextRealPhysicalActionReentryPositionDifferenceMeters:diff,
  currentClockEquivalent:true,
  sourceLiteraryArchiveUnchanged:story.sourceArchive().originalText===p.text}};
writeFileSync(new URL('prse_source_revision_atomic_integrity_v1.json',import.meta.url),
 JSON.stringify(data,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,mutationCasesRejected:rejected.length,
 nextActionPositionDifferenceMeters:diff,
 preservedEventIDs:originalEvents.length,noRemoteLeaks:true}));
savedAndReplayed.story.dispose();story.dispose();
