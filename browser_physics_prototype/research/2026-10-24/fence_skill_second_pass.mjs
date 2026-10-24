import assert from 'node:assert/strict';
import fs from 'node:fs';
import {initializePhysics,GameCore,SETTINGS} from '../../physics-core.js';

await initializePhysics();
// Preserve consumed/raw negative research fixtures: never overwrite an existing result file.
// To reproduce, pass --output=fresh_replay_name.json within this owned research directory.
function outputPath(defaultName){
 const arg=process.argv.find(a=>a.startsWith('--output='));
 const name=arg?arg.slice('--output='.length):defaultName;
 if(!/^[a-zA-Z][a-zA-Z0-9_.-]*\.json$/.test(name))throw Error('Unsafe output name');
 return new URL(name,import.meta.url);
}

const root=new URL('./',import.meta.url);
const MAX_TICKS=260;
const goalX=SETTINGS.fenceX+1.35;
function newWorld(startX,perturb='none'){
  const g=new GameCore();
  g.player.setTranslation({x:startX,y:1,z:0},true);
  g.player.setLinvel({x:0,y:0,z:0},true);
  if(perturb==='carry_2') for(let i=0;i<2;i++)assert(g.character.collectPlank());
  if(perturb==='knee_sprain')g.character.injuries.leftKnee={kind:'sprain',severity:.8};
  return g;
}
function observation(g){
 const p=g.player.translation(),v=g.player.linvel();
 return {x:p.x,y:p.y,vx:v.x,vy:v.y,grounded:g.grounded(),tick:g.stepCount};
}
function teacher(g){
 const s=observation(g);
 return {move:s.x<goalX?1:0, jump:s.grounded && s.x>SETTINGS.fenceX-1.25&&s.x<SETTINGS.fenceX-1.00};
}
function runEpisode(policy,start,perturb='none',extra={}){
 const g=newWorld(start,perturb);const trace=[];
 let maxY=-Infinity,firstJumpTick=null,completed=false,interrupted=false,saveDelta=null;
 for(let tick=0;tick<MAX_TICKS;tick++){
  const o=observation(g),a=policy(g,trace,tick);
  assert([0,1,-1].includes(a.move)&&typeof a.jump==='boolean','invalid macro output');
  assert(g.command({type:'Move',direction:a.move}));
  if(a.jump){assert(g.command({type:'Jump'}));if(firstJumpTick===null)firstJumpTick=tick;}
  if(extra.impulseTick===tick){g.player.applyImpulse({x:g.player.mass()*(extra.dv||-1),y:0,z:0},true);}
  trace.push({...o,action:a});
  g.step();maxY=Math.max(maxY,g.player.translation().y);
  if(g.player.translation().x>goalX&&g.grounded()&&Math.abs(g.player.linvel().x)<.3){completed=true;break;}
 }
 const last=observation(g);
 return {start,perturb,successful:completed,firstJumpTick,maxY,last,trace};
}
const startsTraining=[1.6,1.9,2.2,2.5];const startsHeld=[1.75,1.85,2.05,2.15,2.35,2.45,2.65,2.75];
const train=startsTraining.map(s=>runEpisode(teacher,s));
const positive=train.flatMap(t=>t.trace.filter(x=>x.action.jump&&x.grounded));
const negatives=train.flatMap(t=>t.trace.filter(x=>!x.action.jump&&x.grounded));
const dataset=train.flatMap(t=>t.trace);
const status={trained:train.map(t=>({start:t.start,success:t.successful,firstJumpTick:t.firstJumpTick,maxY:t.maxY,finalX:t.last.x})),
  positives:positive.length,negatives:negatives.length};
function distance(a,b){return ((a.x-b.x)/2)**2+((a.vx-b.vx)/3)**2+(a.grounded===b.grounded?0:.1);}
function nearestMove(g,trace){
 const q=observation(g);
 const seven=dataset.map((r,i)=>({i,d:distance(r,q)})).sort((a,b)=>a.d-b.d||a.i-b.i).slice(0,7);
 return seven.filter(r=>dataset[r.i].action.move>0).length>=4?1:0;
}
const positivesOnly=positive.filter(t=>t.action.jump&&t.grounded);
const bounds={low:positivesOnly.length?Math.min(...positivesOnly.map(p=>p.x)):null,
 high:positivesOnly.length?Math.max(...positivesOnly.map(p=>p.x)):null};
const jumpLearner=g=>{const q=observation(g);return q.grounded&&positivesOnly.length>0
 &&q.x>=bounds.low-.1&&q.x<=bounds.high+.1;};
const majorityJump=g=>{
 const q=observation(g);
 const near=dataset.map((r,i)=>({i,d:distance(r,q)})).sort((a,b)=>a.d-b.d||a.i-b.i).slice(0,7);
 return q.grounded&&near.filter(z=>dataset[z.i].action.jump).length>=4;
};
const medianJump=(()=>{const times=train.filter(x=>x.firstJumpTick!==null).map(x=>x.firstJumpTick).sort((a,b)=>a-b);return times.length?times[Math.floor(times.length/2)]:120;})();
const policies={
 feedback_teacher:teacher,
 timed_macro:(g,history,tick)=>({move:1,jump:tick===medianJump}),
 kNN_two_head:g=>({move:nearestMove(g),jump:majorityJump(g)}),
 positive_class_guard:g=>({move:nearestMove(g),jump:jumpLearner(g)})
};
const scenarios={
 normal:{perturb:'none'},
 carry_2:{perturb:'carry_2'},
 knee_sprain:{perturb:'knee_sprain'},
 mid_push:{perturb:'none',impulseTick:55,dv:-1.2}
};
const results={meta:{core:'GameCore Rapier 3D',realAxis:'x/y physical fence, z intentionally locked by core',
 trainingStarts:startsTraining,heldoutStarts:startsHeld,goalX,ticks:MAX_TICKS,
 firstPriorTrialNotReused:true,manualTeacher:'scripted Move and Jump at physical position, NOT human demonstrations'},
 training:status,learnedJumpBounds:bounds,medianJumpTick:medianJump,evaluation:{}};
for(const [name,policy] of Object.entries(policies)){
 const rows=[];
 for(const [scenario,s] of Object.entries(scenarios)){
  for(const start of startsHeld){
   const {trace,...summary}=runEpisode(policy,start,s.perturb,s);
   rows.push({scenario,...summary});
  }
 }
 results.evaluation[name]={episodes:rows.length,succeeded:rows.filter(r=>r.successful).length,byScenario:Object.fromEntries(Object.keys(scenarios).map(s=>[s,rows.filter(r=>r.scenario===s&&r.successful).length])),rows};
}
fs.writeFileSync(outputPath('fence_skill_results.json'),JSON.stringify(results,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({training:status.trained,jumpPositiveSamples:positive.length,jumpBounds:bounds,
 scores:Object.fromEntries(Object.entries(results.evaluation).map(([k,v])=>[k,{success:v.succeeded,n:v.episodes,byScenario:v.byScenario}]))}));
