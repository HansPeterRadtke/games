// Research-only event-time observer integration for newly corrected RIGHTED
// event, on the SAME eleven previously real SceneEval source-derived false
// present-tense tipping cases. An AUTOMATIC TRACKING SPECTATOR chooses an eye
// point with a true native Rapier ray to the physical target for each event;
// this is a visibility plumbing test, NOT a real human observer or a claim
// of realistic player-camera locomotion.
//
// A separate distant stationary observer never witnesses the events.
// Source text, real native world and witnessed event IDs survive the trusted
// full GameCore/Rapier observer/source save without duplicate presentation.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
await initializePhysics();
const dir='/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Unsafe source evidence output version');
mkdirSync(dir,{recursive:true,mode:0o700});
const original=JSON.parse(readFileSync(dir+'/prse_native_tipped_event_vs_orientation_256_raw_v1.json')).rows;
const frozen=original.filter(x=>x.semanticTippedButCurrentlyUprightAtEnd);
if(frozen.length!==11)throw Error('Expected previous genuine false-current cases');
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const vectors={east_up:{x:4,y:1.1,z:.5},west_up:{x:-4,y:1.1,z:.5},
 south_up:{x:.5,y:1.1,z:4},north_low:{x:1.2,y:.9,z:-3.5}};
const far={x:0,y:1.5,z:0},rows=[];
function eye(story,target){
 const e=story.loop.entities.get(target.id);
 if(!e)return far;
 const p=e.position;
 for(const radius of [1.3,2,3.5,5.5]){
  for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,-1],[1,-1],[-1,1]]){
   const test={x:p.x+dx*radius,y:Math.max(1.3,p.y+1.1),z:p.z+dz*radius};
   if(story.perception.isVisible(e.id,test,{radius:12,mode:'ray'}).visible)return test;
  }
 }
 return far;
}
for(const f of frozen){
 const p=proposals[f.sourceId],layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 let story=null,restored=null;
 const row={sourceId:f.sourceId,action:f.action,status:'started'};
 try{
  if(!layout.accepted)throw Error('Frozen real source not accepted');
  const loop=new PRSELoop(layout.scene);
  loop.tick(36);
  const on=p.relations.filter(x=>x.kind==='object'&&x.type==='on');
  const first=on.find(x=>{
   const xs=loop.scene.entities.filter(e=>e.kind===x.a&&e.source!=='provisional_3D_room_boundary');
   return xs.length===1&&xs[0].body==='dynamic';
  });
  const mover=first?loop.scene.entities.find(e=>e.kind===first.a):
   loop.scene.entities.find(e=>e.body==='dynamic'&&!e.state?.destroyed);
  if(!mover)throw Error('Missing prior native GameCore source mover');
  const target=f.finalBodyPositions.find(x=>x.semanticStickyTipped&&x.nativeUpTiltRadians<.12);
  if(!target||!loop.entities.has(target.id))throw Error('Prior incorrect source ID not present');
  story=new PRSESourceRevision(loop,[],{observerRadius:12});
  const startEye=eye(story,target);
  story.read('autofollow-witness',startEye,{radius:12});
  story.read('remote-unseen',far,{radius:12});
  const stopWatch=story.attachObserver('autofollow-witness',()=>eye(story,target),{radius:12});
  const stopRemote=story.attachObserver('remote-unseen',()=>far,{radius:12});
  if(!loop.applyImpulse(mover.id,vectors[f.action]))throw Error('Original real impulse refused');
  loop.tick(160);
  stopWatch();stopRemote();
  const visibleAtEnd=eye(story,target);
  const watched=story.read('autofollow-witness',visibleAtEnd,{radius:12});
  const unseen=story.read('remote-unseen',far,{radius:12});
  row.witnessedRightings=watched.witnessedEvents.filter(e=>e.text.includes('became upright again')).length;
  row.witnessedTippings=watched.witnessedEvents.filter(e=>e.text.includes('tipped over')).length;
  row.distantUnexpectedEvents=unseen.witnessedEvents.length;
  row.historyCurrentPartitionLossless=
   JSON.stringify([...watched.witnessedEventSentences,...watched.currentWorldFactSentences])===
    JSON.stringify(watched.narrationSentences)&&
   JSON.stringify(watched.narrationSentences)===JSON.stringify(watched.currentSentences)&&
   watched.legacyCurrentSentencesMixesHistoryAndCurrentFacts===true;
  row.sourceCurrentStillUpright=!loop.entities.get(target.id).state.tipped;
  const nativeBody=loop.active.get(target.id),nativeQuat=nativeBody.rotation();
  const nativeN=Math.hypot(nativeQuat.x,nativeQuat.y,nativeQuat.z,nativeQuat.w);
  row.nativeCurrentUpTilt=Math.acos(Math.max(-1,Math.min(1,
   1-2*(nativeQuat.x**2+nativeQuat.z**2)/nativeN**2)));
  const oldExpected=f.finalBodyPositions.find(x=>x.id===target.id);
  row.expectedExactPriorPhysicsUpTilt=oldExpected.nativeUpTiltRadians;
  row.observerMayHaveAlteredPhysicalTrajectory=
   Math.abs(row.nativeCurrentUpTilt-row.expectedExactPriorPhysicsUpTilt)>1e-4;
  // A returned observation includes HISTORICAL genuinely witnessed events
  // AND present-tense current facts. A truthful past 'tipped over' event
  // must never be mis-scored as a false claim about the current upright body.
  row.currentSemanticTextNoFalseTipped=!watched.visibleCurrentStates.some(x=>
   x.entityID===target.id&&x.text.includes('tipped over'));
  row.historicalGenuinelyWitnessedTippingIsNotCurrentState=
   watched.witnessedEvents.filter(x=>x.text.includes('tipped over')).length;
  row.everPhysicallyRayVisible=visibleAtEnd!==far;
  if(row.distantUnexpectedEvents||!row.sourceCurrentStillUpright||!row.currentSemanticTextNoFalseTipped||!row.historyCurrentPartitionLossless)
   throw Error('An observer received false physical state or unseen event');
  const saved=JSON.parse(JSON.stringify(story.snapshot()));
  const reloaded=PRSESourceRevision.restore(saved);
  if(!reloaded.ok)throw Error('Native GameCore/observer/source save rejected: '+reloaded.reason);
  restored=reloaded.story;
  const repeated=restored.read('autofollow-witness',visibleAtEnd,{radius:12});
  row.duplicateHistoricalEvents=repeated.witnessedEvents.length;
  row.originalSourceTextPreserved=restored.sourceArchive().originalText===p.text;
  row.originalNativeBodyIdentity=restored.loop.entities.has(target.id);
  if(row.duplicateHistoricalEvents||!row.originalSourceTextPreserved||!row.originalNativeBodyIdentity)
   throw Error('Prior delivered native event/source record was repeated or lost after reentry');
  row.status='evaluated';
 }catch(e){row.status='failed';row.reason=String(e.message).slice(0,210);}
 finally{restored?.dispose();story?.dispose();}
 rows.push(row);
}
const valid=rows.filter(x=>x.status==='evaluated');
const summary={
 existingKnownBadSourceConditions:11,
 actualGameCoreNativeSourceActionsVerified:valid.length,
 testFailures:rows.length-valid.length,
 witnessedRealNativeRightedEventsViaPhysicalEventTimeRay:valid.reduce((n,x)=>n+x.witnessedRightings,0),
 actualEventTimeTippingWitnesses:valid.reduce((n,x)=>n+x.witnessedTippings,0),
 unseenEventLeaksToDistantObserver:valid.reduce((n,x)=>n+x.distantUnexpectedEvents,0),
 sourceCurrentTextFalseTipped:valid.filter(x=>!x.currentSemanticTextNoFalseTipped).length,
 sourcePrivateOriginalsRestored:valid.filter(x=>x.originalSourceTextPreserved).length,
  historyAndCurrentFactChannelsLosslessInOriginalWrongCases:valid.filter(x=>x.historyCurrentPartitionLossless).length,
 nativeFinalPoseDivergencesWithAttachedObserver:rows.filter(x=>x.observerMayHaveAlteredPhysicalTrajectory).length,
 previouslyWitnessedEventsRepeatedAfterNativeSave:valid.reduce((n,x)=>n+x.duplicateHistoricalEvents,0),
 caveat:'Auto-following real-occlusion-tested spectator is a synthetic observer harness, NOT a human visual/perceptual source label'};
const raw=dir+'/prse_corrected_righted_event_observer_delivery_11_raw_'+version+'.json';
const obj={metadata:{
 source:'Same eleven previously false tipped original source-derived actual Rapier worlds, one native physical action per case',
 sourceGoldNotLoaded:true,trackingSpectatorSyntheticButPhysicalVisibilityRay:true,
 historicalEventAndCurrentStateSeparated:version!=='v1',
 noUserCameraOrRealHumanObserver:true},summary,rows};
writeFileSync(raw,JSON.stringify(obj,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_corrected_righted_witness_11_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...obj.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(raw)).digest('hex')},
 summary,sourceStatus:rows.map(x=>({sourceId:x.sourceId,action:x.action,status:x.status,
 watchedRighting:x.witnessedRightings||0,failedReason:x.reason||null}))},null,2)+'\n',{flag:'wx'});
console.log('EVENT_TIME_RAPIER_RAY_WITNESS',JSON.stringify(summary));
