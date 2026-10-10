// End-to-end gameplay test: only public core commands and actual Rapier integration.
import assert from 'node:assert/strict';
import {initializePhysics,GameCore,SETTINGS as S}from '../physics-core.js';
await initializePhysics();const g=new GameCore();const run=n=>{for(let i=0;i<n;i++)g.step();};
run(90);
// Walk left to the timber pile, allow physical planks to settle, collect two.
g.command({type:'Move',direction:-1});let walkToPlanks=0;while(g.state().nearby?.kind!=='plank'&&walkToPlanks++<240)g.step();assert.ok(walkToPlanks<240,'planks must be reachable by walking');g.command({type:'Move',direction:0});run(8);
for(let i=0;i<2;i++){const ok=g.command({type:'Interact'});assert.ok(ok,`physical plank ${i+1} must be in reach: ${g.events.at(-1).message}`);g.step();}
assert.equal(g.character.inventory.plank,2);const heavySpeed=g.character.locomotion().speedFactor;assert.ok(heavySpeed<1,'carried mass must affect locomotion');
// The semantic goal must use the same simulation path as physical keyboard movement.
assert.equal(g.command({type:'Goal',intent:'crossFence'}),true);let crossTicks=0;while(!g.events.some(e=>e.type==='goal_success')&&crossTicks++<950)g.step();assert.ok(crossTicks<950,'semantic goal must cross real fence carrying timber');assert.equal(g.goal,null);
// Continue walking and stop at actual interactive object, no world teleport.
g.command({type:'Move',direction:1});let workTicks=0;while(g.state().nearby?.kind!=='workbench'&&workTicks++<850)g.step();assert.ok(workTicks<850,`workshop unreachable, x=${g.state().player.x}`);g.command({type:'Move',direction:0});run(6);
assert.equal(g.command({type:'Interact'}),true,g.events.at(-1).message);assert.ok(g.character.bridgeRepaired);assert.equal(g.character.inventory.plank,0);assert.equal(g.semantic.entity('bridge-1').state.repaired,true);run(3);assert.ok(g.worldBridge.active.has('bridge-1'),'repaired bridge collider must physically exist near player');
// Walking over the repaired bridge must reach far bank without respawn.
const respawns=g.events.filter(e=>e.type==='respawn').length;g.command({type:'Move',direction:1});let finishTicks=0,jumpedCrate=false;while(!g.character.farBankReached&&finishTicks++<350){if(!jumpedCrate&&g.state().player.x>=20.45&&g.grounded()){g.command({type:'Jump'});jumpedCrate=true;}g.step();}assert.ok(g.character.farBankReached,`player did not cross repaired bridge ${g.state().player.x}`);assert.equal(g.events.filter(e=>e.type==='respawn').length,respawns,'crossing physical bridge must not respawn the character');
const snapshot=g.snapshot(),copy=new GameCore();assert.equal(copy.restore(snapshot),true);assert.deepEqual(copy.character.snapshot(),g.character.snapshot());assert.equal(copy.worldBridge.active.has('bridge-1'),g.worldBridge.active.has('bridge-1'),'bridge materialization should persist');assert.equal(copy.semantic.entity('bridge-1').state.repaired,true);assert.ok(Math.abs(copy.state().player.x-g.state().player.x)<.0001);
console.log(JSON.stringify({passed:true,stages:['walk_to_timber','pickup_two_physical_logs','load_affects_movement','semantic_fence_goal','walk_to_bridge','repair_with_resources','cross_physical_bridge','save_everything'],walkToPlanks,crossTicks,workTicks,finishTicks,playerX:g.state().player.x,character:g.character.snapshot()}));
