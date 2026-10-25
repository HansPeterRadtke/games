// A meaning-preserving PRSE temporal semantic-world document is NOT a flat
// reprint of a historical literary paragraph or the latest single event.
//
// Validate full current document semantics across actual native GameCore 3D
// forces, saved native contact physics, elapsed world time with unchanged facts,
// unloading, explicitly authored offscreen fire, actual ash rematerialization,
// observer causal privacy, and a second saved reentry. Preserve real negative
// findings from the separate SceneEval corpus; this authored offscreen fire
// case is NOT a human-participant scientific benchmark.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import{writeFileSync}from'node:fs';
import{initializePhysics}from'../../physics-core.js';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{PRSELoop,object}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
import{PRSECurrentSemanticDocument}from'./prse_current_semantic_document.mjs';
await initializePhysics();
const docHash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const results={metadata:{
 purpose:'Actual authoritative GameCore/Rapier → current textual world state → offscreen semantic causality → saved reentry',
 caveat:'Selected external row22 and separately authored offscreen note example; no human LLM literary-quality or random novel world test'},
 externalSource:{},authoredOffscreen:{},tampering:{}};
{
 const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[22];
 let a=new PRSELoop(repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150}).scene);
 a.tick(40);
 let world=new PRSECurrentSemanticDocument(new PRSESourceRevision(a,p.relations,{observerRadius:9}));
 const initial=world.record();
 assert(initial.changed);
 assert(initial.current.text.includes('lamp 1 rests on nightstand 1.'));
 assert(initial.current.scope==='omniscient_verified_world_state_not_player_knowledge');
 assert(initial.current.historicalSourceNotCurrentText);
 let count=world.log.length;
 a.tick(15);
 const unchanged=world.record();
 assert(!unchanged.changed && world.log.length===count,
  'World clock passage alone fabricated semantic story change');
 const clean=PRSECurrentSemanticDocument.restore(JSON.parse(JSON.stringify(world.snapshot())));
 assert(clean.ok,'Unchanged semantic facts fail saved time continuation: '+clean.reason);
 assert(clean.document.current().text===world.current().text);
 clean.document.dispose();
 const lamp=a.scene.entities.find(e=>e.kind==='lamp'&&e.body==='dynamic');
 assert(lamp);
 assert(a.applyImpulse(lamp.id,{x:6,y:1,z:0}));
 a.tick(115);
 const moved=world.record();
 assert(moved.changed,'Actual physical support loss not reflected in narrative');
 assert(!moved.current.text.includes('lamp 1 rests on nightstand 1.'));
 assert(moved.current.verifiedRelations.some(x=>x.type==='on'&&x.truth==='false'));
 const saved=JSON.parse(JSON.stringify(world.snapshot()));
 const restored=PRSECurrentSemanticDocument.restore(saved);
 assert(restored.ok,'Native world/source transaction inconsistent: '+restored.reason);
 const b=restored.document;
 assert(b.current().text===world.current().text);
 assert(b.log.length===world.log.length);
 assert(b.current().historicalSourceNotCurrentText);
 assert(b.story.sourceArchive().originalText===p.text);
 assert(!b.current().text.toLowerCase().includes('impulse'),
  'Current world present description incorrectly invented an unobserved cause');
 const falseNow=b.current().verifiedRelations.filter(x=>x.truth==='false').length;
 results.externalSource={
  source:'SceneEval original human-authored row22; specifically selected non-blind cause continuity example',
  sourceImmutable:b.story.sourceArchive().originalText===p.text,
  initialVerifiedSupport:initial.current.verifiedRelations.filter(x=>x.type==='on'&&x.truth==='true').length,
  unchangedWorldTimeDidNotRewriteNarrative:true,
  afterRealPhysicsSupportFalse:falseNow>=1,
  noPreviouslyFalseSourceRelationPrintedAsCurrentSupport:!b.current().text.includes('lamp 1 rests on nightstand 1.'),
  nativeContactSolverAndSemanticDocumentSaved:true,
  revisionHistoryRetained:b.log.length===world.log.length,
  exactCurrentDocumentRegeneratedAfterRestore:b.current().text===world.current().text,
  noInventedCauseInPresentWorldDocument:!b.current().text.toLowerCase().includes('impulse')};
 b.dispose();world.dispose();
}
{
 const scene={id:'semantic-paper-world-timeline',
  prose:'An old warning note rests upon a desk. The traveler has left the room.',
  entities:[
   object('wooden-desk','desk',{x:-25,y:.45,z:9},{x:2,y:.9,z:1.2},
    {body:'fixed',material:'wood'}),
   object('paper-note','note',{x:-25,y:.91,z:9},{x:.25,y:.02,z:.2},
    {body:'dynamic',material:'paper',mass:.04,supportId:'wooden-desk'})
  ]};
 const predicates=[{kind:'object',type:'on',a:'note',b:'desk',sourceText:'An old warning note rests upon a desk.'}];
 let a=new PRSELoop(scene);a.tick(75);
 let current=new PRSECurrentSemanticDocument(new PRSESourceRevision(a,predicates,{observerRadius:8}));
 const started=current.record();
 assert(started.current.physicallyMaterializedCount===2);
 const observerNear={x:-23.6,y:1.45,z:9.15},far={x:0,y:1.5,z:0};
 const seen=current.story.read('player-reader',observerNear,{radius:8});
 assert(seen.visibleEntityIDs.includes('paper-note'));
 current.story.read('player-reader',far,{radius:8});
 const initially=a.scene.prose;
 const physicallyUnloaded=a.dematerialize();
 assert(physicallyUnloaded===2);
 const latent=current.record();
 assert(latent.changed);
 assert(latent.current.unloadedCount===2&&latent.current.physicallyMaterializedCount===0);
 assert(latent.current.text.includes('not being simulated'));
 assert(!latent.current.text.includes('rests on wooden desk'),
  'Unloaded semantic record masquerades as current physics contact');
 assert(a.igniteOffscreen('paper-note'));
 a.advanceOffscreen(12);
 const changed=current.record();
 assert(changed.changed);
 const ash=[...a.entities.values()].find(e=>e.originId==='paper-note');
 assert(ash && a.entities.get('paper-note').state.destroyed);
 assert(changed.current.historicalDestroyedCount===1);
 assert(changed.current.unloadedCount===2);
 assert(changed.current.text.includes('was destroyed'));
 assert(!changed.current.text.toLowerCase().includes('caught fire'));
 const offscreenJournal=JSON.parse(JSON.stringify(current.snapshot()));
 const fromSave=PRSECurrentSemanticDocument.restore(offscreenJournal);
 assert(fromSave.ok,'Unloaded literary/native physics state cannot restore: '+fromSave.reason);
 const restored=fromSave.document,b=restored.story.loop;
 assert(b.active.size===0);
 assert(b.scene.prose===initially);
 assert(restored.current().text===changed.current.text);
 const activation=b.materialize();
 assert(activation===2);
 assert(!b.active.has('paper-note')&&b.active.has(ash.id));
 assert(b.active.get(ash.id).numColliders()>=1);
 const after=restored.record();
 assert(after.changed);
 assert(after.current.text.toLowerCase().includes('ash from'));
 assert(!after.current.text.includes('not being simulated')||
  after.current.unloadedCount===0);
 const playerText=restored.story.read('player-reader',observerNear,{radius:8});
 assert(playerText.currentSentences.some(x=>x.toLowerCase().includes('ash')));
 assert(playerText.witnessedEvents.length===0);
 assert(restored.story.read('player-reader',observerNear,{radius:8}).currentSentences.length===0);
 const savedAgain=JSON.parse(JSON.stringify(restored.snapshot()));
 const another=PRSECurrentSemanticDocument.restore(savedAgain);
 assert(another.ok);
 assert(another.document.current().text===restored.current().text);
 assert(another.document.story.read('player-reader',observerNear,{radius:8}).text==='');
 assert(Math.abs(another.loop.time-b.time)<1e-6);
 results.authoredOffscreen={
  originallyMaterialized:2,
  qualifiedTextWhileUnloaded:true,
  absentPhysicalStateNotClaimedAsCurrentlySimulated:true,
  originalTextNeverOverwritten:b.scene.prose===initially,
  semanticOffscreenDurationSeconds:12,
  destroyedOriginalIDPreserved:b.entities.has('paper-note'),
  distinctNativeAshColliderRematerialized:true,
  currentSemanticTextMentionsPresentAsh:after.current.text.toLowerCase().includes('ash from'),
  witnessedIgnitionLeakCount:playerText.witnessedEvents.length,
  repeatAfterSecondSave:another.document.story.read('player-reader',observerNear,{radius:8}).text.length,
  nativeAndSemanticTimeMatch:Math.abs(another.loop.time-another.loop.game.time)<1e-6,
  revisions:restored.log.length
 };
 const badClaim=JSON.parse(JSON.stringify(savedAgain));
 badClaim.ledger.expectedCurrentClaimSignature='f'.repeat(64);
 badClaim.ledgerSHA256=docHash(badClaim.ledger);
 const rejected=PRSECurrentSemanticDocument.restore(badClaim);
 assert(!rejected.ok,'Forged current world claims accepted after recomputed unsigned hash');
 const future=JSON.parse(JSON.stringify(savedAgain));
 future.ledger.history[0].worldTime=future.ledger.clock+4;
 future.ledgerSHA256=docHash(future.ledger);
 const futureRejected=PRSECurrentSemanticDocument.restore(future);
 assert(!futureRejected.ok,'Future-timed source event accepted');
 results.tampering={inconsistentClaimsRejected:true,futureDatedRevisionRejected:true,
  caveat:'Owner-trusted SHA integrity only, not signed adversarial save authentication'};
 another.document.dispose();restored.dispose();current.dispose();
}
writeFileSync(new URL('prse_current_semantic_temporal_reentry_v1.json',import.meta.url),
 JSON.stringify(results,null,2)+'\n',{flag:'wx'});
console.log('VERIFIED',JSON.stringify({externallyWrittenSource:results.externalSource,
 offscreenAuthored:results.authoredOffscreen,tampering:results.tampering}));
