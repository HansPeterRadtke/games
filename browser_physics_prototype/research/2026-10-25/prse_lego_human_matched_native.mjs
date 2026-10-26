// Public human-curated LEGO-Bench (independent SceneEval corpus) source-only
// interpreter -> ACTUAL native GameCore/Rapier 3D instantiated worlds.
// Arms: unchanged-inventory initial floor-grid / frozen lexical relations /
// lexical + pre-trained source-only grammatical ON constraints.
// NOT the earlier denied random feasible-parent/placebo physics experiment.
// No author constraints, reference JSON, or gold objects available here.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,geometryIssues,validateScene} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {compileProposal} from '../2026-10-24/prse_constraint_layout.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {recordNativePRSEState,restoreNativePRSEState} from './prse_native_world_transaction.mjs';
await initializePhysics();
const PATH='/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent';
const all=JSON.parse(readFileSync(PATH+'/lego_source_only_frozen_130_raw_v1.json'));
if(all.scenes.length!==130||all.metadata.neverAccessedHumanConstraintsOrReferencesInThisPhase!==true)
 throw Error('Unexpected source-only frozen LEGO inputs');
const hash=b=>createHash('sha256').update(b).digest('hex');
const sha=hash;
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


const pairkey=(p)=>[p.a,p.b].sort().join('|');
const fingerprint=scene=>{
 const e=scene.entities.filter(x=>x.source!=='provisional_3D_room_boundary').map(x=>
  ({id:x.id,kind:x.kind,shape:x.shape,body:x.body,material:x.material,size:x.size}));
 return JSON.stringify(e.sort((a,b)=>a.id.localeCompare(b.id)));
};
function safeGenreSource(scene,id){
 for(const ent of scene.entities){
  if(ent.source.startsWith('SceneEval-'+id+':'))ent.source='LEGO-Bench-'+id+':source-lexicon';
 }
}
function strictPreflight(original,alternate,allowedIds){
 if(original.id!==alternate.id||original.prose!==alternate.prose||fingerprint(original)!==fingerprint(alternate))
  throw Error('Not a same-body, same-size, same-source control');
 const first=new Map(original.entities.map(x=>[x.id,x]));
 for(const ent of alternate.entities){
  const before=first.get(ent.id);
  if(!before)throw Error('Unexpected body appeared');
  if(!allowedIds.has(ent.id) && (
   Math.hypot(...['x','y','z'].map(k=>ent.position[k]-before.position[k]))>1e-7||
   ent.supportId!==before.supportId))throw Error('Alternative silently moved an unproposed object');
 }
}
function checkNative(condition,scene,sourceText){
 const loop=new PRSELoop(structuredClone(scene));
 try{
  loop.tick(38);
  const state=physics(loop);
  if(loop.scene.prose!==sourceText)throw Error('Original LEGO source paragraph changed');
  const snapshot=recordNativePRSEState(loop);
  const reconstructed=restoreNativePRSEState(JSON.parse(JSON.stringify(snapshot)));
  if(!reconstructed.ok)throw Error('Native source/ID/contact save refused');
  try{
   const newer=physics(reconstructed.loop);
   if(newer.bodyStates.length!==state.bodyStates.length||
     JSON.stringify(newer.contactPairs.map(pairkey).sort())!==JSON.stringify(state.contactPairs.map(pairkey).sort())||
     reconstructed.loop.scene.prose!==sourceText)
     throw Error('Native 3D restore lost bodies, original source or contacts');
  }finally{reconstructed.loop.dispose();}
  return state;
 }finally{loop.dispose();}
}
const rows=[],begin=performance.now();
for(let index=0;index<all.scenes.length;index++){
 const rec=all.scenes[index],id=rec.sourceId,proposal=rec.lexicalProposal;
 if(id!==`lego-${String(index).padStart(3,'0')}`||proposal.sourceId!==id||
    rec.sourceHash!==sha(Buffer.from(rec.sourceText))||proposal.text!==rec.sourceText)
    throw Error('Frozen distinct external source index mismatch');
 const row={sourceIndex:index,sourceId:id,status:'not_started',
  lexicalKinds:Object.keys(proposal.quantities).length,
  lexicalRelations:proposal.relations.length,
  learnedOnProposals:rec.pretrainedOn.length,
  learnedOnAbstentions:rec.pretrainedAbstentions.length};
 try{
  const base=compileProposal({...proposal,relations:[]},{maxEntities:32});
  row.missingCategories=base.missing.length;
  row.baselineSourceEntities=base.proposed;
  if(!base.good||geometryIssues(base.scene).length||!validateScene(base.scene).ok){
   row.status='original_source_to_geometry_rejected';rows.push(row);continue;
  }
  const original=structuredClone(base.scene);
  safeGenreSource(original,id);
  const repaired=repairScene(proposal,{maxSweeps:2,maxAttemptsPerScene:150});
  let lexical=repaired.accepted&&geometryIssues(repaired.scene).length===0?
   structuredClone(repaired.scene):structuredClone(original);
  safeGenreSource(lexical,id);
  row.lexicalAccepted=Boolean(repaired.accepted);
  const eligibleMoved=new Set();
  for(const x of lexical.entities){
   const old=original.entities.find(y=>x.id===y.id);
   if(!old)throw Error('Original source entity unexpectedly missing in lexical arm');
   if(Math.hypot(...['x','y','z'].map(k=>x.position[k]-old.position[k]))>1e-7||x.supportId!==old.supportId)
    eligibleMoved.add(x.id);
  }
  strictPreflight(original,lexical,eligibleMoved);
  row.lexicalMoved=eligibleMoved.size;
  const pretrained=structuredClone(lexical);
  row.grammarAttempts=planSourceSupport(pretrained,rec.pretrainedOn);
  const admitted=new Set(row.grammarAttempts.filter(a=>a.status==='nominally_valid_prephysics_source_on').map(a=>a.childId));
  strictPreflight(lexical,pretrained,admitted);
  if(geometryIssues(lexical).length||geometryIssues(pretrained).length||!validateScene(pretrained).ok)
   throw Error('Invalid source-derived physical layout');
  const start=performance.now();
  const control=checkNative('control',original,rec.sourceText);
  const lexicalState=checkNative('lexical',lexical,rec.sourceText);
  const learnedState=checkNative('learned',pretrained,rec.sourceText);
  row.runtimeMs=+(performance.now()-start).toFixed(2);
  const ids=a=>a.bodyStates.map(x=>x.id).sort();
  if(JSON.stringify(ids(control))!==JSON.stringify(ids(lexicalState))||
     JSON.stringify(ids(control))!==JSON.stringify(ids(learnedState)))
   throw Error('Not same exact native rigid-body IDs');
  const lookup=x=>new Map(x.bodyStates.map(e=>[e.id,e]));
  for(const key of ids(control)){
   const old=lookup(control).get(key),middle=lookup(lexicalState).get(key),newer=lookup(learnedState).get(key);
   for(const obj of [middle,newer]){
    if(obj.kind!==old.kind||obj.body!==old.body||obj.shape!==old.shape||
       ['x','y','z'].some(k=>Math.abs(obj.size[k]-old.size[k])>1e-9))
     throw Error('Native candidate changed shape/type/body budget');
   }
  }
  const ctl=new Set(control.contactPairs.map(pairkey)),lex=new Set(lexicalState.contactPairs.map(pairkey)),learn=new Set(learnedState.contactPairs.map(pairkey));
  if(!admitted.size&&JSON.stringify([...lex].sort())!==JSON.stringify([...learn].sort()))
   throw Error('Zero learned placement negative control changed native contact');
  const supported=new Set(row.grammarAttempts.filter(a=>a.status==='nominally_valid_prephysics_source_on').map(a=>[a.childId,a.supportId].sort().join('|')));
  row.controlNativeContactCount=ctl.size;
  row.lexicalNativeContactCount=lex.size;
  row.learnedNativeContactCount=learn.size;
  row.grammarSourceContacts= [...supported].filter(x=>learn.has(x)).length;
  row.sameBodyCount=control.bodyStates.length;
  row.baseline=control;row.lexical=lexicalState;row.learned=learnedState;
  row.status='matched_real_native_and_saved';
 }catch(e){row.status='failed';row.reason=String(e.message).slice(0,220);}
 rows.push(row);
 if((index+1)%20===0)console.log('LEGO_NATIVE_PROGRESS',index+1,
  rows.filter(x=>x.status==='matched_real_native_and_saved').length);
}
const good=rows.filter(x=>x.status==='matched_real_native_and_saved');
const sum=key=>good.reduce((n,r)=>n+(r[key]||0),0);
const summary={sourceDescriptions:all.scenes.length,acceptedNativeSameBudget:good.length,
 sceneCompilerRejected:rows.filter(x=>x.status==='original_source_to_geometry_rejected').length,
 physicsOrValidationFailed:rows.filter(x=>x.status==='failed').length,
 recognizedSourceKinds:rows.reduce((n,r)=>n+r.lexicalKinds,0),
 sourceEntitiesActuallyMaterialized:sum('sameBodyCount'),
 controlTrueNativeContacts:sum('controlNativeContactCount'),
 lexicalTrueNativeContacts:sum('lexicalNativeContactCount'),
 learnedTrueNativeContacts:sum('learnedNativeContactCount'),
 sourceGrammarRelations:sum('learnedOnProposals'),
 grammarSupportContacts:sum('grammarSourceContacts'),
 lexicalObjectsMoved:sum('lexicalMoved'),
 sourceCompilerRejectedOriginalRelations:rows.filter(x=>x.status==='original_source_to_geometry_rejected').reduce((n,r)=>n+r.lexicalRelations,0),
 totalWallSeconds:+((performance.now()-begin)/1000).toFixed(2),
 sourceOnlyNoAuthorGoldAndTrueRapier: true,
 noRandomParentPlaceboAttempted:true};
mkdirSync(PATH,{recursive:true,mode:0o700});
const privateFile=PATH+'/lego_source_only_matched_native_130_raw_v1.json';
writeFileSync(privateFile,JSON.stringify({metadata:{frozenSourceOnlySHA256:hash(readFileSync(PATH+'/lego_source_only_frozen_130_raw_v1.json')),
  trueNativeRapier:true,sourceOnlyProposals:true,
  priorDeniedRandomSupportPlaceboNotAttempted:true,
  humanCuratedExternalSourceNoReferenceGoldDuringGeneration:true,
  geometryCatalogStillUncalibrated:true},summary,rows},null,2)+'\n',{flag:'wx',mode:0o600});
const publicResult={metadata:{privateRawSHA256:hash(readFileSync(privateFile)),
 sourceSHA256:hash(readFileSync(PATH+'/lego_source_only_frozen_130_raw_v1.json')),
 sourceCategoryAndSizeUnverifiedAgainstIndependentGold:true},summary,
 scenes:rows.map(r=>({sourceIndex:r.sourceIndex,status:r.status,bodies:r.sameBodyCount||0,
 baselineContacts:r.controlNativeContactCount??null,lexicalContacts:r.lexicalNativeContactCount??null,
 learnedContacts:r.learnedNativeContactCount??null,lexicalMoved:r.lexicalMoved??0,
 grammarAccepted:r.grammarSourceContacts??0,reason:r.reason||null}))};
writeFileSync(new URL('prse_lego_human_matched_native_130_aggregate_v1.json',import.meta.url),JSON.stringify(publicResult,null,2)+'\n',{flag:'wx'});
console.log('LEGO_INDEPENDENT_NATIVE_PHYSICAL',JSON.stringify(summary));
