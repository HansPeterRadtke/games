// PRSE evidence-driven architectural comparison: preserve ALL uncertain source
// relation hypotheses rather than hard-deleting them before 3D layout.
//
// Full 197 previously physically accepted external SceneEval rooms, exact
// SAME baseline GameCore/Rapier geometry, gravity, contact, native source ID,
// event core and native whole-world save/reentry. The owner-original prose
// and every parser-proposed source relation persist as source hypothesis;
// narrator may only claim syntax-role-approved AND physically true "on".
// Other physically true supports remain PHYSICAL facts only, and uncertain
// source interpretations remain stored (not treated as false/forgotten).
//
// No official author annotations are opened by this inference study. Prior
// independent source ON annotation scores are evaluated separately once these
// native outcomes have been frozen to owner-private files.
//
// Actual physical action: one fixed impulse in available dynamic scenes;
// compare source statuses after real GameCore steps and exact native restore.
// No new GPU, voice, render or live game process changes.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEMeaningHypotheses}from'./prse_source_hypothesis_ledger.mjs';
await initializePhysics();
const privateDir='/data/var/games/prse_semantic_research/runs/2026-10-25-source-hypotheses';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Invalid independent output version');
mkdirSync(privateDir,{recursive:true,mode:0o700});
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const roleRows=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop/prse_source_role_on_200_raw_v1.json')).records;
const bySource=new Map();
for(const r of roleRows){
 if(!bySource.has(r.sourceId))bySource.set(r.sourceId,[]);
 bySource.get(r.sourceId).push(r);
}
const initialBase=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_baseline_200_raw_v2.json')).rows;
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+i*4)];
const sha=b=>createHash('sha256').update(b).digest('hex');
const start=performance.now(),all=[];
for(let k=0;k<ids.length;k++){
 const sourceId=ids[k],p=proposals[sourceId],base=initialBase[k];
 if(base.id!==sourceId)throw Error('Original external-source identifier differs from frozen physical baseline');
 const r={sourceId,subset:sourceId<100?'human':'assisted',
  status:'not_started',originalSourceOnClaims:0};
 if(base.status!=='native_simulated'){r.status='original_geometry_rejected';all.push(r);continue;}
 const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!layout.accepted||geometryIssues(layout.scene).length){
  r.status='baseline_layout_changed';all.push(r);continue;
 }
 let ledger=null,again=null;
 try{
  const native=new PRSELoop(layout.scene);
  native.tick(38);
  ledger=new PRSEMeaningHypotheses(native,p,bySource.get(sourceId)||[]);
  const init=ledger.record(),row=init.current;
  const origIds=new Set(base.bodyStates.map(x=>x.id));
  const nowIds=new Set([...native.active].map(([id])=>id).filter(id=>
   native.entities.has(id)&&native.entities.get(id).source!=='provisional_3D_room_boundary'));
  if(origIds.size!==nowIds.size||[...origIds].some(id=>!nowIds.has(id)))
   throw Error('Non-destructive source hypothesis ledger modified materialized native body IDs');
  r.historicalSourceSHA256=sha(Buffer.from(native.scene.prose));
  r.originalBodyCount=origIds.size;
  r.allOriginalRelationsStillRecorded=row.sourceProposalsPreserved;
  r.originalSourceOnClaims=row.sourceHypotheses.filter(x=>
   x.sourceRelation.kind==='object'&&x.sourceRelation.type==='on').length;
  r.onSyntaxApproved=row.syntaxApprovedSourceOnRelations;
  r.onUncertainPreserved=row.undecidedAndRetainedONRelations;
  r.onNativePhysicallyTrue=row.sourceHypotheses.filter(x=>
   x.sourceRelation.kind==='object'&&x.sourceRelation.type==='on'&&
   x.physicalTruth==='true').length;
  r.onNativePhysicallyTrueAndRoleApproved=row.sourceHypotheses.filter(x=>
   x.sourceRelation.kind==='object'&&x.sourceRelation.type==='on'&&
   x.eligibleForSourceWordedPresentFact).length;
  r.onNativePhysicallyTrueAndSourceUnresolved=row.sourceHypotheses.filter(x=>
   x.sourceRelation.kind==='object'&&x.sourceRelation.type==='on'&&
   x.physicallyTrueButSourceRoleUnresolved).length;
  r.onRecordedTrueButUndecidedSourceDoesNotGetSourceProse=
   row.verifiedPhysicalClauses.filter(c=>
    c.type==='physically_verified_source_relation').length===
   r.onNativePhysicallyTrueAndRoleApproved;
  if(!r.onRecordedTrueButUndecidedSourceDoesNotGetSourceProse)
   throw Error('Unverified source ON role promoted to source-worded prose');
  if(r.allOriginalRelationsStillRecorded!==p.relations.length ||
     r.onSyntaxApproved+r.onUncertainPreserved!==r.originalSourceOnClaims)
   throw Error('A source-relation hypothesis was lost when source syntax abstained');
  const afterSame=ledger.record();
  if(afterSame.changed)throw Error('Physical passage without actual semantic change produced duplicate hypothesis journal');
  const movable=native.scene.entities.find(e=>e.body==='dynamic'&&!e.state?.destroyed&&native.active.has(e.id));
  if(movable){
   const impulse={x:3,y:.8,z:.5};
   if(!native.applyImpulse(movable.id,impulse))throw Error('Actual GameCore impulse refused');
   native.tick(95);
   r.realPhysicalImpulse=true;r.movedObjectId=movable.id;
   const delta=ledger.record();
   r.semanticTruthChangedAfterAction=delta.changed;
   const later=delta.current.sourceHypotheses;
   r.afterImpulseOnTrue=later.filter(x=>x.sourceRelation.type==='on'&&x.sourceRelation.kind==='object'&&
    x.physicalTruth==='true').length;
   r.afterImpulseOnFalse=later.filter(x=>x.sourceRelation.type==='on'&&x.sourceRelation.kind==='object'&&
    x.physicalTruth==='false').length;
   r.afterImpulseOnUnknown=later.filter(x=>x.sourceRelation.type==='on'&&x.sourceRelation.kind==='object'&&
    x.physicalTruth==='unknown').length;
  }else r.realPhysicalImpulse=false;
  const save=JSON.parse(JSON.stringify(ledger.snapshot()));
  const restored=PRSEMeaningHypotheses.restore(save);
  if(!restored.ok)throw Error('Trusted full native GameCore/semantic/source/observer hypothesis restore failed: '+restored.reason);
  again=restored.ledger;
  const current=ledger.current(),replayed=again.current();
  r.restoredSourceCountAndRoleEvidence=
   JSON.stringify(current.sourceHypotheses)===JSON.stringify(replayed.sourceHypotheses);
  r.restoredSourceLiteralText=again.story.sourceArchive().originalText===p.text;
  r.restoredHistoricallyUnresolvedCount=replayed.undecidedAndRetainedONRelations;
  r.restoredNativeActiveBodyIDs=[...again.story.loop.active.keys()].filter(id=>
   again.story.loop.entities.has(id)&&
   again.story.loop.entities.get(id).source!=='provisional_3D_room_boundary').sort();
  r.originalGeometryUnmodified=origIds.size===r.restoredNativeActiveBodyIDs.length &&
   [...origIds].every(id=>r.restoredNativeActiveBodyIDs.includes(id));
  r.savedTransactionDidNotInventHistory=!again.record().changed;
  if(!r.restoredSourceCountAndRoleEvidence||!r.restoredSourceLiteralText||
   !r.originalGeometryUnmodified||!r.savedTransactionDidNotInventHistory)
   throw Error('Source hypotheses, native physics IDs or history were changed after full save');
  r.status='native_source_hypotheses_preserved';
 }catch(e){r.status='failed';r.reason=String(e.message).slice(0,230);}
 finally{again?.dispose();ledger?.dispose();}
 all.push(r);
 if((k+1)%25===0)console.log('SOURCE_HYPOTHESES_PROGRESS',k+1,'of',ids.length);
}
const good=all.filter(x=>x.status==='native_source_hypotheses_preserved');
const sum=f=>good.reduce((n,x)=>n+f(x),0);
const summary={
 sourceDescriptions:ids.length,
 physicallyAcceptedExistingScenes:initialBase.filter(x=>x.status==='native_simulated').length,
 sourceHypothesisLedgerAndFullNativePhysicsSavePassed:good.length,
 unanticipatedFailures:all.filter(x=>x.status==='failed').length,
 baselineInvalidScenes:all.filter(x=>x.status==='original_geometry_rejected').length,
 sourceOriginalParsedRelationsRetained:sum(x=>x.allOriginalRelationsStillRecorded),
 originalONSourceHypothesesRetained:sum(x=>x.originalSourceOnClaims),
 originalONRelationsWithSourceSyntaxEvidence:sum(x=>x.onSyntaxApproved),
 originalONSourceRelationsWithUnresolvedRoleKept:sum(x=>x.onUncertainPreserved),
 physicallyConfirmedOriginalONRelationsRetained:sum(x=>x.onNativePhysicallyTrue),
 physicallyTrueOnAndSourceRoleApproved:sum(x=>x.onNativePhysicallyTrueAndRoleApproved),
 physicallyTrueOnButSourceRoleUnresolved:sum(x=>x.onNativePhysicallyTrueAndSourceUnresolved),
 scenesWithActualGameCorePhysicalImpulse:sum(x=>Number(x.realPhysicalImpulse)),
 scenesWithNewHypothesisSemanticVersionAfterAction:sum(x=>Number(x.semanticTruthChangedAfterAction===true)),
 originalAllRealBodyIDsKept:sum(x=>Number(x.originalGeometryUnmodified)),
 sourceHistoricallyUncertainHypothesesSurvivedSave:sum(x=>x.restoredHistoricallyUnresolvedCount),
 futureAuthorGoldAndIndependent3DAssetTruthNotUsed:true,
 wallSeconds:+((performance.now()-start)/1000).toFixed(2)};
const full={metadata:{
 source:'Frozen 200 SceneEval text proposals and original actual 197 native GameCore/Rapier source scenes, SAME pre-existing grammar roles',
 noGoldInModelOrPhysicalWorld:true,
 scope:'Full original source interpretation hypotheses preserved despite grammar abstention; only strongly grammatical + physically confirmed ON facts eligible for source wording',
 uncertainty:'Pretrained syntactic match is not definitive author entailment; no new source-blind claim of lexical or artistic correctness',
 noProductionEditsOrGPU:true},summary,results:all};
const outfile=privateDir+'/prse_non_destructive_source_hypothesis_native_200_raw_'+version+'.json';
writeFileSync(outfile,JSON.stringify(full,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_non_destructive_hypotheses_200_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...full.metadata,privateRawSHA256:sha(readFileSync(outfile))},
  summary,cases:all.map(x=>({id:x.sourceId,status:x.status,
   sourceON:x.originalSourceOnClaims??null,
   grammarApproved:x.onSyntaxApproved??null,
   undecidedPersisted:x.restoredHistoricallyUnresolvedCount??null,
   physicalTrueOn:x.onNativePhysicallyTrue??null,
   physicalTrueSourceUncertain:x.onNativePhysicallyTrueAndSourceUnresolved??null,
   error:x.reason??null}))},null,2)+'\n',{flag:'wx'});
console.log('FULL_SOURCE_HYPOTHESIS_COMPARISON',JSON.stringify(summary));
