// Research-only continuation: one native GameCore time versus scene semantic time,
// simultaneous native WorldConsequences and independent sidecar offscreen schedule.
// Earlier negative clock-divergence evidence remains immutable in prior results.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from './prse_semantic_roundtrip.mjs';
await initializePhysics();

function newScenario(){
 const scene={id:'timeline-cause-scene',
  prose:'A wooden bench and a paper note remain in a distant unused room as the player leaves.',
  entities:[
   object('timed-wooden-table','bench',{x:-26,y:.45,z:9},{x:2,y:.9,z:1},{body:'fixed',material:'wood'}),
   object('timed-paper-note','note',{x:-26,y:.91,z:9},{x:.25,y:.02,z:.2},
    {material:'paper',mass:.04,supportId:'timed-wooden-table'})
  ]};
 const loop=new PRSELoop(scene);
 loop.tick(90); // real native GameCore.step(), includes physics and semantic clocks
 const start={gameTime:loop.game.time,sceneTime:loop.time,
  nativeSemanticTime:loop.game.semantic.time,nativeAccumulator:loop.game.semanticAccumulator,
  actualPhysicsTicks:loop.game.stepCount};
 assert(Math.abs(loop.game.time-loop.time)<1e-8);
 assert(loop.game.stepCount===90);
 // Create official pre-existing PRSE world/long-running consequences by its own APIs,
 // never by crafting manually-true descriptions.
 loop.game.worldStreamer.update(36,1,loop.game.semantic,{});
 const candle=loop.game.semantic.entity('shelter-candle');
 const note=loop.game.semantic.entity('shelter-note');
 assert(candle && note,'Existing generated PRSE shelter is required');
 assert(!candle.materialized&&!note.materialized);
 candle.state.lit=true;candle.revision++;
 const begun=loop.game.consequences.startPaperFire(loop.game.time,loop.game.semantic);
 assert(begun.ok,'the canonical game core rejected a valid lit-note fire');
 loop.dematerialize();
 assert(loop.igniteOffscreen('timed-paper-note'));
 return {loop,start};
}
const {loop:full,start:initial}=newScenario();
const {loop:part}=newScenario();
const basePhysicsTicks=full.game.stepCount,basePlayer={...full.game.player.translation()};
const small=3.5,long=42.5,total=small+long;
const beforeNativeEvents=full.game.eventSequence;
full.advanceOffscreen(total);
part.advanceOffscreen(small);
const partial=JSON.parse(JSON.stringify(part.snapshot()));
const loaded=PRSELoop.restore(partial);
assert(loaded.ok,'Unable to restore pending offscreen native/core timers');
const resumed=loaded.loop;
resumed.advanceOffscreen(long);
const nativeEvents=instance=>instance.game.events.filter(e=>['paper_smolders','paper_burning','bench_smoldering','paper_ashes','bench_scorching','bench_scorched','shelter_smoky'].includes(e.type));
const compareCore=instance=>({
 time:instance.game.time,
 nativeSemanticTime:instance.game.semantic.time,
 accumulator:instance.game.semanticAccumulator,
 physicsTicks:instance.game.stepCount,
 noteCondition:instance.game.semantic.entity('shelter-note').state.condition,
 benchCondition:instance.game.semantic.entity('shelter-bench').state.condition,
 shelterCondition:instance.game.semantic.entity('shelter-setting').state.condition,
 fireEvents:nativeEvents(instance).map(e=>({type:e.type,time:e.time,visibility:e.visibility,
  cause:e.cause,outcome:e.outcome})),
 pending:instance.game.consequences.pending.length,
 emittedNativeEventCount:instance.game.eventSequence
});
const out={
 metadata:{kind:'research-sidecar, source GameCore and native WorldConsequences are exercised',
  saveVersion:full.snapshot().version,originalPriorResult:'prse_semantic_adversarial_results.json',
  fullOffscreenSeconds:total,noPhysicsDuringUnobservedTime:true,
  nativeRuntimeIntegratesThis:false},
 visibleStart:initial,
 unobservedBaseline:compareCore(full),
 splitRestore:compareCore(resumed),
 sidecarBaseline:{time:full.time,events:full.events,
  noteState:full.entities.get('timed-paper-note').state,
  activeBodies:full.active.size,
  currentProse:full.scene.currentProse},
 sidecarRestored:{time:resumed.time,events:resumed.events,
  noteState:resumed.entities.get('timed-paper-note').state,
  activeBodies:resumed.active.size,
  currentProse:resumed.scene.currentProse},
 differences:{}
};
const near=(a,b,epsilon=1e-6)=>Math.abs(a-b)<=epsilon;
for(const instance of [full,resumed]){
 assert(near(instance.game.time,instance.time),'global/core clock mismatch');
 assert(near(instance.game.semantic.time+instance.game.semanticAccumulator,instance.game.time,.0002),
  'semantic clock and accumulator must reconcile with authoritative clock');
 assert(instance.game.stepCount===basePhysicsTicks,'offscreen passed through actual physics ticks');
 assert(instance.game.consequences.pending.length===0);
 assert(instance.game.semantic.entity('shelter-note').state.condition==='ashes');
 assert(instance.game.semantic.entity('shelter-bench').state.condition==='scorched');
 assert(instance.game.semantic.entity('shelter-setting').state.condition==='smoky');
 assert(nativeEvents(instance).length===7,'All native coarse causal stages needed');
 assert(nativeEvents(instance).every(e=>e.visibility==='offscreen'));
 assert(!instance.active.size,'distant physics must remain unloaded');
 assert(instance.entities.get('timed-paper-note').state.condition==='ashes');
 assert(!instance.entities.get('timed-paper-note').materialized);
 const player=instance.game.player.translation();
 assert(near(player.x,basePlayer.x)&&near(player.y,basePlayer.y)&&near(player.z,basePlayer.z),
  'offscreen advancement moved the native player body');
}
const fa=compareCore(full),fb=compareCore(resumed);
assert(near(fa.time,fb.time,1e-5));
assert.deepEqual(fa.fireEvents,fb.fireEvents,'Native fire timeline changed across save/reload');
for(const key of ['noteCondition','benchCondition','shelterCondition','physicsTicks','pending']){
 assert.deepEqual(fa[key],fb[key],key);
}
assert.deepEqual(full.events,resumed.events,'Sidecar scheduled history changed across save/reload');
assert.equal(full.events.find(e=>e.type==='reduced_to_ashes').time,
 resumed.events.find(e=>e.type==='reduced_to_ashes').time);
const fireTime=full.events.find(e=>e.type==='reduced_to_ashes').time;
assert(near(fireTime,initial.gameTime+6,.001),'sidecar destruction incorrectly timestamped at period end');
const legacy=structuredClone(partial);legacy.version=1;
const forged=structuredClone(partial);forged.game.time=partial.game.time-2;
const rejects={priorUnsynchronizedFormat:!PRSELoop.restore(legacy).ok,
 forgedClockDisagreement:!PRSELoop.restore(forged).ok};
assert(Object.values(rejects).every(Boolean));
out.differences={authoritativeSceneClockDelta:full.time-full.game.time,
 semanticClockPlusAccumulatorDelta:full.game.semantic.time+full.game.semanticAccumulator-full.game.time,
 splitUninterruptedWorldDelta:fa.time-fb.time,
 offscreenPhysicsTicks:full.game.stepCount-basePhysicsTicks,
 chronologicalSidecarAshAt:fireTime,
 sidecarFireTimestampNotAtFinalReturn:fireTime<full.time-20,
 splitNativeEventSequenceEqual:JSON.stringify(fa.fireEvents)===JSON.stringify(fb.fireEvents),
 nativeEvents:fa.fireEvents.length,
 chronologyAfterReloadCorrect:true,
 invalidSnapshotRejections:rejects};
const reentryBodies=resumed.materialize();
assert(reentryBodies===2,'both desk and physical ash patch must rematerialize');
assert(resumed.active.has('ash-timed-paper-note'),'no actual ash-body replacement was created');
assert.equal(resumed.entities.get('ash-timed-paper-note').originId,'timed-paper-note');
assert(!resumed.active.has('timed-paper-note'),'destroyed note physically resurrected on reentry');
out.reentry={materializedSurvivingEntities:reentryBodies,
 destroyedStableIdPreserved:resumed.entities.has('timed-paper-note'),
 prose:resumed.scene.currentProse,
 allNativeEventsStillInHistory:resumed.game.consequences.history.length>=7};
const stepCountBefore=resumed.game.stepCount;
resumed.tick(15);
assert(resumed.game.stepCount===stepCountBefore+15,'native physics never resumed');
assert(near(resumed.time,resumed.game.time));
out.reentry.nativePhysicsStepsAfterReturn=resumed.game.stepCount-stepCountBefore;
const output=process.argv.find(x=>x.startsWith('--output='))?.slice(9)||'prse_clock_latest_results.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(output))throw Error('unsafe output name');
writeFileSync(new URL(output,import.meta.url),
 JSON.stringify(out,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,initial,outcomes:out.differences,
 phaseNativeEvents:fa.fireEvents.map(e=>({type:e.type,time:e.time})),
 offscreenWorldTime:fa.time,stepCount:fa.physicsTicks,reentry:out.reentry}));
for(const instance of [full,part,resumed])instance.dispose();
