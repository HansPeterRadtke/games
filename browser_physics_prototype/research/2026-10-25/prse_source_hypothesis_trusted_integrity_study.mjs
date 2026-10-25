// Trusted internal PRSE source-hypothesis/native GameCore/observer journal
// integrity checks, without claims of cryptographic hostile-save resistance.
// One real previously frozen human SceneEval source room, actual GameCore
// physics and genuine existing supported body. No model or source gold.
// The original owner/source text must remain intact in every accepted save.
//
// Negative variants intentionally tamper with COPIES of a single trusted
// native GameCore/observer/hypothesis save. Reject inconsistent raw files
// even if outer hash/digest is recomputed, without modifying live game.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash}from'node:crypto';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {PRSEMeaningHypotheses}from'./prse_source_hypothesis_ledger.mjs';
await initializePhysics();
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[27];
const grammar=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop/prse_source_role_on_200_raw_v1.json')).records.filter(r=>r.sourceId===27);
const clone=x=>JSON.parse(JSON.stringify(x)),sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const scene=repairScene(source,{maxSweeps:2,maxAttemptsPerScene:150});
if(!scene.accepted)throw Error('Original external source scene rejected');
let original=new PRSELoop(scene.scene);
original.tick(45);
let holder=new PRSEMeaningHypotheses(original,source,grammar);
const prior=holder.record().current;
const saved=clone(holder.snapshot());
let healthy=PRSEMeaningHypotheses.restore(saved);
if(!healthy.ok)throw Error('Unmodified native save refused: '+healthy.reason);
if(healthy.ledger.current().sourceProposalsPreserved!==source.relations.length||
   healthy.ledger.current().undecidedAndRetainedONRelations<1)
 throw Error('Historical uncertain source interpretations not restored');
healthy.ledger.dispose();
const anomalies=[
 ['altered_hypothesis_truth_digest_after_outer_rehash',(s)=>{
  s.sourceLedger.sourceHypothesisDigest='f'.repeat(64);s.ledgerDigest=sha(s.sourceLedger);}],
 ['changed_grammar_approval_after_rehash',(s)=>{
  const r=s.sourceLedger.roleRows.find(x=>x.status==='source_syntax_role_candidate');
  if(!r)throw Error('Original source has no accepted grammar role');
  r.status='abstain';
  s.sourceLedger.grammarDigest=sha(s.sourceLedger.roleRows);
  s.ledgerDigest=sha(s.sourceLedger);
 }],
 ['future_worldclock_after_outer_rehash',(s)=>{
  s.sourceLedger.worldTime+=100;
  s.ledgerDigest=sha(s.sourceLedger);
 }],
 ['forged_later_history_after_outer_rehash',(s)=>{
  s.sourceLedger.history[0].worldTime=s.sourceLedger.worldTime+10;
  s.ledgerDigest=sha(s.sourceLedger);
 }],
 ['physically_forged_source_relation_after_outer_rehash',(s)=>{
  const rel=s.sourceLedger.proposal.relations.find(x=>x.kind==='object'&&x.type==='on');
  if(!rel)throw Error('Expected a source relation');
  rel.b='forged-relation-target';
  s.sourceLedger.originalProposalDigest=sha(s.sourceLedger.proposal);
  s.ledgerDigest=sha(s.sourceLedger);
 }],
 ['corrupted_inner_native_physics_without_rehash',(s)=>{
  s.nativeWorldObserverText.physicalAndStory.physical.nativeBase64='AAAA';
 }]
];
const details=[];
for(const [name,change]of anomalies){
 const x=clone(saved);change(x);
 const r=PRSEMeaningHypotheses.restore(x);
 if(r.ok){
  r.ledger.dispose();
  throw Error('Corrupted internally inconsistent source/physics/observer save was accepted: '+name);
 }
 details.push({name,rejected:true,reason:r.reason});
}
const content={metadata:{
 source:'Original SceneEval human-authored row27, existing native GameCore/Rapier world',
 method:'Trusted internal state source/role/clock/hypothesis and physical snapshot corruption rejection',
 warning:'Plain SHA checks and internal consistency are not an authenticated or adversarially tamper-proof provenance system',
 noAuthorGoldOrGPUorLLM:true
 },validNativeRestore:true,originalSourceUnchanged:prior.sourceProposalsPreserved===source.relations.length,
 sourceHypothesesUnresolvedButRetained:prior.undecidedAndRetainedONRelations,
 intentionallyCorruptTestCopies:details.length,rejectedCorruptTestCopies:details};
writeFileSync(new URL('prse_source_hypothesis_trusted_integrity_v1.json',import.meta.url),
 JSON.stringify(content,null,2)+'\n',{flag:'wx'});
holder.dispose();
console.log('INDEPENDENT_NATIVE_HYPOTHESIS_INTEGRITY',JSON.stringify({
 validFullSave:true,badCopiesRejected:details.length,unresolvedSourceRelationsRetained:content.sourceHypothesesUnresolvedButRetained}));
