// Source-conditioned support CONTACT -> factual current text -> actual
// physics impulse -> semantic revision -> optional genuine offscreen
// unload/time -> same trusted native Rapier/source/observer save and return.
//
// Cohort fixed by the PREVIOUSLY FROZEN 197-native-scene gold-blind grammar
// placement result: every one of the 13 scene IDs with a real candidate
// placement, not selected according to official source annotation success.
// Every body/identity/shape/source proposal was fixed in prior work.
//
// Crucially, a text adapter may describe physically TRUE newly contacting
// bodies as current physical facts, but this is NOT proof the ORIGINAL author
// intended the relationship, or that a generic cube resembles a real object.
// Complete original descriptions and per-scene inputs stay owner-private.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,object,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {PRSESourceRevision}from'./prse_source_revision_story.mjs';
import {PRSECurrentSemanticDocument}from'./prse_current_semantic_document.mjs';
await initializePhysics();
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-source-only-placement';
const version=process.argv.find(x=>x.startsWith('--version='))?.slice(10)||'v1';
if(!/^v[1-9][0-9]?$/.test(version))throw Error('Invalid output version');
mkdirSync(ROOT,{recursive:true,mode:0o700});
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const frozen=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery/prse_spacy_open_vocab_native_200_raw_v1.json')).records;
const original=JSON.parse(readFileSync(ROOT+'/prse_source_only_nounchunk_same_budget_native_200_raw_v4.json')).rows;
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+4*i)];
const selected=original.map((x,k)=>({sourceIndex:k,...x})).filter(x=>x.status==='source_only_native_gamecore_verified'&&x.movedExistingBodyCount>0);
if(selected.length!==13||selected.reduce((n,x)=>n+x.movedExistingBodyCount,0)!==18)
 throw Error('Frozen source-blind selected physical contacting support cohort changed');
const sha=b=>createHash('sha256').update(b).digest('hex');
const BOX={x:.24,y:.28,z:.24},ROOM={minX:-35.7,minZ:5.55};
const overlap=(a,b)=>['x','y','z'].every(k=>
 Math.abs(a.position[k]-b.position[k])<(a.size[k]+b.size[k])/2+.014);
function reconstruct(scene,ref){
 const s=structuredClone(scene),per=new Map();
 for(const row of ref.addedProvenance){
  const kind=row.kind,k=per.get(kind)||0;per.set(kind,k+1);
  const id=s.id+'-candidate-'+kind.slice(0,20).replace(/_/g,'-')+'-'+sha(Buffer.from(kind)).slice(0,7)+'-'+k;
  if(id!==row.id)throw Error('Invalid original source/asset native candidate identity');
  let candidate=null;
  for(let xi=0;xi<29&&!candidate;xi++)
   for(let zi=0;zi<22;zi++){
    const position={x:ROOM.minX+xi*.6,y:BOX.y/2,z:ROOM.minZ+zi*.54};
    const trial=object(id,kind,position,BOX,{
     body:'dynamic',shape:'box',mass:.3,material:'unknown',
     name:kind.replace(/_/g,' ')+' '+(k+1),
     source:'syntax-proposed:'+s.id+':'+row.sourceSpan[0]+':'+row.sourceSpan[1],
     state:{condition:'intact',openVocabularyCandidate:true,
      sourceMeaningIndependentlyVerified:false,shapeAndMaterialIndependentlyVerified:false}});
    if(!s.entities.some(e=>!e.state?.destroyed&&overlap(e,trial))){candidate=trial;break;}
   }
  if(!candidate)throw Error('Frozen generic body cannot be re-instantiated');
  s.entities.push(candidate);
 }
 return s;
}
function contact(loop,a,b){
 const A=loop.active.get(a),B=loop.active.get(b);
 if(!A||!B)return null;
 let n=0;
 for(let i=0;i<A.numColliders();i++)for(let j=0;j<B.numColliders();j++)
  loop.game.world.contactPair(A.collider(i),B.collider(j),m=>n+=m.numContacts());
 return n>0;
}
const records=[];
for(const row of selected){
 const id=row.sourceId,p=source[id],ref=frozen[row.sourceIndex];
 if(ids[row.sourceIndex]!==id||ref.sourceID!==id)throw Error('Frozen source IDs mismatch');
 let world=null,returned=null;
 const result={sourceId:id,sourceGroup:id<100?'human':'assisted',
  originalProposedNativeContacts:row.movedExistingBodyCount,
  status:'started',physicalSupportBefore:[],physicalSupportAfter:[]};
 try{
  const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
  if(!layout.accepted)throw Error('Preaccepted world no longer valid');
  const sc=reconstruct(layout.scene,ref);
  const placed=row.attempts.filter(x=>x.status==='nominally_valid_prephysics_source_on');
  for(const a of placed){
   const e=sc.entities.find(x=>x.id===a.childId);
   if(!e||!sc.entities.some(x=>x.id===a.supportId))throw Error('Lost prior source entity');
   e.position={...a.chosenSourceOnlyPosition};e.supportId=a.supportId;
  }
  if(geometryIssues(sc).length)throw Error('Prior source-conditioned attached world geometry invalid');
  world=new PRSELoop(sc);
  world.tick(38);
  const story=new PRSESourceRevision(world,p.relations,{observerRadius:12});
  const current=new PRSECurrentSemanticDocument(story);
  const before=current.record().current;
  result.initialOriginalSourceUnchanged=story.sourceArchive().originalText===p.text;
  const available=placed.map(x=>({
   childId:x.childId,parentId:x.supportId,
   actuallyTouching:contact(world,x.childId,x.supportId),
   worldDocumentSupportTruth:before.physicalSupportAudit.find(c=>
    c.childID===x.childId&&c.parentID===x.supportId)?.truth||'missing'}));
  result.physicalSupportBefore=available;
  if(available.some(x=>x.actuallyTouching!==true||x.worldDocumentSupportTruth!=='true'))
   throw Error('Physical document failed to report real native support in source-conditioned scene');
  const physicalStatements=before.verifiedTextClauses.filter(c=>
   c.type==='physically_verified_support_not_source_entailed'&&
   placed.some(x=>x.childId===c.ids[0]&&x.supportId===c.ids[1]));
  result.narratedExplicitlyPhysicalButNotSourceEntailed=physicalStatements.length;
  result.initialSourceOnlyContactCount=available.length;
  // One actual GameCore event/action per selected scene, fixed beforehand.
  const disturbed=placed[0];
  if(!world.applyImpulse(disturbed.childId,{x:4,y:1.1,z:.5}))
   throw Error('Native GameCore refused source object impulse');
  world.tick(155);
  const updated=current.record();
  result.actualNativeContactAfterImpulse=contact(world,disturbed.childId,disturbed.supportId);
  result.meaningfulWorldRevision=updated.changed;
  result.afterEventCurrentSourceDescriptionDoesNotInventContact=
   !updated.current.verifiedTextClauses.some(c=>
    c.claim==='true'&&c.ids?.[0]===disturbed.childId&&c.ids?.[1]===disturbed.supportId&&
    result.actualNativeContactAfterImpulse===false);
  if(!result.afterEventCurrentSourceDescriptionDoesNotInventContact)
   throw Error('Post-impulse narrator kept an actual physically false support');
  result.afterImpulseTippedOrMovedActualState=Boolean(world.entities.get(disturbed.childId).state.moved||
   world.entities.get(disturbed.childId).state.tipped);
  // Attempt ONLY real GameCore offscreen unload. Never pretend the solver
  // is stopped or settled when authoritative GameCore does not permit it.
  const unloading=world.dematerialize();
  result.actualOffscreenUnloaded=unloading>0;
  if(result.actualOffscreenUnloaded){
   world.advanceOffscreen(7);
   const asleep=current.record().current;
   result.offscreenSupportTruthNoLongerAsserted=asleep.verifiedTextClauses.every(c=>
     !placed.some(x=>x.childId===c.ids?.[0]&&x.supportId===c.ids?.[1])||
     c.type!=='physically_verified_support_not_source_entailed');
  }
  const snapshot=JSON.parse(JSON.stringify(current.snapshot()));
  const reloaded=PRSECurrentSemanticDocument.restore(snapshot);
  if(!reloaded.ok)throw Error('Full native GameCore/source/observer/semantic restore refused: '+reloaded.reason);
  returned=reloaded.document;
  result.persistedOriginalSource=returned.story.sourceArchive().originalText===p.text;
  result.savedAllOriginalBodyIDs=placed.every(x=>returned.story.loop.entities.has(x.childId)&&
    returned.story.loop.entities.has(x.supportId));
  result.restoreCurrentSemanticDocumentExactly=returned.current().text===current.current().text;
  if(result.actualOffscreenUnloaded){
   returned.story.loop.materialize();returned.story.loop.tick(1);
  }
  result.restoredNativePhysicsTruth=placed.map(x=>({
   childId:x.childId,supportId:x.supportId,
   physicallyTouching:contact(returned.story.loop,x.childId,x.supportId),
   documentSupportTruth:returned.current().physicalSupportAudit.find(y=>
    y.childID===x.childId&&y.parentID===x.supportId)?.truth||'unknown'}));
  result.physicalSupportAfter=result.restoredNativePhysicsTruth;
  result.status='native_source_physical_semantic_return';
  if(!result.persistedOriginalSource||!result.savedAllOriginalBodyIDs||
    !result.restoreCurrentSemanticDocumentExactly)
   throw Error('Lost original historic literary text, IDs or trusted current claims across save');
 }catch(e){result.status='failed';result.error=String(e.message).slice(0,210);}
 finally{returned?.dispose();world?.dispose();}
 records.push(result);
}
const good=records.filter(x=>x.status==='native_source_physical_semantic_return');
const summary={sourceDrivenScenesPreviouslySelected:13,
 originallyValidatedNativeOnContacts:18,
 actualNativeCurrentDocumentAndSaveCompleted:good.length,
 executionFailures:records.filter(x=>x.status==='failed').length,
 initiallyRealSourceContactRecordsVerified:good.reduce((n,x)=>n+x.initialSourceOnlyContactCount,0),
 explicitlyPhysicalOnlyNotSourceEntailedStatements:good.reduce((n,x)=>n+x.narratedExplicitlyPhysicalButNotSourceEntailed,0),
 newActualGameCoreImpulses:good.length,
 semanticRevisionsAfterImpulses:good.filter(x=>x.meaningfulWorldRevision).length,
 postImpulseFalseSupportWronglyNarrated:good.filter(x=>!x.afterEventCurrentSourceDescriptionDoesNotInventContact).length,
 realOffscreenUnloads:good.filter(x=>x.actualOffscreenUnloaded).length,
 restoredFullWorldsWithUnchangedOriginalLiteraryText:good.filter(x=>x.persistedOriginalSource).length,
 sourceHistoricallyOrPhysicalStateFalseClaimsAreNotElevated:true,
 sourceMeaningAndRealismLimit:'Source noun meanings and box physical assets not independently validated'};
const content={metadata:{selection:'Every frozen independent source-only extra physical contact source scene, not gold selected',
 physics:'One authoritative actual PRSELoop/GameCore/Rapier world, native current semantic document and optional real offscreen advance',
 sourceAnnotationsNotAccessedDuringActions:true,
 noFullGeneralLiteraryRewriteOrAssetProof:true},summary,records};
const path=ROOT+'/prse_source_only_native_contact_to_current_semantics_13_raw_'+version+'.json';
writeFileSync(path,JSON.stringify(content,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_source_only_native_contact_to_current_semantics_13_aggregate_'+version+'.json',import.meta.url),
 JSON.stringify({metadata:{...content.metadata,privateRawSHA256:sha(readFileSync(path))},
 summary,sourceCases:records.map(x=>({id:x.sourceId,status:x.status,
  initialContactCount:x.initialSourceOnlyContactCount||0,
  truePhysicalOnlyStatements:x.narratedExplicitlyPhysicalButNotSourceEntailed||0,
  offscreen:x.actualOffscreenUnloaded??false,error:x.error||null}))},null,2)+'\n',{flag:'wx'});
console.log('SOURCE_ONLY_CONTACT_TO_CURRENT_LITERARY_STATE',JSON.stringify(summary));
