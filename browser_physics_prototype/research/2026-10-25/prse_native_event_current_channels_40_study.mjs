// PRSE actual-source observer correctness — independent fixed-sample control
// AFTER correcting native tipping/event-time versus CURRENT world semantics.
//
// Predeclared distinct external SceneEval source rooms that were NOT among
// the eleven prior selected false-tipping regressions, one physical action
// per source selected by source ID modulo 4, rather than by desired success.
// Same authoritative GameCore/Rapier, event subscriber, ray-visible observer,
// distant control observer, current world text and native source/observer save.
//
// Measured endpoints: real current up-axis tilt, event-time tilt for tipped/
// righted, precise observer-visible current text, event provenance and no
// hidden physical cause leakage. This is NOT a pristine new source corpus,
// human literary-quality test or independent original source annotation.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Invalid exclusive output version');
mkdirSync(ROOT,{recursive:true,mode:0o700});
const eligible=JSON.parse(readFileSync(ROOT+'/prse_native_orientation_support_audit_197x4_raw_v1.json')).rows;
const prior=JSON.parse(readFileSync(ROOT+'/prse_native_tipped_event_vs_orientation_256_raw_v1.json')).rows;
const reserved=new Set(prior.filter(r=>r.semanticTippedButCurrentlyUprightAtEnd).map(r=>r.sourceId));
const sources=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const vectors=[{name:'east_up',x:4,y:1.1,z:.5},
 {name:'west_up',x:-4,y:1.1,z:.5},
 {name:'south_up',x:.5,y:1.1,z:4},
 {name:'north_low',x:1.2,y:.9,z:-3.5}];
const ids=[...new Set(eligible.filter(r=>r.status==='measured'&&r.movedBodyId&&!reserved.has(r.sourceId))
 .map(r=>r.sourceId))].sort((a,b)=>a-b).slice(0,40);
if(ids.length!==40)throw Error('Insufficient externally sourced distinct control scene count');
const far={x:0,y:1.6,z:0};
const upright=q=>{
 const norm=Math.hypot(q.x,q.y,q.z,q.w);
 return Math.acos(Math.max(-1,Math.min(1,1-2*(q.x*q.x+q.z*q.z)/(norm*norm))));
};
function findEye(story,e){
 for(const d of [1.4,2.2,3.5,5.5]){
  for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,-1],[1,-1],[-1,1]]){
   const pos={x:e.position.x+dx*d,y:Math.max(1.5,e.position.y+1.3),z:e.position.z+dz*d};
   if(story.perception.isVisible(e.id,pos,{radius:12,mode:'ray'}).visible)return pos;
  }
 }
 return null;
}
const rows=[];
for(const id of ids){
 const p=sources[id],action=vectors[id%4],layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 let story=null,restored=null;
 const row={sourceId:id,action:action.name,status:'started',nativeTypedEvents:[],
  rayObserverInitiallyVisible:false};
 try{
  if(!layout.accepted||geometryIssues(layout.scene).length)throw Error('Selected original scene geometry no longer accepted');
  const loop=new PRSELoop(layout.scene);loop.tick(36);
  const on=p.relations.filter(r=>r.kind==='object'&&r.type==='on');
  const selected=on.find(r=>{
   const t=loop.scene.entities.filter(e=>e.kind===r.a&&e.source!=='provisional_3D_room_boundary');
   return t.length===1&&t[0].body==='dynamic';
  });
  const moving=selected?loop.scene.entities.find(e=>e.kind===selected.a):
   loop.scene.entities.find(e=>e.body==='dynamic'&&!e.state.destroyed);
  if(!moving)throw Error('Selected scene has no native dynamic body');
  story=new PRSESourceRevision(loop,[],{observerRadius:12});
  const eye=findEye(story,moving);
  row.rayObserverInitiallyVisible=Boolean(eye);
  if(eye)story.read('near-observer',eye,{radius:12});
  story.read('far-observer',far,{radius:12});
  const stopEventListener=loop.subscribeEvents(ev=>{
   if(!['tipped','righted'].includes(ev.type))return;
   const rb=loop.active.get(ev.ids[0]),entity=loop.entities.get(ev.ids[0]);
   if(!rb||!entity)throw Error('Native event on absent body');
   row.nativeTypedEvents.push({sequence:ev.sequence,type:ev.type,
    id:ev.ids[0],actualUpTilt:upright(rb.rotation()),worldTime:loop.time});
  });
  const stopNear=eye?story.attachObserver('near-observer',()=>eye,{radius:12}):()=>{};
  const stopFar=story.attachObserver('far-observer',()=>far,{radius:12});
  if(!loop.applyImpulse(moving.id,action))throw Error('Native physics source action refused');
  loop.tick(160);
  stopEventListener();stopNear();stopFar();
  row.nativeFinalBodyCount=loop.active.size;
  const returnEye=eye||far;
  const near=eye?story.read('near-observer',returnEye,{radius:12}):{
   witnessedEvents:[],visibleCurrentStates:[],relationRevisions:[],visibleEntityIDs:[]};
  const distant=story.read('far-observer',far,{radius:12});
  const exposedEventIDs=new Set(near.witnessedEvents.map(x=>x.eventSequence));
  const actualEventIds=new Set(loop.events.map(x=>x.sequence));
  row.noLossFromTypedHistoricalEventCurrentFactPartition=eye &&
   JSON.stringify([...near.witnessedEventSentences,...near.currentWorldFactSentences])===
     JSON.stringify(near.narrationSentences)&&
   JSON.stringify(near.narrationSentences)===JSON.stringify(near.currentSentences)&&
   near.legacyCurrentSentencesMixesHistoryAndCurrentFacts===true;
  row.witnessedEventSentencesCount=eye?near.witnessedEventSentences.length:0;
  row.currentWorldFactSentencesCount=eye?near.currentWorldFactSentences.length:0;
  row.nearWitnessedEventCount=near.witnessedEvents.length;
  row.nearWitnessedTipped=near.witnessedEvents.filter(x=>x.text.includes('tipped over')).length;
  row.nearWitnessedRighted=near.witnessedEvents.filter(x=>x.text.includes('became upright again')).length;
  row.farWitnessedEvents=distant.witnessedEvents.length;
  row.witnessedEventProvenanceValid=[...exposedEventIDs].every(seq=>actualEventIds.has(seq));
  row.nativeTippedEvents=row.nativeTypedEvents.filter(x=>x.type==='tipped').length;
  row.nativeRightedEvents=row.nativeTypedEvents.filter(x=>x.type==='righted').length;
  row.nativeEventInvalidAtEventTime=row.nativeTypedEvents.filter(x=>
   (x.type==='tipped'&&x.actualUpTilt<=.7)||
   (x.type==='righted'&&x.actualUpTilt>=.12)).length;
  row.nearCurrentClaimsDisagreeWithNativeTilt=0;
  row.nearCurrentObjectsChecked=0;
  for(const fact of near.visibleCurrentStates){
   const e=loop.entities.get(fact.entityID);
   const body=loop.active.get(fact.entityID);
   if(!e||!body)throw Error('Narrator stated current source fact for absent body');
   row.nearCurrentObjectsChecked++;
   const actual=upright(body.rotation());
   const tippedFact=/\btipped(?: over)?\b/.test(fact.text);
   if(tippedFact&&actual<.12)row.nearCurrentClaimsDisagreeWithNativeTilt++;
   if(tippedFact&&!e.state.tipped)row.nearCurrentClaimsDisagreeWithNativeTilt++;
  }
  if(row.nativeEventInvalidAtEventTime||!row.witnessedEventProvenanceValid||
    !row.noLossFromTypedHistoricalEventCurrentFactPartition||
    row.nearCurrentClaimsDisagreeWithNativeTilt||row.farWitnessedEvents)
   throw Error('Actual Rapier/native event or witness source statement inconsistency');
  const ss=JSON.parse(JSON.stringify(story.snapshot()));
  const loaded=PRSESourceRevision.restore(ss);
  if(!loaded.ok)throw Error('Native GameCore/semantic/physical observer save refused: '+loaded.reason);
  restored=loaded.story;
  const repeated=eye?restored.read('near-observer',returnEye,{radius:12}):{
   witnessedEvents:[],currentSentences:[]};
  row.repeatedEventDelivery=repeated.witnessedEvents.length;
  row.fullNativeWorldOriginalSourceAndIDsRestored=
   restored.sourceArchive().originalText===p.text&&
   restored.loop.active.has(moving.id);
  if(row.repeatedEventDelivery||!row.fullNativeWorldOriginalSourceAndIDsRestored)
   throw Error('Native replay repeated witnessed event or lost authoritative source objects');
  row.status='native_source_event_observer_verified';
 }catch(e){row.status='failed';row.reason=String(e.message).slice(0,210);}
 finally{restored?.dispose();story?.dispose();}
 rows.push(row);
}
const good=rows.filter(r=>r.status==='native_source_event_observer_verified');
const sum=f=>good.reduce((n,r)=>n+f(r),0);
const summary={
 frozenDistinctNonRegressionSourceScenes:ids.length,
 actualGameCoreSourceSceneActionsVerified:good.length,
 scientificFailures:rows.filter(x=>x.status==='failed').length,
 nativeTypedTippedEvents:sum(x=>x.nativeTippedEvents),
 nativeTypedRightedEvents:sum(x=>x.nativeRightedEvents),
 actuallyRayWitnessedPhysicalEvents:sum(x=>x.nearWitnessedEventCount),
 actuallyRayWitnessedTippedEvents:sum(x=>x.nearWitnessedTipped),
 actuallyRayWitnessedRightedEvents:sum(x=>x.nearWitnessedRighted),
 nativeEventTimeRotationContradictions:sum(x=>x.nativeEventInvalidAtEventTime),
 currentlyVisibleObjectFactsIndependentlyChecked:sum(x=>x.nearCurrentObjectsChecked),
 currentlyVisibleTippedFactsContradictNativeUpAxis:sum(x=>x.nearCurrentClaimsDisagreeWithNativeTilt),
 unseenEventsLeakedToDistantObserver:sum(x=>x.farWitnessedEvents),
 duplicateWitnessEventsAfterSave:sum(x=>x.repeatedEventDelivery),
 originalSourceAndGameCoreNativeWorldPreservedAfterSave:sum(x=>Number(x.fullNativeWorldOriginalSourceAndIDsRestored)),
  nativeHistoricalEventsAndCurrentWorldFactChannelsExactlyPartitioned:sum(x=>Number(x.noLossFromTypedHistoricalEventCurrentFactPartition)),
  historicalEventSentencesOutput:sum(x=>x.witnessedEventSentencesCount),
  currentFactSentencesOutput:sum(x=>x.currentWorldFactSentencesCount),
 firstRaySightAvailable:sum(x=>Number(x.rayObserverInitiallyVisible)),
 sourceGoldNeverLoaded:true,
 selectionCaveat:'Previously exposed SceneEval external source corpus; 40 distinct source rooms fixed by ID, deliberately excluding earlier targeted 11, not a fresh literary evaluation'};
const DIR='/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit';
mkdirSync(DIR,{recursive:true,mode:0o700});
const path=DIR+'/prse_event_and_current_channels_40_raw_'+version+'.json';
const content={metadata:{
 source:'Forty predefined previously unselected external source SceneEval real physics rooms, one fixed GameCore action per source',
 exactSourceIDs:ids,sourceOriginalProseNotPublished:true,
 method:'Native physical event-time vs true ray-observed event delivery vs independently checked present-tense current state and native full save',
 caveat:'This tests event/current truth boundary, not the human-authored original source scene geometry correctness, fluency, or human camera behavior'},
 summary,rows};
writeFileSync(path,JSON.stringify(content,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_event_current_observer_new_40_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...content.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(path)).digest('hex')},
 summary,
 failures:rows.filter(x=>x.status==='failed').map(x=>({id:x.sourceId,reason:x.reason}))},null,2)+'\n',{flag:'wx'});
console.log('PRSE_FORTY_SOURCE_UNSELECTED_OBSERVER_CURRENT_HISTORY',JSON.stringify(summary));
