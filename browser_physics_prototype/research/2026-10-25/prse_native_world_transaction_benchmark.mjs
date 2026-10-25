// Full authoritative PRSE GameCore continuation from the same exact save
// boundary, comparing:
//   A. Uninterrupted native PRSE GameCore/Rapier
//   B. Trusted semantic-JSON + Rapier binary world, restored with explicit
//      authoritative body/joint/semantic ID rebinding
//   C. Existing GameCore JSON body reconstruction baseline.
//
// Unlike the earlier solver-only study, ALL paths call GameCore.step(), so
// ragdoll, player, WorldBridge streaming, character needs, semantic time,
// native event sequences and the actual PRSE scene are genuinely exercised.
//
// Source scenes are the 63 fixed originally sampled SceneEval proposals with
// dynamic bodies from the earlier independent perception benchmark. SceneEval
// annotation labels are NOT used by the solver. Contact-rich failures from
// earlier source IDs 27/91/140 are retained as negative evidence.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {PRSEGroundedFacts}from'./prse_grounded_relation_narration.mjs';
import {recordNativePRSEState,restoreNativePRSEState}from'./prse_native_world_transaction.mjs';
await initializePhysics();
const root='/data/var/games/prse_semantic_research/runs/2026-10-25-offscreen-motion';
mkdirSync(root,{recursive:true,mode:0o700});
const sources=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const previous=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility/prse_observer_event_batch_200_raw_v2.json'));
const selection=previous.rows.filter(x=>x.status==='evaluated');
if(selection.length!==63)throw Error('Source fixture count changed');
const sha=b=>createHash('sha256').update(b).digest('hex');
const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const rotation=(a,b)=>2*Math.acos(Math.max(-1,Math.min(1,Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w))));
const pose=(x,y)=>{
 let positionError=0,velocityError=0,rotationError=0;
 for(const [id,b]of x.active){
  if(!b.isDynamic())continue;
  const other=y.active.get(id);
  if(!other)throw Error('Physical source ID missing after restore');
  positionError=Math.max(positionError,distance(b.translation(),other.translation()));
  velocityError=Math.max(velocityError,distance(b.linvel(),other.linvel()));
  rotationError=Math.max(rotationError,rotation(b.rotation(),other.rotation()));
 }
 return {positionErrorMeters:positionError,velocityErrorMetersPerSecond:velocityError,rotationErrorRadians:rotationError};
};
const eventSequence=x=>x.events.map(e=>[e.sequence,e.type,e.ids,e.origin]);
const facts=(x,original)=>new PRSEGroundedFacts(x,original.relations).current().map(r=>r.truth);
const start=performance.now(),all=[];
for(let i=0;i<selection.length;i++){
 const selected=selection[i],p=sources[+selected.id],scene=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const row={id:selected.id,kind:selected.chosenCategory,subset:selected.sourceType,status:'not-tested'};
 let original=null,native=null,json=null;
 try{
  if(!scene.accepted)throw Error('Previous source fixture invalid');
  original=new PRSELoop(scene.scene);original.tick(18);
  const target=scene.scene.entities.find(e=>e.kind===selected.chosenCategory&&e.body==='dynamic');
  if(!target)throw Error('Original source dynamic target absent');
  original.applyImpulse(target.id,{x:1.1,y:.35,z:.55});original.tick(150);
  const savedNative=recordNativePRSEState(original),savedJSON=JSON.parse(JSON.stringify(original.snapshot()));
  const restoredNative=restoreNativePRSEState(savedNative);
  const restoredJSON=PRSELoop.restore(savedJSON);
  if(!restoredNative.ok||!restoredJSON.ok)
   throw Error('Restored native: '+restoredNative.reason+' / JSON: '+restoredJSON.reason);
  native=restoredNative.loop;json=restoredJSON.loop;
  row.nativeBytes=savedNative.nativeBytes;
  row.totalTransactionalJSONBytes=Buffer.byteLength(JSON.stringify(savedNative));
  row.currentJSONBytes=Buffer.byteLength(JSON.stringify(savedJSON));
  const actions=[{tick:150,impulse:{x:4,y:1.1,z:1.5},advance:110},
   {tick:260,impulse:{x:-1.6,y:.45,z:1},advance:100}];
  for(const input of actions){
   for(const world of [original,native,json]){
    if(!world.applyImpulse(target.id,input.impulse))throw Error('Authoritative action failed');
    world.tick(input.advance);
   }
  }
  const reference=pose(original,original);
  const deltaNative=pose(original,native),deltaJSON=pose(original,json);
  row.native=deltaNative;row.structuredJSON=deltaJSON;
  row.timeErrors={native:Math.abs(native.time-original.time),
   JSON:Math.abs(json.time-original.time)};
  row.semanticFacts={
   nativeDifferences:facts(original,p).filter((e,k)=>e!==facts(native,p)[k]).length,
   JSONDifferences:facts(original,p).filter((e,k)=>e!==facts(json,p)[k]).length};
  row.eventIdentity={
   nativeEqual:JSON.stringify(eventSequence(original))===JSON.stringify(eventSequence(native)),
   JSONEqual:JSON.stringify(eventSequence(original))===JSON.stringify(eventSequence(json))};
  row.playerErrorMeters={native:distance(original.game.player.translation(),native.game.player.translation()),
   JSON:distance(original.game.player.translation(),json.game.player.translation())};
  row.ragdollTorsoErrorMeters={native:distance(original.game.activeRagdoll.parts.torso.translation(),
      native.game.activeRagdoll.parts.torso.translation()),
    JSON:distance(original.game.activeRagdoll.parts.torso.translation(),
      json.game.activeRagdoll.parts.torso.translation())};
  row.originalLiteraryTextPreserved=native.scene.prose===p.text&&json.scene.prose===p.text;
  row.nativeRapierWorldBytesAfter=original.game.world.takeSnapshot().length;
  row.nativeRapierFinalSHAEqual=sha(original.game.world.takeSnapshot())===sha(native.game.world.takeSnapshot());
  row.nativeStructuredCoreSHAEqual=sha(Buffer.from(JSON.stringify(original.game.snapshot())))===
     sha(Buffer.from(JSON.stringify(native.game.snapshot())));
  row.status='evaluated';
 }catch(e){row.status='failed';row.reason=String(e?.message||e).slice(0,230);}
 finally{native?.dispose();json?.dispose();original?.dispose();}
 all.push(row);
 if((i+1)%10===0)console.log('PROGRESS',i+1,'of',selection.length);
}
const good=all.filter(x=>x.status==='evaluated');
const summary={sourceScenes:selection.length,evaluated:good.length,failed:selection.length-good.length,
 nativeFullPhysicalWorldSHAEqual:good.filter(x=>x.nativeRapierFinalSHAEqual).length,
 nativeFullSemanticCoreSHAEqual:good.filter(x=>x.nativeStructuredCoreSHAEqual).length,
 nativePhysicalAbove2cm:good.filter(x=>x.native.positionErrorMeters>.02).length,
 currentJSONPhysicalAbove2cm:good.filter(x=>x.structuredJSON.positionErrorMeters>.02).length,
 maxNativePoseError:good.length?Math.max(...good.map(x=>x.native.positionErrorMeters)):null,
 maxJSONPoseError:good.length?Math.max(...good.map(x=>x.structuredJSON.positionErrorMeters)):null,
 nativeSemanticTruthMismatchingCases:good.filter(x=>x.semanticFacts.nativeDifferences>0).length,
 nativeEventSequenceMismatches:good.filter(x=>!x.eventIdentity.nativeEqual).length,
 nativeWorldClockMismatches:good.filter(x=>x.timeErrors.native>1e-5).length,
 nativePlayerPoseMismatches:good.filter(x=>x.playerErrorMeters.native>.001).length,
 nativeRagdollTorsoMismatches:good.filter(x=>x.ragdollTorsoErrorMeters.native>.01).length,
 originalSourceTextsPreserved:good.filter(x=>x.originalLiteraryTextPreserved).length,
 medianBinarySnapshotBytes:good.length?good.map(x=>x.nativeBytes).sort((a,b)=>a-b)[Math.floor(good.length/2)]:null,
 medianTotalTransactionBytes:good.length?good.map(x=>x.totalTransactionalJSONBytes).sort((a,b)=>a-b)[Math.floor(good.length/2)]:null,
 medianCurrentJSONBytes:good.length?good.map(x=>x.currentJSONBytes).sort((a,b)=>a-b)[Math.floor(good.length/2)]:null,
 wallTimeSeconds:+((performance.now()-start)/1000).toFixed(2)};
const full={metadata:{
 source:'Frozen SceneEval source prompts, first100 human and systematically sampled assisted dynamic cases, no gold annotations',
 comparison:'Existing GameCore/Rapier full native world save plus same semantic JSON vs plain PRSELoop JSON vs uninterrupted full GameCore',
 actualScope:'Real native GameCore.step, ragdoll, player, world bridge, semantic time, current source object IDs and event stream',
 caution:'Trusted build-tied binary snapshot, research-only, not integrated into live save/region streaming, no user participants and no extra model/GPU calls'},
 summary,results:all};
const file=root+'/prse_full_gamecore_native_transaction_63_raw_v1.json';
writeFileSync(file,JSON.stringify(full,null,2)+'\n',{flag:'wx',mode:0o600});
const safe={metadata:{...full.metadata,privateRawSHA256:sha(readFileSync(file)),privateRawPath:file},
 summary,cases:all.map(x=>({id:x.id,subset:x.subset,kind:x.kind,status:x.status,
  nativePoseErrorMeters:x.native?.positionErrorMeters??null,
  JSONPoseErrorMeters:x.structuredJSON?.positionErrorMeters??null,
  nativePhysicalWorldSHAEqual:x.nativeRapierFinalSHAEqual??null,
  nativeWorldTimeError:x.timeErrors?.native??null,
  nativeEventStreamEqual:x.eventIdentity?.nativeEqual??null,reason:x.reason||null}))};
writeFileSync(new URL('prse_full_gamecore_native_transaction_63_aggregate_v1.json',import.meta.url),
 JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log('FINAL',JSON.stringify(summary));
