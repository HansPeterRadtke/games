import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics,GameCore} from '../../physics-core.js';

await initializePhysics();
// Preserve consumed/raw negative research fixtures: never overwrite an existing result file.
// To reproduce, pass --output=fresh_replay_name.json within this owned research directory.
function outputPath(defaultName){
 const arg=process.argv.find(a=>a.startsWith('--output='));
 const name=arg?arg.slice('--output='.length):defaultName;
 if(!/^[a-zA-Z][a-zA-Z0-9_.-]*\.json$/.test(name))throw Error('Unsafe output name');
 return new URL(name,import.meta.url);
}

const previous=JSON.parse(readFileSync(new URL('./fence_skill_results.json',import.meta.url)));
const bounds=previous.learnedJumpBounds,goal=previous.meta.goalX;
assert(bounds.low<bounds.high&&bounds.low>3&&bounds.high<5&&goal>6);
function gameAt(start){
 const g=new GameCore();
 g.player.setTranslation({x:start,y:1,z:0},true);
 g.player.setLinvel({x:0,y:0,z:0},true);
 return g;
}
const sense=g=>({x:g.player.translation().x,v:g.player.linvel().x,grounded:g.grounded(),y:g.player.translation().y});
const policy=s=>({move:s.x<goal?1:0,jump:s.grounded&&s.x>=bounds.low-.1&&s.x<=bounds.high+.1});
function run({start,lag=0,delay=0,manualAt=null,guard=true,perturbAt=null,saveAt=null}){
 let g=gameAt(start),queue=[],frames=[],epoch=0,owner='auto',count=0;
 const events={staleApplied:0,postInterruptAutoApplied:0,jumpsRequested:0,appliedMoves:0,saveRestored:false};
 let maxY=-Infinity,done=false,manualMaintained=true;
 for(let tick=0;tick<250;tick++){
  if(perturbAt===tick)g.player.applyImpulse({x:-g.player.mass()*1.3,y:0,z:0},true);
  const obs=sense(g);frames.push(obs);
  if(manualAt===tick){owner='manual';epoch++;assert(g.command({type:'TakeManualControl'}));}
  if(owner==='auto'){
   const prior=frames[Math.max(0,frames.length-1-lag)];
   const a=policy(prior);queue.push({due:tick+delay,epoch,action:a});
  }else{
   assert(g.command({type:'Move',direction:-1}));
  }
  for(const p of queue.filter(p=>p.due<=tick)){
   if(!guard||p.epoch===epoch){
    if(owner==='manual')events.postInterruptAutoApplied++;
    assert(g.command({type:'Move',direction:p.action.move}));events.appliedMoves++;
    if(p.action.jump){assert(g.command({type:'Jump'}));events.jumpsRequested++;}
   }else events.staleApplied++;
  }
  queue=queue.filter(p=>p.due>tick);
  if(owner==='manual'&&g.manualDirection!==-1)manualMaintained=false;
  g.step();maxY=Math.max(maxY,g.player.translation().y);count++;
  if(tick===saveAt){
   const snap=JSON.parse(JSON.stringify(g.snapshot()));
   const restored=new GameCore();assert(restored.restore(snap));events.saveRestored=true;
   const dx=Math.abs(restored.player.translation().x-g.player.translation().x),dv=Math.abs(restored.player.linvel().x-g.player.linvel().x);
   events.savePositionError=dx;events.saveVelocityError=dv;g=restored;
   queue=JSON.parse(JSON.stringify(queue));frames=JSON.parse(JSON.stringify(frames)); // research controller persistence
  }
  if(manualAt===null&&g.player.translation().x>goal&&g.grounded()&&Math.abs(g.player.linvel().x)<.3){done=true;break;}
 }
 const final=sense(g);
 return {start,lag,delay,guard,manualAt,perturbAt,saveAt,success:done,ticks:count,maxY,
    final,events,manualMaintained};
}
const starts=[1.7,1.8,2.1,2.3,2.6];
const configs=[
 {label:'instant',lag:0,delay:0},
 {label:'sensor_lag_6',lag:6,delay:0},
 {label:'sensor_lag_12',lag:12,delay:0},
 {label:'delivery_delay_6',lag:0,delay:6},
 {label:'combined_6',lag:6,delay:6},
 {label:'combined_12',lag:12,delay:12},
];
const trials={};
for(const c of configs){
 const rows=starts.map(start=>run({start,...c}));
 trials[c.label]={success:rows.filter(r=>r.success).length,n:rows.length,jumpEvents:rows.map(r=>r.events.jumpsRequested),rows};
}
const overrides=[];
for(const at of [30,48,58]){
 for(const delay of [0,6,12]){
  for(const guard of [true,false]){
   const x=run({start:1.8,lag:0,delay,manualAt:at,guard});
   overrides.push({tick:at,delay,guard,manualMaintained:x.manualMaintained,afterManualAutoCommands:x.events.postInterruptAutoApplied,
     rejectedQueueEntries:x.events.staleApplied});
  }
 }
}
// Save during maneuver; persist GameCore and experiment controller queue state.
const restores=[run({start:2.1,delay:6,lag:0,saveAt:52}),
 run({start:2.1,delay:12,lag:12,saveAt:52})];
assert(trials.instant.success===starts.length);
assert(overrides.filter(x=>x.guard).every(x=>x.manualMaintained&&x.afterManualAutoCommands===0));
assert(restores.every(x=>x.events.saveRestored&&x.events.savePositionError<.001));
const result={
 provenance:{core:'GameCore/Rapier, same existing fence',trainedBoundsSource:'fence_skill_results.json',
        noHumanTeacher:true,kind:'exploratory follow-up after fence holdouts; not another untouched final holdout'},
 trials,overrides,restores};
writeFileSync(outputPath('fence_latency_results.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({scores:Object.fromEntries(Object.entries(trials).map(([k,v])=>[k,[v.success,v.n]])),
  unsafeInterruption:overrides.filter(r=>!r.guard&&r.afterManualAutoCommands>0).length,
  guardedInterruptionPassed:overrides.filter(r=>r.guard).length,
  saved:restores.map(x=>({success:x.success,positionError:x.events.savePositionError}))}));
