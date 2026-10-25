// PRSE research-only QUANTITY-SCOPED current semantic text.
//
// Builds on the SAME persistent SourceRevision + CurrentSemanticDocument and
// authoritative GameCore/Rapier rigid-body reality. Source interpreter's
// numeric/attribute proposals are retained as provenance, but do not become
// authoritative world facts or global literary exact counts.
//
// Compared against legacy per-entity present tense to measure actual
// evidence coverage and concise text without hallucinating source meaning.
// Full trusted native physics/source/observer/document snapshot is ONE
// transaction, with source quantity metadata and claim fingerprint attached.
import {createHash} from 'node:crypto';
import {PRSESourceRevision} from './prse_source_revision_story.mjs';
import {PRSECurrentSemanticDocument} from './prse_current_semantic_document.mjs';
import {PRSESourceQuantityEvidence} from './prse_source_quantity_evidence.mjs';

const sha=o=>createHash('sha256').update(JSON.stringify(o)).digest('hex');
const clone=o=>structuredClone(o);
const noun=k=>String(k).replace(/_/g,' ').trim().slice(0,70);
const numWord=n=>n>=0&&n<=10?['zero','one','two','three','four','five','six','seven','eight','nine','ten'][n]:String(n);
function plural(label){
 if(/shelf$/i.test(label))return label.replace(/shelf$/i,'shelves');
 if(/[^aeiou]y$/i.test(label))return label.slice(0,-1)+'ies';
 if(/(?:ch|sh|x|s|z)$/i.test(label))return label+'es';
 return label+'s';
}
function groupText(items){
 return items.map(({type,n})=>numWord(n)+' '+(n===1?noun(type):plural(noun(type)))).join(', ');
}
function currentProse(presenter,counts){
 const full=presenter.verifiedTextClauses;
 const live=counts.currentPhysicalTypeCounts.filter(x=>x.materializedBodies>0).map(x=>({
  type:x.type,n:x.materializedBodies}));
 const notLoaded=counts.currentPhysicalTypeCounts.filter(x=>x.unloadedSemanticIdentities>0).map(x=>({
  type:x.type,n:x.unloadedSemanticIdentities}));
 const result=[];
 if(live.length){
  result.push('In this materialized area: '+groupText(live)+'.');
 }
 if(notLoaded.length){
  result.push('Offscreen records retain '+groupText(notLoaded)+
   '; their current physical positions and contacts are unverified.');
 }
 for(const e of full){
  // Preserve source-linked current relation and current nonstandard
  // physical state. Ordinary bare entity presence is already covered by
  // type grouping above, preventing a second redundant text sentence.
  if(['physically_verified_source_relation',
      'physically_verified_support_not_source_entailed',
      'historical_physical_identity_destroyed'].includes(e.type))
   result.push(e.text);
  else if(e.type==='current_physical_presence'&&(
   /\b(?:ash|tipped over|changed position)\b/i.test(e.text)))
   result.push(e.text);
 }
 return result.join(' ').replace(/\s+/g,' ').trim();
}
export class PRSEQuantityScopedWorld {
 constructor(story,proposal){
  if(!(story instanceof PRSESourceRevision)||!proposal||typeof proposal.text!=='string'||
     proposal.text!==story.sourceProse||typeof proposal.sourceId!=='string')
   throw Error('Quantity-scoped world requires same source and native GameCore history');
  this.story=story;this.proposal=clone(proposal);
  this.proposalHash=sha(this.proposal);
  this.currentDocument=new PRSECurrentSemanticDocument(story);
  this.quantities=new PRSESourceQuantityEvidence(story.loop,proposal);
  this.documentLog=[];this.lastSignature=null;
 }
 current(){
  const facts=this.currentDocument.current();
  const counts=this.quantities.evaluate();
  if(facts.sceneId!==this.story.loop.scene.id||Math.abs(facts.worldTime-counts.worldTime)>1e-5||
     counts.sourceHash!==this.story.sourceHash)
   throw Error('Source/physical/count world clock or source identity diverged');
  const string=currentProse(facts,counts);
  // This is an audit-friendly current-world TEXT, not a player-specific
  // perception feed. A player may access only story.read() or another
  // independently ray-verified observation adapter.
  return {
   schema:1,sceneId:facts.sceneId,worldTime:facts.worldTime,
   type:'omniscient_qualified_current_physical_semantic_text',
   originalSourceSHA256:this.story.sourceHash,
   counts:counts.currentPhysicalTypeCounts,
   countSourceClaims:counts.sourceCountClaims,
   priorSourceClaimTruthStatus:counts.sourceCountClaims.map(c=>({
    type:c.type,worldMatchesCompilerProposal:c.sourceCompilerNumericMatch,
    exactGlobalSourceMeaning:c.sourceExactGlobalCountEntailed,
    referenceResolution:c.referenceUniqueness,
    sourceScope:c.sourceCountScope})),
   sourceMeaningNotIndependentlyVerified:true,
   physicalRegionComplete:counts.fullyPhysicallyMaterialized,
   bodyCount:counts.materializedEntityCount,
   destroyedIdentityCount:counts.destroyedEntityCount,
   unloadedIdentityCount:counts.unloadedEntityCount,
   physicalCurrentSourceRelationClaims:facts.relationClaimCounts,
   text:string,
   proseBytes:Buffer.byteLength(string),
   baselinePerObjectCurrentProseBytes:Buffer.byteLength(facts.text),
   absentExternalSourceAdjectivesAreNotAsserted:true,
   warnings:[
    'This prose counts only the currently materialized region; it does not assert a global literary closed-world count.',
    'Physical bodies were generated from source proposals and are not independent proof the source counts were interpreted correctly.',
    'The text is factual, not a human-rated fluent complete literary rewrite.']
  };
 }
 record(){
  const base=this.currentDocument.record();
  const c=this.current();
  const fp=sha({source:this.proposalHash,body:c.bodyCount,
    counts:c.counts.map(e=>[e.type,e.materializedBodies,e.unloadedSemanticIdentities,
      e.destroyedHistoricalIdentities]),
    sourceTruth:c.physicalCurrentSourceRelationClaims,text:c.text});
  if(this.lastSignature===fp)return {changed:false,logEntries:this.documentLog.length,current:c};
  const e={revision:this.documentLog.length+1,worldTime:c.worldTime,
   baseRevision:base.revisionCount,sourceHash:c.originalSourceSHA256,
   contentSignature:fp,visibleVerifiedClaimCount:c.physicalCurrentSourceRelationClaims.true,
   actualPhysicalBodyCount:c.bodyCount};
  if(this.documentLog.length>=12000)throw Error('Scoped semantic revision journal full');
  this.documentLog.push(e);this.lastSignature=fp;
  return {changed:true,logEntries:this.documentLog.length,current:c};
 }
 snapshot(){
  const current=this.record().current;
  const owner=this.currentDocument.snapshot();
  const archive={schema:1,sourceProposal:clone(this.proposal),
   sourceProposalSHA256:this.proposalHash,
   sourceHash:current.originalSourceSHA256,worldTime:current.worldTime,
   currentSemanticTextSHA256:sha(current.text),
   currentQuantitiesSHA256:sha(current.counts),
   currentSourceClaimsSHA256:sha(current.countSourceClaims),
   lastSignature:this.lastSignature,documentLog:clone(this.documentLog)};
  return {schema:1,trustedOwnerGenerated:true,owner,
   scoped:archive,scopedSHA256:sha(archive)};
 }
 static restore(saved){
  if(!saved||saved.schema!==1||saved.trustedOwnerGenerated!==true||!saved.scoped||
    saved.scopedSHA256!==sha(saved.scoped))return {ok:false,reason:'corrupt_quantity_scope_or_mixed_save'};
  let doc=null;
  try{
   const a=saved.scoped;
   if(a.schema!==1||typeof a.sourceHash!=='string'||!Array.isArray(a.documentLog)||
     a.documentLog.length>12000||sha(a.sourceProposal)!==a.sourceProposalSHA256)
    throw Error('Invalid source-predicate provenance');
   const result=PRSECurrentSemanticDocument.restore(saved.owner);
   if(!result.ok)throw Error('Native GameCore/source/observer document rejected: '+result.reason);
   const story=result.story;
   doc=new PRSEQuantityScopedWorld(story,a.sourceProposal);
   const c=doc.current();
   if(c.originalSourceSHA256!==a.sourceHash||Math.abs(c.worldTime-a.worldTime)>1e-5||
     sha(c.text)!==a.currentSemanticTextSHA256||
     sha(c.counts)!==a.currentQuantitiesSHA256||
     sha(c.countSourceClaims)!==a.currentSourceClaimsSHA256)
    throw Error('Restored native physical quantities or source facts differ from current saved literary text');
   let previousTime=-1;
   for(let i=0;i<a.documentLog.length;i++){
    const e=a.documentLog[i];
    if(e.revision!==i+1||typeof e.contentSignature!=='string'||
      e.contentSignature.length!==64||!Number.isFinite(e.worldTime)||
      e.worldTime<previousTime||e.worldTime>c.worldTime+1e-6||
      e.sourceHash!==c.originalSourceSHA256)
     throw Error('Impossible or disordered current-literary revision history');
    previousTime=e.worldTime;
   }
   if(a.documentLog.length && a.documentLog.at(-1).contentSignature!==a.lastSignature)
    throw Error('Current semantic signature disagrees with most recent revision');
   doc.currentDocument=result.document;
   doc.documentLog=clone(a.documentLog);doc.lastSignature=a.lastSignature;
   return {ok:true,world:doc,story:doc.story};
  }catch(e){doc?.dispose();return {ok:false,reason:String(e.message).slice(0,220)};}
 }
 dispose(){this.story.dispose();}
}
