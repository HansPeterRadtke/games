// Actual local model prose -> independently validated spatial objects -> Rapier scene.
import assert from 'node:assert/strict';
import {GameCore,initializePhysics} from '../physics-core.js';
import {storyRegionBank} from '../generated/story-region-bank.js';
import {chooseLiteraryScene,sceneToEntities} from '../llm-region-adapter.js';
import {validateWorldProposal} from '../world-generator.js';
await initializePhysics();assert.equal(storyRegionBank.scenes.length,4,'two game history decisions must produce four model-authored variants');
for(const scene of storyRegionBank.scenes){
 const result=sceneToEntities(scene);assert.equal(result.ok,true,`Invalid generated scene: ${result.error}`);const game=new GameCore();
 assert.equal(validateWorldProposal(result.entities,new Set(game.semantic.entities.map(e=>e.id))).ok,true,`Invalid converted physics entities: ${scene.branch}`);
 game.semantic.entities.push(...structuredClone(result.entities));game.worldStreamer.generated.push(scene.region);const anchor=scene.anchor;
 game.player.setTranslation({x:anchor-2,y:.86,z:0},true);game.player.setLinvel({x:0,y:0,z:0},true);
 for(let i=0;i<140;i++)game.step();
 const body=game.worldBridge.active.get(`region-${scene.region}-landmark`);assert.ok(body,`Model-authored scene did not enter visible/physical world for ${scene.branch}`);
 const visible=game.state().visibleEntities.filter(e=>e.id.startsWith(`region-${scene.region}-`));assert.ok(visible.length>=2,`Insufficient visible objects in scene ${scene.branch}`);
 assert.ok(body.translation().z>1,'3D source-to-physics relationship must preserve off-lane depth');
 assert.equal(visible.find(e=>e.id===`region-${scene.region}-landmark`).source,scene.source,'visible content must retain LLM provenance');
 const snapshot=game.snapshot(),copy=new GameCore();assert.equal(copy.restore(snapshot),true,`Save and restore of generated scene failed ${scene.branch}`);
 assert.equal(copy.semantic.entity(`region-${scene.region}-landmark`).description,scene.description,'Literary description lost after save/load');
 const before=copy.semantic.entity(`region-${scene.region}-landmark`);before.description+=' The player remembers this location.';before.revision++;const again=copy.snapshot(),againCore=new GameCore();assert.ok(againCore.restore(again));assert.equal(againCore.semantic.entity(before.id).description,before.description,'Human revisions overwritten during restore');
 console.log('VALIDATED_LLM_REGION',scene.branch,'playerX',game.state().player.x.toFixed(1),'objects',visible.length,'3DPosition',JSON.stringify(body.translation()),'source',scene.source);
}
const saved=chooseLiteraryScene(storyRegionBank.scenes,1,{bridgeRepaired:true}),broken=chooseLiteraryScene(storyRegionBank.scenes,1,{bridgeRepaired:false});assert.ok(saved&&broken&&saved.title!==broken.title);assert.notEqual(saved.description,broken.description);
const active=chooseLiteraryScene(storyRegionBank.scenes,2,{mechanismOpen:true}),locked=chooseLiteraryScene(storyRegionBank.scenes,2,{mechanismOpen:false});assert.ok(active&&locked&&active.description!==locked.description);
console.log('PASS: 4 validated local-LLM world variants + causal selection + materialization + persistence');
