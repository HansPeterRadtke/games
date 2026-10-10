import assert from 'node:assert/strict';
import {initializePhysics,GameCore}from '../physics-core.js';
import {TextAdapter}from '../text-adapter.js';
import {sceneProposal}from '../generated/llm-scene-proposal.js';
await initializePhysics();
const g=new GameCore(),step=n=>{for(let i=0;i<n;i++)g.step();};
function place(x){g.player.setTranslation({x,y:.86,z:0},true);g.player.setLinvel({x:0,y:0,z:0},true);step(6);}
place(37);const text=new TextAdapter(g),original=text.describe();assert.ok(original.includes('rain-worn wooden shelter'),'scene should use LLM-created literary text');
assert.ok(original.includes('beeswax candle'));
assert.ok(g.command({type:'Interact',targetId:'shelter-note',verb:'read'}));assert.ok(g.character.knows('warning_note'));
assert.ok(g.command({type:'Interact',targetId:'shelter-candle',verb:'light'}));assert.ok(g.command({type:'Interact',targetId:'shelter-note',verb:'ignite'}));
place(27);step(2440);const hiddenText=text.describe();assert.ok(!hiddenText.toLowerCase().includes('smoke')&&!hiddenText.toLowerCase().includes('ash'),'off-screen state must not leak into text description');
place(35);const aftermath=text.describe();assert.ok(aftermath.toLowerCase().includes('soot')||aftermath.toLowerCase().includes('smoke'));assert.ok(aftermath.toLowerCase().includes('ash'));
assert.ok(!aftermath.includes('warning of fire in the old woods'),'text must not quote a destroyed physical note');assert.ok(g.character.knows('warning_note'),'earlier learned knowledge survives paper destruction');
const saved=g.snapshot(),reloaded=new GameCore();assert.ok(reloaded.restore(saved));assert.equal(new TextAdapter(reloaded).describe(),aftermath,'prose state must survive snapshot');
console.log(JSON.stringify({passed:true,initialProse:original.slice(0,190),aftermathProse:aftermath.slice(0,260),modelSceneId:sceneProposal.scene_id,knownFacts:g.character.knowledge.length}));
