// Counterfactual time/causality comparison: physics-stepped GameCore versus
// offscreen semantic scheduler, from identical initial game state and fire trigger.
// This does NOT claim the whole game (player fatigue/physics) evolves identically.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from './prse_semantic_roundtrip.mjs';
await initializePhysics();
const world={id:'native-fire-timing-parity',
 prose:'The far shelter has a candle beside a vulnerable paper note.',
 entities:[
  object('research-stone','stone',{x:-26,y:.4,z:9},{x:.9,y:.8,z:.65},{body:'fixed',material:'stone'})
 ]};
function create(){
 const a=new PRSELoop(world);
 a.tick(90);
 a.game.worldStreamer.update(36,1,a.game.semantic,{});
 const candle=a.game.semantic.entity('shelter-candle');
 assert(candle&&!candle.materialized,'faraway shelter should be semantic');
 candle.state.lit=true;candle.revision++;
 const ignition=a.game.consequences.startPaperFire(a.time,a.game.semantic);
 assert(ignition.ok);
 return a;
}
const continuous=create(),coarse=create();
const startingTime=continuous.time;
const initialContinuous=continuous.game.snapshot(),initialCoarse=coarse.game.snapshot();
// Independently initialized Rapier ragdolls can show tiny floating-point/contact
// differences. Comparing whole snapshot bytes incorrectly rejects equal source
// text, timing, pending causal rules and character state.
const initialDifference={
 playerYDelta:initialContinuous.player.p.y-initialCoarse.player.p.y,
 torsoYDelta:initialContinuous.ragdoll.parts.torso.position.y-initialCoarse.ragdoll.parts.torso.position.y,
 clockDelta:initialContinuous.time-initialCoarse.time,
 nativeSemanticDelta:initialContinuous.semantic.time-initialCoarse.semantic.time
};
assert(Math.abs(initialDifference.clockDelta)<1e-9);
assert.deepEqual(initialContinuous.consequences.pending,initialCoarse.consequences.pending);
assert.equal(initialContinuous.semantic.entities.find(e=>e.id==='shelter-note').state.condition,
 initialCoarse.semantic.entities.find(e=>e.id==='shelter-note').state.condition);
coarse.dematerialize();
const duration=40;
const t1=performance.now();
for(let i=0;i<4;i++)continuous.tick(600);
const continuousWall=performance.now()-t1;
const t2=performance.now();
coarse.advanceOffscreen(duration);
const coarseWall=performance.now()-t2;
const officialNames=['paper_smolders','paper_burning','bench_smoldering','paper_ashes',
 'bench_scorching','bench_scorched','shelter_smoky'];
function details(game){
 const history=game.consequences.history.filter(e=>officialNames.includes(e.type));
 return {clock:game.time,
  semanticClock:game.semantic.time,remainingAccumulator:game.semanticAccumulator,
  physicsTicks:game.stepCount,
  note:game.semantic.entity('shelter-note').state.condition,
  bench:game.semantic.entity('shelter-bench').state.condition,
  shelter:game.semantic.entity('shelter-setting').state.condition,
  events:history.map(e=>({type:e.type,when:e.time,cause:e.cause,outcome:e.outcome,visibility:e.visibility})),
  fatigue:game.character.fatigue,
  hydration:game.character.hydration};
}
const a=details(continuous.game),b=details(coarse.game);
const same=JSON.stringify(a.events)===JSON.stringify(b.events);
assert(same,'native event sequence or causal timing changed between physical stepping and semantic time');
assert(a.note===b.note&&a.bench===b.bench&&a.shelter===b.shelter);
assert(Math.abs(a.clock-b.clock)<1e-6,'native clock deviated');
assert(Math.abs(a.semanticClock-b.semanticClock)<1e-4,'native offscreen semantic time deviated');
assert(a.events.length===7);
assert(coarse.game.stepCount===90&&continuous.game.stepCount===2490);
const noteUnreentered=!coarse.game.worldBridge.active.has('shelter-note');
assert(noteUnreentered);
const mismatch={
 fatigueDelta:coarse.game.character.fatigue-continuous.game.character.fatigue,
 hydrationDelta:coarse.game.character.hydration-continuous.game.character.hydration,
 physicsTicksDifference:continuous.game.stepCount-coarse.game.stepCount
};
const results={
 metadata:{kind:'headless native game physics vs semantic-only external-region progression',
 source:'Existing GameCore plus WorldConsequences official shelter fire, same initial snapshot',
 rerunVariance:'Host shares heavy CPU work; durations are single observations, not stable speed benchmark'},
 startingTime,initialDifference,durationSeconds:duration,
 fullSimulation:{wallMs:+continuousWall.toFixed(2),...a},
 offscreenOnly:{wallMs:+coarseWall.toFixed(2),...b},
 comparison:{sameSevenNativeCausalEvents:same,
  sameNativeSemanticFinalConditions:a.note===b.note&&a.bench===b.bench&&a.shelter===b.shelter,
  timeDifferenceSeconds:a.clock-b.clock,
  nativeSemanticTimeDifferenceSeconds:a.semanticClock-b.semanticClock,
  noteStayedUnmaterialized:noteUnreentered,
  controlledDifferences:mismatch,
  fullStateEquivalent:false,
  reason:'Offscreen path deliberately does not advance player physics, ragdoll, stamina/fatigue, or physics-step counters'}
};
writeFileSync(new URL('prse_clock_counterfactual_visible_vs_offscreen.json',import.meta.url),
 JSON.stringify(results,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(results.comparison));
console.log('wallMs',+continuousWall.toFixed(2),+coarseWall.toFixed(2));
continuous.dispose();coarse.dispose();
