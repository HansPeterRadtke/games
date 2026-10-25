// Actual PRSE GameCore/Rapier semantic relation → grounded *current* factual
// description → saved observer journal → re-entry across 200 source-derived
// scenes, holding each parser's proposals fixed. Raw text and per-scene facts
// are retained privately; public output is aggregate metrics and hashes.
//
// This is not an automated user study or human text fluency evaluation.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {PRSELoop,geometryIssues} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEPhysicalObserver} from './prse_physical_observer.mjs';
import {PRSEGroundedFacts} from './prse_grounded_relation_narration.mjs';
import {validRelation} from '../2026-10-24/prse_constraint_layout.mjs';
await initializePhysics();
const dir='/data/var/games/prse_semantic_research/runs/2026-10-25-grounded-prose';
const suffix=process.argv.find(x=>x.startsWith('--suffix='))?.slice(9)||'v1';
if(!/^v[1-9][0-9]?$/.test(suffix))throw Error('Unsafe version suffix');
mkdirSync(dir,{recursive:true,mode:0o700});
const parsers={
 deterministic:JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500,
 union:JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model/prse_spacy_sceneeval_500_union_v1.json')).proposalsAll500
};
const samples=[...Array.from({length:100},(_,i)=>i),
 ...Array.from({length:100},(_,i)=>100+i*4)];
const views=[
 {x:-27,y:1.6,z:11.8},{x:-32.8,y:1.6,z:7.9},
 {x:-21,y:1.6,z:7.9},{x:-32.8,y:1.6,z:15.7},{x:-21,y:1.6,z:15.7}
];
function validEye(world,eye){
 let inside=false;
 world.game.world.intersectionsWithPoint(eye,()=>{inside=true;return false;});
 return !inside;
}
function actualObserverIds(loop,perception,eye){
 const objects=[];
 for(const id of loop.entities.keys()){
  if(perception.isVisible(id,eye,{radius:9,mode:'ray'}).visible)objects.push(id);
 }
 return objects;
}
function total(rows,key){return rows.reduce((s,r)=>s+(r[key]||0),0);}
const final=[];
for(const [method,proposals] of Object.entries(parsers)){
 const began=performance.now(),records=[];
 for(const id of samples){
  const p=proposals[id],layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
  const rec={id,subset:id<100?'human':'assisted',status:'not-run',
   proposedRelations:p.relations.length,parsedObjects:layout.provisionalObjects,
   trueRelations:0,falseRelations:0,unknownRelations:0,
   verifiedStatements:0,observedStatements:0,repeatedNarration:0,
   saveFactsConsistent:false,staleProseAccepted:false,worldTimeDelta:0,
   initialPhysicalRelationComparison:{agree:0,disagree:0,unmeasurable:0},
   changedPhysicalRelationCount:0,postImpulseFalseSourceClaims:0,
   achievedOffscreenUnloaded:false};
  if(!layout.accepted||geometryIssues(layout.scene).length||!layout.provisionalObjects){
   rec.status='invalid-layout';records.push(rec);continue;
  }
  let loop=null,again=null;
  try{
   loop=new PRSELoop(layout.scene);loop.tick(24);
   const facts=new PRSEGroundedFacts(loop,p.relations),candidate=facts.current();
   // Exact verified physical predicate/result pairs for an INDEPENDENT,
   // post-hoc scorer. This per-source detail is stored owner-private only.
   // No SceneEval gold labels are read here.
   rec.relationEvidence=candidate.map(x=>({
    key:x.key,kind:x.source.kind,type:x.source.type,
    a:x.source.a,b:x.source.b,truth:x.truth,reason:x.reason,
    worldEntityIds:x.ids||null
   }));
   rec.trueRelations=candidate.filter(x=>x.truth==='true').length;
   rec.falseRelations=candidate.filter(x=>x.truth==='false').length;
   rec.unknownRelations=candidate.filter(x=>x.truth==='unknown').length;
   rec.reasons=Object.fromEntries([...new Set(candidate.filter(x=>x.truth==='unknown').map(x=>x.reason))].map(
     reason=>[reason,candidate.filter(x=>x.reason===reason).length]));
   rec.verifiedStatements=facts.verified().length;
   for(let i=0;i<candidate.length;i++){
    const r=candidate[i];
    if(r.truth==='unknown'){rec.initialPhysicalRelationComparison.unmeasurable++;continue;}
    const independent=validRelation(p.relations[i],loop.scene.entities.filter(e=>e.source!=='provisional_3D_room_boundary'));
    if(independent===null)rec.initialPhysicalRelationComparison.unmeasurable++;
    else if(independent===(r.truth==='true'))rec.initialPhysicalRelationComparison.agree++;
    else rec.initialPhysicalRelationComparison.disagree++;
   }
   const observer=new PRSEPhysicalObserver(loop,{visibilityRadius:9});
   for(let view=0;view<views.length;view++){
    const eye=views[view];
    if(!validEye(loop,eye))continue;
    const visible=actualObserverIds(loop,observer,eye);
    const first=facts.observe('study-eye-'+view,visible);
    rec.observedStatements+=first.changed.length;
    const second=facts.observe('study-eye-'+view,visible);
    rec.repeatedNarration+=second.changed.length;
    if(first.changed.some(x=>x.kind==='verified_now')){
     const verified=facts.current();
     for(const line of first.changed){
      if(line.kind==='verified_now'){
       const claim=verified[line.key];
       if(claim.truth!=='true')throw Error('An unverified current relation became rendered text');
      }
     }
    }
   }
   const before=facts.current().map(x=>x.truth);
   const on=before.findIndex((truth,i)=>truth==='true'
     &&p.relations[i]?.type==='on'
     &&candidate[i]?.ids?.length===2
     &&loop.active.get(candidate[i].ids[0])?.isDynamic());
   if(on>=0){
    const src=candidate[on].ids[0];
    if(loop.applyImpulse(src,{x:4,y:1,z:.25})){
     loop.tick(110);
     const after=facts.current().map(x=>x.truth);
     rec.changedPhysicalRelationCount=after.reduce((n,x,i)=>n+(x!==before[i]),0);
     rec.postImpulseFalseSourceClaims=after.filter((x,i)=>before[i]==='true'&&x==='false').length;
    }
   }
   const saved=JSON.parse(JSON.stringify(loop.snapshot()));
   const restored=PRSELoop.restore(saved);
   if(!restored.ok)throw Error('Native GameCore scene save failed');
   again=restored.loop;
   const journal=PRSEGroundedFacts.restore(again,p.relations,JSON.parse(JSON.stringify(facts.snapshot())));
   const stateBefore=facts.current().map(r=>r.truth),stateAfter=journal.current().map(r=>r.truth);
   rec.saveFactsConsistent=JSON.stringify(stateBefore)===JSON.stringify(stateAfter)
     &&again.scene.prose===p.text
     &&layout.scene.entities.every(x=>again.entities.has(x.id));
   rec.worldTimeDelta=again.time-loop.time;
   if(!rec.saveFactsConsistent)throw Error('Facts diverged on save/reload');
   // Never use old source prose as evidence for now: preserve as immutable original.
   rec.staleProseAccepted=again.scene.prose!==p.text;
   if(rec.repeatedNarration)throw Error('Observed identical unchanged fact twice');
   rec.status='verified-world-and-facts';
  }catch(e){rec.status='failed';rec.error=String(e.message).slice(0,250);}
  finally{again?.dispose();loop?.dispose();}
  records.push(rec);
 }
 const summary={method,scenes:records.length,
  humanScenes:records.filter(x=>x.subset==='human').length,
  assistedScenes:records.filter(x=>x.subset==='assisted').length,
  verifiedSceneSaves:records.filter(x=>x.status==='verified-world-and-facts').length,
  rejectedBeforeSimulation:records.filter(x=>x.status==='invalid-layout').length,
  failed:records.filter(x=>x.status==='failed').length,
  sourceParsedRelations:total(records,'proposedRelations'),
  knownPhysicallyTrue:total(records,'trueRelations'),
  knownPhysicallyFalse:total(records,'falseRelations'),
  physicallyUnknownOrAmbiguous:total(records,'unknownRelations'),
  emittedVerifiedFactStatements:total(records,'observedStatements'),
  sameFactRepeatedOnSameObserver:total(records,'repeatedNarration'),
  independentOracleDisagreements:records.reduce((n,r)=>n+r.initialPhysicalRelationComparison.disagree,0),
  independentOracleComparisons:records.reduce((n,r)=>n+r.initialPhysicalRelationComparison.agree,0),
  changedRelationTruthAfterRealImpulse:total(records,'changedPhysicalRelationCount'),
  physicallyNoLongerTrueAfterImpulse:total(records,'postImpulseFalseSourceClaims'),
  noSourceProseMutation:records.every(x=>!x.staleProseAccepted),
  elapsedWallSeconds:+((performance.now()-began)/1000).toFixed(2)};
 const raw={metadata:{model:method,source:'SceneEval-500 v250610 unchanged parser proposals',
  sourceIDs:samples,sourceAnnotationsNeverRead:true,geometry:'Actual GameCore Rapier and observer physical rays',
  purpose:'Grounded current factual relation truth/deltas, not human literary fluency or exact general story entailment'},
  summary,records};
 const path=dir+'/prse_grounded_prose_'+method+'_200_raw_'+suffix+'.json';
 writeFileSync(path,JSON.stringify(raw,null,2)+'\n',{flag:'wx',mode:0o600});
 const digest=createHash('sha256').update(readFileSync(path)).digest('hex');
 final.push({summary,privateRawSHA256:digest,privatePath:path});
 console.log(method,JSON.stringify(summary));
}
writeFileSync(new URL('prse_grounded_prose_200_aggregate_'+suffix+'.json',import.meta.url),JSON.stringify({
 metadata:{source:'External SceneEval-500, human first100 and systematic assisted100, unchanged source-lexical parser proposals',
 noGoldInput:true,noGenerativeModel:true,
 claims:'Only physically measured supported factual relations; unknown withheld; observer rays control delivery',
 scientificLimit:'Independent geometry oracle only approximately aligned; no lexical literary fluency, no blinded human evaluation, no production integration'},
 variants:final
},null,2)+'\n',{flag:'wx'});
