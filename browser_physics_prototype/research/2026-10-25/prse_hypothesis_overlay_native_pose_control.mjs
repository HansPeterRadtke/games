// Independent read-only native GameCore/Rapier pose and inter-object-contact
// fidelity control for the NON-DESTRUCTIVE source-hypothesis overlay.
//
// Compares source-proposal materializations (with ledger created but NO world
// modifications) to the older completely frozen original-native 197-source
// GameCore pose/collider records, BEFORE any physical interventions.
//
// Crucially compares actual numeric 3D poses, rotations and NATIVE contact
// pairs, not merely semantic entity IDs. No author SceneEval gold annotations
// enter this physics check, and no GPU/LLM or live PRSE process is touched.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {PRSEMeaningHypotheses}from'./prse_source_hypothesis_ledger.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-source-hypotheses';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Unsafe version');
mkdirSync(ROOT,{recursive:true,mode:0o700});
const scenes=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const prior=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_baseline_200_raw_v2.json')).rows;
const grammar=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop/prse_source_role_on_200_raw_v1.json')).records;
const bySource=new Map();
for(const r of grammar){if(!bySource.has(r.sourceId))bySource.set(r.sourceId,[]);bySource.get(r.sourceId).push(r);}
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+i*4)];
const vecdist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const qdist=(a,b)=>{
 const dot=a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w;
 const normA=Math.hypot(a.x,a.y,a.z,a.w),normB=Math.hypot(b.x,b.y,b.z,b.w);
 return 2*Math.acos(Math.max(-1,Math.min(1,Math.abs(dot/(normA*normB)))));
};
const key=(a,b)=>[a,b].sort().join('|');
const cases=[];
for(let k=0;k<ids.length;k++){
 const id=ids[k],base=prior[k],p=scenes[id];
 if(base.id!==id)throw Error('Source selection and frozen native original mismatch');
 const row={id,status:'not_tested'};
 if(base.status!=='native_simulated'){
  row.status='original_scene_not_physically_valid';cases.push(row);continue;
 }
 let ledger=null;
 try{
  const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
  if(!layout.accepted||geometryIssues(layout.scene).length)
   throw Error('Older accepted original native geometry is now rejected');
  const loop=new PRSELoop(layout.scene);loop.tick(38);
  const noLedgerWorldSHA=createHash('sha256').update(loop.game.world.takeSnapshot()).digest('hex');
  ledger=new PRSEMeaningHypotheses(loop,p,bySource.get(id)||[]);
  ledger.record();
  const afterLedgerWorldSHA=createHash('sha256').update(loop.game.world.takeSnapshot()).digest('hex');
  row.unchangedActualRapierNativeWorldBinaryBeforeAndAfterSourceLedger=
   noLedgerWorldSHA===afterLedgerWorldSHA;
  const basePos=new Map(base.bodyStates.map(e=>[e.id,e]));
  const active=[...loop.active.keys()].filter(uid=>
    loop.entities.has(uid)&&loop.entities.get(uid).source!=='provisional_3D_room_boundary');
  if(active.length!==basePos.size||active.some(uid=>!basePos.has(uid)))
   throw Error('Hypothesis overlay replaced or lost original real physical entities');
  let maxPose=0,maxRotation=0;
  for(const uid of active){
   const body=loop.active.get(uid),existing=basePos.get(uid);
   maxPose=Math.max(maxPose,vecdist(body.translation(),existing.position));
   maxRotation=Math.max(maxRotation,qdist(body.rotation(),existing.rotation));
  }
  row.max3DPositionDifferenceMeters=maxPose;
  row.maxRotationDifferenceRadians=maxRotation;
  const contactPairs=[];
  for(let a=0;a<active.length;a++)for(let b=a+1;b<active.length;b++){
   const A=loop.active.get(active[a]),B=loop.active.get(active[b]);
   let contacts=0;
   for(let i=0;i<A.numColliders();i++)for(let j=0;j<B.numColliders();j++)
    loop.game.world.contactPair(A.collider(i),B.collider(j),manifold=>{
     contacts+=manifold.numContacts();});
   if(contacts)contactPairs.push(key(active[a],active[b]));
  }
  const previous=base.nativeContactPairs.map(x=>key(x.a,x.b));
  const sortText=x=>JSON.stringify(x.sort());
  row.allOriginalNativePhysicalContactPairsPreserved=
   sortText(contactPairs)===sortText(previous);
  row.actualNativeContactPairCount=contactPairs.length;
  row.olderNativeContactPairCount=previous.length;
  row.status='evaluated';
 }catch(e){row.status='failed';row.error=String(e.message).slice(0,190);}
 finally{ledger?.dispose();}
 cases.push(row);
}
const good=cases.filter(x=>x.status==='evaluated');
const summary={
 frozenExternalDescriptions:ids.length,
 originalPhysicallyAccepted:good.length,
 unexpectedFailures:cases.filter(x=>x.status==='failed').length,
 maxObjectPositionDifferenceMeters:good.length?Math.max(...good.map(x=>x.max3DPositionDifferenceMeters)):null,
 maxObjectRotationDifferenceRadians:good.length?Math.max(...good.map(x=>x.maxRotationDifferenceRadians)):null,
 casesPreservingAllRapierObjectToObjectContacts:good.filter(x=>x.allOriginalNativePhysicalContactPairsPreserved).length,
 totalOriginalNativePhysicalContactPairs:good.reduce((n,x)=>n+x.olderNativeContactPairCount,0),
 totalAfterHypothesisOverlayNativePhysicalContacts:good.reduce((n,x)=>n+x.actualNativeContactPairCount,0),
 exactNativeWorldBinaryUnchangedByAddingSemanticHypothesisOverlay:good.filter(x=>
  x.unchangedActualRapierNativeWorldBinaryBeforeAndAfterSourceLedger).length,
 goldIndependent:true,
 noGPUorLLM:true};
const file=ROOT+'/prse_hypothesis_overlay_baseline_3d_contact_200_raw_'+version+'.json';
const payload={metadata:{
 method:'Actual native GameCore source-body position/rotation and true Rapier collider contacts, frozen original baseline vs new non-destructive source hypothesis overlay',
 caution:'Exact same 38-step physical input; no guarantee of future contact determinism from single pose comparison; not a source-reference entailment proof'},
 summary,cases};
writeFileSync(file,JSON.stringify(payload,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_hypothesis_overlay_baseline_contacts_200_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...payload.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(file)).digest('hex')},
 summary},null,2)+'\n',{flag:'wx'});
console.log('NATIVE_HYPOTHESIS_OVERLAY_PHYSICAL_IDENTITY',JSON.stringify(summary));
