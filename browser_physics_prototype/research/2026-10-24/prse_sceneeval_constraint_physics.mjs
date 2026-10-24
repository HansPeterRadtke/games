// Fully automatic constrained proposal -> GameCore 3D materialization -> physics
// -> snapshot/restoration -> relation checks from actual post-step 3D state.
// Input comes from a separate text-only interpreter. Gold labels are not used
// to create scenes or choose relationships. This is a research feasibility path.
import {readFileSync,writeFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop} from './prse_semantic_roundtrip.mjs';
import {compileProposal,validRelation} from './prse_constraint_layout.mjs';
import {readResearchEvidence} from './prse_research_evidence_io.mjs';
await initializePhysics();
const DIR=new URL('.',import.meta.url);
const dataArg=process.argv.find(s=>s.startsWith('--data='))?.slice(7)||'prse_semantic_constraints_eval_v2.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(dataArg))throw Error('unsafe input');
const input=JSON.parse(readResearchEvidence(dataArg));
const allProposals=input.proposalsAll500||input.proposalsFirst100;
const readNumber=(flag,fallback)=>{const raw=process.argv.find(s=>s.startsWith('--'+flag+'='))?.split('=')[1];
 if(raw===undefined)return fallback;
 if(!/^\d+$/.test(raw)||Number(raw)>500)return fallback;
 return Number(raw);
};
const first=readNumber('first',0),stride=readNumber('stride',1),limit=readNumber('limit',100);
if(stride<1||limit<1)throw Error('invalid sample bounds');
const proposals=allProposals.filter((p,i)=>i>=first&&(i-first)%stride===0).slice(0,limit);
const results=[],failures=[];
const t0=performance.now();
for(const proposal of proposals){
 const constructed=compileProposal(proposal);
 const rec={id:proposal.sourceId,
  extractedPositiveTypes:Object.values(proposal.quantities).filter(x=>x.count>0).length,
  extractedZeroTypes:Object.values(proposal.quantities).filter(x=>x.count===0).length,
  objectCount:constructed.proposed,missing:constructed.missing,
  sourceRelations:proposal.relations.length,
  relationPredictions:constructed.relations,
  geometryValidBeforePhysics:constructed.good,
  syntaxAndRelationshipAbstentions:constructed.relationGeometryUnknown,
  sourceProse:constructed.source,
  status:'not_started'};
 if(constructed.proposed===0){rec.status='no_entities';results.push(rec);continue;}
 if(!constructed.good){rec.status='rejected_invalid_geometry';rec.geometryIssues=constructed.geometricProblems;results.push(rec);continue;}
 let loop=null,restored=null;
 try{
  const start=performance.now();
  loop=new PRSELoop(constructed.scene);
  const beforeBodies=loop.active.size;
  loop.tick(18);
  const pAfter=loop.scene.entities;
  const semanticRelationOutcomes=proposal.relations.map(r=>({
   a:r.a,b:r.b,type:r.type,kind:r.kind,
   result:validRelation(r,pAfter.filter(e=>e.kind!=='wall'))
  }));
  const snap=JSON.parse(JSON.stringify(loop.snapshot()));
  const load=PRSELoop.restore(snap);
  if(!load.ok)throw Error('Failed save-reentry validation');
  restored=load.loop;
  const shapeCount=restored.active.size;
  const sameOriginalProse=restored.scene.prose===constructed.source;
  const stableIds=constructed.scene.entities.every(e=>restored.entities.has(e.id));
  const maxPositionError=Math.max(...constructed.scene.entities.map(e=>{
   const a=loop.entities.get(e.id),b=restored.entities.get(e.id);
   return Math.hypot(a.position.x-b.position.x,a.position.y-b.position.y,a.position.z-b.position.z);
  }));
  rec.status='materialized_and_reloaded';
  rec.originalPhysicalBodies=beforeBodies;rec.restoredPhysicalBodies=shapeCount;
  rec.sameOriginalProse=sameOriginalProse;rec.stableIds=stableIds;
  rec.maxPositionError=maxPositionError;rec.physicalRelationOutcomes=semanticRelationOutcomes;
  rec.measuredPhysicsAndSaveMs=+(performance.now()-start).toFixed(2);
 }catch(e){rec.status='runtime_rejected';rec.runtimeError=String(e.message).slice(0,150);}
 finally{restored?.dispose();loop?.dispose();}
 results.push(rec);
}
const completed=results.filter(x=>x.status==='materialized_and_reloaded');
const proposedRelations=completed.flatMap(x=>x.physicalRelationOutcomes);
const summary={
 sourceProposals:proposals.length,scenesWithPhysicalBodies:completed.length,
 physicallyRejected:results.filter(x=>x.status==='rejected_invalid_geometry').length,
 noRecognizedEntities:results.filter(x=>x.status==='no_entities').length,
 runtimeRejected:results.filter(x=>x.status==='runtime_rejected').length,
 withValidEntityIdentityAndProse:completed.filter(x=>x.stableIds&&x.sameOriginalProse&&x.maxPositionError<.001).length,
 extractedRelationClaims:proposedRelations.length,
 physicallyGroundedRelationCount:proposedRelations.filter(x=>x.result===true).length,
 physicallyViolatedRelationCount:proposedRelations.filter(x=>x.result===false).length,
 unsupportedRelationCount:proposedRelations.filter(x=>x.result===null).length,
 totalWallClockMs:+(performance.now()-t0).toFixed(2),
 medianPerSceneMs:(()=>{const arr=completed.map(x=>x.measuredPhysicsAndSaveMs).sort((a,b)=>a-b);return arr.length?arr[Math.floor(arr.length/2)]:null;})(),
 negativesAcrossSource:results.filter(x=>x.status!=='materialized_and_reloaded').slice(0,16)
};
const output={metadata:{
 purpose:'Automatic limited text-to-3D constraint grounding in existing authoritative GameCore',
 heldoutClaim:'NO. Parser development inspected first 35 external prompts; this is exploratory evaluation across all first 100.',
 provenance:'SceneEval source text; first100 human-authored, remaining400 VLM-assisted, source IDs stable, NO gold passed to compiler.',
 level:'Object mentions, negation and simple spatial relations; no full literary understanding, wall geometry is provisional.',
 physics:'Native GameCore Rapier 3D rigid-body solver; relation checks read measured post-step state, wrapper save/reload.',
 uncontrolled:'No camera/occlusion, sophisticated collision-aware optimizer, materials/textures, general offscreen stories or new LLM calls.'},
 summary,results};
const outputName=process.argv.find(s=>s.startsWith('--output='))?.slice(9)||'prse_sceneeval_constraint_physics_v1.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(outputName))throw Error('Unsafe output filename');
writeFileSync(new URL(outputName,DIR),JSON.stringify(output,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(summary));
