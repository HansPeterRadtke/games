// Externally authored SceneEval description -> machine-parsed typed relation
// -> actual GameCore Rapier 3D placement -> physical knock-off -> revised semantic
// fact -> observer-correct narration -> save/offscreen/reentry.
// This SINGLE SELECTED EXAMPLE is illustrative after corpus benchmarking,
// not independently held-out model performance.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {compileProposal} from './prse_constraint_layout.mjs';
import {readResearchEvidence} from './prse_research_evidence_io.mjs';
import {PRSELoop} from './prse_semantic_roundtrip.mjs';
await initializePhysics();
const proposals=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_v2.json')).proposalsFirst100;
const original=proposals.find(p=>p.sourceId==='22');
assert(original.text.includes('lamp on the nightstand'));
const planned=compileProposal(original);
assert(planned.good&&planned.proposed===6);
const on=planned.relations.find(r=>r.type==='on'&&r.a==='lamp'&&r.b==='nightstand');
assert(on&&on.grounded);
const g=new PRSELoop(planned.scene);
g.tick(20);
const lamp=g.scene.entities.find(e=>e.kind==='lamp'),nightstand=g.scene.entities.find(e=>e.kind==='nightstand');
assert(lamp&&nightstand&&lamp.supportId===nightstand.id);
assert(g.active.has(lamp.id));
const pre={
 oldLiterarySource:g.scene.prose,
 sourceId:original.sourceId,
 lampId:lamp.id,nightstandId:nightstand.id,
 supportId:lamp.supportId,
 nativePhysicalPosition:{...g.active.get(lamp.id).translation()},
 nowNarration:g.scene.currentProse,
 nativeTime:g.game.time,
 semanticTime:g.time
};
assert(pre.nowNarration.includes('lamp 1 is present; resting on nightstand 1'));
const remoteBefore=g.narrate().text;
assert(!remoteBefore,'distant default player must not receive observer-invisible event');
const observer={x:lamp.position.x,y:1.4,z:lamp.position.z};
const beforeView=g.describe(g.visibleIds(observer,8));
assert(beforeView.includes('lamp 1 is present; resting on nightstand 1'));
const hit={x:6,y:2,z:1};
assert(g.applyImpulse(lamp.id,hit),'actual GameCore impulse was rejected');
g.tick(90);
const off=g.entities.get(lamp.id);
const causal=g.events.filter(e=>e.type==='lost_support'&&e.ids[0]===lamp.id);
assert(causal.length>=1,'physics did not invalidate support relationship');
assert.equal(off.supportId,null);
assert.equal(off.state.dislodgedFrom,nightstand.id);
const changed=g.describe(g.visibleIds(observer,9));
const changedEvents=g.narrate(0,g.visibleIds(observer,9));
assert(changed.includes('no longer on nightstand 1'));
assert(changedEvents.text.includes('no longer supported by nightstand 1'));
assert.equal(g.narrate(changedEvents.cursor,g.visibleIds(observer,9)).text,'');
const snapshot=JSON.parse(JSON.stringify(g.snapshot()));
const r=PRSELoop.restore(snapshot);
assert(r.ok,'save reload failed');
const v=r.loop,loadedLamp=v.entities.get(lamp.id);
assert(loadedLamp.id===lamp.id);
assert(loadedLamp.state.dislodgedFrom===nightstand.id);
assert(loadedLamp.supportId===null);
assert.equal(v.scene.prose,pre.oldLiterarySource);
assert(v.scene.currentProse.includes('no longer supported by nightstand 1'));
const loadedPosition={...v.active.get(lamp.id).translation()};
const beforeUnload={...loadedPosition};
const player=v.game.player.translation();
assert(Math.abs(player.x-observer.x)>3);
const dematerialized=v.dematerialize();
assert(dematerialized>0);
const t=v.time;v.advanceOffscreen(5);
assert(Math.abs(v.time-(t+5))<1e-6&&v.active.size===0);
const afterOffscreen=v.entities.get(lamp.id).position;
const reentered=v.materialize();
assert(reentered===planned.scene.entities.length);
assert(v.active.has(lamp.id));
const reentryPose={...v.active.get(lamp.id).translation()};
const reentryError=Math.hypot(...['x','y','z'].map(k=>beforeUnload[k]-reentryPose[k]));
assert(reentryError<.005);
assert(v.entities.get(lamp.id).supportId===null);
const detailed=v.describe(v.visibleIds(observer,9));
assert(detailed.includes('no longer on nightstand 1'));
const output={
 provenance:{source:'SceneEval-500 human-authored row 22; learned/regex parser output, NOT manual object poses',
  sourceText:original.text,postSelectionIllustration:true,
  modelCalls:0,physics:'existing GameCore Rapier 3D',limitation:'One selected case; manual impulse is an intentional experiment, not human gameplay'},
 parsed: {sceneId:planned.sourceId,objects:planned.proposed,
   relationExtracted:on,initialValid:planned.good},
 before:pre,initialObserverText:beforeView,remoteNoLeak:remoteBefore==='',
 afterPhysical:{
  impulse:hit,finalPosition:{...off.position},
  supportRemoved:off.supportId===null,formerSupport:off.state.dislodgedFrom,
  typedEvents:causal,changeNarration:changed,eventsNarrated:changedEvents.text,
  repeatedEventCount:g.narrate(changedEvents.cursor,g.visibleIds(observer,9)).usedSequences.length},
 saveReentry:{
  originalProseUnchanged:v.scene.prose===original.text,
  stableIdentity:loadedLamp.id===lamp.id,
  persistedSupportLoss:loadedLamp.state.dislodgedFrom===nightstand.id,
  loadedPosition,dematerializedBodies:dematerialized,
  offscreenSeconds:5,nativeTime:v.game.time,sidecarTime:v.time,
  physicalBodiesOnReentry:reentered,positionErrorMeters:reentryError,
  finalNarration:detailed}
};
writeFileSync(new URL('prse_external_text_causal_relationship_roundtrip.json',import.meta.url),
 JSON.stringify(output,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,sourceRow:22,recognizedRelation:'lamp on nightstand',
 originalCount:planned.proposed,physicalSupportLoss:causal.length,
 saveError:reentryError,finalProse:detailed.slice(0,250)}));
v.dispose();g.dispose();
