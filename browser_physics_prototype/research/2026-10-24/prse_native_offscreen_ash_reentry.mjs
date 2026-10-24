// Native PRSE world-bridge re-entry check after offscreen fire; measures residual
// object identity/collider gaps without changing concurrent dirty production main.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from './prse_semantic_roundtrip.mjs';
import {narrateWorld} from '../../narrative-view.js';
await initializePhysics();
const shell=new PRSELoop({id:'native-shelter-residue-gap',
 prose:'A traveler returns to a shelter after a paper fire.',
 entities:[object('marker-stone','stone',{x:-26,y:.35,z:9},{x:.45,y:.7,z:.4},
   {material:'stone',body:'fixed'})]});
shell.tick(90);
shell.game.worldStreamer.update(36,1,shell.game.semantic,{});
const note=shell.game.semantic.entity('shelter-note'),candle=shell.game.semantic.entity('shelter-candle');
assert(note&&!note.materialized);
candle.state.lit=true;candle.revision++;
assert(shell.game.consequences.startPaperFire(shell.time,shell.game.semantic).ok);
shell.dematerialize();shell.advanceOffscreen(40);
assert(note.state.condition==='ashes');
const before=shell.game.snapshot();
shell.game.player.setTranslation({x:37,y:.86,z:0},true);
shell.game.player.setLinvel({x:0,y:0,z:0},true);
shell.game.world.updateSceneQueries();
shell.tick(3);
const nativeBody=shell.game.worldBridge.active.get('shelter-note');
const nativeCondition=shell.game.semantic.entity('shelter-note').state.condition;
const nativeSceneState=shell.game.state();
const visibleNote=nativeSceneState.visibleEntities.find(x=>x.id==='shelter-note');
const narrative=narrateWorld(nativeSceneState);
const result={
 semantic: {originalNoteStillPresent:shell.game.semantic.entity('shelter-note')!==null,
  noteCondition:nativeCondition,sourceID:'shelter-note',sourceTextPreserved:true},
 nativePhysical:{
  originalNoteBodyMaterialized:!!nativeBody,
  originalNoteColliderCount:nativeBody?nativeBody.numColliders():null,
  distinctAshEntityFound:!!shell.game.semantic.entity('ash-shelter-note'),
  sourceNoteVisibleInProjection:!!visibleNote,returnedLocation:{x:37,z:0}},
 narrative:{textClaimsAsh:narrative.toLowerCase().includes('ash'),
  textLeaksReadableWarning:narrative.toLowerCase().includes('warning of fire'),
  snippet:narrative.slice(0,400)},
 limitation:'Existing production-like GameCore renders ash through note state; it does not create a distinct physically colliding remnant identity. The research sidecar now tests one coarse fixed ash-body approach, NOT deployed.'};
assert(result.nativePhysical.originalNoteBodyMaterialized);
assert(result.nativePhysical.originalNoteColliderCount===0);
assert(!result.nativePhysical.distinctAshEntityFound);
assert(result.narrative.textClaimsAsh&&!result.narrative.textLeaksReadableWarning);
writeFileSync(new URL('prse_native_offscreen_ash_reentry_gap.json',import.meta.url),
 JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result));
shell.dispose();
