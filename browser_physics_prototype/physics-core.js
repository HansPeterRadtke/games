import {SemanticWorld} from './semantic-world.js';
import {ActiveRagdoll} from './active-ragdoll.js';
import {WorldBridge} from './world-bridge.js';
import RAPIER from './vendor/rapier.es.js';
export const SETTINGS=Object.freeze({gravity:19.6,playerRadius:.36,playerHalfHeight:.46,groundY:0,walkSpeed:3.3,acceleration:30,jumpHeight:1.12,fenceHeight:.69,fenceX:5.2,crateX:9,mannequinX:-7.05,stoneX:-6.12,step:1/60});
export async function initializePhysics(){await RAPIER.init();}
export class GameCore {
 constructor(){this.create();}
 create(){if(this.world)this.world.free();const s=SETTINGS;this.world=new RAPIER.World({x:0,y:-s.gravity,z:0});this.world.timestep=s.step;
 const fixed=(x,y,hx,hy,hz=1)=>{const b=this.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(x,y,0));this.world.createCollider(RAPIER.ColliderDesc.cuboid(hx,hy,hz).setFriction(.88),b);return b;};
 fixed(0,-.35,120,.35,1.5);this.fence=fixed(s.fenceX,s.fenceHeight/2,.09,s.fenceHeight/2,.7);this.stone=fixed(s.stoneX,.13,.19,.13,.45);
 this.player=this.world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(-4.1,s.playerRadius+s.playerHalfHeight+.04,0).setCanSleep(false).setLinearDamping(.03));this.player.lockRotations(true,true);this.player.setEnabledTranslations(true,true,false,true);this.world.createCollider(RAPIER.ColliderDesc.capsule(s.playerHalfHeight,s.playerRadius).setFriction(.45).setRestitution(0),this.player);
 this.crate=this.world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(s.crateX,.57,0).setLinearDamping(.9).setAngularDamping(.9));this.crate.lockRotations(true,true);this.crate.setEnabledTranslations(true,true,false,true);this.world.createCollider(RAPIER.ColliderDesc.cuboid(.52,.52,.52).setDensity(.42).setFriction(.85),this.crate);
 this.activeRagdoll=new ActiveRagdoll(this.world,s.mannequinX);
 this.goal=null;this.time=0;this.events=[];this.direction=1;this.previousGrounded=false;this.failedGoals=0;this.stepCount=0;this.nextJumpAt=0;this.lastObstacleContact=false;this.semantic=new SemanticWorld();this.worldBridge=new WorldBridge(this.world,this.semantic);}
 grounded(){const p=this.player.translation(),s=SETTINGS;const ray=new RAPIER.Ray({x:p.x,y:p.y-s.playerRadius-s.playerHalfHeight+.07,z:0},{x:0,y:-1,z:0});return !!this.world.castRay(ray,.19,true,undefined,undefined,undefined,this.player);}
 emit(type,message,metadata={}){const ev={id:`ev-${this.stepCount}-${this.events.length}`,type,message,time:this.time,position:{...this.player.translation()},...metadata};this.events.push(ev);if(this.events.length>100)this.events.shift();return ev;}
 command(command){if(!command||typeof command!=='object')return false;
 switch(command.type){case 'Move':if(!Number.isFinite(command.direction)||Math.abs(command.direction)>1)return false;this.manualDirection=command.direction;if(command.direction!==0)this.cancelGoal('Manual control took over.');return true;
 case 'Jump':this.jumpRequested=true;return true;
 case 'PushRagdoll':this.activeRagdoll.push();this.emit('ragdoll_impact','Impulse applied to articulated mannequin.');return true;
 case 'SetRagdollMode':if(!this.activeRagdoll.setMode(command.mode))return false;this.emit('ragdoll_mode',command.mode==='relax'?'Mannequin muscles relaxed.':command.mode==='walk'?'Mannequin performing walking pose.':'Mannequin muscles activated.');return true;
 case 'InjureRagdoll':if(!this.activeRagdoll.injure(command.part,command.injury,command.severity))return false;this.emit('ragdoll_injury',`${command.part} ${command.injury}.`);return true;
 case 'HealRagdoll':this.activeRagdoll.heal();this.emit('ragdoll_heal','Mannequin injuries cleared.');return true;
 case 'Goal':if(command.intent!=='crossFence')return false;this.goal={intent:command.intent,stage:'approach',started:this.time};this.emit('goal','Crossing the fence. Manual controls interrupt.');return true;
 case 'CancelGoal':this.cancelGoal('Automatic movement cancelled.');return true;
 case 'TakeManualControl':this.cancelGoal('Manual control resumed.');return true;
 default:return false;}}
 textCommand(text){if(typeof text!=='string'||text.length>120)return 'Invalid command.';const t=text.toLowerCase().trim();if(t==='describe'||t==='look'||t==='where am i'){const p=this.player.translation();return `You are at x=${p.x.toFixed(1)}m. A ${SETTINGS.fenceHeight.toFixed(2)}m fence stands at x=${SETTINGS.fenceX}m. A movable crate is at x=${this.crate.translation().x.toFixed(1)}m. A jointed mannequin stands at x=${this.activeRagdoll.parts.torso.translation().x.toFixed(1)}m. ${this.semantic.observe(p.x).map(e=>e.description).join(' ')}`;}
 if(['cross fence','jump over fence','jump over the fence','go over fence','go over the fence'].includes(t)){this.command({type:'Goal',intent:'crossFence'});return 'Crossing fence using actual movement and collision.';}
 if(t==='jump'){this.command({type:'Jump'});return 'Jump requested.';}
 if(['walk mannequin','move mannequin'].includes(t)){this.command({type:'SetRagdollMode',mode:'walk'});return 'Joint motors follow walking pose.';}
 if(['stand mannequin','balance mannequin','activate mannequin'].includes(t)){this.command({type:'SetRagdollMode',mode:'balance'});return 'Joint motors and assisted root controller activated.';}
 if(['relax mannequin','drop mannequin'].includes(t)){this.command({type:'SetRagdollMode',mode:'relax'});return 'Joint motors and root controller disabled.';}
 if(['push mannequin','push ragdoll'].includes(t)){this.command({type:'PushRagdoll'});return 'Physics impulse applied.';}
 if(['sprain left knee','injure left knee'].includes(t)){this.command({type:'InjureRagdoll',part:'leftKnee',injury:'sprain',severity:.85});return 'Left-knee motor capability reduced.';}
 if(['heal mannequin','heal knee'].includes(t)){this.command({type:'HealRagdoll'});return 'Knee motor capability restored.';}
 if(['stop','cancel','stop moving'].includes(t)){this.command({type:'CancelGoal'});this.manualDirection=0;return 'Stopped.';}
 return 'Unknown command. Try: describe, jump over fence, walk mannequin, relax mannequin, sprain left knee, heal mannequin.';}
 cancelGoal(text){if(this.goal){this.goal=null;this.emit('goal_cancel',text);}}
 step(){const s=SETTINGS,grounded=this.grounded(),p=this.player.translation(),v=this.player.linvel();let dir=this.manualDirection||0;
 if(this.goal){if(p.x>s.fenceX+.8&&grounded){this.goal=null;this.emit('goal_success','You crossed the fence.');dir=0;}else{dir=1;if(p.x>s.fenceX-1.48&&p.x<s.fenceX-.3&&grounded){this.jumpRequested=true;this.goal.stage='jump';}if(this.time-this.goal.started>12){this.goal=null;dir=0;this.failedGoals++;this.emit('goal_failure','Could not cross the fence.');}}}
 const desired=dir*s.walkSpeed;const deltaSpeed=Math.max(-s.acceleration*s.step,Math.min(s.acceleration*s.step,desired-v.x));this.player.applyImpulse({x:this.player.mass()*deltaSpeed,y:0,z:0},true);
 if(this.jumpRequested&&grounded&&this.time>=this.nextJumpAt){this.nextJumpAt=this.time+.25;this.player.applyImpulse({x:0,y:this.player.mass()*(Math.sqrt(2*s.gravity*s.jumpHeight)-v.y),z:0},true);this.emit('jump','Jump.');}
 this.jumpRequested=false;this.activeRagdoll.update(s.step);this.worldBridge.beforeStep(p);this.world.step();const contactParts=this.activeRagdoll.contactWithObstacle(this.stone.collider(0));if(contactParts.length&&!this.lastObstacleContact)this.emit('limb_contact',`Mannequin ${contactParts.join(' and ')} hit the stone.`,{entityId:'mannequin',cause:'rigid_body_collision',outcome:'limb_obstructed'});this.lastObstacleContact=contactParts.length>0;this.time+=s.step;this.semantic.step(s.step);this.worldBridge.afterStep();this.stepCount++;this.previousGrounded=grounded;
 const next=this.player.translation();if(next.y < -6){this.player.setTranslation({x:-4.1,y:1,z:0},true);this.player.setLinvel({x:0,y:0,z:0},true);this.goal=null;this.emit('respawn','Returned to the clearing.');}
 if(this.player.linvel().x>.12)this.direction=1;else if(this.player.linvel().x<-.12)this.direction=-1;
 }
 snapshot(){return {version:3,time:this.time,stepCount:this.stepCount,direction:this.direction,goal:this.goal,player:{p:{...this.player.translation()},v:{...this.player.linvel()}},crate:{p:{...this.crate.translation()},v:{...this.crate.linvel()}},ragdoll:this.activeRagdoll.state(),semantic:this.semantic.state(),physicalMapping:this.worldBridge.snapshot(),events:this.events.slice(-100)};}
 restore(snapshot){if(!snapshot||![2,3].includes(snapshot.version))return false;
 for(const key of ['player','crate']){const b=snapshot[key];if(!b?.p||!b?.v||!['x','y','z'].every(k=>Number.isFinite(b.p[k])&&Number.isFinite(b.v[k])&&Math.abs(b.p[k])<100000&&Math.abs(b.v[k])<100000))return false;}
 if(snapshot.version===3&&(!snapshot.ragdoll||!this.activeRagdoll.restore(snapshot.ragdoll)))return false;
 if(snapshot.semantic&&!this.semantic.restore(snapshot.semantic))return false;this.worldBridge.rebuild();if(Array.isArray(snapshot.physicalMapping?.events))this.worldBridge.events=snapshot.physicalMapping.events.slice(-50);
 for(const key of ['player','crate']){this[key].setTranslation(snapshot[key].p,true);this[key].setLinvel(snapshot[key].v,true);}
 this.goal=snapshot.goal?.intent==='crossFence'&&Number.isFinite(snapshot.goal.started)?snapshot.goal:null;
 this.time=Number.isFinite(snapshot.time)?Math.max(0,snapshot.time):0;this.stepCount=Number.isInteger(snapshot.stepCount)?snapshot.stepCount:0;this.direction=snapshot.direction===-1?-1:1;
 this.manualDirection=0;this.jumpRequested=false;this.nextJumpAt=this.time+.15;this.lastObstacleContact=false;this.events=Array.isArray(snapshot.events)?snapshot.events.slice(-100):[];
 if(snapshot.version===2)this.emit('save_migrated','Older save restored; the mannequin was reset to its new rig.');return true;}
 state(){return {time:this.time,player:{...this.player.translation()},velocity:{...this.player.linvel()},crate:{...this.crate.translation()},grounded:this.grounded(),goal:this.goal?.stage||null,fenceHeight:SETTINGS.fenceHeight,visibleEntities:this.worldBridge.observe(this.player.translation()),ragdoll:this.activeRagdoll.state(),events:this.events.slice(-10)};}
}
