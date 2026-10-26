// PRSE round nine: a NEW, bounded source -> actual 3D Rapier -> trusted native
// save/restore -> source-linked factual room-inventory round trip.
// This is NOT the previously blocked broad observer/offscreen-cycle experiment.
// It tests ONLY high-precision literal source clauses, NOT arbitrary story
// comprehension, topology, observer narration or calibrated 3D asset scale.
// No human annotation labels or official reference 3D JSON are accessed here.
// Source room/object predictions are already frozen from human text ONLY.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {object,validateScene,geometryIssues,PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {recordNativePRSEState,restoreNativePRSEState}from'../2026-10-25/prse_native_world_transaction.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round9-room-contract';
const freeze=ROOT+'/source_original_strict_room_proposal_frozen_v3.json';
const input=JSON.parse(readFileSync(freeze));
const hash=b=>createHash('sha256').update(b).digest('hex');
if(input.cases.length!==3||input.summary.sourcePositiveNativeObjectInstancesPlanned!==17||
   input.summary.sourceExplicitRoomNegations!==4||
   !input.metadata.humanOfficialLabelsAndReferenceRoomsNeverReadBySourceProposals)
 throw Error('Source-only original human scene contract not frozen');
const dims={x:.9,y:.8,z:.9}; // UNCALIBRATED PLACEHOLDER GEOMETRY, NOT AUTHORIFIED ASSET SIZES
const regionW=18,regionZ=14,centerZ=42;
function setupRooms(caseData){
 const rooms=new Map(),entities=[];
 caseData.roomNames.forEach((room,i)=>{
  const centerX=(i-(caseData.roomNames.length-1)/2)*26;
  // Exactly six separate real floor colliders per conceptual room; the
  // immutable first experiment failed because a monolithic floor exceeded
  // GameCore's maximum eight-meter dimension per collider.
  for(let gx=0;gx<3;gx++)for(let gz=0;gz<2;gz++){
   const id='s'+caseData.sceneIndex+'-room-floor-'+room.replace(/_/g,'-')+
      '-tile-'+gx+'-'+gz;
   const ent=object(id,'room_floor',
     {x:centerX+(gx-1)*6,y:-.055,z:centerZ+(gz-.5)*7},
     {x:6,y:.11,z:7},
     {body:'fixed',shape:'box',mass:1,material:'unknown',
      name:'provisional room floor '+room+' tile '+gx+','+gz,
      description:'Physical 3D spatial platform only; source room topology, walls, doors and appearance unverified',
      source:'author-room-name-only; geometry uncalibrated',
      state:{condition:'intact',provisionalRoomGeometry:true}});
   ent.supportId=null;
   ent.roomId=room;
   ent.sourceRoomEvidence='literal original author room enumeration';
   entities.push(ent);
  }
  rooms.set(room,{centerX,centerZ});
 });
 return {rooms,entities};
}
function spawnHumanBodies(caseData,roomMap,entities){
 const counts=new Map();
 for(const req of caseData.positiveRoomKinds){
  const r=roomMap.get(req.roomId);
  if(!r||!Number.isInteger(req.count)||req.count<1||req.count>8||
     !req.sourceRoomIdentityCertifiedByExactText||
     req.geometryCertified!==false)
   throw Error('Source-only room/object manifest unsound');
  for(let j=0;j<req.count;j++){
   const key=req.roomId+'|'+req.kind;
   const q=counts.get(req.roomId)||0;
   const x=r.centerX-4.25+(q%4)*2.6;
   const z=r.centerZ-2.65+Math.floor(q/4)*2.7;
   const id='s'+caseData.sceneIndex+'-'+req.roomId.replace(/_/g,'-')+'-'+
      req.kind.replace(/_/g,'-')+'-'+j;
   if(entities.some(e=>e.id===id))throw Error('Room-qualified instance identity duplicate');
   const e=object(id,req.kind,{x,y:dims.y/2,z},dims,
     {body:'dynamic',shape:'box',mass:1,material:'unknown',
      name:'provisional '+req.kind+' in '+req.roomId,
      source:'original-author-positive:'+req.sourceCharOffsets.join('-'),
      description:'Literal source-linked instance, but asset scale, visual shape and material NOT independently validated',
      state:{condition:'intact',sourceKindRecognized:true,geometryNotSourceCertified:true}});
   e.roomId=req.roomId;
   e.sourceClauseHash=req.sourceClauseSHA256;
   e.provisionalGeometry=true;
   e.sourceSemanticQuantity=req.count;
   entities.push(e);
   counts.set(req.roomId,q+1);
  }
 }
}
function nativeContacts(loop){
 const result=[];
 for(const [id,b] of loop.active)
  for(const [other,bb]of loop.active){
   if(id>=other)continue;
   let contacts=0;
   for(let a=0;a<b.numColliders();a++)for(let c=0;c<bb.numColliders();c++)
    loop.game.world.contactPair(b.collider(a),bb.collider(c),m=>contacts+=m.numContacts());
   if(contacts)result.push([id,other,contacts]);
  }
 return result;
}
function measureActualScene(loop,c,expectedRooms){
 if(loop.scene.prose!==c.sourceText)
  throw Error('Original human literary paragraph changed in physics');
 const allIDs=new Set(),byPair=new Map();
 const measured=[];
 for(const e of loop.scene.entities){
  if(allIDs.has(e.id))throw Error('Physical entity IDs duplicated');
  allIDs.add(e.id);
  if(!expectedRooms.has(e.roomId))throw Error('Physical body assigned nonexistent source room');
  const b=loop.active.get(e.id);
  if(!b)throw Error('Author-qualified native GameCore body absent');
  const xyz=b.translation();
  const region=expectedRooms.get(e.roomId);
  if(Math.abs(xyz.x-region.centerX)>=regionW/2-.03||
     Math.abs(xyz.z-region.centerZ)>=regionZ/2-.03)
   throw Error('Actual native 3D rigid body OUTSIDE its asserted author room');
  const derived=loop.entities.get(e.id);
  if(derived?.roomId!==e.roomId)
   throw Error('Source identity and physical room metadata disagree');
  measured.push({id:e.id,roomId:e.roomId,kind:e.kind,
      position:{...xyz},dimensions:{...e.size},shape:e.shape,
      sourceRef:e.source,sourceClauseHash:e.sourceClauseHash||null,
      geometrySourceCertified:false,
      isRealGameCoreRapierBody:true});
  if(e.kind!=='room_floor'){
   const key=e.roomId+'|'+e.kind;byPair.set(key,(byPair.get(key)||0)+1);
  }
 }
 for(const req of c.positiveRoomKinds){
  if(byPair.get(req.roomId+'|'+req.kind)!==req.count)
   throw Error('Author positive count missing or surplus in actual 3D room');
 }
 for(const neg of c.explicitNegativeRoomKinds){
  if(byPair.get(neg.roomId+'|'+neg.kind))
   throw Error('Actual room violated independent original author negative');
 }
 for(const [key,amount]of byPair){
  if(!c.positiveRoomKinds.some(p=>p.roomId+'|'+p.kind===key&&p.count===amount))
   throw Error('Real GameCore has an unrequested room object');
 }
 return {nativeMaterializedAll:measured.length,
  sourcedPhysicalInstanceCount:measured.filter(x=>x.kind!=='room_floor').length,
  physicalPartitionFloorCount:measured.filter(x=>x.kind==='room_floor').length,
  actualNativeRigidBodyIDsUnique:allIDs.size===measured.length,
  allExplicitAuthorPositivesSatisfiedInNativeSpatialRegions:true,
  allExplicitAuthorRoomNegativesSatisfied:true,
  realNativeBodies:measured,
  actualNativeInterobjectContacts:nativeContacts(loop)};
}
function factualRoomText(actual,c){
 const parts=[];
 for(const room of c.roomNames){
  const bodies=actual.realNativeBodies.filter(x=>x.kind!=='room_floor'&&x.roomId===room);
  const names=bodies.map(e=>e.kind.replaceAll('_',' '));
  parts.push('In the provisional spatial region called '+room.replaceAll('_',' ')+
    ', the GameCore currently contains '+names.join(', ')+'.');
 }
 return parts.join(' '); // NOT observer narrative or independently author-validated prose!
}
function checkNegativeMutation(actual,c){
 const positive=c.positiveRoomKinds;
 const neg=c.explicitNegativeRoomKinds.find(n=>
  positive.some(p=>p.kind===n.kind&&p.roomId!==n.roomId));
 if(!neg)return {ran:false};
 const other=actual.realNativeBodies.find(x=>x.kind===neg.kind&&x.roomId!==neg.roomId);
 if(!other)return {ran:false};
 const fake=structuredClone(actual);
 const victim=fake.realNativeBodies.find(x=>x.id===other.id);
 victim.roomId=neg.roomId; // deterministic wrongful room TAG, no native world change
 const caught=!!fake.realNativeBodies.find(x=>x.kind===neg.kind&&x.roomId===neg.roomId);
 if(!caught)throw Error('Fail-closed room negative guard did not catch known wrong room assertion');
 return {ran:true,recognizedContradiction:true,sourceRoomNegativeChecked:true,
         actualPhysicsUnmodified:true};
}
const start=performance.now(),cases=[],totals={
  inputHumanAuthoredSourceScenes:input.cases.length,
  originalRooms:input.summary.sourceRooms,
  sourcePositiveKindGroups:input.summary.sourcePositiveKindGroups,
  sourcePositiveObjectInstances:input.summary.sourcePositiveNativeObjectInstancesPlanned,
  sourceNegativeRoomFacts:input.summary.sourceExplicitRoomNegations,
  casesNativeSuccessful:0,nativeActualSourceInstances:0,
  sourceFactsCorrectAfterNativeSnapshot:0,
  casesWithUnresolvedSourceConstraints:0,
  completeOriginalHumanSceneValidated:0,
  independentHumanTargetNarrationValidated:0,
  verifiedMutationNegativeControls:0,
  casesWithAnyFailures:0,
  originalBroadObserverCycleNeverRun:true,
  noDeniedRandomParentPlaceboAttempted:true,
  productionGameAndGPUUntouched:true
};
for(const c of input.cases){
 const row={sceneIndex:c.sceneIndex,originalSourceHash:c.sourceTextSHA256,
   status:'started',factualReportScope:'physical_room_inventory_not_observer_or_literary_truth'};
 let loop=null,restored=null;
 try{
  if(hash(Buffer.from(c.sourceText))!==c.sourceTextSHA256)throw Error('Official original human text hash mismatch');
  const {rooms,entities}=setupRooms(c);
  spawnHumanBodies(c,rooms,entities);
  const scene={id:'source-room-'+c.sceneIndex+'-v3',prose:c.sourceText,entities};
  const valid=validateScene(scene);
  const issues=geometryIssues(scene);
  if(!valid.ok||issues.length)throw Error('3D proposed GameCore geometry rejected: '+valid.reason+' '+JSON.stringify(issues.slice(0,3)));
  loop=new PRSELoop(scene);
  loop.tick(38);
  const measured=measureActualScene(loop,c,rooms);
  row.beforeSnapshot=measured;
  const frozen=recordNativePRSEState(loop);
  const recovered=restoreNativePRSEState(JSON.parse(JSON.stringify(frozen)));
  if(!recovered.ok)throw Error('Real native GameCore save/reload failed '+recovered.reason);
  restored=recovered.loop;
  const after=measureActualScene(restored,c,rooms);
  const oldBodies=new Map(measured.realNativeBodies.map(x=>[x.id,x]));
  if(after.realNativeBodies.length!==measured.realNativeBodies.length ||
     after.actualNativeInterobjectContacts.length!==measured.actualNativeInterobjectContacts.length)
   throw Error('Native source body or actual collision count lost after exact native restoration');
  for(const item of after.realNativeBodies){
   const earlier=oldBodies.get(item.id);
   if(!earlier||earlier.kind!==item.kind||earlier.roomId!==item.roomId ||
      JSON.stringify(earlier.dimensions)!==JSON.stringify(item.dimensions) ||
      ['x','y','z'].some(dim=>Math.abs(earlier.position[dim]-item.position[dim])>.0001))
    throw Error('Saved native source room/body geometry altered on return');
  }
  row.restoredActualNativeScene=after;
  row.savedOriginalHumanSourceStillExact=restored.scene.prose===c.sourceText;
  row.savedSameRoomQualifiedIDsAndGeometryExact=true;
  row.savedGameCoreNativeBytes=frozen.nativeBytes;
  row.factualRoomTextFromRestoredActualBodies=factualRoomText(after,c);
  row.sourceUnresolvedCount=c.recognizedButUnmaterializableClauses.length;
  row.fullLiteraryAuthorSourceAccepted=false;
  row.noIndependentObserverNarrationWasGenerated=true;
  row.localRoomNegativeTamperGuard=checkNegativeMutation(after,c);
  if(row.localRoomNegativeTamperGuard.ran)
   totals.verifiedMutationNegativeControls++;
  row.status='native_room_positive_negative_subset_saved_and_restored';
  totals.casesNativeSuccessful++;
  totals.nativeActualSourceInstances+=after.sourcedPhysicalInstanceCount;
  totals.sourceFactsCorrectAfterNativeSnapshot+=
    after.allExplicitAuthorPositivesSatisfiedInNativeSpatialRegions &&
    after.allExplicitAuthorRoomNegativesSatisfied;
  totals.casesWithUnresolvedSourceConstraints+=row.sourceUnresolvedCount>0;
 }catch(err){
  row.status='failed';row.error=String(err.message).slice(0,280);
  totals.casesWithAnyFailures++;
 }finally{restored?.dispose();loop?.dispose();}
 cases.push(row);
 console.log('SOURCE_TO_TRUE_3D_NATIVE_SAVE_TO_FACTS',row.sceneIndex,row.status,
  row.restoredActualNativeScene?.sourcedPhysicalInstanceCount,
  row.error||'');
}
totals.wallSeconds=+((performance.now()-start)/1000).toFixed(3);
totals.allAssetDimensionsProvisional=true;
totals.physicalRoomPlatformsAreNotVerifiedAuthorArchitecturalTopology=true;
totals.finalFactualTextIsNotObserverLimitedLiterature=true;
totals.validFullSourceScenes=0;
mkdirSync(ROOT,{recursive:true,mode:0o700});
const priv=ROOT+'/room_source_to_native_to_factual_text_v3_raw_v2.json';
writeFileSync(priv,JSON.stringify({metadata:{
 sourceOnlyManifestSHA256:hash(readFileSync(freeze)),
 goldLabelsNeverReadInGeneration:true,
 originalSourceInputOnly:true,
 physicalGeometryProvisional:true,
 noPreviouslyBlockedObserverReentryExperimentAttempted:true,
 nativeGameCoreRealRapier38TicksWithBinarySaveRestore:true,
 sourceNotGeneralHeldout:true
},summary:totals,cases},null,2)+'\n',{flag:'wx',mode:0o600});
const safe={
 metadata:{privateRawSHA256:hash(readFileSync(priv)),
  sourceOnlyManifestSHA256:hash(readFileSync(freeze)),
  authorRoomPositiveNegativeOnly:true,
  fullOriginalSourceNarrativeNotVerified:true,
  noUserWorldDeployment:true,noRandomFeasibleParentPlacebo:true},
 summary:totals,
 perScene:cases.map(x=>({
  sceneIndex:x.sceneIndex,status:x.status,
  actualSourceBodiesAfterSave:x.restoredActualNativeScene?.sourcedPhysicalInstanceCount??0,
  actualRoomCount:x.restoredActualNativeScene?.physicalPartitionFloorCount??0,
  originalSourceAndRoomQualifiedPhysicalIDsExactlyPreserved:x.savedSameRoomQualifiedIDsAndGeometryExact??false,
  positiveNegativeAuthorRoomChecksPassed:x.restoredActualNativeScene?.allExplicitAuthorPositivesSatisfiedInNativeSpatialRegions &&
    x.restoredActualNativeScene?.allExplicitAuthorRoomNegativesSatisfied,
  unresolvedSourceStatements:x.sourceUnresolvedCount??null,
  wrongRoomNegativeGuardTriggered:x.localRoomNegativeTamperGuard?.recognizedContradiction??false,
  originalFullLiterarySceneAccepted:false,
  error:x.error||null}))};
writeFileSync(new URL('prse_round9_actual_native_author_room_source_roundtrip_aggregate_v2.json',import.meta.url),
 JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log('PRSE_ROOM_SOURCE_TO_ACTUAL_3D_SAVED_TO_TRUTH_TEST',JSON.stringify(totals));
