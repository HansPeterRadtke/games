// The primary PRSE loop, not a 2D gameplay toy: original human and
// assisted source descriptions -> original generated source-linked 3D
// GameCore/Rapier scene -> actual physical support/contact -> actual
// impulse and unseen offscreen consequences -> qualified current semantic
// world and observer-specific text -> native full physics + observer/story
// save/reentry -> the same authoritative object IDs and current story.
//
// ORIGINAL SOURCE SELECTION is the previously frozen physical-dynamic unique
// support eligible list (8 source relationships), with source-only syntax
// abstention defined before independent author gold evaluation.
// The test NEVER selects source cases or materializations from gold labels.
//
// This is a bounded matched negative/positive CASE STUDY, not a statistically
// representative test of arbitrary literary fiction, 3D asset realism or
// generative model writing. Offscreen unload is attempted only if physics
// truly quiet enough; refusal is recorded honestly.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{measureRelation}from'./prse_grounded_relation_narration.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
import{PRSECurrentSemanticDocument}from'./prse_current_semantic_document.mjs';
await initializePhysics();
const directory='/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
const vectors={v1:{x:4,y:1.1,z:.5},v2:{x:-4,y:1.1,z:.5},
 v3:{x:.5,y:1.1,z:4},v4:{x:1.2,y:.9,z:-3.5}};
if(!Object.hasOwn(vectors,version))throw Error('Unknown predeclared physical impulse experiment');
const impulse=vectors[version];
mkdirSync(directory,{recursive:true,mode:0o700});
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const grammar=JSON.parse(readFileSync(directory+'/prse_source_role_on_200_raw_v1.json')).records;
const physical=JSON.parse(readFileSync(directory+'/prse_source_blind_support_eligibility_v1.json')).records;
const roleBy=new Map(grammar.map(r=>[r.sourceId+':'+r.sourceRelationIndex,r]));
const eligible=physical.filter(x=>x.eligible).sort((a,b)=>a.id-b.id);
if(eligible.length!==8)throw Error('Predeclared unbiased exact physical-eligibility source count changed');
const sha=x=>createHash('sha256').update(x).digest('hex');
const timeStart=Date.now(),results=[];
const views=(child,support,extra)=>{
 const positions=[support.position,child.position];
 const mean={x:(positions[0].x+positions[1].x)/2,
  y:(positions[0].y+positions[1].y)/2,z:(positions[0].z+positions[1].z)/2};
 const out=[];
 for(const d of [1.8,2.5,4]){
  for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,-1],[1,-1],[-1,1]]){
   out.push({x:mean.x+dx*d,y:1.6,z:mean.z+dz*d});
  }
 }
 return out;
};
function visibleEye(story,a,b){
 for(const eye of views(a,b)){
  const x=story.perception.isVisible(a.id,eye,{radius:12});
  const y=story.perception.isVisible(b.id,eye,{radius:12});
  if(x.visible&&y.visible)return eye;
 }
 return null;
}
for(const item of eligible){
 const p=source[item.id],layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const all=p.relations.map((r,index)=>({r,index})).filter(({r})=>
  r.kind==='object'&&r.type==='on'&&r.a===item.relA&&r.b===item.relB);
 if(all.length!==1)throw Error('Original claim not uniquely addressable by SOURCE TYPE');
 const index=all[0].index,role=roleBy.get(item.id+':'+index);
 if(!role)throw Error('Original source role gate did not preserve matching source identity');
 const gated=role.status==='source_syntax_role_candidate';
 let story=null,restored=null;
 const row={sourceId:item.id,sourceRelationIndex:index,sourceChild:item.relA,
  sourceSupport:item.relB,
  sourceSyntaxAccepted:gated,physicalOriginalEligible:true,
  expectedOriginalHistoricalSourceSHA256:sha(p.text),
  status:'started'};
 try{
  if(!layout.accepted||geometryIssues(layout.scene).length)
   throw Error('Previously source-eligible physical scene rejected');
  const w=new PRSELoop(layout.scene);w.tick(38);
  const child=w.entities.get(item.childId),support=w.entities.get(item.parentId);
  if(!child||!support||!w.active.has(child.id))throw Error('Original native object IDs absent');
  story=new PRSESourceRevision(w,gated?[all[0].r]:[],{observerRadius:12});
  const semantic=new PRSECurrentSemanticDocument(story);
  const before=measureRelation(w,all[0].r);
  if(before.truth!=='true')throw Error('Originally physically supported source claim changed');
  const first=semantic.record();
  row.initialCurrentWorldIsPhysical=true;
  row.initialSourceRoleRelationPrinted=first.current.verifiedTextClauses.some(x=>
   x.type==='physically_verified_source_relation');
  row.initialPhysicalOnlySupportPrinted=first.current.verifiedTextClauses.some(x=>
   x.type==='physically_verified_support_not_source_entailed'&&
   x.ids[0]===child.id&&x.ids[1]===support.id);
  if(gated&&!row.initialSourceRoleRelationPrinted)
   throw Error('Syntax source candidate was not shown with actual physical contact');
  if(!gated&&row.initialSourceRoleRelationPrinted)
   throw Error('Ungrounded literal source role promoted as SOURCE-entailed');
  row.initialRolePhysicalState=before.truth;
  const eye=visibleEye(story,child,support);
  row.initialContactObservableToReader=Boolean(eye);
  if(eye){
   const intro=story.read('visitor',eye,{radius:12});
   row.introNarratedSourceRelationships=intro.relationRevisions.length;
   row.introPhysicalObjectStateMessages=intro.visibleCurrentStates.length;
   const second=story.read('visitor',eye,{radius:12});
   if(second.currentSentences.length)throw Error('Repeated unchanged source/physical fact');
  }
  const far={x:0,y:1.5,z:0};
  story.read('visitor',far,{radius:12});
  const unsubscribe=story.attachObserver('visitor',()=>far,{radius:12});
  const originalTime=w.time;
  const originalSeq=w.nextSeq;
  if(!w.applyImpulse(child.id,impulse))throw Error('Native GameCore rejected physical impulse');
  w.tick(155);
  const remote=story.read('visitor',far,{radius:12});
  row.remotelyLeakedPhysicalEventCount=remote.witnessedEvents.length;
  if(row.remotelyLeakedPhysicalEventCount)throw Error('Previously absent visitor acquired hidden cause');
  unsubscribe();
  const after=measureRelation(w,all[0].r);
  row.afterRealPhysicalImpulse=after.truth;
  row.actualPhysicsEvents=w.events.filter(e=>e.ids?.includes(child.id)&&e.sequence>=originalSeq).length;
  row.elapsedPhysicsSeconds=w.time-originalTime;
  const changed=semantic.record();
  row.currentDocumentRelationTruth=changed.current.relationClaimCounts;
  row.didSemanticDocumentChange=changed.changed;
  row.currentDocumentSourceClaimStillAsserted=changed.current.verifiedTextClauses.some(x=>
   x.type==='physically_verified_source_relation'&&x.claim==='true'&&
   x.sourceRelationIndex===0);
  if(after.truth!=='true'&&row.currentDocumentSourceClaimStillAsserted)
   throw Error('Current literary world still claimed a physically disproved support');
  row.currentSourceStillHistorical=story.sourceArchive().originalText===p.text;
  if(!row.currentSourceStillHistorical)throw Error('Historically original source rewritten by physics');
  // Attempt REAL unloaded semantic continuation: do not fake sleep/settlement.
  // This native dematerialization is allowed only when existing GameCore
  // physics confirms low motion. Otherwise retain live physics and record why.
  let unloaded=0;
  try{
   unloaded=w.dematerialize();
   row.wasPhysicallyUnloaded=unloaded>0;
  }catch(e){
   row.wasPhysicallyUnloaded=false;row.offscreenRefusal=String(e.message).slice(0,120);
  }
  if(row.wasPhysicallyUnloaded){
   const latent=semantic.record().current;
   row.unloadedQualifiedCurrentWorld=latent.unloadedCount>0;
   w.advanceOffscreen(7);
  }else{
   row.unloadedQualifiedCurrentWorld=false;
   // Never pretend unobserved objects stop moving or time stops.
   w.tick(60);
  }
  const saved=JSON.parse(JSON.stringify(semantic.snapshot()));
  const native=PRSECurrentSemanticDocument.restore(saved);
  if(!native.ok)throw Error('Native full GameCore + source + knowledge journal failed: '+native.reason);
  restored=native.document;
  row.savedEventHistoryCount=restored.story.loop.events.length;
  row.restoredHistoricalSourceAndIds=
   restored.story.sourceArchive().originalText===p.text&&
   restored.story.loop.entities.has(child.id)&&restored.story.loop.entities.has(support.id);
  row.restoredNativeWorldClock=restored.story.loop.time;
  if(row.wasPhysicallyUnloaded)restored.story.loop.materialize();
  restored.story.loop.tick(1);
  const r2=measureRelation(restored.story.loop,all[0].r);
  row.finalNativePhysicalOnStatus=r2.truth;
  const current=restored.record().current;
  row.finalCurrentWorldRelationStatus=current.relationClaimCounts;
  row.finalCurrentDocumentSourceClaimStillAsserted=current.verifiedTextClauses.some(x=>
   x.type==='physically_verified_source_relation'&&x.sourceRelationIndex===0);
  if(r2.truth==='false'&&row.finalCurrentDocumentSourceClaimStillAsserted)
   throw Error('Restored semantic document lied about physical contact');
  const finalChild=restored.story.loop.entities.get(child.id);
  const finalSupport=restored.story.loop.entities.get(support.id);
  const eyeBack=visibleEye(restored.story,finalChild,finalSupport);
  row.finalBothObjectsVisibleToReader=Boolean(eyeBack);
  if(eyeBack){
   const returnVisit=restored.story.read('visitor',eyeBack,{radius:12});
   row.reentryRetractions=returnVisit.relationRevisions.filter(e=>
    e.type==='previously_visible_fact_retracted').length;
   row.reentryConfirmedSupport=returnVisit.relationRevisions.filter(e=>
    e.type==='verified_present_fact').length;
   row.reentryWitnessedHiddenEvents=returnVisit.witnessedEvents.length;
   if(row.reentryWitnessedHiddenEvents)throw Error('Invented eyewitness account after unseen physical impulse');
   const duplicate=restored.story.read('visitor',eyeBack,{radius:12});
   row.duplicateCurrentFactMessages=duplicate.currentSentences.length;
   if(row.duplicateCurrentFactMessages)throw Error('Duplicated unchanged text after native reentry');
  }
  row.status='evaluated';
 }catch(e){row.status='failed';row.error=String(e.message).slice(0,250);}
 finally{restored?.dispose();story?.dispose();}
 results.push(row);
}
const good=results.filter(x=>x.status==='evaluated'),sum=(key)=>good.reduce((n,x)=>n+(x[key]||0),0);
const summary={
 sourceBlindPredefinedEligiblePhysicalRelations:eligible.length,
 sourceSyntaxAccepted:good.filter(x=>x.sourceSyntaxAccepted).length,
 successfullyEvaluated:good.length,executionFailures:results.length-good.length,
 initialSourceSupportedRelationsActuallyNarrated:good.filter(x=>x.initialSourceRoleRelationPrinted).length,
 originalPhysicalTrue:good.filter(x=>x.initialRolePhysicalState==='true').length,
 realPhysicalImpulsesApplied:good.length,
 realImpulsesLedToFalseOrUnknownSupport:good.filter(x=>x.afterRealPhysicalImpulse!=='true').length,
 physicallyDisprovedSourceClaimsStillPrinted:good.filter(x=>
  x.afterRealPhysicalImpulse==='false'&&x.currentDocumentSourceClaimStillAsserted).length,
 actualSafeOffscreenRegionUnloads:good.filter(x=>x.wasPhysicallyUnloaded).length,
 unknownUnloadedSemanticsQualified:good.filter(x=>x.unloadedQualifiedCurrentWorld).length,
 nativeSavedAndRematerialized:good.filter(x=>x.restoredHistoricalSourceAndIds).length,
 fromPhysicalWorldToCurrentWorldAfterReentry:good.filter(x=>x.finalNativePhysicalOnStatus==='false'&&
  !x.finalCurrentDocumentSourceClaimStillAsserted).length,
 initialPhysicallyVisibleSourceCases:good.filter(x=>x.initialContactObservableToReader).length,
 reentryPhysicallyVisibleBothObjects:good.filter(x=>x.finalBothObjectsVisibleToReader).length,
 successfulObserverPhysicalRelationRetractions:sum('reentryRetractions'),
 remoteHiddenPhysicalEventLeaks:sum('remotelyLeakedPhysicalEventCount')+sum('reentryWitnessedHiddenEvents'),
 repeatedUnchangedReturnNarrative:sum('duplicateCurrentFactMessages'),
 sourceTextsUnchanged:good.filter(x=>x.currentSourceStillHistorical).length};
const obj={metadata:{
 source:'Original source-derived SceneEval relations before independent gold annotation reading, all 8 predeclared native 3D dynamically supported scenes',
 sourceSelection:'Previously saved physical eligibility list, not selected by author gold or desired outcomes',
 predeclaredImpulseVector:impulse,experimentVersion:version,
 fixedNativeInput:'Actual GameCore/Rapier predeclared impulse, 155 native steps plus conditional real 7s offscreen process',
 caution:'Tiny previously exposed selected subset, not general unrestricted fiction; passed source syntax is NOT full source entailment',
 sourceGoldNeverLoaded:true,
 noLLMorGPUorHumanParticipants:true},summary,results};
const path=directory+'/prse_source_role_full_loop_8_raw_'+version+'.json';
writeFileSync(path,JSON.stringify(obj,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_source_role_full_loop_8_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...obj.metadata,privateRawSHA256:sha(readFileSync(path))},
 summary,results:results.map(x=>({sourceId:x.sourceId,parsedChild:x.sourceChild,
 syntaxAccepted:x.sourceSyntaxAccepted,original:x.initialRolePhysicalState,
 after:x.afterRealPhysicalImpulse,final:x.finalNativePhysicalOnStatus,
 unloaded:x.wasPhysicallyUnloaded,observerRetractions:x.reentryRetractions||0,
 status:x.status,error:x.error||null}))},null,2)+'\n',{flag:'wx'});
console.log('EIGHT_SOURCE_SUPPORT_FULL_LOOPS',JSON.stringify(summary));
