// Exploratory AUTOMATIC text -> object-count extraction -> conservative physical
// placement -> actual GameCore/Rapier simulation -> save/re-entry.
// Text predictions are from the independent SceneEval baseline script, not gold.
// Deliberately demonstrates relation/attribute loss rather than claiming success.
import {readFileSync,writeFileSync} from 'node:fs';
import {initializePhysics} from '../../physics-core.js';
import {object,PRSELoop,geometryIssues} from './prse_semantic_roundtrip.mjs';
import {performance} from 'node:perf_hooks';
await initializePhysics();
const parent=JSON.parse(readFileSync(new URL('sceneeval_counts_with_predictions.json',import.meta.url)));
const counts=parent.preparsed_human_100;
const dimensions={
 bed:[2,.55,1.8],nightstand:[.6,.65,.6],wardrobe:[1.5,2,.8],
 armchair:[.9,.8,.8],floor_lamp:[.25,1.5,.25],sofa:[2,.85,.9],
 bookshelf:[1.5,2,.4],coffee_table:[1.1,.4,.7],dining_table:[1.7,.82,1.3],
 table:[1.5,.78,.9],chair:[.55,.85,.55],desk:[1.3,.75,.7],
 dresser:[1.3,1,.55],cabinet:[1.2,1.5,.5],lamp:[.25,.55,.25],
 television:[.9,1.1,.22],shelf:[1.2,1.5,.35],plant:[.45,.9,.45],
 painting:[.7,1.0,.07],mirror:[.7,1.2,.07],window:[1.2,1.2,.12],
 toilet:[.55,.75,.7],sink:[.7,.8,.5],bathtub:[1.7,.75,.85],
 refrigerator:[.8,1.8,.75],oven:[.8,.85,.75],stool:[.45,.7,.45],
 floor_lamp:[.25,1.5,.25],nightstand:[.65,.65,.65],
 box:[.6,.6,.6],book:[.2,.04,.3],vase:[.2,.4,.2],rug:[1.5,.03,1.2]
};
const selected=counts.filter((_,i)=>i%3===0).slice(0,34);
const results=[];
for(const row of selected){
 const bodies=[];
 const key=[...Object.entries(row.predicted)].filter(([name,n])=>Number.isInteger(n)&&n>0&&n<=24);
 for(const [kind,num]of key)for(let n=0;n<num;n++){
  const idx=bodies.length,columns=6,s=dimensions[kind]||[.7,.8,.6];
  bodies.push(object('auto-'+row.id+'-'+kind.replaceAll('_','-')+'-'+n,kind,
    {x:-32+(idx%columns)*3.1,y:s[1]/2,z:8+Math.floor(idx/columns)*3.1},
    {x:s[0],y:s[1],z:s[2]},
    {body:'fixed',material:'unknown',source:'deterministic_text_only_bounded_parser',
    state:{condition:'intact'}}));
 }
 if(!bodies.length){
  results.push({id:row.id,objects:0,accepted:false,reason:'No vocabulary matches',saved:false});
  continue;
 }
 const scene={id:'external-text-'+row.id,prose:row.description,entities:bodies};
 let instance=null;
 try{
  const t=performance.now();
  instance=new PRSELoop(scene);
  instance.tick(12);
  const record=JSON.parse(JSON.stringify(instance.snapshot()));
  const copied=PRSELoop.restore(record);
  const saved=copied.ok && copied.loop.scene.prose===row.description
   &&copied.loop.active.size===bodies.length;
  copied.loop?.dispose();
  results.push({id:row.id,objects:bodies.length,accepted:true,saved,
   physicsTicks:12,elapsedMs:+(performance.now()-t).toFixed(1),
   relationGrounding:false,attributeGrounding:false,
   initialIssues:geometryIssues(scene).length});
 }catch(e){
  results.push({id:row.id,objects:bodies.length,accepted:false,saved:false,
   reason:String(e.message).slice(0,160)});
 }finally{instance?.dispose();}
}
const summary={inputCount:selected.length,parsedNonempty:results.filter(x=>x.objects>0).length,
 physicalAccepted:results.filter(x=>x.accepted).length,
 savedConsistently:results.filter(x=>x.saved).length,
 meanMs:results.filter(x=>x.elapsedMs).reduce((s,x)=>s+x.elapsedMs,0)/Math.max(1,results.filter(x=>x.elapsedMs).length),
 relationGroundingVerified:0,attributeGroundingVerified:0};
const out={source:'External human-curated SceneEval-100 text predictions from regex-only baseline (no gold used)',
 metadata:{notes:'Automatic pipeline only tests lexical entity detection, generic sized boxes, simulation, save/reentry. No relation geometry, scene style or semantics beyond lexical counts.',
 originalExternalPromptCount:100,selectedIds:results.map(x=>x.id)},summary,results};
writeFileSync(new URL('prse_auto_external_text_to_physics_results.json',import.meta.url),
 JSON.stringify(out,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(summary));
