// Active three-dimensional rigid-body mannequin, viewed through a 2D projection.
// All joints/contacts are solved by Rapier; poses drive motors, not positions.
import RAPIER from './vendor/rapier.es.js';
const LIMIT=0x00020001; // collide with environment (group 1), not another part of this same mannequin (group 2).
const PARTS=Object.freeze({
 torso:{dx:0,y:1.55,length:.76,radius:.18},head:{dx:0,y:2.25,length:.18,radius:.19},
 leftUpperArm:{dx:-.27,y:1.61,length:.48,radius:.105},leftForearm:{dx:-.27,y:1.15,length:.44,radius:.095},
 rightUpperArm:{dx:.27,y:1.61,length:.48,radius:.105},rightForearm:{dx:.27,y:1.15,length:.44,radius:.095},
 leftThigh:{dx:-.16,y:.87,length:.54,radius:.135},leftShin:{dx:-.16,y:.33,length:.54,radius:.105},
 rightThigh:{dx:.16,y:.87,length:.54,radius:.135},rightShin:{dx:.16,y:.33,length:.54,radius:.105}
});
const JOINTS=[
 ['neck','torso','head',[0,.49],[0,-.21]],
 ['leftShoulder','torso','leftUpperArm',[-.27,.30],[0,.24]],
 ['leftElbow','leftUpperArm','leftForearm',[0,-.24],[0,.22]],
 ['rightShoulder','torso','rightUpperArm',[.27,.30],[0,.24]],
 ['rightElbow','rightUpperArm','rightForearm',[0,-.24],[0,.22]],
 ['leftHip','torso','leftThigh',[-.16,-.41],[0,.27]],
 ['leftKnee','leftThigh','leftShin',[0,-.27],[0,.27]],
 ['rightHip','torso','rightThigh', [.16,-.41],[0,.27]],
 ['rightKnee','rightThigh','rightShin',[0,-.27],[0,.27]]
];
const clamp=(n,low,high)=>Math.min(high,Math.max(low,n));
export class ActiveRagdoll {
 constructor(world,x=10.5,options={}){this.motorStiffness=options.motorStiffness??2;this.motorDamping=options.motorDamping??.7;this.balanceGain=options.balanceGain??.005;this.supportGain=options.supportGain??0;this.supportDamping=options.supportDamping??10;this.footContacts=0;this.totalMass=0;this.rootGain=options.rootGain??40;this.rootDamping=options.rootDamping??12;this.targetX=x;this.world=world;this.x=x;this.parts={};this.joints={};this.mode='balance';this.walkTime=0;this.health={leftKnee:{type:'healthy',severity:0},rightKnee:{type:'healthy',severity:0}};
 for(const [name,c] of Object.entries(PARTS)){const desc=RAPIER.RigidBodyDesc.dynamic().setTranslation(x+c.dx,c.y,0).setLinearDamping(.08).setAngularDamping(.1);if(name==='torso')desc.enabledTranslations(true,true,false).enabledRotations(false,false,true);const b=world.createRigidBody(desc);world.createCollider(RAPIER.ColliderDesc.capsule(c.length/2,c.radius).setFriction(1.2).setRestitution(0).setDensity(.95).setCollisionGroups(LIMIT),b);this.parts[name]=b;this.totalMass+=b.mass();}
 for(const [name,a,b,anchorA,anchorB] of JOINTS){const joint=world.createImpulseJoint(RAPIER.JointData.revolute({x:anchorA[0],y:anchorA[1],z:0},{x:anchorB[0],y:anchorB[1],z:0},{x:0,y:0,z:1}),this.parts[a],this.parts[b],true);if(name==='leftKnee'||name==='rightKnee')joint.setLimits(-.2,1.6);this.joints[name]=joint;}
 }
 setMode(mode){if(!['balance','walk','relax'].includes(mode))return false;if(mode!=='relax'&&this.mode==='relax')this.targetX=this.parts.torso.translation().x;this.mode=mode;return true;}
 injure(part,type='sprain',severity=.7){if(!['leftKnee','rightKnee'].includes(part)||!['sprain','bruise','cut'].includes(type)||!Number.isFinite(severity)||severity<0||severity>1)return false;this.health[part]={type,severity};return true;}
 heal(){for(const name of ['leftKnee','rightKnee'])this.health[name]={type:'healthy',severity:0};}
 push(){this.parts.torso.applyImpulse({x:.55,y:.17,z:0},true);}
 update(dt){if(!Number.isFinite(dt)||dt<0||dt>.1)throw Error('Invalid simulation step');if(this.mode==='walk')this.walkTime+=dt;
 const t=this.walkTime*4,active=this.mode!=='relax',w=this.mode==='walk';if(w)this.targetX+=.14*dt;
 const pose={neck:0,leftShoulder:w?-.42*Math.sin(t):0,rightShoulder:w?.42*Math.sin(t):0,leftElbow:-.15,rightElbow:.15,leftHip:w?.38*Math.sin(t):0,rightHip:w?-.38*Math.sin(t):0,leftKnee:w?.34*(1+Math.sin(t)):.04,rightKnee:w?.34*(1-Math.sin(t)):.04};
 for(const [name,joint] of Object.entries(this.joints)){const injury=this.health[name];const penalty=injury?(injury.type==='sprain'?injury.severity*.9:injury.type==='bruise'?injury.severity*.4:injury.severity*.1):0;const strength=active?Math.max(0.1,1-penalty):0;
 joint.configureMotorPosition(active?pose[name]:0,active?this.motorStiffness*strength:0,active?this.motorDamping*strength:0);}
 if(active){const b=this.parts.torso,rot=b.rotation(),angle=2*Math.atan2(rot.z,rot.w),vel=b.angvel().z;const error=Math.atan2(Math.sin(angle),Math.cos(angle));const torque=clamp(-this.balanceGain*error-this.balanceGain*.2*vel,-.03,.03);b.applyTorqueImpulse({x:0,y:0,z:torque},true);
 // Feet can push only when actual world-ray contact exists; otherwise no fake air support.
 const contact=[];for(const key of ['leftShin','rightShin']){const leg=this.parts[key],p=leg.translation(),q=leg.rotation(),a=2*Math.atan2(q.z,q.w),tipX=p.x+.27*Math.sin(a),tipY=p.y-.27*Math.cos(a);const ray=new RAPIER.Ray({x:tipX,y:tipY+.13,z:p.z},{x:0,y:-1,z:0});const hit=this.world.castRay(ray,.30,true,undefined,0x00010001);if(hit&&hit.timeOfImpact<.25)contact.push(key);}
 this.footContacts=contact.length;
 if(contact.length&&Math.abs(error)<.9&&this.supportGain>0){const height=this.parts.torso.translation().y,verticalSpeed=this.parts.torso.linvel().y;const lift=clamp(this.totalMass*(19.6+this.supportGain*(1.55-height)-this.supportDamping*verticalSpeed),0,this.totalMass*19.6*3)*dt/contact.length;for(const key of contact)this.parts[key].applyImpulse({x:0,y:lift,z:0},true);}
 if(this.rootGain>0){const p=b.translation(),v=b.linvel(),gain=this.rootGain,mass=this.totalMass;const xForce=clamp(mass*(gain*(this.targetX-p.x)-this.rootDamping*v.x),-mass*25,mass*25);const yForce=clamp(mass*(19.6+gain*(1.55-p.y)-this.rootDamping*v.y),-mass*8,mass*50);b.applyImpulse({x:xForce*dt,y:yForce*dt,z:0},true);}
 }else this.footContacts=0;
 }
 contactWithObstacle(collider){if(!collider)return [];const result=[];for(const name of ['leftShin','rightShin'])this.world.contactPair(collider,this.parts[name].collider(0),(manifold)=>{if(!result.includes(name))result.push(name);});return result;}
 state(){return {mode:this.mode,walkTime:this.walkTime,targetX:this.targetX,footContacts:this.footContacts,health:structuredClone(this.health),parts:Object.fromEntries(Object.entries(this.parts).map(([name,b])=>[name,{position:{...b.translation()},rotation:{...b.rotation()},velocity:{...b.linvel()},angularVelocity:{...b.angvel()}}]))};}
 restore(snapshot){
 if(!snapshot||!['balance','walk','relax'].includes(snapshot.mode)||!Number.isFinite(snapshot.walkTime)||snapshot.walkTime<0||snapshot.walkTime>1e9||!Number.isFinite(snapshot.targetX)||Math.abs(snapshot.targetX)>1e5||!snapshot.parts||typeof snapshot.parts!=='object'||!snapshot.health)return false;
 const validateVector=(o,keys)=>o&&keys.every(k=>typeof o[k]==='number'&&Number.isFinite(o[k])&&Math.abs(o[k])<=1e5);
 for(const key of Object.keys(PARTS)){const s=snapshot.parts[key];if(!s||!validateVector(s.position,['x','y','z'])||!validateVector(s.velocity,['x','y','z'])||!validateVector(s.angularVelocity,['x','y','z'])||!validateVector(s.rotation,['x','y','z','w']))return false;const q=s.rotation,norm=q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w;if(norm<.5||norm>1.5)return false;}
 for(const key of ['leftKnee','rightKnee']){const h=snapshot.health[key];if(!h||!['healthy','sprain','bruise','cut'].includes(h.type)||!Number.isFinite(h.severity)||h.severity<0||h.severity>1||(h.type==='healthy'&&h.severity!==0))return false;}
 this.mode=snapshot.mode;this.walkTime=snapshot.walkTime;this.targetX=snapshot.targetX;
 for(const key of Object.keys(PARTS)){const b=this.parts[key],s=snapshot.parts[key];b.setTranslation(s.position,true);b.setRotation(s.rotation,true);b.setLinvel(s.velocity,true);b.setAngvel(s.angularVelocity,true);}
 for(const key of ['leftKnee','rightKnee'])this.health[key]={...snapshot.health[key]};
 return true;}

}
export const rigDefinition={parts:PARTS,joints:JOINTS};
