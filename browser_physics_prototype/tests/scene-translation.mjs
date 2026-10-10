import assert from 'node:assert/strict';
import {sceneProposal} from '../generated/llm-scene-proposal.js';
import {translateSceneToEntities,validatedShelterScene} from '../scene-translation.js';
import {validateWorldProposal,proposeRegion} from '../world-generator.js';
import {GameCore,initializePhysics} from '../physics-core.js';
assert.equal(validatedShelterScene.ok,true);
assert.ok(validatedShelterScene.rawPhysicalIssueCount>=2,'LLM numeric geometry must be corrected');
const objects=validatedShelterScene.entities,bench=objects.find(e=>e.kind==='bench');
for(const k of ['candle','note']){
 const e=objects.find(e=>e.kind===k);
 assert.ok(Math.abs(e.y-e.size.y/2-(bench.y+bench.size.y/2))<1e-8,`${k} physically supported by bench top`);
}
assert.ok(Math.abs(bench.y-bench.size.y/2)<1e-8,'bench on floor');
const jug=objects.find(e=>e.kind==='jug');
assert.ok(Math.abs(jug.y-jug.size.y/2)<1e-8,'jug on floor');
for(const objects2 of [sceneProposal.objects.map(e=>({...e,width:NaN})),[...sceneProposal.objects.slice(0,3),sceneProposal.objects[0]],sceneProposal.objects.map(e=>e.kind==='candle'?{...e,x:1e99}:e)]){
 assert.equal(translateSceneToEntities({...sceneProposal,objects:objects2}).ok,false);
}
assert.ok(validateWorldProposal(proposeRegion(0)).ok,'translated entities pass runtime validator');
await initializePhysics();
const game=new GameCore();game.player.setTranslation({x:34,y:.86,z:0},true);
for(let i=0;i<100;i++)game.step();
for(const e of objects){
 assert.ok(game.semantic.entity(e.id),`scene ${e.id} must exist`);
 assert.ok(game.worldBridge.active.has(e.id),`scene ${e.id} must be physically represented`);
}
const benchBody=game.worldBridge.active.get('shelter-bench');
const candleBody=game.worldBridge.active.get('shelter-candle');
assert.ok(Math.abs(benchBody.translation().y-.225)<1e-5,'grounded bench');
assert.ok(Math.abs(candleBody.translation().y-.525)<.06,`candle support ${candleBody.translation().y}`);
const save=game.snapshot(),fresh=new GameCore();
assert.ok(fresh.restore(save),'generated scene saves');
assert.equal(fresh.semantic.entity('shelter-note').description,game.semantic.entity('shelter-note').description);
console.log(JSON.stringify({passed:true,modelDurationSeconds:sceneProposal.elapsed_seconds,llmRawValid:sceneProposal.valid,corrections:validatedShelterScene.corrections,benchY:benchBody.translation().y,candleY:candleBody.translation().y,entityCount:objects.length}));
