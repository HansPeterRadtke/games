// Scheduled causal offscreen physical actions, predeclared in relative game-time
// ticks, compared against uninterrupted authoritative PRSE GameCore/Rapier.
//
// The motion source is a systematic fixed set of previously externally written
// SceneEval descriptions (63 with a real dynamic scene object). The author of
// the present experiment supplies deterministic impulses, not a human player
// or generative LLM. Object IDs, global time, source facts and causality must
// persist across actual save/reload between future actions.
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {createHash}from'node:crypto';
import {performance}from'node:perf_hooks';
import {initializePhysics}from'../../physics-core.js';
import {PRSELoop,geometryIssues}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEGroundedFacts}from'./prse_grounded_relation_narration.mjs';
import {repairScene}from'./prse_relation_local_optimizer.mjs';
import {readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import {playQueuedPhysicalActions}from'./prse_offscreen_physical_action_queue.mjs';
await initializePhysics();

const subset=process.argv.includes('--human')?'human':process.argv.includes('--assisted')?'assisted':null;
if(!subset)throw Error('Specify --human or --assisted');
const privateDir='/data/var/games/prse_semantic_research/runs/2026-10-25-offscreen-motion';
mkdirSync(privateDir,{recursive:true,mode:0o700});
const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const original=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility/prse_observer_event_batch_200_raw_v2.json'));
const cases=original.rows.filter(x=>x.status==='evaluated'&&x.sourceType===subset);
const spec={totalTicks:360,
 initialImpulse:{x:1.1,y:.35,z:.55},
 scheduled:[
  {tick:150,v:{x:4.0,y:1.1,z:1.5}},
  {tick:260,v:{x:-1.6,y:.45,z:1.0}}
 ],
 maxPhysicalTicksPerInterval:120,stableConsecutiveTicks:20,
 forcedSaveAndReloadAtEveryEvent:true,
 sourceKind:'SceneEval official descriptions, fixed source IDs and unchanged parser/geometry proposals',
 provenance:'Synthetic game action queue, NOT player-taught physical skills',
 goldSourceAnnotationsNotUsed:true};
const start=performance.now(),out=[];
const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const quatDiff=(a,b)=>{
 const v=Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w);
 return 2*Math.acos(Math.max(-1,Math.min(1,v)));
};
function physicalView(l){
 const answer=new Map();
 for(const [id,body]of l.active)if(body.isDynamic())
  answer.set(id,{p:{...body.translation()},v:{...body.linvel()},q:{...body.rotation()}});
 return answer;
}
function compare(a,b,ids){
 const aa=physicalView(a),bb=physicalView(b);
 let displacement=0,speedDifference=0,rotation=0;
 for(const id of ids){
  const x=aa.get(id),y=bb.get(id);
  if(!x||!y)throw Error('Required dynamic identity missing from final physical region');
  displacement=Math.max(displacement,distance(x.p,y.p));
  speedDifference=Math.max(speedDifference,distance(x.v,y.v));
  rotation=Math.max(rotation,quatDiff(x.q,y.q));
 }
 return {maxPoseMeters:displacement,maxSpeedDiffMetersPerSecond:speedDifference,maxRotationRadians:rotation};
}
const physicalTypes=new Set(['external_impulse','impact','displaced','rotated','tipped','lost_support','rested_on']);
const seq=loop=>loop.events.filter(e=>physicalTypes.has(e.type)).map(e=>[e.type,...e.ids]);
const truth=(loop,proposal)=>new PRSEGroundedFacts(loop,proposal.relations).current().map(x=>x.truth);
for(let ix=0;ix<cases.length;ix++){
 const c=cases[ix],proposal=p[+c.id];
 const scene=repairScene(proposal,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!scene.accepted||geometryIssues(scene.scene).length)
  throw Error('Previously verified physical input no longer accepted');
 let initial=null,continuous=null,branch=null;
 const item={id:proposal.sourceId,subset,chosenCategory:c.chosenCategory,
  status:'not-started',eventTicks:spec.scheduled.map(x=>x.tick)};
 try{
  initial=new PRSELoop(scene.scene);initial.tick(18);
  const entity=scene.scene.entities.find(e=>e.kind===c.chosenCategory&&e.body==='dynamic');
  if(!entity)throw Error('Chosen actual physical dynamic body not found');
  item.entityId=entity.id;
  if(!initial.applyImpulse(entity.id,spec.initialImpulse))throw Error('Initial GameCore impulse denied');
  const seed=JSON.parse(JSON.stringify(initial.snapshot()));
  const full=PRSELoop.restore(seed),reduced=PRSELoop.restore(seed);
  if(!full.ok||!reduced.ok)throw Error('Initial GameCore seed rejected');
  continuous=full.loop;branch=reduced.loop;
  const ids=[...continuous.active].filter(([id,b])=>b.isDynamic()).map(([id])=>id);
  const scheduled=spec.scheduled.map(x=>({tick:x.tick,id:entity.id,impulse:x.v}));
  let last=0;
  const fullActions=[];
  for(const action of scheduled){
   continuous.tick(action.tick-last);
   const before=continuous.time;
   if(!continuous.applyImpulse(action.id,action.impulse))throw Error('Reference action denied');
   const ev=continuous.events.at(-1);
   fullActions.push({time:ev.time,tick:action.tick,sequence:ev.sequence,
    origin:ev.origin,emittedType:ev.type});
   last=action.tick;
  }
  continuous.tick(spec.totalTicks-last);
  const controlEvents=seq(continuous);
  const reducedResult=playQueuedPhysicalActions(branch,scheduled,{
   totalTicks:spec.totalTicks,maxPhysicalTicks:spec.maxPhysicalTicksPerInterval,
   requiredQuietTicks:spec.stableConsecutiveTicks,reloadAtEachEvent:true
  });
  branch=reducedResult.loop;
  item.scheduledEvents=scheduled.length;
  item.segmentStatus=reducedResult.segments;
  item.actualActionTimes=reducedResult.actionRecords.map(x=>x.appliedTime);
  item.eventClockErrors=reducedResult.actionRecords.map(x=>Math.abs(x.plannedTime-x.appliedTime));
  item.offloadSegments=reducedResult.offloadSegments;
  item.skippedPhysicsTicks=reducedResult.skippedPhysicsTicks;
  item.actualPhysicalTicks=reducedResult.physicsTicks;
  item.eventSequencesEqual=JSON.stringify(controlEvents)===JSON.stringify(seq(branch));
  item.worldClockErrorSeconds=Math.abs(continuous.time-branch.time);
  item.playerHydrationDelta=branch.game.character.hydration-continuous.game.character.hydration;
  item.originalProseUnchanged=branch.scene.prose===proposal.text&&branch.scene.prose===continuous.scene.prose;
  item.maxPosErrorBeforeOneStep=compare(continuous,branch,ids);
  continuous.tick(1);branch.tick(1);
  item.maxPosErrorAfterOneStep=compare(continuous,branch,ids);
  const a=truth(continuous,proposal),b=truth(branch,proposal);
  item.differingPhysicalSemanticFacts=a.filter((x,i)=>x!==b[i]).length;
  const rec=PRSELoop.restore(JSON.parse(JSON.stringify(branch.snapshot())));
  if(!rec.ok)throw Error('Final scene after delayed physical events cannot save/reenter');
  const checkpoint=rec.loop;
  item.allObjectIDsPersist=[...branch.entities.keys()].every(id=>checkpoint.entities.has(id));
  item.finalSavePoseErrorMeters=compare(branch,checkpoint,ids).maxPoseMeters;
  checkpoint.dispose();
  item.status='evaluated';
 }catch(e){item.status='failed';item.reason=String(e?.message||e).slice(0,200);}
 finally{branch?.dispose();continuous?.dispose();initial?.dispose();}
 out.push(item);
 if((ix+1)%10===0)console.log('PROGRESS',subset,ix+1,'of',cases.length);
}
const analyzed=out.filter(x=>x.status==='evaluated');
const summary={subset,sourceScenes:cases.length,scheduleEventsPerScene:spec.scheduled.length,
  evaluatedEpisodes:analyzed.length,failedEpisodes:out.length-analyzed.length,
  episodesWithOneOrMoreOffloads:analyzed.filter(x=>x.offloadSegments>0).length,
  actualUnloadIntervals:analyzed.reduce((n,x)=>n+x.offloadSegments,0),
  totalPhysicsTicksSaved:analyzed.reduce((n,x)=>n+x.skippedPhysicsTicks,0),
  clockAndSourcePreserved:analyzed.filter(x=>x.worldClockErrorSeconds<1e-5&&x.originalProseUnchanged&&x.allObjectIDsPersist).length,
  physicalEventSequenceMismatches:analyzed.filter(x=>!x.eventSequencesEqual).length,
  sourceRelationTruthMismatchingScenes:analyzed.filter(x=>x.differingPhysicalSemanticFacts>0).length,
  actionChronologyErrors:analyzed.filter(x=>x.eventClockErrors.some(y=>y>1e-5)).length,
  poseDiffMoreThan2cm:analyzed.filter(x=>x.maxPosErrorAfterOneStep.maxPoseMeters>.02).length,
  worstPoseDifferenceMeters:analyzed.length?Math.max(...analyzed.map(x=>x.maxPosErrorAfterOneStep.maxPoseMeters)):null,
  worstOffloadedPoseDifferenceMeters:analyzed.filter(x=>x.offloadSegments>0).length?Math.max(...analyzed.filter(x=>x.offloadSegments>0).map(x=>x.maxPosErrorAfterOneStep.maxPoseMeters)):null,
  wallSeconds:+((performance.now()-start)/1000).toFixed(1)};
const data={metadata:{spec,actualSolver:'Native existing PRSE GameCore/Rapier',
  sourceSceneAnnotationsUsed:false,noGPUorModel:true,noHumanParticipant:true,
  persistentInternalIDs:true,
  limitation:'Only explicit scheduled impulses; unknown external events, active NPCs and interactions between loaded and unloaded regions are unsupported'},summary,records:out};
const file=privateDir+'/prse_offscreen_action_schedule_'+subset+'_raw_v1.json';
writeFileSync(file,JSON.stringify(data,null,2)+'\n',{flag:'wx',mode:0o600});
const hash=createHash('sha256').update(readFileSync(file)).digest('hex');
const safe={metadata:{...data.metadata,privateRawSHA256:hash,privateRawPath:file},summary,
 perSource:out.map(x=>({id:x.id,status:x.status,offloaded:x.offloadSegments||0,
  skippedPhysicsTicks:x.skippedPhysicsTicks||0,poseDifferenceMeters:x.maxPosErrorAfterOneStep?.maxPoseMeters??null,
  physicalEventSequenceEqual:x.eventSequencesEqual??null,
  semanticTruthDisagreements:x.differingPhysicalSemanticFacts??null,
  note:x.reason||null}))};
writeFileSync(new URL('prse_offscreen_action_schedule_'+subset+'_aggregate_v1.json',import.meta.url),
 JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log('FINAL',JSON.stringify(summary));
