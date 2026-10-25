// A new acceptance gate for PRSE's central semantic ↔ native 3D ↔ semantic
// loop: the world document must distinguish an ACTUAL counted rigid-body
// population from the quantity a language interpreter guessed or extracted.
//
// This benchmark freezes earlier SceneEval source descriptions and their
// complete interpreter outputs, and runs EXACT real GameCore/Rapier world
// materialization and native saved-state reentry.  No author annotation data
// enters it. A separate scorer opens official gold labels ONLY after results
// are saved on owner-private Nitro storage.
//
// IMPORTANT: agreement of the physical population with the compiler's
// proposed count is tautological unless independently compared with source
// annotations. We deliberately report such circular agreement as diagnostic,
// never as source-semantic success.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import{performance}from'node:perf_hooks';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSESourceQuantityEvidence}from'./prse_source_quantity_evidence.mjs';

await initializePhysics();
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
if(source.length!==500)throw Error('Expected frozen external source count 500');
const ids=[...Array.from({length:100},(_,i)=>i),
 ...Array.from({length:100},(_,i)=>100+4*i)];
const directory='/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance';
mkdirSync(directory,{recursive:true,mode:0o700});
const results=[],started=performance.now();
let analyzedSpans=0,explicit=0,implicit=0,repeatedTypes=0,parsedNegation=0;
for(const p of source){
 const nByType=new Map();
 for(const m of p.mentions){
  analyzedSpans++;
  if(m.certainty==='quantified')explicit++;else implicit++;
  nByType.set(m.type,(nByType.get(m.type)||0)+1);
 }
 repeatedTypes+=Number([...nByType.values()].some(x=>x>1));
 parsedNegation+=(Object.values(p.quantities).some(q=>q.count===0)?1:0);
}
for(let i=0;i<ids.length;i++){
 const id=ids[i],proposal=source[id],layout=repairScene(proposal,{maxSweeps:2,maxAttemptsPerScene:150});
 const rec={sourceID:id,sourceSubset:id<100?'human':'assisted',status:'not_run',
  sourceProposedTypes:Object.keys(proposal.quantities).length,
  mentionCount:proposal.mentions.length,
  repeatedTypes:Object.keys(proposal.quantities).filter(k=>proposal.mentions.filter(m=>m.type===k).length>1).length,
  explicitSourceAbsenceTypes:Object.entries(proposal.quantities).filter(([k,q])=>q.count===0).map(([k])=>k),
  sourceMentionSpanIntegrity:'pending'};
 if(!layout.accepted||geometryIssues(layout.scene).length){
  rec.status='geometrically_rejected';results.push(rec);continue;
 }
 let loop=null,restored=null;
 try{
  loop=new PRSELoop(layout.scene);loop.tick(24);
  const before=new PRSESourceQuantityEvidence(loop,proposal).evaluate();
  rec.nativeWorldFullyMaterialized=before.fullyPhysicallyMaterialized;
  rec.rawWorldObjectCount=before.materializedEntityCount;
  rec.sourceClaims=before.sourceCountClaims.map(x=>({
   type:x.type,requestedCount:x.request.count,requestedOp:x.request.op,
   originalMentionCount:x.mentionCount,explicitMentions:x.explicitMentionCount,
   implicitMentions:x.implicitMentionCount,negatedMentions:x.negatedMentions,
   scope:x.sourceCountScope,referenceUniqueness:x.referenceUniqueness,
   physicallyMaterializedCount:x.physicallyMaterializedCount,
   sourceCompilerNumericMatch:x.sourceCompilerNumericMatch,
   sourceConservativePresence:x.sourceConservativePresence,
   explicitSourceAbsenceMatch:x.explicitSourceAbsenceMatch,
   sourceExactGlobalCountEntailed:x.sourceExactGlobalCountEntailed,
   physicallyVerifiedAttributes:x.sourceAttributesPhysicallyIndependentlyVerified,
   mentionOffsets:x.mentionOffsets}));
  rec.physicalTypeCounts=before.currentPhysicalTypeCounts.map(x=>({
   type:x.type,materialized:x.materializedBodies,
   unmaterialized:x.unloadedSemanticIdentities,
   destroyed:x.destroyedHistoricalIdentities,
   materialLabels:x.actualPhysicalMaterials.map(p=>p.physicalSolverMaterial)}));
  rec.sourceMentionSpanIntegrity=before.sourceCountClaims.every(x=>
   x.mentionOffsets.every(pos=>proposal.text.slice(pos.start,pos.end).length>0));
  const world=JSON.parse(JSON.stringify(loop.snapshot()));
  const clone=PRSELoop.restore(world);
  if(!clone.ok)throw Error('GameCore world native state could not reload');
  restored=clone.loop;
  const again=new PRSESourceQuantityEvidence(restored,proposal).evaluate();
  rec.identicalCountsAfterActualGameCoreSave=JSON.stringify(before.currentPhysicalTypeCounts)===
   JSON.stringify(again.currentPhysicalTypeCounts);
  rec.identicalCountClaimEvidenceAfterSave=JSON.stringify(before.sourceCountClaims)===
   JSON.stringify(again.sourceCountClaims);
  rec.sourceProseUnchanged=restored.scene.prose===proposal.text;
  // Move a *real* body, if any, and verify counting is about persistent
  // instances, not every frame's position changes or transient contact.
  const moving=loop.scene.entities.find(x=>x.body==='dynamic'&&!x.state.destroyed);
  if(moving){
   if(!loop.applyImpulse(moving.id,{x:2.8,y:.7,z:.9}))throw Error('Real physics impulse denied');
   loop.tick(62);
   const changed=new PRSESourceQuantityEvidence(loop,proposal).evaluate();
   rec.worldBodyCountAfterRealMovement=changed.materializedEntityCount;
   rec.countUnchangedByMovement=changed.materializedEntityCount===before.materializedEntityCount;
  }
  if(!rec.identicalCountsAfterActualGameCoreSave||!rec.identicalCountClaimEvidenceAfterSave||
     !rec.sourceProseUnchanged||rec.countUnchangedByMovement===false)
   throw Error('Physical/source numerical facts not invariant under GameCore native save or motion');
  rec.status='native_3d_verified';
 }catch(e){rec.status='failed';rec.error=String(e.message).slice(0,180);}
 finally{restored?.dispose();loop?.dispose();}
 results.push(rec);
 if((i+1)%25===0)console.log('PROGRESS',i+1,'of',ids.length);
}
const successful=results.filter(x=>x.status==='native_3d_verified');
const sum=(f)=>successful.reduce((n,x)=>n+f(x),0);
const summary={
 sourceDescriptionsTotal:500,
 descriptionsWithRepeatedObjectTypeMentions:repeatedTypes,
 sourceMentionSpansTotal:analyzedSpans,
 sourceMentionsExplicitlyQuantified:explicit,
 sourceMentionsWithoutExplicitNumericalQuantifier:implicit,
 parserProposedNegatedTypeInSourceScenes:parsedNegation,
 physicalSampleDescriptions:ids.length,
 acceptedAndActuallySaved:successful.length,
 rejectedSceneGeometry:results.filter(x=>x.status==='geometrically_rejected').length,
 failureCases:results.filter(x=>x.status==='failed').length,
 physicalBodiesAcrossAcceptedScenes:sum(x=>x.rawWorldObjectCount),
 numericSourceProposalCount:sum(x=>x.sourceClaims.length),
 numericalCompilerMatchTrue:sum(x=>x.sourceClaims.filter(c=>c.sourceCompilerNumericMatch==='true').length),
 numericalCompilerMatchFalse:sum(x=>x.sourceClaims.filter(c=>c.sourceCompilerNumericMatch==='false').length),
 numericalCompilerMatchUnknown:sum(x=>x.sourceClaims.filter(c=>c.sourceCompilerNumericMatch==='unknown').length),
 explicitSourceAbsencesChecked:sum(x=>x.sourceClaims.filter(c=>c.negatedMentions>0).length),
 explicitSourceAbsencesPhysicallyPresentDespiteNegation:sum(x=>x.sourceClaims.filter(c=>
  c.negatedMentions>0&&c.physicallyMaterializedCount>0).length),
 sourceTypeClaimsWithRepeatedReferents:sum(x=>x.sourceClaims.filter(c=>c.originalMentionCount>1).length),
 originalExactCountClaimsIndependentlyEntailed:sum(x=>x.sourceClaims.filter(c=>
  c.sourceExactGlobalCountEntailed!=='unknown').length),
 objectVisualAttributesIndependentlyVerified:sum(x=>x.sourceClaims.filter(c=>
  c.physicallyVerifiedAttributes===true).length),
 matchedNativeSaveCounts:sum(x=>Number(x.identicalCountsAfterActualGameCoreSave)),
 originalProsePreserved:sum(x=>Number(x.sourceProseUnchanged)),
 wallSeconds:+((performance.now()-started)/1000).toFixed(2)};
const raw={metadata:{description:'Frozen external source quantity parser proposal vs real PRSE GameCore/Rapier physical count and native save',
 sourceAnnotationsNeverLoaded:true,noGPUorLLM:true,
 limitation:'A physical count produced FROM the interpreter proposal does not establish independent faithful source quantifier interpretation',
 sourceTextNotInPublicSafeResult:true},summary,results};
const file=directory+'/prse_source_quantity_physics_200_raw_v1.json';
writeFileSync(file,JSON.stringify(raw,null,2)+'\n',{flag:'wx',mode:0o600});
const agg={metadata:{...raw.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(file)).digest('hex'),
 privateRawPath:file},summary,
 scenarios:results.map(x=>({id:x.sourceID,status:x.status,sourceTypes:x.sourceProposedTypes,
  compilerQuantities:x.sourceClaims?.length||0,realBodies:x.rawWorldObjectCount??null,
  repeatedTypes:x.repeatedTypes,absentTypes:x.explicitSourceAbsenceTypes,
  error:x.error||null}))};
writeFileSync(new URL('prse_source_quantity_physics_200_aggregate_v1.json',import.meta.url),
 JSON.stringify(agg,null,2)+'\n',{flag:'wx'});
console.log('FINAL',JSON.stringify(summary));
