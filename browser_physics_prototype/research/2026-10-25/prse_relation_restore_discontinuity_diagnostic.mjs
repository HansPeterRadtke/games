// Preserve the actual negative event without changing prior results. The
// third overnight corpus run found one story-fact discrepancy immediately
// after save/reload; identify exact source relation and Rapier contact state.
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEGroundedFacts} from './prse_grounded_relation_narration.mjs';
await initializePhysics();
const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[240];
const scene=repairScene(p);
if(!scene.accepted)throw Error('Source case not accepted');
const a=new PRSELoop(scene.scene);a.tick(24);
const f=new PRSEGroundedFacts(a,p.relations);
const before=f.current();
const dynamicIndex=before.findIndex((r,i)=>r.truth==='true'&&p.relations[i].type==='on'
 &&r.ids?.length===2&&a.active.get(r.ids[0])?.isDynamic());
let impulse=null;
if(dynamicIndex>=0){
 impulse=before[dynamicIndex].ids[0];
 if(!a.applyImpulse(impulse,{x:4,y:1,z:.25}))throw Error('Expected impulse rejected');
 a.tick(110);
}
const prepared=f.current();
const save=JSON.parse(JSON.stringify(a.snapshot()));
const result=PRSELoop.restore(save);if(!result.ok)throw Error('Save failed');
const b=result.loop,fr=new PRSEGroundedFacts(b,p.relations),loaded=fr.current();
const mismatches=[];
for(let i=0;i<prepared.length;i++){
 if(prepared[i].truth!==loaded[i].truth)
 mismatches.push({i,sourceType:p.relations[i].type,sourceA:p.relations[i].a,
  sourceB:p.relations[i].b,before:prepared[i],after:loaded[i]});
}
const beforeStep={a:f.current(),b:fr.current()};
a.tick(1);b.tick(1);
const afterStep={a:f.current(),b:fr.current()};
const resultData={metadata:{sourceRow:240,sourceProsePreserved:b.scene.prose===p.text,
 previousNegative:'prse_grounded_prose_deterministic_200_raw_v1.json, source 240',
 investigatorProbe:'Independent replay, original raw evidence left unmodified'},
 sourceRelations:p.relations.map(r=>({kind:r.kind,type:r.type,a:r.a,b:r.b})),
 selectedImpulseEntity:impulse,pairedMismatches:mismatches,
 beforeNextPhysicsStep:beforeStep,afterNextPhysicsStep:afterStep,
 worldClockBefore:a.time,restoredClock:b.time};
writeFileSync(new URL('prse_relation_restore_discontinuity_source240_negative.json',import.meta.url),
 JSON.stringify(resultData,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({source240:{entities:scene.scene.entities.length,relations:p.relations.length},
 impulse,mismatches:mismatches.map(x=>({i:x.i,type:x.sourceType,a:x.sourceA,b:x.sourceB,
 previous:x.before.truth,after:x.after.truth,reasons:[x.before.reason,x.after.reason]})),
 afterOneStep:[afterStep.a.map(x=>x.truth),afterStep.b.map(x=>x.truth)]}));
b.dispose();a.dispose();
