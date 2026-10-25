// PRSE research-only, observer-specific semantic revision of literary sources.
//
// The original descriptive source is a HISTORICAL DOCUMENT, never blindly
// reissued as current truth. Two distinct projections are used:
//  * source-proposed relations which must be verified in existing real 3D Rapier,
//  * physically perceptible current world-object facts and events.
//
// A language model may later phrase these verified statements more artfully,
// but must not alter authoritative evidence or invent unseen causes.
// Native whole-world snapshots + physical observer + relation history are
// saved in one trusted, versioned research transaction.
import {createHash} from 'node:crypto';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEPhysicalObserver} from './prse_physical_observer.mjs';
import {PRSEGroundedFacts} from './prse_grounded_relation_narration.mjs';
import {recordNativePRSEState,restoreNativePRSEState} from './prse_native_world_transaction.mjs';

const hash=x=>createHash('sha256').update(typeof x==='string'?x:JSON.stringify(x)).digest('hex');
const clone=x=>structuredClone(x);
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const goodId=id=>typeof id==='string'&&/^[a-z][a-z0-9-]{2,60}$/.test(id);
export class PRSESourceRevision {
 constructor(loop,proposals,{observerRadius=9}={}){
  if(!(loop instanceof PRSELoop)||!Array.isArray(proposals)||proposals.length>512||
   !finite(observerRadius)||observerRadius<=0||observerRadius>50)throw Error('Invalid source evidence inputs');
  this.loop=loop;
  this.sourceProse=loop.scene.prose;
  this.sourceHash=hash(this.sourceProse);
  this.sourceRelations=clone(proposals);
  this.relationHash=hash(this.sourceRelations);
  this.facts=new PRSEGroundedFacts(loop,this.sourceRelations);
  this.perception=new PRSEPhysicalObserver(loop,{visibilityRadius:observerRadius});
  this.observerRadius=observerRadius;
  this.revisionJournal=[];
  this.visitorCount=0;
  this.lastReadTime=new Map();
 }
 attachObserver(id,positionProvider,options={}){
  if(!goodId(id)||typeof positionProvider!=='function')throw Error('Invalid live observer');
  return this.perception.attach(id,positionProvider,{radius:this.observerRadius,...options});
 }
 read(id,eye,{radius=this.observerRadius}={}){
  if(!goodId(id))throw Error('Invalid observer ID');
  if(this.loop.scene.prose!==this.sourceProse||hash(this.loop.scene.prose)!==this.sourceHash)
   throw Error('Original literary source mutated during physical world evolution');
  if(!finite(this.loop.time)||this.loop.time+1e-6<(this.lastReadTime.get(id)||0))
   throw Error('World time went backwards for an observer');
  const sight=this.perception.observe(id,eye,{radius,mode:'ray'});
  const facts=this.facts.observe(id,sight.visibleIds);
  const claims=this.facts.current();
  const events=sight.witnessedEvents.map(e=>({
   type:'witnessed_physical_event',eventSequence:e.sequence,
   worldTime:this.loop.events.find(x=>x.sequence===e.sequence)?.time??null,
   text:e.text,observer:id,source:'authoritative_gamecore_event_at_observation_time'
  }));
  // Source-relations are neither an inference of speaker intent nor a story
  // generator. We report only identity-specific already verified current facts.
  const revisions=facts.changed.map(row=>({
   type:row.kind==='verified_now'?'verified_present_fact':'previously_visible_fact_retracted',
   relationKey:row.key,sourceRelation:this.sourceRelations[row.key],
   sourceEntityIDs:row.sources,worldTime:this.loop.time,
   evidence:row.evidence,text:row.text,observer:id
  }));
  // Distinct current object-state facts (e.g. source-linked ash or damage) are
  // ALSO required. The first version forgot to include the physical observer's
  // changedFacts, so it could see a real ash collider but say nothing about it.
  // Avoid duplicating the same principal object already described by a
  // separately verified source relation, while preserving new remnant facts.
  const alreadyDescribed=new Set(revisions.map(r=>r.sourceEntityIDs[0]));
  const appearances=sight.changedFacts.filter(row=>!alreadyDescribed.has(row.id)).map(row=>{
   const physical=this.loop.entities.get(row.id);
   if(!physical||!sight.visibleIds.includes(row.id))
    throw Error('Invented object-state change outside authoritative visible world');
   return {type:'current_visible_physical_state',entityID:row.id,
    originID:physical.originId||null,
    worldTime:this.loop.time,observer:id,
    evidence:'GameCore_current_entity_and_Rapier_physical_visibility',
    text:row.text};
  });
  const emitted=[...events,...revisions,...appearances];
  if(this.revisionJournal.length+emitted.length>20000)
   throw Error('Bounded revision history capacity exceeded before editing journal');
  for(const entry of emitted)this.revisionJournal.push(clone(entry));
  this.lastReadTime.set(id,this.loop.time);
  this.visitorCount++;
  const last=this.loop.scene.entities.length;
  return {
   schema:1,sourceProseHash:this.sourceHash,sourceDocumentStillHistorical:true,
   sceneId:this.loop.scene.id,worldTime:this.loop.time,
   worldEntityCount:last,observer:id,
   visibleEntityIDs:[...sight.visibleIds],
   witnessedEvents:events,relationRevisions:revisions,
   visibleCurrentStates:appearances,
   currentSentences:emitted.map(e=>e.text),
   // This is the text adapter output. It cannot claim fluent literary
   // rewriting; the original remains separately accessible for provenance.
   text:emitted.map(e=>e.text).join(' '),
   physicallyVerifiableRelations:claims.filter(c=>c.truth==='true').length,
   physicallyRefutedRelations:claims.filter(c=>c.truth==='false').length,
   unverifiableRelations:claims.filter(c=>c.truth==='unknown').length,
   unknownClaimsSuppressed:claims.filter(c=>c.truth==='unknown').length,
   sourceStillOriginal:this.loop.scene.prose===this.sourceProse
  };
 }
 revisionsForObserver(id){
  if(!goodId(id))throw Error('Invalid observer ID');
  return this.revisionJournal.filter(e=>e.observer===id).map(clone);
 }
 sourceArchive(){
  return {kind:'historical_source_prose',sceneId:this.loop.scene.id,
   sourceSHA256:this.sourceHash,originalText:this.sourceProse,
   warning:'Historical source is not automatically current physical truth'};
 }
 currentWorldAudit(){
  const rows=this.facts.current();
  return {sourceHash:this.sourceHash,relationHash:this.relationHash,
   sourceClaims:rows.length,true:rows.filter(x=>x.truth==='true').length,
   false:rows.filter(x=>x.truth==='false').length,
   unknown:rows.filter(x=>x.truth==='unknown').length,
   worldTime:this.loop.time,sourceStillHistorical:this.loop.scene.prose===this.sourceProse};
 }
 snapshot(){
  if(this.loop.scene.prose!==this.sourceProse)throw Error('Original source text changed');
  const physical=recordNativePRSEState(this.loop);
  const observers=this.perception.snapshot();
  const relationKnowledge=this.facts.snapshot();
  const scene=this.loop.scene.id;
  const semanticBundle={
   schema:1,scene,sourceProseHash:this.sourceHash,
   sourceRelationHash:this.relationHash,sourceRelations:clone(this.sourceRelations),
   observerRadius:this.observerRadius,
   originalSourceDocument:this.sourceProse,
   worldClock:this.loop.time,eventSequence:this.loop.nextSeq,
   observers,relationKnowledge,
   revisions:clone(this.revisionJournal),
   visitorCount:this.visitorCount,lastReadTime:[...this.lastReadTime]
  };
  return {schema:1,trustedOwnerGeneratedOnly:true,physical,
   semanticBundle,
   semanticBundleSHA256:hash(semanticBundle),
   physicalPayloadSHA256:hash(physical)};
 }
 static restore(saved){
  if(!saved||saved.schema!==1||saved.trustedOwnerGeneratedOnly!==true||
   !saved.physical||!saved.semanticBundle||
   hash(saved.physical)!==saved.physicalPayloadSHA256||
   hash(saved.semanticBundle)!==saved.semanticBundleSHA256)
   return {ok:false,reason:'invalid_or_mixed_transaction_digest'};
  let loop=null;
  try{
   const s=saved.semanticBundle;
   if(!goodId(s.scene)||!Array.isArray(s.sourceRelations)||s.sourceRelations.length>512||
    hash(s.sourceRelations)!==s.sourceRelationHash||
    hash(s.originalSourceDocument)!==s.sourceProseHash||
    !finite(s.worldClock)||!Number.isSafeInteger(s.eventSequence)||
    !Array.isArray(s.revisions)||s.revisions.length>20000||
    !Array.isArray(s.lastReadTime)||s.lastReadTime.length>8||
    !Number.isSafeInteger(s.visitorCount)||s.visitorCount<0||
    s.visitorCount>1000000000)
    throw Error('Invalid current semantic world provenance');
   const result=restoreNativePRSEState(saved.physical);
   if(!result.ok)throw Error('Native GameCore and Rapier restore failed: '+result.reason);
   loop=result.loop;
   if(loop.scene.id!==s.scene||loop.time!==s.worldClock||
    loop.nextSeq!==s.eventSequence||loop.scene.prose!==s.originalSourceDocument)
    throw Error('Mixed authoritative native/semantic/observer times or IDs');
   const answer=new PRSESourceRevision(loop,s.sourceRelations,{observerRadius:s.observerRadius});
   answer.perception=PRSEPhysicalObserver.restore(loop,s.observers);
   answer.facts=PRSEGroundedFacts.restore(loop,s.sourceRelations,s.relationKnowledge);
   for(const [id,time] of s.lastReadTime){
    if(!goodId(id)||!finite(time)||time<0||time>loop.time+1e-6||
       answer.lastReadTime.has(id))throw Error('Invalid observer last-read state');
    answer.lastReadTime.set(id,time);
   }
   const validEventSequences=new Set(loop.events.map(e=>e.sequence));
   for(const entry of s.revisions){
    if(!goodId(entry.observer)||!finite(entry.worldTime)||entry.worldTime>loop.time+1e-6||
     !['witnessed_physical_event','verified_present_fact',
       'previously_visible_fact_retracted','current_visible_physical_state'].includes(entry.type))
     throw Error('Malformed current-world revision');
    if(entry.type==='witnessed_physical_event'){
     if(!validEventSequences.has(entry.eventSequence)||entry.source!=='authoritative_gamecore_event_at_observation_time')
      throw Error('Revision refers to nonexistent physical event');
    }else if(entry.type==='current_visible_physical_state'){
     if(!goodId(entry.entityID)||!loop.entities.has(entry.entityID)||
        entry.evidence!=='GameCore_current_entity_and_Rapier_physical_visibility'||
        (entry.originID!==null&&
          (!goodId(entry.originID)||!loop.entities.has(entry.originID))))
      throw Error('Unidentifiable or forged observed current object state');
    }else if(!Number.isInteger(entry.relationKey)||
       entry.relationKey<0||entry.relationKey>=s.sourceRelations.length||
       JSON.stringify(entry.sourceRelation)!==JSON.stringify(s.sourceRelations[entry.relationKey])||
       !Array.isArray(entry.sourceEntityIDs)||
       !entry.sourceEntityIDs.every(id=>loop.entities.has(id)))
      throw Error('Revision refers to nonexistent original semantic claim/entity');
   }
   answer.revisionJournal=clone(s.revisions);
   answer.visitorCount=s.visitorCount;
   return {ok:true,story:answer,loop};
  }catch(e){loop?.dispose();return {ok:false,reason:String(e.message).slice(0,300)};}
 }
 dispose(){this.loop.dispose();}
}
