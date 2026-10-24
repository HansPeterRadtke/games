import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics,GameCore} from '../../physics-core.js';
import {resonanceAt,measureResonance} from '../../hidden-mechanism.js';
await initializePhysics();
const goal=-1.2,dt=1/60;
function reset(x=-4.1){const g=new GameCore();g.player.setTranslation({x,y:1,z:0},true);g.player.setLinvel({x:0,y:0,z:0},true);return g;}
function expert(g){const x=g.player.translation().x, v=g.player.linvel().x;return x<goal-.08&&x+v*.22<goal?1:0;}
function rollout(control,start,interruptAt=null,saveAt=null){let g=reset(start),ticks=0,trace=[],snapOK=null,interruptOK=null;for(;ticks<330;ticks++){const x=g.player.translation().x,v=g.player.linvel().x,a=control(g,ticks);assert(g.command({type:'Move',direction:a}));trace.push({tick:ticks,time:g.time,x,v,action:a});g.step();if(ticks===saveAt){const snap=g.snapshot(),copy=new GameCore();snapOK=copy.restore(snap)&&Math.abs(copy.player.translation().x-g.player.translation().x)<.002;g=copy;}if(ticks===interruptAt){g.command({type:'Move',direction:-1});g.step();interruptOK=g.manualDirection===-1&&g.goal===null;break;}if(x>=goal-.12&&Math.abs(v)<.45)break;}let x=g.player.translation().x;return {success:interruptAt===null&&x>=goal-.12&&x<=goal+.4&&Math.abs(g.player.linvel().x)<.5,ticks,x,interruptOK,snapOK,trace};}
const trainingStarts=[-4.1,-3.8,-3.5,-3.2];let train=trainingStarts.map(s=>rollout(expert,s));const dataset=train.flatMap(t=>t.trace);
// Tiny non-neural 2-feature kNN imitation; normalized distances keep speed relevant.
function clone(g){const x=g.player.translation().x,v=g.player.linvel().x;let near=dataset.map(p=>({d:((p.x-x)/2)**2+((p.v-v)/3)**2,a:p.action})).sort((a,b)=>a.d-b.d).slice(0,7);return near.reduce((s,p)=>s+p.a,0)>=4?1:0;}
const macro=(g,t)=>t<80?1:0;
const starts=[-4,-3.9,-3.7,-3.6,-3.4,-3.3,-3.1,-2.9];
const results={metadata:{core:'GameCore/Rapier 3D',dt,goal,trainingStarts,starts,seed:'deterministic fixtures, no randomness',trainedSamples:dataset.length},trained:train.map(({trace,...r})=>r),heldout:{}};
for(const [name,policy] of Object.entries({macro,clone,feedback:expert})){results.heldout[name]=starts.map(s=>{let r=rollout(policy,s,null,15);let {trace,...summary}=r;return {start:s,...summary};});results.heldout[name+'_interrupted']=starts.map(s=>{let r=rollout(policy,s,45);let {trace,...summary}=r;return {start:s,...summary};});}
// A hidden rule is fair to discover only if observations distinguish alternatives within a reasonable horizon.
const mechanisms={existing_resonance:t=>resonanceAt(t),simple_periodic:t=>Math.sin(2*Math.PI*t/8),two_frequency:t=>.6*Math.sin(2*Math.PI*t/8)+.4*Math.sin(2*Math.PI*t/3),constant:t=>.7};
results.hidden={};for(const [name,f] of Object.entries(mechanisms)){let successes=0,attempts=0,measurements=[];for(let i=0;i<240;i++){const t=i*.25,v=f(t);if(i%8===0)measurements.push({time:t,intensity:Math.round(v*100)});successes+=v>=.66?1:0;attempts++;}results.hidden[name]={successes,attempts,opportunityRate:successes/attempts,measurements};}
results.hidden.existing_sample=measureResonance(4);
assert(dataset.length>30);assert(results.heldout.feedback.length===8);assert(results.heldout.clone_interrupted.every(r=>r.interruptOK));
writeFileSync(new URL('./results.json',import.meta.url),JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify({trainedSamples:dataset.length,heldout:Object.fromEntries(Object.entries(results.heldout).map(([k,rs])=>[k,{success:rs.filter(r=>r.success).length,n:rs.length,interrupt:rs.filter(r=>r.interruptOK).length,saved:rs.filter(r=>r.snapOK).length}])),hidden:Object.fromEntries(Object.entries(results.hidden).filter(([k])=>k!=='existing_sample').map(([k,v])=>[k,v.opportunityRate]))}));
