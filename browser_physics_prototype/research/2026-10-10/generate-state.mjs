// Recreate the controlled experiment using exactly the deployed GameCore.
// Does not inspect a user's browser session or contact an LLM.
import {initializePhysics,GameCore} from '../../physics-core.js';
await initializePhysics();const game=new GameCore();const step=n=>{for(let i=0;i<n;i++)game.step();};
const ids=['shelter-setting','shelter-bench','shelter-candle','shelter-jug','shelter-note'];
const capture=(label)=>({label,objects:ids.map(id=>{const entity=game.semantic.entity(id),body=game.worldBridge.active.get(id);return {id,kind:entity.kind,description:entity.description,condition:entity.state?.condition,lit:entity.state?.lit,wet:entity.state?.wet,water:entity.state?.water,size:entity.size,position:body?.translation()||{x:entity.x,y:entity.y,z:entity.z},support:entity.state?.supportId};}),worldTime:game.time,visible:game.state().visibleEntities.filter(e=>ids.includes(e.id)).map(e=>e.id)});
game.player.setTranslation({x:37,y:.86,z:0},true);step(70);const original=capture('unlit');
game.command({type:'Interact',targetId:'shelter-candle',verb:'light'});step(40);const lit=capture('lit but not ignited');
game.command({type:'Interact',targetId:'shelter-note',verb:'ignite'});step(2500);const burned=capture('after paper fire');
const kept=new Set(['candle_lit','note_ignited','paper_smolders','paper_burning','bench_smoldering','paper_ashes','bench_scorching','bench_scorched','shelter_smoky']);const events=game.events.filter(e=>kept.has(e.type)).map(e=>({type:e.type,message:e.message,time:e.time,visibility:e.visibility}));
console.log(JSON.stringify({original,lit,burned,events,queued:game.consequences.pending.length},null,2));
