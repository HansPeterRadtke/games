// Read-only PRE-NATIVE source equality gate for the independent LEGO corpus.
// Recompile the same original source-only body inventory with the frozen
// deterministic source lexical relation module. Reject any moved object whose
// category is NOT mentioned as a relation subject in the original source.
import {readFileSync} from 'node:fs';
import {compileProposal} from '../2026-10-24/prse_constraint_layout.mjs';
import {repairScene} from './prse_relation_local_optimizer.mjs';
const file='/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent/lego_source_only_frozen_130_raw_v1.json';
const scenes=JSON.parse(readFileSync(file)).scenes;
if(scenes.length!==130)throw Error('Original frozen source subset not complete');
let moved=0;
for(const row of scenes){
 const proposal=row.lexicalProposal;
 const ctl=compileProposal({...proposal,relations:[]},{maxEntities:32});
 const alt=repairScene(proposal,{maxSweeps:2,maxAttemptsPerScene:150});
 if(!ctl.good||!alt.accepted)throw Error('A previously physics-accepted original scene was not recreated');
 const old=new Map(ctl.scene.entities.map(e=>[e.id,e]));
 const subjects=new Set(proposal.relations.map(r=>r.a));
 const fingerprint=e=>JSON.stringify({id:e.id,kind:e.kind,shape:e.shape,body:e.body,size:e.size});
 for(const entity of alt.scene.entities){
  const former=old.get(entity.id);
  if(!former||fingerprint(entity)!==fingerprint(former))
   throw Error('Source alternative changed original object identity, category or geometry');
  const diff=Math.hypot(...['x','y','z'].map(k=>entity.position[k]-former.position[k]));
  if(diff>1e-7||entity.supportId!==former.supportId){
   if(!subjects.has(entity.kind))
    throw Error('Object moved without explicit frozen source-relation subject kind: '+row.sourceId);
   moved++;
  }
 }
 if(ctl.scene.entities.length!==alt.scene.entities.length)
  throw Error('Source alternative changed original body budget');
}
if(moved!==67)throw Error('Original measured source movements unexpectedly changed');
console.log('VERIFIED original 130 source scene body identities, fixed original 3D collider dimensions,');
console.log('all 67 source-conditioned moved bodies explicitly relate to prior source-relation subjects.');
