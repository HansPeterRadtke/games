// Previously demonstrated real semantic errors:
// (1) object lifted vertically still falsely 'on' its stand;
// (2) moving object frozen across unloaded offscreen time.
// Both original negative files remain unchanged. This test verifies the
// conservative corrected policy with the SAME SceneEval-authored source.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {compileProposal} from './prse_constraint_layout.mjs';
import {readResearchEvidence} from './prse_research_evidence_io.mjs';
import {PRSELoop} from './prse_semantic_roundtrip.mjs';
await initializePhysics();
const directory=new URL('.',import.meta.url);
const negatives=[
 JSON.parse(readFileSync(new URL('prse_vertical_support_false_claim_before_fix.json',directory))),
 JSON.parse(readFileSync(new URL('prse_offscreen_dynamic_freeze_before_guard.json',directory)))
];
assert(negatives[0].after.incorrectSupportClaim===true);
assert(negatives[1].positionFrozen && negatives[1].velocityStillNonzero);
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_v2.json')).proposalsFirst100;
const source=proposals.find(x=>x.sourceId==='22');
const c=compileProposal(source),g=new PRSELoop(c.scene);
g.tick(20);
const lamp=g.scene.entities.find(e=>e.kind==='lamp'),nightstand=g.scene.entities.find(e=>e.kind==='nightstand');
assert(lamp.supportId===nightstand.id);
const gap=()=>lamp.position.y-lamp.size.y/2-nightstand.position.y-nightstand.size.y/2;
assert(Math.abs(gap())<.04);
g.applyImpulse(lamp.id,{x:0,y:7,z:0});g.tick(10);
const lifted={
 sourceId:source.sourceId,heightAboveSupport:gap(),sourceIdentity:lamp.id,
 supportClaim:lamp.supportId,dislodgedFrom:lamp.state.dislodgedFrom,
 lastEvent:g.events.filter(x=>x.type==='lost_support').at(-1)
};
assert(lifted.heightAboveSupport>.3&&lamp.supportId===null);
assert(lifted.lastEvent?.details.reason==='separated_vertically');
const started=g.active.size,earlierTime=g.time;
let refusal=null;
try{g.dematerialize();}catch(e){refusal=String(e.message);}
assert(refusal?.includes('Unresolved dynamic motion'));
assert(g.active.size===started && g.time===earlierTime,'failed unloading partially mutated the world');
const saved=JSON.parse(JSON.stringify(g.snapshot()));
const loaded=PRSELoop.restore(saved);
assert(loaded.ok);
const resumed=loaded.loop,resumedLamp=resumed.entities.get(lamp.id);
assert(resumedLamp.supportId===null&&resumedLamp.state.dislodgedFrom===nightstand.id);
g.tick(110);resumed.tick(110);
const reference=g.entities.get(lamp.id),actual=resumed.entities.get(lamp.id);
const divergence=Math.hypot(...['x','y','z'].map(k=>reference.position[k]-actual.position[k]));
const recovered=resumed.events.filter(e=>e.type==='rested_on'&&e.ids[0]===lamp.id);
assert(actual.supportId===nightstand.id&&actual.state.dislodgedFrom===null);
assert(recovered.length>=1&&recovered.at(-1).details.cause==='verified_rigid_body_contact');
assert(divergence<.025,'save/replay and physical support reconciliation diverged beyond accepted scale');
const prose=resumed.scene.currentProse;
assert(prose.includes('lamp 1')&&prose.includes('resting on nightstand 1'));
const count=resumed.dematerialize();
assert(count>0,'settled scene could not unload');
const old=resumed.time;
resumed.advanceOffscreen(5);
assert(Math.abs(resumed.time-old-5)<.00001);
assert(resumed.game.time===resumed.time);
const packed=JSON.parse(JSON.stringify(resumed.snapshot()));
const again=PRSELoop.restore(packed);
assert(again.ok);
assert(again.loop.active.size===0);
again.loop.materialize();
assert(again.loop.entities.get(lamp.id).supportId===nightstand.id);
assert(again.loop.scene.currentProse.includes('resting on nightstand 1'));
const out={metadata:{
 source:'Independent SceneEval manually authored row22, text-only constraint parser and existing GameCore Rapier 3D',
 oldNegativesPreserved:['prse_vertical_support_false_claim_before_fix.json','prse_offscreen_dynamic_freeze_before_guard.json'],
 humanLearning:false,modelCalls:0,limits:'single selected case with axis-aligned support geometry; no unrestricted language understanding'},
 earlierContradictions:{verticalFalseClaim:negatives[0].after.incorrectSupportClaim,
  frozenMovingBody:negatives[1].positionFrozen},
 correctedLift:lifted,activePhysicsUnloadingRefused:{reason:refusal,bodiesRetained:started,timeUnchanged:g.time>=earlierTime},
 recontact:{newSupportedBy:actual.supportId,verifiedContactEvent:recovered.at(-1),
  savedActiveTrajectoryDivergenceMeters:divergence,updatedCurrentProse:prose},
 finalReentry:{physicalBodiesUnloadCount:count,offscreenSeconds:5,
  originalSourceTextKept:again.loop.scene.prose===source.text,
  stableLampId:again.loop.entities.has(lamp.id),restingSupport:again.loop.entities.get(lamp.id).supportId}};
writeFileSync(new URL('prse_vertical_support_and_dynamic_unload_corrected.json',directory),
 JSON.stringify(out,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,negativeOriginalsPreserved:true,
 separatedGap:lifted.heightAboveSupport,unloadingBlocked:true,
 contactVerifiedRecovered:true,divergenceMeters:divergence,
 reentrySupportKept:true}));
again.loop.dispose();resumed.dispose();g.dispose();
