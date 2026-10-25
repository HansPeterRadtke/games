// Independent geometry-only visibility comparison across frozen SceneEval text
// proposals. Actual PRSE GameCore / Rapier world raycasts, not image heuristics.
// Observer locations are fixed investigator-defined viewpoints, NOT human play.
import {writeFileSync,readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {PRSELoop,geometryIssues} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEPhysicalObserver} from './prse_physical_observer.mjs';

await initializePhysics();
const privateDir='/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility/';
const tag=process.argv.find(x=>x.startsWith('--output-tag='))?.slice(13)||'v1';
if(!/^[a-z][a-z0-9-]{0,30}$/.test(tag))throw Error('Invalid replay tag');
const original=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const subsets={
 human:original.slice(0,100),
 assisted:original.filter((p,i)=>i>=100&&(i-100)%4===0).slice(0,100)
};
const views=[
 {x:-27,y:1.5,z:11.8},
 {x:-32.8,y:1.5,z:7.9},
 {x:-21.0,y:1.5,z:7.9},
 {x:-32.8,y:1.5,z:15.7},
 {x:-21.0,y:1.5,z:15.7}
];
function observerIsClear(world,eye){
 // Check the actual Rapier collision shape rather than guessed bounding boxes.
 let intersect=false;
 world.game.world.intersectionsWithPoint(eye,()=>{intersect=true;return false;});
 return !intersect;
}
const all=[];
const start=performance.now();
for(const [part,proposals]of Object.entries(subsets)){
 const scores=[];
 for(const p of proposals){
  const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
  const row={id:p.sourceId,sourceSubset:part,created:layout.accepted&&layout.scene.entities.length>12,
   views:0,objectsInRadius:0,visibleWithRay:0,occludedByCollider:0,
   roomWallBlockers:0,furnitureBlockers:0,untrackedWorldBlockers:0,
   physicsRayQueries:0,invalidViews:0,perceptualEvents:0,
   falsePositiveTypes:{}};
  if(!layout.accepted||geometryIssues(layout.scene).length||!row.created){scores.push(row);continue;}
  let w=null;
  try{
   w=new PRSELoop(layout.scene);w.tick(18);
   const watcher=new PRSEPhysicalObserver(w,{visibilityRadius:9.0});
   const t0=watcher.occlusionQueries;
   for(const eye of views){
    if(!observerIsClear(w,eye)){row.invalidViews++;continue;}
    row.views++;
    for(const e of layout.scene.entities){
     if(e.source==='provisional_3D_room_boundary'||e.state?.destroyed)continue;
     const d=watcher.isVisible(e.id,eye,{mode:'distance',radius:9});
     if(!d.visible)continue;
     row.objectsInRadius++;
     const r=watcher.isVisible(e.id,eye,{mode:'ray',radius:9});
     if(r.visible){row.visibleWithRay++;continue;}
     if(r.reason==='occluded_by_physical_collision'){
      row.occludedByCollider++;
      const blocker=r.blocking?.by;
      if(blocker?.includes('-wall-'))row.roomWallBlockers++;
      else if(blocker==='core_world_collider')row.untrackedWorldBlockers++;
      else row.furnitureBlockers++;
      row.falsePositiveTypes[e.kind]=(row.falsePositiveTypes[e.kind]||0)+1;
     }
    }
   }
   row.physicsRayQueries=watcher.occlusionQueries-t0;
  }catch(e){row.failure=String(e.message).slice(0,150);}
  finally{w?.dispose();}
  scores.push(row);
 }
 const sum={
  descriptions:scores.length,
  physicallyAccepted:scores.filter(x=>x.created&&!x.failure).length,
  validObserverViews:scores.reduce((s,x)=>s+x.views,0),
  rejectedObserverViewInsideCollider:scores.reduce((s,x)=>s+x.invalidViews,0),
  distanceVisibleObjectObservations:scores.reduce((s,x)=>s+x.objectsInRadius,0),
  rayConfirmedVisibleObjectObservations:scores.reduce((s,x)=>s+x.visibleWithRay,0),
  blockedAsOccluded:scores.reduce((s,x)=>s+x.occludedByCollider,0),
  blockedByRoomWall:scores.reduce((s,x)=>s+x.roomWallBlockers,0),
  blockedByFurniture:scores.reduce((s,x)=>s+x.furnitureBlockers,0),
  blockedByOtherCoreCollider:scores.reduce((s,x)=>s+x.untrackedWorldBlockers,0),
  actualRaycasts:scores.reduce((s,x)=>s+x.physicsRayQueries,0),
  failures:scores.filter(x=>x.failure).length
 };
 sum.distanceOnlyFalsePositiveFraction=sum.distanceVisibleObjectObservations?
  sum.blockedAsOccluded/sum.distanceVisibleObjectObservations:0;
 all.push({part,sum,rows:scores});
}
const elapsed=performance.now()-start;
const full={metadata:{kind:'Source-derived, manually fixed camera positions and actual GameCore/Rapier raycasts',
  originalSource:'SceneEval-500 v250610 external descriptions, not copied into output',
  scope:'No visibility human ground truth, no camera facing/FOV or sensory audio, occluders approximate provisional geometry',
  objectMeaning:'Ray first-hit is an exact collider hit in the provisional scene, not proof the original intended layout is correct',
  sampleMethod:'same saved text-only source proposals and deterministic layout settings, 100 human and 100 assisted IDs',
  views:'center and four fixed interior viewpoints, max radius 9 m; observer colliders excluded if viewpoint embedded',
  reproducibility:'low priority CPU, real physics step state, preserved source and result hashes'},elapsedMs:+elapsed.toFixed(1),groups:all};
const path=privateDir+'prse_occlusion_raw_'+tag+'.json';
writeFileSync(path,JSON.stringify(full,null,2)+'\n',{flag:'wx',mode:0o600});
const summary={metadata:{...full.metadata,rawSHA256:createHash('sha256').update(readFileSync(path)).digest('hex'),
 privateRawData:path},elapsedMs:full.elapsedMs,
 groups:all.map(({part,sum})=>({part,...sum}))};
writeFileSync(new URL('prse_occlusion_200_aggregate_'+tag+'.json',import.meta.url),
 JSON.stringify(summary,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(summary.groups));
