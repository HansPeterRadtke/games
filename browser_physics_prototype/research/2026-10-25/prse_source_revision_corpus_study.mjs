// PRSE source-preserving, observer-knowledge and native 3D revision continuity
// on a PREVIOUSLY FROZEN selection of 63 SceneEval externally authored
// physical scenes. The same GameCore drives every physical movement.
//
// Current *literary* output = verified observer-visible changes, not reprinting
// the historical source description; the original remains archived by hash.
//
// The observer witnesses impulses only if the authoritative Rapier first-hit
// geometry allows observation at event emission. No current-source annotation
// labels or generative model calls enter the pipeline.
//
// This is a bounded engineering evidence study, NOT human assessment of prose.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import{performance}from'node:perf_hooks';
import{initializePhysics}from'../../physics-core.js';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
await initializePhysics();

const inputs=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const frozen=JSON.parse(readFileSync(
 '/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility/prse_observer_event_batch_200_raw_v2.json'));
const selections=frozen.rows.filter(r=>r.status==='evaluated');
if(selections.length!==63)throw Error('Frozen external source sample altered');
const views=[
 {x:-27,y:1.5,z:11.8},{x:-32.8,y:1.5,z:7.9},
 {x:-21,y:1.5,z:7.9},{x:-32.8,y:1.5,z:15.7},
 {x:-21,y:1.5,z:15.7}
],far={x:0,y:1.5,z:0};
const saveDir='/data/var/games/prse_semantic_research/runs/2026-10-25-literary-revision';
mkdirSync(saveDir,{recursive:true,mode:0o700});
const hash=b=>createHash('sha256').update(b).digest('hex');
const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Unsafe evidence output version');
const started=performance.now(),cases=[];
for(let i=0;i<selections.length;i++){
 const choice=selections[i],source=inputs[Number(choice.id)];
 const pose=repairScene(source,{maxSweeps:2,maxAttemptsPerScene:150});
 const rec={id:choice.id,subset:choice.sourceType,kind:choice.chosenCategory,
  status:'not_started',initialRelationCount:source.relations.length};
 let original=null,restored=null,story=null;
 try{
  if(!pose.accepted||geometryIssues(pose.scene).length)throw Error('Previously accepted scene is invalid');
  original=new PRSELoop(pose.scene);original.tick(25);
  story=new PRSESourceRevision(original,source.relations,{observerRadius:9});
  const target=pose.scene.entities.find(e=>e.kind===choice.chosenCategory&&e.body==='dynamic');
  if(!target)throw Error('Dynamic source object no longer available');
  const eye=views.find(pos=>story.perception.isVisible(target.id,pos,{radius:9,mode:'ray'}).visible);
  if(!eye)throw Error('No original verified physical eye for dynamic source object');
  const intro=story.read('near-reader',eye);
  const remote=story.read('far-reader',far);
  const noDup=story.read('near-reader',eye);
  if(remote.text||noDup.text)throw Error('Current world leaked unseen or repeated intro');
  rec.initialIntroSentences=intro.currentSentences.length;
  rec.initialVerifiedRelationSentences=intro.relationRevisions.length;
  rec.initialVisibleObjectStateSentences=intro.visibleCurrentStates.length;
  rec.initialWitnessedEvents=intro.witnessedEvents.length;
  rec.remoteInitialMessages=remote.currentSentences.length;
  rec.sourceProseWouldHaveBeenBytes=Buffer.byteLength(source.text);
  rec.introActualBytes=Buffer.byteLength(intro.text);
  rec.sourceRelationsPhysicallyTrueBefore=story.currentWorldAudit().true;
  // These explicit event-time observers MUST be attached to the exact
  // authoritative PRSELoop.emit stream (not a one-frame-late UI poll).
  const unsubscribeVisible=story.attachObserver('near-reader',()=>eye,{radius:9});
  const unsubscribeRemote=story.attachObserver('far-reader',()=>far,{radius:9});
  if(!original.applyImpulse(target.id,{x:4,y:1.0,z:.65}))
   throw Error('Real GameCore impulse refused');
  original.tick(95);
  const afterLocal=story.read('near-reader',eye);
  const afterRemote=story.read('far-reader',far);
  if(afterRemote.text)throw Error('Remote observer learned the hidden event');
  rec.liveVisibleImpulseReports=afterLocal.witnessedEvents.filter(e=>e.text.includes('impulse')).length;
  rec.afterImpulseVisiblePhysicalStateSentences=afterLocal.visibleCurrentStates.length;
  rec.afterImpulseVerifiedRelationSentences=afterLocal.relationRevisions.length;
  rec.outputEvidence=[...intro.witnessedEvents,...intro.relationRevisions,...intro.visibleCurrentStates,
    ...afterLocal.witnessedEvents,...afterLocal.relationRevisions,...afterLocal.visibleCurrentStates].map(e=>({
       category:e.type,entityID:e.entityID||null,originID:e.originID||null,
       entityIDs:e.sourceEntityIDs||null,eventSeq:e.eventSequence||null,
       relationKey:e.relationKey??null,evidence:e.evidence||e.source||null,
       text:e.text
    }));
  rec.remoteEventLeaks=afterRemote.witnessedEvents.length;
  rec.physicallyCurrentRelationChanges=afterLocal.relationRevisions.length;
  rec.sourceRelationsPhysicallyTrueAfter=story.currentWorldAudit().true;
  rec.localReportBytes=Buffer.byteLength(afterLocal.text);
  rec.repeatedText=Buffer.byteLength(story.read('near-reader',eye).text);
  if(rec.outputEvidence.some(e=>!['current_visible_physical_state','witnessed_physical_event',
    'verified_present_fact','previously_visible_fact_retracted'].includes(e.category)))
   throw Error('Unattributed story text appeared in authoritative evidence channel');
  if(rec.repeatedText)throw Error('Repeated unchanged observer message');
  unsubscribeVisible();unsubscribeRemote();
  const save=JSON.parse(JSON.stringify(story.snapshot()));
  rec.nativeSceneTransactionBytes=Buffer.byteLength(JSON.stringify(save));
  const loaded=PRSESourceRevision.restore(save);
  if(!loaded.ok)throw Error('Native physical + semantic + observer transaction failed: '+loaded.reason);
  restored=loaded.story;
  const reentry=restored.read('near-reader',eye);
  const distant=restored.read('far-reader',far);
  if(distant.text||reentry.witnessedEvents.length||reentry.text)
   throw Error('Repeated previously delivered witness or relation after transactional save');
  rec.staleHistoricalProseReplayed=false;
  rec.originalSourceRetained=restored.sourceArchive().originalText===source.text;
  rec.sentenceCountAfterNativeReload=reentry.currentSentences.length;
  rec.nativePoseSaveErrorMeters=distance(
   original.active.get(target.id).translation(),loaded.loop.active.get(target.id).translation());
  rec.nativeClockEqual=Math.abs(original.time-loaded.loop.time)<1e-6;
  // An additional physical cause after the save must not diverge merely
  // because observer/revision state was saved and world references rebound.
  const follow={x:-1.5,y:.55,z:.9};
  if(!original.applyImpulse(target.id,follow)||!loaded.loop.applyImpulse(target.id,follow))
   throw Error('Post-save native GameCore action failed');
  original.tick(90);loaded.loop.tick(90);
  rec.nextPhysicalCauseDeviationMeters=distance(
   original.active.get(target.id).translation(),loaded.loop.active.get(target.id).translation());
  rec.nextWorldClockError=Math.abs(original.time-loaded.loop.time);
  rec.futureSourceTruthMatches=story.currentWorldAudit().true===restored.currentWorldAudit().true &&
   story.currentWorldAudit().false===restored.currentWorldAudit().false &&
   story.currentWorldAudit().unknown===restored.currentWorldAudit().unknown;
  rec.status='evaluated';
 }catch(e){
  rec.status='failed';rec.reason=String(e?.message||e).slice(0,240);
 }finally{
  restored?.dispose();if(!restored)original?.dispose();
  else original?.dispose();
 }
 cases.push(rec);
 if((i+1)%10===0)console.log('PROGRESS',i+1,'of',selections.length);
}
const valid=cases.filter(r=>r.status==='evaluated');
const summary={inputSourceScenes:cases.length,valid:valid.length,failed:cases.length-valid.length,
 witnessedEvents:valid.reduce((n,r)=>n+r.liveVisibleImpulseReports,0),
 failedObserverPrivacyCases:valid.filter(r=>r.remoteEventLeaks>0||r.remoteInitialMessages>0).length,
 duplicatedReports:valid.filter(r=>r.repeatedText>0||r.sentenceCountAfterNativeReload>0).length,
 sourceArchivesUnchanged:valid.filter(r=>r.originalSourceRetained).length,
 identicalCurrentRelationTruthAfterLaterNativeSave:valid.filter(r=>r.futureSourceTruthMatches).length,
 physicalSaveDifferencesOverTwoCm:valid.filter(r=>r.nextPhysicalCauseDeviationMeters>.02).length,
 largestNativeSavePositionDifferenceMeters:valid.length?Math.max(...valid.map(r=>r.nextPhysicalCauseDeviationMeters)):null,
 sceneReadInitialStatements:valid.reduce((n,r)=>n+r.initialIntroSentences,0),
 firstVisibleObjectStateStatements:valid.reduce((n,r)=>n+r.initialVisibleObjectStateSentences,0),
 firstVerifiedRelationStatements:valid.reduce((n,r)=>n+r.initialVerifiedRelationSentences,0),
 laterVisibleObjectStateStatements:valid.reduce((n,r)=>n+r.afterImpulseVisiblePhysicalStateSentences,0),
 laterVerifiedRelationStatements:valid.reduce((n,r)=>n+r.afterImpulseVerifiedRelationSentences,0),
 sourceClaimsBeforeTruth:valid.reduce((n,r)=>n+r.sourceRelationsPhysicallyTrueBefore,0),
 elapsedWallSeconds:+((performance.now()-started)/1000).toFixed(2)};
const full={metadata:{
 source:'Exact 63 earlier externally authored SceneEval source scenes with a real dynamic body and physical ray-verified observer',
 annotationsNotRead:true,noGPUorLLM:true,
 goal:'Test immutable literary source, event-time observer knowledge, physically supported current prose, atomic native physical/semantic/observer save and further causal continuation',
 caution:'Not a human prose-quality study, source text parsing remains poor; 3D solver and observer logic are research-only'},summary,cases};
const target=saveDir+'/prse_source_revision_63_raw_'+version+'.json';
writeFileSync(target,JSON.stringify(full,null,2)+'\n',{flag:'wx',mode:0o600});
const aggregate={metadata:{...full.metadata,privateEvidenceSHA256:hash(readFileSync(target)),
 privateEvidencePath:target},summary,
 cases:cases.map(r=>({
  id:r.id,subset:r.subset,status:r.status,initialMessages:r.initialIntroSentences||0,
  visibleWitnesses:r.liveVisibleImpulseReports||0,remoteLeaks:r.remoteEventLeaks||0,
  postSavePhysicalDifferenceMeters:r.nextPhysicalCauseDeviationMeters??null,
  afterSavePhysicalFactsConsistent:r.futureSourceTruthMatches??false,
  failedReason:r.reason||null}))};
writeFileSync(new URL('prse_source_revision_63_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify(aggregate,null,2)+'\n',{flag:'wx'});
console.log('FINAL',JSON.stringify(summary));
