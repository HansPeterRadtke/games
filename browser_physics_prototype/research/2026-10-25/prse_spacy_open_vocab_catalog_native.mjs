// PRSE research-only high-precision 3D *catalog-gated* noun integration.
//
// Same frozen SceneEval sources and pretrained spaCy candidates as the broad
// generic-box feasibility study. In contrast, this arm adds a REAL physical
// entity only if the project's preexisting GameCore scene compiler recognizes
// the category and supplies dimension, collision shape/body class and mass.
// It never fabricates approximate dimensions for an unknown type.
//
// This is still source-provisional geometry, not a licensed 3D visual asset,
// source-reference resolution, color calibration, real physical deformation,
// or a credible complete world generated from arbitrary prose.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,object,geometryIssues,validateScene}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {compileProposal}from'../2026-10-24/prse_constraint_layout.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {recordNativePRSEState,restoreNativePRSEState}from'./prse_native_world_transaction.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery';
mkdirSync(ROOT,{recursive:true,mode:0o700});
const INPUT=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const MODEL=JSON.parse(readFileSync(ROOT+'/prse_spacy_open_vocab_500_proposals_raw_v1.json')).records;
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+4*i)];
const cache=new Map(),digest=b=>createHash('sha256').update(b).digest('hex');
const temp=(kind)=>{
 if(cache.has(kind))return cache.get(kind);
 const sourceId='catalog-check';
 const proposal={sourceId,text:'An object is described but not yet verified.',
  quantities:{[kind]:{count:1,op:'eq'}},mentions:[],relations:[]};
 const compiled=compileProposal(proposal);
 const entity=compiled.scene.entities.find(e=>e.kind===kind &&
  e.source!=='provisional_3D_room_boundary');
 const value=entity?{size:entity.size,mass:entity.mass,shape:entity.shape,
  material:entity.material,body:entity.body}:null;
 cache.set(kind,value);return value;
};
const collision=(a,b)=>['x','y','z'].every(k=>Math.abs(a.position[k]-b.position[k])<
 (a.size[k]+b.size[k])/2+.015);
function place(scene,kind,idx,evidence,geometry){
 const suffix=digest(Buffer.from(kind)).slice(0,8);
 const id=scene.id+'-catalog-'+kind.slice(0,22).replace(/_/g,'-')+'-'+suffix+'-'+idx;
 for(let i=0;i<30;i++)for(let j=0;j<24;j++){
  const x=-35.7+i*.57,z=5.58+j*.52;
  if(x-geometry.size.x/2<-35.92||x+geometry.size.x/2>-18.04||
     z-geometry.size.z/2<5.42||z+geometry.size.z/2>18.0)continue;
  const entity=object(id,kind,{x,y:geometry.size.y/2,z},geometry.size,{
    body:geometry.body,mass:geometry.mass||1,
    shape:geometry.shape,material:geometry.material||'unknown',
    name:kind.replaceAll('_',' ')+' '+(idx+1),
    description:'Existing approximate category 3D geometry; source identity, orientation and visual asset still not independently validated',
    source:'pretrained-noun-existing-catalog:'+scene.id+':'+evidence.sourceOffsets.join(':'),
    state:{condition:'intact',existingEngineGeometry:true,
     noIndependentSourceMeaningVerification:true,noVisualAssetProof:true}
  });
  if(!scene.entities.some(e=>!e.state?.destroyed&&collision(e,entity)))return entity;
 }
 return null;
}
const results=[],start=performance.now();
for(const sourceId of ids){
 const p=INPUT[sourceId],extra=MODEL[sourceId];
 if(extra.sourceText!==p.text)throw Error('Frozen source mismatch');
 const original=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const row={sourceId,subset:sourceId<100?'human':'assisted',status:'original_rejected',
  eligibleNounTypes:extra.boundedNewTypes.length,retainedCategories:[],
  refusedWithoutRecognizedPhysicalGeometry:0,refusedPlacement:0};
 if(!original.accepted||geometryIssues(original.scene).length){results.push(row);continue;}
 const scene=structuredClone(original.scene);
 const sourceIDs=new Set(scene.entities.map(e=>e.id));
 const counts=new Map();
 for(const e of scene.entities){
  if(e.source==='provisional_3D_room_boundary'||e.state?.destroyed)continue;
  counts.set(e.kind,(counts.get(e.kind)||0)+1);
 }
 let add=0;
 for(const e of extra.boundedNewTypes){
  if(p.quantities[e.type]?.count===0)continue;
  const size=temp(e.type);
  if(!size){row.refusedWithoutRecognizedPhysicalGeometry++;continue;}
  const existing=counts.get(e.type)||0;
  const wanted=Math.max(0,Math.min(12,e.count)-existing);
  const source=extra.candidates.find(x=>x.type===e.type);
  if(!source)throw Error('No actual source span backing new catalog type');
  if(p.text.slice(...source.sourceOffsets)!==source.sourceText)
   throw Error('Source text offset corruption');
  for(let idx=0;idx<wanted;idx++){
   if(add>=16){row.refusedPlacement++;continue;}
   const body=place(scene,e.type,idx,source,size);
   if(!body){row.refusedPlacement++;continue;}
   scene.entities.push(body);add++;
   counts.set(e.type,(counts.get(e.type)||0)+1);
   row.retainedCategories.push({id:body.id,kind:e.type,sourceSpan:source.sourceOffsets,
    approxCategoryDimensions:size.size,
    explicitUncertainty:'Existing category physics estimate only, source meaning/asset unverified'});
  }
 }
 if(geometryIssues(scene).length||!validateScene(scene).ok){
  row.status='rejected_after_catalog_additions';results.push(row);continue;
 }
 let a=null,b=null;
 try{
  a=new PRSELoop(scene);a.tick(35);
  const snap=recordNativePRSEState(a);
  const restored=restoreNativePRSEState(JSON.parse(JSON.stringify(snap)));
  if(!restored.ok)throw Error('Native GameCore restore refused: '+restored.reason);
  b=restored.loop;
  const phys={};
  for(const e of a.scene.entities){
   if(e.source==='provisional_3D_room_boundary'||e.state?.destroyed||!a.active.has(e.id))continue;
   phys[e.kind]=(phys[e.kind]||0)+1;
  }
  const phys2={};
  for(const e of b.scene.entities){
   if(e.source==='provisional_3D_room_boundary'||e.state?.destroyed||!b.active.has(e.id))continue;
   phys2[e.kind]=(phys2[e.kind]||0)+1;
  }
  if(JSON.stringify(phys)!==JSON.stringify(phys2)||
     ![...sourceIDs].every(id=>b.entities.has(id))||b.scene.prose!==p.text)
   throw Error('Authoritative native 3D population, IDs or source prose not preserved');
  row.afterNativePhysicalCount=phys;row.addedActualNativeBodies=add;
  row.status='accepted_native_3d_reentered';
 }catch(e){row.status='runtime_failed';row.reason=String(e.message).slice(0,200);}
 finally{b?.dispose();a?.dispose();}
 results.push(row);
}
const good=results.filter(x=>x.status==='accepted_native_3d_reentered');
const metrics={
 originalSourceScenes:200,baselineAccepted:results.filter(x=>x.status!=='original_rejected').length,
 acceptedWithCatalogGate:good.length,
 moreRejectedThanBaseline:results.filter(x=>x.status==='rejected_after_catalog_additions').length,
 runtimeFailures:results.filter(x=>x.status==='runtime_failed').length,
 addedApproxCategorySizeRealRapierBodies:good.reduce((s,r)=>s+(r.addedActualNativeBodies||0),0),
 addedSourceTypeInstances:good.reduce((s,r)=>s+new Set(r.retainedCategories.map(x=>x.kind)).size,0),
 physicalSceneWorldsWithNewCatalogEntities:good.filter(x=>x.addedActualNativeBodies>0).length,
 candidateCategoriesRefusedForNoKnownGeometry:results.reduce((s,r)=>s+r.refusedWithoutRecognizedPhysicalGeometry,0),
 placementRefusals:results.reduce((s,r)=>s+r.refusedPlacement,0),
 sourceTextAndNativeWorldIDRestored:good.length,
 compiledNativeFixedBuildOnly:true,
 stillNotActual3DAssetOrSourceEntailment:true,
 elapsedSeconds:+((performance.now()-start)/1000).toFixed(2)};
const privateFile=ROOT+'/prse_spacy_open_vocab_catalog_native_200_raw_v1.json';
const full={metadata:{
 'source':'Same frozen external text and pretrained grammar source candidate proposals, NO author gold during physical scene generation',
 'method':'Only existing PRSE DIM size catalog types, actual native GameCore/Rapier and source-ID native saved-state',
 'important':'A catalog dimension approximation is not a renderable physical asset or validated literary semantic source meaning'},
 metrics,results};
writeFileSync(privateFile,JSON.stringify(full,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_spacy_open_vocab_catalog_native_200_aggregate_v1.json',import.meta.url),
 JSON.stringify({metadata:{...full.metadata,privateRawSHA256:digest(readFileSync(privateFile))},
  metrics,scenes:results.map(x=>({id:x.sourceId,status:x.status,
   physicallyAdded:x.addedActualNativeBodies||0,
   geometryRefusals:x.refusedWithoutRecognizedPhysicalGeometry,
   placementRefusals:x.refusedPlacement}))},null,2)+'\n',{flag:'wx'});
console.log('KNOWN_3D_CATALOG_ONLY',JSON.stringify(metrics));
