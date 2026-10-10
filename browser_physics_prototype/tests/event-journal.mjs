import assert from 'node:assert/strict';import{initializePhysics,GameCore}from '../physics-core.js';await initializePhysics();
const core=new GameCore();for(let i=0;i<170;i++)core.emit('test_event',`event ${i}`,{cause:'test',visibility:'visible'});
assert.equal(core.events.length,100,'bounded event journal');assert.equal(core.events[0].sequence,71,'oldest evicted event retains globally monotonic numbering');assert.equal(core.eventSequence,170);assert.equal(core.events.at(-1).sequence,170);
const snapshot=core.snapshot(),restored=new GameCore();assert.ok(restored.restore(snapshot));assert.equal(restored.eventSequence,170);restored.emit('after_save','event after save');assert.equal(restored.events.at(-1).sequence,171,'sequence must never restart on save/reload');
assert.equal(new Set(restored.events.map(e=>e.sequence)).size,restored.events.length,'no duplicate event keys');
console.log(JSON.stringify({passed:true,boundedEvents:core.events.length,lastSequence:restored.eventSequence,restoredContinuity:true}));
