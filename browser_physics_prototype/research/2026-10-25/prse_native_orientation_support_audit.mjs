// Independent source-neutral audit: whether PRSE's current fact projection
// calls a support/near relation TRUE from stale axis-aligned semantic bounds
// when authoritative Rapier bodies are rotated, tilted or multicollider.
//
// Same exact frozen 197 accepted externally authored SceneEval source scenes.
// Predeclared four impulse vectors, real native Rapier/GameCore time stepping.
// All source proposals, positions, rotations, contact manifolds come from the
// current engine. No author label, model inference, GPU or production edits.
//
// We measure discrepancies, not automatically redefine all tilted contacts:
// a tilted solid may still be physically supported and needs oriented
// contact normal / shape analysis. Candidate current 'on' proof is flagged
// UNKNOWN when tilt exceeds .12 rad (~7 deg), not falsely proved TRUE/FALSE.
// A corrected physical projection will be designed only if actual evidence
// warrants it.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {measureRelation}from'./prse_grounded_relation_narration.mjs';
import {PRSESourceRevision}from'./prse_source_revision_story.mjs';
import {PRSECurrentSemanticDocument}from'./prse_current_semantic_document.mjs';
await initializePhysics();
const dir='/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit';
mkdirSync(dir,{recursive:true,mode:0o700});
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+4*i)];
const orientations=[
 {label:'east_up',x:4,y:1.1,z:.5},
 {label:'west_up',x:-4,y:1.1,z:.5},
 {label:'south_up',x:.5,y:1.1,z:4},
 {label:'north_low',x:1.2,y:.9,z:-3.5}
];
const start=performance.now(),rows=[];
function normUp(q){
 const n=Math.hypot(q.x,q.y,q.z,q.w);
 if(n<.5||!Number.isFinite(n))return NaN;
 const x=q.x/n,z=q.z/n;
 return Math.acos(Math.max(-1,Math.min(1,1-2*(x*x+z*z))));
}
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
function physical(l,a,b){
 const A=l.active.get(a.id),B=l.active.get(b.id);
 if(!A||!B)return {status:'unknown',cause:'unloaded'};
 if(!A.numColliders()||!B.numColliders())return {status:'unknown',cause:'no_colliders'};
 const p=A.translation(),q=B.translation(),ar=A.rotation(),br=B.rotation();
 const childTilt=normUp(ar),supportTilt=normUp(br);
 const localDiffMax=Math.max(dist(p,a.position),dist(q,b.position));
 let contactAny=false,contactFirst=false;
 for(let i=0;i<A.numColliders();i++)for(let j=0;j<B.numColliders();j++)
 l.game.world.contactPair(A.collider(i),B.collider(j),m=>{
  if(m.numContacts()>0){contactAny=true;if(i===0&&j===0)contactFirst=true;}
 });
 if(!Number.isFinite(childTilt)||!Number.isFinite(supportTilt))
  return {status:'unknown',cause:'bad_rotation',childTilt,supportTilt,contactAny,contactFirst,localDiffMax};
 if(childTilt>.12||supportTilt>.12)
  return {status:'unknown',cause:'tilted_or_rotated_support_shape_needs_oriented_test',childTilt,supportTilt,contactAny,contactFirst,localDiffMax};
 if(a.shape==='sphere'||b.shape==='sphere')
  return {status:'unknown',cause:'round_contact_geometry_not_planar',childTilt,supportTilt,contactAny,contactFirst,localDiffMax};
 const fits=Math.abs(p.x-q.x)+a.size.x/2<=b.size.x/2+.015 &&
  Math.abs(p.z-q.z)+a.size.z/2<=b.size.z/2+.015;
 const plane=Math.abs((p.y-a.size.y/2)-(q.y+b.size.y/2))<=.055;
 if(A.isDynamic()&&!contactAny&&fits&&plane)
  return {status:'unknown',cause:'native_contact_missing',fits,plane,childTilt,supportTilt,contactAny,contactFirst,localDiffMax};
 return {status:(fits&&plane&&(contactAny||!A.isDynamic()))?'true':'false',
  cause:'native_rigidbody_translation_and_upright_contact',
  fits,plane,childTilt,supportTilt,contactAny,contactFirst,localDiffMax};
}
for(const id of ids){
 const source=proposals[id],layout=repairScene(source,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!layout.accepted||geometryIssues(layout.scene).length){rows.push({sourceId:id,status:'original_scene_not_accepted'});continue;}
 for(const impulse of orientations){
  let l=null;
  const out={sourceId:id,impulse:impulse.label,status:'started'};
  try{
   l=new PRSELoop(layout.scene);l.tick(36);
   const on=source.relations.filter(r=>r.kind==='object'&&r.type==='on');
   const sourceSelected=on.find(r=>{
    const a=l.scene.entities.filter(e=>e.kind===r.a&&e.source!=='provisional_3D_room_boundary');
    return a.length===1&&a[0].body==='dynamic';
   });
   const candidate=sourceSelected?l.scene.entities.find(e=>e.kind===sourceSelected.a):
    l.scene.entities.find(e=>e.body==='dynamic'&&!e.state?.destroyed);
   out.initialSourceOnCount=on.length;
   out.activeDynamicEntityCount=l.scene.entities.filter(e=>e.body==='dynamic'&&!e.state?.destroyed).length;
   if(candidate){
    out.movedBodyId=candidate.id;
    if(!l.applyImpulse(candidate.id,impulse))throw Error('GameCore physical impulse failed');
    l.tick(160);
   }
   const evaluations=[];
   for(const r of on){
    const a=l.scene.entities.filter(e=>e.kind===r.a&&e.source!=='provisional_3D_room_boundary');
    const b=l.scene.entities.filter(e=>e.kind===r.b&&e.source!=='provisional_3D_room_boundary');
    if(a.length!==1||b.length!==1||a[0]===b[0]){evaluations.push({type:'source_on',status:'not_unique'});continue;}
    const older=measureRelation(l,r),native=physical(l,a[0],b[0]);
    evaluations.push({type:'source_on',a:r.a,b:r.b,
     old:older.truth,new:native.status,cause:native.cause,
     childTilt:native.childTilt,supportTilt:native.supportTilt,
     contactAny:native.contactAny,contactFirst:native.contactFirst,
     localDiffMax:native.localDiffMax});
   }
   // Physical-only source supportId relations can be present without any
   // parsed original source "on" clause. Same native geometry reliability.
   for(const a of l.scene.entities){
    if(!a.supportId||a.supportId==='floor'||a.state?.destroyed)continue;
    const b=l.entities.get(a.supportId);
    if(!b)continue;
    const native=physical(l,a,b);
    const legacy=(()=>{const A=l.active.get(a.id),B=l.active.get(b.id);if(!A||!B)return'unknown';
     const f=Math.abs(a.position.x-b.position.x)+a.size.x/2<=b.size.x/2+.015&&
     Math.abs(a.position.z-b.position.z)+a.size.z/2<=b.size.z/2+.015;
     const h=Math.abs(a.position.y-a.size.y/2-b.position.y-b.size.y/2)<.055;
     let c=false;l.game.world.contactPair(A.collider(0),B.collider(0),m=>{
      if(m.numContacts()>0)c=true;});
     if(f&&h&&A.isDynamic()&&!c)return 'unknown';
     return f&&h&&(c||!A.isDynamic())?'true':'false';
    })();
    evaluations.push({type:'physical_support',a:a.id,b:b.id,old:legacy,
     new:native.status,cause:native.cause,childTilt:native.childTilt,
     supportTilt:native.supportTilt,contactAny:native.contactAny,contactFirst:native.contactFirst,
     localDiffMax:native.localDiffMax});
   }
   out.status='measured';
   out.relations=evaluations;
  }catch(e){out.status='failed';out.reason=String(e.message).slice(0,220);}
  finally{l?.dispose();}
  rows.push(out);
 }
}
const measured=rows.filter(r=>r.status==='measured'),all=measured.flatMap(r=>r.relations);
const categorized=label=>all.filter(x=>x.type===label);
const summary={
 inputExternalSourceScenes:ids.length,
 originalGeometryAccepted:ids.length-rows.filter(x=>x.status==='original_scene_not_accepted').length,
 physicalWorldActionConditions:measured.length,
 physicallyActedConditions:measured.filter(x=>x.movedBodyId).length,
 physicallyActedUniqueSources:new Set(measured.filter(x=>x.movedBodyId).map(x=>x.sourceId)).size,
 runtimeFailures:rows.filter(x=>x.status==='failed').length,
 sourceOnUniqueRelationsEvaluated:categorized('source_on').filter(x=>x.old).length,
 physicalSupportRelationsEvaluated:categorized('physical_support').length,
 oldCurrentFactsTrue:all.filter(x=>x.old==='true').length,
 oldCurrentFactsTrueButNativeUprightUnknown:all.filter(x=>x.old==='true'&&x.new==='unknown').length,
 oldCurrentFactsTrueButNativeGeometryFalse:all.filter(x=>x.old==='true'&&x.new==='false').length,
 oldCurrentFactsUnknownButNativePhysicallyTrue:all.filter(x=>x.old==='unknown'&&x.new==='true').length,
 oldCurrentFactsFalseButNativePhysicallyTrue:all.filter(x=>x.old==='false'&&x.new==='true').length,
 oldCurrentFactsTrueOnTiltedBody:all.filter(x=>x.old==='true'&&x.cause==='tilted_or_rotated_support_shape_needs_oriented_test').length,
 oldCurrentFactsTrueContactOnlyOnLaterCollider:all.filter(x=>x.old==='true'&&x.contactAny&&!x.contactFirst).length,
 maximumMetadataVsNativeTranslationDistance:Math.max(0,...all.map(x=>x.localDiffMax||0)),
 rotationGeometricUncertainty:all.filter(x=>x.cause==='tilted_or_rotated_support_shape_needs_oriented_test').length,
 wallSeconds:+((performance.now()-start)/1000).toFixed(2),
 limitation:'Independent conservative native orientation safety audit of generated AABB proxies, not arbitrary 3D meshes; all source semantics already untrusted as possible annotations' };
const file=dir+'/prse_native_orientation_support_audit_197x4_raw_v1.json';
const payload={metadata:{
 source:'Frozen first100 human+systematically sampled100 assisted SceneEval descriptions, preexisting PRSELoop/GameCore real native Rapier world',
 physicalInputs:orientations,
 noGoldAnnotationsOrModels:true,
 originalWorldAndNarrowSourceRelationStatusSeparatelyMeasured:true},summary,rows};
writeFileSync(file,JSON.stringify(payload,null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_native_orientation_support_197x4_aggregate_v1.json',import.meta.url),
 JSON.stringify({metadata:{...payload.metadata,privateRawSHA256:createHash('sha256').update(readFileSync(file)).digest('hex')},
  summary,
  discrepantCases:rows.filter(r=>r.status==='measured'&&r.relations.some(x=>
   x.old==='true'&&x.new!=='true')).map(r=>({
    sourceId:r.sourceId,action:r.impulse,
    mismatches:r.relations.filter(x=>x.old==='true'&&x.new!=='true').map(x=>({
     type:x.type,old:x.old,new:x.new,cause:x.cause}))}))},null,2)+'\n',{flag:'wx'});
console.log('NATIVE_PHYSICAL_RELATION_ORIENTATION_AUDIT',JSON.stringify(summary));
