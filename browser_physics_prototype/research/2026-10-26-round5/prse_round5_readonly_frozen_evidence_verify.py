#!/usr/bin/env python3
"""Truly READ ONLY independent verification of completed PRSE round-five runs.

No child server launches, no model, no output writes, no authority rewriting.
Check frozen human source/response identity, reference ID provenance,
real earlier native Rapier physics, changed deployment errors, elapsed times
and exact persistent source/host bytes protected at 0600.
"""
from pathlib import Path
from stat import S_IMODE
from collections import Counter
from hashlib import sha256
import json, math, statistics
HERE=Path(__file__).resolve().parent
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
EXT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1')
RUN=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-round5-source-authority')
def hashfile(p):return sha256(p.read_bytes()).hexdigest()
def jsonfile(p):return json.loads(p.read_text())
def utf16size(s):return len(s.encode('utf-16-le'))//2
goldpath=BASE/'lego_full_data_public_human_gold.json'
gold=jsonfile(goldpath)
assert len(gold)==130
assert S_IMODE(RUN.stat().st_mode)==0o700
assert S_IMODE(goldpath.stat().st_mode)==0o600
ref={i:jsonfile(BASE/f'reference-snapshots/data_{i}.json') for i in range(130)}
assert all(ref[i]['index']==i and ref[i]['query']==gold[i]['instruction'] for i in range(130))
originals=[]
for i,doc in enumerate(gold):
 originals.append((i,'complete_human_author_instruction','Full human source',None,doc['instruction']))
 for l in doc['labels']:
  originals.append((i,'human_annotated_clause',l['condition_type'],
                    l['condition_idx'],' '.join(l['instructions'])))
assert len(originals)==1380
accepted=[]
for name in ['committed_research_viewer_server','current_canonical_uncommitted_server']:
 raw=RUN/(name+'-raw-v2.json')
 assert S_IMODE(raw.stat().st_mode)==0o600
 r=jsonfile(raw)
 assert r['metadata']['LEGOHumanAuthoredIndependentConstraintSourceSHA256']==hashfile(goldpath)
 assert len(r['perOriginalRequest'])==1380
 assert r['results']['sampleCount']==1380
 records=r['perOriginalRequest']
 c=Counter()
 for request,row in zip(originals,records):
  scene,group,label,idx,s=request
  assert row['sourceIndex']==scene
  assert row['group']==group
  assert row['labelType']==label
  assert row['originalLabelIndex']==idx
  assert row['originalInputLengthJSUTF16']==utf16size(s)
  assert row['originalSourceSHA256']==sha256(s.encode()).hexdigest()
  assert (row['responseType']=='rejected')==(utf16size(s)>120)
  c[(group,row['responseCategory'])]+=1
 assert sum(v for (group,code),v in c.items() if group=='complete_human_author_instruction')==130
 assert sum(v for (group,code),v in c.items() if group=='human_annotated_clause')==1250
 assert sum(v for (group,code),v in c.items() if code=='rejected')==147
 assert sum(v for (group,code),v in c.items() if code=='other_text_without_confirmed_source_world')==2
 assert sum(v for (group,code),v in c.items() if code=='unsupported_foreign_world_object')==136
 assert r['results']['finalSavedGameSceneEntities']==11
 assert r['results']['finalSavedSourceSpecificProjectorCount']==0
 assert r['results']['finalSavedSourceSpecificTableCount']==0
 assert r['results']['modelRequestsSent']==0
 data=RUN/(name+'-private-game-state-v2')
 assert S_IMODE(data.stat().st_mode)==0o700
 snapshots=list(data.glob('*.snapshot.json'));logs=list(data.glob('*.events.ndjson'))
 assert len(snapshots)==len(logs)==1
 for p in (snapshots[0],logs[0]):
  assert S_IMODE(p.stat().st_mode)==0o600
 snapshot=jsonfile(snapshots[0])
 assert snapshot['version']==5 and len(snapshot['semantic']['entities'])==11
 assert not any(e['kind'] in ('projector','table') for e in snapshot['semantic']['entities'])
 events=[json.loads(x) for x in logs[0].read_text().splitlines() if x.strip()]
 assert Counter(x.get('eventType') for x in events if x.get('kind')=='event')==Counter({'invalid_action':1,'invalid_target':1})
 assert sum(x.get('kind')=='text_command' for x in events)==1233
 assert not any(x.get('kind','').startswith('llm') for x in events)
 accepted.append(r)
safe2=jsonfile(HERE/'prse_round5_real_human_source_websocket_cost_error_latency_aggregate_v2.json')
safe3=jsonfile(HERE/'prse_round5_corrected_source_deployment_accuracy_cost_latency_aggregate_v3.json')
for name,r in zip(('committed_research_viewer_server','current_canonical_uncommitted_server'),accepted):
 assert safe2['comparison'][name]['privateCompleteRawSHA256']==hashfile(RUN/(name+'-raw-v2.json'))
 a=safe3['serverVersions'][name]
 assert a['privateFrozenEvidenceSHA256']==hashfile(RUN/(name+'-raw-v2.json'))
 assert a['classification']['full_rejected']==128
 assert a['classification']['full_help']==2
 assert a['classification']['clause_rejected']==19
 assert a['classification']['clause_help']==1229
 assert a['classification']['clause_invalid_game_action']==2
 assert a['classification']['unsupported_bench_not_in_user_input']==133
 assert a['nativeInvalidActionErrors']=={'invalid_action':1,'invalid_target':1}
 assert a['originalSceneSuccessfulMaterializations']==0
 assert abs(a['medianResponseMs']-r['results']['latencyMilliseconds']['all']['median'])<.0001
 assert abs(a['p95ResponseMs']-r['results']['latencyMilliseconds']['all']['p95'])<.0001
 assert a['totalIndependentSceneSources']==130
 assert a['originalIndependentlyHumanAnnotatedClauses']==1250
 assert a['noGpuOrModelInference']
assert all(
 (x['sourceIndex'],x['responseType'],x['responseSHA256'],x['originalSourceSHA256'])==
 (y['sourceIndex'],y['responseType'],y['responseSHA256'],y['originalSourceSHA256'])
 for x,y in zip(accepted[0]['perOriginalRequest'],accepted[1]['perOriginalRequest']))
srcaudit=jsonfile(HERE/'prse_round5_source_authority_reference_native_aggregate_v1.json')
priv=RUN/'prse_round5_source_vs_reference_vs_native_percase_v1.json'
assert priv.is_file() and S_IMODE(priv.stat().st_mode)==0o600
assert srcaudit['metadata']['percaseRawSHA256']==hashfile(priv)
assert srcaudit['metadata']['independentOriginalHumanSourceSHA256']==hashfile(goldpath)
native=EXT/'lego_extended_actual_native_matched_130_raw_v2.json'
assert srcaudit['metadata']['newExtendedNativeFrozenSHA256']==hashfile(native)
c=srcaudit['counts']
assert c['humanScenes']==130
assert c['sourceNamedReferenceRoomInstances']==295
assert c['multipleRoomScenes']==95
assert c['referenceIdCategorizedAssets']==6844
assert c['sameIdRepeatedInReferenceAssets']==6
assert c['rawIdReferenceOldMatch']==251 and c['rawIdReferenceExtendedMatch']==294
assert c['physicalBodiesPrevious']==575 and c['physicalBodiesExtended']==678
assert c['realNativeContactPairsExtended']==11
assert c['physicalContactNotUprightTopSupport']==1
assert c['physicalContactWronglyCalledHumanOnByLegacyMachineGold']==1
assert c['physicalContactEntailedBySelectedHumanClause']+c['physicalContactEntailedByPreviouslySelectedHumanClause']==9
assert c['sixAuthorSourceDirectOnHumanClauses']==6 and c['sixAuthorExactLinkedReferencePairs']==1
assert len(srcaudit['sixPosthocNewSupportSourceReferenceCases'])==6
assert len({e['id'] for refscene in ref.values() for e in refscene['objects']}) < 6844 # IDs repeat within a few scenes
assert sum(len({e['id'] for e in r['objects']}) for r in ref.values())==6838
prev=BASE/'lego_source_only_matched_native_130_raw_v1.json'
a=jsonfile(prev)['summary']; b=jsonfile(native)['summary']
assert a['totalWallSeconds']==40.88 and b['fullCpuWallSeconds']==45.55
assert b['trueNewNativeSourceContacts']==6 and b['originalNativeContactsLost']==0
assert b['samePhysicalBodiesInEachArm']==678
prev3=jsonfile(HERE.parent/'2026-10-26-round3/round3_independent_human_source_hard_negative_gold_aggregate_v1.json')
assert prev3['measured']['nonvertical_source_new_contact_unsupported']==1
assert prev3['measured']['original_machine_gold_nonvertical']==11
# Fixed benchmark post-frozen independent human positives: no false positive
# rate estimate beyond the selected cases is permitted.
assert safe3['metadata']['noIndependentExhaustiveSourceContactNegatives']
assert safe3['metadata']['posthocSourceTopSelectionBiasStillApplies']
assert safe3['metadata']['backendResponseLatencyMeasuresFastErrorRepliesNotSceneGeneration']
print('VERIFIED PRSE ROUND FIVE, read-only, no external effects:')
print('Original 130 human scenes + 1,250 human source constraints, exactly same inputs to both actual GameCore backends.')
print('128 full scenes too long, 2 short unsupported; 19 annotations overlimit, 1,229 help, 2 spurious actions, zero scenes created.')
print('Both isolated backends persisted 11 original forest entities and emitted 1 invalid action plus 1 invalid target.')
print('Original LEGO source/reference IDs, native Rapier 11 contacts: 10 top, 9 posthoc source-selected support.')
print('No source-hallucination precision claim, no exhaustive negatives, no random-parent placebo.')
