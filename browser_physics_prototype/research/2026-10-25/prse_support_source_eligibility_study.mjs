// Source-blind diagnosis of parser-proposed "on" relations before attempting
// additional physically grounded PRSE semantic↔Rapier↔semantic work.
// No SceneEval gold annotations are opened in this script.
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,geometryIssues} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {measureRelation} from './prse_grounded_relation_narration.mjs';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
await initializePhysics();
const outdir='/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop';
mkdirSync(outdir,{recursive:true,mode:0o700});
const source=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const ids=[...Array.from({length:100},(_,i)=>i),...Array.from({length:100},(_,i)=>100+i*4)];
const records=[];
for(const id of ids){
 const p=source[id];
 const on=p.relations.filter(r=>r.kind==='object'&&r.type==='on');
 if(!on.length)continue;
 const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!layout.accepted||geometryIssues(layout.scene).length){
  records.push({id,valid:false,onCount:on.length});continue;
 }
 let loop=null;
 try{
  loop=new PRSELoop(layout.scene);loop.tick(36);
  for(const rel of on){
   const a=loop.scene.entities.filter(e=>e.kind===rel.a&&e.source!=='provisional_3D_room_boundary'),
    b=loop.scene.entities.filter(e=>e.kind===rel.b&&e.source!=='provisional_3D_room_boundary');
   const child=a.length===1?a[0]:null,parent=b.length===1?b[0]:null;
   const measured=measureRelation(loop,rel);
   const eligible=Boolean(child&&parent&&child!==parent&&
    child.body==='dynamic'&&parent.shape!=='sphere'&&
    parent.size.x>=child.size.x+.02&&parent.size.z>=child.size.z+.02&&
    !loop.scene.entities.some(e=>e.supportId===child.id));
   const lineage={id,sourceSpan:rel.sourceText,relA:rel.a,relB:rel.b,
    candidateInstanceCounts:[a.length,b.length],
    status:measured.truth,reason:measured.reason,
    eligible,childId:child?.id??null,parentId:parent?.id??null,
    childBody:child?.body??null,sourceProposedSupportId:child?.supportId??null,
    supportHasChildren:!!child&&loop.scene.entities.some(e=>e.supportId===child.id),
    fittingSurface:!!(child&&parent&&parent.size.x>=child.size.x+.02&&parent.size.z>=child.size.z+.02)};
   records.push(lineage);
  }
 }finally{loop?.dispose();}
}
const tally={sourceDescriptions:ids.length,parsedOnRelations:records.length,
 originalScenesWithOn:[...new Set(records.map(x=>x.id))].length,
 baselineTrue:records.filter(x=>x.status==='true').length,
 baselineFalse:records.filter(x=>x.status==='false').length,
 baselineUnknown:records.filter(x=>x.status==='unknown').length,
 eligibleForPotentialUnambiguousDynamicPhysicalRepair:records.filter(x=>x.eligible).length,
 eligibleButNotPhysicallyTrue:records.filter(x=>x.eligible&&x.status!=='true').length,
 multipleOrUnresolvedReferences:records.filter(x=>
  x.candidateInstanceCounts&&(x.candidateInstanceCounts[0]!==1||x.candidateInstanceCounts[1]!==1)).length,
 nonfittingSurface:records.filter(x=>x.candidateInstanceCounts&&!x.fittingSurface).length};
const path=outdir+'/prse_source_blind_support_eligibility_v1.json';
writeFileSync(path,JSON.stringify({tally,records},null,2)+'\n',{flag:'wx',mode:0o600});
const sha=createHash('sha256').update(readFileSync(path)).digest('hex');
writeFileSync(new URL('prse_support_eligibility_200_aggregate_v1.json',import.meta.url),
 JSON.stringify({tally,privateRawSHA256:sha,originalGoldAnnotationsUnused:true},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(tally));
console.log('ELIGIBLE_CASES',records.filter(r=>r.eligible).map(r=>({id:r.id,a:r.relA,b:r.relB,
 status:r.status,reason:r.reason})));
