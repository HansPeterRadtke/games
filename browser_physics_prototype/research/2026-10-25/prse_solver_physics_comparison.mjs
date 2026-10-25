// Frozen text proposal -> baseline greedy vs bounded, geometry-valid deterministic
// constraint-repair candidate -> *same* PRSE GameCore Rapier 3D physics and save.
// No gold labels enter layout or selection. Source text stays owner-private.
// Predeclared: max 2 sweeps, 150 candidates per scene; 100 human vs every 4th
// assisted SceneEval example. Historical baseline raw file is not rewritten.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {performance} from 'node:perf_hooks';
import {createHash} from 'node:crypto';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,geometryIssues} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {validRelation} from '../2026-10-24/prse_constraint_layout.mjs';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';

await initializePhysics();
const params=new Set(process.argv.slice(2));
const sample=params.has('--assisted')?'assisted':params.has('--human')?'human':null;
if(!sample)throw Error('Usage: --human or --assisted');
const original=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json'));
const indexed=sample==='human'?original.proposalsAll500.slice(0,100):
 original.proposalsAll500.filter((p,i)=>i>=100&&(i-100)%4===0).slice(0,100);
if(indexed.length!==100)throw Error('Wrong sample');
const rawDir='/data/var/games/prse_semantic_research/runs/2026-10-25-relation-solver';
mkdirSync(rawDir,{recursive:true,mode:0o700});
const fullOutput=join(rawDir,'prse_solver_'+sample+'_100_raw_v1.json');
const aggregateFile=new URL('prse_solver_'+sample+'_100_aggregate_v1.json',import.meta.url);
const result=[],started=performance.now();
function outcomeFor(p){
 const before=performance.now(),proposed=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const rec={id:p.sourceId,status:'not_run',baselineValid:proposed.baselineValid,
  repairAccepted:proposed.accepted,
  proposals:proposed.sourceConstraints,
  attempts:proposed.attempts,
  editedConstraints:proposed.amended.length,
  poseShiftMetres:+proposed.summedPositionChangeMetres.toFixed(3),
  initialGroundedCount:proposed.before.grounded,
  finalProposedGroundedCount:proposed.after.grounded,
  initialViolatedCount:proposed.before.violated,
  finalProposedViolatedCount:proposed.after.violated,
  relations:[],initialErrors:proposed.remainingInvalidIssues.length};
 if(!proposed.accepted||geometryIssues(proposed.scene).length){
  rec.status='invalid_scene_rejected';rec.ms=+(performance.now()-before).toFixed(2);
  return rec;
 }
 const objects=proposed.scene.entities.filter(e=>e.source!=='provisional_3D_room_boundary');
 if(!objects.length){rec.status='no_entities';return rec;}
 let game=null,save=null;
 try{
  game=new PRSELoop(proposed.scene);
  const ids=objects.map(e=>e.id);
  game.tick(18);
  const relations=p.relations.map(r=>({kind:r.kind,type:r.type,a:r.a,b:r.b,
    result:validRelation(r,game.scene.entities.filter(e=>e.source!=='provisional_3D_room_boundary'))}));
  rec.relations=relations;
  rec.physicallyGroundedCount=relations.filter(r=>r.result===true).length;
  rec.physicallyViolatedCount=relations.filter(r=>r.result===false).length;
  rec.physicallyUnsupportedCount=relations.filter(r=>r.result===null).length;
  const state=JSON.parse(JSON.stringify(game.snapshot()));
  const restored=PRSELoop.restore(state);
  if(!restored.ok)throw Error('GameCore-backed wrapper reload rejected');
  save=restored.loop;
  rec.stableIds=ids.every(id=>save.entities.has(id));
  rec.sourceProsePreserved=save.scene.prose===p.text;
  rec.maxReloadPositionError=Math.max(...ids.map(id=>{
   const x=game.entities.get(id).position,y=save.entities.get(id).position;
   return Math.hypot(x.x-y.x,x.y-y.y,x.z-y.z);
  }));
  if(!(rec.stableIds&&rec.sourceProsePreserved&&rec.maxReloadPositionError<.001))
   throw Error('State continuity failed');
  rec.status='materialized_and_reloaded';
 }catch(e){rec.status='runtime_failed';rec.error=String(e.message).slice(0,130);}
 finally{save?.dispose();game?.dispose();}
 rec.ms=+(performance.now()-before).toFixed(2);
 return rec;
}
for(const p of indexed)result.push(outcomeFor(p));
const completed=result.filter(r=>r.status==='materialized_and_reloaded');
const summary={
 sample,sourceDescriptions:100,
 physicallyMaterialized:completed.length,
 rejectedInvalid:result.filter(r=>r.status==='invalid_scene_rejected').length,
 noEntities:result.filter(r=>r.status==='no_entities').length,
 runtimeFailure:result.filter(r=>r.status==='runtime_failed').length,
 stableOriginalIdentitiesAndProse:completed.filter(x=>x.stableIds&&x.sourceProsePreserved).length,
 parsedConstraints:result.reduce((v,x)=>v+x.proposals,0),
 beforeGreedySatisfied:result.reduce((v,x)=>v+x.initialGroundedCount,0),
 afterProposedSatisfied:result.reduce((v,x)=>v+x.finalProposedGroundedCount,0),
 afterActualPhysicsSatisfied:completed.reduce((v,x)=>v+x.physicallyGroundedCount,0),
 afterActualPhysicsViolated:completed.reduce((v,x)=>v+x.physicallyViolatedCount,0),
 afterActualPhysicsUnsupported:completed.reduce((v,x)=>v+x.physicallyUnsupportedCount,0),
 sceneCorrections:result.reduce((v,x)=>v+x.editedConstraints,0),
 correctedScenes:result.filter(x=>x.editedConstraints>0).length,
 totalCandidateChecks:result.reduce((v,x)=>v+x.attempts,0),
 wallTimeMs:+(performance.now()-started).toFixed(1)
};
const data={metadata:{
 method:'deterministic local discrete constraint search on fixed text-only proposals, then actual native PRSE GameCore/Rapier dynamics and wrapper snapshot',
 noGoldUsed:true,source:'official SceneEval-500 v250610 external descriptions; human first100 or every4th assisted100',
 humanHoldout:'NOT preregistered; corpus partially inspected during earlier studies',
 limits:'one physical subscene per text, fixed approximate furniture dimensions, no occlusion/visual material truth, only typed relation checks',
 maxSweeps:2,maxCandidateAttemptsPerScene:150,runRevision:1},summary,results:result};
writeFileSync(fullOutput,JSON.stringify(data,null,2)+'\n',{flag:'wx',mode:0o600});
const safe={metadata:{...data.metadata,privateRawResultFile:fullOutput,
 rawSHA256:createHash('sha256').update(readFileSync(fullOutput)).digest('hex')},
 summary,
 statusCounts:result.reduce((d,r)=>(d[r.status]=(d[r.status]||0)+1,d),{}),
 beforeAfterById:result.map(r=>({id:r.id,status:r.status,greedy:r.initialGroundedCount,
  optimized:r.finalProposedGroundedCount,physicallyGrounded:r.physicallyGroundedCount??null,
  violations:r.physicallyViolatedCount??null,
  edits:r.editedConstraints,saveReliable:r.stableIds&&r.sourceProsePreserved}))};
writeFileSync(aggregateFile,JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(summary));
