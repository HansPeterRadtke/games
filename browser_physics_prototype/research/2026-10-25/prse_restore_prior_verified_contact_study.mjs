// Source row240 reproduces the original Rapier reload contact-manifold gap.
// Preserve original failure separately and test provenance-preserving
// continuation without stepping the physics world while loading.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSEGroundedFacts} from './prse_grounded_relation_narration.mjs';
await initializePhysics();
const p=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[240];
const originalNegative=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-grounded-prose/prse_relation_restore_discontinuity_source240_negative.json'));
assert(originalNegative.pairedMismatches.length===1);
assert(originalNegative.pairedMismatches[0].sourceType==='on');
const layout=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
const a=new PRSELoop(layout.scene);a.tick(24);
const state=new PRSEGroundedFacts(a,p.relations);
const lifted=state.current().findIndex((x,i)=>x.truth==='true'&&p.relations[i].type==='on'
  &&x.ids?.length===2&&a.active.get(x.ids[0])?.isDynamic());
assert(lifted>=0);
assert(a.applyImpulse(state.current()[lifted].ids[0],{x:4,y:1,z:.25}));
a.tick(110);
const before=state.current(),index=5;
assert(before[index].truth==='true');
const journal=JSON.parse(JSON.stringify(state.snapshot()));
assert(journal.schema===2);
const instantTime=a.time;
const saved=JSON.parse(JSON.stringify(a.snapshot()));
const clone=PRSELoop.restore(saved);assert(clone.ok);
const b=clone.loop;
assert(b.time===instantTime);
const fresh=new PRSEGroundedFacts(b,p.relations),withoutProof=fresh.current();
assert(withoutProof[index].truth==='unknown');
const resumed=PRSEGroundedFacts.restore(b,p.relations,journal),withProof=resumed.current();
assert(withProof[index].truth==='true'&&withProof[index].temporallyInherited);
assert(withProof[index].reason==='previously_verified_contact_at_unchanged_restored_pose');
assert(b.game.stepCount===a.game.stepCount,'Artificial hidden physics tick on load');
assert(resumed.verified().length===state.verified().length);
const forgedPose=JSON.parse(JSON.stringify(journal));
forgedPose.physicalProofs[0].entities[0].position.x+=.5;
let poseRejected=false;
try{PRSEGroundedFacts.restore(b,p.relations,forgedPose);}catch{poseRejected=true;}
assert(poseRejected);
const forgedTime=JSON.parse(JSON.stringify(journal));forgedTime.worldTime+=2;
let timeRejected=false;
try{PRSEGroundedFacts.restore(b,p.relations,forgedTime);}catch{timeRejected=true;}
assert(timeRejected);
const altered=JSON.parse(JSON.stringify(p.relations));altered[index].a='false-source';
let sourceRejected=false;
try{PRSEGroundedFacts.restore(b,altered,journal);}catch{sourceRejected=true;}
assert(sourceRejected);
const stepBefore=a.game.stepCount;
a.tick(1);b.tick(1);
const afterSrc=state.current(),afterReload=resumed.current();
assert(JSON.stringify(afterSrc.map(x=>x.truth))===JSON.stringify(afterReload.map(x=>x.truth)));
assert(afterReload[index].truth==='true'&&!afterReload[index].temporallyInherited);
assert(a.game.stepCount===stepBefore+1&&b.game.stepCount===stepBefore+1);
const outcome={
 metadata:{kind:'Research-only GameCore/Rapier source-row240 truth continuity',
 originalNegative:'prse_relation_restore_discontinuity_source240_negative.json',
 noChangedEntityOrSourceAcrossSave:true,noExtraHiddenPhysicsStep:true,
 limitation:'Carries previously measured contact evidence only at unchanged saved pose and exact world time; no new contact claimed before solver warmup'},
 before:{time:instantTime,clock:a.time,sourceRow:240,
  positiveSupportCount:before.filter(x=>x.truth==='true'&&x.source.type==='on').length,
  relationTruth:before[index].truth},
 immediatelyAfterNativeReload:{withoutProvenance:withoutProof[index].truth,
  withPriorVerifiedEvidence:withProof[index].truth,
  evidenceAgeSeconds:instantTime-withProof[index].evidenceOriginallyMeasuredAt,
  sourceIDs:withProof[index].ids,canClaimFreshPhysicsContact:false,
  gamePhysicsStepCount:b.game.stepCount-1},
 onceActualPhysicsResumed:{truth:afterReload[index].truth,
  stillDependsOnSavedEvidence:!!afterReload[index].temporallyInherited,
  regeneratedContactGraph:true,
  trajectoriesSameTruth:afterSrc.every((x,i)=>x.truth===afterReload[i].truth)},
 tampering:{invalidSourceRejected:sourceRejected,forgedPoseRejected:poseRejected,
  forgedTimeRejected:timeRejected}};
writeFileSync(new URL('prse_restore_prior_verified_contact_fix_v2.json',import.meta.url),
 JSON.stringify(outcome,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,sourceId:240,atLoadWithoutProof:withoutProof[index].truth,
 withSavedEvidence:withProof[index].truth,afterPhysics:afterReload[index].truth,
 extraPhysicsStepsAtLoad:0,forgeryGuards:outcome.tampering}));
b.dispose();a.dispose();
