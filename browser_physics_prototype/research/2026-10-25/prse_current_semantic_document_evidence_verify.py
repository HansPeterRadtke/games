#!/usr/bin/env python3
"""Read-only evidence and immutable-failure verifier for PRSE's current semantic
document over the SAME authoritative GameCore/Rapier world.

Covers original failed journal-time v1, new v2 physical/source/observer native
save and actual next GameCore step, third-party SceneEval source provenance,
past independent support audit and explicit offscreen fire/ash rematerialization.

Complete source-derived rows and original authored descriptions remain
owner-private Nitro research bytes, not copied into public Games Git.
"""
import csv,io,json,hashlib,stat,zipfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-current-document')
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(rows)==500
ids=list(range(100))+list(range(100,500,4))
manifest={}
summary={}
for method,version in [('deterministic','v1'),('deterministic','v2'),('union','v2')]:
 file=PRIVATE/f'prse_current_world_document_{method}_200_raw_{version}.json'
 assert file.is_file() and stat.S_IMODE(file.stat().st_mode)==0o600
 data=read(file)
 output=read(ROOT/f'prse_current_world_document_{method}_200_aggregate_{version}.json')
 assert sha(file)==output['metadata']['privateRawSHA256']
 assert data['summary']==output['summary']
 results=data['results']
 assert len(results)==200 and [x['sourceID'] for x in results]==ids
 assert all(rows[x['sourceID']]['ID']==str(x['sourceID']) for x in results)
 s=data['summary']
 if method=='deterministic' and version=='v1':
  assert s['runtimeFailures']==7 and s['accepted']==190
  failed=[x for x in results if x['status']=='failed']
  assert sorted(x['sourceID'] for x in failed)==[34,46,120,132,332,356,416]
  assert all('Inconsistent final historical facts' in x['failure'] for x in failed)
 else:
  assert s['runtimeFailures']==0
  assert s['accepted']==(197 if method=='deterministic' else 195)
  assert s['physicalSceneRejected']==(3 if method=='deterministic' else 5)
  assert s['unsupportedOriginalRelationsNarrated']==0
  assert s['validNativeWorldAndSemanticJournalSave']==s['accepted']
  assert s['nativeResumedPhysicalSourceTruthEqual']==s['accepted']
  assert s['noDuplicateUnchangedRevision']==s['accepted']
  assert s['semanticsChangedAfterNativeImpulse']==57
  assert s['currentPhysicalEntityClaims']>800
  assert s['sourceRelationsNotVerifiable']>s['sourceRelationsPhysicallyVerified']
  assert s['currentUnloadedIdentityClaims']==0, 'This corpus is deliberately materialized; offscreen tested separately'
  assert s['newCanonicalCurrentDocumentBytes']<s['originalHistoricalDescriptionBytes']
  assert all(x['unverifiedSourceRelationsNarrated']==0 for x in results)
  assert all(x['nativeSaveRestored'] and x['identicalNativeText'] for x in results if x['status']=='verified')
 manifest[file.name]={'sha256':sha(file),'bytes':file.stat().st_size,'private':True}
 summary[f'{method}_{version}']=s

prior=read(ROOT/'prse_legacy_support_claim_audit_200_aggregate_v1.json')
legacyRaw=PRIVATE/'prse_legacy_describe_support_claims_200_raw_v1.json'
assert legacyRaw.is_file() and stat.S_IMODE(legacyRaw.stat().st_mode)==0o600
assert sha(legacyRaw)==prior['privateRawSHA256']
assert prior['summary']['savedNonFloorSupportClaims']==39
assert prior['summary']['physicalTrue']==39
assert prior['summary']['physicalFalse']==prior['summary']['physicalUnknown']==0
manifest[legacyRaw.name]={'sha256':sha(legacyRaw),'bytes':legacyRaw.stat().st_size,'private':True}
annotation=read(ROOT/'prse_grounded_prose_source_annotation_audit_v3.json')
priorAnnotated={}
for name in ('deterministic','union'):
  parts=annotation['results'][name]['sourceAudit']['object_unordered']
  countedTrue=sum(parts[grp]['confirmedActualPhysicalTypePairs'] for grp in ('human','assisted'))
  annotatedTrue=sum(parts[grp]['matchedGoldAndPhysicallyVerified'] for grp in ('human','assisted'))
  assert countedTrue==summary[name+'_v2']['sourceRelationsPhysicallyVerified']
  assert (countedTrue,annotatedTrue)==((100,27) if name=='deterministic' else (133,31))
  priorAnnotated[name]={'physicalTrue':countedTrue,'independentlySourceAnnotatedTrue':annotatedTrue,
   'warning':'Direction-insensitive object-type pair matching, not a semantic sentence-entailment evaluation'}

off=read(ROOT/'prse_current_semantic_temporal_reentry_v1.json')
assert off['externalSource']['nativeContactSolverAndSemanticDocumentSaved']
assert off['externalSource']['unchangedWorldTimeDidNotRewriteNarrative']
assert off['externalSource']['noInventedCauseInPresentWorldDocument']
assert off['authoredOffscreen']['qualifiedTextWhileUnloaded']
assert off['authoredOffscreen']['absentPhysicalStateNotClaimedAsCurrentlySimulated']
assert off['authoredOffscreen']['distinctNativeAshColliderRematerialized']
assert off['authoredOffscreen']['currentSemanticTextMentionsPresentAsh']
assert off['authoredOffscreen']['witnessedIgnitionLeakCount']==0
assert off['authoredOffscreen']['nativeAndSemanticTimeMatch']
assert off['tampering']['inconsistentClaimsRejected'] and off['tampering']['futureDatedRevisionRejected']
evidence={
 'metadata':{
  'source':'SceneEval-500 official author ZIP, fixed human IDs 0..99 and sampled assisted IDs 100,104,...496',
  'sourceZipSHA256':sha(CORPUS),
  'noGoldLabelsDuringWorldInterpretation':True,
  'independentAudit':'Existing separate Rapier materialized contact checks plus native current document/semantic journal roundtrips',
  'sourceMeaningNotProven':'Original SceneEval source relation recall remains poor; this audit proves physics-based factual qualifiers, not textual entailment or human prose quality',
  'noLLMorGPUandNoHumanParticipants':True},
 'measuredOriginalTimeBug':{
  'failedDocuments':summary['deterministic_v1']['runtimeFailures'],
  'restorationFailuresCorrectedInSameSourceSamples':summary['deterministic_v2']['runtimeFailures'],
  'reason':'Meaningful semantic revisions need not occur at every native physics world tick'},
 'results':{'deterministic_v2':summary['deterministic_v2'],'union_v2':summary['union_v2']},
 'independentContactAudit':prior['summary'],
 'independentSourceAnnotationConcordance':priorAnnotated,
 'originalOffscreenFactAndCausalRevision':{
  'archivedSourceUnchanged':off['authoredOffscreen']['originalTextNeverOverwritten'],
  'semanticClockAdvancesWithoutClaimingActivePhysics':off['authoredOffscreen']['qualifiedTextWhileUnloaded'],
  'realAshColliderAfterReentry':off['authoredOffscreen']['distinctNativeAshColliderRematerialized'],
  'noUnwitnessedIgnitionDisclosure':True,
  'historyAndCurrentClaimsIntegrityTamperingRejected':True},
 'rawPrivateManifest':manifest}
destination=ROOT/'prse_current_semantic_document_evidence_manifest_v2.json'
if destination.exists():assert read(destination)==evidence,'Do not overwrite consumed differing evidence manifest'
else:
 with destination.open('x') as f:json.dump(evidence,f,indent=2);f.write('\n')
print('VERIFIED two hundred externally sourced scenes in both source interpreters,')
print('original seven false history-clock failures retained and fixed,')
print('physics-confirmed relation and actual native save/reentry,')
print('exactly thirty-nine previously checked native physical support claims,')
print('and original authored offscreen fire/ash semantic continuity.')
