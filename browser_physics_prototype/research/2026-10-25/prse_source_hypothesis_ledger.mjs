// PRSE research-only non-destructive source hypothesis ledger.
//
// Problem proved by prior independent author labels: deleting syntactically
// uncertain ON interpretations BEFORE actual physics removes author-supported
// world structure, but trusting ALL parsed source relationships as narrative
// source meaning prints claims not grounded in the historical source.
//
// This layer retains EVERY source ON hypothesis with original source span,
// original relation ordinal, grammatical uncertainty and *separate* measured
// native GameCore/Rapier status. It never edits scene geometry. Only source-
// syntax approved relations are eligible for observer SOURCE wording; other
// relationships may remain TRUE as independent physical observations without
// being advertised as source-entailed. Hypotheses survive source/observer/
// native solver transaction and later physical contact changes.
//
// A source-only grammar candidate is NOT external author-validated source
// entailment. All relations not ON are recorded as unresolved hypotheses in
// this particular study, rather than being silently reported as true source
// prose. This is not a general discourse parser or production game module.
import {createHash} from 'node:crypto';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {measureRelation} from './prse_grounded_relation_narration.mjs';
import {PRSESourceRevision} from './prse_source_revision_story.mjs';
import {PRSECurrentSemanticDocument} from './prse_current_semantic_document.mjs';

const hash=x=>createHash('sha256').update(typeof x==='string'?x:JSON.stringify(x)).digest('hex');
const clone=x=>structuredClone(x);
const validId=x=>typeof x==='string'&&/^[a-z][a-z0-9-]{1,79}$/.test(x);
function rolesFor(proposal,roles){
 if(!proposal||typeof proposal.text!=='string'||!Array.isArray(proposal.relations)||
  proposal.relations.length>512||!Array.isArray(roles)||roles.length>512)
  throw Error('Unbounded or missing literary source/role evidence');
 const by=new Map();
 for(const r of roles){
  if(!Number.isInteger(r.sourceRelationIndex)||r.sourceRelationIndex<0||
   r.sourceRelationIndex>=proposal.relations.length||by.has(r.sourceRelationIndex)||
   !['source_syntax_role_candidate','abstain'].includes(r.status))
   throw Error('Corrupt/duplicate source-relationship ordinal or grammar decision');
  const source=proposal.relations[r.sourceRelationIndex];
  if(source.kind!=='object'||source.type!=='on'||source.a!==r.parsedChild||
   source.b!==r.parsedSupport||source.sourceText!==r.literalSourceSpan)
   throw Error('Source grammatical role does not match literal source interpretation');
  by.set(r.sourceRelationIndex,clone(r));
 }
 for(const [index,relation]of proposal.relations.entries()){
  if(relation.kind==='object'&&relation.type==='on'&&!by.has(index))
   throw Error('Missing ON hypothesis is not evidence of source rejection');
  const snippet=relation.sourceText;
  if(snippet&&(!proposal.text.includes(snippet)||snippet.length>proposal.text.length))
   throw Error('Original source relation span does not occur in literary source');
 }
 return by;
}
export class PRSEMeaningHypotheses {
 constructor(loop,proposal,roleRows,{maxHistory=20000}={}){
  if(!(loop instanceof PRSELoop)||!proposal||loop.scene.prose!==proposal.text||
   !Number.isInteger(maxHistory)||maxHistory<1||maxHistory>20000)
   throw Error('Source hypothesis record requires live matching native GameCore source');
  this.proposal=clone(proposal);
  this.roleRows=clone(roleRows);
  this.roleBy=rolesFor(this.proposal,this.roleRows);
  this.originalSourceDigest=hash(proposal.text);
  this.originalProposalDigest=hash(this.proposal);
  this.grammarDigest=hash(this.roleRows);
  this.maxHistory=maxHistory;
  this.approvedOrdinals=[...this.roleBy.entries()]
    .filter(([i,r])=>r.status==='source_syntax_role_candidate').map(([i])=>i).sort((a,b)=>a-b);
  // Narrator is deliberately narrower than native physical records.
  const eligible=this.approvedOrdinals.map(index=>this.proposal.relations[index]);
  this.story=new PRSESourceRevision(loop,eligible,{observerRadius:12});
  this.document=new PRSECurrentSemanticDocument(this.story);
  this.history=[];
  this.previous=null;
  this.lastEventSeq=0;
 }
 hypotheses(){
  const loop=this.story.loop;
  if(loop.scene.prose!==this.proposal.text||hash(loop.scene.prose)!==this.originalSourceDigest)
   throw Error('Original history was edited without a versioned source change');
  if(Math.abs(loop.time-loop.game.time)>1e-6)throw Error('GameCore world timeline and semantic timeline disagree');
  return this.proposal.relations.map((source,i)=>{
   const physical=measureRelation(loop,source),grammar=this.roleBy.get(i);
   const syntacticallyEligible=grammar?.status==='source_syntax_role_candidate';
   return {sourceRelationIndex:i,sourceRelation:clone(source),
    originalSourceSpan:source.sourceText??null,
    historicalSourceDigest:this.originalSourceDigest,
    grammarEvidenceKind:syntacticallyEligible?'limited_pretrained_syntax_role_candidate':
      grammar?'ambiguous_on_role_preserved':'other_relation_not_source_entailed_in_this_ON_study',
    sourceMeaning:'unverified_by_independent_author_label_in_production',
    physicalTruth:physical.truth,physicalReason:physical.reason,
    physicalIds:physical.ids||null,
    eligibleForSourceWordedPresentFact:Boolean(syntacticallyEligible&&physical.truth==='true'),
    physicallyTrueButSourceRoleUnresolved:Boolean(
     !syntacticallyEligible&&physical.truth==='true'),
    sourceNotErasedForUncertainty:true};
  });
 }
 current(){
  const hypotheses=this.hypotheses();
  const factual=this.document.current();
  const admitted=hypotheses.filter(h=>h.eligibleForSourceWordedPresentFact);
  const physicalOnly=hypotheses.filter(h=>h.physicallyTrueButSourceRoleUnresolved);
  for(const a of admitted){
   if(!this.approvedOrdinals.includes(a.sourceRelationIndex))
    throw Error('Ungrounded language source role made source semantic claim');
  }
  return {schema:1,sceneId:this.story.loop.scene.id,worldTime:this.story.loop.time,
   originalLiterarySourceSHA256:this.originalSourceDigest,
   sourceProposalsPreserved:hypotheses.length,
   syntaxApprovedSourceOnRelations:this.approvedOrdinals.length,
   undecidedAndRetainedONRelations:hypotheses.filter(h=>
    h.sourceRelation.kind==='object'&&h.sourceRelation.type==='on'&&
    !this.approvedOrdinals.includes(h.sourceRelationIndex)).length,
   physicallyTrueSupportedSyntaxSourceClaims:admitted.length,
   physicallyTrueButSourceRoleUnresolved:physicalOnly.length,
   presentText:factual.text,verifiedPhysicalClauses:factual.verifiedTextClauses,
   historicalSourceIsNotCurrentText:factual.historicalSourceNotCurrentText,
   sourceHypotheses:hypotheses};
 }
 record(){
  const physical=this.document.record();
  const current=this.current();
  const sig=hash(current.sourceHypotheses.map(x=>
   [x.sourceRelationIndex,x.grammarEvidenceKind,x.physicalTruth,(x.physicalIds||[]).join('|')]));
  if(this.previous?.signature===sig)
   return {changed:false,current,historyLength:this.history.length};
  if(this.history.length>=this.maxHistory)throw Error('Source hypothesis status history cap reached');
  if(this.previous&&current.worldTime+1e-7<this.previous.worldTime)
   throw Error('World clock reversed after source hypothesis update');
  const history={ordinal:this.history.length+1,worldTime:current.worldTime,
   hypothesisPhysicalSignature:sig,previous:this.previous?.signature||null,
   sourceSHA256:this.originalSourceDigest};
  this.history.push(history);
  this.previous={signature:sig,worldTime:current.worldTime};
  return {changed:true,current,historyLength:this.history.length};
 }
 snapshot(){
  const current=this.record().current;
  const structured={
   schema:1,proposal:clone(this.proposal),roleRows:clone(this.roleRows),
   originalSourceDigest:this.originalSourceDigest,
   originalProposalDigest:this.originalProposalDigest,
   grammarDigest:this.grammarDigest,
   sceneId:this.story.loop.scene.id,
   worldTime:current.worldTime,
   sourceHypothesisDigest:hash(current.sourceHypotheses),
   sourceHypothesisPhysicalSignature:this.previous.signature,
   previous:clone(this.previous),history:clone(this.history)
  };
  return {schema:1,trustedOwnerGeneratedOnly:true,
   nativeWorldObserverText:this.document.snapshot(),
   sourceLedger:structured,ledgerDigest:hash(structured)};
 }
 static restore(snapshot){
  if(!snapshot||snapshot.schema!==1||snapshot.trustedOwnerGeneratedOnly!==true||
   !snapshot.sourceLedger||hash(snapshot.sourceLedger)!==snapshot.ledgerDigest)
   return {ok:false,reason:'Source hypothesis ledger digest or owner-trust mismatch'};
  let wrapped=null,restoredPhysical=null;
  try{
   const saved=snapshot.sourceLedger;
   if(saved.schema!==1||hash(saved.proposal)!==saved.originalProposalDigest||
    hash(saved.proposal.text)!==saved.originalSourceDigest||
    hash(saved.roleRows)!==saved.grammarDigest||
    !validId(saved.sceneId)||!Number.isFinite(saved.worldTime)||
    !Array.isArray(saved.history)||saved.history.length>20000)
    throw Error('Source text, roles or historical timestamps corrupt');
   const physical=PRSECurrentSemanticDocument.restore(snapshot.nativeWorldObserverText);
   if(!physical.ok)throw Error('Native GameCore/observer/source state cannot restore: '+physical.reason);
   restoredPhysical=physical;
   // Physical restore creates an existing document with exact approved role
   // subset. Check source-proposed interpretation and narrator subset before
   // constructing our own wrapper.
   const eligibleMap=rolesFor(saved.proposal,saved.roleRows);
   const selected=[...eligibleMap.entries()].filter(([i,r])=>
    r.status==='source_syntax_role_candidate').map(([i])=>i).sort((a,b)=>a-b);
   if(JSON.stringify(selected.map(i=>saved.proposal.relations[i]))!==
      JSON.stringify(physical.story.sourceRelations)||
      physical.loop.scene.id!==saved.sceneId||
      physical.loop.scene.prose!==saved.proposal.text||
      Math.abs(physical.loop.time-saved.worldTime)>1e-6)
    throw Error('Mismatched source hypotheses and currently restored narrator/native world');
   wrapped=Object.create(PRSEMeaningHypotheses.prototype);
   wrapped.proposal=clone(saved.proposal);wrapped.roleRows=clone(saved.roleRows);
   wrapped.roleBy=eligibleMap;
   wrapped.originalSourceDigest=saved.originalSourceDigest;
   wrapped.originalProposalDigest=saved.originalProposalDigest;
   wrapped.grammarDigest=saved.grammarDigest;
   wrapped.maxHistory=20000;
   wrapped.approvedOrdinals=selected;
   wrapped.story=physical.story;wrapped.document=physical.document;
   wrapped.history=clone(saved.history);wrapped.previous=clone(saved.previous);
   wrapped.lastEventSeq=0;
   const now=wrapped.current();
   const signature=hash(now.sourceHypotheses.map(x=>
    [x.sourceRelationIndex,x.grammarEvidenceKind,x.physicalTruth,(x.physicalIds||[]).join('|')]));
   if(hash(now.sourceHypotheses)!==saved.sourceHypothesisDigest||
      signature!==saved.sourceHypothesisPhysicalSignature||
      wrapped.previous?.signature!==signature ||
      wrapped.previous.worldTime>now.worldTime+1e-6||
      wrapped.history.at(-1)?.hypothesisPhysicalSignature!==signature)
    throw Error('Claim status contradicts actual restored native world');
   for(let i=0;i<wrapped.history.length;i++){
    const e=wrapped.history[i];
    if(e.ordinal!==i+1||e.sourceSHA256!==saved.originalSourceDigest||
     !Number.isFinite(e.worldTime)||e.worldTime>now.worldTime+1e-6||
     (i>0&&e.worldTime+1e-6<wrapped.history[i-1].worldTime))
     throw Error('Forged or future-timed source-hypothesis historical claim');
   }
   return {ok:true,ledger:wrapped,loop:physical.loop};
  }catch(e){
   // An inconsistent source/grammar hypothesis can be rejected BEFORE the
   // wrapper object has been constructed. Release its already restored
   // native Rapier world rather than leaking solver memory on bad saves.
   if(wrapped)wrapped.dispose();
   else restoredPhysical?.story?.dispose();
   return {ok:false,reason:String(e.message).slice(0,300)};
  }
 }
 dispose(){this.story.dispose();}
}
