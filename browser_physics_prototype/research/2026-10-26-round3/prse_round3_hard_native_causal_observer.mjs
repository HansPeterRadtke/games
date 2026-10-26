// Round-three REAL native 3D causal/observer stress on difficult *already
// human-authored* LEGO scenes. This does NOT rerun earlier 130-scene placement
// experiment: initialize from its frozen author-source-linked native state,
// then apply NEW real GameCore impulses, after-event semantic/observer checks,
// offscreen unload and exact source + identity restoration.
//
// Selection is a disclosed posthoc stress cohort, not a heldout accuracy test.
// Reconstructed colliders remain provisional and may differ from true assets.
// No random feasible-parent placebo, no external production change.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {initializePhysics} from '../../physics-core.js';
import {object,PRSELoop,validateScene} from '../2026-10-24/prse_semantic_roundtrip.mjs';
import {PRSESourceRevision} from '../2026-10-25/prse_source_revision_story.mjs';
import {PRSECurrentSemanticDocument} from '../2026-10-25/prse_current_semantic_document.mjs';
await initializePhysics();
const OUT='/data/var/games/prse_semantic_research/runs/2026-10-26-prse-hard-negatives-r3';
const BASE='/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent';
const EXT='/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1';
const source=JSON.parse(readFileSync(BASE+'/lego_source_only_frozen_130_raw_v1.json')).scenes;
const input=JSON.parse(readFileSync(EXT+'/lego_extended_actual_native_matched_130_raw_v2.json'));
if(source.length!==130||input.rows.length!==130||input.summary.accepted!==130)
 throw Error('Frozen original source/native study is incomplete');
const sha=b=>createHash('sha256').update(b).digest('hex');
const hard=[
 {id:17,kind:'lamp',role:'nonvertical_human_source_but_real_lamp_bed_contact'},
 {id:28,kind:'blanket',role:'source_two_rooms_two_beds_ambiguous_parent_reference'},
 {id:32,kind:'computer',role:'source_two_computers_two_desks_placement_abstained'},
 {id:53,kind:'lamp',role:'explicit_human_lamp_on_desk_true_positive'},
 {id:54,kind:'mouse',role:'computer_with_mouse_on_desk_composite_not_direct_source_claim'},
 {id:120,kind:'doll',role:'explicit_human_doll_on_bed_true_positive'},
 {id:121,kind:'box',role:'jewelry_box_on_dresser_refused_fixed_box_child'}
];
const records=[];const started=performance.now();
for(const testcase of hard){
 const id=testcase.id,p=source[id],previous=input.rows[id];
 const r={id,kind:testcase.kind,role:testcase.role,
  originalSourceHash:p.sourceHash,status:'started'};
 let loop=null,returnDoc=null;
 try{
  if(previous.status!=='matched_native_3d_saved')throw Error('Original native study not complete');
  const inventory=previous.candidate.bodyStates;
  if(!inventory.every(e=>e.id&&e.kind&&e.size&&e.position&&e.rotation&&e.body))
    throw Error('Frozen source/native inventory missing true entity poses or types');
  const entities=inventory.map(e=>{
   const ent=object(e.id,e.kind,e.position,e.size,{
    body:e.body,shape:e.shape,material:'unknown',
    source:e.source,name:e.kind.replace(/_/g,' ')+' (frozen original ID)',
    description:'Reconstructed frozen Rapier collider; physical size is provisional',
    mass:.6,supportId:e.supportId||'floor',
    state:{condition:'intact',sourceOriginalMeaningNotIndependentlyEntailed:true}
   });
   ent.rotation=e.rotation;
   return ent;
  });
  const world={id:'sem-hard-source-'+String(id),prose:p.sourceText,entities};
  if(!validateScene(world).ok)throw Error('Frozen native snapshot failed world schema check');
  loop=new PRSELoop(world,{checkGeometry:false});
  loop.tick(4);
  if(loop.scene.prose!==p.sourceText)throw Error('Original human literary source mutated');
  const trueIds=new Set([...loop.active.keys()]);
  if(trueIds.size!==inventory.length||inventory.some(x=>!trueIds.has(x.id)))
   throw Error('Actual Rapier body IDs not recoverable from frozen original');
  const story=new PRSESourceRevision(loop,p.lexicalProposal.relations,{observerRadius:12});
  const current=new PRSECurrentSemanticDocument(story);
  const before=current.record();
  const child=inventory.find(x=>x.kind===testcase.kind&&x.body==='dynamic');
  r.initialNativeBodies=loop.active.size;
  r.originalSourcePreserved=story.sourceArchive().originalText===p.sourceText;
  r.readableCurrentClauses=before.current?.verifiedTextClauses?.length??0;
  r.sourceOnlyCurrentSupportAsAuthorNotVerified=Boolean(before.current?.verifiedTextClauses?.every(c=>
    c.type!=='source_inferred_support_as_author_proved'));
  r.dynamicChildPresent=Boolean(child);
  if(child){
   const prior={...loop.active.get(child.id).translation()};
   if(!loop.applyImpulse(child.id,{x:4,y:1.1,z:.5}))
    throw Error('Real GameCore impulse refused');
   loop.tick(155);
   const physical={...loop.active.get(child.id).translation()};
   r.impulseChildId=child.id;
   r.impulseActualMotionMeters=Math.hypot(...['x','y','z'].map(k=>physical[k]-prior[k]));
   r.impulseProducedActualMovement=r.impulseActualMotionMeters>.03;
   const after=current.record();
   r.afterImpulseCurrentDocumentChanged=Boolean(after.changed);
   r.afterImpulseVerifiedClauses=after.current?.verifiedTextClauses?.length??0;
   r.afterImpulseSourceStillOriginal=story.sourceArchive().originalText===p.sourceText;
  }
  const unload=loop.dematerialize();
  r.offscreenActuallyUnloaded=unload>0;
  if(unload>0){
   loop.advanceOffscreen(7);
   current.record();
  }
  const frozen=JSON.parse(JSON.stringify(current.snapshot()));
  const restore=PRSECurrentSemanticDocument.restore(frozen);
  if(!restore.ok)throw Error('Trusted GameCore/semantic restore refused: '+restore.reason);
  returnDoc=restore.document;
  r.postRestoreOriginalSourcePreserved=returnDoc.story.sourceArchive().originalText===p.sourceText;
  r.postRestoreAllIDsPresent=inventory.every(e=>returnDoc.story.loop.entities.has(e.id));
  r.postRestoreCurrentDocumentExact=returnDoc.current().text===current.current().text;
  if(!r.postRestoreOriginalSourcePreserved||!r.postRestoreAllIDsPresent||!r.postRestoreCurrentDocumentExact)
   throw Error('Offscreen source/history/identity/current semantic transaction changed on restore');
  r.status='real_rapier_causal_semantic_offscreen_saved';
 }catch(err){r.status='failed';r.failure=String(err.message).slice(0,220);}
 finally{returnDoc?.dispose();loop?.dispose();}
 records.push(r);
 console.log('ROUND3_HARD_NATIVE_CAUSAL',r.id,r.status,r.impulseActualMotionMeters??null,r.failure??'');
}
const ok=records.filter(r=>r.status==='real_rapier_causal_semantic_offscreen_saved');
const summary={humanOriginalSourceCases:hard.length,
 realNativePhysicalWorldsAndSemanticPersistenceCompleted:ok.length,
 runtimeFailures:records.filter(r=>r.status==='failed').length,
 trueNewImpulseCases:ok.filter(x=>x.dynamicChildPresent).length,
 physicallyMovedImpulseSubjects:ok.filter(x=>x.impulseProducedActualMovement).length,
 currentSemanticChangedAfterActualMotion:ok.filter(x=>x.afterImpulseCurrentDocumentChanged).length,
 actualPhysicsOffscreenUnloads:ok.filter(x=>x.offscreenActuallyUnloaded).length,
 originalSourceAndBodyIDsAllRestored:ok.filter(x=>x.postRestoreOriginalSourcePreserved&&x.postRestoreAllIDsPresent&&x.postRestoreCurrentDocumentExact).length,
 elapsedSeconds:+((performance.now()-started)/1000).toFixed(2),
 originalIndependentAssetGeometryStillUnproven:true,
 sourceContactClaimsNotEstablishedByThisPhysicsOnlyTest:true};
mkdirSync(OUT,{recursive:true,mode:0o700});
const privateFile=OUT+'/round3_hard_original_human_native_causal_observer_raw_v1.json';
writeFileSync(privateFile,JSON.stringify({metadata:{
 originalHumanLEGOTextSHA256:sha(readFileSync(BASE+'/lego_source_only_frozen_130_raw_v1.json')),
 originalFrozenRealRapierV2SHA256:sha(readFileSync(EXT+'/lego_extended_actual_native_matched_130_raw_v2.json')),
 posthocFrozenHumanHardSceneSelection:true,untouchedOriginalWorktree:true,
 realGameCoreNotReconstructedAssetMesh:true,noRandomParentPlacebo:true
},summary,records},null,2)+'\n',{flag:'wx',mode:0o600});
writeFileSync(new URL('prse_round3_hard_human_native_causal_observer_aggregate_v1.json',import.meta.url),
 JSON.stringify({metadata:{privateRawSHA256:sha(readFileSync(privateFile)),noSourceGoldInput:true},summary,
 cases:records.map(x=>({id:x.id,status:x.status,impulseMovementMeters:x.impulseActualMotionMeters??null,
  actualOffscreen:x.offscreenActuallyUnloaded??false,error:x.failure??null}))},null,2)+'\n',{flag:'wx'});
console.log('ROUND3_HARD_NATIVE_SUMMARY',JSON.stringify(summary));
