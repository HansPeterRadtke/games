// Experimental open-vocabulary text candidate -> ACTUAL authoritative 3D
// PRSE GameCore/Rapier bodies, on exactly the already frozen SceneEval
// first-100-human plus systematic assisted-100 previously evaluated scenes.
//
// The CPU pretrained spaCy noun candidates were frozen BEFORE any official
// gold annotation score was opened. No gold labels enter this physical compiler.
//
// Critical limitation: unknown noun types have NO calibrated shape/scale or
// asset catalog. Their fallback is explicitly a small generic fixed-size
// provisional BOX collider. This only tests whether extra source-linked
// entity COUNT can be instantiated/saved without invalid placement; it
// DOES NOT prove faithful physical shape, object identity, affordance,
// relationships, colors, materials, animation or artistic 3D generation.
//
// Refuse a candidate when it cannot be placed without overlaps, a source
// negation forbids it, or the bounded new-object budget is exhausted.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {PRSELoop,object,geometryIssues,validateScene} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
import {readResearchEvidence} from '../2026-10-24/prse_research_evidence_io.mjs';
import {recordNativePRSEState,restoreNativePRSEState} from './prse_native_world_transaction.mjs';
await initializePhysics();
const SOURCE=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500;
const EXTRA=JSON.parse(readFileSync('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery/prse_spacy_open_vocab_500_proposals_raw_v1.json'));
if(EXTRA.records.length!==500||SOURCE.length!==500)throw Error('Frozen external source dataset changed');
const privateDir='/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery';
mkdirSync(privateDir,{mode:0o700,recursive:true});
const hash=x=>createHash('sha256').update(x).digest('hex');
const ids=[...Array.from({length:100},(_,i)=>i),
 ...Array.from({length:100},(_,i)=>100+4*i)];
const realSize={x:.24,y:.28,z:.24},maxAdded=16;
const room={minX:-35.7,maxX:-18.0,minZ:5.55,maxZ:17.8};
const collision=(a,b)=>
 ['x','y','z'].every(k=>Math.abs(a.position[k]-b.position[k])<
  (a.size[k]+b.size[k])/2+.014);
function fallbackObject(scene,kind,idx,start,end){
 const token=hash(Buffer.from(kind)).slice(0,7),prefix='sem-'+scene.id.replace(/^sem-/,'');
 const id=prefix+'-candidate-'+kind.slice(0,20).replace(/_/g,'-')+'-'+token+'-'+idx;
 if(scene.entities.some(x=>x.id===id))throw Error('Unexpected identity collision');
 for(let xi=0;xi<29;xi++)for(let zi=0;zi<22;zi++){
  const position={x:room.minX+xi*.6,y:realSize.y/2,z:room.minZ+zi*.54};
  const proposed=object(id,kind,position,realSize,{
    body:'dynamic',material:'unknown',shape:'box',mass:.3,
    name:kind.replace(/_/g,' ')+' '+(idx+1),
    source:'syntax-proposed:'+scene.id+':'+start+':'+end,
    description:'PROVISIONAL TYPE ONLY; generic AABB collider with UNVERIFIED physical scale, mass and source meaning',
    state:{condition:'intact',openVocabularyCandidate:true,
      sourceMeaningIndependentlyVerified:false,
      shapeAndMaterialIndependentlyVerified:false}
  });
  if(!scene.entities.some(e=>!e.state?.destroyed&&collision(e,proposed)))
   return proposed;
 }
 return null;
}
const started=performance.now(),rows=[];
for(let i=0;i<ids.length;i++){
 const sourceID=ids[i],p=SOURCE[sourceID],extra=EXTRA.records[sourceID];
 if(extra.sourceText!==p.text)throw Error('Source identity/prose divergence');
 const original=repairScene(p,{maxSweeps:2,maxAttemptsPerScene:150});
 const row={sourceID,subset:sourceID<100?'human':'assisted',baselineAccepted:original.accepted,
  status:'original_scene_rejected',added:0,
  sourceCandidateTypes:extra.boundedNewTypes.length,
  candidateMentions:extra.candidates.length,
  budget:maxAdded,
  refused:{},addedProvenance:[],
  originalPhysicalInstances:original.provisionalObjects};
 if(!original.accepted||geometryIssues(original.scene).length){
  rows.push(row);continue;
 }
 const scene=structuredClone(original.scene);
 let newBodies=0;
 const existing=new Map();
 for(const e of scene.entities){
  if(e.state?.destroyed||e.source==='provisional_3D_room_boundary')continue;
  existing.set(e.kind,(existing.get(e.kind)||0)+1);
 }
 for(const c of extra.boundedNewTypes){
  const negative=p.quantities[c.type];
  if(negative?.count===0){row.refused['source_explicitly_negated']=(row.refused['source_explicitly_negated']||0)+1;continue;}
  const previous=existing.get(c.type)||0;
  const wanted=Math.max(0,Math.min(c.count,12)-previous);
  const proof=extra.candidates.find(x=>x.type===c.type);
  if(!proof||!proof.sourceOffsets||p.text.slice(...proof.sourceOffsets)!==proof.sourceText)
   throw Error('Unsupported source span or invented noun phrase');
  if(wanted<=0)continue;
  for(let j=0;j<wanted;j++){
   if(newBodies>=maxAdded){row.refused['bounded_extra_objects']=(row.refused['bounded_extra_objects']||0)+1;continue;}
   const candidate=fallbackObject(scene,c.type,j,...proof.sourceOffsets);
   if(!candidate){row.refused['spatially_unplaceable']=(row.refused['spatially_unplaceable']||0)+1;continue;}
   scene.entities.push(candidate);newBodies++;existing.set(c.type,(existing.get(c.type)||0)+1);
   row.addedProvenance.push({id:candidate.id,kind:c.type,sourceSpan:proof.sourceOffsets,
    previousLexiconOverlap:proof.previousLexiconOverlap,
    provisionalShape:'generic_actual_Rapier_box_no_real_asset_or_scale'});
  }
 }
 row.added=newBodies;
 row.status='compiled';
 const originalIDs=new Set(original.scene.entities.map(x=>x.id));
 const issue=geometryIssues(scene),schema=validateScene(scene);
 if(issue.length||!schema.ok){
  row.status='rejected_geometry_or_schema';row.reasons=issue.slice(0,3);
  rows.push(row);continue;
 }
 let loop=null,reloaded=null;
 try{
  loop=new PRSELoop(scene);
  loop.tick(38);
  const physicalCount=Object.fromEntries([...new Set(loop.scene.entities.filter(x=>
   x.source!=='provisional_3D_room_boundary'&&!x.state?.destroyed).map(x=>x.kind))]
   .map(k=>[k,loop.scene.entities.filter(x=>x.kind===k&&!x.state.destroyed&&loop.active.has(x.id)).length]));
  const actualAdd=row.addedProvenance.filter(x=>loop.active.has(x.id)).length;
  if(actualAdd!==newBodies)throw Error('New candidate was not a real native Rapier rigid body');
  const native=recordNativePRSEState(loop);
  const clone=restoreNativePRSEState(JSON.parse(JSON.stringify(native)));
  if(!clone.ok)throw Error('Native full GameCore/semantic save/restore failed: '+clone.reason);
  reloaded=clone.loop;
  const postPhysical=Object.fromEntries(Object.keys(physicalCount).map(k=>
   [k,reloaded.scene.entities.filter(x=>x.kind===k&&!x.state.destroyed&&reloaded.active.has(x.id)).length]));
  if(JSON.stringify(physicalCount)!==JSON.stringify(postPhysical)||
   reloaded.scene.prose!==p.text||![...originalIDs].every(id=>reloaded.entities.has(id)))
   throw Error('Native save broke current physical body counts, historical source, or original IDs');
  row.finalPhysicalCounts=physicalCount;
  row.totalPhysicalBodies=Object.values(physicalCount).reduce((a,b)=>a+b,0);
  row.addedActuallyNativePhysicalBodies=actualAdd;
  row.originalIDsUnaffected=[...originalIDs].every(id=>loop.entities.has(id));
  row.savedGenericProvisionalDimensions=realSize;
  row.sourceHistoricTextUnchanged=loop.scene.prose===p.text;
  row.status='native_saved_and_reentered';
 }catch(e){row.status='runtime_failed';row.reason=String(e.message).slice(0,230);}
 finally{reloaded?.dispose();loop?.dispose();}
 rows.push(row);
 if((i+1)%25===0)console.log('PROGRESS',i+1,'of',ids.length);
}
const good=rows.filter(r=>r.status==='native_saved_and_reentered');
const summary={
 originalFrozenSourceScenes:200,
 originalPhysicallyAccepted:rows.filter(r=>r.baselineAccepted).length,
 augmentedPhysicallyAcceptedAndRestored:good.length,
 rejectedByOriginalGeometry:rows.filter(r=>!r.baselineAccepted).length,
 rejectedAfterExtraGeometry:rows.filter(r=>r.status==='rejected_geometry_or_schema').length,
 runtimeSaveFailures:rows.filter(r=>r.status==='runtime_failed').length,
 addedActualGenericRapierBodies:good.reduce((n,x)=>n+x.addedActuallyNativePhysicalBodies,0),
 addedNewTypes:good.reduce((n,x)=>n+new Set(x.addedProvenance.map(z=>z.kind)).size,0),
 scenesWithExtraNativeBodies:good.filter(x=>x.added>0).length,
 originalIDsAndTextPreserved:good.filter(x=>x.originalIDsUnaffected&&x.sourceHistoricTextUnchanged).length,
 unknownGeometryAndPhysicalScaleForEveryNewNoun:true,
 geometryModel:'Native real 3D Rapier contacts on arbitrarily small provisional generic boxes, NOT source-calibrated assets',
 wallSeconds:+((performance.now()-started)/1000).toFixed(2)};
const path=privateDir+'/prse_spacy_open_vocab_native_200_raw_v1.json';
const result={metadata:{source:'Frozen 500 SceneEval text-only spaCy 3.8 proposals, same first100 human and systematic assisted100 original physical scenes',
 authority:'Native PRSE GameCore/Rapier, consistent source IDs and trusted native full-world save',
 noGoldDuringCandidateGenerationOrPhysics:true,
 limitation:'Generic small boxes are physically real but not semantically faithful shapes, dimensions or affordances'},
 summary,records:rows};
writeFileSync(path,JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
const safe={metadata:{...result.metadata,privateRawSHA256:hash(readFileSync(path))},
 summary,scenes:rows.map(x=>({id:x.sourceID,status:x.status,
  numNewPhysical:x.addedActuallyNativePhysicalBodies||0,
  physicalCount:x.totalPhysicalBodies||null,
  refused:x.refused,reason:x.reason||null}))};
writeFileSync(new URL('prse_spacy_open_vocab_native_200_aggregate_v1.json',import.meta.url),
 JSON.stringify(safe,null,2)+'\n',{flag:'wx'});
console.log('FROZEN_CANDIDATE_PHYSICS',JSON.stringify(summary));
