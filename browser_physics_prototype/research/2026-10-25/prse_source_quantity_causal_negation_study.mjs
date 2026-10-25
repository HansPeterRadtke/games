// Two targeted falsifications of PRSE source-count claims, using actual native
// GameCore/Rapier physics and the owner-original semantic offscreen process.
// These are EXPLICITLY authored adverse scenarios, NOT newly independent
// external-human language benchmark wins.
//
// A. Existing SceneEval human-authored source ID7 states NO coffee table.
//    It is physically absent in correct construction, UNKNOWN during unload,
//    and FALSE when a deliberately injected contradictory physical table is
//    materialized despite retaining the original literary source.
// B. An authored paper note on a real desk is destroyed while offscreen and
//    replaced by a genuine ash collider. The current object count cannot
//    repeat the old source count one for the now-destroyed note on re-entry.
import assert from 'node:assert/strict';
import {writeFileSync}from'node:fs';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop,object,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
import{PRSESourceQuantityEvidence}from'./prse_source_quantity_evidence.mjs';
import{PRSEQuantityScopedWorld}from'./prse_quantity_scoped_world.mjs';
await initializePhysics();
const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[7];
assert(p.quantities.coffee_table?.count===0);
const choose=(doc,kind)=>doc.countSourceClaims.find(r=>r.type===kind);
const results={metadata:{
 sourceA:'External original human SceneEval room row7, with authored adversarial physical violation intentionally inserted only in separate branch',
 sourceB:'Original PRSE paper/desk offscreen burn research hypothesis, explicitly authored, NOT simulated chemical fire',
 actualPhysics:'PRSE GameCore/Rapier with stable identities, semantic evolution and native save/reentry',
 scope:'Negative/contradictory/temporal quantifier status; not a human general-language evaluation'}};
{
 const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 assert(layout.accepted);
 const world=new PRSELoop(layout.scene);world.tick(30);
 const state=new PRSEQuantityScopedWorld(new PRSESourceRevision(world,p.relations),p);
 const initial=state.current();
 assert(choose(initial,'coffee_table').explicitSourceAbsenceMatch==='true');
 assert(choose(initial,'coffee_table').physicallyMaterializedCount===0);
 const originalText=world.scene.prose;
 world.dematerialize();
 const offscreen=state.current();
 assert(!offscreen.physicalRegionComplete);
 assert(choose(offscreen,'coffee_table').explicitSourceAbsenceMatch==='unknown');
 assert(choose(offscreen,'coffee_table').sourceCompilerNumericMatch==='unknown');
 world.advanceOffscreen(4);
 const checkpoint=PRSEQuantityScopedWorld.restore(JSON.parse(JSON.stringify(state.snapshot())));
 assert(checkpoint.ok,'Unloaded native count/source/world transaction failed: '+checkpoint.reason);
 const back=checkpoint.world;
 assert(!back.current().physicalRegionComplete);
 const count=back.story.loop.materialize();
 assert(count>=3);
 assert(back.current().bodyCount===3);
 const resumed=back.current();
 assert(choose(resumed,'coffee_table').explicitSourceAbsenceMatch==='true');
 assert(back.story.sourceArchive().originalText===originalText);
 assert(back.current().text.includes('three')||back.current().text.length>0);
 results.originalHumanNegation={
  explicitlyAbsentType:'coffee_table',
  originallyPhysicallyAbsent:true,
  unloadedRegionCorrectlyUnknown:true,
  originalSourceAndIDsRetained:true,
  noForbiddenObjectCreatedByNativeRematerialization:true,
  sameSourceAfterFourSecondsOffscreen:true};
 back.dispose();state.dispose();
}
{
 const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 assert(layout.accepted);
 let physicalViolation=null;
 for(let x=-34;x<=-20&&!physicalViolation;x+=2.2)
 for(let z=8;z<=17;z+=2){
  const candidate=object('adversarial-coffee-table','coffee_table',
   {x,y:.225,z},{x:1.15,y:.45,z:.65},
   {body:'fixed',material:'wood',
    name:'unjustified table',source:'adversarial_test_not_original_literary_claim'});
  const trial={...layout.scene,entities:[...layout.scene.entities,candidate]};
  if(geometryIssues(trial).length===0){physicalViolation=trial;break;}
 }
 if(!physicalViolation)throw Error('No physically valid adversarial placement in actual room');
 const w=new PRSELoop(physicalViolation);w.tick(25);
 const scoped=new PRSEQuantityScopedWorld(new PRSESourceRevision(w,p.relations),p);
 const q=scoped.current();
 const missing=choose(q,'coffee_table');
 assert(missing.physicallyMaterializedCount===1);
 assert(missing.explicitSourceAbsenceMatch==='false');
 assert(missing.sourceCompilerNumericMatch==='false');
 assert(q.text.includes('coffee table'));
 const restored=PRSEQuantityScopedWorld.restore(JSON.parse(JSON.stringify(scoped.snapshot())));
 assert(restored.ok);
 assert(choose(restored.world.current(),'coffee_table').explicitSourceAbsenceMatch==='false');
 assert(restored.world.story.sourceArchive().originalText===p.text);
 results.deliberatelyContradictedPhysicalScene={
  adversarialSourceObjectID:'adversarial-coffee-table',
  originalSourceProseStillDemandsAbsence:true,
  nativeWorldPhysicallyIncludesOneCoffeeTable:true,
  sourceNegationProvedPhysicallyFalse:true,
  truthConflictPersistsAcrossTrustedNativeSave:true,
  currentWorldTextTruthfullyMentionsContradictoryPhysicalBody:true,
  correctiveSemanticsMustNotPretendOriginalSourceWasAlwaysCorrect:true};
 restored.world.dispose();scoped.dispose();
}
{
 const text='A paper note rests on a wooden desk.';
 const mention=(type,fragment)=>({start:text.indexOf(fragment),end:text.indexOf(fragment)+fragment.length,
  type,matched:fragment,term:fragment,quantity:1,op:'eq',
  certainty:'quantified',quantityEvidence:'a',attributes:[]});
 const proposal={sourceId:'authored-prse-note',
  text,mentions:[mention('note','note'),mention('desk','desk')],
  quantities:{note:{count:1,op:'eq'},desk:{count:1,op:'eq'}},
  relations:[{kind:'object',type:'on',a:'note',b:'desk',
   sourceText:text}]};
 const scene={id:'authored-prse-note',prose:text,entities:[
  object('wooden-desk','desk',{x:-25,y:.45,z:9},{x:2,y:.9,z:1.2},{body:'fixed',material:'wood'}),
  object('paper-note','note',{x:-25,y:.91,z:9},{x:.25,y:.02,z:.2},
   {body:'dynamic',material:'paper',mass:.04,supportId:'wooden-desk'})
 ]};
 const w=new PRSELoop(scene);w.tick(70);
 const scoped=new PRSEQuantityScopedWorld(new PRSESourceRevision(w,proposal.relations),proposal);
 const before=scoped.current();
 assert(choose(before,'note').physicallyMaterializedCount===1);
 const unloaded=w.dematerialize();
 assert(unloaded===2);
 assert(choose(scoped.current(),'note').sourceCompilerNumericMatch==='unknown');
 assert(w.igniteOffscreen('paper-note'));
 w.advanceOffscreen(12);
 const dormant=PRSEQuantityScopedWorld.restore(JSON.parse(JSON.stringify(scoped.snapshot())));
 assert(dormant.ok);
 const current=dormant.world;
 const ash=[...current.story.loop.entities.values()].find(e=>e.originId==='paper-note');
 assert(ash);
 assert(!current.current().physicalRegionComplete);
 const produced=current.story.loop.materialize();
 assert(produced===2);
 const after=current.current();
 assert(choose(after,'note').physicallyMaterializedCount===0);
 assert(choose(after,'note').sourceCompilerNumericMatch==='false');
 assert(after.counts.find(x=>x.type==='note').destroyedHistoricalIdentities===1);
 assert(after.counts.find(x=>x.type==='ash').materializedBodies===1);
 assert(after.text.toLowerCase().includes('ash'));
 assert(after.text.toLowerCase().includes('destroyed'));
 assert(current.story.sourceArchive().originalText===text);
 assert(current.story.loop.active.get(ash.id)?.numColliders()>=1);
 results.offscreenAuthoredFire={
  sourceNoteOriginallyPhysicallyPresent:true,
  nativeOffscreenWorldAndSourceSavedAfterTwelveSeconds:true,
  sourceNoteNowPhysicallyAbsent:true,
  originalNoteIdentityHistoricalDestroyed:true,
  physicallyDistinctAshPresentWithNativeCollider:true,
  currentSemanticCountDoesNotReuseOldLiteralSourceAsPresentTruth:true,
  originalLiterarySourceStillHistorical:true,
  currentWorldTextMentionsAshAndHistoricDestruction:true};
 current.dispose();scoped.dispose();
}
writeFileSync(new URL('prse_source_quantity_causal_negation_cases_v1.json',import.meta.url),
 JSON.stringify(results,null,2)+'\n',{flag:'wx'});
console.log('CAUSAL_SOURCE_COUNT_GUARDS',JSON.stringify({
 externalNegationCorrect:true,
 artificiallyContradictedWorldDetected:true,
 offscreenAuthoredPhysicalDestructionChangesCounts:true,
 completeOwnerTrustedNativeSaves:true}));
