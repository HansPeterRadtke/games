// Independent offscreen motion continuation vs uninterrupted GameCore/Rapier
// baseline on the SAME frozen externally written SceneEval scene proposals.
// Uses the actual authoritative native 3D solver for both paths. No toy solver.
//
// The source texts/scene proposals were frozen in previous research. The
// external annotated gold does NOT enter this motion study. Perturbations are
// investigator-fixed physical impulses, not human gameplay demonstrations.
//
// Offscreen policy: run real native physics until *all* moving bodies are
// sufficiently stable with actual contact evidence over 20 consecutive ticks.
// Then remove the physics region, advance semantic time without physics,
// save/reload the unloaded representation, and rematerialize original body IDs.
// If not demonstrably safe within 180 native steps, keep real physics running.
import assert from 'node:assert/strict';
import {writeFileSync,readFileSync,mkdirSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {createHash} from 'node:crypto';
import {initializePhysics} from '../../physics-core.js';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {PRSELoop,geometryIssues} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {PRSEGroundedFacts} from './prse_grounded_relation_narration.mjs';
import {physicallySettleThenUnload} from './prse_offscreen_motion_settling.mjs';

await initializePhysics();
const subset=process.argv.includes('--human')?'human':process.argv.includes('--assisted')?'assisted':null;
if(!subset)throw Error('Specify --human or --assisted');
const configuration={
 horizonTicks:300,maximumPhysicalTicksBeforeRefusal:180,
 requiredQuietTicks:20,
 impulses:[
  {name:'moderate',v:{x:1.1,y:.35,z:.55}},
  {name:'strong',v:{x:4,y:1.2,z:1.6}}
 ],source:'First 100 original human and every fourth 400 semi-automated SceneEval descriptions',
 policy:'Native GameCore/Rapier physical settling before offscreen semantic eviction; no independent solver',
 oracle:'Uninterrupted GameCore physics for exactly same starting world state and elapsed time',
 assumptions:'One unloaded remote research region; native player/NPC physics not simulated offscreen; no generative model or human demonstration'};
const base='/data/var/games/prse_semantic_research/runs/2026-10-25-offscreen-motion';
mkdirSync(base,{recursive:true,mode:0o700});
const past=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility/prse_observer_event_batch_200_raw_v2.json'));
const target=past.rows.filter(x=>x.status==='evaluated'&&x.sourceType===subset);
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const hash=(s)=>createHash('sha256').update(s).digest('hex');
const quatGap=(a,b)=>{
 const dot=Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w);
 return 2*Math.acos(Math.max(-1,Math.min(1,dot)));
};
const physicalEvents=new Set(['external_impulse','displaced','tipped','rotated','impact','lost_support','rested_on']);
const poses=loop=>new Map([...loop.active].filter(([id,b])=>b.isDynamic())
 .map(([id,b])=>[id,{p:{...b.translation()},v:{...b.linvel()},q:{...b.rotation()},ang:{...b.angvel()}}]));
function compare(worldA,worldB,ids){
 const a=poses(worldA),b=poses(worldB);
 let positionError=0,linearVelocityError=0,rotationError=0,angularVelocityError=0;
 for(const id of ids){
  if(!a.has(id)||!b.has(id))throw Error('Object identity or physical body disappeared');
  const x=a.get(id),y=b.get(id);
  const error=(p,q)=>Math.hypot(p.x-q.x,p.y-q.y,p.z-q.z);
  positionError=Math.max(positionError,error(x.p,y.p));
  linearVelocityError=Math.max(linearVelocityError,error(x.v,y.v));
  angularVelocityError=Math.max(angularVelocityError,error(x.ang,y.ang));
  rotationError=Math.max(rotationError,quatGap(x.q,y.q));
 }
 return {maxPositionMeters:positionError,maxLinearVelocityMetersPerSecond:linearVelocityError,
  maxOrientationRadians:rotationError,maxAngularVelocityRadiansPerSecond:angularVelocityError};
}
function sourceClaims(loop,p){
 const rows=new PRSEGroundedFacts(loop,p.relations).current();
 return rows.map(r=>r.truth);
}
const events=loop=>loop.events.filter(x=>physicalEvents.has(x.type)).map(x=>({type:x.type,ids:x.ids}));
const start=performance.now();
const results=[];
for(let ix=0;ix<target.length;ix++){
 const targetCase=target[ix],p=source[+targetCase.id];
 const physical=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!physical.accepted||geometryIssues(physical.scene).length)
  throw Error('A source eligibility fixture changed: '+p.sourceId);
 for(const stimulus of configuration.impulses){
  let initial=null,reference=null,accelerated=null,semanticReloaded=null,finalReloaded=null;
  const record={id:p.sourceId,subset,chosenCategory:targetCase.chosenCategory,
   impulse:stimulus.name,impulseVector:stimulus.v,
   timeSeconds:configuration.horizonTicks/60,status:'started'};
  try{
   initial=new PRSELoop(physical.scene);initial.tick(18);
   const selected=physical.scene.entities.find(e=>e.kind===targetCase.chosenCategory&&e.body==='dynamic');
   if(!selected)throw Error('Frozen original dynamic category disappeared');
   record.entityId=selected.id;
   if(!initial.applyImpulse(selected.id,stimulus.v))throw Error('Impulse invalid');
   const savedStart=JSON.parse(JSON.stringify(initial.snapshot()));
   const A=PRSELoop.restore(savedStart),B=PRSELoop.restore(savedStart);
   if(!A.ok||!B.ok)throw Error('Identical initial GameCore snapshot could not restore');
   reference=A.loop;accelerated=B.loop;
   const mutableIDs=[...reference.active].filter(([id,b])=>b.isDynamic()).map(([id])=>id);
   record.numberDynamicObjects=mutableIDs.length;
   if(mutableIDs.length!==[...accelerated.active].filter(([id,b])=>b.isDynamic()).length)
    throw Error('Mismatched clone body counts');
   // Clock and physical starting poses must actually be identical.
   const original=compare(reference,accelerated,mutableIDs);
   if(original.maxPositionMeters>1e-5)throw Error('Starting world state was not identical');
   const beforeRef=reference.game.time;
   reference.tick(configuration.horizonTicks);
   const baselineEvents=events(reference);
   const tPolicy=performance.now();
   const settled=physicallySettleThenUnload(accelerated,{
    maxPhysicalTicks:configuration.maximumPhysicalTicksBeforeRefusal,
    requiredQuietTicks:configuration.requiredQuietTicks,
    totalTicks:configuration.horizonTicks
   });
   const policyWallMs=performance.now()-tPolicy;
   const maxTimeDelta=Math.abs(reference.time-accelerated.time);
   if(maxTimeDelta>1e-5)throw Error('Authoritative clocks disagree');
   record.offloaded=settled.offloaded;
   record.policy={reason:settled.reason,actualPhysicalTicks:settled.physicalTicks,
    skippedPhysicsTicks:settled.skippedPhysicsTicks,
    budgetFractionSaved:settled.skippedPhysicsTicks/configuration.horizonTicks,
    lastProbe:settled.lastProbe,
    measuredPolicyWallMs:+policyWallMs.toFixed(2)};
   record.sourceProsePreserved=reference.scene.prose===accelerated.scene.prose&&
    accelerated.scene.prose===p.text;
   record.poseBeforeOneTick=compare(reference,accelerated,mutableIDs);
   record.referencePhysicsEvents=baselineEvents;
   record.policyPhysicalEvents=events(accelerated);
   record.eventTypesIdentical=JSON.stringify(baselineEvents)===JSON.stringify(record.policyPhysicalEvents);
   record.globalClockErrorSeconds=maxTimeDelta;
   record.characterHydrationDifference=accelerated.game.character.hydration-reference.game.character.hydration;
   // Every offloaded region is also *actually saved while unloaded*, and
   // then restored via the same native GameCore snapshot contract.
   if(settled.offloaded){
    const savedWhileUnloaded=settled.savedWhileSemantic;
    if(savedWhileUnloaded.materialized)throw Error('Claimed offscreen save was materialized');
    const saved=PRSELoop.restore(savedWhileUnloaded);
    if(!saved.ok||saved.loop.active.size)throw Error('Unloaded semantic snapshot could not restore');
    semanticReloaded=saved.loop;
    record.unloadedSaveRestored=true;
    record.savedSemanticTimeError=Math.abs(semanticReloaded.time-accelerated.time);
    record.savedOriginalIdsPreserved=[...semanticReloaded.entities].every(([id])=>accelerated.entities.has(id));
    semanticReloaded.materialize();
    const offscreenReturn=compare(semanticReloaded,accelerated,mutableIDs);
    record.semanticReloadPoseErrorMeters=offscreenReturn.maxPositionMeters;
   }
   // Independent source-fact oracle only after an *actual* resumed physics
   // step on both paths to rebuild true Rapier contact manifolds.
   reference.tick(1);accelerated.tick(1);
   record.poseAfterOneTick=compare(reference,accelerated,mutableIDs);
   const actualReference=sourceClaims(reference,p),actualPolicy=sourceClaims(accelerated,p);
   record.sourceTruthClaims=actualReference.length;
   record.sourceTruthDisagreements=actualReference.filter((x,i)=>x!==actualPolicy[i]).length;
   const final=JSON.parse(JSON.stringify(accelerated.snapshot()));
   const reloaded=PRSELoop.restore(final);
   if(!reloaded.ok)throw Error('Final game-world save failed');
   finalReloaded=reloaded.loop;
   record.finalIDsStable=[...accelerated.entities.keys()].every(id=>finalReloaded.entities.has(id));
   record.finalPoseSaveErrorMeters=compare(accelerated,finalReloaded,mutableIDs).maxPositionMeters;
   record.status='evaluated';
  }catch(e){record.status='failed';record.reason=String(e?.message||e).slice(0,220);}
  finally{finalReloaded?.dispose();semanticReloaded?.dispose();accelerated?.dispose();reference?.dispose();initial?.dispose();}
  results.push(record);
 }
 if((ix+1)%10===0)console.log('PROGRESS',subset,ix+1,'sourceScenesOf',target.length);
}
const complete=results.filter(x=>x.status==='evaluated');
const saved=complete.filter(x=>x.offloaded);
const full=complete.filter(x=>!x.offloaded);
const summary={
 subset,sourceScenes:target.length,perturbationsPerScene:configuration.impulses.length,
 episodes:results.length,evaluated:complete.length,failed:results.length-complete.length,
 offloadAccepted:saved.length,offloadRefused:full.length,
 worldClockEquivalent:complete.filter(x=>x.globalClockErrorSeconds<1e-5).length,
 sceneProseAndIdentityPreserved:complete.filter(x=>x.sourceProsePreserved&&x.finalIDsStable).length,
 externalSourceTruthMismatchingCases:complete.filter(x=>x.sourceTruthDisagreements>0).length,
 eventStreamMismatchCases:complete.filter(x=>!x.eventTypesIdentical).length,
 comparisonLargePoseDeviationCases:complete.filter(x=>x.poseAfterOneTick.maxPositionMeters>.02).length,
 medianUnloadedPhysicsTicks: saved.length? saved.map(x=>x.policy.skippedPhysicsTicks).sort((a,b)=>a-b)[Math.floor(saved.length/2)]:null,
 maximumPoseErrorMeters:complete.length?Math.max(...complete.map(x=>x.poseAfterOneTick.maxPositionMeters)):null,
 maximumOffloadPoseErrorMeters:saved.length?Math.max(...saved.map(x=>x.poseAfterOneTick.maxPositionMeters)):null,
 worstUnloadedSemanticSavePoseErrorMeters:saved.length?Math.max(...saved.map(x=>x.semanticReloadPoseErrorMeters)):null,
 maxCharacterHydrationDifference:complete.length?Math.max(...complete.map(x=>Math.abs(x.characterHydrationDifference||0))):null,
 wallTimeSeconds:+((performance.now()-start)/1000).toFixed(2)};
const payload={metadata:{
 source:'Official SceneEval-500 external descriptions, original human and fixed assisted sampling, no annotated gold used',
 sourceIDs:target.map(x=>x.id),
 study:'One GameCore/Rapier 3D continuous trajectory versus bounded physical-until-converged then unloaded semantic-time/reentry trajectory',
 difference:'Only unloading method; identical source scene, initial actual GameCore snapshot, physical impulse and global time.',
 unsupported:'Production multiple active regions, NPCs, human quality, render throughput, friction/material fidelity, magic offscreen physics, generative narrative are not demonstrated',
 configuration,noGPUorLLM:true,noHumanPlaytest:true},summary,results};
const outName='prse_offscreen_motion_'+subset+'_raw_v1.json';
const targetPath=base+'/'+outName;
writeFileSync(targetPath,JSON.stringify(payload,null,2)+'\n',{flag:'wx',mode:0o600});
const safe={metadata:{...payload.metadata,rawSHA256:hash(readFileSync(targetPath)),
 privateRawPath:targetPath},summary,
 perScene:results.map(x=>({
  id:x.id,impulse:x.impulse,status:x.status,
  unloaded:x.offloaded||false,skippedTicks:x.policy?.skippedPhysicsTicks||0,
  maxPoseErrorMeters:x.poseAfterOneTick?.maxPositionMeters??null,
  factDisagreements:x.sourceTruthDisagreements??null,
  eventSequenceEqual:x.eventTypesIdentical??null,reason:x.reason||null
 }))};
const outfile=new URL('prse_offscreen_motion_'+subset+'_aggregate_v1.json',import.meta.url);
writeFileSync(outfile,JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log('RESULT',JSON.stringify(summary));
