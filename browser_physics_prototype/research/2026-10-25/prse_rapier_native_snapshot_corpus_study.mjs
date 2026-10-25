// Independent solver-level matched serialization comparison across the SAME
// 63 source-derived dynamic PRSE scenes used by earlier observer/offscreen work.
//
// Input geometry, body IDs, impulses, active GameCore Rapier physics state and
// step schedule are frozen. After serializing at tick150, three alternatives:
//   - original still-loaded Rapier solver,
//   - native binary Rapier World restore,
//   - current PRSE JSON body reconstruction.
// Then run identical two actual RAPIER physics impulses and 210 solver steps.
//
// This isolates whether retaining internal Rapier world state reduces later
// contact divergence. It does NOT replay all GameCore character, semantic,
// observer or narrative processes after the snapshot.
import RAPIER from '../../vendor/rapier.es.js';
import {writeFileSync,readFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';

await initializePhysics();
const base='/data/var/games/prse_semantic_research/runs/2026-10-25-offscreen-motion';
mkdirSync(base,{recursive:true,mode:0o700});
const corpus=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const previous=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility/prse_observer_event_batch_200_raw_v2.json'));
const selected=previous.rows.filter(r=>r.status==='evaluated');
if(selected.length!==63)throw Error('Expected frozen external source selection changed');
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const qdist=(a,b)=>2*Math.acos(Math.min(1,Math.max(-1,Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w))));
function difference(ref,other){
 return {positionMeters:dist(ref.translation(),other.translation()),
  velocityMetersPerSecond:dist(ref.linvel(),other.linvel()),
  orientationRadians:qdist(ref.rotation(),other.rotation())};
}
const physicalActions=[
 {tick:150,impulse:{x:4,y:1.1,z:1.5},advance:110},
 {tick:260,impulse:{x:-1.6,y:.45,z:1},advance:100}
];
const start=performance.now(),cases=[];
for(let index=0;index<selected.length;index++){
 const item=selected[index],input=corpus[+item.id],plan=repairScene(input,{maxSweeps:2,maxAttemptsPerScene:150});
 const record={id:item.id,subset:item.sourceType,kind:item.chosenCategory,status:'started'};
 let original=null,reconstructed=null,binaryA=null,binaryB=null;
 try{
  if(!plan.accepted)throw Error('Previously verified physical source scene no longer accepted');
  original=new PRSELoop(plan.scene);original.tick(18);
  const target=plan.scene.entities.find(e=>e.kind===item.chosenCategory&&e.body==='dynamic');
  if(!target)throw Error('Original dynamic target missing');
  original.applyImpulse(target.id,{x:1.1,y:.35,z:.55});original.tick(150);
  const binaryData=original.game.world.takeSnapshot();
  const structuredData=original.snapshot();
  binaryA=RAPIER.World.restoreSnapshot(binaryData);
  binaryB=RAPIER.World.restoreSnapshot(binaryData);
  const load=PRSELoop.restore(JSON.parse(JSON.stringify(structuredData)));
  if(!load.ok)throw Error('JSON wrapper restore failed');
  reconstructed=load.loop;
  const bodyHandle=original.active.get(target.id).handle;
  const rawBodies=[
    original.active.get(target.id),
    binaryA.getRigidBody(bodyHandle),binaryB.getRigidBody(bodyHandle),
    reconstructed.active.get(target.id)
  ];
  if(rawBodies.some(b=>!b))throw Error('Physical body handle was not preserved by native binary snapshot');
  record.nativeBinaryBytes=binaryData.length;
  record.structuredJSONBytes=Buffer.byteLength(JSON.stringify(structuredData));
  record.dynamicBodies=[...original.active].filter(([id,b])=>b.isDynamic()).length;
  record.initialBinaryDeviation=difference(rawBodies[0],rawBodies[1]).positionMeters;
  record.initialJSONDeviation=difference(rawBodies[0],rawBodies[3]).positionMeters;
  record.stages=[];
  for(const action of physicalActions){
   for(const b of rawBodies)b.applyImpulse(action.impulse,true);
   for(let i=0;i<action.advance;i++){
    original.game.world.step();binaryA.step();binaryB.step();reconstructed.game.world.step();
   }
   record.stages.push({afterTick:action.tick+action.advance,
    binaryVsLive:difference(rawBodies[0],rawBodies[1]),
    secondBinaryVsLive:difference(rawBodies[0],rawBodies[2]),
    binaryReplicas:difference(rawBodies[1],rawBodies[2]),
    JSONVsLive:difference(rawBodies[0],rawBodies[3])});
  }
  record.status='evaluated';
 }catch(e){record.status='failed';record.reason=String(e?.message||e).slice(0,190);}
 finally{binaryA?.free();binaryB?.free();reconstructed?.dispose();original?.dispose();}
 cases.push(record);
 if((index+1)%10===0)console.log('PROGRESS',index+1,'of',selected.length);
}
const good=cases.filter(x=>x.status==='evaluated');
const threshold=.02;
const summary={
 sourceScenes:cases.length,evaluated:good.length,failed:cases.length-good.length,
 nativeBinaryMuchBetter:good.filter(r=>r.stages.at(-1).binaryVsLive.positionMeters+.001<r.stages.at(-1).JSONVsLive.positionMeters).length,
 JSONMuchBetter:good.filter(r=>r.stages.at(-1).JSONVsLive.positionMeters+.001<r.stages.at(-1).binaryVsLive.positionMeters).length,
 nativeBinaryAbove2cm:good.filter(r=>r.stages.at(-1).binaryVsLive.positionMeters>threshold).length,
 structuredJSONAbove2cm:good.filter(r=>r.stages.at(-1).JSONVsLive.positionMeters>threshold).length,
 binaryReplicaAbove2cm:good.filter(r=>r.stages.at(-1).binaryReplicas.positionMeters>threshold).length,
 medianNativeBinaryBytes:good.length?good.map(r=>r.nativeBinaryBytes).sort((a,b)=>a-b)[Math.floor(good.length/2)]:null,
 medianStructuredJSONBytes:good.length?good.map(r=>r.structuredJSONBytes).sort((a,b)=>a-b)[Math.floor(good.length/2)]:null,
 maxBinaryErrorMeters:good.length?Math.max(...good.map(r=>r.stages.at(-1).binaryVsLive.positionMeters)):null,
 maxJSONErrorMeters:good.length?Math.max(...good.map(r=>r.stages.at(-1).JSONVsLive.positionMeters)):null,
 elapsedSeconds:+((performance.now()-start)/1000).toFixed(2)};
const payload={
 metadata:{sample:'Exactly 63 frozen SceneEval source IDs previously eligible in physical observer study',
 sourceAnnotationsNotRead:true,noGPUorLLM:true,
 solver:'Actual GameCore Rapier binary snapshot vs current PRSE structured JSON reconstruction',
 caveat:'Solver-only replay. Semantic/character/offscreen core ticks not evaluated after serialization, no human participants.',
 actionTicks:[150,260],singleFixedModerateAndTwoScheduledRealRapierImpulses:true},
 summary,cases};
const file=base+'/prse_rapier_native_snapshot_63_raw_v1.json';
writeFileSync(file,JSON.stringify(payload,null,2)+'\n',{flag:'wx',mode:0o600});
const safe={
 metadata:{...payload.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(file)).digest('hex'),
  privateRawFile:file},
 summary,
 cases:cases.map(x=>({
  id:x.id,subset:x.subset,kind:x.kind,status:x.status,
  binaryDeviation:x.stages?.at(-1)?.binaryVsLive.positionMeters??null,
  JSONDeviation:x.stages?.at(-1)?.JSONVsLive.positionMeters??null,
  twoNativeCopiesDeviation:x.stages?.at(-1)?.binaryReplicas.positionMeters??null,
  error:x.reason||null
 }))};
writeFileSync(new URL('prse_rapier_native_snapshot_63_aggregate_v1.json',import.meta.url),
 JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log('FINAL',JSON.stringify(summary));
