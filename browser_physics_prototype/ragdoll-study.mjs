import R from './vendor/rapier.es.js';
await R.init();const world=new R.World({x:0,y:-9.81,z:0});world.timestep=1/60;
const floor=world.createRigidBody(R.RigidBodyDesc.fixed().setTranslation(0,-.4,0));world.createCollider(R.ColliderDesc.cuboid(20,.4,2),floor);
function part(x,y,length){const b=world.createRigidBody(R.RigidBodyDesc.dynamic().setTranslation(x,y,0));world.createCollider(R.ColliderDesc.capsule(length/2,.1),b);return b;}
const torso=part(0,2.6,.7),leg=part(.05,1.7,.8),arm=part(.33,2.48,.65);
world.createImpulseJoint(R.JointData.spherical({x:0,y:-.43,z:0},{x:0,y:.5,z:0}),torso,leg,true);
world.createImpulseJoint(R.JointData.spherical({x:.14,y:.3,z:0},{x:0,y:.37,z:0}),torso,arm,true);
for(let i=0;i<180;i++)world.step();for(const [name,b] of [['torso',torso],['leg',leg],['arm',arm]]){const p=b.translation();if(!Number.isFinite(p.x)||!Number.isFinite(p.y))throw Error('invalid body '+name);console.log(name,p)}
console.log('RAGDOLL_JOINT_STUDY_OK');
