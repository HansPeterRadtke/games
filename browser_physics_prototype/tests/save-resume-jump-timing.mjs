import assert from 'node:assert/strict';
import {initializePhysics,GameCore} from '../physics-core.js';
await initializePhysics();

// Prescribed acceptance: a player who saves after requesting a jump must still jump
// on the next authoritative step after restore, without an invented recovery cooldown.
const game=new GameCore();
for(let i=0;i<45;i++)game.step();
assert(game.grounded(),'fixture must be on solid ground');
assert(game.command({type:'Jump'}));
const snap=JSON.parse(JSON.stringify(game.snapshot()));
assert.equal(snap.jumpRequested,true);
const copy=new GameCore();assert(copy.restore(snap));
assert.equal(copy.jumpRequested,true);
assert.equal(copy.nextJumpAt,game.nextJumpAt);
assert.equal(copy.grounded(),true,'grounded query must be accurate immediately after restoring transforms');
game.step();copy.step();
assert(game.events.some(e=>e.type==='jump'),'reference jump must be physical');
assert(copy.events.some(e=>e.type==='jump'),'restored pending jump must actually happen');
assert(Math.abs(game.player.linvel().y-copy.player.linvel().y)<.002,'next step must preserve jump velocity');

// The physical spring/cooldown gate must survive snapshot as well.
const midair=JSON.parse(JSON.stringify(game.snapshot()));
const after=new GameCore();assert(after.restore(midair));
assert.equal(after.nextJumpAt,game.nextJumpAt);
assert.equal(after.jumpRequested,false);

// Corrupt timing fields cannot enter the game.
for(const value of [-1,Infinity,NaN,midair.time+10,'tomorrow']){
 const bad={...midair,nextJumpAt:value};
 assert.equal(new GameCore().restore(bad),false);
}
for(const key of ['jumpRequested','lastObstacleContact']){
 assert.equal(new GameCore().restore({...midair,[key]:'yes'}),false);
}
const old={...midair};delete old.nextJumpAt;delete old.jumpRequested;delete old.lastObstacleContact;
assert(new GameCore().restore(old),'old v5 saves remain readable');
console.log(JSON.stringify({passed:true,pendingJumpRetained:true,cooldownRetained:true,
 oldSaveReadable:true,invalidValuesRejected:7}));
