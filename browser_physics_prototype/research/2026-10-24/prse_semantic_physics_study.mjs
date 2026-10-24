// Three distinct evidence layers:
// 1. External SceneEval descriptions, *manually mapped* physical instance plans.
// 2. Actual authoritative GameCore / Rapier 3D simulation, event capture and persistence.
// 3. Separate synthetic scalability stress and adversarial invalid-scene rejection.
// Explicit physical scene plans are not proof of unconstrained text parsing.
import assert from 'node:assert/strict';
import {writeFileSync,readFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {object,PRSELoop,validateScene,geometryIssues} from './prse_semantic_roundtrip.mjs';
await initializePhysics();
const SOURCE=JSON.parse(readFileSync(new URL('sceneeval_six_source_annotations.json',import.meta.url)));
const external=id=>SOURCE.selected[id].description;

const P=object;
const base=[-25,6];
function obj(sceneId,category,n,x,z,size,options={}){
 return P(sceneId+'-'+category+'-'+n,category,{x,y:size.y/2,z},size,{
  name:category+' '+n,body:'fixed',source:'SceneEval manually mapped; NOT model-generated',...options
 });
}
function room(id,prose,contents){
 return {id,prose,entities:contents};
}
const cases=[
 room('sceneeval-bedroom-0',external(0),[
 obj('bed0','bed',1,-25,6,{x:2,y:.55,z:1.8}),
 obj('bed0','nightstand',1,-27.1,6,{x:.55,y:.65,z:.55}),
 obj('bed0','nightstand',2,-22.95,6,{x:.55,y:.65,z:.55}),
 obj('bed0','wardrobe',1,-29.2,8.8,{x:1.3,y:2,z:.65}),
 ].map(e=>({...e,id:'bed0'+e.id.slice(4)}))),
 room('sceneeval-bedroom-2',external(2),[
  obj('bed2','bed',1,-28,7,{x:2.1,y:.52,z:1.9}),
  obj('bed2','armchair',1,-24,7,{x:.9,y:.8,z:.9}),
  obj('bed2','armchair',2,-21.7,7,{x:.9,y:.8,z:.9}),
  obj('bed2','floor-lamp',1,-24,9,{x:.25,y:1.8,z:.25})
 ]),
 room('sceneeval-living-7',external(7),[
  obj('liv7','television',1,-27,7,{x:.9,y:1.1,z:.3}),
  obj('liv7','sofa',1,-23,8,{x:2.1,y:.8,z:.9}),
  obj('liv7','bookshelf',1,-20,7,{x:1.2,y:2,z:.4})
 ]),
 room('sceneeval-living-10',external(10),[
  obj('liv10','bookcase',1,-29,7,{x:1,y:2,z:.38}),
  obj('liv10','bookcase',2,-26,7,{x:1,y:2,z:.38}),
  obj('liv10','chair',1,-24,8,{x:.55,y:1,z:.6}),
  obj('liv10','painting',1,-21,7,{x:.8,y:1.1,z:.04})
 ]),
 room('sceneeval-dining-15',external(15),[
  obj('din15','dining-table',1,-25,6,{x:1.7,y:.9,z:1.4}),
  obj('din15','chair',1,-27.2,6,{x:.5,y:.85,z:.5}),
  obj('din15','chair',2,-23,6,{x:.5,y:.85,z:.5}),
  obj('din15','chair',3,-25,8,{x:.5,y:.85,z:.5})
 ]),
 room('sceneeval-bedroom-22',external(22),[
  obj('bed22','bed',1,-27,6,{x:2,y:.56,z:1.8}),
  obj('bed22','nightstand',1,-25.5,6,{x:.6,y:.67,z:.6}),
  P('bed22-lamp-1','lamp',{x:-25.5,y:.67+.3,z:6},{x:.22,y:.6,z:.22},
   {supportId:'bed22-nightstand-1',mass:.4,material:'metal',source:'SceneEval authored support mapping'}),
  obj('bed22','office-desk',1,-21.5,8,{x:1.2,y:.75,z:.7}),
  P('bed22-monitor-1','monitor',{x:-21.5,y:1.05,z:8},{x:.45,y:.6,z:.12},
   {supportId:'bed22-office-desk-1',mass:.8,body:'fixed',material:'metal',source:'SceneEval authored support mapping'}),
  obj('bed22','sofa-chair',1,-21.5,6.3,{x:.7,y:.85,z:.7})
 ])
];
for(const c of cases){const validation=validateScene(c);assert(validation.ok,JSON.stringify({id:c.id,validation}));assert.deepEqual(geometryIssues(c),[],c.id);}
function physical(scene){
 const t=performance.now(),world=new PRSELoop(scene);
 const before=world.scene.entities.map(e=>({id:e.id,p:{...e.position},supportId:e.supportId}));
 world.tick(80);const record=world.snapshot();
 const positions=world.scene.entities.map(e=>({id:e.id,p:{...e.position},velocity:{...e.velocity}}));
 const restored=PRSELoop.restore(JSON.parse(JSON.stringify(record)));
 assert(restored.ok,'restore failed '+scene.id);
 const pair=positions.map(({id,p})=>{
  const x=restored.loop.entities.get(id);return Math.hypot(x.position.x-p.x,x.position.y-p.y,x.position.z-p.z);
 });
 const savedOriginal=world.scene.prose===restored.loop.scene.prose;
 const stableIds=positions.every(({id})=>restored.loop.entities.has(id));
 const all3D=world.scene.entities.every(e=>Number.isFinite(e.position.z)&&Number.isFinite(e.position.y));
 const changedDescriptions=world.narrate(0),repeat=world.narrate(changedDescriptions.cursor);
 const result={scene:scene.id,externalHumanAuthoredDescription:true,
  entities:scene.entities.length,sceneProsePreserved:savedOriginal,stableIds,all3D,
  maxReloadPositionError:Math.max(...pair),initialInterpenetrations:world.initialSpatialIssues||0,
  narrativeEvents:changedDescriptions.usedSequences.length,duplicateNarrativeOnCursor:repeat.text.length>0,
  wallMs:+(performance.now()-t).toFixed(1)};
 restored.loop.dispose();world.dispose();return result;
}
const aliases={'television':'TV','dining-table':'dining_table','chair':'chair',
 'floor-lamp':'floor_lamp','office-desk':'office_desk','sofa-chair':'sofa_chair'};
const sourceIds=[0,2,7,10,15,22];
const sourceCountResults=cases.map((c,i)=>{
 const truth=SOURCE.selected[sourceIds[i]].count;
 const wanted=truth.split(';').map(x=>x.trim().split(',').map(z=>z.trim())).filter(x=>x.length===3);
 const counts={};for(const e of c.entities){const kind=aliases[e.kind]||e.kind;
 const key=kind==='chair'&&c.id==='sceneeval-dining-15'?'dining_chair':kind;
 counts[key]=(counts[key]||0)+1;
 }
 const facts=wanted.map(([op,n,kind])=>({op,kind,min:+n,actual:counts[kind]||0,
  satisfied:op==='eq'?(counts[kind]||0)===+n:op==='ge'?(counts[kind]||0)>=+n:false}));
 return {id:c.id,sourceId:sourceIds[i],facts,
  allCountFactsSatisfied:facts.every(x=>x.satisfied),
  relationClaims:SOURCE.selected[sourceIds[i]].relations,
  roomRelationClaims:SOURCE.selected[sourceIds[i]].roomRelations};
});
const rooms=cases.map(physical);
const encounter=room('original-stacked-workbench','A wooden workbench holds two small ceramic pots. A heavy ball rolls against one pot; the pot may slide off.',[
  P('workbench-1','workbench',{x:-25,y:.4,z:6},{x:2.2,y:.8,z:1.8},{body:'fixed',material:'wood'}),
  P('pot-1','pot',{x:-25.55,y:.8+.18,z:6.2},{x:.28,y:.36,z:.28},
   {supportId:'workbench-1',material:'ceramic',mass:1}),
  P('pot-2','pot',{x:-24.95,y:.8+.18,z:6.2},{x:.28,y:.36,z:.28},
   {supportId:'workbench-1',material:'ceramic',mass:1}),
  P('ball-1','ball',{x:-24.3,y:.8+.17,z:6.2},{x:.34,y:.34,z:.34},
   {supportId:'workbench-1',shape:'sphere',material:'metal',mass:3})
 ]);
assert.deepEqual(geometryIssues(encounter),[]);
const moving=new PRSELoop(encounter);
const initial=structuredClone(moving.scene.entities.map(e=>({id:e.id,pos:e.position})));
assert(moving.applyImpulse('ball-1',{x:-4,y:.1,z:0}));
moving.tick(150);
const firstMoved=moving.scene.entities.filter(e=>e.state.moved).map(e=>e.id);
const impactObserverIds=moving.visibleIds({x:-25,y:1,z:6.2});
const physicalEvents=moving.narrate(0,impactObserverIds);
const dedupe=moving.narrate(physicalEvents.cursor,impactObserverIds);
assert(physicalEvents.usedSequences.length>=3,'audited observer lost genuine impact or motion events');
assert(dedupe.text==='','observer replayed events already displayed');
const impulseSceneSave=moving.snapshot();
const saved=PRSELoop.restore(JSON.parse(JSON.stringify(impulseSceneSave)));
assert(saved.ok&&saved.loop.entities.has('ball-1')&&saved.loop.entities.has('pot-1'));
const worldPositionsBefore=[...moving.entities].map(([id,e])=>({id,p:e.position}));
const worldPositionsAfter=[...saved.loop.entities].map(([id,e])=>({id,p:e.position}));
const impactEvents=moving.events.filter(e=>e.type==='impact');
const maxError=Math.max(...worldPositionsBefore.map((r,i)=>Math.hypot(
 r.p.x-worldPositionsAfter[i].p.x,r.p.y-worldPositionsAfter[i].p.y,r.p.z-worldPositionsAfter[i].p.z)));
saved.loop.dispose();
moving.dematerialize();
assert(moving.active.size===0&&moving.entities.get('pot-1').revision>=0);
const savedAfterAway=moving.snapshot();
const preserved=PRSELoop.restore(JSON.parse(JSON.stringify(savedAfterAway)));
assert(preserved.ok&&preserved.loop.active.size===0);
const returnReentry=preserved.loop.materialize();
const reentryIdentity=[...preserved.loop.entities.keys()];
const returnStatement=preserved.loop.describe(preserved.loop.visibleIds({x:-25,y:1,z:6.2}));
preserved.loop.dispose();
const returnTest={physical3D:true,impulseOnExistingRapier:true,physicallyMoved:firstMoved,impactEvents:impactEvents.map(e=>({ids:e.ids,speed:e.details.relativeSpeedMetersPerSecond})),
  allCurrentNarrative:moving.scene.currentProse.slice(0,290),
  physicalEventCount:physicalEvents.usedSequences.length,duplicateAfterCursor:dedupe.text.length,
  maxSavePositionError:maxError,rematerialized:returnReentry,stableIds:reentryIdentity.length===4,
  causalEvents:physicalEvents.text,returnsText:returnStatement.slice(0,220),
  restoredOffscreenSnapshotWithoutBodies:true};
moving.dispose();
// Independent off-screen literary evolution and persistent tombstone.
const fire=room('original-paper-on-desk','An old note sits on a wooden workbench, and remains part of the persistent story after a fire.',[
  P('wooden-desk','desk',{x:-25,y:.4,z:6},{x:2,y:.8,z:1.2},{body:'fixed',material:'wood'}),
  P('paper-note','note',{x:-25,y:.81,z:6},{x:.3,y:.02,z:.25},
   {supportId:'wooden-desk',body:'dynamic',material:'paper',mass:.04})
 ]);
assert.deepEqual(geometryIssues(fire),[]);
const burning=new PRSELoop(fire);
burning.tick(25);
burning.dematerialize();
assert(burning.igniteOffscreen('paper-note'));
const beforeBurn=burning.snapshot();
burning.advanceOffscreen(12);
const fireSaved=burning.snapshot(),fireRestored=PRSELoop.restore(JSON.parse(JSON.stringify(fireSaved)));
assert(fireRestored.ok);
const note=fireRestored.loop.entities.get('paper-note');
const offscreenNoLeak=fireRestored.loop.narrate().text==='';
const activeAfterFire=fireRestored.loop.materialize();
const fireObserverIds=fireRestored.loop.visibleIds({x:-25,y:1,z:6});
const beforeReentry=fireRestored.loop.describe(fireObserverIds);
assert(note.state.condition==='ashes'&&note.state.destroyed);
assert(!fireRestored.loop.active.has('paper-note'));
assert(fireRestored.loop.entities.has('paper-note'));
const offscreenTest={currentNarrative:fireRestored.loop.scene.currentProse,preBurnState:beforeBurn.scene.entities.find(e=>e.id==='paper-note').state.condition,
 finalCondition:note.state.condition,stableTombstoneId:fireRestored.loop.entities.has('paper-note'),
 survivingBodies:activeAfterFire,remainingNotePhysicalBody:fireRestored.loop.active.has('paper-note'),
 narrative:fireRestored.loop.narrate(0,fireObserverIds).text,offscreenNoLeak,descriptiveReturn:beforeReentry,
 offscreenCausalEvents:fireRestored.loop.events.filter(e=>e.origin==='semantic_rule').length};
fireRestored.loop.dispose();burning.dispose();
// A wrong scene from an LLM should be rejected, not teleported into validity.
const invalids=[
 {name:'overlap',scene:structuredClone(cases[0])},
 {name:'float',scene:structuredClone(cases[0])},
 {name:'duplicate_identity',scene:structuredClone(cases[0])},
 {name:'missing_support',scene:structuredClone(cases[0])}
];
invalids[0].scene.entities[1].position={...invalids[0].scene.entities[0].position};
invalids[1].scene.entities[0].position.y+=1;
invalids[2].scene.entities[1].id=invalids[2].scene.entities[0].id;
invalids[3].scene.entities[0].supportId='unlisted-table';
const negatives=invalids.map(({name,scene})=>{
 let rejected=false;
 try{const obj=new PRSELoop(scene);obj.dispose();}catch{rejected=true;}
 return {name,rejected};
});
const stress=[];
for(const n of [10,30,100,300]){
 const cols=Math.ceil(Math.sqrt(n)),spacing=1.7;
 const scene=room('stress-'+n,'Artificial bounded physical scene with '+n+' separate boxes placed in three-dimensional space.',
 Array.from({length:n},(_,i)=>{
  const gx=i%cols,gz=Math.floor(i/cols);
  return P('stress-'+n+'-part-'+i,'crate',{x:-35+gx*spacing,y:.21,z:6+gz*spacing},
   {x:.4,y:.42,z:.4},{mass:1,material:'wood',body:'dynamic'});
 }));
 const t=performance.now(),w=new PRSELoop(scene);
 const created=w.active.size;const first=process.memoryUsage().heapUsed;
 w.tick(15);const after=process.memoryUsage().heapUsed;
 const snap=JSON.stringify(w.snapshot());
 const elapsed=performance.now()-t;
 stress.push({entities:n,actualRapierRigidBodies:created,sceneJsonBytes:snap.length,
  elapsedMs:+elapsed.toFixed(1),estimatedPerFrameMs:+(elapsed/15).toFixed(2),
  processHeapDeltaBytes:after-first,initialGeometryIssues:geometryIssues(scene).length});
 w.dispose();
}
const result={metadata:{project:'Existing Nitro PRSE GameCore world/Rapier',
 sceneProvenance:'SceneEval-500 IDs 0,2,7,10,15,22 externally written human prompts; mapping to spatial spec manually authored',
 notProven:'Unconstrained text to 3D generation, fully general LLM world rewriting, multi-GPU graphics',
 ownScenarioSources:'August 13 & October 9 original recordings; synthetic authored stress counts',
 physics:'Actual GameCore Rapier 3D bodies with all 3 axes of translation and rotation unlocked for research objects',
 modelCalls:0},
 rooms,sourceCountResults,roomPlans:cases.map(c=>({id:c.id,entities:c.entities})),physicalContact:{...returnTest},offscreenDamage:offscreenTest,negativeSceneValidation:negatives,stress};
assert(rooms.every(x=>x.stableIds&&x.sceneProsePreserved&&x.maxReloadPositionError<.0001));
assert(sourceCountResults.every(x=>x.allCountFactsSatisfied),'manually mapped source object counts inconsistent');
assert(negatives.every(x=>x.rejected));
assert(offscreenTest.stableTombstoneId&&!offscreenTest.remainingNotePhysicalBody);
assert(offscreenTest.offscreenNoLeak&&offscreenTest.narrative.includes('ashes'));
assert(returnTest.stableIds&&returnTest.maxSavePositionError<.0001);
const out=process.argv.find(x=>x.startsWith('--output='))?.slice('--output='.length)||'prse_semantic_physics_results.json';
if(!/^[a-z][a-z0-9_.-]*\.json$/.test(out))throw Error('unsafe result file');
writeFileSync(new URL(out,import.meta.url),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({mappedCountClaims:sourceCountResults.reduce((n,r)=>n+r.facts.length,0),externalRooms:rooms.length,consistentRooms:rooms.filter(x=>x.stableIds&&x.sceneProsePreserved).length,
 physical:result.physicalContact,offscreen:offscreenTest,
 rejectedInvalids:negatives,stress:stress.map(x=>({n:x.entities,ms:x.elapsedMs,bytes:x.sceneJsonBytes}))}));
