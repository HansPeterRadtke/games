// Genuine semantic-source hypothesis continuity across physical GameCore/Rapier
// contacts, offscreen semantic time, native world/observer/ledger saving and
// truthful return. Fixed SAME previously source-blind selected eight supportable
// external SceneEval physically valid supports and same four fixed action
// vectors. This reuses PRIOR native source samples, not 32 independent scenes.
//
// Unlike earlier all-or-nothing source-role pruning, source evidence remains
// retained even if its grammar PP role is unresolved or its current physical
// truth changes after actual Rapier impulse.
//
// No gold annotations, GPU/LLM, commercial render, live game, or user calendar
// action occurs here. All outputs are exclusive versioned research files.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {PRSEMeaningHypotheses}from'./prse_source_hypothesis_ledger.mjs';
await initializePhysics();
const directory='/data/var/games/prse_semantic_research/runs/2026-10-25-source-hypotheses';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Invalid versioned raw output');
mkdirSync(directory,{recursive:true,mode:0o700});
const old='/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop';
const grammar=JSON.parse(readFileSync(old+'/prse_source_role_on_200_raw_v1.json')).records;
const cases=JSON.parse(readFileSync(old+'/prse_source_blind_support_eligibility_v1.json')).records.filter(x=>x.eligible);
if(cases.length!==8)throw Error('Source subset no longer matches independent prior eligibility');
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const vectors=[
 {x:4,y:1.1,z:.5},{x:-4,y:1.1,z:.5},{x:.5,y:1.1,z:4},{x:1.2,y:.9,z:-3.5}];
const digest=x=>createHash('sha256').update(Buffer.isBuffer(x)?x:JSON.stringify(x)).digest('hex');
function maybeEye(story,a,b){
 const mean={x:(a.position.x+b.position.x)/2,z:(a.position.z+b.position.z)/2};
 for(const d of [1.8,2.5,4])
  for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,-1],[1,-1],[-1,1]]){
   const eye={x:mean.x+dx*d,y:1.6,z:mean.z+dz*d};
   if(story.perception.isVisible(a.id,eye,{radius:12}).visible&&
      story.perception.isVisible(b.id,eye,{radius:12}).visible)return eye;
  }
 return null;
}
const results=[];
for(const chosen of cases){
 const source=proposals[chosen.id];
 const sourceRoles=grammar.filter(x=>x.sourceId===chosen.id);
 const parsedIndex=source.relations.findIndex(r=>r.kind==='object'&&r.type==='on'&&
  r.a===chosen.relA&&r.b===chosen.relB);
 if(parsedIndex<0)throw Error('Previously selected real-world relation no longer recorded in source');
 for(let version=0;version<vectors.length;version++){
  const row={sourceId:chosen.id,child:chosen.relA,support:chosen.relB,
   sourceOrdinal:parsedIndex,physicalImpulse:vectors[version],variant:version+1,
   status:'started'};
  let ledger=null,restored=null;
  try{
   const layout=repairScene(source,{maxSweeps:2,maxAttemptsPerScene:150});
   if(!layout.accepted)throw Error('Frozen selected source layout no longer physically valid');
   const world=new PRSELoop(layout.scene);world.tick(38);
   ledger=new PRSEMeaningHypotheses(world,source,sourceRoles);
   const original=ledger.record().current;
   const sourceRel=original.sourceHypotheses[parsedIndex];
   if(sourceRel.physicalTruth!=='true')throw Error('Preselected originally native contact support not true');
   row.initialSourceClaimPresent=sourceRel.sourceNotErasedForUncertainty;
   row.initialSourceRoleIsSyntacticallyEligible=
    sourceRel.grammarEvidenceKind==='limited_pretrained_syntax_role_candidate';
   row.initialCanNarrateSourceMeaning=sourceRel.eligibleForSourceWordedPresentFact;
   row.initialPhysicalWorldTrue=true;
   const child=world.entities.get(chosen.childId),support=world.entities.get(chosen.parentId);
   const eye=maybeEye(ledger.story,child,support);
   if(!eye)throw Error('Authoritative physical scene not observable from predeclared candidate viewpoints');
   row.initialVisibleBoth=true;
   ledger.story.read('visitor',eye,{radius:12});
   ledger.story.read('visitor',{x:0,y:1.5,z:0},{radius:12});
   const far={x:0,y:1.5,z:0};
   const stop=ledger.story.attachObserver('visitor',()=>far,{radius:12});
   const initialHypCount=original.sourceProposalsPreserved;
   if(!world.applyImpulse(child.id,vectors[version]))
    throw Error('Native PRSE/Rapier rejected predeclared physical disturbance');
   world.tick(155);stop();
   const remote=ledger.story.read('visitor',far,{radius:12});
   row.unwitnessedPhysicalEventLeaks=remote.witnessedEvents.length;
   if(row.unwitnessedPhysicalEventLeaks)throw Error('Remote physical cause leaked into narrator');
   const beforeUnload=ledger.record().current;
   row.afterImpulsePhysicalStatus=beforeUnload.sourceHypotheses[parsedIndex].physicalTruth;
   row.afterImpulseHistoricalSourceClaimStillExists=
    beforeUnload.sourceProposalsPreserved===initialHypCount;
   const actualUnloaded=world.dematerialize();
   if(actualUnloaded===0)throw Error('Offscreen source region did not physically unload');
   world.advanceOffscreen(7);
   const dormant=ledger.record().current;
   row.dormantPhysicalTruth=dormant.sourceHypotheses[parsedIndex].physicalTruth;
   row.dormantHistoricalClaimPersists=
    dormant.sourceHypotheses[parsedIndex].sourceNotErasedForUncertainty;
   row.dormantWorldTime=dormant.worldTime;
   if(row.dormantPhysicalTruth!=='unknown'||!row.dormantHistoricalClaimPersists)
    throw Error('Sleeping source relation falsely judged from absent colliders or original source forgotten');
   const saved=JSON.parse(JSON.stringify(ledger.snapshot()));
   const loaded=PRSEMeaningHypotheses.restore(saved);
   if(!loaded.ok)throw Error('Native physics + original source + observer and hypothesis journal not restored: '+loaded.reason);
   restored=loaded.ledger;
   row.sourcedRolesStillUnresolvedAfterNativeSave=restored.current().undecidedAndRetainedONRelations===
    dormant.undecidedAndRetainedONRelations;
   row.fullOriginalLiterarySourceUntouched=restored.story.sourceArchive().originalText===source.text;
   row.nativeWorldTimeUnchangedBySave=Math.abs(restored.story.loop.time-world.time)<1e-6;
   if(!row.sourcedRolesStillUnresolvedAfterNativeSave||
      !row.fullOriginalLiterarySourceUntouched||!row.nativeWorldTimeUnchangedBySave)
    throw Error('Source uncertainty or authoritative time lost across full native world save');
   restored.story.loop.materialize();restored.story.loop.tick(1);
   const back=restored.record().current.sourceHypotheses[parsedIndex];
   row.returnedPhysicalStatus=back.physicalTruth;
   row.returnedUndecidedSourceCandidateRemains=
    !row.initialCanNarrateSourceMeaning&&back.grammarEvidenceKind!=='limited_pretrained_syntax_role_candidate'&&
     back.sourceNotErasedForUncertainty;
   row.sourceRoleIsUnchanged=back.grammarEvidenceKind===sourceRel.grammarEvidenceKind;
   if(!row.sourceRoleIsUnchanged)throw Error('Native rematerialization silently rewrote literary source interpretation');
   const afterEye=maybeEye(restored.story,
    restored.story.loop.entities.get(chosen.childId),
    restored.story.loop.entities.get(chosen.parentId));
   row.reentryJointlyVisible=Boolean(afterEye);
   if(afterEye){
    const next=restored.story.read('visitor',afterEye,{radius:12});
    row.sourceSemanticRetractions=next.relationRevisions.filter(x=>
     x.type==='previously_visible_fact_retracted').length;
    row.reentryUnwitnessedEvents=next.witnessedEvents.length;
    row.repeatAfterReturn=restored.story.read('visitor',afterEye,{radius:12}).currentSentences.length;
    if(row.reentryUnwitnessedEvents||row.repeatAfterReturn)
     throw Error('Native restored visitor was told unseen cause or duplicate narration');
   }
   row.status='evaluated';
  }catch(e){row.status='failed';row.reason=String(e.message).slice(0,250);}
  finally{restored?.dispose();ledger?.dispose();}
  results.push(row);
 }
}
const ok=results.filter(x=>x.status==='evaluated');
const sum=f=>ok.reduce((n,x)=>n+f(x),0);
const summary={
 distinctPreselectedSourceONClaims:cases.length,
 fixedIndependentNativeImpulsesPerClaim:vectors.length,
 real3DSourceHypothesisOffscreenEpisodes:ok.length,
 failedEpisodes:results.filter(x=>x.status==='failed').length,
 retainedOriginalHistoricalSource:sum(x=>Number(x.fullOriginalLiterarySourceUntouched)),
 actuallyPhysicallyUnloadedAndNativeRestored:sum(x=>Number(x.sourcedRolesStillUnresolvedAfterNativeSave)),
 offscreenPhysicalUnknownNotInvented:sum(x=>Number(x.dormantPhysicalTruth==='unknown')),
 realPhysicalSupportBecameFalseOrUnknown:sum(x=>Number(x.afterImpulsePhysicalStatus!=='true')),
 syntaxRoleApprovedBeforePhysicalCause:sum(x=>Number(x.initialCanNarrateSourceMeaning)),
 undecidedSourceInterpretationSurvivedNativeSave:sum(x=>Number(x.returnedUndecidedSourceCandidateRemains)),
 unseenPhysicalImpulseLeaks:sum(x=>x.unwitnessedPhysicalEventLeaks+(x.reentryUnwitnessedEvents||0)),
 observerSupportRetractions:sum(x=>x.sourceSemanticRetractions||0),
 noRepeatedNarrationAfterReturn:ok.every(x=>!x.repeatAfterReturn),
 noGoldDuringSelectionOrPhysics:true};
const evidence={metadata:{
 source:'Same eight frozen physically eligible SceneEval source support claims and four predeclared actual GameCore impulses as previous research, NOT new independent stories',
 sourceInterpretation:'All source hypotheses preserved under syntax ambiguity; reporter only admits syntax-positive AND actually supported native facts',
 caveat:'Offscreen event is an observed fixed native physical impulse, NOT random NPC social behavior; no unrestricted literary model, human quality or asset fidelity test',
 noGPUorSharedInference:true},summary,results};
const file=directory+'/prse_nondestructive_source_hypotheses_offscreen_32_raw_'+version+'.json';
writeFileSync(file,JSON.stringify(evidence,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_nondestructive_hypotheses_offscreen_32_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...evidence.metadata,privateRawSHA256:digest(readFileSync(file))},
 summary,cases:results.map(x=>({sourceId:x.sourceId,variant:x.variant,
  initialSourceEligible:x.initialCanNarrateSourceMeaning,
  after:x.afterImpulsePhysicalStatus,unloaded:x.dormantPhysicalTruth,
  afterReturn:x.returnedPhysicalStatus,
  sourceAmbiguityRetained:x.returnedUndecidedSourceCandidateRemains,
  status:x.status,reason:x.reason||null}))},null,2)+'\n',{flag:'wx'});
console.log('NATIVE_PERSISTENT_SOURCE_HYPOTHESES_OFFSCREEN',JSON.stringify(summary));
