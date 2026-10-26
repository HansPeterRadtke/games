#!/usr/bin/env python3
"""Read-only post-frozen correction and deployment choice comparison.

The two fully frozen v2 tests were source identical but had a misleading
'author_relevant_answer=2' diagnostic. These were actually WRONG in-game
target/action errors, not successful literary interpretation. Compare exact
WebSocket replies to original independently authored LEGO scenes and ALL
1,250 human-annotated constraints, and prior authoritative Rapier studies.
Never rerun the external effects or denied placebos; preserve all versions.
"""
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
from stat import S_IMODE
import json,statistics
HERE=Path(__file__).resolve().parent
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
EXT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1')
RUN=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-round5-source-authority')
def read(p):return json.loads(p.read_text())
def sha(p):return sha256(p.read_bytes()).hexdigest()
def sha_text(s):return sha256(s.encode()).hexdigest()
def jslen(s):return len(s.encode('utf-16-le'))//2
gold=read(BASE/'lego_full_data_public_human_gold.json')
assert len(gold)==130
cases=[]
for i,row in enumerate(gold):
  cases.append((i,'complete_human_author_instruction','Full human source',None,row['instruction']))
  for label in row['labels']:
    cases.append((i,'human_annotated_clause',label['condition_type'],label['condition_idx'],
                  ' '.join(label['instructions'])))
assert len(cases)==1380
versions=['committed_research_viewer_server','current_canonical_uncommitted_server']
results={};_raw={}
for name in versions:
 p=RUN/(name+'-raw-v2.json')
 assert S_IMODE(p.stat().st_mode)==0o600
 d=read(p)
 assert d['metadata']['LEGOHumanAuthoredIndependentConstraintSourceSHA256']==sha(BASE/'lego_full_data_public_human_gold.json')
 assert d['results']['sampleCount']==len(cases)
 assert len(d['perOriginalRequest'])==len(cases)
 summary=Counter()
 for i,(case,r) in enumerate(zip(cases,d['perOriginalRequest'])):
  scene,kind,label,originalIndex,text=case
  assert (r['sourceIndex'],r['group'],r['labelType'],r['originalLabelIndex'])==(scene,kind,label,originalIndex)
  assert r['originalInputLengthJSUTF16']==jslen(text) and r['originalSourceSHA256']==sha_text(text)
  over=jslen(text)>120
  assert (r['responseType']=='rejected')==over
  c=r['responseCategory']
  summary['all']+=1;summary['full' if kind.startswith('complete') else 'clause']+=1
  summary['full_overlimit' if over and kind.startswith('complete') else 'clause_overlimit' if over else 'valid_within_limit']+=1
  summary['full_rejected' if kind.startswith('complete') and over else 'full_help' if kind.startswith('complete') else 'clause_rejected' if over else 'clause_help' if 'unsupported' in c else 'clause_invalid_game_action']+=1
  summary['unsupported_foreign_game_target']+=int(c=='unsupported_foreign_world_object')
  summary['unsupported_bench_not_in_user_input']+=int(c=='unsupported_foreign_world_object' and 'bench' not in text.casefold())
  summary['unexpected_native_game_action_dispatch']+=int(c=='other_text_without_confirmed_source_world')
 assert summary['full']==130 and summary['clause']==1250
 assert summary['full_overlimit']==128 and summary['clause_overlimit']==19
 assert summary['full_rejected']==128 and summary['full_help']==2
 assert summary['clause_rejected']==19 and summary['clause_help']==1229
 assert summary['clause_invalid_game_action']==2
 assert summary['unexpected_native_game_action_dispatch']==2
 assert summary['unsupported_foreign_game_target']==136 and summary['unsupported_bench_not_in_user_input']==133
 assert d['results']['finalSavedGameSceneEntities']==11
 assert d['results']['finalSavedSourceSpecificProjectorCount']==0
 assert d['results']['finalSavedSourceSpecificTableCount']==0
 assert d['results']['modelRequestsSent']==0
 assert d['results']['allIsolatedServerProcessesTerminated']
 assert d['results']['privateSavedDataPermissionsOk']
 assert d['results']['reportedConfiguredPhysicsHz']==60
 logfile=next((RUN/(name+'-private-game-state-v2')).glob('*.events.ndjson'))
 assert S_IMODE(logfile.stat().st_mode)==0o600
 events=[json.loads(s) for s in logfile.read_text().splitlines() if s.strip()]
 invalid=Counter(x.get('eventType') for x in events if x.get('kind')=='event')
 assert invalid==Counter({'invalid_action':1,'invalid_target':1}), invalid
 assert not any(x.get('kind','').startswith('llm_') for x in events)
 assert sum(x.get('kind')=='text_command' for x in events)==1233
 if name==versions[0]:
  recorded=[x for x in events if x.get('kind')=='text_command']
  valid=[case for case in cases if jslen(case[4])<=120]
  assert len(valid)==len(recorded)
  for x,src in zip(recorded,valid):
    assert sha_text(x['input'])==sha_text(src[4])
  invalid_texts={sha_text(x['result']):x['result'] for x in recorded
                 if x.get('result') in ('That action is not possible with Loose timber plank.','There is no such object.')}
  shown={x['responseSHA256'] for x in d['perOriginalRequest']
         if x['responseCategory']=='other_text_without_confirmed_source_world'}
  assert shown==set(invalid_texts), (shown,invalid_texts)
 results[name]={'privateFrozenEvidenceSHA256':sha(p),'actualBackendSourceSHA256':d['results']['serverEngineCodeSHA256'],
 'classification':dict(summary),'medianResponseMs':d['results']['latencyMilliseconds']['all']['median'],
 'p95ResponseMs':d['results']['latencyMilliseconds']['all']['p95'],
 'allRequestWallSeconds':d['results']['allQueriesWallSeconds'],
 'serverStartupSeconds':d['results']['startupSeconds'],
 'hostCPUSampledSeconds':d['results']['CPUSecondsForHostSampled'],
 'hostPeakObservedRSSMiB':d['results']['peakObservedResidentMiB'],
 'originalSceneSuccessfulMaterializations':0,
 'totalIndependentSceneSources':130,'originalIndependentlyHumanAnnotatedClauses':1250,
 'nativeInvalidActionErrors':dict(invalid),
 'originalAuthorSceneEntitiesNeverCreated':True,
 'noGpuOrModelInference':True}
 _raw[name]=d
assert all(
 (r['sourceIndex'],r['originalSourceSHA256'],r['responseCategory'],r['responseSHA256'])==
 (s['sourceIndex'],s['originalSourceSHA256'],s['responseCategory'],s['responseSHA256'])
 for r,s in zip(_raw[versions[0]]['perOriginalRequest'],_raw[versions[1]]['perOriginalRequest']))
# Performance is a single sequential sample, NOT an independent controlled
# timing trial: do not infer causation/variance advantage from these numbers.
past=read(BASE/'lego_source_only_matched_native_130_raw_v1.json')
new=read(EXT/'lego_extended_actual_native_matched_130_raw_v2.json')
extras=read(EXT/'lego_extended_source_only_130_raw_v1.json')
reference=read(HERE/'prse_round5_source_authority_reference_native_aggregate_v1.json')
physical_metrics={'sourceOnlyFullCorpusCount':130,
 'oldPhysicalWorldArms':390,'oldEngineWallSeconds':past['summary']['totalWallSeconds'],
 'oldNativeBodyInstancesInOneArm':past['summary']['sourceEntitiesActuallyMaterialized'],
 'oldActualInterobjectNativeContacts':past['summary']['lexicalTrueNativeContacts'],
 'extendedPhysicalWorldArms':260,'extendedEngineWallSeconds':new['summary']['fullCpuWallSeconds'],
 'extendedSourceGrammarWallSeconds':extras['elapsedSeconds'],
 'extendedNativeBodyInstancesPerArm':new['summary']['samePhysicalBodiesInEachArm'],
 'extendedActualNativeContactPairs':new['summary']['extendedSourceOnlyNativeContacts'],
 'extendedActuallyNewInterobjectContacts':new['summary']['trueNewNativeSourceContacts'],
 'extendedNativePreexistingContactsLost':new['summary']['originalNativeContactsLost'],
 'extendedNativeTrueTopSupports':new['summary']['extendedSourceOnlyNativeContacts']-reference['counts']['physicalContactNotUprightTopSupport'],
 'extendedPhysicalContactsBackedByPosthocSelectedHumanSourceClauses':reference['counts']['physicalContactEntailedBySelectedHumanClause']+reference['counts']['physicalContactEntailedByPreviouslySelectedHumanClause'],
 'extendedPhysicalContactsNotEntailedByHumanWordMeaning':reference['counts']['physicalContactWronglyCalledHumanOnByLegacyMachineGold'],
 'extendedPhysicalContactButNotTopSurface':reference['counts']['physicalContactNotUprightTopSupport'],
 'independentlyNamedReferenceRoomInstances':reference['counts']['sourceNamedReferenceRoomInstances'],
 'multiRoomReferenceScenesNotGroundedByCompiler':reference['counts']['multipleRoomScenes'],
 'referenceIdObjectCategoryOverlapCeilingPrevious':reference['counts']['rawIdReferenceOldMatch'],
 'referenceIdObjectCategoryOverlapCeilingExtended':reference['counts']['rawIdReferenceExtendedMatch'],
 'referenceIdObjectCategoryCoverageIsNotSourceRecall':True}
assert physical_metrics['extendedNativeTrueTopSupports']==10
assert physical_metrics['extendedPhysicalContactsBackedByPosthocSelectedHumanSourceClauses']==9
assert physical_metrics['extendedPhysicalContactsNotEntailedByHumanWordMeaning']==1
assert physical_metrics['extendedPhysicalContactButNotTopSurface']==1
timing=new['rows'];k={}
for key in ('controlSeconds','candidateSeconds'):
 xs=sorted(1000*r[key] for r in timing)
 assert len(xs)==130
 k[key]={'n':130,'p50ms':round(xs[64],3),'p95ms':round(xs[123],3),
         'meanMs':round(statistics.mean(xs),3),'maximumMs':round(xs[-1],3)}
physical_metrics['extendedNewNativePairedArmTimingMs']=k
p0=_raw[versions[0]]['perOriginalRequest']
p1=_raw[versions[1]]['perOriginalRequest']
delta=[b['elapsedMilliseconds']-a['elapsedMilliseconds'] for a,b in zip(p0,p1)]
physical_metrics['versionTimingDifferenceMs']={
 'pairedSinglePassMedianCanonicalMinusCommitted':round(statistics.median(delta),3),
 'fasterCanonicalResponses':sum(x<0 for x in delta),'pairs':len(delta),
 'notCausalOrRepeatControlled':True}
final={'metadata':{'LEGOOriginalHumanAnnotatedSourceSHA256':sha(BASE/'lego_full_data_public_human_gold.json'),
 'humanOriginalSourceAndIndependentConstraintLabelsOverrideReferenceInstanceNamingConflicts':True,
 'current3DPhysicsClaimsNeedNativeContactManifoldButCannotProveAuthorMeaning':True,
 'incorrectPriorV2Field':'source_author_relevant_answer counted two unrelated invalid game actions; corrected here; original raw is preserved',
 'noIndependentExhaustiveSourceContactNegatives':True,'posthocSourceTopSelectionBiasStillApplies':True,
 'nonComparableFullRunWallTimesHaveDifferentWorldArmCountsAndBodyCounts':True,
 'backendResponseLatencyMeasuresFastErrorRepliesNotSceneGeneration':True,
 'noExternalProductionEffects':True,'doNotPromoteRawSceneReferenceAssetsOverOriginalHumanConstraints':True},
 'serverVersions':results,'frozenActualNativePhysicsAndSourceParsing':physical_metrics}
outfile=HERE/'prse_round5_corrected_source_deployment_accuracy_cost_latency_aggregate_v3.json'
with outfile.open('x') as f:json.dump(final,f,indent=2);f.write('\n')
print('CORRECTED_REAL_HUMAN_SOURCE_DEPLOYMENT',json.dumps({k:{
 'fullSourceRejected':v['classification']['full_rejected'],
 'shortFullSourceHelp':v['classification']['full_help'],
 'humanClauseRejected':v['classification']['clause_rejected'],
 'humanClauseHelp':v['classification']['clause_help'],
 'humanClauseInvalidGameActions':v['classification']['clause_invalid_game_action'],
 'medianMs':v['medianResponseMs'],'p95Ms':v['p95ResponseMs']}
 for k,v in results.items()},sort_keys=True))
print('INDEPENDENT_PAPER_SOURCE_REFERENCE_NATIVE_COSTS',json.dumps(physical_metrics,sort_keys=True))
