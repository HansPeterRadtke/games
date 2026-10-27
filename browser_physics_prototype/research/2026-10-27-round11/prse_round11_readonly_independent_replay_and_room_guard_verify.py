#!/usr/bin/env python3
"""READ-ONLY independent PRSE round 11 frozen native physics continuation audit.
Checks true source-only 3D world reproduction, genuine Rapier contacts,
trusted binary-vs-uninterrupted and JSON-vs-uninterrupted after identical
actions, room-specific current-text truth, actual immutable human labels,
previous denied-operation protections and owner-only source privacy.

--write-once emits a new safe aggregate ONLY, exclusively, after evidence
verification. Default is strictly READ ONLY and rerunnable.
"""
import json,hashlib,math,statistics,sys
from pathlib import Path
from stat import S_IMODE
from collections import Counter
HERE=Path(__file__).resolve().parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round11-causal-restore')
PREVIOUS=Path('/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round9-room-contract')
LEGO=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
def read(p):return json.loads(p.read_text())
def hashpath(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def certifyPrivate(p):
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600,(p,str(oct(p.stat().st_mode)))
SOURCE=PREVIOUS/'source_original_strict_room_proposal_frozen_v3.json'
PRIOR=PREVIOUS/'room_source_to_native_to_factual_text_v3_raw_v2.json'
PRIORGOLD=PREVIOUS/'actual_saved_native_source_vs_independent_human_constraints_v1.json'
HUMAN=LEGO/'lego_full_data_public_human_gold.json'
INITIAL=PRIVATE/'round11_actual_native_three_human_source_continuation_raw_v1.json'
AMPLITUDE=PRIVATE/'round11_native_impulse_strength_diagnostic_raw_v2.json'
for dir in (PRIVATE,PREVIOUS):
 assert dir.is_dir() and S_IMODE(dir.stat().st_mode)==0o700
for f in (SOURCE,PRIOR,PRIORGOLD,HUMAN,INITIAL,AMPLITUDE):
 certifyPrivate(f)
S=read(SOURCE);old=read(PRIOR);gold=read(PRIORGOLD);H=read(HUMAN)
FIRST=read(INITIAL);SECOND=read(AMPLITUDE)
assert len(S['cases'])==len(old['cases'])==3
assert [e['sceneIndex'] for e in S['cases']]==[20,26,40]
assert old['summary']['nativeActualSourceInstances']==17
assert old['summary']['sourceNegativeRoomFacts']==4
assert old['summary']['casesNativeSuccessful']==3
assert gold['metrics']['sourceGoldComputerSupportClausesUnfulfilled']==1
assert gold['metrics']['sourceGoldRoomAdjacencyClausesViolated']==1
assert gold['metrics']['completeLiteraryScenesAccepted']==0
for sourceCase in S['cases']:
 i=sourceCase['sceneIndex']
 assert sourceCase['sourceText']==H[i]['instruction']
 assert sourceCase['sourceTextSHA256']==hashlib.sha256(H[i]['instruction'].encode()).hexdigest()
 assert sourceCase['FULL_AUTHOR_SCENE_APPROVED'] is False
for version,raw in (('v1',FIRST),('v2',SECOND)):
 assert raw['metadata']['frozenStrictSourceOnlySHA256']==hashpath(SOURCE)
 assert raw['metadata']['previousRound9NativeWorldSHA256']==hashpath(PRIOR)
 assert raw['metadata']['originalAuthorHumanLabelsNotReadByPhysics']
 assert raw['metadata']['deniedRandomParentNeverTried']
 assert raw['metadata']['blockedObserverOffscreenNeverTried']
 assert raw['metadata']['realGameCoreRapierNativeOnly']
 assert raw['summary']['productionGPUAndUserSessionsUntouched']
 assert len(raw['rows'])==6
 assert raw['summary']['pairedNativeBinaryVsUninterruptedScenarios']==6
 assert raw['summary']['expectedNativeBodysAcrossScenes']==65
 for row in raw['rows']:
  assert row['scene'] in (20,26,40)
  assert row['sourceSHA256']==next(x['sourceTextSHA256'] for x in S['cases'] if x['sceneIndex']==row['scene'])
  assert row['originalPhysicalWorldReproduction']['originalNativeContactPairsReproducedExactly']
  assert row['originalPhysicalWorldReproduction']['maximum3DPositionDifferenceMetres']<.0005
  assert row['initialNativeRestore']['maximumPositionDifferenceMetres']==0
  assert row['initialNativeRestore']['maximumVelocityDifference']==0
  assert row['initialNativeRestore']['nativeContactPairIDsIdentical']
  assert row['initialNativeRestore']['nativeStepCountEqual']
  assert not row['initialLegacyJSONRestore']['nativeContactPairIDsIdentical']
  assert row['initialLegacyJSONRestore']['maximumPositionDifferenceMetres']==0
  assert row['endNativeBinaryVsUninterrupted']['sourceTextExactlyIdentical']
  assert row['endNativeBinaryVsUninterrupted']['sourceSceneIDExactlyIdentical']
  assert row['endNativeBinaryVsUninterrupted']['nativeStepCountEqual']
  assert row['endNativeBinaryVsUninterrupted']['authoritativeTimeDifferenceSeconds']==0
  assert row['endNativeBinaryVsUninterrupted']['nativeContactPairIDsIdentical']
  assert row['endJSONReconstructionVsUninterrupted']['nativeContactPairIDsIdentical']
  assert row['originalSourceTextStillUnchanged']
  assert row['originalAuthoredFullWorldStillNotValidated']
  assert row['sourceRoomGuard']['inside']+row['sourceRoomGuard']['outside'] in (3,6,8)
  # Independent source-room physical containment oracle from frozen author
  # source room names and physical source-only 18 x 14 m tile envelope.
  c=next(x for x in S['cases'] if x['sceneIndex']==row['scene'])
  inferred={}
  for j,room in enumerate(c['roomNames']):
   inferred[room]=(j-(len(c['roomNames'])-1)/2)*26
  mismatches=0
  records=row['sourceRoomGuard']['records']
  for e in records:
   assert e['sourceRoom'] in inferred
   assert e['id'].startswith('s'+str(c['sceneIndex'])+'-')
   assert e['guardedCurrentText']
   p=e['physicallyObservedPosition']
   inside=(abs(p['x']-inferred[e['sourceRoom']])<=9-.01 and
           abs(p['z']-42)<=7-.01)
   assert inside==e['truePhysicalLocationInsideSourceRoomRegion'],(version,row['scene'],row['scenario'],e['id'],inside)
   if not inside:
    assert 'current room is unverified' in e['guardedCurrentText']
    mismatches+=1
   else:
    assert 'physically in the provisional region' in e['guardedCurrentText']
  assert mismatches==row['sourceRoomGuard']['naiveRoomMetadataDescriptionsNowStale']
  assert mismatches==row['sourceRoomGuard']['outside']
# First experiment has EXACT stable controls, and 2/3 high-energy actions fail
# deterministic post-save replay. A failed native binary action is NOT an
# invalid original world; it is a failure of future exact trajectory matching.
A={(r['scene'],r['scenario']):r for r in FIRST['rows']}
assert set(A)=={(i,t)for i in [20,26,40]for t in ('no_action_negative_control','physical_impulse_positive_control')}
assert FIRST['summary']['completed']==4 and FIRST['summary']['failed']==2
assert FIRST['summary']['nativeBinaryReplayExactContacts']==6
for i in (20,26,40):
 stable=A[(i,'no_action_negative_control')]
 assert stable['status']=='actual_rapier_source_continuation_compared'
 assert stable['realImpulseDisplacementMeters']==0
 assert stable['endNativeBinaryVsUninterrupted']['maximumPositionDifferenceMetres']==0
 assert stable['endJSONReconstructionVsUninterrupted']['maximumPositionDifferenceMetres']<=.00001
for i in (26,40):
 high=A[(i,'physical_impulse_positive_control')]
 assert high['status']=='failed'
 assert high['endNativeBinaryVsUninterrupted']['maximumPositionDifferenceMetres']>.01
assert A[(20,'physical_impulse_positive_control')]['status']=='actual_rapier_source_continuation_compared'
assert A[(20,'physical_impulse_positive_control')]['sourceRoomGuard']['outside']==1
assert A[(26,'physical_impulse_positive_control')]['sourceRoomGuard']['outside']==1

# New independently varied impulse magnitudes quantify how far discrepancy
# depends on the impulse/collision outcome, with NO gold-driven tuning.
B={(r['scene'],r['scenario']):r for r in SECOND['rows']}
assert set(B)=={(i,t)for i in (26,40)for t in ('low_impulse','medium_impulse','high_impulse')}
assert SECOND['summary']['completed']==6 and SECOND['summary']['failed']==0
assert SECOND['summary']['nativeWithinHalfMillimetre']==1
assert SECOND['summary']['nativeDivergedOverOneCentimetre']==4
assert SECOND['summary']['nativeBinaryReplayExactContacts']==6
assert SECOND['summary']['sourceRoomStaleAfterPhysicsCount']==1
checkpoints=Counter();kindErrors=Counter()
for row in B.values():
 assert row['status']=='native_future_source_action_divergence_measured'
 assert row['realImpulseDisplacementMeters']>.5
 assert len(row['intermediateNativeDeviation'])==3
 assert [s['tick'] for s in row['intermediateNativeDeviation']]==[30,120,180]
 for state in row['intermediateNativeDeviation']:
  assert state['native']['nativeContactPairIDsIdentical']
  assert state['json']['nativeContactPairIDsIdentical']
  assert state['native']['sourceTextExactlyIdentical']
  assert state['native']['nativeStepCountEqual']
  checkpoints[state['tick']]+=1
  diff=state['worstNativeObject']
  if diff['metres']>.0005:
   kindErrors[diff['kind']]+=1
assert checkpoints==Counter({30:6,120:6,180:6})
assert SECOND['summary']['nativeBinaryMaxPositionDifferenceMetres']==.2177102
assert SECOND['summary']['legacyJSONMaxPositionDifferenceMetres']==.6587755
assert FIRST['summary']['legacyJSONMaxPositionDifferenceMetres']==.6587755
def round_(v):return round(float(v),6)
initial_medians=statistics.median([row['elapsedMs'] for row in FIRST['rows']])
diagnostic_medians=statistics.median([row['elapsedMs'] for row in SECOND['rows']])
m={
 'previousRound9NativeFrozenSourceScenes':3,
 'previousRound9NativeRigidBodiesReproduced':65,
 'previousOriginalHumanSourceQualifiedObjects':17,
 'newNoActionNativeControlsExact':3,
 'newPositiveStrongImpulseScenarios':3,
 'newStrongImpulseNativeReplayNotExact':2,
 'newImpulseMagnitudeFollowupCases':6,
 'lowMediumHighNewImpulseReplayDiscrepancyAbove1cm':4,
 'newImpulseMagnitudeNativePerfectSubMillimeterCases':1,
 'nativeBinaryMaxAfterFutureActionDifferenceMetres':.2177102,
 'jsonReconstructionMaxAfterFutureActionDifferenceMetres':.6587755,
 'initialNativeRestoresExactIncludingOriginalContactIDs':12,
 'initialJSONRestoresWithMatchingContactIDs':0,
 'postContinuationNativeContactPairIDsMatched':12,
 'newPhysicalRoomFactsBecameStaleAcrossV1V2':3,
 'newHighEnergyRoomDescriptionStaleCases':sum(r['sourceRoomGuard']['outside']>0 for r in
    [A[(20,'physical_impulse_positive_control')],A[(26,'physical_impulse_positive_control')]]),
 'newSourcePhysicsMeanCPUOrGPUTimeUnmeasured':True,
 'round11Initial6ScenarioMeasuredElapsedWallSeconds':FIRST['summary']['elapsedSeconds'],
 'round11New6ScenarioMeasuredElapsedWallSeconds':SECOND['summary']['elapsedSeconds'],
 'round11InitialMedianPerScenarioWallMilliseconds':round_(initial_medians),
 'round11AmplitudeMedianPerScenarioWallMilliseconds':round_(diagnostic_medians),
 'realNativeSceneGeometrySourceCertified':False,
 'independentHumanPostEventObserverTextGoldAvailable':False,
 'fullLiteraryWorldsVerified':0,
 'sourceRoomProvenancePredicateCanFailClosedAfterRealNativeMotion':True,
 'v1V2NotPristineHeldoutNorPopulationUncertaintyEstimate':True
}
safe={'metadata':{
 'round9FrozenSourceOnlyManifestSHA256':hashpath(SOURCE),
 'round9ActualAuthoritativeNativeWorldReceiptSHA256':hashpath(PRIOR),
 'humanIndependentOriginalSourceSHA256':hashpath(HUMAN),
 'round11InitialActualNativeContinuationSHA256':hashpath(INITIAL),
 'round11IndependentImpulseMagnitudePhysicalEvidenceSHA256':hashpath(AMPLITUDE),
 'originalAuthorHumanGoldNotConsultedByNativePhysics':True,
 'deniedFeasibleParentPlaceboNeverAttempted':True,
 'blockedBroadObserverOffscreenCycleNeverAttempted':True,
 'allActualGameCoreAndRapierSourceSystemsUnchanged':True,
 'futureIdenticalPhysicsIsNotProvenByImmediateNativeSnapshot':True,
 'noBenchmarkWideRateOrUnbiasedCIFrom3KnownHumanScenes':True
 },'summary':m,'firstRoundCases':[{
  'scene':r['scene'],'scenario':r['scenario'],'status':r['status'],
  'nativeFinalPositionDifferenceM':r['endNativeBinaryVsUninterrupted']['maximumPositionDifferenceMetres'],
  'legacyJSONFinalPositionDifferenceM':r['endJSONReconstructionVsUninterrupted']['maximumPositionDifferenceMetres'],
  'sourceRoomStateNoLongerMatchesTrueNativePosition':r['sourceRoomGuard']['outside']>0}
  for r in FIRST['rows']],
 'newImpulseStrengthCases':[{
  'scene':r['scene'],'impulseStrength':r['scenario'],'nativeReplayDifferenceM':
   r['endNativeBinaryVsUninterrupted']['maximumPositionDifferenceMetres'],
  'legacyJSONReplayDifferenceM':r['endJSONReconstructionVsUninterrupted']['maximumPositionDifferenceMetres'],
  'nativeContactIDsStillMatch':r['endNativeBinaryVsUninterrupted']['nativeContactPairIDsIdentical'],
  'first30TickNativeDeviationM':r['intermediateNativeDeviation'][0]['native']['maximumPositionDifferenceMetres'],
  'sourceRoomNoLongerPhysicallyVerified':r['sourceRoomGuard']['outside']>0}
  for r in SECOND['rows']]}
out=HERE/'prse_round11_native_postsave_replay_and_room_guard_aggregate_v1.json'
if '--write-once' in sys.argv:
 with out.open('x') as f:json.dump(safe,f,indent=2);f.write('\n')
if out.exists():
 assert read(out)==safe,'Versioned public aggregate diverges from independently verified private raw'
print('VERIFIED new isolated native GameCore/Rapier sourced saved-state continuation:')
print('All 65 previous native bodies/true contact pairs reproducibly rebuilt across three previously known author worlds.')
print('3 no-action trusted binary restore/control worlds exactly match later uninterrupted motion, 3/3.')
print('2/3 high impulses differ up to .218 m despite exact initial restoration and unchanged contact IDs.')
print('6 additional same-source impulse magnitude tests: 4 exceed 1 cm native continuation discrepancy.')
print('All 12 native binary initial contact pairs match; no initial structured JSON contact sets match.')
print('Original room descriptions become stale for physical objects that leave their assigned real 3D region.')
print('Source-only verified rooms are provisional; zero full literary scene and zero human observer-prose success.')
print('No previously denied placebo or blocked observer experiment was executed.')
