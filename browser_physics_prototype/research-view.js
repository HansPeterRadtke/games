// Optional browser presentation of authoritative PRSE state. No LLM calls and no mutations.
import {narrateWorld} from './narrative-view.js';
export function observeResearch(core){
 const scene=['shelter-setting','shelter-bench','shelter-candle','shelter-jug','shelter-note'];
 const records=scene.map(id=>{const e=core.semantic.entity(id);if(!e)return null;const physical=core.worldBridge.active.get(id);return {name:e.name,kind:e.kind,condition:e.state?.condition||'unknown',lit:e.kind==='candle'?!!e.state?.lit:undefined,water:e.kind==='jug'?e.state.water:undefined,materialized:!!physical,position:e.materialized&&physical?physical.translation():{x:e.x,y:e.y,z:e.z},description:e.description};}).filter(Boolean);
 const fire=core.consequences.pending.length,latest=core.events.filter(e=>e.entityId?.startsWith('shelter-')||e.type.startsWith('paper_')||e.type.startsWith('bench_')||e.type==='candle_lit'||e.type==='note_ignited').slice(-10);
 const here=Math.abs(core.player.translation().x-37)<4;
 const candle=records.find(o=>o.kind==='candle');const note=records.find(o=>o.kind==='note');const bench=records.find(o=>o.kind==='bench');
 const explain=`${here?'Shelter in perception: physical 3D objects are active.':'Shelter outside perception: durable semantic state remains; distant 3D simulation is released.'}\nCandle: ${candle?.lit?'lit':'unlit'}. Note: ${note?.condition||'unknown'}. Bench: ${bench?.condition||'unknown'}. ${fire?`${fire} future causal transitions remain scheduled.`:'No delayed fire transitions scheduled.'}\nLighting the candle alone changes its lit state; combustion requires a separate ignition action in this prototype. No LLM observes the current game automatically.`;
 return {explain,text:here?narrateWorld(core.state()):'The shelter is outside your perception; its state is intentionally not narrated as current knowledge.',detail:{time:core.time,here,scene:records,upcomingEvents:fire,recentEvents:latest.map(e=>({type:e.type,message:e.message,time:e.time,visibility:e.visibility}))}};
}
