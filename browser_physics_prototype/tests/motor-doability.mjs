import R from '../vendor/rapier.es.js';
await R.init();
function make(){let w=new R.World({x:0,y:-9.81,z:0});w.timestep=1/60;let ground=w.createRigidBody(R.RigidBodyDesc.fixed().setTranslation(0,-.3,0));w.createCollider(R.ColliderDesc.cuboid(50,.3,2),ground);
 const torso=w.createRigidBody(R.RigidBodyDesc.dynamic().setTranslation(0,1.5,0).enabledRotations(false,false,true).enabledTranslations(true,true,false));w.createCollider(R.ColliderDesc.capsule(.38,.17).setCollisionGroups(0x00020001),torso);
 const limb=w.createRigidBody(R.RigidBodyDesc.dynamic().setTranslation(.25,1.2,0).enabledRotations(false,false,true).enabledTranslations(true,true,false));w.createCollider(R.ColliderDesc.capsule(.22,.09).setCollisionGroups(0x00020001),limb);
 const joint=w.createImpulseJoint(R.JointData.revolute({x:.25,y:-.08,z:0},{x:0,y:.22,z:0},{x:0,y:0,z:1}),torso,limb,true);return {w,torso,limb,joint};}
for(const k of [0,4,15,60,250]){const {w,torso,limb,joint}=make();joint.configureMotorPosition(1.05,k,k===0?0:Math.sqrt(k)*1.5);for(let i=0;i<120;i++)w.step();let a=torso.rotation(),b=limb.rotation();let deg=(q)=>Math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z));console.log('motor',k,'torso',deg(a).toFixed(3),'limb',deg(b).toFixed(3),'relative',(deg(b)-deg(a)).toFixed(3),'pos',limb.translation().y.toFixed(3));}
