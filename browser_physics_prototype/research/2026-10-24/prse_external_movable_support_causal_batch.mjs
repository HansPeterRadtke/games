// All currently recognized, geometry-valid SceneEval human descriptions among
// the first 100 with a *movable* child explicitly "on" a supporting object.
// The single fixed action is applied to every eligible case; no manual poses,
// no gold lookups, no cherry-picked success outcomes.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop} from './prse_semantic_roundtrip.mjs';
import {compileProposal} from './prse_constraint_layout.mjs';
import {readResearchEvidence} from './prse_research_evidence_io.mjs';
await initializePhysics();
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_v2.json')).proposalsFirst100;
const types=new Set(['ball','vase','book','cup','jug','teapot','doll','potted_plant','lamp']);
const eligible=[];
for(const p of proposals){
 const compiled=compileProposal(p);
 if(!compiled.good)continue;
 for(const r of compiled.relations){
  if(r.kind==='object'&&r.type==='on'&&types.has(r.a)&&r.grounded===true){
   const a=compiled.scene.entities.find(e=>e.kind===r.a),b=compiled.scene.entities.find(e=>e.kind===r.b);
   if(a&&b&&a.supportId===b.id&&a.body==='dynamic')eligible.push({p,compiled,r,a,b});
  }
 }
}
const results=[];
for(const trial of eligible){
 const {p,compiled,r,a,b}=trial;
 let g=null,reloaded=null;
 const row={sceneId:p.sourceId,languageRelation:r,source:p.text,childId:a.id,supportId:b.id};
 try{
  g=new PRSELoop(compiled.scene);
  g.tick(24);
  const active=g.entities.get(a.id),s=g.entities.get(b.id);
  row.afterSettling={relationRemained:active.supportId===s.id,
    childPosition:{...active.position},supportPosition:{...s.position},
    kg:active.mass};
  if(active.supportId!==s.id){row.status='initial_contact_unstable';results.push(row);continue;}
  const vec={x:4,y:1,z:0};row.fixedImpulse=vec;
  assert(g.applyImpulse(a.id,vec));
  g.tick(100);
  const child=g.entities.get(a.id);
  row.afterPhysics={position:{...child.position},supportId:child.supportId,
    dislodgedFrom:child.state.dislodgedFrom||null,
    lostSupportEvents:g.events.filter(e=>e.type==='lost_support'&&e.ids[0]===a.id).length,
    reportedCurrentDescription:g.scene.currentProse.includes('no longer supported by '+s.name)};
  const save=JSON.parse(JSON.stringify(g.snapshot()));
  const loaded=PRSELoop.restore(save);
  if(!loaded.ok)throw Error('snapshot was rejected');
  reloaded=loaded.loop;
  const reread=reloaded.entities.get(a.id);
  row.afterSave={idStable:reloaded.entities.has(a.id),supportId:reread.supportId,
    matchedSupportId:reread.supportId===child.supportId,
    sourceExact:reloaded.scene.prose===p.text,
    dislodgedFrom:reread.state.dislodgedFrom||null};
  row.pass=row.afterPhysics.lostSupportEvents>=1&&row.afterPhysics.supportId===null
      &&row.afterPhysics.reportedCurrentDescription
      &&row.afterSave.idStable&&row.afterSave.matchedSupportId&&row.afterSave.sourceExact;
  row.status='physics_tested';
 }catch(e){row.status='runtime_failure';row.error=String(e.message).slice(0,220);}
 finally{reloaded?.dispose();g?.dispose();}
 results.push(row);
}
const summary={humanDescriptionsConsidered:proposals.length,
  eligibleExplicitMovableSupportRelations:eligible.length,
  tested:results.filter(x=>x.status==='physics_tested').length,
  passed:results.filter(x=>x.pass).length,
  notPassed:results.filter(x=>!x.pass).length,
  sampleIds:eligible.map(x=>x.p.sourceId)};
const data={metadata:{source:'SceneEval original human-authored 100 (official external text), textual constraints produced without annotation labels',
 method:'fixed x=4,y=1,z=0 impulse for every identified dynamic on relation, native GameCore Rapier',
 limitations:'Very small automatic eligibility set; no independent human gameplay; no general semantic interpretation; comparison exploratory'},
 summary,results};
writeFileSync(new URL('prse_external_movable_support_causal_batch_v1.json',import.meta.url),
 JSON.stringify(data,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({summary,perScene:results.map(r=>({id:r.sceneId,status:r.status,pass:r.pass,
 eventCount:r.afterPhysics?.lostSupportEvents,initialStable:r.afterSettling?.relationRemained,
 child:r.languageRelation.a,support:r.languageRelation.b}))}));
