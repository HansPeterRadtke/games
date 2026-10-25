// PRSE research-only event-time physical orientation fidelity audit.
//
// The native GameCore *current* state uses sticky e.state.tipped and emits
// "tipped" when total quaternion rotation angle exceeds 0.7 radians.
// However total quaternion rotation includes pure YAW: an upright cuboid may
// turn around the world vertical axis without tipping. Likewise a body may
// tip and later stand upright, so historic "tipped" cannot prove its CURRENT
// orientation. This audit compares genuine Rapier transforms at the EXACT
// first emitted tipped event and after 160 real physics steps.
//
// Frozen external SceneEval source-derived cases and FOUR predeclared native
// impulse vectors from the previous immutable full 197x4 support audit;
// only real dynamic cases need be simulated. No independent gold source
// labels, no synthetic scripted teacher, no GPU, no live game changes.
//
// Source-independent neutral physical error category: "tipped" event claims
// but rigid-body local-up tilt <0.7 (including yaw-only false positives).
// This is an ACTUAL SEMANTIC EVENT accuracy test, not a quality rating.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Invalid evidence version');
mkdirSync(ROOT,{recursive:true,mode:0o700});
const previous=JSON.parse(readFileSync(ROOT+'/prse_native_orientation_support_audit_197x4_raw_v1.json')).rows;
const scenarios=previous.filter(r=>r.status==='measured'&&r.movedBodyId);
const inputs=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const vectors={east_up:{x:4,y:1.1,z:.5},
 west_up:{x:-4,y:1.1,z:.5},south_up:{x:.5,y:1.1,z:4},
 north_low:{x:1.2,y:.9,z:-3.5}};
if(scenarios.length!==256)throw Error('Real dynamic source-case count changed from frozen prior audit');
const tiltAngle=q=>{
 const n=Math.hypot(q.x,q.y,q.z,q.w);
 if(n<.5||!Number.isFinite(n))throw Error('Invalid native body rotation');
 const x=q.x/n,z=q.z/n;
 return Math.acos(Math.max(-1,Math.min(1,1-2*(x*x+z*z))));
};
const totalAngle=q=>{
 const n=Math.hypot(q.x,q.y,q.z,q.w);
 return 2*Math.acos(Math.max(-1,Math.min(1,Math.abs(q.w/n))));
};
const rows=[],start=performance.now();
for(let k=0;k<scenarios.length;k++){
 const x=scenarios[k],p=inputs[x.sourceId],impulse=vectors[x.impulse];
 const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!impulse||!layout.accepted||geometryIssues(layout.scene).length)
  throw Error('Prior accepted real action/source unexpectedly invalid');
 let l=null;
 const row={sourceId:x.sourceId,action:x.impulse,status:'started',
  firstTippedEvents:[],initialDynamicCount:0,currentTippedAtEnd:0,
  physicallyTiltedAtEnd:0,semanticTippedButCurrentlyUprightAtEnd:0};
 try{
  l=new PRSELoop(layout.scene);l.tick(36);
  const dynamic=l.scene.entities.filter(e=>e.body==='dynamic'&&!e.state?.destroyed&&e.shape!=='sphere');
  row.initialDynamicCount=dynamic.length;
  if(!l.applyImpulse(x.movedBodyId,impulse))
   throw Error('Predeclared physical intervention impossible in current GameCore');
  for(let t=0;t<160;t++){
   const before=l.nextSeq;
   l.tick(1);
   const newEvents=l.events.filter(e=>e.sequence>=before&&e.type==='tipped');
   for(const ev of newEvents){
    const entity=l.entities.get(ev.ids[0]),body=l.active.get(ev.ids[0]);
    if(!body||!entity||entity.shape==='sphere')throw Error('Tipped event without real non-sphere physical body');
    const up=tiltAngle(body.rotation()),all=totalAngle(body.rotation());
    row.firstTippedEvents.push({entityId:entity.id,type:entity.kind,tick:t,
     physicallyMeasuredUpTiltRadians:up,quaternionTotalRotationRadians:all,
     actuallyReachedPhysicalTippingThreshold:up>.7,
     historicalEventType:ev.type});
   }
  }
  row.finalBodyPositions=[];
  for(const e of dynamic){
   const b=l.active.get(e.id),up=tiltAngle(b.rotation()),all=totalAngle(b.rotation());
   if(up>.7)row.physicallyTiltedAtEnd++;
   if(e.state.tipped)row.currentTippedAtEnd++;
   if(e.state.tipped&&up<.12)row.semanticTippedButCurrentlyUprightAtEnd++;
   row.finalBodyPositions.push({id:e.id,kind:e.kind,
    nativeUpTiltRadians:up,nativeTotalRotationRadians:all,
    semanticStickyTipped:e.state.tipped,
    semanticCurrentProseClaimsTipped:e.state.tipped?'is tipped over':null});
  }
  row.status='measured';
 }catch(e){row.status='failed';row.reason=String(e.message).slice(0,240);}
 finally{l?.dispose();}
 rows.push(row);
 if((k+1)%32===0)console.log('ORIENTATION_EVENT_PROGRESS',k+1,'of',scenarios.length);
}
const good=rows.filter(r=>r.status==='measured'),allEvents=good.flatMap(r=>r.firstTippedEvents);
const num=f=>good.reduce((n,x)=>n+f(x),0);
const summary={
 frozenExternalSceneAndActualActionConditions:scenarios.length,
 successfullyMeasuredRealNativeActionCases:good.length,
 executionErrors:rows.filter(x=>x.status==='failed').length,
 emittedHistoricalTippedEvents:allEvents.length,
 eventsWhereNativeBodyNotActuallyTiltedPastOriginalThreshold:allEvents.filter(x=>!x.actuallyReachedPhysicalTippingThreshold).length,
 eventsWithNativeUpTiltLessThanTwelveHundredthsRad:allEvents.filter(x=>x.physicallyMeasuredUpTiltRadians<.12).length,
 recordedStickyTippedCurrentEntityAtEnd:num(x=>x.currentTippedAtEnd),
 actuallyTiltedNativeBodiesAtEnd:num(x=>x.physicallyTiltedAtEnd),
 currentSemanticTippedButNativeBodyUprightAtEnd:num(x=>x.semanticTippedButCurrentlyUprightAtEnd),
 maxEventTotalAngularVsActualTiltDifference:allEvents.length?
  Math.max(...allEvents.map(x=>x.quaternionTotalRotationRadians-x.physicallyMeasuredUpTiltRadians)):null,
 wallSeconds:+((performance.now()-start)/1000).toFixed(2),
 scope:'Native actual orientations, event-time labels and post-event current-state physical truth, not source-language semantics'};
const raw=ROOT+'/prse_native_tipped_event_vs_orientation_256_raw_'+version+'.json';
writeFileSync(raw,JSON.stringify({metadata:{
 method:'Exact actual authoritative GameCore tipping event at tick and native Rapier local Y-axis upright test on same frozen source-derived dynamic scenes',
 originalThresholdRadians:.7,actualUpAxisThreshold:.7,
 physicalInputs:vectors,sourceGoldLabelsNeverRead:true,
 physicalBodyEndStateNeverAssumedHistoricalEventStillCurrent:true},summary,rows},null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_native_tipped_event_orientation_256_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{privateRawSHA256:createHash('sha256').update(readFileSync(raw)).digest('hex'),
  benchmark:'Same frozen 64 external SceneEval physically active source rooms under four real GameCore impulses',
  warning:'Native rotation test is physically grounded but not arbitrary realistic articulated object behavior'},
  summary,
  errors:rows.filter(r=>r.firstTippedEvents.some(x=>!x.actuallyReachedPhysicalTippingThreshold)||
   r.semanticTippedButCurrentlyUprightAtEnd).map(r=>({
    sourceId:r.sourceId,action:r.action,
    falseTippedEvents:r.firstTippedEvents.filter(x=>!x.actuallyReachedPhysicalTippingThreshold).length,
    stickyCurrentTippedDespiteNativeUpright:r.semanticTippedButCurrentlyUprightAtEnd}))},null,2)+'\n',{flag:'wx'});
console.log('NATIVE_GAMECORE_PHYSICAL_TIPPING_ACCURACY',JSON.stringify(summary));
