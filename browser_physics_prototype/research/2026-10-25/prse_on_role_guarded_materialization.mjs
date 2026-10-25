// Source-only "on" role ABSTENTION applied BEFORE layout and actual
// PRSE GameCore/Rapier materialization, not merely to narrative phrasing.
// Same frozen 200 external descriptions, nouns, quantities, real 3D bodies,
// physics rule code, native save contract and observer semantic document.
//
// NO SceneEval author-gold annotation enters this physical world builder.
// Frozen spaCy source PP roles alone decide which preexisting ambiguous ON
// constraints are withheld. Every other source proposal remains unchanged.
// Compare against the earlier independently frozen baseline physical world;
// score the physically frozen scene with author labels in a SEPARATE script.
//
// A physically correct new world is not proof of source sentence entailment,
// human visual realism, or general literary model capability.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import{performance}from'node:perf_hooks';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
import{PRSECurrentSemanticDocument}from'./prse_current_semantic_document.mjs';
import{measureRelation}from'./prse_grounded_relation_narration.mjs';
await initializePhysics();

const directory='/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Unsafe run identifier');
mkdirSync(directory,{recursive:true,mode:0o700});
const inputs=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const roles=JSON.parse(readFileSync(directory+'/prse_source_role_on_200_raw_v1.json')).records;
const prior=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_baseline_200_raw_v2.json')).rows;
const ids=[...Array.from({length:100},(_,i)=>i),
 ...Array.from({length:100},(_,i)=>100+i*4)];
if(prior.length!==200)throw Error('Baseline frozen source selection mismatch');
const roleBy=new Map(roles.map(x=>[x.sourceId+':'+x.sourceRelationIndex,x]));
const hash=x=>createHash('sha256').update(x).digest('hex');
const started=performance.now(),results=[];
function physicalWorld(w){
 const entities=w.scene.entities.filter(e=>e.source!=='provisional_3D_room_boundary'
  &&!e.state?.destroyed&&w.active.has(e.id));
 const bodies=entities.map(e=>({id:e.id,kind:e.kind,size:{...e.size},
  position:{...w.active.get(e.id).translation()},
  rotation:{...w.active.get(e.id).rotation()},shape:e.shape,
  source:e.source,supportId:e.supportId,body:e.body}));
 const contacts=[];
 for(let i=0;i<entities.length;i++)for(let j=i+1;j<entities.length;j++){
  const a=w.active.get(entities[i].id),b=w.active.get(entities[j].id);
  let count=0;
  for(let x=0;x<a.numColliders();x++)
  for(let y=0;y<b.numColliders();y++)
   w.game.world.contactPair(a.collider(x),b.collider(y),m=>count+=m.numContacts());
  if(count)contacts.push({a:entities[i].id,b:entities[j].id,contactCount:count});
 }
 return {bodies,contacts};
}
for(let i=0;i<ids.length;i++){
 const id=ids[i],p=inputs[id],base=prior[i];
 if(base.id!==id)throw Error('Frozen physical baseline sourceID mismatch');
 const source=p.relations.map((r,index)=>({r,index}));
 const sourceOn=source.filter(({r})=>r.kind==='object'&&r.type==='on');
 const acceptedOn=sourceOn.filter(({index})=>
  roleBy.get(id+':'+index)?.status==='source_syntax_role_candidate');
 for(const {index}of sourceOn)if(!roleBy.has(id+':'+index))throw Error('Missing frozen source-only syntax eligibility');
 const filtered={...p,relations:source.filter(({r,index})=>r.kind!=='object'||r.type!=='on'||
  roleBy.get(id+':'+index).status==='source_syntax_role_candidate').map(x=>x.r)};
 const row={sourceId:id,subset:id<100?'human':'assisted',
  preexistingBaselineStatus:base.status,
  sourceOnClaims:sourceOn.length,sourceRoleAcceptedOnClaims:acceptedOn.length,
  sourceRoleAbstainedOnClaims:sourceOn.length-acceptedOn.length,status:'not_run'};
 if(base.status!=='native_simulated'){
  row.status='original_scene_not_physically_valid';results.push(row);continue;
 }
 const scene=repairScene(filtered,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!scene.accepted||geometryIssues(scene.scene).length){
  row.status='filtered_scene_invalid';results.push(row);continue;
 }
 let story=null,loaded=null;
 try{
  const w=new PRSELoop(scene.scene);w.tick(38);
  story=new PRSESourceRevision(w,filtered.relations,{observerRadius:9});
  const current=new PRSECurrentSemanticDocument(story);
  const first=current.record();
  const initial=physicalWorld(w);
  const baselineBodies=base.bodyStates;
  const originalIds=new Set(baselineBodies.map(e=>e.id));
  const nowIds=new Set(initial.bodies.map(e=>e.id));
  if(originalIds.size!==nowIds.size||
    ![...originalIds].every(x=>nowIds.has(x))||
    w.scene.prose!==p.text)
   throw Error('Abstaining from unsupported source ON constraints altered original body IDs/prose');
  const originalBodyPositions=new Map(baselineBodies.map(x=>[x.id,x.position]));
  row.initial3DBodyCount=initial.bodies.length;
  row.initialContactPairCount=initial.contacts.length;
  row.originalBodyIDsPreserved=true;
  row.changedEntityPositionCount=initial.bodies.filter(x=>{
   const y=originalBodyPositions.get(x.id),z=x.position;
   return Math.hypot(y.x-z.x,y.y-z.y,y.z-z.z)>.01;
  }).length;
  row.initialBodyStates=initial.bodies;
  row.initialNativeContactPairs=initial.contacts;
  row.sourceOnOutcomes=sourceOn.map(({r,index})=>({
   sourceRelationIndex:index,sourceA:r.a,sourceB:r.b,
   roleAccepted:roleBy.get(id+':'+index).status==='source_syntax_role_candidate',
   physical:measureRelation(w,r).truth}));
  row.sourceClaimedPhysicalOnTrue=row.sourceOnOutcomes.filter(x=>x.physical==='true').length;
  row.sourceClaimedPhysicallyTrueAndRoleAccepted=row.sourceOnOutcomes.filter(x=>x.physical==='true'&&x.roleAccepted).length;
  row.sourceClaimedPhysicallyTrueAndRoleAbstained=row.sourceOnOutcomes.filter(x=>x.physical==='true'&&!x.roleAccepted).length;
  row.currentInitialSourceClaimCount=first.current.relationClaimCounts;
  // Exact ON-only source predicate count. Earlier v1/v2 study mistakenly
  // included ALL verified source relationships in this per-type diagnostic.
  // Original raw outputs are retained; corrected v3 uses an exclusive file.
  row.narratedTrueSourceOnCount=first.current.verifiedTextClauses.filter(x=>
   x.type==='physically_verified_source_relation'&&x.ids.length===2&&
   filtered.relations[x.sourceRelationIndex]?.kind==='object'&&
   filtered.relations[x.sourceRelationIndex]?.type==='on').length;
  row.currentTextBefore=first.current.text;
  // One predeclared genuine native physical cause in scenes with an actual
  // movable object. Prefer child of syntax-gated uniquely identified source
  // support only when that physical source relation is initially TRUE;
  // otherwise use the first existing dynamic entity. Never use gold.
  const chosen=sourceOn.find(({r,index})=>{
   const gate=roleBy.get(id+':'+index);
   if(gate.status!=='source_syntax_role_candidate')return false;
   const actual=w.scene.entities.filter(e=>e.kind===r.a&&e.source!=='provisional_3D_room_boundary');
   return actual.length===1&&actual[0].body==='dynamic'&&
    measureRelation(w,r).truth==='true';
  });
  const movable=chosen?w.scene.entities.find(e=>e.kind===chosen.r.a):
   w.scene.entities.find(e=>e.body==='dynamic'&&!e.state?.destroyed);
  if(movable){
   row.actionTargetId=movable.id;row.actionSourceRoleGated=Boolean(chosen);
   if(!w.applyImpulse(movable.id,{x:3,y:.8,z:.5}))
    throw Error('Authoritative native GameCore refused real physical action');
   w.tick(95);
   const delta=current.record();
   row.afterImpulseMeaningfulRevision=delta.changed;
   row.currentTextAfter=delta.current.text;
   row.sourceTruthAfterImpulse=delta.current.relationClaimCounts;
   row.physicalEvents=w.events.filter(e=>e.ids?.includes(movable.id)).length;
  }
  const archive=JSON.parse(JSON.stringify(current.snapshot()));
  const copy=PRSECurrentSemanticDocument.restore(archive);
  if(!copy.ok)throw Error('Native physical plus source/observer/document transaction rejected: '+copy.reason);
  loaded=copy.document;
  row.exactCurrentTextAfterNativeReentry=current.current().text===loaded.current().text;
  row.fullOriginalLiterarySourcePreserved=loaded.story.sourceArchive().originalText===p.text;
  row.nativeWorldAndSemanticClockEqual=Math.abs(loaded.story.loop.time-w.time)<1e-6;
  row.unchangedSemanticRecordDoesNotRepeat=!loaded.record().changed;
  if(!row.exactCurrentTextAfterNativeReentry||
   !row.fullOriginalLiterarySourcePreserved||
   !row.nativeWorldAndSemanticClockEqual||
   !row.unchangedSemanticRecordDoesNotRepeat)
   throw Error('Current literary/native physics save consistency failed');
  row.status='native_valid_source_guarded';
 }catch(e){row.status='failure';row.error=String(e.message).slice(0,230);}
 finally{loaded?.dispose();story?.dispose();}
 results.push(row);
 if((i+1)%30===0)console.log('PROGRESS',i+1,'of',ids.length);
}
const valid=results.filter(x=>x.status==='native_valid_source_guarded');
const sum=f=>valid.reduce((n,x)=>n+f(x),0);
const summary={
 frozenSourceDescriptions:ids.length,
 originalAcceptedNativeScenes:prior.filter(x=>x.status==='native_simulated').length,
 sourceGuardedAcceptedNativeScenes:valid.length,
 sourceGuardedPhysicsFailures:results.filter(x=>x.status==='failure').length,
 sourceGuardedGeometryRejections:results.filter(x=>x.status==='filtered_scene_invalid').length,
 originalLiterarySourcesAndRealBodyIDsPreserved:sum(x=>Number(x.originalBodyIDsPreserved&&x.fullOriginalLiterarySourcePreserved)),
 parsedOnClaimsInAccepted:sum(x=>x.sourceOnClaims),
 roleAcceptedOnClaims:sum(x=>x.sourceRoleAcceptedOnClaims),
 roleAbstainedOnClaims:sum(x=>x.sourceRoleAbstainedOnClaims),
 actual3DOnRelationsTrue:sum(x=>x.sourceClaimedPhysicalOnTrue),
 actual3DOnRelationsTrueWithSourceSyntaxGate:sum(x=>x.sourceClaimedPhysicallyTrueAndRoleAccepted),
 physicalOnTrueButNoSourceRoleProof:sum(x=>x.sourceClaimedPhysicallyTrueAndRoleAbstained),
 actualNativeInterobjectRapierContactPairs:sum(x=>x.initialContactPairCount),
 changedPhysicalBodyPositionsRelativeToBaseline:sum(x=>x.changedEntityPositionCount),
 currentDocumentNativeSaveVerifications:sum(x=>Number(x.exactCurrentTextAfterNativeReentry)),
 actualNativeGameCorePhysicalActions:sum(x=>Number(Boolean(x.actionTargetId))),
 actionProducedMeaningfulSemanticRevision:sum(x=>Number(x.afterImpulseMeaningfulRevision===true)),
 originalSourceRepresentationNotRewritten:sum(x=>Number(x.fullOriginalLiterarySourcePreserved)),
 durationWallSeconds:+((performance.now()-started)/1000).toFixed(2)};
const obj={metadata:{
 method:'Frozen pretrained source-only on-PP role abstention before source constraint layout',
 benchmark:'Same first100 human + every fourth assisted100 frozen SceneEval scene descriptions as previous owned research',
 authoritative3D:'Native original PRSE GameCore/Rapier physics and full native whole-world physical/semantic/observer save',
 warning:'No author SceneEval gold was consulted; source PP syntax not full entailment; physical dimensions, visuals/3D assets and repeated object references unverified'},
 summary,results};
const path=directory+'/prse_source_syntax_guarded_native_200_raw_'+version+'.json';
writeFileSync(path,JSON.stringify(obj,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_source_syntax_guarded_native_200_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...obj.metadata,privateNativeRawSHA256:hash(readFileSync(path))},
 summary,cases:results.map(x=>({sourceId:x.sourceId,status:x.status,
 onProposals:x.sourceOnClaims,onAccepted:x.sourceRoleAcceptedOnClaims,
 onAbstained:x.sourceRoleAbstainedOnClaims,actualTrue:x.sourceClaimedPhysicalOnTrue,
 trueWithRole:x.sourceClaimedPhysicallyTrueAndRoleAccepted,
 error:x.error||null}))},null,2)+'\n',{flag:'wx'});
console.log('PRE_LAYOUT_SOURCE_ROLE_ABSTENTION',JSON.stringify(summary));
