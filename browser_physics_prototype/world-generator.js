import {storyRegionBank} from './generated/story-region-bank.js';
import {chooseLiteraryScene,sceneToEntities} from './llm-region-adapter.js';
import {validatedLocalProposal}from './llm-proposal-sample.js';
// Safe generated-world data boundary. Runtime code from an LLM is never executed.
import {createWorldSeed} from './world-seed.js';
import {validatedShelterScene} from './scene-translation.js';
const ALLOWED_KINDS=new Set(['tree','resonator','wanderer','spring','workbench','bridge','destination','plank','rock','grove','shelter','bench','candle','jug','note']);
const ALLOWED_COLLIDERS=new Set(['none','cuboid','capsule']);
const ALLOWED_ACTIONS={bench:new Set(['inspect']),candle:new Set(['light','extinguish','tip','inspect']),jug:new Set(['pour','inspect']),note:new Set(['read','ignite'])};
const validNumber=(n,min,max)=>typeof n==='number'&&Number.isFinite(n)&&n>=min&&n<=max;
export function validateWorldProposal(entities,existingIds=new Set()){
 if(!Array.isArray(entities)||entities.length>60)return {ok:false,error:'Invalid entity array or excessive count'};
 const ids=new Set(existingIds);
 for(const e of entities){if(!e||typeof e.id!=='string'||!/^[a-z][a-z0-9-]{2,79}$/.test(e.id)||ids.has(e.id))return {ok:false,error:'Invalid or duplicate entity identity'};ids.add(e.id);
  if(!ALLOWED_KINDS.has(e.kind)||typeof e.name!=='string'||e.name.length>90||typeof e.description!=='string'||e.description.length>4000||typeof e.source!=='string'||e.source.length>200)return {ok:false,error:'Invalid semantic content'};
  for(const k of ['x','y','z'])if(!validNumber(e[k],-1000,1000))return {ok:false,error:'Invalid spatial coordinates'};
  if(!e.physical||!['fixed','dynamic'].includes(e.physical.body)||!ALLOWED_COLLIDERS.has(e.physical.collider))return {ok:false,error:'Unknown physics primitive'};
  if(e.physical.collider==='cuboid'&&(!Array.isArray(e.physical.halfExtents)||e.physical.halfExtents.length!==3||!e.physical.halfExtents.every(n=>validNumber(n,.001,20))))return {ok:false,error:'Invalid cuboid dimensions'};
  if(e.physical.collider==='capsule'&&(!validNumber(e.physical.halfHeight,.001,20)||!validNumber(e.physical.radius,.001,20)))return {ok:false,error:'Invalid capsule dimensions'};
  if(e.physical.mass!==undefined&&!validNumber(e.physical.mass,.01,200))return {ok:false,error:'Invalid physical mass'};
  if(e.state===null||typeof e.state!=='object'||Array.isArray(e.state))return {ok:false,error:'Invalid object state'};
  if(e.affordances!==undefined){if(!Array.isArray(e.affordances)||e.affordances.length>8)return{ok:false,error:'Invalid action list'};const seenVerbs=new Set();for(const a of e.affordances){if(!a||!ALLOWED_ACTIONS[e.kind]?.has(a.verb)||typeof a.label!=='string'||a.label.length<1||a.label.length>70||seenVerbs.has(a.verb)||a.origin!=='llm-validated'||typeof a.promptHash!=='string'||!/^[a-f0-9]{12}$/.test(a.promptHash))return{ok:false,error:'Untrusted generated action'};seenVerbs.add(a.verb);}}
 }
 return {ok:true,count:entities.length};
}
export function parseWorldProposal(json,ids){if(typeof json!=='string'||json.length>200000)return {ok:false,error:'Invalid proposal size'};
 let parsed;try{parsed=JSON.parse(json);}catch{return {ok:false,error:'Invalid JSON'}};
 const entities=Array.isArray(parsed)?parsed:parsed?.entities;
 const validation=validateWorldProposal(entities,ids);return validation.ok?{ok:true,entities}:{ok:false,error:validation.error};}
const makeEntity=(id,kind,name,x,y,description,physics={body:'fixed',collider:'none'})=>({
 id,kind,name,description,source:'procedural-seed-v1',x,y,z:0,home:x,range:0,speed:0,phase:0,vx:0,vy:0,vz:0,revision:0,materialized:false,q:{x:0,y:0,z:0,w:1},angular:{x:0,y:0,z:0},state:{},physical:physics
});
function hash(n){let h=(n^0x9e3779b9)>>>0;h=Math.imul(h^(h>>>16),0x85ebca6b);h=Math.imul(h^(h>>>13),0xc2b2ae35);return (h^(h>>>16))>>>0;}
export function proposeRegion(index,flags={}){if(!Number.isInteger(index)||index<0||index>=8)throw Error('Region outside bounded demo world');
 const literary=chooseLiteraryScene(storyRegionBank.scenes,index,flags);
 if(literary){const result=sceneToEntities(literary);if(!result.ok)throw Error(`Invalid pre-generated LLM region: ${result.error}`);return result.entities;}
 const start=29+index*12,choice=hash(index)%3;
 const kind=index===0?validatedLocalProposal.kind:['tree','rock','spring'][choice];
 const text=index===0?validatedLocalProposal.description:{tree:'A broad old tree grows beside the path. The next valley remains unexplored.',rock:'A large solitary boulder marks a bend in the path.',spring:'Clear water runs from a rocky bank into the valley.'}[kind];
 const collider=kind==='rock'?{body:'fixed',collider:'cuboid',halfExtents:[.28,.25,.65]}:{body:'fixed',collider:'none'};
 const items=[makeEntity(`region-${index}-landmark`,kind,index===0?validatedLocalProposal.name:kind==='tree'?'Valley tree':kind==='spring'?'Hidden spring':'Standing stone',start+2.1,kind==='tree'?1.3:.4,text,collider)];if(index===0)items[0].source='local-llm-proposal:qwen3.8-27b:2026-10-10';
 if(index%2===0)items.push(makeEntity(`region-${index}-marker`,'destination','Old trail marker',start+6,.4,'An old trail marker bears a half-erased carving. Someone traveled this way before.'));
 if(index===0)items.push(...validatedShelterScene.entities.map(e=>structuredClone(e)));
 return items;
}
export class WorldStreamer {
 constructor(){this.generated=[];this.maxRegions=8;}
 update(playerX,direction,semantic,flags={}){if(!Number.isFinite(playerX)||![-1,1].includes(direction))return 0;
  const ahead=playerX+(direction>0?17:8);if(ahead<29)return 0;
  const target=Math.floor((ahead-29)/12),existing=new Set(semantic.entities.map(e=>e.id));let added=0;
  for(let region=0;region<=Math.min(target,this.maxRegions-1);region++){
   if(this.generated.includes(region))continue;
   const proposal=proposeRegion(region,flags),check=validateWorldProposal(proposal,existing);if(!check.ok)throw Error(check.error);
   semantic.entities.push(...proposal);this.generated.push(region);for(const e of proposal)existing.add(e.id);added+=proposal.length;
  }
  return added;
 }
 snapshot(){return {version:1,generated:[...this.generated]};}
 restore(snapshot,semantic,{upgradePreShelter=false}={}){
  if(!snapshot||snapshot.version!==1||!Array.isArray(snapshot.generated)||snapshot.generated.length>this.maxRegions||!snapshot.generated.every(n=>Number.isInteger(n)&&n>=0&&n<this.maxRegions)||new Set(snapshot.generated).size!==snapshot.generated.length)return false;
  // Never silently re-generate altered content in new save formats.
  for(const n of snapshot.generated)if(!semantic.entity(`region-${n}-landmark`))return false;
  if(upgradePreShelter&&snapshot.generated.includes(0)){
   // Compatibility with version-4 saves created before the generated shelter was introduced.
   for(const e of validatedShelterScene.entities)if(!semantic.entity(e.id))semantic.entities.push(structuredClone(e));
  }
  this.generated=[...snapshot.generated];return true;
 }
}
