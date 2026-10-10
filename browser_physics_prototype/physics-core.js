import {SemanticWorld} from './semantic-world.js';
import {ActiveRagdoll} from './active-ragdoll.js';
import {WorldBridge} from './world-bridge.js';
import {CharacterModel} from './character-model.js';
import {WorldStreamer,validateWorldProposal} from './world-generator.js';
import {nearbyInteraction,resolveInteraction,resolveExperiment} from './gameplay-rules.js';
import RAPIER from './vendor/rapier.es.js';
export const SETTINGS=Object.freeze({gravity:19.6,playerRadius:.36,playerHalfHeight:.46,groundY:0,walkSpeed:3.3,acceleration:30,jumpHeight:1.12,fenceHeight:.69,fenceX:5.2,crateX:9,mannequinX:-15.05,stoneX:-14.12,step:1/60});
export async function initializePhysics(){await RAPIER.init();}
export class GameCore {
 constructor(){this.create();}
 create(){if(this.world)this.world.free();const s=SETTINGS;this.world=new RAPIER.World({x:0,y:-s.gravity,z:0});this.world.timestep=s.step;
 const fixed=(x,y,hx,hy,hz=1)=>{const b=this.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(x,y,0));this.world.createCollider(RAPIER.ColliderDesc.cuboid(hx,hy,hz).setFriction(.88),b);return b;};
 fixed(-48.8,-.35,71.2,.35,1.5);fixed(213.1,-.35,188.3,.35,1.5);this.fence=this.world.createRigidBody(RAPIER.RigidBodyDesc.kinematicPositionBased().setTranslation(s.fenceX,s.fenceHeight/2,0));this.world.createCollider(RAPIER.ColliderDesc.cuboid(.09,s.fenceHeight/2,.7).setFriction(.85),this.fence);this.stone=fixed(s.stoneX,.13,.19,.13,.45);
 this.player=this.world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(-4.1,s.playerRadius+s.playerHalfHeight+.04,0).setCanSleep(false).setLinearDamping(.03));this.player.lockRotations(true,true);this.player.setEnabledTranslations(true,true,false,true);this.world.createCollider(RAPIER.ColliderDesc.capsule(s.playerHalfHeight,s.playerRadius).setFriction(.45).setRestitution(0),this.player);this.player.setAdditionalMass(65,true);
 this.crate=this.world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(s.crateX,.57,0).setLinearDamping(.9).setAngularDamping(.9));this.crate.lockRotations(true,true);this.crate.setEnabledTranslations(true,true,false,true);this.world.createCollider(RAPIER.ColliderDesc.cuboid(.52,.52,.52).setDensity(.42).setFriction(.85),this.crate);
 this.activeRagdoll=new ActiveRagdoll(this.world,s.mannequinX);
 this.goal=null;this.time=0;this.events=[];this.direction=1;this.previousGrounded=false;this.failedGoals=0;this.stepCount=0;this.nextJumpAt=0;this.lastObstacleContact=false;this.semantic=new SemanticWorld();this.worldBridge=new WorldBridge(this.world,this.semantic);this.character=new CharacterModel();this.gateProgress=0;this.gateRaising=false;this.worldStreamer=new WorldStreamer();this.semanticAccumulator=0;}
 grounded(){const p=this.player.translation(),s=SETTINGS;const ray=new RAPIER.Ray({x:p.x,y:p.y-s.playerRadius-s.playerHalfHeight+.07,z:0},{x:0,y:-1,z:0});return !!this.world.castRay(ray,.19,true,undefined,undefined,undefined,this.player);}
 emit(type,message,metadata={}){const ev={id:`ev-${this.stepCount}-${this.events.length}`,type,message,time:this.time,position:{...this.player.translation()},...metadata};this.events.push(ev);if(this.events.length>100)this.events.shift();return ev;}
 command(command){if(!command||typeof command!=='object')return false;
 switch(command.type){
 case 'Move':if(!Number.isFinite(command.direction)||Math.abs(command.direction)>1)return false;this.manualDirection=command.direction;if(command.direction!==0)this.cancelGoal('Manual control took over.');return true;
 case 'Jump':this.jumpRequested=true;return true;
 case 'Interact':return this.interact();
 case 'Experiment':return this.experiment();
 case 'Goal':if(command.intent!=='crossFence')return false;this.goal={intent:command.intent,stage:'approach',started:this.time};this.emit('goal','Crossing the fence. Manual controls interrupt.');return true;
 case 'CancelGoal':this.cancelGoal('Automatic movement cancelled.');return true;
 case 'TakeManualControl':this.cancelGoal('Manual control resumed.');return true;
 case 'PushRagdoll':this.activeRagdoll.push();this.emit('ragdoll_impact','Impulse applied to articulated mannequin.');return true;
 case 'SetRagdollMode':if(!this.activeRagdoll.setMode(command.mode))return false;this.emit('ragdoll_mode',command.mode==='relax'?'Mannequin muscles relaxed.':command.mode==='walk'?'Mannequin performing walking pose.':'Mannequin muscles activated.');return true;
 case 'InjureRagdoll':if(!this.activeRagdoll.injure(command.part,command.injury,command.severity))return false;this.emit('ragdoll_injury',`${command.part} ${command.injury}.`);return true;
 case 'HealRagdoll':this.activeRagdoll.heal();this.emit('ragdoll_heal','Mannequin injuries cleared.');return true;
 default:return false;}}
 interact(){const result=resolveInteraction({actor:this.player.translation(),character:this.character,semantic:this.semantic,active:this.worldBridge.active,time:this.time});if(result.ok){for(const effect of result.effects||[]){
   switch(effect.type){case 'collect':if(!this.character.collectPlank())return false;this.worldBridge.remove(effect.id);break;
   case 'recordMeasurement':this.character.note(effect.sample);break;
   case 'drink':this.character.drink();break;
   case 'repairBridge':if(!this.character.spendPlanks(2))return false;this.character.bridgeRepaired=true;for(const id of ['bridge-1','bridge-stand-1']){const e=this.semantic.entity(id);e.state.repaired=true;e.revision++;}break;
   default:throw Error('Unrecognized gameplay effect');
  }}}
  this.emit(result.event,result.message,{success:result.ok});return result.ok;}
 experiment(){const result=resolveExperiment({actor:this.player.translation(),semantic:this.semantic,character:this.character,time:this.time});if(result.ok)for(const effect of result.effects||[])if(effect.type==='unlockFence'){this.character.fenceOpened=true;this.gateRaising=true;this.semantic.entity('resonator-1').state.opened=true;this.semantic.entity('resonator-1').revision++;}this.emit(result.event,result.message,{success:result.ok});return result.ok;}
 textCommand(text){if(typeof text!=='string'||text.length>120)return 'Invalid command.';const t=text.trim().toLowerCase();if(!t)return 'Enter a command.';
 if(['look','describe','where am i'].includes(t)){const p=this.player.translation(),o=this.worldBridge.observe(p).filter(e=>!e.state?.collected);return `You are at x ${p.x.toFixed(1)} meters. ${o.length?'Nearby: '+o.map(e=>e.name).join(', ')+'.':''} ${this.character.bridgeRepaired?'The footbridge has been repaired.':'The footbridge is missing two planks.'}`;}
 if(['cross fence','jump over fence','jump over the fence','go over fence','go over the fence'].includes(t)){this.command({type:'Goal',intent:'crossFence'});return this.events.at(-1).message;}
 if(['interact','take','pick up','pick up plank','repair bridge','talk','drink','measure','inspect','examine'].includes(t)){this.interact();return this.events.at(-1).message;}
 if(['tune','try mechanism','experiment','activate mechanism'].includes(t)){this.experiment();return this.events.at(-1).message;}
 if(t==='jump'){this.command({type:'Jump'});return 'Jump requested.';}
 if(['walk mannequin','stand mannequin','relax mannequin','push mannequin','sprain left knee','heal mannequin'].includes(t)){const c={'walk mannequin':{type:'SetRagdollMode',mode:'walk'},'stand mannequin':{type:'SetRagdollMode',mode:'balance'},'relax mannequin':{type:'SetRagdollMode',mode:'relax'},'push mannequin':{type:'PushRagdoll'},'sprain left knee':{type:'InjureRagdoll',part:'leftKnee',injury:'sprain',severity:.85},'heal mannequin':{type:'HealRagdoll'}}[t];this.command(c);return this.events.at(-1).message;}
 if(['stop','cancel','stop moving'].includes(t)){this.command({type:'CancelGoal'});this.manualDirection=0;return 'Stopped.';}
 return 'Try: look, take, interact, measure, tune, jump over fence, repair bridge, talk.';}
 cancelGoal(text){if(this.goal){this.goal=null;this.emit('goal_cancel',text);}}
 step(){const s=SETTINGS,grounded=this.grounded(),p=this.player.translation(),v=this.player.linvel();let dir=this.manualDirection||0;
 if(this.goal){if(p.x>s.fenceX+.8&&grounded){this.goal=null;this.emit('goal_success','You crossed the fence.');dir=0;}else{dir=1;if(this.gateProgress<.72&&p.x>s.fenceX-1.48&&p.x<s.fenceX-.3&&grounded){this.jumpRequested=true;this.goal.stage='jump';}if(this.time-this.goal.started>12){this.goal=null;dir=0;this.failedGoals++;this.emit('goal_failure','Could not cross the fence.');}}}
 const desired=dir*s.walkSpeed*this.character.locomotion().speedFactor;const deltaSpeed=Math.max(-s.acceleration*s.step,Math.min(s.acceleration*s.step,desired-v.x));this.player.applyImpulse({x:this.player.mass()*deltaSpeed,y:0,z:0},true);
 if(this.jumpRequested&&grounded&&this.time>=this.nextJumpAt){this.nextJumpAt=this.time+.25;this.player.applyImpulse({x:0,y:this.player.mass()*(Math.sqrt(2*s.gravity*s.jumpHeight)-v.y),z:0},true);this.emit('jump','Jump.');}
 this.jumpRequested=false;if(this.gateRaising){this.gateProgress=Math.min(1,this.gateProgress+s.step/1.65);if(this.gateProgress>=1)this.gateRaising=false;}this.fence.setNextKinematicTranslation({x:s.fenceX,y:s.fenceHeight/2+2.3*this.gateProgress,z:0});this.activeRagdoll.update(s.step);this.worldBridge.beforeStep(p);this.world.step();const contactParts=this.activeRagdoll.contactWithObstacle(this.stone.collider(0));if(contactParts.length&&!this.lastObstacleContact)this.emit('limb_contact',`Mannequin ${contactParts.join(' and ')} hit the stone.`,{entityId:'mannequin',cause:'rigid_body_collision',outcome:'limb_obstructed'});this.lastObstacleContact=contactParts.length>0;this.time+=s.step;this.semanticAccumulator+=s.step;if(this.semanticAccumulator>=.25-1e-9){this.semantic.step(.25);this.semanticAccumulator=Math.max(0,this.semanticAccumulator-.25);}this.worldBridge.afterStep();if(this.stepCount%30===0)this.worldStreamer.update(this.player.translation().x,this.direction,this.semantic);this.character.step(s.step,this.player.linvel().x);this.stepCount++;const playerX=this.player.translation().x;if(!this.character.farBankReached&&playerX>25.35){this.character.farBankReached=true;this.emit('destination_reached','You reached the far bank. The world continues beyond this path.');}this.previousGrounded=grounded;
 const next=this.player.translation();if(next.y < -6){this.player.setTranslation({x:-4.1,y:1,z:0},true);this.player.setLinvel({x:0,y:0,z:0},true);this.goal=null;this.emit('respawn','Returned to the clearing.');}
 if(this.player.linvel().x>.12)this.direction=1;else if(this.player.linvel().x<-.12)this.direction=-1;
 }
 snapshot(){return {version:4,time:this.time,stepCount:this.stepCount,direction:this.direction,goal:this.goal,character:this.character.snapshot(),gateProgress:this.gateProgress,gateRaising:this.gateRaising,player:{p:{...this.player.translation()},v:{...this.player.linvel()}},crate:{p:{...this.crate.translation()},v:{...this.crate.linvel()}},ragdoll:this.activeRagdoll.state(),semantic:this.semantic.state(),physicalMapping:this.worldBridge.snapshot(),worldStreaming:this.worldStreamer.snapshot(),semanticAccumulator:this.semanticAccumulator,events:this.events.slice(-100)};}
 restore(snapshot){if(!snapshot||![2,3,4].includes(snapshot.version))return false;
 for(const key of ['player','crate']){const b=snapshot[key];if(!b?.p||!b?.v||!['x','y','z'].every(k=>Number.isFinite(b.p[k])&&Number.isFinite(b.v[k])&&Math.abs(b.p[k])<100000&&Math.abs(b.v[k])<100000))return false;}
 if(snapshot.version>=3&&(!snapshot.ragdoll||!this.activeRagdoll.restore(snapshot.ragdoll)))return false;
 if(snapshot.version===4){
  if(!Number.isFinite(snapshot.gateProgress)||snapshot.gateProgress<0||snapshot.gateProgress>1||typeof snapshot.gateRaising!=='boolean'||!Number.isFinite(snapshot.semanticAccumulator??0)||snapshot.semanticAccumulator<0||snapshot.semanticAccumulator>.251)return false;
  const candidateCharacter=new CharacterModel(),candidateSemantic=new SemanticWorld(),candidateStreamer=new WorldStreamer();
  if(!candidateCharacter.restore(snapshot.character)||!candidateSemantic.restore(snapshot.semantic))return false;
  if(!validateWorldProposal(candidateSemantic.entities).ok||candidateSemantic.entities.filter(e=>e.materialized).length>32)return false;
  if(snapshot.worldStreaming&&!candidateStreamer.restore(snapshot.worldStreaming,candidateSemantic))return false;
 }
 if(snapshot.version===4)this.character.restore(snapshot.character);if(snapshot.semantic&&!this.semantic.restore(snapshot.semantic))return false;if(snapshot.version===4&&snapshot.worldStreaming&&!this.worldStreamer.restore(snapshot.worldStreaming,this.semantic))return false;this.worldBridge.rebuild();if(Array.isArray(snapshot.physicalMapping?.events))this.worldBridge.events=snapshot.physicalMapping.events.slice(-50);
 for(const key of ['player','crate']){this[key].setTranslation(snapshot[key].p,true);this[key].setLinvel(snapshot[key].v,true);}
 if(snapshot.version===4){this.gateProgress=snapshot.gateProgress;this.gateRaising=!!snapshot.gateRaising;}this.fence.setTranslation({x:SETTINGS.fenceX,y:SETTINGS.fenceHeight/2+2.3*this.gateProgress,z:0},true);this.fence.setNextKinematicTranslation({x:SETTINGS.fenceX,y:SETTINGS.fenceHeight/2+2.3*this.gateProgress,z:0});
 this.goal=snapshot.goal?.intent==='crossFence'&&Number.isFinite(snapshot.goal.started)?snapshot.goal:null;
 this.time=Number.isFinite(snapshot.time)?Math.max(0,snapshot.time):0;this.semanticAccumulator=snapshot.version===4?(snapshot.semanticAccumulator||0):0;this.stepCount=Number.isInteger(snapshot.stepCount)?snapshot.stepCount:0;this.direction=snapshot.direction===-1?-1:1;
 this.manualDirection=0;this.jumpRequested=false;this.nextJumpAt=this.time+.15;this.lastObstacleContact=false;this.events=Array.isArray(snapshot.events)?snapshot.events.slice(-100):[];
 if(snapshot.version===2)this.emit('save_migrated','Older save restored; the mannequin was reset to its new rig.');return true;}
 state(){return {time:this.time,player:{...this.player.translation()},velocity:{...this.player.linvel()},crate:{...this.crate.translation()},grounded:this.grounded(),goal:this.goal?.stage||null,character:this.character.snapshot(),nearby:nearbyInteraction(this.player.translation(),this.semantic,this.worldBridge.active),gateProgress:this.gateProgress,fence:{x:this.fence.translation().x,y:this.fence.translation().y},direction:this.direction,playerDimensions:{radius:SETTINGS.playerRadius,halfHeight:SETTINGS.playerHalfHeight},fenceHeight:SETTINGS.fenceHeight,visibleEntities:this.worldBridge.observe(this.player.translation()),ragdoll:this.activeRagdoll.state(),events:this.events.slice(-10)};}
}
