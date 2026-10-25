// Exact previously FAILED live-source scenario regression for corrected PRSE
// tipped vs upright semantics, actual observer perception and Rapier native
// whole-world save/reentry. Selected from original frozen 256-case real 3D
// orientation false current-state findings, before the correction.
//
// These are 11 targeted regression conditions across source-derived scenes,
// NOT 11 newly sampled independent literary worlds. Source IDs, input forces,
// prior false tipped state and corrected same native physical trajectory are
// determined by immutable owner-private original/after metrics, not author
// gold labels or any new optimizer.
//
// No GPU/LLM, no deployed PRSE server and no owner calendar effects.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSESourceRevision}from'./prse_source_revision_story.mjs';
import {PRSECurrentSemanticDocument}from'./prse_current_semantic_document.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit';
mkdirSync(ROOT,{recursive:true,mode:0o700});
const orig=JSON.parse(readFileSync(ROOT+'/prse_native_tipped_event_vs_orientation_256_raw_v1.json')).rows;
const corrected=JSON.parse(readFileSync(ROOT+'/prse_native_tipped_event_vs_orientation_256_raw_v2.json')).rows;
const sources=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const vectors={east_up:{x:4,y:1.1,z:.5},west_up:{x:-4,y:1.1,z:.5},
 south_up:{x:.5,y:1.1,z:4},north_low:{x:1.2,y:.9,z:-3.5}};
const tilt=q=>{
 const n=Math.hypot(q.x,q.y,q.z,q.w);
 return Math.acos(Math.max(-1,Math.min(1,1-2*(q.x*q.x+q.z*q.z)/(n*n))));
};
const old=[];
for(let i=0;i<orig.length;i++){
 const first=orig[i],second=corrected[i];
 if((first.sourceId!==second.sourceId)||(first.action!==second.action))
  throw Error('Original and corrected physics inputs were not paired');
 const prior=first.finalBodyPositions.filter(x=>x.semanticStickyTipped&&x.nativeUpTiltRadians<.12);
 if(prior.length!==first.semanticTippedButCurrentlyUprightAtEnd)
  throw Error('Original false-current statement case not identified consistently');
 if(prior.length)old.push({sourceId:first.sourceId,action:first.action,
  previouslyFalseCurrentTipped:prior.map(x=>x.id),
  originalPhysicsMeasuredUp:prior.map(x=>x.nativeUpTiltRadians)});
}
if(old.length!==11)throw Error('Expected 11 previously measured false-current source conditions');
function eyeFor(story,entity){
 const p=entity.position;
 for(const radius of [1.5,2.5,4]){
  for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,-1],[1,-1],[-1,1]]){
   const eye={x:p.x+dx*radius,y:1.5,z:p.z+dz*radius};
   if(story.perception.isVisible(entity.id,eye,{radius:12}).visible)return eye;
  }
 }
 return null;
}
const rows=[];
for(const oldCase of old){
 const proposal=sources[oldCase.sourceId],layout=repairScene(proposal,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!layout.accepted)throw Error('Previously accepted source geometry invalid');
 let l=null,restored=null;
 const row={sourceId:oldCase.sourceId,action:oldCase.action,failedPreviously:oldCase.previouslyFalseCurrentTipped,
  status:'started',eventTimePhysicalFlags:[],oldFalseUpTilts:oldCase.originalPhysicsMeasuredUp};
 try{
  l=new PRSELoop(layout.scene);l.tick(36);
  const firstTarget=oldCase.previouslyFalseCurrentTipped[0],target=l.entities.get(firstTarget);
  if(!target)throw Error('Original source entity not found');
  const eye=eyeFor(new PRSESourceRevision(l,[],{observerRadius:12}),target);
  row.returningEyePhysicallyValid=Boolean(eye);
  const revoke=l.subscribeEvents(ev=>{
   if(!['tipped','righted'].includes(ev.type))return;
   const actual=l.active.get(ev.ids[0]);
   if(!actual)throw Error('Claimed actual physical event on missing native body');
   row.eventTimePhysicalFlags.push({event:ev.type,entityID:ev.ids[0],
    nativeActualUpTilt:tilt(actual.rotation()),worldTime:l.time,
    sourceCurrentTipped:!!l.entities.get(ev.ids[0]).state.tipped});
  });
  const dynamic=layout.scene.entities.find(e=>e.body==='dynamic'&&e.kind!== 'sphere' &&e.id===firstTarget);
  if(!dynamic)throw Error('Previously measured tipped source object is not dynamic');
  // Same original experiment applies the impulse to first preferred ON
  // child, else the first movable real body; it need not be the falsely
  // tipped object. Reconstruct that exact prior physical action target.
  const proposedOn=proposal.relations.filter(r=>r.kind==='object'&&r.type==='on');
  const firstOn=proposedOn.find(r=>{
   const xs=l.scene.entities.filter(e=>e.kind===r.a&&e.source!=='provisional_3D_room_boundary');
   return xs.length===1&&xs[0].body==='dynamic';
  });
  const mover=firstOn?l.scene.entities.find(e=>e.kind===firstOn.a):
   l.scene.entities.find(e=>e.body==='dynamic'&&!e.state?.destroyed);
  if(!mover||!l.applyImpulse(mover.id,vectors[oldCase.action]))
   throw Error('Original exactly matched physical impulse no longer possible');
  l.tick(160);revoke();
  const currentDoc=new PRSESourceRevision(l,[],{observerRadius:12});
  const current=new PRSECurrentSemanticDocument(currentDoc);
  const state=current.record().current;
  row.oldSourceStillImmutable=l.scene.prose===proposal.text;
  row.currentPhysicallyUprightIds=oldCase.previouslyFalseCurrentTipped.filter(id=>
   tilt(l.active.get(id).rotation())<.12&&!l.entities.get(id).state.tipped);
  if(row.currentPhysicallyUprightIds.length!==oldCase.previouslyFalseCurrentTipped.length)
   throw Error('Research correction still reports previously false current tipped status');
  row.currentDocumentWrongTippedClaims=state.verifiedTextClauses.filter(c=>
    c.type==='current_physical_presence'&&oldCase.previouslyFalseCurrentTipped.includes(c.ids[0])&&
    c.text.includes('is tipped over')).length;
  if(row.currentDocumentWrongTippedClaims)throw Error('Source-derived current text claims false tipped');
  row.verifiedRealTippedEventCount=row.eventTimePhysicalFlags.filter(e=>
    e.event==='tipped'&&e.nativeActualUpTilt>.7).length;
  row.badEventTimeTippedCount=row.eventTimePhysicalFlags.filter(e=>
    e.event==='tipped'&&e.nativeActualUpTilt<=.7).length;
  row.verifiedRealRightingEventCount=row.eventTimePhysicalFlags.filter(e=>
    e.event==='righted'&&e.nativeActualUpTilt<.12).length;
  row.badEventTimeRightingCount=row.eventTimePhysicalFlags.filter(e=>
    e.event==='righted'&&e.nativeActualUpTilt>=.12).length;
  if(row.badEventTimeTippedCount||row.badEventTimeRightingCount)
   throw Error('Corrected event stream includes nonphysical tipping/righting');
  if(eye){
   const view=currentDoc.read('visitor',eye,{radius:12});
   row.returningRayVisibleSourceObject=view.visibleEntityIDs.includes(firstTarget);
   row.returnedFalseTippedText=view.visibleCurrentStates.filter(x=>
    x.entityID===firstTarget&&x.text.includes('tipped over')).length;
   if(row.returnedFalseTippedText)throw Error('Real reader saw a false current tipped claim');
  }
  const saved=JSON.parse(JSON.stringify(current.snapshot()));
  const answer=PRSECurrentSemanticDocument.restore(saved);
  if(!answer.ok)throw Error('Native whole world/observer/current-source restore failed: '+answer.reason);
  restored=answer.document;
  row.sourceAndCurrentTextRestored=
   restored.story.sourceArchive().originalText===proposal.text&&
   restored.current().text===state.text;
  row.originalIDsRestored=oldCase.previouslyFalseCurrentTipped.every(id=>
   restored.story.loop.entities.has(id)&&restored.story.loop.active.has(id));
  row.savedCurrentUpright=oldCase.previouslyFalseCurrentTipped.every(id=>
   !restored.story.loop.entities.get(id).state.tipped&&
   tilt(restored.story.loop.active.get(id).rotation())<.12);
  if(!row.sourceAndCurrentTextRestored||!row.originalIDsRestored||!row.savedCurrentUpright)
   throw Error('Native save/reentry lost corrected current physical orientation truth');
  row.status='corrected_real_native_semantic_and_observer';
 }catch(e){row.status='failed';row.reason=String(e.message).slice(0,260);}
 finally{restored?.dispose();l?.dispose();}
 rows.push(row);
}
const good=rows.filter(x=>x.status==='corrected_real_native_semantic_and_observer');
const sum=f=>good.reduce((n,x)=>n+f(x),0);
const summary={
 previouslyDisprovedSourceDerivedCurrentTippedCases:old.length,
 correctedWholeSceneNativeSources:good.length,
 scientificRunFailures:rows.length-good.length,
 correctedPhysicallyUprightPersistedObjectIDs:sum(x=>x.currentPhysicallyUprightIds.length),
 explicitlyActualNativeTippingEventsVerified:sum(x=>x.verifiedRealTippedEventCount),
 actualNativeRightingEventsVerified:sum(x=>x.verifiedRealRightingEventCount),
 wrongTippingEventsAfterCorrection:sum(x=>x.badEventTimeTippedCount),
 wrongRightingEventsAfterCorrection:sum(x=>x.badEventTimeRightingCount),
 wrongCurrentTippedSourceTextAfterCorrection:sum(x=>x.currentDocumentWrongTippedClaims),
 rayVisibleReturnedSourceScenes:good.filter(x=>x.returningRayVisibleSourceObject).length,
 factualHistoricalSourceAndNativePhysicsPersistenceVerified:good.filter(x=>x.sourceAndCurrentTextRestored&&x.originalIDsRestored&&x.savedCurrentUpright).length,
 extrapolationLimit:'Known false historical cases selected on past results; no independent story corpus/human language evaluation'};
const out='/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit/prse_corrected_tipped_current_observer_native_11_raw_v1.json';
const content={metadata:{
 source:'Eleven previously exposed real external source-scene false current tipped statuses, native GameCore authoritative physics and current literary source/observer',
 noAuthorGoldForSelection:true,
 noGPUorLLM:true,
 notIndependentNewRandomScenes:true},summary,rows};
writeFileSync(out,JSON.stringify(content,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_corrected_tipping_native_observer_11_aggregate_v1.json',import.meta.url),
 JSON.stringify({metadata:{...content.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(out)).digest('hex')},
 summary,
 perSource:rows.map(x=>({sourceId:x.sourceId,action:x.action,status:x.status,
 realNativeRightings:x.verifiedRealRightingEventCount,
 savedAndVerified:x.savedCurrentUpright??false,reason:x.reason||null}))},null,2)+'\n',{flag:'wx'});
console.log('ORIENTATION_SEMANTIC_OBSERVER_NATIVE_REENTRY',JSON.stringify(summary));
