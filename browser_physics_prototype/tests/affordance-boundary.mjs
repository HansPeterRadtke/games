import assert from 'node:assert/strict';
import {safeAffordances} from '../generated/llm-affordances.js';
import {sceneProposal}from '../generated/llm-scene-proposal.js';
import {validateWorldProposal,proposeRegion}from '../world-generator.js';
import {initializePhysics,GameCore}from '../physics-core.js';
assert.equal(safeAffordances.accepted.length,3,'local model suggested three valid actions');
const proposal=proposeRegion(0);assert.equal(validateWorldProposal(proposal).ok,true);
const candle=proposal.find(e=>e.id==='shelter-candle');const note=proposal.find(e=>e.id==='shelter-note');const jug=proposal.find(e=>e.id==='shelter-jug');
assert.equal(candle.affordances[0].label,'Light the candle');assert.equal(note.affordances[0].label,'Read the note');assert.equal(jug.affordances[0].label,'Pour water from the jug');
for(const actions of [[{verb:'extinguish',label:'Wrong',origin:'llm-validated',promptHash:'123456abcdef'}],[{verb:'inspect',label:'<script>unsafe</script>',origin:'dynamic',promptHash:'123456abcdef'}]]){
 const bad=proposal.map(e=>e.id==='shelter-bench'?{...e,affordances:actions}:e);assert.equal(validateWorldProposal(bad).ok,false,'hallucinated object-verb pair must not be executable');
}
await initializePhysics();const g=new GameCore();g.player.setTranslation({x:37.35,y:.86,z:0},true);for(let i=0;i<50;i++)g.step();
assert.ok(g.state().visibleEntities.find(e=>e.id==='shelter-candle').affordances.length>0,'generated safe actions survive semantic->physical->UI');
assert.equal(g.command({type:'Interact',targetId:'shelter-bench',verb:'extinguish'}),false,'core rejects invalid model action');
console.log(JSON.stringify({passed:true,sceneObjects:sceneProposal.objects.length,safeAffordances:safeAffordances.accepted.length,rejectedFromGenerator:4,typedInteractionConfirmed:true}));
