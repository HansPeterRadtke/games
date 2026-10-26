#!/usr/bin/env python3
"""READ ONLY independent verifier of Nr3D cross-genre frozen preregistration,
blind source predictions, genuine GameCore/Rapier matched native worlds and
post-frozen phrase-to-3D human reference labels. No new effects.
"""
import json,hashlib,math,csv,re
from pathlib import Path
from stat import S_IMODE
from collections import Counter
from scipy.stats import binomtest
HERE=Path(__file__).resolve().parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-nr3d-independent-r7')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
F={
 'prereg':P/'PREREG_ORIGINAL_FROZEN_BEFORE_GOLD.md',
 'csv':P/'ScanEnts3D_Nr3D_official_raw.csv',
 'cohort':P/'nr3d_one_per_scene_480_sourceonly_frozen_v1.json',
 'pred':P/'nr3d_source_only_predictions_480_frozen_v1.json',
 'gold':P/'nr3d_postfrozen_independent_human_3d_gold_percase_v1.json',
 'physicalSource':P/'nr3d_physical_feasibility_goldblind_input_v1.json',
 'physicalRaw':P/'nr3d_matched_true_native_rapier_31cases_raw_v1.json',
 'physicsGold':P/'nr3d_31_actual_native_rapier_independent_human_phrase_labels_raw_v1.json'}
assert S_IMODE(P.stat().st_mode)==0o700
assert all(p.is_file() and S_IMODE(p.stat().st_mode)==0o600 for p in F.values())
assert sha(F['prereg'])=='688fc6d8199b30617a481460386de87a329f8ceeea1f255d2774b7416d06076f'
assert sha(F['csv'])=='f6b437e2bfc15c69c2b497c755e9a5b42eec110dccc25deb29594e3734a31f5b'
A=read(F['cohort']);B=read(F['pred']);C=read(F['gold'])
assert A['metadata']['preRegistrationSHA256']==sha(F['prereg'])
assert B['metadata']['preregSHA256']==sha(F['prereg'])
assert B['metadata']['sourceOnlyFrozenCohortSHA256']==sha(F['cohort'])
assert B['metadata']['noHumanGroundTruthFieldsOpened']
assert len(A['sourceCohort'])==len(B['records'])==len(C['rows'])==480
assert len({x['scanId'] for x in A['sourceCohort']})==480
pred={row['datasetIndex']:row for row in B['records']}
reference={row['sourceId']:row for row in C['rows']}
assert set(pred)==set(reference)
agg=read(HERE/'prse_round7_nr3d_independent_real3d_reference_aggregate_v1.json')
assert agg['metadata']['originalFrozenPreRegistrationSHA256']==sha(F['prereg'])
assert agg['metadata']['sourceOnlyFrozenPredictionSHA256']==sha(F['pred'])
assert agg['metadata']['postFrozenIndependentAnnotationPerCaseSHA256']==sha(F['gold'])
m=agg['metrics']
assert m['independent3DScanScenes']==480
assert m['baselineSourceLexiconProposed']==389
assert m['pretrainedSourceNounProposed']==479
assert m['baselineAllSourceExactTargetKind']==231
assert m['pretrainedAllSourceExactTargetKind']==309
assert m['pairedBySceneGain']==104 and m['pairedBySceneLoss']==26
assert math.isclose(binomtest(26,130,.5).pvalue,3.025786266290503e-12,rel_tol=1e-4)
assert m['pretrainedMinusLexiconAllInputExactTargetGain']==.1625
assert m['pairedBootstrap95Gain']==[.116667,.208333]
assert m['humanTargetPhrase3DObjectIdGoldAvailable']==478
assert m['naturalNontopCaseCount']==71 and m['naturalNontopFalseTopPromotionCount']==0
assert m['unverifiedSourceOnlyOnProposalsCount']==15
assert not m['preregisteredSourceTransferAccepted']
assert not m['preregisteredFullPRSELiteraryWorldGeneralizationAccepted']
for item in A['sourceCohort']:
 i=item['datasetIndex'];prior=pred[i];after=reference[i]
 assert item['sourceHash']==prior['sourceHash']==after['sourceSHA256']
 assert hashlib.sha256(item['text'].encode()).hexdigest()==after['sourceSHA256']
 assert prior['scanId']==after['scanId']==item['scanId']
 assert not prior['badSupportProposalOverlap']
 assert bool(prior['sourceOnlyPretrainedTargetType'])==bool(after['pretrainedPredictedKind'])
 assert bool(prior['baselineTargetType'])==bool(after['baselinePredictedKind'])
# Original human 3D target class/instance evaluated only after prediction;
# phrases are one per scan and carry target IDs; outputs have no instance ID.
assert all(isinstance(x['officialTarget3DInstanceId'],str) for x in C['rows'])
assert not any('targetIdPrediction' in x for x in B['records'])
Psrc=read(F['physicalSource']);Pnative=read(F['physicalRaw']);Pgold=read(F['physicsGold'])
assert Psrc['metadata']['sourceOnlyPredictionsSHA256']==sha(F['pred'])
assert Psrc['metadata']['goldNotConsulted']
assert Pnative['metadata']['sourceOnlyPhysicalSpecSHA256']==sha(F['physicalSource'])
assert Pnative['metadata']['originalHumanGoldNotReadByNativeExperiment']
assert Pgold['metadata']['frozenSourceOnlyPhysicalSpecSHA256']==sha(F['physicalSource'])
assert Pgold['metadata']['frozenActualGameCoreRapier_SHA256']==sha(F['physicalRaw'])
assert len(Psrc['cases'])==len(Pnative['records'])==len(Pgold['cases'])==31
n=Pnative['summary']
assert n['sourceExplicitOnProposals']==15 and n['humanNegativeWithoutSourceOn']==16
assert n['actualWorldsWithExactNativeSave']==62 and n['runFailures']==0
assert n['preservedExactSameBodyKindAndDimensions']==31
assert n['realNativeSourceSupportContactCount']==15
assert n['negativeControlNativeContactDifference']==0
assert n['allBodiesProvisionalGeometry']
assert n['matchedIndependentNativePhysicsContactTruthNotAuthorSourceTruth']
assert n['human3DScanNetMeshGroundTruthUnavailable']
C=Counter()
for x,y,g in zip(Psrc['cases'],Pnative['records'],Pgold['cases']):
 assert x['scanId']==y['scanId']==g['scanId']
 assert x['datasetIndex']==y['datasetIndex']==g['datasetIndex']
 assert x['sourceHash']==y['sourceHash']==g['originalNamedSourcePhraseSHA256']
 assert y['status']=='paired_real_rapier_38ticks_each'
 assert y['nativeControl']['realNativeBodyCount']==y['nativeCandidate']['realNativeBodyCount']==2
 assert {z['id'] for z in y['nativeControl']['states']}=={z['id'] for z in y['nativeCandidate']['states']}
 state0={z['id']:z for z in y['nativeControl']['states']}
 for z in y['nativeCandidate']['states']:
  w=state0[z['id']]
  assert z['kind']==w['kind'] and z['shape']==w['shape'] and z['size']==w['size']
 assert not y['nativeControl']['contactPairs']
 assert y['nativeControl']['savedContactsExact'] and y['nativeCandidate']['savedContactsExact']
 if x['category']=='source_explicit_pretrained_on_proposal':
  assert len(y['nativeCandidate']['contactPairs'])==1
  pair=y['nativeCandidate']['contactPairs'][0]
  assert {pair['a'],pair['b']}=={x['oldBody1'],x['oldBody2']}
  assert pair['contactCount']>0
  C['sourceOnHumanTargetClassCorrect']+=g['independentTargetKindMatchesProposedChild']
  C['sourceOnHumanParentAnchorLabeled']+=g['independentDifferentInstanceAnchorOfParentKind']
  C['sourceOnBothGoldNounsMatch']+=g['independentDifferentInstanceAnchorOfParentKind'] and g['independentTargetKindMatchesProposedChild']
  C['trueNativeSupportContacts']+=1
 else:
  assert not y['nativeCandidate']['contactPairs']
  C['negativeNoNewTrueRapierContact']+=1
assert dict(C)=={'sourceOnHumanTargetClassCorrect':11,'sourceOnHumanParentAnchorLabeled':4,
 'sourceOnBothGoldNounsMatch':4,'trueNativeSupportContacts':15,'negativeNoNewTrueRapierContact':16}
assert read(HERE/'prse_round7_nr3d_actual_native_rapier_feasibility_aggregate_v1.json')['metadata']['privateActualNativeRapierSHA256']==sha(F['physicalRaw'])
assert read(HERE/'prse_round7_independent_physical_roles_actual_gold_aggregate_v1.json')['metadata']['originalHuman3DReferenceRoleAuditSHA256']==sha(F['physicsGold'])
print('VERIFIED PRSE NR3D independent cross-genre 480 different 3D scene language sources; frozen prereg, no label leakage.')
print('Original lexicon exact category 231/480, frozen pretrained nominal class 309/480, paired gain 78')
print('with 95%-CI +11.7 to +20.8 points; preregistered 75% target FAILS. Nr3D unique 3D IDs remain unpredicted.')
print('Independent ScanEnts3D 3D target mentions 478/480, 71 source natural non-top controls with 0 false on proposals.')
print('31 paired REAL GameCore/Rapier source-only scenes, 62 native snapshots, identical bodies,')
print('15 real contacts from source-only candidate support placements, 16 natural negative scenes with unchanged contacts.')
print('Independent 3D annotation: only 11 source target classes and 4 anchor classes matched in these 15;')
print('real ScanNet meshes/metric geometry and author-rated physical contacts UNAVAILABLE, so no physical fidelity claim.')
