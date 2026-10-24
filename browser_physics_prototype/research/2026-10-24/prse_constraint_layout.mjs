// Compile a LIMITED automatically interpreted SceneEval entity/relation proposal
// into source-linked 3D Rapier GameCore objects. No annotations/gold used here.
// We do NOT claim arbitrary language understanding; log abstentions/failures.
import {object,PRSELoop,geometryIssues,validateScene} from './prse_semantic_roundtrip.mjs';

const room={cx:-27,cz:11.8,halfX:9.4,halfZ:6.6};
const DIM={
 bed:[2.1,.6,1.6],nightstand:[.55,.7,.55],wardrobe:[1.4,2,.7],
 armchair:[.95,.85,.95],floor_lamp:[.25,1.65,.25],sofa:[2.2,.85,.9],
 bookshelf:[1.25,2.1,.45],bookcase:[1.25,2.1,.45],coffee_table:[1.15,.45,.65],
 dining_table:[1.7,.78,1.2],table:[1.45,.76,.85],chair:[.55,.88,.55],
 desk:[1.4,.75,.8],dresser:[1.2,.9,.6],cabinet:[1.2,1.5,.6],
 lamp:[.3,.6,.3],rug:[1.6,.03,1.2],plant:[.5,.9,.5],
 painting:[.8,.6,.08],mirror:[.8,1.1,.09],window:[1.2,1.1,.12],
 TV:[.8,.9,.16],tv_stand:[1.25,.62,.6],shelf:[1.2,1.3,.35],
 toilet:[.55,.8,.6],sink:[.7,.9,.55],bathtub:[1.7,.8,.82],
 fridge:[.8,1.7,.75],oven:[.8,.9,.72],stool:[.45,.72,.45],
 book:[.18,.05,.25],box:[.65,.5,.55],ball:[.25,.25,.25],
 vase:[.25,.4,.25],floor_cushion:[.5,.16,.5],wall_cabinet:[1.1,.9,.4],
 bar_table:[1.55,1.0,.8],bar_stool:[.5,.8,.5],wine_cabinet:[1.2,1.7,.5],
 dining_chair:[.52,.88,.52],office_chair:[.65,.85,.65],
 office_desk:[1.4,.75,.75],sofa_chair:[.85,.82,.85],bean_bag:[.7,.5,.7],
 pendant_light:[.32,.5,.32],ceiling_light:[.35,.3,.35],
 wall_light:[.25,.35,.2],toy_box:[.8,.55,.65],doll:[.24,.35,.2],
 monitor:[.56,.4,.14],cup:[.09,.12,.09],jug:[.25,.35,.22],
 potted_plant:[.38,.65,.38],clock:[.35,.35,.08],tray:[.36,.04,.3],
 teapot:[.24,.22,.18],wall_shelf:[1.0,.08,.32],display_shelf:[1.2,1.65,.5],
 light:[.28,.5,.28],electronic_peripheral:[.25,.08,.12]
};
const dynamic=new Set(['ball','vase','book','cup','jug','teapot','doll','potted_plant','lamp']);
const massByType={ball:.5,vase:.9,book:.3,cup:.25,jug:.8,teapot:.7,doll:.24,potted_plant:2.5,lamp:.9,monitor:3.5};
const color=new Set(['blue','red','green','white','black','brown','grey']);
function walls(prefix){
 const e=[];
 // Physical wall segments (each at most eight metres), built as source-linked
 // research geometry around the room. The source only mentions a room, not
 // these precise dimensions; their scale is therefore provisional.
 let n=0;
 for(const z of [5.05,18.55])for(const x of [-33.25,-27,-20.75]){
  e.push(object(prefix+'-wall-'+n++,'wall',{x,y:1.45,z},{x:6.1,y:2.9,z:.13},
    {body:'fixed',material:'stone',source:'provisional_3D_room_boundary'}));
 }
 for(const x of [-36.6,-17.4])for(const z of [8.4,12.0,15.65]){
  e.push(object(prefix+'-wall-'+n++,'wall',{x,y:1.45,z},{x:.13,y:2.9,z:3.2},
    {body:'fixed',material:'stone',source:'provisional_3D_room_boundary'}));
 }
 return e;
}
const center=()=>({x:room.cx,z:room.cz});
const clearance=(a,b)=>(a.size.x+b.size.x)/2+.24;
const overlaps2d=(a,b,margin=.02)=>
 Math.abs(a.position.x-b.position.x)<(a.size.x+b.size.x)/2+margin
 &&Math.abs(a.position.z-b.position.z)<(a.size.z+b.size.z)/2+margin
 &&Math.abs(a.position.y-b.position.y)<(a.size.y+b.size.y)/2-.01;
const within=e=>e.position.x-e.size.x/2>room.cx-room.halfX+.4
 &&e.position.x+e.size.x/2<room.cx+room.halfX-.4
 &&e.position.z-e.size.z/2>room.cz-room.halfZ+.4
 &&e.position.z+e.size.z/2<room.cz+room.halfZ-.4;
function collide(e,entities){
 return entities.some(b=>b!==e&&b.state?.condition!=='ashes'&&overlaps2d(e,b));
}
function legal(e,items){return within(e)&&!collide(e,items);}
function validRelation(r,items){
 const a=items.find(e=>e.kind===r.a),b=items.find(e=>e.kind===r.b);
 if(!a)return null;
 if(r.kind==='room'){
  if(r.type==='against'&&r.b==='wall')
   return Math.min(a.position.x-a.size.x/2-(room.cx-room.halfX),
    room.cx+room.halfX-(a.position.x+a.size.x/2),
    a.position.z-a.size.z/2-(room.cz-room.halfZ),
    room.cz+room.halfZ-(a.position.z+a.size.z/2))<.8;
  if(r.type==='corner')return Math.abs(a.position.x-room.cx)>room.halfX-2.7
   &&Math.abs(a.position.z-room.cz)>room.halfZ-2.7;
  if(['middle','center'].includes(r.type))return Math.hypot(a.position.x-room.cx,a.position.z-room.cz)<2.2;
  return null;
 }
 if(!b)return null;
 const dx=a.position.x-b.position.x,dz=a.position.z-b.position.z,dy=a.position.y-b.position.y;
 const gap=Math.hypot(Math.max(0,Math.abs(dx)-(a.size.x+b.size.x)/2),
                       Math.max(0,Math.abs(dz)-(a.size.z+b.size.z)/2));
 if(r.type==='on')return a.supportId===b.id&&Math.abs(a.position.y-a.size.y/2-b.position.y-b.size.y/2)<.07;
 if(['next','near','adjacent','beside'].includes(r.type))return gap<1.1;
 if(r.type==='front')return dz<-.3;
 if(r.type==='behind')return dz>.3;
 if(r.type==='above')return dy>(a.size.y+b.size.y)/2-.1;
 if(r.type==='left')return dx<-.35;
 if(r.type==='right')return dx>.35;
 if(['across','opposite'].includes(r.type))return Math.hypot(dx,dz)>2.5;
 if(r.type==='surround')return gap<2.5;
 return null;
}
function setSupport(a,b,items){
 // Relation only valid if target is a real non-tombstone support and fits.
 if(!b||a===b||b.size.x<a.size.x+.02||b.size.z<a.size.z+.02||a.kind==='rug')return false;
 const prior={position:{...a.position},supportId:a.supportId};
 a.supportId=b.id;
 a.position={x:b.position.x,y:b.position.y+b.size.y/2+a.size.y/2+.001,z:b.position.z};
 if(!legal(a,items)){a.position=prior.position;a.supportId=prior.supportId;return false;}
 return true;
}
function moveRelative(a,b,r,items){
 if(!b||a===b||a.supportId!=='floor')return false;
 const gap=clearance(a,b);
 const dirs=r.type==='front'?[[0,-1]]:r.type==='behind'?[[0,1]]:
  r.type==='left'?[[-1,0]]:r.type==='right'?[[1,0]]:
  [['1',0],[-1,0],[0,1],[0,-1]]; // generic near alternatives
 for(const [ux,uz] of dirs){
  const old={...a.position};
  a.position.x=b.position.x+Number(ux)*gap;
  a.position.z=b.position.z+Number(uz)*((a.size.z+b.size.z)/2+.35);
  if(legal(a,items))return true;
  a.position=old;
 }
 return false;
}
export function compileProposal(proposal, {maxEntities=32}={}){
 if(!proposal||typeof proposal.text!=='string'||typeof proposal.sourceId!=='string')throw Error('Bad text proposal');
 const sceneId='sem-'+proposal.sourceId;
 const candidates=[],refusals=[];
 // If a type is negated it must never be silently materialized.
 const types=Object.entries(proposal.quantities||{}).filter(([name,count])=>count.count>0);
 let seq=0;
 for(const [kind,data] of types){
  if(data.ambiguous){refusals.push({type:'ambiguous_count',kind});continue;}
  const n=data.count+(data.op==='gt'?1:0);
  if(n>12){refusals.push({type:'too_many_same_type',kind,n});continue;}
  if(!DIM[kind]){refusals.push({type:'unknown_geometry',kind,count:n});continue;}
  for(let i=0;i<n;i++){
   if(candidates.length>=maxEntities){refusals.push({type:'bounded_budget_exhausted',kind});break;}
   const [x,y,z]=DIM[kind],idx=seq++;
   const pos={x:-33.6+(idx%5)*3.2,y:y/2,z:8.15+Math.floor(idx/5)*2.6};
   const props=proposal.mentions.filter(m=>m.type===kind).flatMap(m=>m.attributes);
   const derived=object(sceneId+'-'+kind.toLowerCase().replace(/[^a-z0-9]/g,'-')+'-'+i,
    kind,pos,{x,y,z},{
     body:dynamic.has(kind)?'dynamic':'fixed',
     material:props.includes('wooden')?'wood':props.includes('metal')?'metal':'unknown',
     shape:kind==='ball'?'sphere':'box',
     mass:massByType[kind]??1,
     name:kind+' '+(i+1),
     source:'SceneEval-'+proposal.sourceId+':text-span-grounding',
     description:kind+'; provisional scale and layout',
     state:{condition:'intact',predictedAttributes:[...new Set(props)]}
    });
   candidates.push(derived);
  }
 }
 // Physical constraints must not be forced when the proposed relationship
 // conflicts with sizes or another placement. Record abstention and continue.
 const outcomes=[];
 for(const relation of proposal.relations||[]){
  const a=candidates.find(e=>e.kind===relation.a),b=candidates.find(e=>e.kind===relation.b);
  let attempted=false,resolved=false;
  if(relation.kind==='object'&&a&&b){
   if(relation.type==='on'){attempted=true;resolved=setSupport(a,b,candidates);}
   else if(['next','near','adjacent','front','behind','left','right'].includes(relation.type)){
    attempted=true;resolved=moveRelative(a,b,relation,candidates);
   }
  }
  if(relation.kind==='room'&&a){
   const old={...a.position};
   if(relation.type==='corner'){
    attempted=true;a.position.x=room.cx-room.halfX+a.size.x/2+.6;
    a.position.z=room.cz-room.halfZ+a.size.z/2+.6;
   }else if(relation.type==='against'&&relation.b==='wall'){
    attempted=true;a.position.x=room.cx-room.halfX+a.size.x/2+.45;
   }else if(['middle','center'].includes(relation.type)){
    attempted=true;a.position.x=room.cx;a.position.z=room.cz;
   }
   if(attempted){resolved=legal(a,candidates);if(!resolved)a.position=old;}
  }
  const grounded=validRelation(relation,candidates);
  outcomes.push({type:relation.type,kind:relation.kind,a:relation.a,b:relation.b,
   attempted,resolved,grounded,sourceText:relation.sourceText});
 }
 // Some complex predicted scenes need a separate spatial solver; skip corrupt
 // geometry rather than throwing random boxes into game world.
 const validC=candidates.every(x=>legal(x,candidates));
 const world={id:sceneId,prose:proposal.text,entities:[...walls(sceneId),...candidates]};
 const geometricProblems=geometryIssues(world);
 const good=validC&&geometricProblems.length===0;
 return {sourceId:proposal.sourceId,source:proposal.text,scene:world,proposed:candidates.length,
  missing:refusals,relations:outcomes,hasUnknownRelations:outcomes.some(x=>x.grounded===null),
  relationGeometryCorrect:outcomes.filter(x=>x.grounded===true).length,
  relationGeometryWrong:outcomes.filter(x=>x.grounded===false).length,
  relationGeometryUnknown:outcomes.filter(x=>x.grounded===null).length,
  good,geometricProblems,correctionsAreProvisional:true,
  geometryStrategy:'conservative physical sizes, twelve-metre room, grid + prioritized relative layout; not calibrated architectural truth'};
}
export {validRelation};
