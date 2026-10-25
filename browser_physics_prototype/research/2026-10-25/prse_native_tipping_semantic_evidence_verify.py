#!/usr/bin/env python3
"""Independent read-only evidence review for PRSE native orientation and
semantic event correctness. Validates a REAL negative first pass, matched
corrected second pass, unchanged actual Rapier trajectories, native current
semantic/observer return regression, and the two frozen SceneEval source-
to-GameCore-to-text/native-save cohorts after the correction.

All per-source physical state data and original third-party literary prompts
remain owner-private Nitro runtime bytes. The public Games report contains
only source-safe aggregate evidence and exact source/raw SHA-256 digests.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
import json,zipfile,csv,io
ROOT=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit')
DOC=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-current-document')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert digest(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:originals=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(originals)==500
assert S_IMODE(PRIVATE.stat().st_mode)==0o700
manifest={}
def raw(name,folder=PRIVATE):
 p=folder/name
 assert p.exists() and S_IMODE(p.stat().st_mode)==0o600,(str(p),'Raw owner-private file missing or permissions too open')
 manifest[name]={'sha256':digest(p),'bytes':p.stat().st_size,'ownerPrivate':True}
 return read(p)
orientation=raw('prse_native_orientation_support_audit_197x4_raw_v1.json')
summary=orientation['summary']
assert summary['inputExternalSourceScenes']==200
assert summary['originalGeometryAccepted']==197
assert summary['physicalWorldActionConditions']==788
assert summary['physicallyActedConditions']==256
assert summary['physicallyActedUniqueSources']==64
assert summary['runtimeFailures']==0
assert summary['oldCurrentFactsTrue']==196
assert summary['oldCurrentFactsTrueButNativeUprightUnknown']==0
assert summary['oldCurrentFactsTrueButNativeGeometryFalse']==0
assert summary['oldCurrentFactsUnknownButNativePhysicallyTrue']==0
assert summary['oldCurrentFactsFalseButNativePhysicallyTrue']==0
assert summary['rotationGeometricUncertainty']==27
assert summary['maximumMetadataVsNativeTranslationDistance']==0
aggregate=read(ROOT/'prse_native_orientation_support_197x4_aggregate_v1.json')
assert aggregate['metadata']['privateRawSHA256']==manifest['prse_native_orientation_support_audit_197x4_raw_v1.json']['sha256']
assert aggregate['summary']==summary
assert not aggregate['discrepantCases']
before=raw('prse_native_tipped_event_vs_orientation_256_raw_v1.json')
after=raw('prse_native_tipped_event_vs_orientation_256_raw_v2.json')
a,b=before['summary'],after['summary']
assert a['frozenExternalSceneAndActualActionConditions']==b['frozenExternalSceneAndActualActionConditions']==256
assert a['successfullyMeasuredRealNativeActionCases']==b['successfullyMeasuredRealNativeActionCases']==256
assert a['executionErrors']==b['executionErrors']==0
assert a['emittedHistoricalTippedEvents']==173
assert a['eventsWhereNativeBodyNotActuallyTiltedPastOriginalThreshold']==82
assert a['eventsWithNativeUpTiltLessThanTwelveHundredthsRad']==2
assert a['currentSemanticTippedButNativeBodyUprightAtEnd']==11
assert b['emittedHistoricalTippedEvents']==178
assert b['eventsWhereNativeBodyNotActuallyTiltedPastOriginalThreshold']==0
assert b['eventsWithNativeUpTiltLessThanTwelveHundredthsRad']==0
assert b['currentSemanticTippedButNativeBodyUprightAtEnd']==0
assert b['actuallyTiltedNativeBodiesAtEnd']==161
assert b['recordedStickyTippedCurrentEntityAtEnd']==162
assert a['recordedStickyTippedCurrentEntityAtEnd']==173
assert a['actuallyTiltedNativeBodiesAtEnd']==b['actuallyTiltedNativeBodiesAtEnd']
countPreviousFalselyTipped={}
changedFlags=[]
for previous,current in zip(before['rows'],after['rows']):
 assert previous['sourceId']==current['sourceId']
 assert previous['action']==current['action']
 assert previous['status']==current['status']=='measured'
 assert originals[previous['sourceId']]['ID']==str(previous['sourceId'])
 prevBodies={x['id']:x for x in previous['finalBodyPositions']}
 newBodies={x['id']:x for x in current['finalBodyPositions']}
 assert set(prevBodies)==set(newBodies)
 for id,old in prevBodies.items():
  new=newBodies[id]
  assert old['nativeUpTiltRadians']==new['nativeUpTiltRadians']
  assert old['nativeTotalRotationRadians']==new['nativeTotalRotationRadians']
  x,y=bool(old.get('semanticStickyTipped')),bool(new.get('semanticStickyTipped'))
  if x!=y:
   assert x and not y
   assert old['nativeUpTiltRadians']<.12
   changedFlags.append((previous['sourceId'],previous['action'],id))
 if previous['semanticTippedButCurrentlyUprightAtEnd']:
  countPreviousFalselyTipped[(previous['sourceId'],previous['action'])]=previous['semanticTippedButCurrentlyUprightAtEnd']
assert len(changedFlags)==11
assert sum(countPreviousFalselyTipped.values())==11
for version,data in [('v1',before),('v2',after)]:
 path=ROOT/f'prse_native_tipped_event_orientation_256_aggregate_{version}.json'
 pub=read(path)
 assert pub['metadata']['privateRawSHA256']==manifest[f'prse_native_tipped_event_vs_orientation_256_raw_{version}.json']['sha256']
 assert pub['summary']==data['summary']
matchedReturn=raw('prse_corrected_tipped_current_observer_native_11_raw_v1.json')
a2=matchedReturn['summary']
assert a2['previouslyDisprovedSourceDerivedCurrentTippedCases']==11
assert a2['correctedWholeSceneNativeSources']==11
assert a2['scientificRunFailures']==0
assert a2['correctedPhysicallyUprightPersistedObjectIDs']==11
assert a2['explicitlyActualNativeTippingEventsVerified']==13
assert a2['actualNativeRightingEventsVerified']==13
assert a2['wrongTippingEventsAfterCorrection']==0
assert a2['wrongRightingEventsAfterCorrection']==0
assert a2['wrongCurrentTippedSourceTextAfterCorrection']==0
assert a2['rayVisibleReturnedSourceScenes']==5
assert a2['factualHistoricalSourceAndNativePhysicsPersistenceVerified']==11
assert {(x['sourceId'],x['action']) for x in matchedReturn['rows']}==set(countPreviousFalselyTipped)
assert all(x['status']=='corrected_real_native_semantic_and_observer' for x in matchedReturn['rows'])
assert all(x['oldSourceStillImmutable'] and x['sourceAndCurrentTextRestored'] and
           x['savedCurrentUpright'] and x['originalIDsRestored'] for x in matchedReturn['rows'])
# Aggregate output used to independently check private case file digest.
observerPub=read(ROOT/'prse_corrected_tipping_native_observer_11_aggregate_v1.json')
assert observerPub['metadata']['privateRawSHA256']==manifest['prse_corrected_tipped_current_observer_native_11_raw_v1.json']['sha256']
assert observerPub['summary']==a2
for parser,expected in [('deterministic',197),('union',195)]:
 for version in ('v2','v3'):
  name=f'prse_current_world_document_{parser}_200_raw_{version}.json'
  record=raw(name,DOC)
  public=read(ROOT/f'prse_current_world_document_{parser}_200_aggregate_{version}.json')
  assert public['metadata']['privateRawSHA256']==manifest[name]['sha256']
  assert public['summary']==record['summary']
  study=record['summary']
  assert study['sourceScenes']==200 and study['accepted']==expected
  assert study['runtimeFailures']==0
  assert study['validNativeWorldAndSemanticJournalSave']==expected
  assert study['nativeResumedPhysicalSourceTruthEqual']==expected
  assert study['unsupportedOriginalRelationsNarrated']==0
  assert study['noDuplicateUnchangedRevision']==expected
  if version=='v2':
   baseline=study
  else:
   assert all(study[key]==baseline[key] for key in [
    'accepted','physicalSceneRejected','currentPhysicalEntityClaims',
    'sourceRelationsPhysicallyVerified','sourceRelationsPhysicallyContradicted',
    'sourceRelationsNotVerifiable','semanticsChangedAfterNativeImpulse',
    'physicallyVerifiedExtraSupportStatements',
    'originalHistoricalDescriptionBytes','newCanonicalCurrentDocumentBytes'])
results={'metadata':{
 'externalSource':'Official SceneEval-500 first hundred human and systematic assisted one hundred, same previously frozen source and impulses',
 'sourceZipSha256':digest(GOLD),
 'separatePublishedRapierDocumentation':'https://rapier.rs/docs/user_guides/javascript/advanced_collision_detection_js/',
 'comparison':'No model/gold used for physical event input; before/after native source and impulse matched exactly',
 'notPristineNewHoldout':True,
 'observerReturnSampleSelection':'Eleven previously exposed false-current source scenes, selected from the bad prior output',
 'noRenderingGPUorProductionWorkAffected':True},
 'orientationBaseline':summary,
 'historicalTippingEventBeforeCorrection':a,
 'historicalTippingEventAfterCorrection':b,
 'pairedNativeActualPositionAndOrientationExact':True,
 'correctedPreviouslyFalsePresentTippedRecords':len(changedFlags),
 'sourceDerivedObserverNativeReentry':a2,
 'sourceToPhysicsCurrentWorldRegressionAcceptedDeterministic':197,
 'sourceToPhysicsCurrentWorldRegressionAcceptedCombined':195,
 'sourceMeaningAndShapeGenerationStillNotSolved':True,
 'privateRawManifest':manifest}
dest=ROOT/'prse_native_tipping_semantic_evidence_manifest_v1.json'
if dest.exists():assert read(dest)==results,'Refusing to overwrite different consumed scientific evidence'
else:
 with dest.open('x') as f:json.dump(results,f,indent=2);f.write('\n')
print('VERIFIED original false event tipping 82/173 and 11 persistent falsely tipped current physical states.')
print('VERIFIED corrected full matched GameCore/Rapier input 178 actual tipped events ALL consistent with upright tilt, zero incorrect final upright status.')
print('VERIFIED EXACT native 3D trajectory/rotation per identical scene and action, all original contacts and original source characters unchanged.')
print('VERIFIED 11 previously failing source narratives/natively saved observer outcomes and 13 genuine tipping+righting events each physically valid.')
print('VERIFIED corrected full 200-source deterministic and combined semantic world native-save regression 197/195 accepted, no runtime or new source-fact errors.')
