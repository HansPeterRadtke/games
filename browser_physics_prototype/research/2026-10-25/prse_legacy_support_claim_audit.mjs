// Independent 3D physical support audit of the EXISTING PRSE textual observer.
// Older PRSELoop.describe() trusts entity.supportId when saying "resting on"
// without rechecking real Rapier contact. Audit that source of unsupported prose
// before changing any implementation, across the frozen 200 SceneEval scenes.
//
// All raw per-scene external source detail stays on private Nitro storage.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import{createHash}from'node:crypto';
import{initializePhysics}from'../../physics-core.js';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
await initializePhysics();
const sample=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+4*i)];
const ROOT='/data/var/games/prse_semantic_research/runs/2026-10-25-current-document';
mkdirSync(ROOT,{recursive:true,mode:0o700});
export function nativeSupportEvidence(loop,child,parent){
 const c=loop.active.get(child.id),p=loop.active.get(parent?.id);
 if(!c||!p||!c.numColliders()||!p.numColliders())return {truth:'unknown',reason:'one_or_both_unmaterialized'};
 if(parent.shape==='sphere')return {truth:'unknown',reason:'sphere_is_not_verified_planar_support'};
 const foot=Math.abs(child.position.x-parent.position.x)+child.size.x/2<=parent.size.x/2+.02
   &&Math.abs(child.position.z-parent.position.z)+child.size.z/2<=parent.size.z/2+.02;
 const verticalGap=child.position.y-child.size.y/2-parent.position.y-parent.size.y/2;
 let actual=false;
 for(let i=0;i<c.numColliders();i++)
  for(let j=0;j<p.numColliders();j++)
   loop.game.world.contactPair(c.collider(i),p.collider(j),manifold=>{
    if(manifold.numContacts()>0)actual=true;
   });
 const geometricallySupported=foot&&Math.abs(verticalGap)<.055;
 if(c.isDynamic()&&geometricallySupported&&!actual)
  return {truth:'unknown',reason:'support_contact_not_yet_verified',foot,verticalGap};
 return {truth:geometricallySupported&&(actual||!c.isDynamic())?'true':'false',
  reason:'AABB_top_face_and_native_Rapier_contact',foot,verticalGap,actual};
}
const raw=[],summary={scenes:ids.length,accepted:0,rejected:0,
 savedNonFloorSupportClaims:0,physicalTrue:0,physicalFalse:0,physicalUnknown:0,
 staleTextWouldSaySupported:0,staleTextAmongPhysicalFalse:0,
 staleTextAmongPhysicalUnknown:0,unsupportedByReason:{}};
for(const id of ids){
 const prop=sample[id],layout=repairScene(prop,{maxSweeps:2,maxAttemptsPerScene:150});
 const row={id,status:layout.accepted?'accepted':'rejected',supportClaims:[]};
 if(!layout.accepted){summary.rejected++;raw.push(row);continue;}
 let loop=null;
 try{
  loop=new PRSELoop(layout.scene);loop.tick(24);summary.accepted++;
  for(const c of loop.scene.entities){
   if(!c.supportId||c.supportId==='floor'||c.source==='provisional_3D_room_boundary'||c.state.destroyed)continue;
   const parent=loop.entities.get(c.supportId);
   if(!parent)continue;
   const evidence=nativeSupportEvidence(loop,c,parent);
   const claimed=loop.describe([c.id]).includes('resting on '+parent.name);
   summary.savedNonFloorSupportClaims++;
   if(evidence.truth==='true')summary.physicalTrue++;
   if(evidence.truth==='false')summary.physicalFalse++;
   if(evidence.truth==='unknown')summary.physicalUnknown++;
   if(claimed)summary.staleTextWouldSaySupported++;
   if(claimed&&evidence.truth==='false')summary.staleTextAmongPhysicalFalse++;
   if(claimed&&evidence.truth==='unknown')summary.staleTextAmongPhysicalUnknown++;
   if(evidence.truth!=='true')summary.unsupportedByReason[evidence.reason]=(summary.unsupportedByReason[evidence.reason]||0)+1;
   row.supportClaims.push({childID:c.id,parentID:parent.id,actual:evidence,
    oldTextClaimesSupported:claimed,previousText:loop.describe([c.id])});
  }
 }finally{loop?.dispose();}
 raw.push(row);
}
const path=ROOT+'/prse_legacy_describe_support_claims_200_raw_v1.json';
writeFileSync(path,JSON.stringify({summary,source:'Frozen existing SceneEval source prompts, same scene geometry, actual native 3D Rapier contacts',cases:raw},null,2)+'\n',{flag:'wx',mode:0o600});
const digest=createHash('sha256').update(readFileSync(path)).digest('hex');
writeFileSync(new URL('prse_legacy_support_claim_audit_200_aggregate_v1.json',import.meta.url),
 JSON.stringify({summary,source:'Actual GameCore Rapier, source IDs 0:99 and 100:496 every fourth',
  nonGenerative:true,privateRawSHA256:digest,privateRawPath:path},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(summary));
