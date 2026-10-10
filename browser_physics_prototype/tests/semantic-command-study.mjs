import assert from 'node:assert/strict';
import {resolveNaturalAction}from '../semantic-command.js';
import {initializePhysics,GameCore}from '../physics-core.js';
await initializePhysics();
const g=new GameCore();g.player.setTranslation({x:37,y:.86,z:0},true);for(let i=0;i<45;i++)g.step();
const yes=[
 ['Please light the beeswax candle', 'shelter-candle','light'],
 ['blow out the candle','shelter-candle','extinguish'],
 ['put out the flame','shelter-candle','extinguish'],
 ['read handwritten note','shelter-note','read'],
 ['burn the note','shelter-note','ignite'],
 ['set the paper on fire','shelter-note','ignite'],
 ['pour the jug','shelter-jug','pour'],
 ['splash the water','shelter-jug','pour'],
 ['examine the long oak bench','shelter-bench','inspect'],
 ['inspect the hut','shelter-setting','inspect'],
 ['tell traveler','wanderer-1','tell'],
 ['talk to wanderer','wanderer-1','talk'],
 ['knock the candle','shelter-candle','tip'],
];
const no=[
 'light the jug','read the candle','burn water','take candle','ignite bench',
 'make magic','use it','attack the bear','blow it up','light the candle and read the note',
 'pour note','jump over bench','destroy the world','walk into fire',
];
for(const [text,targetId,verb] of yes){const result=resolveNaturalAction(text,g.semantic,g.player.translation());assert.ok(result.ok,`${text}: ${result.reason}`);assert.equal(result.targetId,targetId);assert.equal(result.verb,verb);}
for(const text of no){const result=resolveNaturalAction(text,g.semantic,g.player.translation());assert.equal(result.ok,false,`dangerous/unknown command was interpreted: ${text} -> ${JSON.stringify(result)}`);}
const count=g.events.length,prior=g.semantic.entity('shelter-candle').state.lit;assert.equal(prior,false);const invalid=g.textCommand('light the jug');assert.ok(invalid.includes('No supported action'));assert.equal(g.events.length,count,'invalid language cannot cause gameplay event');assert.equal(g.semantic.entity('shelter-candle').state.lit,false);
const good=g.textCommand('Please light the beeswax candle');assert.ok(good.includes('light the candle'));assert.equal(g.semantic.entity('shelter-candle').state.lit,true);
const putout=g.textCommand('put out the flame');assert.ok(putout.includes('snuff'));assert.equal(g.semantic.entity('shelter-candle').state.lit,false);
const away=new GameCore();away.player.setTranslation({x:34,y:.86,z:0},true);for(let i=0;i<50;i++)away.step();away.player.setTranslation({x:-4.1,y:.86,z:0},true);for(let i=0;i<8;i++)away.step();assert.ok(away.textCommand('read handwritten note').includes('out of reach'),'valid commands still honor physical reach');
const oldText=g.semantic.entity('shelter-note').description;assert.ok(g.textCommand('read the note').includes('handwriting'));assert.equal(g.semantic.entity('shelter-note').description,oldText);
console.log(JSON.stringify({passed:true,recognized:yes.length,rejected:no.length,actualActions:['light','extinguish','read'],noUntrustedCode:true,physicsReachEnforced:true}));
