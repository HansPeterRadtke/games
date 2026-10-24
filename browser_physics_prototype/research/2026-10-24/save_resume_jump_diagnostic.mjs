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

const meta=JSON.parse(readFileSync(new URL('fence_skill_results.json',import.meta.url)));
const {low,high}=meta.learnedJumpBounds;
const goal=meta.meta.goalX;
function go(mode){
 let g=new GameCore();g.player.setTranslation({x:2.1,y:1,z:0},true);g.player.setLinvel({x:0,y:0,z:0},true);
 let history=[],queue=[],trace=[],jumpTicks=[],guardBefore=null,guardAfter=null;
 for(let tick=0;tick<250;tick++){
  const p=g.player.translation(),v=g.player.linvel();
  const obs={x:p.x,v:v.x,grounded:g.grounded(),y:p.y};
  history.push(obs);
  const cmd={move:obs.x<goal?1:0,jump:obs.grounded&&obs.x>=low-.1&&obs.x<=high+.1};
  queue.push({due:tick+6,cmd});
  for(const item of queue.filter(x=>x.due<=tick)){
   assert(g.command({type:'Move',direction:item.cmd.move}));
   if(item.cmd.jump)assert(g.command({type:'Jump'}));
  }
  queue=queue.filter(x=>x.due>tick);
  const jumpBefore=g.events.filter(e=>e.type==='jump').length;
  g.step();
  if(g.events.filter(e=>e.type==='jump').length>jumpBefore)jumpTicks.push(tick);
  if(tick===52 && mode!=='original'){
   const previous={nextJumpAt:g.nextJumpAt,manualDirection:g.manualDirection,jumpRequested:g.jumpRequested,previousGrounded:g.previousGrounded};
   guardBefore=previous;
   const snapshot=JSON.parse(JSON.stringify(g.snapshot()));
   const copy=new GameCore();assert(copy.restore(snapshot));
   guardAfter={nextJumpAt:copy.nextJumpAt,manualDirection:copy.manualDirection,jumpRequested:copy.jumpRequested,previousGrounded:copy.previousGrounded};
   if(mode==='preserve_jump_guard'||mode==='preserve_both')copy.nextJumpAt=previous.nextJumpAt;
   if(mode==='preserve_input'||mode==='preserve_both')copy.manualDirection=previous.manualDirection;
   if(mode==='preserve_both'){copy.previousGrounded=previous.previousGrounded;copy.jumpRequested=previous.jumpRequested;}
   g=copy;
  }
  trace.push({tick,x:g.player.translation().x,y:g.player.translation().y,vx:g.player.linvel().x,vy:g.player.linvel().y,grounded:g.grounded()});
  if(g.player.translation().x>goal && g.grounded() && Math.abs(g.player.linvel().x)<.3)
   return {mode,success:true,finalTick:tick,jumpTicks,guardBefore,guardAfter,trace};
 }
 return {mode,success:false,finalTick:249,jumpTicks,guardBefore,guardAfter,trace};
}
const modes=['original','standard_restore','preserve_jump_guard','preserve_input','preserve_both'];
const runs=Object.fromEntries(modes.map(k=>[k,go(k)]));
const base=runs.original.trace;
for(const r of Object.values(runs)){
 const n=Math.min(base.length,r.trace.length);
 let firstPositionDiff=null;for(let i=0;i<n;i++){
  if(Math.abs(base[i].x-r.trace[i].x)>1e-4 || Math.abs(base[i].y-r.trace[i].y)>1e-4){firstPositionDiff=i;break;}
 }
 r.firstPositionDivergenceTick=firstPositionDiff===null?null:base[firstPositionDiff].tick;
 delete r.trace;
}
assert(runs.original.success,'baseline failed; no diagnostic');
const outputName=process.argv.includes('--patched')?'save_resume_jump_patched_results.json':'save_resume_jump_diagnostic_results.json';
writeFileSync(outputPath(outputName),JSON.stringify(runs,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(runs));
