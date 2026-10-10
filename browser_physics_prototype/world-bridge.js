// Bounded 3D materialization bridge: stable semantic IDs map to Rapier bodies.
// This is the authoritative transition layer, not a renderer or an LLM.
import RAPIER from './vendor/rapier.es.js';
export class WorldBridge {
 constructor(world,semantic){this.world=world;this.semantic=semantic;this.active=new Map();this.events=[];this.maxActive=32;}
 #spawn(e){if(this.active.size>=this.maxActive)throw Error('Active world capacity exceeded');const desc=RAPIER.RigidBodyDesc.dynamic().setTranslation(e.x,e.y,e.z).setLinearDamping(1).setCanSleep(false).enabledTranslations(true,true,false).enabledRotations(false,false,true);
 const body=this.world.createRigidBody(desc);this.world.createCollider(RAPIER.ColliderDesc.capsule(.56,.24).setFriction(.8).setDensity(.65),body);body.setLinvel({x:e.vx,y:e.vy||0,z:e.vz||0},true);body.setRotation(e.q||{x:0,y:0,z:0,w:1},true);body.setAngvel(e.angular||{x:0,y:0,z:0},true);this.active.set(e.id,body);e.materialized=true;this.events.push({type:'materialized',id:e.id,time:this.semantic.time});}
 #capture(e){const body=this.active.get(e.id);if(!body)return;this.semantic.updatePhysical(e.id,body.translation(),body.linvel(),body.rotation(),body.angvel());}
 #release(e){const body=this.active.get(e.id);if(!body)return;this.#capture(e);if(Math.abs(e.x-e.home)>e.range)e.home=e.x;e.materialized=false;this.world.removeRigidBody(body);this.active.delete(e.id);this.events.push({type:'dematerialized',id:e.id,time:this.semantic.time});}
 beforeStep(player){if(!player||!['x','y','z'].every(k=>Number.isFinite(player[k])))throw Error('Invalid perception position');for(const e of this.semantic.entities){const dist=Math.hypot(e.x-player.x,e.y-player.y,e.z-player.z),active=this.active.has(e.id);if(active&&dist>this.semantic.radius+1.5)this.#release(e);else if(!active&&dist<=this.semantic.radius)this.#spawn(e);
  const body=this.active.get(e.id);if(!body)continue;
  // Target motions are force-limited so collisions can obstruct the physical actor.
  const v=body.linvel(),dx=(e.vx-v.x),wanted=Math.max(-.08,Math.min(.08,dx));body.applyImpulse({x:wanted*body.mass(),y:0,z:0},true);
 }}
 afterStep(){for(const e of this.semantic.entities)if(this.active.has(e.id))this.#capture(e);if(this.events.length>50)this.events.splice(0,this.events.length-50);}
 snapshot(){return {version:1,activeIds:[...this.active.keys()],events:this.events.slice(-50)};}
 rebuild(){for(const body of this.active.values())this.world.removeRigidBody(body);this.active.clear();for(const e of this.semantic.entities){if(e.materialized){e.materialized=false;this.#spawn(e);}}}
 observe(player){return this.semantic.observe(player);}
}
