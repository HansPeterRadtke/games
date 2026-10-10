// PRSE semantic source of truth for the unobserved world.
// WorldBridge creates/removes the physical scene. This class never calls Rapier or Canvas.
export class SemanticWorld {
 constructor(){this.radius=6;this.time=0;this.entities=[{id:'wanderer-1',kind:'wanderer',name:'Forest wanderer',x:17,y:.85,z:0,vx:.58,vy:0,vz:0,q:{x:0,y:0,z:0,w:1},angular:{x:0,y:0,z:0},home:17,range:4,speed:.58,phase:0,revision:0,source:'initial-world-seed',description:'A wandering traveler follows the forest path.',materialized:false}];}
 step(dt){if(!Number.isFinite(dt)||dt<0||dt>1)throw Error('Invalid semantic step');this.time+=dt;
 for(const e of this.entities){if(e.materialized)continue;
  const width=e.range*2,speed=Math.abs(e.vx);if(width>0&&speed>0){
   const phase=(e.vx>=0?e.x-(e.home-e.range):2*width-(e.x-(e.home-e.range)))+speed*dt;
   const folded=((phase%(2*width))+2*width)%(2*width);
   e.x=e.home-e.range+(folded<=width?folded:2*width-folded);
   e.vx=(folded<=width?1:-1)*speed;
  }else if(width===0){e.x=e.home;e.vx=0;}
  if(e.y>.85||e.vy!==0){e.y+=e.vy*dt-.5*19.6*dt*dt;e.vy-=19.6*dt;if(e.y<=.85){e.y=.85;e.vy=0;}}
  e.revision++;
 }}
 entity(id){return this.entities.find(e=>e.id===id)||null;}
 updatePhysical(id,position,velocity,rotation,angularVelocity){const e=this.entity(id);if(!e||!e.materialized)return false;
 if(!['x','y','z'].every(k=>Number.isFinite(position[k])&&Number.isFinite(velocity[k])&&Number.isFinite(angularVelocity[k]))||!['x','y','z','w'].every(k=>Number.isFinite(rotation[k])))return false;
 e.x=position.x;e.y=position.y;e.z=position.z;e.vx=Math.max(-2,Math.min(2,velocity.x));e.vy=velocity.y;e.vz=velocity.z;e.q={...rotation};e.angular={...angularVelocity};e.revision++;return true;}
 observe(player){const p=typeof player==='number'?{x:player,y:.85,z:0}:player;if(!p||!['x','y','z'].every(k=>Number.isFinite(p[k])))throw Error('Invalid perception position');return this.entities.filter(e=>Math.hypot(e.x-p.x,e.y-p.y,e.z-p.z)<=this.radius+1.5).map(e=>({id:e.id,kind:e.kind,name:e.name,position:{x:e.x,y:e.y,z:e.z},description:e.description,revision:e.revision,physical:e.materialized}));}
 state(){return {version:2,time:this.time,radius:this.radius,entities:this.entities.map(e=>({...e}))};}
 restore(s){if(!s||![1,2].includes(s.version)||!Number.isFinite(s.time)||s.time<0||!Array.isArray(s.entities)||s.entities.length>1000)return false;
 const ids=new Set();for(const e of s.entities){if(typeof e.id!=='string'||!e.id||e.id.length>80||ids.has(e.id)||typeof e.description!=='string'||e.description.length>3000||!['x','y','z','home','range','speed','phase'].every(k=>Number.isFinite(e[k])&&Math.abs(e[k])<1e6)||e.range<0||e.range>1e5||e.speed<0||e.speed>100||!Number.isInteger(e.revision)||e.revision<0||typeof e.materialized!=='boolean'||(e.vx!==undefined&&(!Number.isFinite(e.vx)||Math.abs(e.vx)>2))||(e.vy!==undefined&&(!Number.isFinite(e.vy)||Math.abs(e.vy)>100))||(e.vz!==undefined&&(!Number.isFinite(e.vz)||Math.abs(e.vz)>100))||(e.q!==undefined&&(!['x','y','z','w'].every(k=>Number.isFinite(e.q?.[k])&&Math.abs(e.q[k])<2)))||(e.angular!==undefined&&(!['x','y','z'].every(k=>Number.isFinite(e.angular?.[k])&&Math.abs(e.angular[k])<100))))return false;ids.add(e.id);}
 this.time=s.time;this.entities=s.entities.map(e=>({...e,vx:Number.isFinite(e.vx)?e.vx:e.speed,vy:Number.isFinite(e.vy)?e.vy:0,vz:Number.isFinite(e.vz)?e.vz:0,q:e.q||{x:0,y:0,z:0,w:1},angular:e.angular||{x:0,y:0,z:0}}));return true;}
}
