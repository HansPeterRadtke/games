// Actual 3D Rapier/GameCore relation test: reject misleadingly 'near'
// relationships that have horizontal projections close but are distant in Y,
// or diagonal X/Z gaps whose Euclidean distance exceeds the threshold.
// Original pre-fix observed errors are retained as separate immutable JSON.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {measureRelation,PRSEGroundedFacts} from './prse_grounded_relation_narration.mjs';
await initializePhysics();
const directory=new URL('.',import.meta.url);
const verticalBefore=JSON.parse(readFileSync(new URL('prse_false_near_vertical_gap_prefixed_negative.json',directory)));
const diagonalBefore=JSON.parse(readFileSync(new URL('prse_false_diagonal_near_before_distance_fix.json',directory)));
assert(verticalBefore.wronglyVerified&&verticalBefore.actualVerticalGapMeters>4);
assert(diagonalBefore.incorrectIfNear&&diagonalBefore.actualSurfaceEuclideanClearanceMetres>1.5);
const fixtures=[
 {id:'vertical',a:{x:-25,y:5,z:9},b:{x:-25,y:.25,z:9},expected:'false'},
 {id:'diagonal',a:{x:-20,y:.25,z:10},b:{x:-21.7,y:.25,z:8.3},expected:'false'},
 {id:'same-floor-near',a:{x:-25,y:.25,z:9},b:{x:-25.9,y:.25,z:9},expected:'true'}
];
const results=[];
for(const c of fixtures){
 const a=object('first-entity','stone',c.a,{x:.4,y:.5,z:.4},{body:'fixed',material:'stone'});
 a.supportId=null;
 const b=object('second-entity','lamp',c.b,{x:.4,y:.5,z:.4},{body:'fixed',material:'metal'});
 const w=new PRSELoop({id:'aabb-'+c.id,prose:'Two physical 3D objects with a testable surface distance.',entities:[a,b]});
 w.tick(3);
 const rel={kind:'object',type:'near',a:'stone',b:'lamp'};
 const first=measureRelation(w,rel);
 assert.equal(first.truth,c.expected,c.id);
 const journal=new PRSEGroundedFacts(w,[rel]);
 const savedWorld=PRSELoop.restore(JSON.parse(JSON.stringify(w.snapshot())));
 assert(savedWorld.ok);
 const known=PRSEGroundedFacts.restore(savedWorld.loop,[rel],JSON.parse(JSON.stringify(journal.snapshot())));
 assert.equal(known.current()[0].truth,c.expected);
 results.push({id:c.id,truth:first.truth,physicsReason:first.reason,
  actualDelta:{x:Math.abs(c.a.x-c.b.x),y:Math.abs(c.a.y-c.b.y),z:Math.abs(c.a.z-c.b.z)},
  afterNativeSave:known.current()[0].truth});
 savedWorld.loop.dispose();w.dispose();
}
const outcome={
 provenance:{task:'PRSE physically grounded near-relation correctness in three real dimensions',
 method:'Native PRSELoop/GameCore/Rapier fixed bodies and saved/reloaded physics',
 priorNegativeSources:['prse_false_near_vertical_gap_prefixed_negative.json',
    'prse_false_diagonal_near_before_distance_fix.json'],
 noExternalHumanExamplesClaimed:true},
 preFixCounterexamples:{verticalWrong:verticalBefore.wronglyVerified,
  diagonalWrong:diagonalBefore.incorrectIfNear},
 corrected:results};
writeFileSync(new URL('prse_3d_surface_distance_guard_results.json',import.meta.url),
 JSON.stringify(outcome,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,oldCounterexamplesRetained:2,
 verifiedCurrent3DRelations:results.map(x=>[x.id,x.truth])}));
