// Text presentation/input adapter for the exact same 3D simulation.
// No semantic command is allowed to bypass core movement, collision or inventory.
import {SETTINGS}from './physics-core.js';
const finite=(n,a,b)=>Number.isFinite(n)&&n>=a&&n<=b;
export class TextAdapter {
 constructor(core){this.core=core;}
 describe(){const s=this.core.state(),entities=s.visibleEntities.filter(e=>!e.state?.collected),p=s.player;
  const visible=entities.length?`Nearby: ${entities.map(e=>e.name).join(', ')}.`:'No nearby objects.';
  const near=s.nearby?`You can: ${s.nearby.label.toLowerCase()}.`:'';
  return `You are at x ${p.x.toFixed(1)}, y ${p.y.toFixed(1)}, z ${p.z.toFixed(1)}. ${s.grounded?'On solid ground.':'In the air.'} ${visible} ${near} Carrying ${s.character.inventory.plank} timber planks. ${s.character.bridgeRepaired?'The footbridge is repaired.':'The stream crossing is missing its deck.'}`;}
 run(phrase){if(typeof phrase!=='string'||phrase.length>120)return {ok:false,output:'Command is invalid.'};const command=phrase.trim().toLowerCase();if(!command)return {ok:false,output:'Enter a command.'};
  const before=this.core.events.length;let ok=true;
  if(['look','describe','where am i'].includes(command))return {ok:true,output:this.describe()};
  const movement=command.match(/^(left|right|west|east)\s+(\d+(?:\.\d+)?)$/);
  const wait=command.match(/^wait\s+(\d+(?:\.\d+)?)$/);
  if(movement||wait){const sec=Number((movement||wait)[2]||wait?.[1]);if(!finite(sec,0,30))return {ok:false,output:'Duration must be between zero and thirty seconds.'};
   if(movement)this.core.command({type:'Move',direction:['left','west'].includes(movement[1])?-1:1});
   for(let t=0;t<Math.ceil(sec/SETTINGS.step);t++)this.core.step();
   if(movement)this.core.command({type:'Move',direction:0});
   return {ok:true,output:this.describe()};}
  if(['jump over fence','cross fence','go over the fence'].includes(command)){ok=this.core.command({type:'Goal',intent:'crossFence'});if(ok){for(let t=0;t<30/SETTINGS.step&&this.core.goal;t++)this.core.step();ok=this.core.events.slice(before).some(e=>e.type==='goal_success');}}
  else if(command==='jump'){ok=this.core.command({type:'Jump'});this.core.step();}
  else if(['take','interact','measure','repair bridge','talk','drink'].includes(command))ok=this.core.command({type:'Interact'});
  else if(['tune','try mechanism'].includes(command))ok=this.core.command({type:'Experiment'});
  else if(command==='cancel')ok=this.core.command({type:'CancelGoal'});
  else return {ok:false,output:'Unknown command. Try: look, right 2, wait 1, interact, tune, jump over fence.'};
  const events=this.core.events.slice(before);const report=events.length?events.map(e=>e.message).join(' '):'';
  return {ok,output:`${report}${report?' ':''}${this.describe()}`};
 }
}
