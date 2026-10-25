#!/usr/bin/env python3
"""Independently verify repaired historical-vs-current PRSE observer protocol on
originally failed and additional fixed externally sourced native 3D scenes.

Do not confuse:
- A TRUE historical witnessed TIPPED event with a FALSE claim that the body
  is presently tipped after a later genuine RIGHTED event.
- The original ten FAILED research assertions in version one with ten native
  physics failures. Preserve original raw file and exact SHA.
- Forty source rooms from a previously exposed SceneEval-500 corpus with a
  fresh independently annotated literary-scene benchmark. This is a distinct
  observer regression/control sample, not unseen general literature.

Every experiment already took place. This script only READS raw owner-private
source/physical/observer evidence and freezes public-safe numerical evidence.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
from collections import Counter
import json,csv,zipfile,io
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
SOURCES=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
def read(p):return json.loads(p.read_text())
def digest(p):return sha256(p.read_bytes()).hexdigest()
assert digest(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:labelRows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
proposals=read(SOURCES)['proposalsAll500']
assert len(proposals)==len(labelRows)==500
assert S_IMODE(P.stat().st_mode)==0o700
manifest={}
def ownerRaw(name):
 p=P/name
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600
 manifest[name]={'sha256':digest(p),'bytes':p.stat().st_size,'ownerPrivate':True}
 return read(p)

legacy=ownerRaw('prse_native_tipped_event_vs_orientation_256_raw_v1.json')
corrected=ownerRaw('prse_native_tipped_event_vs_orientation_256_raw_v2.json')
assert len(legacy['rows'])==len(corrected['rows'])==256
assert legacy['summary']['emittedHistoricalTippedEvents']==173
assert legacy['summary']['eventsWhereNativeBodyNotActuallyTiltedPastOriginalThreshold']==82
assert legacy['summary']['currentSemanticTippedButNativeBodyUprightAtEnd']==11
assert corrected['summary']['emittedHistoricalTippedEvents']==178
assert corrected['summary']['eventsWhereNativeBodyNotActuallyTiltedPastOriginalThreshold']==0
assert corrected['summary']['currentSemanticTippedButNativeBodyUprightAtEnd']==0
distinctCorrected=[]
badPairs=set()
for first,next_ in zip(legacy['rows'],corrected['rows']):
 assert (first['sourceId'],first['action'])==(next_['sourceId'],next_['action'])
 if first['semanticTippedButCurrentlyUprightAtEnd']:
  badPairs.add((first['sourceId'],first['action']))
 old={x['id']:x for x in first['finalBodyPositions']}
 new={x['id']:x for x in next_['finalBodyPositions']}
 assert set(old)==set(new)
 for name in old:
  assert old[name]['nativeUpTiltRadians']==new[name]['nativeUpTiltRadians']
  assert old[name]['nativeTotalRotationRadians']==new[name]['nativeTotalRotationRadians']
  if bool(old[name].get('semanticStickyTipped')) != bool(new[name].get('semanticStickyTipped')):
   assert old[name].get('semanticStickyTipped') and not new[name].get('semanticStickyTipped')
   assert old[name]['nativeUpTiltRadians']<.12
   distinctCorrected.append(name)
assert len(badPairs)==len(distinctCorrected)==11

wrongResearchTest=ownerRaw('prse_corrected_righted_event_observer_delivery_11_raw_v1.json')
proper=ownerRaw('prse_corrected_righted_event_observer_delivery_11_raw_v2.json')
a=wrongResearchTest['summary'];b=proper['summary']
assert a['existingKnownBadSourceConditions']==b['existingKnownBadSourceConditions']==11
assert a['actualGameCoreNativeSourceActionsVerified']==1 and a['testFailures']==10
assert b['actualGameCoreNativeSourceActionsVerified']==11 and b['testFailures']==0
assert b['witnessedRealNativeRightedEventsViaPhysicalEventTimeRay']==13
assert b['actualEventTimeTippingWitnesses']==13
assert b['unseenEventLeaksToDistantObserver']==0
assert b['sourceCurrentTextFalseTipped']==0
assert b['sourcePrivateOriginalsRestored']==11
assert b['nativeFinalPoseDivergencesWithAttachedObserver']==0
assert b['previouslyWitnessedEventsRepeatedAfterNativeSave']==0
assert {(x['sourceId'],x['action']) for x in proper['rows']}==badPairs
for old,new in zip(wrongResearchTest['rows'],proper['rows']):
 assert old['sourceId']==new['sourceId'] and old['action']==new['action']
 assert new['status']=='evaluated'
 assert new['sourceCurrentStillUpright'] and new['currentSemanticTextNoFalseTipped']
 assert new['witnessedTippings']>=0 and new['witnessedRightings']>=0
 assert new['historicalGenuinelyWitnessedTippingIsNotCurrentState']==new['witnessedTippings']
 assert not new['observerMayHaveAlteredPhysicalTrajectory']
 assert new['originalSourceTextPreserved'] and new['originalNativeBodyIdentity']
 assert new['duplicateHistoricalEvents']==0
# Both versions' printed summary SHA matches exact owner-private raw bytes.
for v,private in [('v1',wrongResearchTest),('v2',proper)]:
 file=R/f'prse_corrected_righted_witness_11_aggregate_{v}.json'
 pub=read(file)
 assert pub['metadata']['privateRawSHA256']==manifest[
  f'prse_corrected_righted_event_observer_delivery_11_raw_{v}.json']['sha256']
 assert pub['summary']==private['summary']

typed=ownerRaw('prse_corrected_righted_event_observer_delivery_11_raw_v3.json')
typed11=typed['summary']
assert typed11['historyAndCurrentFactChannelsLosslessInOriginalWrongCases']==11
assert typed11['witnessedRealNativeRightedEventsViaPhysicalEventTimeRay']==13
assert typed11['actualEventTimeTippingWitnesses']==13
assert typed11['actualGameCoreNativeSourceActionsVerified']==11
assert typed11['nativeFinalPoseDivergencesWithAttachedObserver']==0
for old,newer in zip(proper['rows'],typed['rows']):
 assert (old['sourceId'],old['action'])==(newer['sourceId'],newer['action'])
 assert newer['status']=='evaluated' and newer['historyCurrentPartitionLossless']
 assert old['witnessedTippings']==newer['witnessedTippings']
 assert old['witnessedRightings']==newer['witnessedRightings']
 assert old['sourceCurrentStillUpright']==newer['sourceCurrentStillUpright']
pub=read(R/'prse_corrected_righted_witness_11_aggregate_v3.json')
assert pub['summary']==typed11
assert pub['metadata']['privateRawSHA256']==manifest['prse_corrected_righted_event_observer_delivery_11_raw_v3.json']['sha256']

new=ownerRaw('prse_event_and_current_channels_40_raw_v1.json')
s=new['summary']
assert s['frozenDistinctNonRegressionSourceScenes']==40
assert s['actualGameCoreSourceSceneActionsVerified']==40
assert s['scientificFailures']==0
assert s['nativeTypedTippedEvents']==29
assert s['nativeTypedRightedEvents']==0
assert s['actuallyRayWitnessedPhysicalEvents']==118
assert s['actuallyRayWitnessedTippedEvents']==26
assert s['actuallyRayWitnessedRightedEvents']==0
assert s['nativeEventTimeRotationContradictions']==0
assert s['currentlyVisibleObjectFactsIndependentlyChecked']==37
assert s['currentlyVisibleTippedFactsContradictNativeUpAxis']==0
assert s['unseenEventsLeakedToDistantObserver']==0
assert s['duplicateWitnessEventsAfterSave']==0
assert s['originalSourceAndGameCoreNativeWorldPreservedAfterSave']==40
assert s['firstRaySightAvailable']==40
pub=read(R/'prse_event_current_observer_new_40_aggregate_v1.json')
assert pub['summary']==s
assert pub['metadata']['privateRawSHA256']==manifest['prse_event_and_current_channels_40_raw_v1.json']['sha256']
allowedSceneIDs=set(list(range(100))+list(range(100,500,4)))
assert len(new['rows'])==40
assert [r['sourceId'] for r in new['rows']]==sorted(set(r['sourceId'] for r in new['rows']))
actions=['east_up','west_up','south_up','north_low']
for row in new['rows']:
 i=row['sourceId']
 assert i in allowedSceneIDs and (i,row['action']) not in badPairs
 assert row['action']==actions[i%4]
 assert row['status']=='native_source_event_observer_verified'
 assert labelRows[i]['Description']==proposals[i]['text'] and labelRows[i]['ID']==str(i)
 assert row['witnessedEventProvenanceValid'] and row['fullNativeWorldOriginalSourceAndIDsRestored']
 assert row['nativeEventInvalidAtEventTime']==row['nearCurrentClaimsDisagreeWithNativeTilt']==0
 assert row['farWitnessedEvents']==row['repeatedEventDelivery']==0
 assert row['nearWitnessedTipped']<=row['nativeTippedEvents']
typed40=ownerRaw('prse_event_and_current_channels_40_raw_v2.json')
typed40Summary=typed40['summary']
assert typed40Summary['nativeHistoricalEventsAndCurrentWorldFactChannelsExactlyPartitioned']==40
assert typed40Summary['historicalEventSentencesOutput']==118
assert typed40Summary['currentFactSentencesOutput']==37
assert typed40Summary['scientificFailures']==0
assert typed40Summary['actuallyRayWitnessedTippedEvents']==26
assert typed40Summary['currentlyVisibleTippedFactsContradictNativeUpAxis']==0
assert typed40Summary['originalSourceAndGameCoreNativeWorldPreservedAfterSave']==40
for before,after in zip(new['rows'],typed40['rows']):
 assert before['sourceId']==after['sourceId'] and before['action']==after['action']
 assert before['status']==after['status']=='native_source_event_observer_verified'
 assert after['noLossFromTypedHistoricalEventCurrentFactPartition']
 for k in ['nearWitnessedEventCount','nearWitnessedTipped','nearWitnessedRighted',
  'nativeTippedEvents','nativeRightedEvents','nearCurrentObjectsChecked',
  'farWitnessedEvents','repeatedEventDelivery']:
  if k in before:assert before[k]==after[k],(k,before['sourceId'])
pub=read(R/'prse_event_current_observer_new_40_aggregate_v2.json')
assert pub['summary']==typed40Summary
assert pub['metadata']['privateRawSHA256']==manifest['prse_event_and_current_channels_40_raw_v2.json']['sha256']

# Corroborate overarching independent author-gold failures were NOT erased.
goldCounts=read(R/'prse_source_quantity_official_gold_200_aggregate_v1.json')['combined']
goldRelations=read(R/'prse_pre_layout_source_role_gold_200_aggregate_v1.json')['counter']
assert goldCounts['goldCountClauses']==1237
assert goldCounts['goldCountSatisfiedByPhysicalWorld']==565
assert goldRelations['authorOnClauses']==354
assert goldRelations['authorOnPhysicallyConfirmedBaseline']==3
out={'metadata':{
 'originalExternalCorpusSHA256':digest(GOLD),
 'frozenSourceProposalSHA256':digest(SOURCES),
 'sameOriginalPhysicalInputs':True,
 'correction':'Real Rapier upright axis for tipped/righted + separate witnessed event history and current physical state',
 'priorInvalidResearchCheckPreserved':'One version mixed witnessed historical event strings with current physical-state assertions; no claim those ten invalid tests indicate physics failures',
 'newControl':'Forty different previously available source scenes, chosen by fixed source IDs and deterministic action direction, not by observed success',
 'sourceMeaningWarning':'Official author object-count and spatial gold remain largely unmatched; source scene prose fluency/LLM intent not tested',
 'noGoldModelTuningOrGPUUse':True},
 'firstMeasuredEventAccuracy':legacy['summary'],
 'correctedPhysicalEventAccuracy':corrected['summary'],
 'priorElevenBadResearchAssertionOutcome':a,
 'correctedElevenEventCurrentObserverControl':b,
 'additionalFortySceneObserverAndNarrativeControl':s,
 'explicitElevenSceneHistoryCurrentWordPartition':typed11,
 'explicitFortySceneLosslessHistoryCurrentWordPartition':typed40Summary,
 'sourceMeaningNegativeGoldChecks':{
  'authorObjectCountClauses':1237,
  'actual3DObjectCountClausesSatisfied':565,
  'authorOnRelationClauses':354,
  'actuallyContactSupportedAuthorOnRelations':3},
 'ownerPrivateRawEvidenceManifest':manifest}
name=R/'prse_native_event_current_observer_evidence_manifest_v2.json'
if name.exists():assert read(name)==out,'Source evidence conflict; do not rewrite consumed result'
else:
 with name.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED 256 matched native source scene interventions: 82 previously false tipping events corrected to zero without changing actual Rapier orientations.')
print('VERIFIED original flawed observer research assertion 1/11, corrected historical/current source channel 11/11 with 13 true tips +13 true rightings witnessed, zero remote leaks.')
print('VERIFIED 40 fixed different source rooms: 29 true physics tips, 26 genuinely event-time witnessed, 118 actual native witnessed events total, zero false current orientation statements and 40/40 source/world/observer saves.')
print('VERIFIED explicit HISTORICAL EVENT and CURRENT PHYSICAL STATE word channels losslessly reconstruct legacy combined text in all 11 known-source and 40 other fixed-source controls.')
print('VERIFIED independent author source count/ON-negative controls unchanged, with owner-private raw files mode600 and exact SHA.')
