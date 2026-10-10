import assert from 'node:assert/strict';
import {GameCore,initializePhysics} from '../physics-core.js';
import {storyRegionBank} from '../generated/story-region-bank.js';
await initializePhysics();
const wanted=(region,branch)=>storyRegionBank.scenes.find(e=>e.region===region&&e.branch===branch);
function advance(game,x,ticks=60){game.player.setTranslation({x,y:1.02,z:0},true);game.player.setLinvel({x:0,y:0,z:0},true);for(let i=0;i<ticks;i++)game.step();}
for(const repaired of [false,true]){
 const g=new GameCore();g.character.bridgeRepaired=repaired;
 advance(g,27);const story=wanted(1,repaired?'bridge_repaired':'bridge_unrepaired');
 const e=g.semantic.entity('region-1-landmark');assert.ok(e,'future scene not generated');assert.equal(e.description,story.description,'player behavior did not select correct LLM-authored branch');
 assert.equal(e.source,story.source,'LLM source lineage lost');const name=e.name;
 // Retrospective edits to the state cannot erase already-generated, persistent text.
 g.character.bridgeRepaired=!repaired;advance(g,42);assert.equal(g.semantic.entity(e.id).description,story.description,'existing world retroactively rewritten when player behavior changes');
 assert.ok(g.worldBridge.active.has(e.id),'selected prose did not materialize into a Rapier scene');
 const restored=new GameCore();assert.equal(restored.restore(g.snapshot()),true);assert.equal(restored.semantic.entity(e.id).description,story.description);
 console.log('REAL_PLAYER_BRIDGE_BRANCH',repaired,story.title,'source=',story.source,'visible=',g.state().visibleEntities.some(x=>x.id===e.id));
}
for(const open of [false,true]){
 const g=new GameCore();g.character.fenceOpened=open;advance(g,40);const story=wanted(2,open?'mechanism_open':'mechanism_closed');const e=g.semantic.entity('region-2-landmark');assert.ok(e);assert.equal(e.description,story.description);console.log('MECHANISM_STORY_BRANCH',open,story.title);
}
console.log('PASS: game-state-dependent LLM-authored region generation, physical materialization, no retroactive retcon, full save/reload.');
