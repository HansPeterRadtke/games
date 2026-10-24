// Tests absence of offscreen fact leakage, truthful current state on return,
// explicit causal support loss, and stable identity across save/re-entry.
// Research-only GameCore Rapier adapter; no live server.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object} from './prse_semantic_roundtrip.mjs';
await initializePhysics();
const scene={id:'perception-and-support-scene',
 prose:'The ceramic pot stands on a wooden table; a paper sheet nearby is intact.',
 entities:[
  object('oak-table','table',{x:-25,y:.5,z:9},{x:2,y:1,z:1.5},{body:'fixed',material:'wood'}),
  object('ceramic-pot','pot',{x:-25,y:1.2,z:9},{x:.35,y:.4,z:.35},
   {supportId:'oak-table',material:'ceramic',mass:1.2}),
  object('loose-note','note',{x:-24.3,y:1.01,z:9},{x:.2,y:.02,z:.2},
   {supportId:'oak-table',material:'paper',mass:.04})
 ]};
const loop=new PRSELoop(scene);
loop.tick(30);
const untouched=loop.entities.get('ceramic-pot');
assert.equal(untouched.supportId,'oak-table');
assert(!loop.events.some(e=>e.type==='lost_support'),'no spontaneous false support loss');
const playerPrior={...loop.game.player.translation()};
assert.equal(loop.visibleIds().length,0,'far-away game player somehow sees the distant table');
assert.equal(loop.narrate().text,'','no explicit player observation must leak remote events');
loop.dematerialize();
assert(loop.igniteOffscreen('loose-note'));
loop.advanceOffscreen(16);
const remoteEvents=loop.narrate(),remoteProse=loop.describe();
assert.equal(remoteEvents.text,'','remote offscreen fire leaked to the player');
assert.equal(remoteProse,'','internal offscreen prose leaked through player description');
assert.equal(loop.scene.currentProse.includes('ash'),true,'internal semantic fact missing');
const saved=loop.snapshot(),forged=structuredClone(saved);
forged.scene.currentProse='The note is intact and readable.';
const loaded=PRSELoop.restore(forged);
assert(loaded.ok);
const copy=loaded.loop;
assert(!copy.scene.currentProse.includes('intact and readable'),'forged outdated prose overrode authoritative state');
assert(copy.scene.currentProse.includes('ash'),'current prose did not regenerate from saved facts');
const sidecarNativeTimeError=Math.abs(copy.game.time-copy.time);
const afterCopyNoLeak=copy.narrate().text.length===0;
const returned=copy.materialize();
assert(returned===3&&copy.active.has('ash-loose-note')&&copy.entities.has('loose-note')&&!copy.active.has('loose-note'),
 'ash tombstone must persist but not resurrect physical paper');
copy.game.player.setTranslation({x:-25,y:.86,z:9},true);
copy.game.player.setLinvel({x:0,y:0,z:0},true);
copy.game.world.updateSceneQueries();
const visible=copy.visibleIds();
assert(visible.includes('loose-note'));
const observed=copy.narrate(),description=copy.describe();
assert(observed.text.includes('scorched')&&observed.text.includes('ashes'));
assert(description.includes('Ash from note remains at the former location'));
assert(description.split('Ash from note').length===2,'remnant should be narrated once, not as two independent objects');
assert.equal(copy.narrate(observed.cursor).text,'','observer must not repeat already shown events');
const afterReloadIds=[...copy.entities.keys()];
copy.dispose();loop.dispose();

const supportScene={id:'physical-support-drop-scene',
 prose:'A small ceramic pot rests on a wooden platform.',
 entities:[
  object('platform-1','platform',{x:-25,y:.5,z:9},{x:2,y:1,z:1.5},
   {body:'fixed',material:'wood'}),
  object('pot-1','pot',{x:-25,y:1.2,z:9},{x:.35,y:.4,z:.35},
   {supportId:'platform-1',material:'ceramic',mass:1.0})
 ]};
const attempt=new PRSELoop(supportScene);
attempt.tick(25);
assert(attempt.applyImpulse('pot-1',{x:12,y:4,z:1}));
attempt.tick(130);
const pot=attempt.entities.get('pot-1'),supportLost=attempt.events.filter(e=>e.type==='lost_support');
const supportResult={potPosition:pot.position,potSupport:pot.supportId,
 supportEvents:supportLost,sourceProseUnchanged:attempt.scene.prose===supportScene.prose,
 currentFactText:attempt.scene.currentProse,events:attempt.events.filter(e=>e.ids.includes('pot-1')).map(e=>e.type)};
const persisted=PRSELoop.restore(JSON.parse(JSON.stringify(attempt.snapshot())));
assert(persisted.ok);
assert.equal(persisted.loop.entities.get('pot-1').supportId,pot.supportId,
 'saved physical support fact was reset to original author scene');
persisted.loop.dispose();attempt.dispose();
assert.equal(pot.supportId,null,'physical loss of support was not projected to semantic relation');
assert(supportLost.length>=1);
const data={metadata:{scope:'Existing GameCore research adapter; observer distance only, not occlusion',
  method:'Real Rapier dynamic pot impulse and explicit offscreen semantic burn; no LLM inference',
  sourceProseIsHistorical:true},before:{remotePlayer:playerPrior,offscreenNoEventsLeaked:remoteEvents.text.length===0,
  offscreenNoCurrentDescriptionLeaked:remoteProse.length===0,
  noSpontaneousSupportLoss:true},
 offscreen:{nativeTimeError:sidecarNativeTimeError,
  acceptedForgedOldCurrentProseButRecomputed:true,offscreenNoLeakAfterRestore:afterCopyNoLeak},
 reentry:{rematerializedBodies:returned,visibleIds:visible,events:observed,
  description,stableIds:afterReloadIds,duplicateAfterCursor:0},
 support:supportResult};
const output=process.argv.find(x=>x.startsWith('--output='))?.slice(9)||'prse_observer_latest_results.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(output))throw Error('unsafe output name');
writeFileSync(new URL(output,import.meta.url),
 JSON.stringify(data,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,remoteText:remoteProse,noLeak:afterCopyNoLeak,
 nativeClockDelta:sidecarNativeTimeError,reentry:description,
 causalSupportLoss:supportLost.length,potSupport:pot.supportId}));
