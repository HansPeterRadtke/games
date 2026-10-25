// Independent no-gold reconstruction of the ALREADY frozen 197 PRSE
// SceneEval source worlds: original 3D GameCore scene, added open-noun generic
// real Rapier bodies, and strict built-in physical category-only additions.
//
// DO NOT ACCESS GOLD ANNOTATIONS HERE. Proposals, accepted source IDs, per-case
// new category instances and their source spans are frozen in owner-private
// prior 2026-10-25 research artifacts. The reconstructed native body
// positions, sizes and real Rapier contact manifolds are committed ONLY to
// owner-private /data/var/games output, with safe hashes in Git.
//
// A separate scorer may then ask whether independently author-annotated source
// relations hold in those physically frozen spaces. The parser and physics
// MUST NOT know those source gold constraints when placing the objects.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,object,geometryIssues,validateScene}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {compileProposal}from'../2026-10-24/prse_constraint_layout.mjs';
await initializePhysics();

const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Unsafe result version');
mkdirSync(ROOT,{recursive:true,mode:0o700});
const SOURCE=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const PRIVATE='/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery';
const generic=JSON.parse(readFileSync(PRIVATE+'/prse_spacy_open_vocab_native_200_raw_v1.json')).records;
const catalog=JSON.parse(readFileSync(PRIVATE+'/prse_spacy_open_vocab_catalog_native_200_raw_v1.json')).results;
const sha=b=>createHash('sha256').update(b).digest('hex');
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+i*4)];
if(ids.length!==200||generic.length!==200||catalog.length!==200)throw Error('Frozen source selection mismatch');

const BOX={x:.24,y:.28,z:.24};
const GENERIC_ROOM={minX:-35.7,minZ:5.55};
const CATALOG_ROOM={minX:-35.7,minZ:5.58};
const cOverlap=(a,b,extra=.014)=>
 ['x','y','z'].every(k=>Math.abs(a.position[k]-b.position[k])<(a.size[k]+b.size[k])/2+extra);
function genericPlacement(scene,kind,i,sourceSpan){
 const id=scene.id+'-candidate-'+kind.slice(0,20).replace(/_/g,'-')+
  '-'+sha(Buffer.from(kind)).slice(0,7)+'-'+i;
 for(let xi=0;xi<29;xi++)for(let zi=0;zi<22;zi++){
  const position={x:GENERIC_ROOM.minX+xi*.6,y:BOX.y/2,
   z:GENERIC_ROOM.minZ+zi*.54};
  const e=object(id,kind,position,BOX,{
    body:'dynamic',shape:'box',mass:.3,material:'unknown',
    name:kind.replace(/_/g,' ')+' '+(i+1),
    source:'syntax-proposed:'+scene.id+':'+sourceSpan[0]+':'+sourceSpan[1],
    state:{condition:'intact',openVocabularyCandidate:true,
      sourceMeaningIndependentlyVerified:false,
      shapeAndMaterialIndependentlyVerified:false}});
  if(!scene.entities.some(x=>!x.state?.destroyed&&cOverlap(x,e)))return e;
 }
 return null;
}
const knownShapes=new Map();
function physicsType(kind){
 if(knownShapes.has(kind))return knownShapes.get(kind);
 const d=compileProposal({sourceId:'catalog-check',
  text:'An object is described but not yet verified.',
  quantities:{[kind]:{count:1,op:'eq'}},mentions:[],relations:[]});
 const e=d.scene.entities.find(x=>x.kind===kind &&
  x.source!=='provisional_3D_room_boundary');
 const shape=e?{size:e.size,mass:e.mass,shape:e.shape,material:e.material,body:e.body}:null;
 knownShapes.set(kind,shape);
 return shape;
}
function catalogPlacement(scene,kind,index,sourceSpan,shape){
 const id=scene.id+'-catalog-'+kind.slice(0,22).replace(/_/g,'-')+
  '-'+sha(Buffer.from(kind)).slice(0,8)+'-'+index;
 for(let xi=0;xi<30;xi++)for(let zi=0;zi<24;zi++){
  const x=CATALOG_ROOM.minX+xi*.57,z=CATALOG_ROOM.minZ+zi*.52;
  if(x-shape.size.x/2<-35.92||x+shape.size.x/2>-18.04||
     z-shape.size.z/2<5.42||z+shape.size.z/2>18.0)continue;
  const e=object(id,kind,{x,y:shape.size.y/2,z},shape.size,{
   body:shape.body,mass:shape.mass||1,shape:shape.shape,
   material:shape.material||'unknown',
   name:kind.replaceAll('_',' ')+' '+(index+1),
   source:'pretrained-noun-existing-catalog:'+scene.id+':'+sourceSpan.join(':'),
   state:{condition:'intact',existingEngineGeometry:true,
    noIndependentSourceMeaningVerification:true,noVisualAssetProof:true}});
  if(!scene.entities.some(q=>!q.state?.destroyed&&cOverlap(q,e,.015)))return e;
 }
 return null;
}
function buildScene(input,id,method){
 const source=structuredClone(input);
 if(method==='baseline')return source;
 const expected=method==='generic'?generic[id]:catalog[id];
 const rows=method==='generic'?expected.addedProvenance:expected.retainedCategories;
 if(!rows)throw Error('Missing previously frozen result for '+method+' source '+id);
 const count=new Map();
 for(const r of rows){
  const i=count.get(r.kind)||0;
  count.set(r.kind,i+1);
  const span=r.sourceSpan;
  if(!Array.isArray(span)||span.length!==2||!SOURCE[ids[id]].text.slice(...span))
   throw Error('Invalid original source mention evidence');
  const e=method==='generic'?genericPlacement(source,r.kind,i,span):
   catalogPlacement(source,r.kind,i,span,physicsType(r.kind));
  if(!e||e.id!==r.id||source.entities.some(existing=>existing.id===e.id))
   throw Error('Failed exact independent physical reproduction '+id+' '+method+' '+r.kind+' '+i);
  source.entities.push(e);
 }
 if(rows.length!==source.entities.length-input.entities.length)
  throw Error('Rebuilt entity quantities disagree with frozen source');
 return source;
}
function physicsSnapshot(loop){
 const entities=loop.scene.entities.filter(x=>x.source!=='provisional_3D_room_boundary' &&
   !x.state?.destroyed&&loop.active.has(x.id));
 const info=entities.map(e=>{
  const b=loop.active.get(e.id);
  return {id:e.id,kind:e.kind,originId:e.originId||null,
   source:e.source,position:{...b.translation()},rotation:{...b.rotation()},
   size:{...e.size},shape:e.shape,body:e.body,supportId:e.supportId,
   sourceValidatedAsset:false};
 });
 const pairs=[];
 for(let i=0;i<entities.length;i++)
  for(let j=i+1;j<entities.length;j++){
   const a=loop.active.get(entities[i].id),b=loop.active.get(entities[j].id);
   let contacts=0;
   for(let x=0;x<a.numColliders();x++)
    for(let y=0;y<b.numColliders();y++)
     loop.game.world.contactPair(a.collider(x),b.collider(y),m=>{
      if(m.numContacts()>0)contacts+=m.numContacts();
     });
   if(contacts)pairs.push({a:entities[i].id,b:entities[j].id,
    contactPointCount:contacts});
  }
 return {entities:info,actualContactPairs:pairs};
}
const out=[];
const started=performance.now();
for(const method of ['baseline','generic','catalog']){
 const data=[];
 for(let k=0;k<ids.length;k++){
  const id=ids[k],p=SOURCE[id],layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
  const prior=generic[k],restricted=catalog[k];
  if(prior.sourceID!==id||restricted.sourceId!==id)throw Error('Frozen inputs not same source');
  if(!layout.accepted||geometryIssues(layout.scene).length){
   data.push({id,status:'not_physically_accepted_in_original',
    authoritativeGoldNotUsed:true});continue;
  }
  let loop=null;
  const record={id,status:'started',method};
  try{
   const scene=buildScene(layout.scene,k,method);
   if(!validateScene(scene).ok||geometryIssues(scene).length)
    throw Error('Reconstructed prior native physical scene invalid');
   loop=new PRSELoop(scene);
   loop.tick(38);
   const state=physicsSnapshot(loop);
   record.status='native_simulated';
   record.realBodies=state.entities.length;
   record.bodyStates=state.entities;
   record.nativeContactPairs=state.actualContactPairs;
   const expectedAdded=method==='generic'?prior.addedActuallyNativePhysicalBodies:
    method==='catalog'?restricted.addedActualNativeBodies:0;
   const actualAdded=state.entities.length-
    layout.scene.entities.filter(x=>x.source!=='provisional_3D_room_boundary'&&!x.state.destroyed).length;
   if(actualAdded!==expectedAdded)
    throw Error('Reconstruction differs from previous frozen source body counts');
   record.addedNativeBodies=actualAdded;
   record.originalLiterarySourceHash=sha(Buffer.from(loop.scene.prose));
  }catch(e){record.status='failed';record.error=String(e.message).slice(0,210);}
  finally{loop?.dispose();}
  data.push(record);
 }
 const good=data.filter(x=>x.status==='native_simulated');
 const metric={method,
  sampleSourceScenes:ids.length,
  acceptedNativeBodyScenes:good.length,
  failedRebuilds:data.filter(x=>x.status==='failed').length,
  nativePhysicalBodies:good.reduce((s,r)=>s+r.realBodies,0),
  actualNativeContactPairs:good.reduce((s,r)=>s+r.nativeContactPairs.length,0),
  provisionalAddedBodies:good.reduce((s,r)=>s+r.addedNativeBodies,0),
  sourceTextStillHasSameHash:good.every(x=>x.originalLiterarySourceHash===sha(Buffer.from(SOURCE[x.id].text)))};
 const obj={metadata:{
  method,
  sourceIds:ids,
  exactFrozenNativeWorldReconstruction:true,
  source:'SceneEval-500 source text frozen prior; no independent source author gold labels loaded',
  meaning:'Actual GameCore/Rapier post-tick body transformations and collider contact pairs for independent later scorer',
  limitation:'All physics contains approximate axis-aligned colliders; new generic types have no realistic asset/scale/affordance'},
  summary:metric,
  rows:data};
 const f=ROOT+'/prse_post_asset_native_'+method+'_200_raw_'+version+'.json';
 writeFileSync(f,JSON.stringify(obj,null,2)+'\n',{flag:'wx',mode:0o600});
 const checksum=sha(readFileSync(f));
 out.push({summary:metric,privateRawSHA256:checksum,privateBytes:Buffer.byteLength(JSON.stringify(obj))});
 console.log('NATIVE_RELATION_INPUT',JSON.stringify(metric));
}
writeFileSync(new URL('prse_post_asset_relation_input_200_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{
  frozenSourceSHA256:sha(Buffer.from(JSON.stringify(SOURCE))),
  independentGoldNotRead:true,
  geometry:'Same authoritative native GameCore/Rapier real body poses and collision manifolds',
  caveat:'This only freezes geometric inputs for later independent scorer; no spatial gold outcomes yet'},methods:out},null,2)+'\n',{flag:'wx'});
console.log('COMPLETE',out.length);
