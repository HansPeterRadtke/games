// Extended identity and unsafe-scheduling guards for the research-only PRSE adapter.
// All fixtures are authored edge cases; none represent a model or a human playtest.
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object,validateScene} from './prse_semantic_roundtrip.mjs';
await initializePhysics();
const longName='paper-'+'x'.repeat(72);
assert(longName.length>76&&longName.length<=80);
const longScene={id:'long-lineage-provenance',
 prose:'A fragile paper object with a long stable identifier burns while the player is away.',
 entities:[object(longName,'note',{x:-25,y:.01,z:9},{x:.2,y:.02,z:.15},
  {material:'paper',mass:.1})]};
const first=new PRSELoop(longScene,{startMaterialized:false});
assert(first.igniteOffscreen(longName));
first.advanceOffscreen(9);
const ash=first.scene.entities.find(x=>x.originId===longName);
assert(ash&&ash.id.length<=80&&ash.id.startsWith('ash-'));
assert(validateScene(first.scene).ok,'remnant lineage violated scene validation');
const restored=PRSELoop.restore(JSON.parse(JSON.stringify(first.snapshot())));
assert(restored.ok&&restored.loop.entities.get(ash.id).originId===longName);
const active=restored.loop.materialize();
assert(active===1&&!restored.loop.active.has(longName)&&restored.loop.active.has(ash.id));
const bad=JSON.parse(JSON.stringify(first.snapshot()));
bad.scene.entities.find(x=>x.id===ash.id).originId='nonexistent-parent';
const invalidOriginRejected=!PRSELoop.restore(bad).ok;
assert(invalidOriginRejected);
const longOutcome={sourceIdLength:longName.length,physicalRemnantIdLength:ash.id.length,
 explicitOriginReferenceVerified:true,rematerializedRemnant:active,
 forgedOriginRejected:invalidOriginRejected};
restored.loop.dispose();first.dispose();

const fullEntries=[];
for(let i=0;i<319;i++){
 fullEntries.push(object('filler-'+i.toString(36).padStart(3,'0'),'placeholder',
  {x:-31+(i%16)*1.8,y:.25,z:7+Math.floor(i/16)*1.8},{x:.25,y:.5,z:.25},
  {body:'fixed',material:'wood'}));
}
fullEntries.push(object('capacity-paper','note',{x:-25,y:.01,z:9},{x:.2,y:.02,z:.2},{material:'paper'}));
const capped=new PRSELoop({id:'capacity-320',prose:'An extremely full remote region has one combustible note.',entities:fullEntries},
 {startMaterialized:false,checkGeometry:false});
assert(capped.scene.entities.length===320);
assert(capped.igniteOffscreen('capacity-paper'));
const timeBefore=capped.game.time;let thrown=false;
try{capped.advanceOffscreen(9);}catch(e){thrown=/capacity/.test(e.message);}
assert(thrown);
assert(capped.game.time===timeBefore&&capped.time===timeBefore);
assert(capped.entities.get('capacity-paper').state.condition==='scorched');
assert(capped.offscreenRules.length===1);
const atCapacity={rejected:true,unchangedGameTime:capped.game.time,
 causalEntryStillPending:capped.offscreenRules.length,regionSize:capped.scene.entities.length};
capped.dispose();
const source={id:'active-goal-refusal',
 prose:'The offscreen scene cannot silently skip a live player goal.',
 entities:[object('single-block','block',{x:-25,y:.25,z:9},{x:.5,y:.5,z:.5},
  {body:'fixed',material:'stone'})]};
const goalGuard=new PRSELoop(source,{startMaterialized:false});
assert(goalGuard.game.command({type:'Goal',intent:'wait',duration:10}));
let prevented=false;try{goalGuard.advanceOffscreen(15);}catch(e){prevented=e.message.includes('goal');}
assert(prevented&&goalGuard.game.time===0&&goalGuard.time===0);
goalGuard.dispose();
const out={metadata:{method:'GameCore research sidecar identity/time guard adversarial fixtures; no live world',
 resultsNotRepresentative:'These guards are bounded and do not prove arbitrary generated-world security'},
 stableDerivedPhysicalRemnant:longOutcome,
 boundedCapacityBehavior:atCapacity,
 activeGoalSkipsRefused:prevented};
writeFileSync(new URL('prse_ash_lineage_capacity_guard_results.json',import.meta.url),
 JSON.stringify(out,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,longOutcome,atCapacity,prevented}));
