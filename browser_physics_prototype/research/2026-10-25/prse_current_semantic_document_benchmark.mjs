// Source-derived PRSE current-semantic DOCUMENT comparison across a frozen
// external corpus. Compares two prior frozen language parsers only; this study
// does NOT retrain them, open gold annotations, or treat original literary
// prose as current physical truth.
//
// Old baseline: PRSELoop.currentProse() textual facts from stored entity flags.
// New: regenerable current world semantic document with explicit live/latent/
// destroyed entity identities, physically verified relations, source provenance,
// full native 3D save/reentry and semantic revision journal.
//
// Raw source-derived scene rows go to OWNER-PRIVATE Nitro storage; Git receives
// only statistical aggregates, reproducer and file hashes. All methods step
// the SAME existing GameCore/Rapier physics, no second solver or GPU/LLM.
import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createHash}from'node:crypto';
import{performance}from'node:perf_hooks';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{PRSESourceRevision}from'./prse_source_revision_story.mjs';
import{PRSECurrentSemanticDocument}from'./prse_current_semantic_document.mjs';
await initializePhysics();
const mode=process.argv.includes('--union')?'union':process.argv.includes('--deterministic')?'deterministic':null;
if(!mode)throw Error('Specify --union or --deterministic');
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Unsafe versioned output name');
const privateDir='/data/var/games/prse_semantic_research/runs/2026-10-25-current-document';
mkdirSync(privateDir,{recursive:true,mode:0o700});
const inputs=mode==='union'?
 JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model/prse_spacy_sceneeval_500_union_v1.json')).proposalsAll500:
 JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const ids=[...Array.from({length:100},(_,i)=>i),
 ...Array.from({length:100},(_,i)=>100+4*i)];
const start=performance.now(),all=[];
const num=(xs,key)=>xs.reduce((acc,x)=>acc+(x[key]||0),0);
for(let i=0;i<ids.length;i++){
 const id=ids[i],p=inputs[id],layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const result={sourceID:id,parser:mode,subset:id<100?'human':'assisted',
  status:layout.accepted?'started':'source_layout_rejected',
  parsedRelations:p.relations.length,
  countCurrentProseBytes:0,currentDocumentBytes:0,
  sourceArchiveBytes:Buffer.byteLength(p.text),
  physicallyVerifiedRelations:0,physicallyRefutedRelations:0,unverifiableRelations:0,
  materializedEntities:0,latentEntities:0,destroyedEntities:0,
  strictlyAuditedClauses:0,physicalSupportClauses:0,
  physicalSupportUnknown:0,unverifiedSourceRelationsNarrated:0,
  changedSemanticVersions:0,repeatedUnchangedRevisionCount:0,
  nativeSaveRestored:false,identicalNativeText:false,
  futurePhysicsSourceTruthEqual:false};
 if(!layout.accepted||geometryIssues(layout.scene).length){
  all.push(result);continue;
 }
 let original=null,restored=null;
 try{
  original=new PRSELoop(layout.scene);original.tick(24);
  const narrative=new PRSESourceRevision(original,p.relations,{observerRadius:9});
  const current=new PRSECurrentSemanticDocument(narrative);
  const initial=current.record();
  result.status='materialized';
  const doc=initial.current;
  result.countCurrentProseBytes=Buffer.byteLength(original.scene.currentProse||'');
  result.currentDocumentBytes=Buffer.byteLength(doc.text);
  result.physicallyVerifiedRelations=doc.relationClaimCounts.true;
  result.physicallyRefutedRelations=doc.relationClaimCounts.false;
  result.unverifiableRelations=doc.relationClaimCounts.unknown;
  result.materializedEntities=doc.physicallyMaterializedCount;
  result.latentEntities=doc.unloadedCount;
  result.destroyedEntities=doc.historicalDestroyedCount;
  result.strictlyAuditedClauses=doc.verifiedTextClauses.length;
  result.physicalSupportClauses=doc.verifiedTextClauses.filter(c=>
   c.type==='physically_verified_support_not_source_entailed').length;
  result.physicalSupportUnknown=doc.physicalSupportAudit.filter(c=>c.truth==='unknown').length;
  result.unverifiedSourceRelationsNarrated=doc.verifiedTextClauses.filter(c=>
   c.type==='physically_verified_source_relation' &&
   !doc.verifiedRelations.find(x=>x.sourceRelationIndex===c.sourceRelationIndex&&x.truth==='true')).length;
  if(result.unverifiedSourceRelationsNarrated)throw Error('Narrative includes source claims not verified by physics');
  const second=current.record();
  if(second.changed)throw Error('Unchanged native physics generated another semantic world revision');
  result.repeatedUnchangedRevisionCount=second.changed?1:0;
  const candidate=original.scene.entities.find(e=>e.body==='dynamic'&&!e.state?.destroyed);
  if(candidate){
   if(!original.applyImpulse(candidate.id,{x:3.2,y:.7,z:.4}))
    throw Error('Native physical input rejected');
   original.tick(90);
   const after=current.record();
   result.changedSemanticVersions=after.revisionCount-initial.revisionCount;
  }
  // Commit CURRENT world claims with the full native contact solver, source
  // record, independent observer journals, and semantic-revision ledger.
  const snapshot=JSON.parse(JSON.stringify(current.snapshot()));
  const fresh=PRSECurrentSemanticDocument.restore(snapshot);
  if(!fresh.ok)throw Error('World+document transaction rejected: '+fresh.reason);
  restored=fresh.document;
  const a=current.current(),b=restored.current();
  result.identicalNativeText=a.text===b.text;
  result.nativeSaveRestored=true;
  if(!result.identicalNativeText)throw Error('Current semantic text was not identical on reentry');
  if(!restored.current().historicalSourceNotCurrentText)
   throw Error('World description incorrectly claimed original prose was current');
  result.nativeSaveSizeBytes=Buffer.byteLength(JSON.stringify(snapshot));
  result.currentWorldDocPhysicallyTrueAfter=a.relationClaimCounts.true;
  // Resume actual native physics in BOTH GameCore worlds. This tests causal
  // continuation, not just whether saved JSON decodes.
  original.tick(1);restored.story.loop.tick(1);
  result.futurePhysicsSourceTruthEqual=
   JSON.stringify(current.current().relationClaimCounts)===
   JSON.stringify(restored.current().relationClaimCounts);
  if(!result.futurePhysicsSourceTruthEqual)
   throw Error('Physically verified current story claims changed after native reentry');
  result.status='verified';
 }catch(e){result.status='failed';result.failure=String(e?.message||e).slice(0,220);}
 finally{restored?.dispose();original?.dispose();}
 all.push(result);
 if((i+1)%25===0)console.log('PROGRESS',mode,i+1,'of',ids.length);
}
const passed=all.filter(r=>r.status==='verified');
const summary={
 sourceScenes:all.length,parser:mode,
 sourceGroups:{human:all.filter(x=>x.subset==='human').length,
  assisted:all.filter(x=>x.subset==='assisted').length},
 accepted:passed.length,
 physicalSceneRejected:all.filter(x=>x.status==='source_layout_rejected').length,
 runtimeFailures:all.filter(x=>x.status==='failed').length,
 currentPhysicalEntityClaims:num(passed,'materializedEntities'),
 currentUnloadedIdentityClaims:num(passed,'latentEntities'),
 sourceRelationsPhysicallyVerified:num(passed,'physicallyVerifiedRelations'),
 sourceRelationsPhysicallyContradicted:num(passed,'physicallyRefutedRelations'),
 sourceRelationsNotVerifiable:num(passed,'unverifiableRelations'),
 physicallyVerifiedExtraSupportStatements:num(passed,'physicalSupportClauses'),
 unsupportedOriginalRelationsNarrated:num(passed,'unverifiedSourceRelationsNarrated'),
 semanticsChangedAfterNativeImpulse:passed.filter(x=>x.changedSemanticVersions>0).length,
 noDuplicateUnchangedRevision:passed.filter(x=>x.repeatedUnchangedRevisionCount===0).length,
 validNativeWorldAndSemanticJournalSave:passed.filter(x=>x.nativeSaveRestored&&x.identicalNativeText).length,
 nativeResumedPhysicalSourceTruthEqual:passed.filter(x=>x.futurePhysicsSourceTruthEqual).length,
 originalHistoricalDescriptionBytes:num(passed,'sourceArchiveBytes'),
 previousPRSECurrentProseBytes:num(passed,'countCurrentProseBytes'),
 newCanonicalCurrentDocumentBytes:num(passed,'currentDocumentBytes'),
 wallSeconds:+((performance.now()-start)/1000).toFixed(2)};
const raw={metadata:{method:'Source-preserving structured current-world document evaluated on actual existing Rapier/GameCore materializations',
 source:'External SceneEval-500 descriptions, same first100 human and every-fourth assisted100 as earlier research',
 sourceLabelsNotRead:true,noHumanOrLanguageModel:true,mode,
 limits:'Physically verified facts and qualified latent records are NOT fluent revised literature; source semantic parser remains extremely incomplete'},
 summary,results:all};
const path=privateDir+'/prse_current_world_document_'+mode+'_200_raw_'+version+'.json';
writeFileSync(path,JSON.stringify(raw,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_current_world_document_'+mode+'_200_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...raw.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(path)).digest('hex'),
  privateRawFile:path},summary,
 failures:all.filter(x=>x.status==='failed').map(x=>({id:x.sourceID,reason:x.failure})),
 statusByScene:all.map(x=>({id:x.sourceID,status:x.status,verified:x.physicallyVerifiedRelations,
   ambiguous:x.unverifiableRelations,changed:x.changedSemanticVersions,bytes:x.currentDocumentBytes}))
 },null,2)+'\n',{flag:'wx'});
console.log('FINAL',JSON.stringify(summary));
