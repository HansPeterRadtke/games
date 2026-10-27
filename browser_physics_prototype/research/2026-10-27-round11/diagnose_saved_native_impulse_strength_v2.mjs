// Round eleven: NEW post-save causal continuation consistency experiment.
// Reconstruct three already-frozen SOURCE-ONLY human room worlds with
// unchanged source/body IDs, sizes, category and primitive colliders, validate
// against previous frozen real GameCore/Rapier 38-tick state, then branch:
// (A) uninterrupted native GameCore, (B) trusted actual native binary restore,
// (C) older structured JSON-only restore. Compare next real native physics.
//
// This is NOT the earlier DENIED random feasible-support-parent placebo.
// This is NOT the previously BLOCKED full observer/offscreen literary study.
// No user game, GPU, model services, production port or other checkout touched.
// Human source annotations are not opened by this experiment; all author
// sentences, source-only manifests and previous native poses are FROZEN.
// No assertion of metric/mesh/observer-literary quality from provisional boxes.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {object,PRSELoop,validateScene,geometryIssues} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {recordNativePRSEState,restoreNativePRSEState} from '../2026-10-25/prse_native_world_transaction.mjs';
await initializePhysics();
const PRIVATE='/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round11-causal-restore';
const PREV='/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round9-room-contract';
const PREVIOUS=PREV+'/room_source_to_native_to_factual_text_v3_raw_v2.json';
const FROZEN=PREV+'/source_original_strict_room_proposal_frozen_v3.json';
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=JSON.parse(readFileSync(FROZEN));
const prev=JSON.parse(readFileSync(PREVIOUS));
if(sources.cases.length!==3||prev.cases.length!==3||sources.summary.sourcePositiveNativeObjectInstancesPlanned!==17||
 !sources.metadata.humanOfficialLabelsAndReferenceRoomsNeverReadBySourceProposals||
 !prev.metadata.goldLabelsNeverReadInGeneration)
 throw Error('Previously frozen original author-source/native input incomplete');
const SIZE={x:.9,y:.8,z:.9}, regionW=18,regionZ=14,centerZ=42;
const vecDist=(a,b)=>Math.hypot(...['x','y','z'].map(k=>a[k]-b[k]));
function makeScene(c){
 const entities=[],rooms=new Map();
 c.roomNames.forEach((room,i)=>{
  const centerX=(i-(c.roomNames.length-1)/2)*26;
  rooms.set(room,{centerX,centerZ});
  for(let gx=0;gx<3;gx++)for(let gz=0;gz<2;gz++){
   const id='s'+c.sceneIndex+'-room-floor-'+room.replaceAll('_','-')+'-tile-'+gx+'-'+gz;
   const e=object(id,'room_floor',
    {x:centerX+(gx-1)*6,y:-.055,z:centerZ+(gz-.5)*7},
    {x:6,y:.11,z:7},
    {body:'fixed',shape:'box',mass:1,material:'unknown',
     name:'provisional room floor '+room+' tile '+gx+','+gz,
     description:'Physical 3D spatial platform only; source room topology, walls, doors and appearance unverified',
     source:'author-room-name-only; geometry uncalibrated',
     state:{condition:'intact',provisionalRoomGeometry:true}});
   e.supportId=null;e.roomId=room;
   e.sourceRoomEvidence='literal original author room enumeration';
   entities.push(e);
  }
 });
 const counts=new Map();
 for(const req of c.positiveRoomKinds){
  const r=rooms.get(req.roomId);
  if(!r||req.geometryCertified!==false||req.sourceRoomIdentityCertifiedByExactText!==true)
   throw Error('Source-only original room/asset source authority unproven');
  for(let j=0;j<req.count;j++){
   const q=counts.get(req.roomId)||0;
   const id='s'+c.sceneIndex+'-'+req.roomId.replaceAll('_','-')+'-'+req.kind.replaceAll('_','-')+'-'+j;
   const e=object(id,req.kind,
     {x:r.centerX-4.25+(q%4)*2.6,y:SIZE.y/2,z:r.centerZ-2.65+Math.floor(q/4)*2.7},
     SIZE,{body:'dynamic',shape:'box',mass:1,material:'unknown',
       name:'provisional '+req.kind+' in '+req.roomId,
       source:'original-author-positive:'+req.sourceCharOffsets.join('-'),
       description:'Literal source-linked instance, but asset scale, visual shape and material NOT independently validated',
       state:{condition:'intact',sourceKindRecognized:true,geometryNotSourceCertified:true}});
   e.roomId=req.roomId;e.sourceClauseHash=req.sourceClauseSHA256;e.provisionalGeometry=true;e.sourceSemanticQuantity=req.count;
   entities.push(e);
   counts.set(req.roomId,q+1);
  }
 }
 const scene={id:'source-room-'+c.sceneIndex+'-v3',prose:c.sourceText,entities};
 if(!validateScene(scene).ok||geometryIssues(scene).length)
  throw Error('Independent reproduction of previous GameCore world failed schema/geometry');
 return {scene,rooms};
}
function realContacts(loop){
 const found=[];
 for(const [id,a] of loop.active)for(const [other,b] of loop.active){
  if(id>=other)continue;
  let n=0;
  for(let i=0;i<a.numColliders();i++)for(let j=0;j<b.numColliders();j++)
    loop.game.world.contactPair(a.collider(i),b.collider(j),m=>n+=m.numContacts());
  if(n>0)found.push([id,other,n]);
 }
 return found.sort((a,b)=>(a[0]+a[1]).localeCompare(b[0]+b[1]));
}
function physical(loop){
 const bodies=[];
 for(const e of loop.scene.entities){
  const native=loop.active.get(e.id);
  if(!native)throw Error('Trusted GameCore physical object missing '+e.id);
  bodies.push({id:e.id,kind:e.kind,roomId:e.roomId,
   position:{...native.translation()},velocity:{...native.linvel()},
   rotation:{...native.rotation()},dimensions:{...e.size},
   isDynamic:native.isDynamic(),originalSourceHash:e.sourceClauseHash||null,
   physicalStateIsRealRapier:true});
 }
 return {sourceText:loop.scene.prose,sceneId:loop.scene.id,worldTime:loop.time,
   stepCount:loop.game.stepCount,bodyCount:bodies.length,
   bodies,contactPairs:realContacts(loop)};
}
function compare(before,after){
 const index=new Map(before.bodies.map(b=>[b.id,b]));
 if(index.size!==before.bodies.length||index.size!==after.bodies.length)
  throw Error('Compared world has changed body identities');
 let maxPosition=0,maxVelocity=0,maxRotation=0;
 for(const b of after.bodies){
  const old=index.get(b.id);
  if(!old||b.kind!==old.kind||b.roomId!==old.roomId||
   JSON.stringify(b.dimensions)!==JSON.stringify(old.dimensions))
   throw Error('Scene changed entity source provenance/body ID, type or size');
  maxPosition=Math.max(maxPosition,vecDist(old.position,b.position));
  maxVelocity=Math.max(maxVelocity,vecDist(old.velocity,b.velocity));
  maxRotation=Math.max(maxRotation,Math.hypot(...['x','y','z','w'].map(k=>old.rotation[k]-b.rotation[k])));
 }
 const mk=p=>p.map(x=>x.slice(0,2).join('|')).sort();
 return {maximumPositionDifferenceMetres:+maxPosition.toFixed(7),
  maximumVelocityDifference:+maxVelocity.toFixed(7),
  maximumQuaternionDifference:+maxRotation.toFixed(7),
  sourceTextExactlyIdentical:before.sourceText===after.sourceText,
  sourceSceneIDExactlyIdentical:before.sceneId===after.sceneId,
  authoritativeTimeDifferenceSeconds:+Math.abs(after.worldTime-before.worldTime).toFixed(7),
  nativeStepCountEqual:after.stepCount===before.stepCount,
  nativeContactPairIDsIdentical:JSON.stringify(mk(before.contactPairs))===JSON.stringify(mk(after.contactPairs))};
}
function compareToPrevious(now,old,c){
 const prior=old.restoredActualNativeScene;
 if(old.sceneIndex!==c.sceneIndex||old.originalSourceHash!==c.sourceTextSHA256||
    now.sourceText!==c.sourceText||now.bodyCount!==prior.nativeMaterializedAll)
  throw Error('Independent rebuilt initial scene does NOT reproduce frozen scene inventory');
 const ind=new Map(prior.realNativeBodies.map(e=>[e.id,e]));
 if(ind.size!==now.bodyCount)throw Error('Original source body ID inventory has duplicates');
 let maxDiff=0;
 for(const x of now.bodies){
  const y=ind.get(x.id);
  if(!y||y.kind!==x.kind||y.roomId!==x.roomId||
     JSON.stringify(x.dimensions)!==JSON.stringify(y.dimensions))
   throw Error('Independent initial body category/room/id differs from prior saved original');
  maxDiff=Math.max(maxDiff,vecDist(y.position,x.position));
 }
 const contacts=p=>p.map(x=>x.slice(0,2).join('|')).sort().join(',');
 const a=contacts(now.contactPairs),b=contacts(prior.actualNativeInterobjectContacts);
 if(maxDiff>.0005||a!==b)
  throw Error('Independent source-derived reproduction deviated from prior actual native result '+maxDiff+' contact '+(a===b));
 return {previousFrozenGameCoreBodyCountMatched:now.bodyCount,
  maximum3DPositionDifferenceMetres:+maxDiff.toFixed(7),
  originalNativeContactPairsReproducedExactly:true};
}
function spatialRoomGuard(state,c){
 const floorByRoom=new Map();
 for(const r of c.roomNames)floorByRoom.set(r,state.bodies.filter(b=>b.kind==='room_floor'&&b.roomId===r));
 const records=[];
 let incorrectlyClaimed=0,inside=0,outside=0;
 for(const b of state.bodies){
  if(b.kind==='room_floor')continue;
  const floor=floorByRoom.get(b.roomId)||[];
  const minX=Math.min(...floor.map(e=>e.position.x-e.dimensions.x/2));
  const maxX=Math.max(...floor.map(e=>e.position.x+e.dimensions.x/2));
  const minZ=Math.min(...floor.map(e=>e.position.z-e.dimensions.z/2));
  const maxZ=Math.max(...floor.map(e=>e.position.z+e.dimensions.z/2));
  const certified=Boolean(floor.length&&b.position.x>=minX+.01&&b.position.x<=maxX-.01&&
    b.position.z>=minZ+.01&&b.position.z<=maxZ-.01);
  if(certified)inside++;else{outside++;incorrectlyClaimed++}
  records.push({id:b.id,sourceRoom:b.roomId,kind:b.kind,
   truePhysicalLocationInsideSourceRoomRegion:certified,
   physicallyObservedPosition:b.position,
   guardedCurrentText:certified?
    'A '+b.kind+' is physically in the provisional region '+b.roomId+'.':
    'The recorded '+b.kind+' has left its originally assigned region; current room is unverified.'});
 }
 return {inside,outside,naiveRoomMetadataDescriptionsNowStale:incorrectlyClaimed,
  records};
}
const original=performance.now();
const selectedFocus={
  20:{kind:'bed',roomId:'kitchen'},
  26:{kind:'fridge',roomId:'bedroom'},
  40:{kind:'computer',roomId:'guard_control_room'}
};
// Diagnostic varying the STRENGTH of a frozen, same-target physical
// impulse. No feasible-parent placebo and no observer/offscreen operation.
const scenarios=[{name:'low_impulse',impulse:{x:6,y:.5,z:.1},ticks:180},
 {name:'medium_impulse',impulse:{x:14,y:1.0,z:.2},ticks:180},
 {name:'high_impulse',impulse:{x:28,y:2,z:.5},ticks:180}];
function largestSourceBodyDeviation(a,b){
 const t=new Map(b.bodies.map(e=>[e.id,e]));let most=null;
 for(const e of a.bodies){const y=t.get(e.id);const d=vecDist(e.position,y.position);
  if(!most||d>most.metres)most={id:e.id,kind:e.kind,sourceRoom:e.roomId,metres:+d.toFixed(7),
   uninterrupted:e.position,restored:y.position};}
 return most;
}
const rows=[],summary={
  humanSourceScenesPreviouslyFrozen:3,
  pairedNativeBinaryVsUninterruptedScenarios:6,
  expectedNativeBodysAcrossScenes:65,
  originallyProvisionalSourceObjects:17,
  normalizedOriginalSourceFactsReadOnly:true,
  deniedFeasibleRandomParentPlaceboNeverAttempted:true,
  previouslyBlockedObserverOffscreenExperimentNeverAttempted:true,
  productionGPUAndUserSessionsUntouched:true};
for(let i=0;i<sources.cases.length;i++){
 const caseData=sources.cases[i],old=prev.cases[i];
 if(![26,40].includes(caseData.sceneIndex))continue;
 const {scene}=makeScene(caseData);
 for(const scenario of scenarios){
  let continuous=null,native=null,jsonRestore=null;
  const began=performance.now();
  const out={scene:caseData.sceneIndex,
   scenario:scenario.name,sourceSHA256:caseData.sourceTextSHA256,
   status:'started',continuationTicks:scenario.ticks};
  try{
   continuous=new PRSELoop(scene);
   continuous.tick(38);
   const start=physical(continuous);
   out.originalPhysicalWorldReproduction=compareToPrevious(start,old,caseData);
   const nativeSnapshot=recordNativePRSEState(continuous);
   const structuredSnapshot=JSON.parse(JSON.stringify(continuous.snapshot()));
   const nr=restoreNativePRSEState(JSON.parse(JSON.stringify(nativeSnapshot)));
   if(!nr.ok)throw Error('New trusted Rapier binary exact restore rejected '+nr.reason);
   native=nr.loop;
   const jr=PRSELoop.restore(structuredSnapshot);
   if(!jr.ok)throw Error('Existing structured JSON GameCore restore rejected '+jr.reason);
   jsonRestore=jr.loop;
   const restoredNativeStart=physical(native),restoredJSONStart=physical(jsonRestore);
   out.initialNativeRestore=compare(start,restoredNativeStart);
   out.initialLegacyJSONRestore=compare(start,restoredJSONStart);
   const id=caseData.positiveRoomKinds.find(p=>
       p.kind===selectedFocus[caseData.sceneIndex].kind&&
       p.roomId===selectedFocus[caseData.sceneIndex].roomId);
   if(!id)throw Error('Frozen original human source missing chosen causal target kind');
   const focus='s'+caseData.sceneIndex+'-'+id.roomId.replaceAll('_','-')+'-'+id.kind.replaceAll('_','-')+'-0';
   if(!continuous.active.get(focus)?.isDynamic())throw Error('Original native target is not a real dynamic body');
   const before={...continuous.active.get(focus).translation()};
   if(scenario.impulse){
    for(const loop of [continuous,native,jsonRestore]){
     if(!loop.applyImpulse(focus,scenario.impulse))
      throw Error('True isolated native GameCore external impulse refused');
    }
   }
   out.intermediateNativeDeviation=[];
   let advanced=0;
   for(const until of [30,120,180]){
    const n=until-advanced;
    continuous.tick(n);native.tick(n);jsonRestore.tick(n);
    const nowA=physical(continuous),nowB=physical(native),nowC=physical(jsonRestore);
    out.intermediateNativeDeviation.push({tick:until,
     native:compare(nowA,nowB),json:compare(nowA,nowC),
     worstNativeObject:largestSourceBodyDeviation(nowA,nowB),
     worstJSONBody:largestSourceBodyDeviation(nowA,nowC)});
    advanced=until;
   }
   const afterA=physical(continuous),afterB=physical(native),afterC=physical(jsonRestore);
   out.endNativeBinaryVsUninterrupted=compare(afterA,afterB);
   out.endJSONReconstructionVsUninterrupted=compare(afterA,afterC);
   out.realImpulseDisplacementMeters=+vecDist(before,afterA.bodies.find(x=>x.id===focus).position).toFixed(5);
   out.originalSourceTextStillUnchanged=afterA.sourceText===caseData.sourceText;
   out.focusBodyID=focus;
   out.finalNativeContactCount=afterA.contactPairs.length;
   out.finalNativeBinaryContactCount=afterB.contactPairs.length;
   out.finalJSONContactCount=afterC.contactPairs.length;
   out.sourceRoomGuard=spatialRoomGuard(afterB,caseData);
   out.originalAuthoredFullWorldStillNotValidated=true;
   if(!out.originalSourceTextStillUnchanged||
       !out.endNativeBinaryVsUninterrupted.sourceTextExactlyIdentical||
       !out.endNativeBinaryVsUninterrupted.sourceSceneIDExactlyIdentical)
    throw Error('Original source or persistent scene ID changed after true native save');
   out.nativeWithinHalfMillimetre=out.endNativeBinaryVsUninterrupted.maximumPositionDifferenceMetres<=.0005;
   out.nativeContactIDsStable=out.endNativeBinaryVsUninterrupted.nativeContactPairIDsIdentical;
   if(out.realImpulseDisplacementMeters<.5)
    throw Error('Actual source-linked body failed to move after real native impulse');
   out.status='native_future_source_action_divergence_measured';
  }catch(e){
   out.status='failed';out.error=String(e.message).slice(0,300);
  }finally{
   jsonRestore?.dispose();native?.dispose();continuous?.dispose();
  }
  out.elapsedMs=+(performance.now()-began).toFixed(3);
  rows.push(out);
  console.log('ROUND11 TRUE NATIVE POSTSAVE CONTINUATION',out.scene,out.scenario,out.status,
   'motion',out.realImpulseDisplacementMeters,'binary discrepancy',out.endNativeBinaryVsUninterrupted?.maximumPositionDifferenceMetres,
   'json discrepancy',out.endJSONReconstructionVsUninterrupted?.maximumPositionDifferenceMetres,
   'left original source region',out.sourceRoomGuard?.outside,'error',out.error||'');
 }
}
summary.completed=rows.filter(x=>x.status==='native_future_source_action_divergence_measured').length;
summary.failed=rows.filter(x=>x.status==='failed').length;
summary.lowMediumHighPositiveControls=rows.filter(x=>x.status==='native_future_source_action_divergence_measured').length;
summary.physicsNegativeControlsFromPriorFrozenV1=3;
summary.nativeBinaryReplayExactContacts=rows.filter(x=>x.endNativeBinaryVsUninterrupted?.nativeContactPairIDsIdentical).length;
summary.nativeBinaryMaxPositionDifferenceMetres=Math.max(0,...rows.map(x=>x.endNativeBinaryVsUninterrupted?.maximumPositionDifferenceMetres||0));
summary.legacyJSONMaxPositionDifferenceMetres=Math.max(0,...rows.map(x=>x.endJSONReconstructionVsUninterrupted?.maximumPositionDifferenceMetres||0));
summary.sourceRoomStaleAfterPhysicsCount=rows.reduce((n,x)=>n+(x.sourceRoomGuard?.outside||0),0);
summary.nativeWithinHalfMillimetre=rows.filter(x=>x.nativeWithinHalfMillimetre).length;
summary.nativeDivergedOverOneCentimetre=rows.filter(x=>x.endNativeBinaryVsUninterrupted?.maximumPositionDifferenceMetres>.01).length;
summary.elapsedSeconds=+((performance.now()-original)/1000).toFixed(3);
summary.completeSourceLiteraryNarrationVerified=0;
summary.assetMetricGeometryIndependentCertified=0;
summary.humanIndependentObserverPostEventGoldAvailable=false;
mkdirSync(PRIVATE,{recursive:true,mode:0o700});
const privateOutput=PRIVATE+'/round11_native_impulse_strength_diagnostic_raw_v2.json';
writeFileSync(privateOutput,JSON.stringify({metadata:{
 frozenStrictSourceOnlySHA256:sha(readFileSync(FROZEN)),
 previousRound9NativeWorldSHA256:sha(readFileSync(PREVIOUS)),
 originalAuthorHumanLabelsNotReadByPhysics:true,
 realGameCoreRapierNativeOnly:true,
 deniedRandomParentNeverTried:true,
 blockedObserverOffscreenNeverTried:true
 },summary,rows},null,2)+'\n',{flag:'wx',mode:0o600});
const publicOutput={
 metadata:{privateRawSHA256:sha(readFileSync(privateOutput)),
  frozenStrictSourceOnlySHA256:sha(readFileSync(FROZEN)),
  priorRealNativeSourceBaselineSHA256:sha(readFileSync(PREVIOUS)),
  worldGeometryAllProvisional:true,
  notIndependentHumanHeldout:true,
  noObserverOrOffscreenTest:true,
  noRandomParentPlacebo:true},summary,
 cases:rows.map(x=>({scene:x.scene,scenario:x.scenario,status:x.status,
  positiveImpulseMovement:x.realImpulseDisplacementMeters,
  trustedNativeMaxPostsave3DDiscrepancy:x.endNativeBinaryVsUninterrupted?.maximumPositionDifferenceMetres??null,
  legacyJSONMaxPostsave3DDiscrepancy:x.endJSONReconstructionVsUninterrupted?.maximumPositionDifferenceMetres??null,
  nativeSameContactIDs:x.endNativeBinaryVsUninterrupted?.nativeContactPairIDsIdentical??null,
  earliestNativeDivergence:x.intermediateNativeDeviation?.map(z=>({tick:z.tick,
   discrepancyMetres:z.native.maximumPositionDifferenceMetres,
   responsibleKind:z.worstNativeObject?.kind}))??null,
  numberOfNowInvalidOriginalRoomDescriptions:x.sourceRoomGuard?.outside??null,
  error:x.error||null}))};
writeFileSync(new URL('prse_round11_native_impulse_strength_diagnostic_aggregate_v2.json',import.meta.url),
 JSON.stringify(publicOutput,null,2)+'\n',{flag:'wx'});
console.log('ROUND11 SOURCE NATIVE SAVE IMPULSE STRENGTH DIAGNOSTIC',JSON.stringify(summary));
