// Independent adversarial diagnosis of the already preserved 62-cm PRSE
// offscreen scheduled-action failure in externally authored source ID 27.
// Compare four paths from exactly the same verified native GameCore state:
//
// A: uninterrupted authoritative physics.
// B: full physics, but save/reload at scheduled action times.
// C: contact-verified offscreen settling, without boundary save/reload.
// D: contact-verified offscreen settling AND boundary save/reload.
//
// Do NOT change the original failing raw result; preserve this separate
// diagnostic, including the first checkpoint where trajectories diverge.
import {writeFileSync}from'node:fs';
import {initializePhysics}from'../../physics-core.js';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {physicallySettleThenUnload}from'./prse_offscreen_motion_settling.mjs';
await initializePhysics();
const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[27];
const scene=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
if(!scene.accepted)throw Error('Source fixture rejected');
let starting=new PRSELoop(scene.scene);starting.tick(18);
const dynamic=scene.scene.entities.find(e=>e.kind==='cup'&&e.body==='dynamic');
if(!dynamic)throw Error('Original moving cup identity missing');
starting.applyImpulse(dynamic.id,{x:1.1,y:.35,z:.55});
const seed=JSON.parse(JSON.stringify(starting.snapshot()));starting.dispose();
const cases={};
for(const id of ['uninterrupted','full_saved','coarse_no_save','coarse_saved']){
 const r=PRSELoop.restore(seed);
 if(!r.ok)throw Error('Cannot clone original world');
 cases[id]={loop:r.loop,segments:[],mode:id};
}
const vecDist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const quatDist=(a,b)=>2*Math.acos(Math.max(-1,Math.min(1,Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w))));
const pose=l=>{
 const b=l.active.get(dynamic.id);
 if(!b)throw Error('Target body not active at action boundary');
 return {position:{...b.translation()},velocity:{...b.linvel()},rotation:{...b.rotation()},
  angular:{...b.angvel()},supportId:l.entities.get(dynamic.id).supportId,worldTime:l.time};
};
const impulses=[{tick:150,v:{x:4,y:1.1,z:1.5}},{tick:260,v:{x:-1.6,y:.45,z:1}}];
const checkpoints=[],segments=[150,110,100];
let already=0;
for(let i=0;i<segments.length;i++){
 const n=segments[i],current={tick:already+n,mode:{}};
 for(const [key,c] of Object.entries(cases)){
  let report=null;
  if(key.startsWith('coarse'))report=physicallySettleThenUnload(c.loop,{
   totalTicks:n,maxPhysicalTicks:Math.min(120,n),requiredQuietTicks:20
  });
  else c.loop.tick(n);
  const pre=pose(c.loop);
  if(i<impulses.length&&key!=='uninterrupted'&&(key==='full_saved'||key==='coarse_saved')){
   const checkpoint=JSON.parse(JSON.stringify(c.loop.snapshot()));
   const r=PRSELoop.restore(checkpoint);
   if(!r.ok)throw Error('Reference save/load failed');
   const old=c.loop;c.loop=r.loop;old.dispose();
  }
  const reloaded=pose(c.loop);
  current.mode[key]={beforeSave:pre,afterSave:reloaded,
   policy:report?{offloaded:report.offloaded,physicalTicks:report.physicalTicks,
     skippedTicks:report.skippedPhysicsTicks,reason:report.reason}:null};
  if(i<impulses.length&&!c.loop.applyImpulse(dynamic.id,impulses[i].v))
   throw Error('Scheduled physical action failed');
 }
 const control=current.mode.uninterrupted.afterSave;
 for(const [key,v]of Object.entries(current.mode)){
  v.differenceFromUninterrupted={
   positionMeters:vecDist(v.afterSave.position,control.position),
   velocityMetersPerSecond:vecDist(v.afterSave.velocity,control.velocity),
   rotationRadians:quatDist(v.afterSave.rotation,control.rotation)};
 }
 checkpoints.push(current);
 already+=n;
}
for(const c of Object.values(cases))c.loop.dispose();
const output={metadata:{sourceId:27,source:'Real SceneEval authored room with movable cup; external gold labels never used',
 originalFailure:'prse_offscreen_action_schedule_human_raw_v1.json, source27, cup, 0.62 m',
 investigation:'Uninterrupted native PRSE GameCore, pure save/reload, offscreen no reload, offscreen with reload, from identical starting GameCore snapshot',
 narrativeNote:'This diagnoses physical state differences; no human viewing data or model inference'},checkpoints};
writeFileSync(new URL('prse_offscreen_queued_cup_62cm_failure_diagnostic_v1.json',import.meta.url),
 JSON.stringify(output,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(checkpoints.map(r=>({tick:r.tick,...Object.fromEntries(Object.entries(r.mode).map(([k,v])=>
 [k,{error:v.differenceFromUninterrupted.positionMeters,rotation:v.differenceFromUninterrupted.rotationRadians,
 offloaded:v.policy?.offloaded,skipped:v.policy?.skippedTicks,
 prePostReloadMove:vecDist(v.beforeSave.position,v.afterSave.position)}]))}))));
