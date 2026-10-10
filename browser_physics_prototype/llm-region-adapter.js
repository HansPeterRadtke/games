import {semanticAssetManifest} from './generated/semantic-asset-manifest.js';
// Converts independently generated, validated literary regions to 3D spatial facts.
// The game owns identities, physics semantics and save/load; generated prose is data.
const KINDS=new Set(['tree','rock','spring','shelter','destination']);
const number=(v,lo,hi)=>Number.isFinite(v)&&v>=lo&&v<=hi;
export function validateLiteraryScene(scene){
 if(!scene||!Number.isInteger(scene.region)||scene.region<0||scene.region>=8||!['bridge_repaired','bridge_unrepaired','mechanism_open','mechanism_closed'].includes(scene.branch)||!number(scene.anchor,0,150)||typeof scene.description!=='string'||scene.description.length<40||scene.description.length>950||typeof scene.title!=='string'||scene.title.length<5||scene.title.length>100||typeof scene.source!=='string'||scene.source.length>200)return {ok:false,error:'Invalid scene identity or prose'};
 if(!Array.isArray(scene.objects)||scene.objects.length<2||scene.objects.length>4)return {ok:false,error:'Invalid object count'};
 const bounds=[];
 for(const [i,obj] of scene.objects.entries()){
  if(!obj||!KINDS.has(obj.kind)||typeof obj.name!=='string'||obj.name.length<2||obj.name.length>90||typeof obj.description!=='string'||obj.description.length<4||obj.description.length>300||typeof obj.interaction_clue!=='string'||obj.interaction_clue.length>300)return {ok:false,error:`Invalid object semantic data: ${i}`};
  for(const [k,lo,hi] of [['offset_x_m',-4.2,4.2],['center_height_m',.08,5],['width_m',.15,5.5],['height_m',.15,8],['depth_m',.15,5.5],['mass_kg',.05,20000]])if(!number(obj[k],lo,hi))return {ok:false,error:`Invalid physical attribute: ${i}:${k}`};
  if(obj.center_height_m+0.02<obj.height_m/2)return {ok:false,error:`Initial ground penetration: ${i}`};
  // Geometry placed in same side-view scene: reject intersecting volumes, irrespective of class.
  for(const previous of bounds){if(Math.abs(previous.x-obj.offset_x_m)<(previous.width+obj.width_m)/2-.09&&Math.abs(previous.y-obj.center_height_m)<(previous.height+obj.height_m)/2-.06)return {ok:false,error:`Overlapping objects: ${i}`};}
  bounds.push({x:obj.offset_x_m,y:obj.center_height_m,width:obj.width_m,height:obj.height_m});
 }
 return {ok:true,count:scene.objects.length};
}
const physicsOf=obj=>obj.kind==='rock'?{body:'fixed',collider:'cuboid',halfExtents:[obj.width_m/2,obj.height_m/2,obj.depth_m/2]}:obj.kind==='tree'?{body:'fixed',collider:'cuboid',halfExtents:[Math.min(.25,obj.width_m/5),obj.height_m/2,Math.min(.35,obj.depth_m/5)]}:{body:'fixed',collider:'none'};
export function sceneToEntities(scene){const validation=validateLiteraryScene(scene);if(!validation.ok)return {...validation,entities:[]};
 const source=scene.source,description=scene.description,region=scene.region,branch=scene.branch;
 const base=(id,kind,name,x,y,z,description,physical,extra={})=>({id,kind,name,x,y,z,home:x,range:0,speed:0,phase:0,vx:0,vy:0,vz:0,q:{x:0,y:0,z:0,w:1},angular:{x:0,y:0,z:0},source,revision:0,description,materialized:false,physical,state:{inspected:false},...extra});
 const center=base(`region-${region}-landmark`,'shelter',scene.title,scene.anchor,1.2,2,description,{body:'fixed',collider:'none'},{narrative:{chapter:`region-${region}`,branch,originalDescription:description}});
 const entities=[center];for(const [i,obj] of scene.objects.entries()){
  // Tall landmark scenery stands off the walking lane but retains true 3D coordinates.
  const z=obj.kind==='tree'||obj.kind==='shelter'?Math.min(1.9,Math.max(.7,obj.depth_m/2+.52)):0;
  const art=semanticAssetManifest.selection[`${region}:${branch}:${i}`]?.artifact;
  const asset=art&&art.license==='CC0'&&/^catalog\/[a-f0-9]{20}\.png$/.test(art.relative_path)?{relativePath:art.relative_path,sha256:art.sha256,pack:art.pack,source:art.source,license:art.license}:null;
  entities.push(base(`region-${region}-llm-${i}`,obj.kind,obj.name,scene.anchor+obj.offset_x_m,obj.center_height_m,z,obj.description,physicsOf(obj),{size:{x:obj.width_m,y:obj.height_m,z:obj.depth_m},artwork:asset,narrative:{chapter:`region-${region}`,interactionClue:obj.interaction_clue,originalDescription:obj.description,branch}}));
 }
 return {ok:true,entities};
}
export function chooseLiteraryScene(scenes,region,flags={}){
 if(!Array.isArray(scenes)||!Number.isInteger(region))return null;
 const branch=region===1?(flags.bridgeRepaired?'bridge_repaired':'bridge_unrepaired'):region===2?(flags.mechanismOpen?'mechanism_open':'mechanism_closed'):null;
 return branch?scenes.find(scene=>scene.region===region&&scene.branch===branch)||null:null;
}
