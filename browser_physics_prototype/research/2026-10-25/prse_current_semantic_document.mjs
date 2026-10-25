// PRSE research-only CURRENT SEMANTIC WORLD DOCUMENT.
//
// This is not a string-replacement of historic literary prose. It maintains
// a current, regenerable source/ID-linked factual document over the SAME
// authoritative PRSELoop/GameCore/Rapier physics, with explicit TRUE/FALSE/
// UNKNOWN and materialized/unmaterialized/dead status.
//
// World-internal, omniscient document is NOT directly a player readout:
// observer knowledge and witnessed causes use the separate PRSESourceRevision
// physically ray-tested observer. A later LLM may rewrite these VERIFIED
// clauses only as rejectable proposals, never directly change world truth.
import {createHash} from 'node:crypto';
import {PRSESourceRevision} from './prse_source_revision_story.mjs';

const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const sq=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const escName=s=>String(s??'an object').replace(/[\r\n]+/g,' ').replace(/\s+/g,' ').trim().slice(0,110);
const clone=x=>structuredClone(x);
const countA=s=>s?1:0;
function relationshipSentence(row,world){
 if(row.truth!=='true'||!Array.isArray(row.ids)||row.ids.length!==2)return null;
 // The only safe verbalizations already accepted by the existing bounded
 // physically checked source-relation projector remain its responsibility.
 // Its render() rejects unverified unsupported topology/identity itself.
 return world.facts.render(row);
}
function physicalSupport(loop,e,p){
 const a=loop.active.get(e.id),b=loop.active.get(p.id);
 if(!a||!b||!a.numColliders()||!b.numColliders()||p.shape==='sphere')
  return {truth:'unknown',reason:'physical_bodies_or_planar_support_missing'};
 // Conservative planar bounds, NOT proof for complex rotated/multipart forms.
 const overlap=Math.abs(e.position.x-p.position.x)+e.size.x/2<=p.size.x/2+.015
  &&Math.abs(e.position.z-p.position.z)+e.size.z/2<=p.size.z/2+.015;
 const gap=e.position.y-e.size.y/2-p.position.y-p.size.y/2;
 let contact=false;
 for(let i=0;i<a.numColliders();i++)
 for(let j=0;j<b.numColliders();j++)
  loop.game.world.contactPair(a.collider(i),b.collider(j),m=>{
   if(m.numContacts()>0)contact=true;
  });
 if(overlap&&Math.abs(gap)<.055&&a.isDynamic()&&!contact)
  return {truth:'unknown',reason:'contact_manifold_unverified_after_restore'};
 return {truth:overlap&&Math.abs(gap)<.055&&(contact||!a.isDynamic())?'true':'false',
  reason:'real_native_rapier_contact_and_planar_top_face'};
}
function physicalNativeBody(loop,id){
 const body=loop.active.get(id);
 if(!body)return null;
 return {position:{...body.translation()},rotation:{...body.rotation()},
  velocity:{...body.linvel()},angularVelocity:{...body.angvel()}};
}
export class PRSECurrentSemanticDocument{
 constructor(story,{maximumHistory=12000}={}){
  if(!(story instanceof PRSESourceRevision)||
   !Number.isInteger(maximumHistory)||maximumHistory<1||maximumHistory>20000)
   throw Error('Current narrative document requires existing live PRSE source revision adapter');
  this.story=story;this.maximumHistory=maximumHistory;
  this.sourceHash=story.sourceHash;this.relationHash=story.relationHash;
  this.previous=null;this.log=[];this.lastSeq=0;
 }
 #now(){
  const loop=this.story.loop;
  if(loop.scene.prose!==this.story.sourceProse||this.sourceHash!==this.story.sourceHash||
    this.relationHash!==this.story.relationHash)
   throw Error('Historical semantic source or typed relations changed unexpectedly');
  if(Math.abs(loop.time-loop.game.time)>1e-6)
   throw Error('GameCore semantic and native world clocks disagree');
  const clauses=[],statuses=[],verified=[],worldIds=new Set();
  const entities=loop.scene.entities;
  for(const e of entities){
   if(e.source==='provisional_3D_room_boundary')continue;
   if(worldIds.has(e.id))throw Error('Two semantic objects share an authoritative identity');
   worldIds.add(e.id);
   const body=physicalNativeBody(loop,e.id),destroyed=!!e.state?.destroyed;
   const name=escName(e.name);
   let status;
   if(destroyed)status='destroyed_historical_identity';
   else if(body)status='physically_materialized';
   else status='unloaded_semantic_identity';
   statuses.push({id:e.id,kind:e.kind,name,materialization:status,
    originId:e.originId||null,
    source:e.source||null,
    sourceReferencedOriginal:this.story.sourceHash,
    lastKnownWorldPosition:body?.position||clone(e.position),
    condition:e.state?.condition||'intact',
    moved:!!e.state?.moved,tipped:!!e.state?.tipped,rotated:!!e.state?.rotated});
   if(status==='unloaded_semantic_identity'){
    // The semantic world continues to exist outside the player's physical
    // perception. This is a QUALIFIED record, not proof of current live 3D
    // position, present contact, continuing velocity or other unseen causes.
    clauses.push({key:'latent:'+e.id,type:'persisted_unloaded_semantic_record',
     claim:'true',ids:[e.id],sourceRef:e.source||null,
     evidence:'saved_semantic_identity_no_active_Rapier_body',
     text:'The record of '+name+' remains, although its current physical state is not being simulated.'});
    continue;
   }
   if(status==='destroyed_historical_identity'){
    // Authored semantic destruction is authoritative history, but the
    // WORLD document must not assert a current live physical object.
    const descendant=entities.find(x=>x.originId===e.id&&!x.state?.destroyed);
    if(descendant){
     // Current physical residue gets its own actual present clause below.
     clauses.push({key:'tomb:'+e.id,type:'historical_physical_identity_destroyed',
      claim:'true',ids:[e.id,descendant.id],sourceRef:e.source||null,
      evidence:'authoritative_semantic_rule_and_lineage',
      text:name+' was destroyed; a distinct remnant has its own physical identity.'});
    }else clauses.push({key:'tomb:'+e.id,type:'historical_physical_identity_destroyed',
      claim:'true',ids:[e.id],sourceRef:e.source||null,
      evidence:'authoritative_semantic_destroyed_state',
      text:name+' was destroyed.'});
    continue;
   }
   // Current live collider/transform exists. We do NOT infer adjectives,
   // material appearance, motives or historical cause from the old paragraph.
   const presentText=e.kind==='ash'&&e.originId?
    'Ash from '+escName(loop.entities.get(e.originId)?.name||'a previous object')+' remains.' :
    name+(e.state?.tipped?' is tipped over.':e.state?.moved?' has changed position.':' is present.');
   clauses.push({key:'entity:'+e.id,type:'current_physical_presence',claim:'true',
    ids:[e.id],sourceRef:e.source||null,evidence:'native_Rapier_materialized_rigid_body',
    text:presentText});
  }
  // Any original source-interpretation relation must be checked against
  // physics. Missing/false relations stay in diagnostics, NOT narration.
  const relations=this.story.facts.current();
  const acceptedSupport=new Set();
  for(const r of relations){
   verified.push({sourceRelationIndex:r.key,type:r.source.type,
    sourceA:r.source.a,sourceB:r.source.b,
    truth:r.truth,reason:r.reason,physicalEntityIDs:r.ids||null});
   if(r.truth!=='true')continue;
   const statement=relationshipSentence(r,this.story);
   if(statement){
    clauses.push({key:'source_relation:'+r.key,type:'physically_verified_source_relation',
     claim:'true',ids:clone(r.ids),
     sourceRef:r.source.sourceText||null,evidence:r.reason,text:statement,
     sourceRelationIndex:r.key});
    if(r.source.type==='on')acceptedSupport.add(r.ids.join('|'));
   }
  }
  // Directly proven support relationships can be stated as PHYSICAL facts
  // even if a weak source parser never extracted them. They cannot thereby
  // be advertised as a faithful interpretation of the historical literature.
  const supportAudit=[];
  for(const e of entities){
   if(!e.supportId||e.supportId==='floor'||e.state?.destroyed||
    e.source==='provisional_3D_room_boundary')continue;
   const parent=loop.entities.get(e.supportId);
   if(!parent)continue;
   const measurement=physicalSupport(loop,e,parent);
   supportAudit.push({childID:e.id,parentID:parent.id,truth:measurement.truth,reason:measurement.reason});
   if(measurement.truth==='true'&&!acceptedSupport.has(e.id+'|'+parent.id)){
    clauses.push({key:'physical_support:'+e.id+'|'+parent.id,
     type:'physically_verified_support_not_source_entailed',
     claim:'true',ids:[e.id,parent.id],
     sourceRef:null,evidence:measurement.reason,
     text:escName(e.name)+' rests on '+escName(parent.name)+'.'});
   }
  }
  // Reject duplicated clause keys; the whole current document must be
  // deterministically regenerable from the same physical/semantic state.
  const seen=new Set();
  for(const c of clauses){
   if(seen.has(c.key)||!c.ids.every(id=>loop.entities.has(id))||
     c.claim!=='true'||!c.text?.trim()||!c.evidence)
    throw Error('Current textual fact not grounded in physical/source evidence');
   seen.add(c.key);
  }
  const text=clauses.map(c=>c.text).join(' ');
  return {schema:1,sceneId:loop.scene.id,worldTime:loop.time,
   scope:'omniscient_verified_world_state_not_player_knowledge',
   archivedSourceDigest:this.sourceHash,
   historicalSourceNotCurrentText:true,
   physicallyMaterializedCount:statuses.filter(x=>x.materialization==='physically_materialized').length,
   historicalDestroyedCount:statuses.filter(x=>x.materialization==='destroyed_historical_identity').length,
   unloadedCount:statuses.filter(x=>x.materialization==='unloaded_semantic_identity').length,
   relationClaimCounts:{
    true:verified.filter(x=>x.truth==='true').length,
    false:verified.filter(x=>x.truth==='false').length,
    unknown:verified.filter(x=>x.truth==='unknown').length},
   verifiedRelations:verified,physicalSupportAudit:supportAudit,
   semanticEntityRecords:statuses,verifiedTextClauses:clauses,text};
 }
 current(){
  return this.#now();
 }
 #semanticSignature(c){
  // Fast-moving pose coordinates are factual numeric context, but not every
  // sub-millimetre physics tick is a narratively meaningful proposition
  // change. The signed claim set tracks persistent semantic presence,
  // condition and verified relations rather than raw frame-by-frame poses.
  const q=[];
  for(const x of c.semanticEntityRecords)q.push(['entity',x.id,x.materialization,x.condition,x.originId,x.moved,x.tipped,x.rotated]);
  for(const x of c.verifiedRelations)q.push(['source',x.sourceRelationIndex,x.truth,(x.physicalEntityIDs||[]).join('|')]);
  for(const x of c.physicalSupportAudit)q.push(['support',x.childID,x.parentID,x.truth]);
  return hash(q);
 }
 record(){
  const c=this.#now(),signature=this.#semanticSignature(c),last=this.previous;
  if(last&&c.worldTime+1e-7<last.worldTime)throw Error('World time reversal in semantic document');
  if(last?.signature===signature)return {changed:false,revisionCount:this.log.length,current:c};
  const eventSequences=this.story.loop.events.filter(e=>e.sequence>this.lastSeq).map(e=>e.sequence);
  const record={revision:this.log.length+1,worldTime:c.worldTime,
   semanticSignature:signature,previousSignature:last?.signature||null,
   authoritativeEventSequences:eventSequences,
   relationTruth:c.relationClaimCounts,
   materializedCount:c.physicallyMaterializedCount,
   destroyedCount:c.historicalDestroyedCount,
   unloadedCount:c.unloadedCount};
  if(this.log.length>=this.maximumHistory)throw Error('Semantic revision history full');
  this.log.push(record);
  this.previous={signature,worldTime:c.worldTime};
  this.lastSeq=Math.max(this.lastSeq,...eventSequences,0);
  return {changed:true,revisionCount:this.log.length,current:c};
 }
 snapshot(){
  const latest=this.record(),transaction=this.story.snapshot();
  return {schema:1,trustedOwnerGenerated:true,
   physicalAndStory:transaction,
   ledger:{sourceHash:this.sourceHash,relationHash:this.relationHash,
    sceneId:this.story.loop.scene.id,clock:this.story.loop.time,
    previous:clone(this.previous),lastSeq:this.lastSeq,
    history:clone(this.log),
    expectedCurrentClaimSignature:this.#semanticSignature(latest.current)},
   ledgerSHA256:hash({sourceHash:this.sourceHash,relationHash:this.relationHash,
    sceneId:this.story.loop.scene.id,clock:this.story.loop.time,
    previous:this.previous,lastSeq:this.lastSeq,history:this.log,
    expectedCurrentClaimSignature:this.#semanticSignature(latest.current)})};
 }
 static restore(saved){
  if(!saved||saved.schema!==1||saved.trustedOwnerGenerated!==true||
   !saved.ledger||hash(saved.ledger)!==saved.ledgerSHA256)
   return {ok:false,reason:'Invalid or inconsistent semantic ledger'};
  let story=null;
  try{
   const r=PRSESourceRevision.restore(saved.physicalAndStory);
   if(!r.ok)throw Error('Native GameCore / observer source transaction rejected: '+r.reason);
   story=r.story;
   const l=saved.ledger;
   if(l.sourceHash!==story.sourceHash||l.relationHash!==story.relationHash||
    l.sceneId!==story.loop.scene.id||Math.abs(l.clock-story.loop.time)>1e-6||
    !Array.isArray(l.history)||l.history.length>12000||
    !Number.isInteger(l.lastSeq)||l.lastSeq<0||l.lastSeq>=story.loop.nextSeq)
    throw Error('Source, time, scene or revision-history continuity broken');
   const d=new PRSECurrentSemanticDocument(story);
   const c=d.#now();
   if(d.#semanticSignature(c)!==l.expectedCurrentClaimSignature)
    throw Error('Saved current semantic claims disagree with restored authoritative physical state');
   const existingEvents=new Set(story.loop.events.map(e=>e.sequence));
   for(let i=0;i<l.history.length;i++){
    const h=l.history[i];
    if(!Number.isInteger(h.revision)||h.revision!==i+1||
     !finite(h.worldTime)||h.worldTime>story.loop.time+1e-6||
     typeof h.semanticSignature!=='string'||h.semanticSignature.length!==64||
     !Array.isArray(h.authoritativeEventSequences)||
     h.authoritativeEventSequences.some(seq=>!existingEvents.has(seq)))
     throw Error('Corrupt or invented historical world revision');
   }
   // The physical world clock can advance WITHOUT any semantic proposition
   // changing. The last meaningful revision therefore must be no later than
   // the current world time, but need not be at the exact latest physics tick.
   // Requiring timestamp equality silently corrupts stable literary scenes.
   if((l.history.length>0&&!l.previous)||
    (l.previous&&l.history.at(-1)?.semanticSignature!==l.previous.signature)||
    (l.previous&&(!finite(l.previous.worldTime)||l.previous.worldTime<0||
      l.previous.worldTime>l.clock+1e-6))||
    l.history.some((entry,i)=>i>0&&entry.worldTime+1e-6<l.history[i-1].worldTime))
    throw Error('Inconsistent final historical facts');
   d.previous=clone(l.previous);d.lastSeq=l.lastSeq;d.log=clone(l.history);
   return {ok:true,document:d,story,loop:story.loop};
  }catch(e){story?.dispose();return {ok:false,reason:String(e.message).slice(0,260)};}
 }
 dispose(){this.story.dispose();}
}
