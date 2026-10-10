// PRSE three-dimensional physical materialization boundary; never renders.
// Only validated kinds and named Rapier collider shapes are allowed to become physics.
import RAPIER from './vendor/rapier.es.js';
const valid=(n)=>typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<=20;
export class WorldBridge {
 constructor(world,semantic){this.world=world;this.semantic=semantic;this.active=new Map();this.events=[];this.maxActive=32;}
 #colliderFor(entity){const p=entity.physical||{};switch(p.collider){
  case 'none':return null;
  case 'cuboid':if(!Array.isArray(p.halfExtents)||p.halfExtents.length!==3||!p.halfExtents.every(v=>valid(v)&&v>0))throw Error('Invalid collider');return RAPIER.ColliderDesc.cuboid(...p.halfExtents).setFriction(.78).setDensity(1);
  case 'capsule':if(!valid(p.halfHeight)||!valid(p.radius)||p.halfHeight===0||p.radius===0)throw Error('Invalid capsule');return RAPIER.ColliderDesc.capsule(p.halfHeight,p.radius).setFriction(.8).setDensity(.65);
  default:throw Error('Unsupported physical collider '+p.collider);
 }}
 #shouldSpawn(e){return !e.state?.collected&&(e.kind!=='bridge'||e.state?.repaired===true);}
 #spawn(e){if(!this.#shouldSpawn(e))return;if(this.active.size>=this.maxActive)throw Error('Active world capacity exceeded');const p=e.physical||{};
 const desc=(p.body==='fixed'?RAPIER.RigidBodyDesc.fixed():p.body==='dynamic'?RAPIER.RigidBodyDesc.dynamic():null);if(!desc)throw Error('Unsupported body');
 desc.setTranslation(e.x,e.y,e.z);if(p.body==='dynamic'){desc.setLinearDamping(.65).setCanSleep(false).enabledTranslations(true,true,false).enabledRotations(false,false,true);}
 const body=this.world.createRigidBody(desc);const collider=this.#colliderFor(e);if(collider){if(Number.isFinite(p.mass)&&p.mass>0&&p.mass<200&&p.body==='dynamic')collider.setMass(p.mass);this.world.createCollider(collider,body);}
 if(p.body==='dynamic'){body.setLinvel({x:e.vx,y:e.vy||0,z:e.vz||0},true);body.setRotation(e.q||{x:0,y:0,z:0,w:1},true);body.setAngvel(e.angular||{x:0,y:0,z:0},true);}
 this.active.set(e.id,body);e.materialized=true;this.events.push({type:'materialized',id:e.id,time:this.semantic.time});}
 #capture(e){const body=this.active.get(e.id);if(!body)return;this.semantic.updatePhysical(e.id,body.translation(),body.linvel(),body.rotation(),body.angvel());}
 #release(e){const body=this.active.get(e.id);if(!body)return;this.#capture(e);if(e.range===0||(e.range>0&&Math.abs(e.x-e.home)>e.range))e.home=e.x;e.materialized=false;this.world.removeRigidBody(body);this.active.delete(e.id);this.events.push({type:'dematerialized',id:e.id,time:this.semantic.time});}
 refresh(id){const e=this.semantic.entity(id);if(!e)return false;const was=this.active.has(id);if(was)this.#release(e);if(this.#shouldSpawn(e)&&was)this.#spawn(e);return true;}
 remove(id){const e=this.semantic.entity(id);if(!e)return false;if(this.active.has(id))this.#release(e);e.state.collected=true;e.revision++;return true;}
 beforeStep(player){if(!player||!['x','y','z'].every(k=>Number.isFinite(player[k])))throw Error('Invalid perception position');for(const e of this.semantic.entities){
  const dist=Math.hypot(e.x-player.x,e.y-player.y,e.z-player.z),active=this.active.has(e.id);
  if(active&&(dist>this.semantic.radius+1.5||!this.#shouldSpawn(e)))this.#release(e);
  else if(!active&&dist<=this.semantic.radius&&this.#shouldSpawn(e))this.#spawn(e);
  const body=this.active.get(e.id);if(!body||e.kind!=='wanderer')continue;
  if(e.range>0&&(e.x>=e.home+e.range||e.x<=e.home-e.range))e.vx=-e.vx||.4;
  const v=body.linvel(),wanted=Math.max(-.08,Math.min(.08,e.vx-v.x));body.applyImpulse({x:wanted*body.mass(),y:0,z:0},true);
 }}
 afterStep(){for(const e of this.semantic.entities)if(this.active.has(e.id))this.#capture(e);if(this.events.length>64)this.events.splice(0,this.events.length-64);}
 snapshot(){return {version:2,activeIds:[...this.active.keys()],events:this.events.slice(-64)};}
 rebuild(){for(const body of this.active.values())this.world.removeRigidBody(body);this.active.clear();for(const e of this.semantic.entities){if(e.materialized){e.materialized=false;this.#spawn(e);}}}
 observe(player){return this.semantic.observe(player);}
}
