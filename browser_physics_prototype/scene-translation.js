// Literary description -> validated, supported three-dimensional entities.
// The LLM chooses object classes, descriptions, approximate dimensions and relations.
// Support constraints and world physics are independently enforced; never run model code.
import {sceneProposal} from './generated/llm-scene-proposal.js';
import {safeAffordances} from './generated/llm-affordances.js';
const ROLES=new Set(['bench','candle','jug','note']);
const bounded=(n,min,max)=>typeof n==='number'&&Number.isFinite(n)&&n>=min&&n<=max;
const clean=(s,n)=>typeof s==='string'&&s.length>0&&s.length<=n;
function verifyProposal(proposal){
 if(!proposal||!clean(proposal.scene_description,3000)||!Array.isArray(proposal.objects)||proposal.objects.length!==4)return {ok:false,reason:'Invalid scene or object count'};
 const seen=new Set();for(const o of proposal.objects){
  if(!o||!ROLES.has(o.id)||o.id!==o.kind||seen.has(o.id)||!clean(o.name,90)||!clean(o.description,700)||!['bench','floor'].includes(o.support))return {ok:false,reason:'Invalid object identity, prose or support'};
  if(!['x','y','z'].every(k=>bounded(o[k],-3,3))||!['width','height','depth'].every(k=>bounded(o[k],.001,4))||!bounded(o.mass,.0001,400))return {ok:false,reason:'Invalid physical quantity'};
  seen.add(o.id);
 }
 if(seen.size!==4)return {ok:false,reason:'Missing object type'};
 const bench=proposal.objects.find(e=>e.id==='bench');if(bench.support!=='floor'||bench.width<1||bench.width>3||bench.height<.3||bench.height>1.5)return{ok:false,reason:'Invalid bench'};
 const candle=proposal.objects.find(e=>e.id==='candle'),note=proposal.objects.find(e=>e.id==='note'),jug=proposal.objects.find(e=>e.id==='jug');
 if(candle.support!=='bench'||note.support!=='bench'||jug.support!=='floor')return{ok:false,reason:'Unworkable support relation'};
 for(const item of [candle,note])if(Math.abs(item.x-bench.x)+item.width/2>bench.width/2+.01||Math.abs(item.z-bench.z)+item.depth/2>bench.depth/2+.02)return{ok:false,reason:'Object extends beyond its support'};
 if(Math.abs(jug.x-bench.x)<(jug.width+bench.width)/2-.05 && Math.abs(jug.z-bench.z)<(jug.depth+bench.depth)/2-.05)return{ok:false,reason:'Jug intersects bench footprint'};
 return {ok:true};
}
export function translateSceneToEntities(proposal,anchor=37){
 const result=verifyProposal(proposal);if(!result.ok)return {...result,entities:[]};
 if(!bounded(anchor,-500,500))return {ok:false,reason:'Invalid anchor',entities:[]};
 const bench=proposal.objects.find(o=>o.id==='bench');
 const benchTop=bench.height;
 const world=[];const corrections=[];
 const ordered=['bench','candle','jug','note'];
 for(const kind of ordered){const obj=proposal.objects.find(o=>o.id===kind);
  const centerY=(obj.support==='bench'?benchTop:0)+obj.height/2;
  const correction=centerY-obj.y;
  if(Math.abs(correction)>.02)corrections.push({id:obj.id,modelCenterY:obj.y,physicalCenterY:centerY,reason:'support geometry reconciled'});
  const isThin=kind==='note';
  const dynamic=['candle','jug'].includes(kind);
  world.push({
   id:`shelter-${kind}`,kind,name:obj.name,description:obj.description,source:`local-llm:qwen3.8-27b:2026-10-10:${proposal.prompt_sha256.slice(0,12)}`,
   x:anchor+obj.x,y:centerY,z:obj.z,home:anchor+obj.x,range:0,speed:0,phase:0,vx:0,vy:0,vz:0,revision:0,materialized:false,
   q:{x:0,y:0,z:0,w:1},angular:{x:0,y:0,z:0},
   physical:{body:dynamic?'dynamic':'fixed',collider:isThin?'none':'cuboid',halfExtents:[obj.width/2,obj.height/2,obj.depth/2],...(dynamic?{mass:obj.mass}: {})},
   state:{condition:'intact',lit:false,fallen:false,wet:false,water:kind==='jug'?1:0,flammable:['bench','note'].includes(kind),supportId:obj.support==='bench'?'shelter-bench':null},
   affordances:safeAffordances.accepted.filter(a=>a.object_id===kind).map(a=>({verb:a.verb,label:a.label,origin:'llm-validated',promptHash:safeAffordances.prompt_sha256.slice(0,12)})),
   size:{x:obj.width,y:obj.height,z:obj.depth},sceneId:proposal.scene_id,
  });
 }
 world.unshift({id:'shelter-setting',kind:'shelter',name:'Abandoned riverside shelter',description:proposal.scene_description,source:`scene-prose:${proposal.prompt_sha256.slice(0,12)}`,x:anchor,y:1.4,z:.3,home:anchor,range:0,speed:0,phase:0,vx:0,vy:0,vz:0,q:{x:0,y:0,z:0,w:1},angular:{x:0,y:0,z:0},revision:0,materialized:false,physical:{body:'fixed',collider:'none'},state:{condition:'intact'}});
 return {ok:true,entities:world,corrections,rawPhysicalIssueCount:corrections.length};
}
export const validatedShelterScene=translateSceneToEntities(sceneProposal,37);
if(!validatedShelterScene.ok)throw new Error('Scene translation failed: '+validatedShelterScene.reason);
