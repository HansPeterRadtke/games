// Solver-level forensic comparison of native Rapier World binary serialization
// vs PRSE's current JSON rigid-body reconstruction for already documented
// source-derived contact-trajectory discrepancies.
//
// The actual physics authority is Rapier in both arms. This controlled study
// deliberately steps only native Rapier World after the snapshot so it can
// isolate contact/solver serialization, NOT pretend to replay the entire
// GameCore character model, narrative state, observer ledger or scheduled time.
import RAPIER from '../../vendor/rapier.es.js';
import {writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {initializePhysics} from '../../physics-core.js';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
await initializePhysics();
const props=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const cases=[{id:27,kind:'cup'},{id:91,kind:'vase'},{id:140,kind:'ball'}];
const bounds=[{tick:150,impulse:{x:4,y:1.1,z:1.5},steps:110},
 {tick:260,impulse:{x:-1.6,y:.45,z:1},steps:100}];
const vecDist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const quatDiff=(a,b)=>2*Math.acos(Math.min(1,Math.max(-1,Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w))));
const score=(base,other)=>({
 locationMeters:vecDist(base.translation(),other.translation()),
 velocityMetersPerSecond:vecDist(base.linvel(),other.linvel()),
 rotationRadians:quatDiff(base.rotation(),other.rotation()),
 angularSpeedRadPerSec:vecDist(base.angvel(),other.angvel())
});
const results=[];
for(const spec of cases){
 const plan=repairScene(props[spec.id],{maxSweeps:2,maxAttemptsPerScene:150});
 if(!plan.accepted)throw Error('Previously verified source rejected');
 const holder=new PRSELoop(plan.scene);
 holder.tick(18);
 const target=plan.scene.entities.find(e=>e.kind===spec.kind&&e.body==='dynamic');
 if(!target)throw Error('Original target missing');
 holder.applyImpulse(target.id,{x:1.1,y:.35,z:.55});
 holder.tick(150);
 const serializedBinary=holder.game.world.takeSnapshot();
 const serializedJSON=holder.snapshot();
 const binaryWorld=RAPIER.World.restoreSnapshot(serializedBinary);
 const independentNativeCopy=RAPIER.World.restoreSnapshot(serializedBinary);
 const restored=PRSELoop.restore(JSON.parse(JSON.stringify(serializedJSON)));
 if(!restored.ok)throw Error('PRSE structured JSON could not restore');
 const rebuilt=restored.loop;
 const rawHandle=holder.active.get(target.id).handle;
 const binaryBody=binaryWorld.getRigidBody(rawHandle),
       cloneBody=independentNativeCopy.getRigidBody(rawHandle),
       liveBody=holder.active.get(target.id),
       reconstructed=rebuilt.active.get(target.id);
 if(!binaryBody||!cloneBody)throw Error('Native binary world rigid body handles were not preserved');
 const probe={sourceId:spec.id,bodyType:spec.kind,
  binaryBytes:serializedBinary.length,
  jsonUtf8Bytes:Buffer.byteLength(JSON.stringify(serializedJSON)),
  binarySHA256:createHash('sha256').update(serializedBinary).digest('hex'),
  stages:[{atTick:150,
    nativeBinaryToLive:score(liveBody,binaryBody),
    structuredJSONToLive:score(liveBody,reconstructed),
    binaryReplicas:score(binaryBody,cloneBody)}]};
 try{
  let tick=150;
  for(const phase of bounds){
   for(const body of [liveBody,binaryBody,cloneBody,reconstructed])
    body.applyImpulse(phase.impulse,true);
   for(let i=0;i<phase.steps;i++){
    holder.game.world.step();
    binaryWorld.step();independentNativeCopy.step();rebuilt.game.world.step();
   }
   tick+=phase.steps;
   probe.stages.push({afterTick:tick,
     nativeBinaryToLive:score(liveBody,binaryBody),
     structuredJSONToLive:score(liveBody,reconstructed),
     binaryReplicas:score(binaryBody,cloneBody)});
  }
 }finally{binaryWorld.free();independentNativeCopy.free();rebuilt.dispose();holder.dispose();}
 results.push(probe);
}
const payload={metadata:{kind:'Same authoritative Rapier physics engine, World.takeSnapshot/restoreSnapshot versus current PRSE JSON body rebuild',
 source:'External SceneEval rows 27,91,140 selected from original discrepancies; original raw errors preserved',
 limitation:'Solver-only stepping after snapshot; not replay of full GameCore modules or proof binary format safely loads arbitrary files'},
 results};
writeFileSync(new URL('prse_solver_binary_vs_json_restore_v1.json',import.meta.url),JSON.stringify(payload,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(results.map(r=>({id:r.sourceId,type:r.bodyType,
 binaryBytes:r.binaryBytes,jsonBytes:r.jsonUtf8Bytes,after:r.stages.at(-1)}))));
