// Real PRSE GameCore/Rapier matched SAME-BODY source-only support placement.
//
// CONTROL: exact frozen source-native 3D world from prior verified physical
// generic-noun experiment (same 197/200 accepted SceneEval descriptions).
// ALTERNATIVE: copy the same source scene, same objects, same IDs, same
// dimensions, and *only* attempt ON attachments proposed by already frozen
// source-only pretrained grammar noun-chunk candidates; ZERO author gold.
//
// The physical world, NOT string geometry alone, decides whether a proposed
// source-supported relation made true native Rapier contacts after 38 steps.
// Predeclared abstentions: unknown/multiple child or support, fixed child,
// child already attached elsewhere, size insufficient, colliding or floating.
// No source-authored oracle co-ordinates or gold constraints. Record all
// refusals/failed proposals, actual post-tick collider contacts, and verify
// SAME native entity/ID budget against old frozen control per scene.
// All full source text, per-entity poses and contacts owner-private on Nitro.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import{performance}from'node:perf_hooks';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop,object,geometryIssues,validateScene}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{recordNativePRSEState,restoreNativePRSEState}from'./prse_native_world_transaction.mjs';
await initializePhysics();
const DIR='/data/var/games/prse_semantic_research/runs/2026-10-25-source-only-placement';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
const policy=process.argv.find(x=>x.startsWith('--policy='))?.slice(9)||'pretrained';
if(!['pretrained','lexical'].includes(policy))throw Error('Source-only source-relation comparator unknown');
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Invalid version');
mkdirSync(DIR,{recursive:true,mode:0o700});
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const frozenSourceNouns=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery/prse_spacy_open_vocab_native_200_raw_v1.json')).records;
const sourceRelations=JSON.parse(readFileSync(DIR+'/prse_source_only_on_nounchunk_200_raw_v1.json')).cases;
const oldControl=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_generic_200_raw_v2.json')).rows;
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+i*4)];
const sha=b=>createHash('sha256').update(b).digest('hex');
const BOX={x:.24,y:.28,z:.24},ROOM={minX:-35.7,minZ:5.55};
const overlap=(a,b,extra=.014)=>['x','y','z'].every(k=>
 Math.abs(a.position[k]-b.position[k])<(a.size[k]+b.size[k])/2+extra);
function restoreGenericOriginal(scene,frozen){
 const s=structuredClone(scene),count=new Map();
 for(const record of frozen.addedProvenance){
  const kind=record.kind,idx=count.get(kind)||0;count.set(kind,idx+1);
  const id=s.id+'-candidate-'+kind.slice(0,20).replace(/_/g,'-')+'-'+
   sha(Buffer.from(kind)).slice(0,7)+'-'+idx;
  if(id!==record.id)throw Error('Original generic object ID was not reproducible');
  const span=record.sourceSpan;
  if(!Array.isArray(span)||span.length!==2)throw Error('Original source span missing');
  let next=null;
  for(let xi=0;xi<29&&!next;xi++)for(let zi=0;zi<22;zi++){
   const position={x:ROOM.minX+xi*.6,y:BOX.y/2,z:ROOM.minZ+zi*.54};
   const candidate=object(id,kind,position,BOX,{
    body:'dynamic',shape:'box',mass:.3,material:'unknown',
    name:kind.replace(/_/g,' ')+' '+(idx+1),
    source:'syntax-proposed:'+s.id+':'+span[0]+':'+span[1],
    state:{condition:'intact',openVocabularyCandidate:true,
      sourceMeaningIndependentlyVerified:false,shapeAndMaterialIndependentlyVerified:false}});
   if(!s.entities.some(e=>!e.state?.destroyed&&overlap(e,candidate))){next=candidate;break;}
  }
  if(!next)throw Error('Generic prior original cannot be rebuilt without overlaps');
  s.entities.push(next);
 }
 return s;
}
function planSourceSupport(scene,relations){
 const attempts=[];
 let success=0;
 for(const relation of relations){
  const rec={a:relation.a,b:relation.b,
   sourceCharPositions:relation.sourceCharPositions,
   sourceDependencyEvidence:relation.confidence,status:'not_attempted'};
  const a=scene.entities.filter(e=>e.kind===relation.a&&e.source!=='provisional_3D_room_boundary');
  const b=scene.entities.filter(e=>e.kind===relation.b&&e.source!=='provisional_3D_room_boundary');
  if(a.length!==1||b.length!==1){rec.status='ambiguous_or_missing_instance';attempts.push(rec);continue;}
  const child=a[0],support=b[0];
  rec.childId=child.id;rec.supportId=support.id;
  if(child.id===support.id){rec.status='same_instance';attempts.push(rec);continue;}
  if(child.body!=='dynamic'||child.shape==='sphere'){rec.status='not_supported_dynamic_box';attempts.push(rec);continue;}
  if(child.supportId&&child.supportId!=='floor'){
   rec.status='already_has_support';attempts.push(rec);continue;
  }
  if(scene.entities.some(e=>e.supportId===child.id)){rec.status='child_is_parent_of_another_entity';attempts.push(rec);continue;}
  if(support.shape!=='box'||support.size.x<child.size.x+.025||
     support.size.z<child.size.z+.025){rec.status='physically_incompatible_support_size';attempts.push(rec);continue;}
  if(success>=8){rec.status='per_scene_source_constraint_budget';attempts.push(rec);continue;}
  const previousPos={...child.position},previousSupport=child.supportId;
  let chosen=null;
  const roomX=(support.size.x-child.size.x)/2,roomZ=(support.size.z-child.size.z)/2;
  for(const x of [0,-.5,.5]){
   for(const z of [0,-.5,.5]){
    child.position={x:support.position.x+x*roomX,y:support.position.y+support.size.y/2+child.size.y/2+.001,
      z:support.position.z+z*roomZ};
    child.supportId=support.id;
    if(!geometryIssues(scene).length){chosen={...child.position};break;}
   }
   if(chosen)break;
  }
  if(!chosen){child.position=previousPos;child.supportId=previousSupport;rec.status='no_nonoverlapping_source_supported_position';}
  else{
   success++;rec.status='nominally_valid_prephysics_source_on';
   rec.originalPosition=previousPos;rec.chosenSourceOnlyPosition=chosen;
  }
  attempts.push(rec);
 }
 return attempts;
}
function physics(loop){
 const bodies=loop.scene.entities.filter(e=>e.source!=='provisional_3D_room_boundary'&&
   !e.state?.destroyed&&loop.active.has(e.id));
 const bodyStates=bodies.map(e=>({
  id:e.id,kind:e.kind,source:e.source,position:{...loop.active.get(e.id).translation()},
  rotation:{...loop.active.get(e.id).rotation()},size:{...e.size},shape:e.shape,
  body:e.body,supportId:e.supportId}));
 const contactPairs=[];
 for(let i=0;i<bodies.length;i++)for(let j=i+1;j<bodies.length;j++){
  const a=loop.active.get(bodies[i].id),b=loop.active.get(bodies[j].id);
  let contactPoints=0;
  for(let x=0;x<a.numColliders();x++)for(let y=0;y<b.numColliders();y++)
   loop.game.world.contactPair(a.collider(x),b.collider(y),m=>contactPoints+=m.numContacts());
  if(contactPoints)contactPairs.push({a:bodies[i].id,b:bodies[j].id,contactPointCount:contactPoints});
 }
 return {bodyStates,contactPairs};
}
const rows=[],start=performance.now();
for(let index=0;index<ids.length;index++){
 const id=ids[index],p=source[id],old=oldControl[index],frozen=frozenSourceNouns[index],
  src=sourceRelations[index];
 if(old.id!==id||frozen.sourceID!==id||src.sourceId!==id||
  src.sourceHash!==sha(Buffer.from(p.text)))
  throw Error('Frozen original source identity/proposals were not matched');
 const original=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const row={sourceId:id,sourceGroup:id<100?'human':'assisted',
  status:'not_started',attempts:[],preexistingNativeStatus:old.status};
 if(old.status!=='native_simulated'){
  row.status='original_scene_not_physically_accepted';rows.push(row);continue;
 }
 let game=null,restored=null;
 try{
  if(!original.accepted)throw Error('Previously physically accepted baseline now rejected');
  const scene=restoreGenericOriginal(original.scene,frozen);
  if(geometryIssues(scene).length||!validateScene(scene).ok)
   throw Error('Frozen original control generic scene has invalid geometry');
  // Critical correction to earlier v2/v3 comparisons: check the FULL
  // physical control actually reproduces the earlier native world, including
  // every body 3D position and real contact pair, not only the entity count.
  let control=null;
  try{
   control=new PRSELoop(structuredClone(scene));control.tick(38);
   const exact=physics(control),frozenBodies=new Map(old.bodyStates.map(e=>[e.id,e]));
   const maxDeviation=exact.bodyStates.reduce((max,e)=>{
    const older=frozenBodies.get(e.id);
    if(!older)throw Error('Frozen control body ID missing: '+e.id);
    return Math.max(max,Math.hypot(...['x','y','z'].map(k=>e.position[k]-older.position[k])));
   },0);
   const contactKeys=pairs=>pairs.map(e=>[e.a,e.b].sort().join('|')).sort();
   row.originalPreexistingMaximumBodyDisplacementMeters=maxDeviation;
   row.originalPhysicalContactPairsExact=
    JSON.stringify(contactKeys(exact.contactPairs))===JSON.stringify(contactKeys(old.nativeContactPairs));
   row.originalNativeBodyCountExact=exact.bodyStates.length===old.realBodies;
   if(maxDeviation>1e-4||!row.originalPhysicalContactPairsExact||!row.originalNativeBodyCountExact)
    throw Error('Frozen original 3D physics/layout was NOT reproduced exactly BEFORE alternative source placement');
  }finally{control?.dispose();}
  const originalIds=new Set(scene.entities.filter(e=>e.source!=='provisional_3D_room_boundary').map(e=>e.id));
  const olderIds=new Set(old.bodyStates.map(e=>e.id));
  if(originalIds.size!==olderIds.size||[...originalIds].some(id=>!olderIds.has(id)))
   throw Error('Prior original native source entity IDs changed');
  const candidates=policy==='lexical'?p.relations.filter(r=>r.kind==='object'&&r.type==='on').map(r=>({
   a:r.a,b:r.b,type:'on',kind:'object',
   sourceCharPositions:[Math.max(0,p.text.indexOf(r.sourceText))],
   confidence:'frozen_deterministic_lexical_phrase_on',
   sourceSnippet:r.sourceText
  })):src.proposedOn;
  row.attempts=planSourceSupport(scene,candidates);
  if(geometryIssues(scene).length||!validateScene(scene).ok)
   throw Error('Source-only constraint placement invalidated actual GameCore source geometry');
  game=new PRSELoop(scene);game.tick(38);
  const now=physics(game);
  const actualIds=new Set(now.bodyStates.map(e=>e.id));
  if(actualIds.size!==olderIds.size||[...actualIds].some(id=>!olderIds.has(id))||
   game.scene.prose!==p.text)
   throw Error('Candidate placement changed the same-budget original native bodies or source prose');
  const sourceAttachmentKeys=new Set(row.attempts.filter(a=>a.status==='nominally_valid_prephysics_source_on')
   .map(a=>[a.childId,a.supportId].sort().join('|')));
  const observedNative=new Set(now.contactPairs.map(c=>[c.a,c.b].sort().join('|')));
  row.sourceConditionedAttachmentCount=sourceAttachmentKeys.size;
  row.actualNewSourceAttachmentContactPairs=[...sourceAttachmentKeys].filter(k=>observedNative.has(k)).length;
  row.nativeBodyCount=now.bodyStates.length;
  row.nativeContactPairCount=now.contactPairs.length;
  row.bodyStates=now.bodyStates;
  row.nativeContactPairs=now.contactPairs;
  row.movedExistingBodyCount=row.attempts.filter(a=>a.status==='nominally_valid_prephysics_source_on').length;
  row.originalSourceTextUntouched=true;
  const native=recordNativePRSEState(game);
  const clone=restoreNativePRSEState(JSON.parse(JSON.stringify(native)));
  if(!clone.ok)throw Error('Native GameCore/Rapier full world save/restore refused: '+clone.reason);
  restored=clone.loop;
  const second=physics(restored);
  row.nativeSaveBodyCountPreserved=second.bodyStates.length===row.nativeBodyCount;
  row.nativeSaveContactIDsPreserved=JSON.stringify(second.contactPairs.map(x=>[x.a,x.b].sort().join('|')).sort())===
   JSON.stringify(now.contactPairs.map(x=>[x.a,x.b].sort().join('|')).sort());
  row.nativeOriginalSourcePreserved=restored.scene.prose===p.text;
  if(!row.nativeSaveBodyCountPreserved||!row.nativeSaveContactIDsPreserved||!row.nativeOriginalSourcePreserved)
   throw Error('Same-budget source-only native world/save diverged');
  row.status='source_only_native_gamecore_verified';
 }catch(e){row.status='failed';row.error=String(e.message).slice(0,240);}
 finally{restored?.dispose();game?.dispose();}
 rows.push(row);
 if((index+1)%25===0)console.log('SOURCE_ONLY_NATIVE_PLACEMENT_PROGRESS',index+1,'of',ids.length);
}
const good=rows.filter(x=>x.status==='source_only_native_gamecore_verified');
const sum=f=>good.reduce((a,b)=>a+f(b),0);
const refused={};
for(const r of rows)for(const x of r.attempts||[])refused[x.status]=(refused[x.status]||0)+1;
const summary={sourceDescriptions:ids.length,
 originalAcceptedSameSourceScenes:oldControl.filter(x=>x.status==='native_simulated').length,
 actualNativeSourceOnlyPlacedAndSaved:good.length,
 nativeReconstructionFailures:rows.filter(x=>x.status==='failed').length,
 originalNonwallPhysicalBodyBudgetAcrossScenes:oldControl.filter(x=>x.status==='native_simulated')
  .reduce((n,r)=>n+r.realBodies,0),
 sameNativePhysicalBodiesAcrossSourceOnlyScenes:sum(x=>x.nativeBodyCount),
 sourceOnlyPretrainedOnCandidates:sum(x=>x.attempts.length),
 candidateResultCategories:refused,
 acceptedSourceOnlyExtraNativePlacements:sum(x=>x.movedExistingBodyCount),
 actualNewSourceOnlyOnContactPairs:sum(x=>x.actualNewSourceAttachmentContactPairs),
 allActualNativeContactsAfterSourceOnlyPlacement:sum(x=>x.nativeContactPairCount),
 originalBaselineGenericNativeInterobjectContacts:oldControl.filter(x=>x.status==='native_simulated')
  .reduce((n,r)=>n+r.nativeContactPairs.length,0),
 sourceHistoryAndNativeRapierContactsSavedExactly:sum(x=>Number(x.nativeSaveBodyCountPreserved&&x.nativeSaveContactIDsPreserved&&x.nativeOriginalSourcePreserved)),
 elapsedSeconds:+((performance.now()-start)/1000).toFixed(2),
 sourceAnnotationsNeverRead:true,
 originalBodyPoseAndNativeContactsActuallyPreflightChecked:true,
 policy,
 physicalAssetCaveat:'Same 1110 extra uncalibrated generic boxes. Contact can be genuine native Rapier but generic categories are NOT realistic objects.'};
const full={metadata:{method:'Same existing generic source entities and native GameCore/Rapier world, grammar noun chunk on constrained vs original frozen arbitrary positions',
 sourceSelection:'First100 human and systematic every fourth100 assisted previously exposed SceneEval source paragraphs',
 sourceGrammarFrozenBeforeGold:true,
 sourceOnlyPolicy:policy,
 physicalBudgetExactlyMatchedPerScene:true,
 oraclePlacementOrAnnotationGoldUsed:false},summary,rows};
const path=DIR+'/prse_source_only_nounchunk_same_budget_native_200_raw_'+version+'.json';
writeFileSync(path,JSON.stringify(full,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_source_only_nounchunk_same_budget_native_200_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...full.metadata,privateNativeRawSHA256:sha(readFileSync(path))},
  summary,scenes:rows.map(x=>({id:x.sourceId,status:x.status,
   attempted:x.attempts.length,placed:x.movedExistingBodyCount??0,
   actualSourceNativeContact:x.actualNewSourceAttachmentContactPairs??0,
   allNativeContacts:x.nativeContactPairCount??null,
   sourceBodyCount:x.nativeBodyCount??null,error:x.error||null}))},null,2)+'\n',{flag:'wx'});
console.log('SOURCE_ONLY_NATIVE_SUPPORT_PLACEMENT_SAME_BUDGET',JSON.stringify(summary));
