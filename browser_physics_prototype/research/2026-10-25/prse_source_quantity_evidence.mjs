// Research-only quantitative semantic source ↔ actual native PRSE GameCore 3D
// object-count evidence, with explicit closed/open-world and reference scope.
//
// The original SceneEval lexical interpreter supplies SOURCE mention/quantity
// proposals (not gold annotations). Only currently instantiated authoritative
// Rapier rigid bodies establish a physical count. A singular noun or repeated
// noun mention does NOT establish a globally exact object count in literary
// prose: source reference/coreference and closed-world scope remain UNKNOWN.
//
// This component does not change world truth, choose body positions, create
// objects or infer that source adjectives have become physical measurements.
import {createHash}from'node:crypto';
import{PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
const copy=x=>structuredClone(x);
const hash=x=>createHash('sha256').update(typeof x==='string'?x:JSON.stringify(x)).digest('hex');
const nint=n=>Number.isSafeInteger(n)&&n>=0&&n<=100000;
const belongs=e=>e.source!=='provisional_3D_room_boundary';
const propositionSupported=(op,count,observed)=>{
 if(op==='gt')return observed>count;
 if(op==='ge')return observed>=count;
 if(op==='eq')return observed===count;
 return null;
};
const observedMaterial=(e)=>{
 // A compiler-chosen provisional material parameter is *real solver input*
 // but cannot independently establish that the source's color/woodenness is
 // true, because that parameter was derived from the same source proposal.
 return {physicalSolverMaterial:e.material||'unknown',
  externalMaterialEvidence:'not_independently_verified',
  claimedVisualColorEvidence:'not_observed_by_materialized_physics'};
};
function quantRows(proposal){
 const mentions=proposal.mentions||[],q=proposal.quantities||{};
 if(!Array.isArray(mentions)||typeof q!=='object'||Object.keys(q).length>100)
  throw Error('Invalid frozen source claim graph');
 return Object.entries(q).map(([type,p])=>{
  if(!type||typeof type!=='string'||!p||!nint(p.count)||!['eq','ge','gt'].includes(p.op))
   throw Error('Unsupported quantity source claim');
  const spans=mentions.filter(m=>m.type===type);
  if(!spans.every(m=>nint(m.start)&&nint(m.end)&&m.end>=m.start
    &&m.end<=proposal.text.length))
   throw Error('Source mention offsets cannot be verified against literary source');
  const exactSpans=spans.every(m=>proposal.text.slice(m.start,m.end)===m.matched);
  if(!exactSpans)throw Error('Proposed literary mention is not in original source at its attributed span');
  const zeros=spans.filter(m=>m.quantity===0),positive=spans.filter(m=>m.quantity>0);
  const explicit=spans.filter(m=>m.certainty==='quantified'),
    implicit=spans.filter(m=>m.certainty!=='quantified');
  const conflicting=Boolean(p.ambiguous)||Boolean(zeros.length&&positive.length);
  const min=p.count+(p.op==='gt'?1:0);
  let sourceCountScope='open_world_reference_identity_unresolved';
  if(conflicting)sourceCountScope='contradictory_source_mentions';
  else if(p.count===0 && explicit.length)sourceCountScope='explicit_source_absence';
  else if(explicit.length&&spans.length===1)sourceCountScope='single_explicit_source_count_no_closed_world';
  else if(spans.length>1)sourceCountScope='repeated_type_reference_or_multiple_instances_unresolved';
  else if(implicit.length)sourceCountScope='unquantified_presence_only';
  return {type,request:{...p},minimumProposed:min,
   mentionCount:spans.length,explicitMentionCount:explicit.length,
   implicitMentionCount:implicit.length,negatedMentions:zeros.length,
   repeatedRef:spans.length>1,conflicting,sourceCountScope,
   mentionOffsets:spans.map(m=>({start:m.start,end:m.end,quantity:m.quantity,
    operator:m.op,certainty:m.certainty,attributes:copy(m.attributes||[])}))};
 });
}
export class PRSESourceQuantityEvidence{
 constructor(loop,proposal){
  if(!(loop instanceof PRSELoop)||!proposal||typeof proposal.text!=='string'||
    typeof proposal.sourceId!=='string'||loop.scene.prose!==proposal.text)
   throw Error('Source quantity evidence requires matching GameCore world and exact frozen original literary text');
  this.world=loop;this.source=copy(proposal);
  this.sourceHash=hash(proposal.text);
  this.countClaims=quantRows(proposal);
  this.sourceQuantitiesHash=hash(this.countClaims);
 }
 evaluate(){
  const world=this.world;
  if(world.scene.prose!==this.source.text||hash(world.scene.prose)!==this.sourceHash||
     Math.abs(world.time-world.game.time)>1e-5)throw Error('World prose or native clock changed');
  const all=world.scene.entities.filter(belongs);
  const present=all.filter(e=>!e.state?.destroyed && world.active.has(e.id));
  const unloaded=all.filter(e=>!e.state?.destroyed&&!world.active.has(e.id));
  const destroyed=all.filter(e=>!!e.state?.destroyed);
  const scopeComplete=unloaded.length===0;
  const kinds=[...new Set([...all.map(e=>e.kind),
   ...this.countClaims.map(x=>x.type)])].sort();
  const grouped=kinds.map(type=>{
   const physicallyPresent=present.filter(e=>e.kind===type);
   return {type,materializedBodies:physicallyPresent.length,
    unloadedSemanticIdentities:unloaded.filter(e=>e.kind===type).length,
    destroyedHistoricalIdentities:destroyed.filter(e=>e.kind===type).length,
    materializedIDs:physicallyPresent.map(x=>x.id),
    actualPhysicalMaterials:physicallyPresent.map(observedMaterial)};
  });
  const physical=new Map(grouped.map(row=>[row.type,row]));
  const claims=this.countClaims.map(source=>{
   const observed=physical.get(source.type);
   const count=observed?.materializedBodies||0;
   const complete=scopeComplete;
   let countStatus='unknown',why='some_region_objects_unloaded';
   if(source.conflicting){
    why='contradictory_source_mentions';
   }else if(complete){
    // This test is against the SOURCE PARSER'S numerical proposal, not
    // independent author intent. Keep that epistemic distinction explicit.
    const yes=propositionSupported(source.request.op,source.request.count,count);
    countStatus=yes?'true':'false';
    why='compiler_proposal_compared_with_actual_native_body_count';
   }
   let conservativePresence='unknown';
   if(!source.conflicting&&source.request.count>0){
    if(count>=source.minimumProposed)conservativePresence='true';
    else if(complete)conservativePresence='false';
   }
   let explicitAbsence='unknown';
   if(!source.conflicting&&source.request.count===0&&source.negatedMentions>0&&complete)
    explicitAbsence=count===0?'true':'false';
   const possiblyRepeatingReference=source.repeatedRef;
   // Do not equate a parsed eq N with global exact source meaning when
   // the scene description has not stated closed-world quantifier scope.
   return {...source,physicallyMaterializedCount:count,
    physicallyUnloadedCount:observed?.unloadedSemanticIdentities||0,
    sourceCompilerNumericMatch:countStatus,
    sourceConservativePresence:conservativePresence,
    explicitSourceAbsenceMatch:explicitAbsence,
    sourceExactGlobalCountEntailed:'unknown',
    reason:why,referenceUniqueness:'unknown',
    sourceLiteraryTruthValidatedByExternalAnnotations:false,
    sourceAttributesPhysicallyIndependentlyVerified:false,
    originalWorldSceneIDs:observed?.materializedIDs||[]};
  });
  const currentFacts=grouped.filter(x=>x.materializedBodies>0||x.unloadedSemanticIdentities>0||
    x.destroyedHistoricalIdentities>0).map(g=>{
   const state=g.unloadedSemanticIdentities?
    'incomplete_semantic_region':'currently_materialized_region';
   // Scope every numeric statement. Unloaded objects are NOT counted as
   // actively existing rigid bodies, but stable semantic IDs are retained.
   return {type:g.type,scope:state,
    text:state==='currently_materialized_region'?
     'The currently materialized region contains '+g.materializedBodies+
        ' physical objects classified as '+g.type+'.':
     'This region has '+g.materializedBodies+' materialized '+g.type+
        ' bodies and '+g.unloadedSemanticIdentities+
        ' unloaded semantic records; its current physical count is incomplete.',
    evidence:'actual_authoritative_Rapier_active_ids_plus_saved_semantic_records'};
  });
  return {schema:1,sourceId:this.source.sourceId,sourceHash:this.sourceHash,
   worldTime:world.time,fullyPhysicallyMaterialized:scopeComplete,
   materializedEntityCount:present.length,unloadedEntityCount:unloaded.length,
   destroyedEntityCount:destroyed.length,
   currentPhysicalTypeCounts:grouped,
   sourceCountClaims:claims,
   currentCountSentences:currentFacts,
   epistemicWarnings:[
    'A source parser proposed each original object quantity; no independent source-meaning validation is implied.',
    'A physically realized body count is scoped to this generated region and is not a claim about all objects of the literary universe.',
    'An unquantified singular mention does not prove globally exact count one.',
    'An original adjective or simulated material parameter does not independently prove visible color, texture, composition or physical truth.',
    'Unloaded-region live physical counts remain unknown until the area is actually materialized.']};
 }
}
