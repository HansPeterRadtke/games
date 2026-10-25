// Adversarial source-meaning guards. SceneEval row 7 is independent annotated
// evidence of explicit negation; the contradictory examples below are synthetically
// authored regression guards, NOT independent semantic benchmark scores.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {compileProposal} from '../2026-10-24/prse_constraint_layout.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
await initializePhysics();
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_v2.json')).proposalsFirst100;
const source=proposals.find(p=>p.sourceId==='7');
assert(source&&source.quantities.coffee_table.count===0);
const c=repairScene(source),scene=c.scene;
assert(c.accepted&&scene.entities.some(e=>e.kind==='sofa'));
assert(!scene.entities.some(e=>e.kind==='coffee_table'),
 'Text-to-scene compile invented an explicitly absent table');
const native=new PRSELoop(scene);
native.tick(20);
assert(!native.scene.entities.some(e=>e.kind==='coffee_table'));
const loaded=PRSELoop.restore(JSON.parse(JSON.stringify(native.snapshot())));
assert(loaded.ok&&!loaded.loop.scene.entities.some(e=>e.kind==='coffee_table'));
const zeroCase={sourceId:'7',noCoffeeTableObserved:true,
 sceneContainsExpectedSofa:loaded.loop.scene.entities.some(e=>e.kind==='sofa'),
 preservedPhysicalEntityIDs:loaded.loop.active.size===native.active.size,
 sourceStillVerbatim:loaded.loop.scene.prose===source.text};
loaded.loop.dispose();native.dispose();

const contradiction={
 sourceId:'synthetic-untrusted-1',text:'A lamp is simultaneously to the left and to the right of a sofa.',
 quantities:{sofa:{count:1,op:'eq'},lamp:{count:1,op:'eq'}},
 mentions:[],
 relations:[
  {kind:'object',type:'left',a:'lamp',b:'sofa',sourceText:'simultaneously to the left'},
  {kind:'object',type:'right',a:'lamp',b:'sofa',sourceText:'simultaneously to the right'}
 ]};
const conflict=repairScene(contradiction,{maxSweeps:2,maxAttemptsPerScene:100});
const contradictoryNotBothSatisfied=conflict.after.grounded<2;
assert(contradictoryNotBothSatisfied);
const conflictOut={source:'synthetic contradiction (not a human data point)',
 constraints:2,satisfied:conflict.after.grounded,
 rejectedAsFullySatisfied:contradictoryNotBothSatisfied,
 geometryValid:conflict.accepted,
 unverifiableIsNotClaimed:true};

const ambiguous={
 sourceId:'synthetic-untrusted-2',
 text:'There is no lamp in the room. A lamp is standing on the table.',
 mentions:[],
 quantities:{lamp:{count:1,op:'eq',ambiguous:true},table:{count:1,op:'eq'}},
 relations:[{kind:'object',type:'on',a:'lamp',b:'table',sourceText:'lamp standing on table'}]};
const rejected=repairScene(ambiguous);
const abstain={ambiguousEntityNotMaterialized:!rejected.scene.entities.some(e=>e.kind==='lamp'),
 typedRefusal:rejected.missing.some(e=>e.type==='ambiguous_count'),
 unverifiedSupportNotClaimed:rejected.after.grounded===0};
assert(abstain.ambiguousEntityNotMaterialized&&abstain.typedRefusal&&abstain.unverifiedSupportNotClaimed);
const data={
 provenance:{externalText:'SceneEval-500 human authored row7 (source held private)',
 remaining:'Two explicitly synthetic logical-contradiction regression examples; NOT empirical generalization',
 codePath:'text-only parsed proposals -> prior compiler/constraint repair -> actual GameCore Rapier + saved state'},
 sourceNegation:zeroCase,contradiction:conflictOut,unknownSemantics:abstain};
writeFileSync(new URL('prse_relation_negation_guard_results_v1.json',import.meta.url),
 JSON.stringify(data,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,sourceNegation:zeroCase,conflict:conflictOut,abstained:abstain}));
