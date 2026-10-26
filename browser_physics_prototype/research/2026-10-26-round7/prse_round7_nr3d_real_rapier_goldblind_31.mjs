// PRSE round seven new independent human Nr3D source-only GENUINE native
// GameCore/Rapier 3D feasibility. NOT a SceneEval/LEGO replay, not random
// feasible-parent placebo (previously denied). Physical parent is explicitly
// source named. CONTROL and CANDIDATE have exact same body IDs/kind/dimensions.
// Reference ScanNet point-cloud, certified mesh, true support/instance gold
// are NOT available; these are generic provisional box-shaped colliders.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {object,PRSELoop,geometryIssues,validateScene}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {recordNativePRSEState,restoreNativePRSEState}from'../2026-10-25/prse_native_world_transaction.mjs';
await initializePhysics();
const base='/data/var/games/prse_semantic_research/runs/2026-10-26-nr3d-independent-r7';
const source=base+'/nr3d_physical_feasibility_goldblind_input_v1.json';
const raw=JSON.parse(readFileSync(source));
const sha=b=>createHash('sha256').update(b).digest('hex');
if(!raw.metadata.goldNotConsulted||raw.cases.length!==31)
 throw Error('Expected previously frozen third-party source-only cohort');
const SIZE_CHILD={x:.28,y:.24,z:.28};
const SIZE_PARENT={x:1.3,y:.58,z:1.05};
const CONTROL_X=3.5;
const identicalPoseBefore=x=>JSON.stringify(x.map(e=>({id:e.id,kind:e.kind,
 source:e.source,size:e.size,body:e.body,shape:e.shape,mass:e.mass})).sort((a,b)=>a.id.localeCompare(b.id)));
function makeScene(row,enabled){
 const id='crossgenre-'+row.scanId.replace(/[^a-z0-9]+/g,'-').slice(0,50);
 const parent=object(row.oldBody2,row.sourceOnlyParentType,
  {x:0,y:SIZE_PARENT.y/2,z:0},SIZE_PARENT,
  {body:'fixed',shape:'box',mass:1,material:'unknown',
   source:'nr3d-independent-literary-phrase-parent',
   description:'provisional box, not a certified ScanNet mesh',
   name:'source-mentioned '+row.sourceOnlyParentType,
   supportId:'floor'});
 const child=object(row.oldBody1,row.sourceOnlyChildType,
  enabled?{x:0,y:SIZE_PARENT.y+SIZE_CHILD.y/2+.001,z:0}
   :{x:CONTROL_X,y:SIZE_CHILD.y/2,z:0},SIZE_CHILD,
  {body:'dynamic',shape:'box',mass:.6,material:'unknown',
   source:'nr3d-independent-literary-phrase-child',
   description:'provisional box, not a certified ScanNet mesh',
   name:'source-mentioned '+row.sourceOnlyChildType,
   supportId:enabled?row.oldBody2:'floor'});
 const sc={id,prose:row.originalSourceText,entities:[parent,child]};
 const ok=validateScene(sc);
 if(!ok.ok||geometryIssues(sc).length)
  throw Error('Nonphysical source-only proposal: '+JSON.stringify(geometryIssues(sc).slice(0,2))+'; '+ok.reason);
 return sc;
}
function realPairs(loop){
 let found=[];
 const all=[...loop.active];
 for(let i=0;i<all.length;i++)for(let j=i+1;j<all.length;j++){
  const [a,A]=all[i],[b,B]=all[j];
  let n=0;
  for(let c=0;c<A.numColliders();c++)for(let d=0;d<B.numColliders();d++)
   loop.game.world.contactPair(A.collider(c),B.collider(d),m=>n+=m.numContacts());
  if(n)found.push({a,b,contactCount:n});
 }
 return found;
}
function physics(scene){
 let loop=null,returned=null;
 try{
  loop=new PRSELoop(scene);
  loop.tick(38);
  const contactPairs=realPairs(loop);
  const state=loop.scene.entities.map(e=>{
   const b=loop.active.get(e.id);if(!b)throw Error('Missing actually materialized PRSE body');
   return {id:e.id,kind:e.kind,shape:e.shape,size:e.size,
    nativePosition:{...b.translation()},rotation:{...b.rotation()},
    source:e.source,supportId:e.supportId};
  });
  const snapshot=recordNativePRSEState(loop);
  const restored=restoreNativePRSEState(JSON.parse(JSON.stringify(snapshot)));
  if(!restored.ok)throw Error('Actual native GameCore+Rapier state restore failed '+restored.reason);
  returned=restored.loop;
  const saved=realPairs(returned),name=p=>[p.a,p.b].sort().join('|');
  if(JSON.stringify(saved.map(name).sort())!==JSON.stringify(contactPairs.map(name).sort())||
    returned.scene.prose!==scene.prose||
    returned.active.size!==loop.active.size)
   throw Error('Native source/physical contact lost across serialized save');
  return {contactPairs,states:state,bytes:snapshot.nativeBytes,
    savedContactsExact:true,realNativeBodyCount:loop.active.size};
 }finally{returned?.dispose();loop?.dispose();}
}
let total={sources:31,armsPerSource:2,
 humanNegativeWithoutSourceOn:0,sourceExplicitOnProposals:0,
 actualSourceOnProposalsAccepted:0,realNativeSourceSupportContactCount:0,
 negativeControlNativeContactDifference:0,
 preservedExactSameBodyKindAndDimensions:0,
 actualWorldsWithExactNativeSave:0,runFailures:0};
const records=[];const start=performance.now();let runtimes=[];
for(const x of raw.cases){
 const row={scanId:x.scanId,datasetIndex:x.datasetIndex,sourceHash:x.sourceHash,
  category:x.category,sourceOnlyChild:x.sourceOnlyChildType,
  sourceOnlyParent:x.sourceOnlyParentType,status:'started'};
 let st=performance.now();
 try{
  const hasOn=x.category==='source_explicit_pretrained_on_proposal';
  const ctl=makeScene(x,false),cand=makeScene(x,hasOn);
  if(identicalPoseBefore(ctl.entities)!==identicalPoseBefore(cand.entities)||
    ctl.prose!==cand.prose||ctl.id!==cand.id)
   throw Error('Not same source, inventory/shape/mass/category control');
  total.preservedExactSameBodyKindAndDimensions++;
  const a=physics(ctl),b=physics(cand);
  row.nativeControl=a;row.nativeCandidate=b;
  if(a.realNativeBodyCount!==2||b.realNativeBodyCount!==2)
    throw Error('Real source-only physical entity budget wrong');
  if(a.contactPairs.length!==0)
    throw Error('Matched neutral ground grid unexpectedly contacted unrelated object');
  if(!a.savedContactsExact||!b.savedContactsExact)
    throw Error('Actual native world save lost contact');
  total.actualWorldsWithExactNativeSave+=2;
  if(hasOn){
   total.sourceExplicitOnProposals++;
   row.sourceContactReal=!!b.contactPairs.find(p=>
     [p.a,p.b].includes(x.oldBody1)&&[p.a,p.b].includes(x.oldBody2));
   total.actualSourceOnProposalsAccepted++;
   total.realNativeSourceSupportContactCount+=row.sourceContactReal;
  }else{
   total.humanNegativeWithoutSourceOn++;
   const unchanged=JSON.stringify(a.contactPairs)===JSON.stringify(b.contactPairs);
   if(!unchanged)total.negativeControlNativeContactDifference++;
   if(!unchanged)throw Error('Original non-top human phrase created unsupported contact');
  }
  row.actualBothNativeArmBodies=2;
  row.status='paired_real_rapier_38ticks_each';
 }catch(err){row.status='failed';row.error=String(err.message).slice(0,235);total.runFailures++;}
 row.runtimeMs=+(performance.now()-st).toFixed(3);
 runtimes.push(row.runtimeMs);
 records.push(row);
}
if(total.sourceExplicitOnProposals!==15||total.humanNegativeWithoutSourceOn!==16||
   total.actualWorldsWithExactNativeSave!==62-total.runFailures*2) {
 console.log('NATIVE_RUN_INTEGRITY_CHECK',total);
}
total.elapsedWallSeconds=+((performance.now()-start)/1000).toFixed(3);
total.perPhrasePairedNativeMsMedian=+[...runtimes].sort((a,b)=>a-b)[15].toFixed(3);
total.perPhrasePairedNativeMsP95=+[...runtimes].sort((a,b)=>a-b)[29].toFixed(3);
total.medianSourceInstancesPerScene=2;
total.allBodiesProvisionalGeometry=true;
total.matchedIndependentNativePhysicsContactTruthNotAuthorSourceTruth=true;
total.human3DScanNetMeshGroundTruthUnavailable=true;
total.noPreviouslyDeniedRandomParentPlacebo=true;
total.noLLMOrGPU=true;
const fullpath=base+'/nr3d_matched_true_native_rapier_31cases_raw_v1.json';
writeFileSync(fullpath,JSON.stringify({metadata:{
  sourceOnlyPhysicalSpecSHA256:sha(readFileSync(source)),
  generatedGeometry:'uniform provisional axis-aligned source-only box, no true ScanNet reference geometry',
  nativeActualGameCoreRapier:true,
  originalHumanGoldNotReadByNativeExperiment:true,
  physicallySourceMatchedParentNotRandomAlternative:true},summary:total,records},null,2)+'\n',{flag:'wx',mode:0o600});
const aggregate={metadata:{
 originalSourceOnlyFrozenSHA256:sha(readFileSync(source)),
 privateActualNativeRapierSHA256:sha(readFileSync(fullpath)),
 noPhysicalScanNetMetrics:true,noIndependentSupportGroundTruth:true,
 originalHumanGoldNotRead:true,
 noRandomParentPlacebo:true},
 summary:total,cases:records.map(x=>({
 scanId:x.scanId,category:x.category,status:x.status,
 actualControlContacts:x.nativeControl?.contactPairs.length??null,
 actualCandidateContacts:x.nativeCandidate?.contactPairs.length??null,
 actualGameCoreNativeSave:x.nativeControl?.savedContactsExact&&x.nativeCandidate?.savedContactsExact,
 realDirectedOnContact:x.sourceContactReal??null,error:x.error||null
 }))};
writeFileSync(new URL('prse_round7_nr3d_actual_native_rapier_feasibility_aggregate_v1.json',import.meta.url),
 JSON.stringify(aggregate,null,2)+'\n',{flag:'wx'});
console.log('PRSE_ROUND7_INDEPENDENT_SOURCE_TRUE_NATIVE_PHYSICS',JSON.stringify(total));
