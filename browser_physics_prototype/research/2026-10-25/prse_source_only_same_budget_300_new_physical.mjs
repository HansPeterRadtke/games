// New physically untested SceneEval subsets: source-only frozen grammar versus
// exact SAME native Rapier objects before and after grammar-conditioned placement.
// Independent official author source labels are NOT loaded in this phase.
// The full SceneEval corpus has been examined before: this is a new PHYSICAL
// split, not a pristine generalization corpus. No random-parent placebo here.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object,geometryIssues,validateScene} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {recordNativePRSEState,restoreNativePRSEState} from './prse_native_world_transaction.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-26-new-physical-300';
const VERSION='v1';
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const extras=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery/prse_spacy_open_vocab_500_proposals_raw_v1.json')).records;
const proposals=JSON.parse(readFileSync(ROOT+'/prse_source_only_on_nounchunk_300_raw_v1.json')).cases;
const ids=Array.from({length:400},(_,i)=>i+100).filter(i=>(i-100)%4!==0);
if(ids.length!==300||ids.some(id=>id<100||((id-100)%4===0))||source.length!==500||extras.length!==500||proposals.length!==300)throw Error('Unexpected experimental split');
const hash=x=>createHash('sha256').update(x).digest('hex');
const sha=x=>hash(x);
const realSize={x:.24,y:.28,z:.24},maxAdded=16;
const room={minX:-35.7,maxX:-18.0,minZ:5.55,maxZ:17.8};
const collision=(a,b)=>
 ['x','y','z'].every(k=>Math.abs(a.position[k]-b.position[k])<
  (a.size[k]+b.size[k])/2+.014);
function fallbackObject(scene,kind,idx,start,end){
 const token=hash(Buffer.from(kind)).slice(0,7),prefix='sem-'+scene.id.replace(/^sem-/,'');
 const id=prefix+'-candidate-'+kind.slice(0,20).replace(/_/g,'-')+'-'+token+'-'+idx;
 if(scene.entities.some(x=>x.id===id))throw Error('Unexpected identity collision');
 for(let xi=0;xi<29;xi++)for(let zi=0;zi<22;zi++){
  const position={x:room.minX+xi*.6,y:realSize.y/2,z:room.minZ+zi*.54};
  const proposed=object(id,kind,position,realSize,{
    body:'dynamic',material:'unknown',shape:'box',mass:.3,
    name:kind.replace(/_/g,' ')+' '+(idx+1),
    source:'syntax-proposed:'+scene.id+':'+start+':'+end,
    description:'PROVISIONAL TYPE ONLY; generic AABB collider with UNVERIFIED physical scale, mass and source meaning',
    state:{condition:'intact',openVocabularyCandidate:true,
      sourceMeaningIndependentlyVerified:false,
      shapeAndMaterialIndependentlyVerified:false}
  });
  if(!scene.entities.some(e=>!e.state?.destroyed&&collision(e,proposed)))
   return proposed;
 }
 return null;
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


function addFrozenSourceOnlyBodies(scene,p,extra){
 const existing=new Map(),records=[];
 for(const e of scene.entities){
  if(e.state?.destroyed||e.source==='provisional_3D_room_boundary')continue;
  existing.set(e.kind,(existing.get(e.kind)||0)+1);
 }
 for(const c of extra.boundedNewTypes){
  if(p.quantities[c.type]?.count===0)continue;
  const previous=existing.get(c.type)||0,wanted=Math.max(0,Math.min(c.count,12)-previous);
  const proof=extra.candidates.find(x=>x.type===c.type);
  if(!proof||!Array.isArray(proof.sourceOffsets)||p.text.slice(...proof.sourceOffsets)!==proof.sourceText)
   throw Error('Missing original source evidence for generic noun');
  for(let j=0;j<wanted&&records.length<16;j++){
   const candidate=fallbackObject(scene,c.type,j,...proof.sourceOffsets);
   if(!candidate)break;
   scene.entities.push(candidate);existing.set(c.type,(existing.get(c.type)||0)+1);
   records.push({id:candidate.id,kind:c.type,sourceOffsets:proof.sourceOffsets});
  }
 }
 return records;
}
const key=e=>[e.a,e.b].sort().join('|');
function assertMatched(scene,candidate,old,newer,attempts){
 const b=new Map(old.bodyStates.map(x=>[x.id,x]));
 const a=new Map(newer.bodyStates.map(x=>[x.id,x]));
 if(b.size!==a.size||[...a.keys()].some(x=>!b.has(x)))throw Error('Alternative changed actual physical entity IDs');
 for(const [id,x] of a){
  const y=b.get(id);
  if(x.kind!==y.kind||x.body!==y.body||x.shape!==y.shape||
     ['x','y','z'].some(k=>Math.abs(x.size[k]-y.size[k])>1e-9))
    throw Error('Alternative changed object kinds or physical shapes');
 }
 const moved=new Set(attempts.filter(x=>x.status==='nominally_valid_prephysics_source_on').map(x=>x.childId));
 const original=new Map(scene.entities.map(x=>[x.id,x]));
 for(const x of candidate.entities){
  const y=original.get(x.id);if(!y)throw Error('New body appeared');
  if(!moved.has(x.id)&&(['x','y','z'].some(k=>x.position[k]!==y.position[k])||x.supportId!==y.supportId))
   throw Error('Unproposed source object was moved or changed');
 }
 if(!moved.size){
  const c=pairs=>JSON.stringify(pairs.map(key).sort());
  if(c(old.contactPairs)!==c(newer.contactPairs))
   throw Error('Zero-placement negative control unexpectedly altered native contacts');
 }
}
const rows=[],start=performance.now();
for(let n=0;n<ids.length;n++){
 const id=ids[n],p=source[id],extra=extras[id],rel=proposals[n];
 if(id!==Number(p.sourceId)||id!==Number(extra.id)||id!==rel.sourceId||
    p.text!==extra.sourceText||rel.sourceHash!==sha(Buffer.from(p.text)))
  throw Error('Source split/provenance mismatch');
 const original=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const row={sourceId:id,sourceGroup:'assisted',originalAccepted:original.accepted,
   status:'original_scene_not_physically_accepted',candidateCount:rel.proposedOn.length,
   sourceHash:rel.sourceHash,attempts:[],genericCandidates:0};
 if(!original.accepted||geometryIssues(original.scene).length){rows.push(row);continue;}
 let control=null,alt=null,reload=null;
 try{
  const scene=structuredClone(original.scene);
  row.genericCandidates=addFrozenSourceOnlyBodies(scene,p,extra).length;
  if(geometryIssues(scene).length||!validateScene(scene).ok){row.status='generic_geometry_rejected';rows.push(row);continue;}
  control=new PRSELoop(structuredClone(scene));control.tick(38);
  const older=physics(control);
  const candidate=structuredClone(scene);
  row.attempts=planSourceSupport(candidate,rel.proposedOn);
  if(geometryIssues(candidate).length||!validateScene(candidate).ok)
   throw Error('Source attachment invalidated geometry');
  alt=new PRSELoop(candidate);alt.tick(38);
  const newer=physics(alt);
  assertMatched(scene,candidate,older,newer,row.attempts);
  if(alt.scene.prose!==p.text||control.scene.prose!==p.text)
   throw Error('Original author historic source changed');
  const save=recordNativePRSEState(alt);
  const restore=restoreNativePRSEState(JSON.parse(JSON.stringify(save)));
  if(!restore.ok)throw Error('Native save/restore refused');
  reload=restore.loop;
  const saved=physics(reload);
  const k=pairs=>JSON.stringify(pairs.map(key).sort());
  if(saved.bodyStates.length!==newer.bodyStates.length||
     k(saved.contactPairs)!==k(newer.contactPairs)||reload.scene.prose!==p.text)
   throw Error('Physical scene changed after rematerialization');
  const proposed=new Set(row.attempts.filter(a=>a.status==='nominally_valid_prephysics_source_on').map(a=>[a.childId,a.supportId].sort().join('|')));
  const actual=new Set(newer.contactPairs.map(key));
  row.status='same_body_real_native_matched';
  row.oldBodyStates=older.bodyStates;row.oldNativeContactPairs=older.contactPairs;
  row.newBodyStates=newer.bodyStates;row.newNativeContactPairs=newer.contactPairs;
  row.oldNativeContacts=older.contactPairs.length;row.newNativeContacts=newer.contactPairs.length;
  row.bodyCount=newer.bodyStates.length;
  row.placed=row.attempts.filter(a=>a.status==='nominally_valid_prephysics_source_on').length;
  row.actualNewSourcePairs=[...proposed].filter(k=>actual.has(k)).length;
  row.identicalSourceAndNativeEntityBudget=true;row.savedNativeSourceAndContacts=true;
 }catch(e){row.status='failed';row.error=String(e.message).slice(0,240);}
 finally{reload?.dispose();alt?.dispose();control?.dispose();}
 rows.push(row);
 if((n+1)%25===0)console.log('NEW300_NATIVE_PROGRESS',n+1,rows.filter(x=>x.status==='same_body_real_native_matched').length);
}
const accepted=rows.filter(x=>x.status==='same_body_real_native_matched');
const sum=f=>accepted.reduce((n,r)=>n+f(r),0);
const refusals={};for(const r of rows)for(const x of r.attempts)refusals[x.status]=(refusals[x.status]||0)+1;
const summary={sourceDescriptions:ids.length,originalScenesAccepted:rows.filter(x=>x.originalAccepted).length,
 matchedNativeScenarios:accepted.length,failures:rows.filter(x=>x.status==='failed').length,
 geometryRejected:rows.filter(x=>x.status==='generic_geometry_rejected').length,
 totalSamePhysicalBodiesPerArm:sum(x=>x.bodyCount),baselineNativeContactPairs:sum(x=>x.oldNativeContacts),
 sourceOnlyNativeContactPairs:sum(x=>x.newNativeContacts),placed:sum(x=>x.placed),
 sourceOnlyProposedContactsReal:sum(x=>x.actualNewSourcePairs),
 sourceOnlyProposals:sum(x=>x.candidateCount),preplannedAbstentions:refusals,
 zeroPlacementNegativeControlScenes:accepted.filter(x=>x.placed===0).length,
 actualNativeSaveAndSameBodies:accepted.filter(x=>x.identicalSourceAndNativeEntityBudget&&x.savedNativeSourceAndContacts).length,
 elapsedSeconds:+((performance.now()-start)/1000).toFixed(2)};
const dir=ROOT;mkdirSync(dir,{recursive:true,mode:0o700});
const raw=dir+'/prse_source_only_same_budget_native_300_raw_'+VERSION+'.json';
writeFileSync(raw,JSON.stringify({metadata:{sourceSelection:'Remaining three hundred assisted descriptions excluded from prior two-hundred-scene PHYSICAL test; full corpus previously examined',sameBodyNativeComparison:true,originalAuthorGoldNeverOpened:true,sourceOnlyGrammarAndGenericNounCandidatesFrozen:true,realPhysics:'GameCore Rapier 3D'},summary,rows},null,2)+'\n',{flag:'wx',mode:0o600});
const safe={metadata:{rawSHA256:hash(readFileSync(raw)),newPhysicalSubsetOnly:true,generalCorpusNotPristine:true,
 noOfficialAnnotationsRead:true,genericBoxDimensionsUnverified:true},summary,scenes:rows.map(r=>({id:r.sourceId,status:r.status,
 oldContacts:r.oldNativeContacts??null,newContacts:r.newNativeContacts??null,
 newPlacement:r.placed??0,realProposedContacts:r.actualNewSourcePairs??0,bodyCount:r.bodyCount??null,
 reason:r.error??null}))};
writeFileSync(new URL('prse_source_only_same_budget_native_300_aggregate_v1.json',import.meta.url),JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log('NEW300_NATIVE_VERIFIED',JSON.stringify(summary));
