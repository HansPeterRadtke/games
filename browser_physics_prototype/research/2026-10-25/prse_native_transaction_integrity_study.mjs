// Actual native GameCore semantic/physics transaction validation against
// corrupted binary bytes, wrong Rapier build fingerprint, altered source prose,
// forged native handles and mixed snapshots. This is a trusted internal save
// contract, not cryptographic authentication of hostile user-supplied files.
import{writeFileSync}from'node:fs';
import{createHash}from'node:crypto';
import{initializePhysics}from'../../physics-core.js';
import{PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';
import{repairScene}from'./prse_relation_local_optimizer.mjs';
import{readResearchEvidence}from'../2026-10-24/prse_research_evidence_io.mjs';
import{recordNativePRSEState,restoreNativePRSEState}from'./prse_native_world_transaction.mjs';
await initializePhysics();
const proposal=JSON.parse(readResearchEvidence('prse_semantic_constraints_eval_all500_v3.json')).proposalsAll500[27];
const layout=repairScene(proposal,{maxSweeps:2,maxAttemptsPerScene:150});
const native=new PRSELoop(layout.scene);
native.tick(50);
const original=recordNativePRSEState(native);
const valid=restoreNativePRSEState(original);
if(!valid.ok)throw Error('Pristine physical/semantic transaction failed: '+valid.reason);
valid.loop.dispose();
const json=x=>JSON.parse(JSON.stringify(x)),sha=x=>createHash('sha256').update(x).digest('hex');
const cases=[
 ['corrupt_binary_sha',s=>s.nativeSha256='f'.repeat(64)],
 ['wrong_rapier_build',s=>s.rapierVendoredSha256='f'.repeat(64)],
 ['different_narrative_source',s=>s.structured.scene.prose='Unexpected replaced historical description'],
 ['wrong_native_player_handle',s=>s.handles.player=123456789],
 ['wrong_native_data_length',s=>s.nativeBytes+=2],
 ['future_world_time',s=>s.currentWorldTime+=5],
 ['absent_scene_object',s=>s.exactEntityIDs.pop()],
 ['untrusted_type',s=>s.requiresTrustedInput=false],
 ['missing_contact_history',s=>s.frameContactPairs.push('unverified_pair')]
];
const results=[];
for(const [name,alter]of cases){
 const changed=json(original);
 alter(changed);
 const loaded=restoreNativePRSEState(changed);
 if(loaded.ok){loaded.loop.dispose();throw Error('An intentionally corrupted native snapshot was accepted: '+name);}
 results.push({type:name,rejected:!loaded.ok,reason:loaded.reason});
}
// More serious: mutate a body handle to an invalid one AND independently
// recompute the simple file-corruption hash. This is still not an authenticated
// proof: the project explicitly only loads trusted owner-produced snapshots.
const wrong=json(original);
wrong.handles.player=123456789;
wrong.handleMapSHA256=sha(Buffer.from(JSON.stringify(wrong.handles)));
const rejectedMissing=restoreNativePRSEState(wrong);
if(rejectedMissing.ok){rejectedMissing.loop.dispose();throw Error('Native handle validation accepted nonexistent player body');}
const status={metadata:{source:'Previously frozen SceneEval source27, exact native Rapier/GameCore',limitation:'Owner-trusted snapshot integrity only, not cryptographic tamper-proof authenticated save'},
 validNativeRestores:true,
 rejectedCorruptedCases:results,
 invalidNativeBodyHandleRejectedEvenWhenFileHashRecomputed:!rejectedMissing.ok,
 noSourceDataOrBinaryCommitted:true};
writeFileSync(new URL('prse_native_transaction_integrity_results_v1.json',import.meta.url),
 JSON.stringify(status,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({valid:true,testedBadSnapshots:results.length,allRejected:results.every(x=>x.rejected),
  invalidBodyHandleRejected:!rejectedMissing.ok}));
native.dispose();
