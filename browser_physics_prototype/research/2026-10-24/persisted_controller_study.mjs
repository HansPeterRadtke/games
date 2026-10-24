import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics,GameCore} from '../../physics-core.js';
await initializePhysics();
const folder=new URL('.',import.meta.url);
const paths={active:new URL('checkpoint_active.json',folder),manual:new URL('checkpoint_manual.json',folder)};
const current = game => ({x:game.player.translation().x,v:game.player.linvel().x});
const target=-1.2;
function newWorld(x){const g=new GameCore();g.player.setTranslation({x,y:1,z:0},true);g.player.setLinvel({x:0,y:0,z:0},true);return g;}
const teacher=g=>{const {x,v}=current(g);return x<target-.08&&x+v*.22<target?1:0;};
function getSamples(){
  const samples=[];
  for(const x of [-4.1,-3.8,-3.5,-3.2]){
    const g=newWorld(x);
    for(let i=0;i<180;i++){
      const p=current(g),a=teacher(g);samples.push({...p,a});
      assert(g.command({type:'Move',direction:a}));g.step();
      const now=current(g);
      if(now.x>=target-.12&&Math.abs(now.v)<.5)break;
    }
  }
  return samples;
}
function model(samples,game){
  const {x,v}=current(game);
  const neighbors=samples.map((p,i)=>({i,score:((p.x-x)/2)**2+((p.v-v)/3)**2}))
    .sort((a,b)=>a.score-b.score||a.i-b.i).slice(0,7);
  return neighbors.reduce((s,r)=>s+samples[r.i].a,0)>=4?1:0;
}
function validate(checkpoint){
  if(checkpoint?.version!==1||!['active','manual'].includes(checkpoint.mode)
    ||!Array.isArray(checkpoint.samples)||checkpoint.samples.length<4||checkpoint.samples.length>1000)return false;
  if(!checkpoint.samples.every(s=>Number.isFinite(s.x)&&Number.isFinite(s.v)&&(s.a===0||s.a===1)))return false;
  if(checkpoint.hash!==createHash('sha256').update(JSON.stringify(checkpoint.samples)).digest('hex'))return false;
  return true;
}
function runFromCheckpoint(c){
  if(!validate(c))throw Error('invalid or corrupted model checkpoint');
  const g=new GameCore();assert(g.restore(c.world));
  let policyCommands=0,manualFrames=0,succeeded=false;
  for(let i=0;i<160;i++){
    if(c.mode==='active'){
      assert(g.command({type:'Move',direction:model(c.samples,g)}));policyCommands++;
    }else{
      assert(g.command({type:'Move',direction:-1}));manualFrames++;
    }
    g.step();
    if(c.mode==='active'&&current(g).x>=target-.12&&Math.abs(current(g).v)<.5){succeeded=true;break;}
    if(c.mode==='manual')assert.equal(g.manualDirection,-1);
  }
  return {mode:c.mode,policyCommands,manualFrames,succeeded,final:current(g),worldTime:g.time,controllerEnabled:c.mode==='active'};
}
if(process.argv[2]==='prepare'){
  const samples=getSamples();
  for(const [mode,path] of Object.entries(paths)){
    const g=newWorld(-3.72);let ticks=0;
    for(;ticks<20;ticks++){assert(g.command({type:'Move',direction:model(samples,g)}));g.step();}
    if(mode==='manual'){
      assert(g.command({type:'TakeManualControl'}));assert(g.command({type:'Move',direction:-1}));g.step();
    }
    const checkpoint={version:1,mode,world:g.snapshot(),samples,
      hash:createHash('sha256').update(JSON.stringify(samples)).digest('hex'),
      info:{trainingStarts:[-4.1,-3.8,-3.5,-3.2],tick:ticks,hasRealPlayerData:false}};
    assert(validate(checkpoint));writeFileSync(path,JSON.stringify(checkpoint,null,2)+'\n');
  }
  console.log(JSON.stringify({prepared:true,samples:samples.length,fixtures:Object.keys(paths)}));
}else if(process.argv[2]==='resume'){
  const data=Object.fromEntries(Object.entries(paths).map(([kind,path])=>[kind,JSON.parse(readFileSync(path,'utf8'))]));
  const corrupted=structuredClone(data.active);corrupted.samples[0].v=NaN;
  assert.equal(validate(corrupted),false);
  const reports={};
  for(const [kind,c] of Object.entries(data)){
    const first=runFromCheckpoint(c),second=runFromCheckpoint(c);
    assert.deepEqual(first,second,'loaded checkpoint is not deterministic from same starting state');
    if(kind==='active')assert(first.succeeded&&first.policyCommands>0);
    else assert(first.policyCommands===0&&first.manualFrames===160);
    reports[kind]=first;
  }
  writeFileSync(new URL('persistence_results.json',folder),JSON.stringify({reports,validationCorruptRejected:true},null,2)+'\n');
  console.log(JSON.stringify({freshProcessResume:true,reports,corruptionRejected:true}));
}else throw Error('Usage: node persisted_controller_study.mjs prepare|resume');
