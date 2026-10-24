// Independent adverse cases for GENERAL scene loop, not a playable acceptance test.
// Saves raw outcomes, including failures, without changing the existing game main.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object,geometryIssues} from './prse_semantic_roundtrip.mjs';
import {sceneProposal} from '../../generated/llm-scene-proposal.js';
import {translateSceneToEntities} from '../../scene-translation.js';
await initializePhysics();
const dynamic={id:'real3d-moving-scene',prose:'A rectangular wooden crate rests on a real floor. A diagonal impact drives it across the room.',
 entities:[object('movable-crate','crate',{x:-26,y:.3,z:9},{x:.6,y:.6,z:.55},{material:'wood',mass:4})]};
const world=new PRSELoop(dynamic),before=structuredClone(world.entities.get('movable-crate').position);
assert(world.applyImpulse('movable-crate',{x:8,y:12,z:30}));
world.tick(70);
const halfway=structuredClone(world.entities.get('movable-crate').position);
const out3d=Math.abs(halfway.z-before.z);
const snap=JSON.parse(JSON.stringify(world.snapshot()));
const candidate=PRSELoop.restore(snap);assert(candidate.ok);
const b=candidate.loop;
const immediateDist=Math.hypot(...['x','y','z'].map(k=>world.entities.get('movable-crate').position[k]-b.entities.get('movable-crate').position[k]));
world.tick(70);b.tick(70);
const o=world.entities.get('movable-crate'),p=b.entities.get('movable-crate');
const resumedError=Math.hypot(...['x','y','z'].map(k=>o.position[k]-p.position[k]));
const transform={start:before,after70:halfway,displacementZ:out3d,immediatePositionError:immediateDist,
 replay70PositionError:resumedError,post1:structuredClone(o.position),post2:structuredClone(p.position),
 detectedPhysicalEvents:world.events.length,sourceProseUnchanged:world.scene.prose===dynamic.prose,
 currentProse:world.scene.currentProse};
b.dispose();world.dispose();
const unburnt={id:'unburnt-scene',prose:'A sheet of paper lies on a workbench in an abandoned room.',
 entities:[
  object('long-workbench','bench',{x:-27,y:.45,z:8},{x:2.4,y:.9,z:1.1},{body:'fixed'}),
  object('clean-paper','paper',{x:-27,y:.91,z:8},{x:.2,y:.02,z:.18},{material:'paper',mass:.02,supportId:'long-workbench'})
 ]};
assert(!geometryIssues(unburnt).length);
const quiet=new PRSELoop(unburnt);quiet.tick(8);quiet.dematerialize();quiet.advanceOffscreen(60);
const unchanged=quiet.entities.get('clean-paper').state.condition==='intact';
const noInventedFire=quiet.events.every(e=>e.type!=='scorched'&&e.type!=='reduced_to_ashes');
const quietSaved=PRSELoop.restore(JSON.parse(JSON.stringify(quiet.snapshot())));
assert(quietSaved.ok);
const stillPresent=quietSaved.loop.materialize()===2&&quietSaved.loop.entities.get('clean-paper').state.condition==='intact';
const timeGap=Math.abs(quietSaved.loop.time-quietSaved.loop.game.time);
quietSaved.loop.dispose();quiet.dispose();
const oldModel=translateSceneToEntities(sceneProposal);
assert(oldModel.ok);
const modelReference={modelElapsedSeconds:sceneProposal.elapsed_seconds,
 rawModelValid:sceneProposal.valid,rawModelObjectCount:sceneProposal.objects.length,
 deterministicCorrections:oldModel.corrections.length,
 rawObjectRoles:sceneProposal.objects.map(e=>e.kind),
 liveModelWasCalledNow:false,
 noteRawPhysicsIssue:oldModel.corrections.some(e=>e.id==='note')};
const result={metadata:{source:'PRSE GameCore Rapier, prior authentic model shelter proposal from October 10 (reused, not rerun)',
 notProof:'No new LLM call; no general language parsing; no new scene assets or renderer; offscreen logic is a bounded research-only causal rule'},
 realThreeDimensionalImpulse:transform,
 noCauseNoDamage:{intact:unchanged,noHallucinatedFire:noInventedFire,
  rereadAfterLongOffscreen:stillPresent,
  semanticVsGameCoreTimeGapSeconds:timeGap},
 recordedModelProposal:modelReference};
assert(out3d>.2,'actual lateral 3D displacement missing');
assert(immediateDist<.002);
assert(unchanged&&noInventedFire&&stillPresent);
writeFileSync(new URL('prse_semantic_adversarial_results.json',import.meta.url),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result));
