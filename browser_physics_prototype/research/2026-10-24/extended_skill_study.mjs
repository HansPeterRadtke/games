import assert from 'node:assert/strict';
import {writeFileSync, readFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {initializePhysics, GameCore} from '../../physics-core.js';

await initializePhysics();
const GOAL = -1.2, TICK = 1 / 60, LIMIT = 210;
const rng = (() => {let value=0x19A2D4E7;return () => {value ^= value << 13; value ^= value >>> 17; value ^= value << 5; return (value >>> 0) / 4294967296;};})();
const measure = game => ({x:game.player.translation().x, v:game.player.linvel().x, y:game.player.translation().y,
  speedFactor:game.character.locomotion().speedFactor, time:game.time});
const success = game => {
  const s=measure(game);
  return s.x >= GOAL - .12 && s.x <= GOAL + .4 && Math.abs(s.v) < .5;
};
function gameAt(x, environment='normal') {
  const game = new GameCore();
  game.player.setTranslation({x,y:1,z:0},true);
  game.player.setLinvel({x:0,y:0,z:0},true);
  if(environment==='one_plank'||environment==='two_planks') for(let i=0;i<(environment==='one_plank'?1:2);i++) assert(game.character.collectPlank());
  if(environment==='sprain') game.character.injuries.leftKnee={kind:'sprain',severity:.8};
  if(environment==='fatigue') game.character.fatigue=85;
  return game;
}
function cleanTeacher(game){
  const s=measure(game);
  return s.x < GOAL - .08 && s.x + s.v * .22 < GOAL ? 1 : 0;
}
function feature(game, history){
  const s=measure(game),prev=history.length>=6?history[history.length-6]:history[0];
  return {...s, lagV:prev?.v ?? s.v, lagAction:prev?.action ?? 0};
}
function simulate(start, environment, decide, {perturbation=null, trace=false, maximum=LIMIT, saveTick=null}={}) {
  let game=gameAt(start,environment),history=[], saved=null, saveError=null;
  let stopped=false, count=0, massAtPerturbation=null;
  for(let tick=0;tick<maximum;tick++){
    if(perturbation && tick===perturbation.tick){
      // Exact impulse uses the player's current rigid-body mass.
      massAtPerturbation=game.player.mass();
      game.player.applyImpulse({x:massAtPerturbation*perturbation.deltaV,y:0,z:0},true);
    }
    const info=feature(game,history),action=decide(game,history,tick);
    assert([0,1,-1].includes(action),'invalid imitation action');
    history.push({...info,action,tick});
    assert(game.command({type:'Move',direction:action}));
    game.step();
    count=tick+1;
    if(tick===saveTick){
      saved=JSON.parse(JSON.stringify(game.snapshot()));
      const restored=new GameCore();
      const ok=restored.restore(saved);
      saveError= ok ? Math.abs(restored.player.translation().x-game.player.translation().x):Infinity;
      if(!ok) throw Error('GameCore rejected save');
      game=restored;
    }
    if(success(game)){stopped=true;break;}
  }
  const last=measure(game);
  return {start,environment,perturbation,success:stopped,ticks:count,final:last,
    saveError, sampleCount:history.length, ...(trace?{history}:{}),game};
}
const trainingStarts=[-4.1,-3.8,-3.5,-3.2];
const cleanTrain=trainingStarts.map(x=>simulate(x,'normal',cleanTeacher,{trace:true}));
const cleanSamples=cleanTrain.flatMap(t=>t.history);
const syntheticStarts=[-4.03,-3.83,-3.53,-3.23];
function makeNoisyTeacher(){
  let held=0;
  return (game,history,tick)=>{
    if(tick%7===0) {
      const intended=cleanTeacher(game);
      const wrong=rng()<.12, pause=rng()<.09;
      held=wrong ? (intended===1?0:1) : pause?0:intended;
    }
    return held;
  };
}
const noisyTrain=syntheticStarts.map(x=>simulate(x,'normal',makeNoisyTeacher(),{trace:true,maximum:LIMIT}));
const noisySamples=noisyTrain.flatMap(t=>t.history);
const filteredSamples=noisyTrain.filter(t=>t.success).flatMap(t=>t.history);
function makeNearest(samples,temporal=false){
  if(samples.length===0) throw Error('no training examples');
  return (game,history)=>{
    const q=feature(game,history);
    const nearest=samples.map((d,i)=>({i,d:
      ((d.x-q.x)/2)**2 + ((d.v-q.v)/3)**2
      +(temporal? ((d.lagV-q.lagV)/4)**2 *.18 + ((d.lagAction-q.lagAction)/2)**2 *.12:0)
    })).sort((a,b)=>a.d-b.d||a.i-b.i).slice(0,7);
    return nearest.reduce((sum,item)=>sum+samples[item.i].action,0)>=4?1:0;
  };
}
const policies={
  fixed_macro:(game,history,tick)=>tick<80?1:0,
  clean_knn:makeNearest(cleanSamples),
  clean_temporal_knn:makeNearest(cleanSamples,true),
  noisy_temporal_knn:makeNearest(noisySamples,true),
  successful_noisy_temporal_knn:filteredSamples.length?makeNearest(filteredSamples,true):()=>0,
  feedback_reference:cleanTeacher,
};
const starts=[-4.05,-3.75,-3.45,-3.15,-2.85,-2.55,-2.25,-2.0];
const perturbations={
  normal:{environment:'normal',perturbation:null},
  one_plank:{environment:'one_plank',perturbation:null},
  two_planks:{environment:'two_planks',perturbation:null},
  sprain:{environment:'sprain',perturbation:null},
  fatigue:{environment:'fatigue',perturbation:null},
  push_forward:{environment:'normal',perturbation:{tick:20,deltaV:1.7}},
  push_backward:{environment:'normal',perturbation:{tick:20,deltaV:-1.7}},
};
const t0=performance.now(),summaries={};
for(const [name,policy] of Object.entries(policies)){
  const rows=[];
  for(const [scenario,setup] of Object.entries(perturbations))
    for(const start of starts){
      const {game,history,...result}=simulate(start,setup.environment,policy,{perturbation:setup.perturbation});
      rows.push({...result,scenario});
    }
  summaries[name]={count:rows.length,successes:rows.filter(r=>r.success).length,
    byScenario:Object.fromEntries(Object.keys(perturbations).map(s=>{const subset=rows.filter(r=>r.scenario===s);return [s,{success:subset.filter(r=>r.success).length,episodes:subset.length}];})),
    rows};
}

// The controller is currently a research-side arbiter, not integrated into live PRSE.
class HabitArbiter{
  constructor(policy){this.policy=policy;this.state='inactive';this.commands=0;}
  activate(game){if(this.state==='manual'||measure(game).speedFactor<.6||measure(game).x>=GOAL+.4) return false;
    this.state='active';return true;}
  step(game,history,tick){if(this.state!=='active')return false;
    const action=this.policy(game,history,tick);
    if (![0,1,-1].includes(action)){this.state='manual';return false;}
    this.commands++;return game.command({type:'Move',direction:action});
  }
  interrupt(game,direction=-1){this.state='manual';return game.command({type:'TakeManualControl'})
      && game.command({type:'Move',direction});}
  snapshot(){return {version:1,state:this.state,commands:this.commands};}
  restore(state){if(state?.version!==1||!['inactive','active','manual'].includes(state.state)
    ||!Number.isSafeInteger(state.commands)||state.commands<0)return false;
    this.state=state.state;this.commands=state.commands;return true;}
}
const interruption=[];
for(const at of [1,20,45,70]){
  const g=gameAt(-4.1),arbiter=new HabitArbiter(policies.clean_temporal_knn);
  assert(arbiter.activate(g));let history=[], count=0;
  for(let tick=0;tick<at;tick++){
    arbiter.step(g,history,tick);history.push({...feature(g,history),action:g.manualDirection});
    g.step();
  }
  const before=arbiter.commands;
  assert(arbiter.interrupt(g,-1),'TakeManualControl failed');
  let noReactivate=true;
  for(let i=0;i<120;i++){
    if(arbiter.step(g,history,at+i))noReactivate=false;
    assert(g.command({type:'Move',direction:-1}));g.step();
    if(g.manualDirection!==-1)noReactivate=false;
  }
  const saved=JSON.parse(JSON.stringify({world:g.snapshot(),controller:arbiter.snapshot()}));
  const restoredGame=new GameCore(),restoredArbiter=new HabitArbiter(policies.clean_temporal_knn);
  assert(restoredGame.restore(saved.world));assert(restoredArbiter.restore(saved.controller));
  let afterResumeNoReactivate=true;
  for(let i=0;i<90;i++){
    if(restoredArbiter.step(restoredGame,[],i))afterResumeNoReactivate=false;
    assert(restoredGame.command({type:'Move',direction:-1}));restoredGame.step();
  }
  assert(restoredArbiter.state==='manual');
  interruption.push({interruptTick:at,controllerCommandsBefore:before,controllerCommandsAfter:arbiter.commands,
    interruptedNoReassert:noReactivate&&before===arbiter.commands,
    resumedNoReassert:afterResumeNoReactivate,controllerStatePersisted:restoredArbiter.state==='manual'});
}
assert(interruption.every(r=>r.interruptedNoReassert&&r.resumedNoReassert));
// Character-state precondition blocks potentially unsafe deployment.
const guard=new HabitArbiter(policies.clean_knn),injured=gameAt(-4,'sprain'); // .64 locomotion, still allowed
const severelyInjured=gameAt(-4,'fatigue');severelyInjured.character.injuries.leftKnee={kind:'sprain',severity:1};
const refused=guard.activate(severelyInjured);assert.equal(refused,false);
// A corrupted output must return control to manual rather than emit invalid physics action.
const broken=new HabitArbiter(()=>NaN),testGame=gameAt(-4);
assert(broken.activate(testGame));assert.equal(broken.step(testGame,[],0),false);assert.equal(broken.state,'manual');
const savedRun=simulate(-3.75,'one_plank',policies.clean_temporal_knn,{saveTick:25});
const output={metadata:{core:'GameCore/Rapier3D',sourceRevision:'ada2611',step:TICK,
  trialDesign:'additional distinct heldout starts; scenarios predeclared in this source',trainingStarts,starts,
  syntheticTeacher:'seven tick hold, deterministic xorshift seed, twelve percent wrong-key and nine percent pause per decision; not human input',
  trainingSamples:{clean:cleanSamples.length,noisy:noisySamples.length,successfulNoisy:filteredSamples.length},
  elapsedWallMilliseconds:Math.round(performance.now()-t0)},
  training: {clean:cleanTrain.map(({game,history,...r})=>r),syntheticNoisy:noisyTrain.map(({game,history,...r})=>r)},
  evaluation:summaries,interruption,preconditionRefused:refused===false,
  invalidPolicyFallback:broken.state==='manual',savedCoreOneEpisode:savedRun.saveError,
  observation:'research-side arbiter, not integrated production controller'};
writeFileSync(new URL('./extended_results.json',import.meta.url),JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({training:output.metadata.trainingSamples,
  scores:Object.fromEntries(Object.entries(summaries).map(([k,v])=>[k,{total:[v.successes,v.count],
    normal:v.byScenario.normal,planks:v.byScenario.two_planks,sprain:v.byScenario.sprain,push:v.byScenario.push_backward}])),
  interruption:interruption.map(r=>({tick:r.interruptTick,pass:r.interruptedNoReassert&&r.resumedNoReassert})),
  preconditionRefused:output.preconditionRefused,invalidPolicyFallback:output.invalidPolicyFallback,
  saveError:savedRun.saveError,runMs:output.metadata.elapsedWallMilliseconds}));
