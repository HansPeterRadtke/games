// Full frozen SceneEval-source quantity-scoped CURRENT WORLD textual audit.
//
// Compare ordinary per-entity physical present tense with grouped explicitly
// scoped numerical current-world text on the SAME authoritative GameCore/Rapier
// state. Both use the source-linked PRSE current semantic document/observer.
//
// Independently author-annotated gold labels are NOT read here. Self-matching
// source quantifier proposals must never be advertised as source fidelity.
// All complete 200-scene raw rows remain in owner-private Nitro storage.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {PRSESourceRevision}from'./prse_source_revision_story.mjs';
import {PRSEQuantityScopedWorld}from'./prse_quantity_scoped_world.mjs';

await initializePhysics();
const inputs=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Unsafe run version');
const ids=[...Array.from({length:100},(_,i)=>i),
 ...Array.from({length:100},(_,i)=>100+i*4)];
const directory='/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance';
mkdirSync(directory,{recursive:true,mode:0o700});
const rows=[],t0=performance.now();
const sum=(items,f)=>items.reduce((n,x)=>n+f(x),0);
for(let i=0;i<ids.length;i++){
 const id=ids[i],p=inputs[id],layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const record={sourceID:id,sourceSubset:id<100?'human':'assisted',status:'not-run'};
 if(!layout.accepted||geometryIssues(layout.scene).length){
  record.status='rejected_geometry';rows.push(record);continue;
 }
 let loop=null,again=null;
 try{
  loop=new PRSELoop(layout.scene);loop.tick(24);
  const scoped=new PRSEQuantityScopedWorld(new PRSESourceRevision(loop,p.relations),p);
  const first=scoped.record();
  const base=scoped.currentDocument.current();
  record.sourceClaimTypes=first.current.countSourceClaims.length;
  record.materializedBodyCount=first.current.bodyCount;
  record.reportedKinds=first.current.counts.filter(e=>e.materializedBodies>0).length;
  record.sourceReferentUnknowns=first.current.countSourceClaims.filter(c=>c.referenceUniqueness==='unknown').length;
  record.explicitAbsenceGrounded=first.current.countSourceClaims.filter(c=>c.explicitSourceAbsenceMatch==='true').length;
  record.compactTextBytes=first.current.proseBytes;
  record.previousPerObjectTextBytes=first.current.baselinePerObjectCurrentProseBytes;
  record.originalProseBytes=Buffer.byteLength(p.text);
  record.actualCurrentText=first.current.text;
  record.textSaysScopedMaterialization=first.current.text.startsWith('In the currently materialized region');
  record.reportedPhysicalRelationCount=base.verifiedTextClauses.filter(c=>
   c.type==='physically_verified_source_relation').length;
  record.actualPresentObjectClaims=base.verifiedTextClauses.filter(c=>
   c.type==='current_physical_presence').length;
  const noSecond=scoped.record();
  if(noSecond.changed)throw Error('Unchanged physics generated new quantity-scope story revision');
  const save=JSON.parse(JSON.stringify(scoped.snapshot()));
  const restored=PRSEQuantityScopedWorld.restore(save);
  if(!restored.ok)throw Error('Native source/count/current world transaction could not reenter: '+restored.reason);
  again=restored.world;
  const same=again.current();
  record.currentTextExactAfterReentry=same.text===first.current.text;
  record.currentCountEvidenceExactAfterReentry=JSON.stringify(same.counts)===JSON.stringify(first.current.counts);
  record.unchangedHistoryDoesNotRepeat=again.record().changed===false;
  record.sameHistoricalLiteraryText=again.story.sourceArchive().originalText===p.text;
  if(!record.currentTextExactAfterReentry||!record.currentCountEvidenceExactAfterReentry||
    !record.unchangedHistoryDoesNotRepeat||!record.sameHistoricalLiteraryText)
   throw Error('Current physically scoped semantic document changed on native full reentry');
  const moving=loop.scene.entities.find(e=>e.body==='dynamic'&&!e.state?.destroyed);
  if(moving){
   if(!loop.applyImpulse(moving.id,{x:2,y:.5,z:.7}))throw Error('Physical impulse failed');
   loop.tick(65);
   const after=new PRSEQuantityScopedWorld(new PRSESourceRevision(loop,p.relations),p).current();
   record.movePreservedInstanceCount=after.bodyCount===first.current.bodyCount;
   if(!record.movePreservedInstanceCount)throw Error('Physical movement altered semantic entity population');
  }
  record.status='verified';
 }catch(e){record.status='failed';record.error=String(e.message).slice(0,210);}
 finally{again?.dispose();loop?.dispose();}
 rows.push(record);
 if((i+1)%25===0)console.log('PROGRESS',i+1,ids.length);
}
const ok=rows.filter(x=>x.status==='verified');
const safe={
 sourceScenes:rows.length,
 acceptedNativeSavedWorlds:ok.length,
 rejectedByGeometry:rows.filter(x=>x.status==='rejected_geometry').length,
 realExecutionFailures:rows.filter(x=>x.status==='failed').length,
 exactNativePhysicsSourceTextAndCountRestoration:ok.filter(x=>x.currentTextExactAfterReentry&&
  x.currentCountEvidenceExactAfterReentry&&x.sameHistoricalLiteraryText).length,
 meaningfulQuantitySourceClaims:sum(ok,x=>x.sourceClaimTypes),
 referentialUniquenessStillUnknown:sum(ok,x=>x.sourceReferentUnknowns),
 explicitlyAbsentSourceClassesPhysicallyGrounded:sum(ok,x=>x.explicitAbsenceGrounded),
 nativePhysicalObjectCount:sum(ok,x=>x.materializedBodyCount),
 physicallyVerifiedSourceRelationshipsInDocument:sum(ok,x=>x.reportedPhysicalRelationCount),
 previousBareEntityPresentStatements:sum(ok,x=>x.actualPresentObjectClaims),
 previousPerObjectTextBytes:sum(ok,x=>x.previousPerObjectTextBytes),
 scopedGroupedPhysicalTextBytes:sum(ok,x=>x.compactTextBytes),
 initialLiterarySourceBytes:sum(ok,x=>x.originalProseBytes),
 changedPhysicalMotionDidNotChangeEntityCounts:ok.filter(x=>x.movePreservedInstanceCount===true).length,
 elapsedSeconds:+((performance.now()-t0)/1000).toFixed(2)};
const details={metadata:{
 source:'Fixed SceneEval descriptions first 100 human + 100 every-fourth assisted, unchanged parser and 3D spatial compiler',
 comparison:'Old per-entity current-document factual text vs explicitly 3D region-scoped grouped physical count prose',
 actualAuthority:'Same native GameCore/Rapier, authoritative object identities, prior observer and trusted native full world snapshot',
 warnings:'Improved economy/readability is NOT independently rated literary quality or original-source quantitative fidelity',
 noGoldOrGPUorLLM:true},summary:safe,results:rows};
const out=directory+'/prse_scoped_quantity_world_text_200_raw_'+version+'.json';
writeFileSync(out,JSON.stringify(details,null,2)+'\n',{flag:'wx',mode:0o600});
const safePublic={
 metadata:{...details.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(out)).digest('hex'),
  privateRawPath:out},summary:safe,
 cases:rows.map(x=>({id:x.sourceID,subset:x.sourceSubset,status:x.status,
  currentBytes:x.compactTextBytes??null,baselineBytes:x.previousPerObjectTextBytes??null,
  physicsBodyCount:x.materializedBodyCount??null,sourceReferenceUnknowns:x.sourceReferentUnknowns??null,
  error:x.error||null}))};
writeFileSync(new URL('prse_scoped_quantity_world_text_200_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify(safePublic,null,2)+'\n',{flag:'wx'});
console.log('FINAL',JSON.stringify(safe));
