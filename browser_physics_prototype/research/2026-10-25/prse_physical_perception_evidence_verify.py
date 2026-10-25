#!/usr/bin/env python3
"""Independently audit PRSE's physical occlusion / witness-at-event results.

This compares two physically identical frozen SceneEval samples: first with
visibility checked one step AFTER the impulse, then at the precise emission
instant. Raw external source-derived cases are owner-private; only aggregates,
case IDs and hashes are published. No gold meaning labels are used.
"""
import hashlib,json,stat
from pathlib import Path
ROOT=Path(__file__).parent
RAW=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
source=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
assert digest(source)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
distance=read(ROOT/'prse_occlusion_200_aggregate_v1.json')
visual=read(RAW/'prse_occlusion_raw_v1.json')
assert digest(RAW/'prse_occlusion_raw_v1.json')==distance['metadata']['rawSHA256']
parts={x['part']:x for x in distance['groups']}
assert len(visual['groups'])==2
assert parts['human']['physicallyAccepted']==97
assert parts['assisted']['physicallyAccepted']==99
assert parts['human']['blockedAsOccluded']==75
assert parts['assisted']['blockedAsOccluded']==67
assert sum(x['distanceVisibleObjectObservations'] for x in parts.values())==2917
assert sum(x['blockedAsOccluded'] for x in parts.values())==142
for part in ('human','assisted'):
 summary=parts[part]
 assert summary['rayConfirmedVisibleObjectObservations']+summary['blockedAsOccluded']==summary['distanceVisibleObjectObservations']
 assert summary['blockedByFurniture']+summary['blockedByRoomWall']+summary['blockedByOtherCoreCollider']==summary['blockedAsOccluded']
 assert summary['failures']==0

oldfile=RAW/'prse_observer_event_batch_200_raw_v1.json'
newfile=RAW/'prse_observer_event_batch_200_raw_v2.json'
old,new=read(oldfile),read(newfile)
m1=read(ROOT/'prse_observer_event_batch_200_aggregate_v1.json')
m2=read(ROOT/'prse_observer_event_batch_200_aggregate_v2.json')
assert digest(oldfile)==m1['metadata']['rawSHA256']
assert digest(newfile)==m2['metadata']['rawSHA256']
assert len(old['rows'])==len(new['rows'])==200
for a,b in zip(old['rows'],new['rows']):
 assert (a['id'],a['sourceType'],a['status'],a['chosenCategory'] if 'chosenCategory' in a else None,
         a['hasOccludedContrast'] if 'hasOccludedContrast' in a else None)==(
          b['id'],b['sourceType'],b['status'],b.get('chosenCategory'),b.get('hasOccludedContrast'))
 assert a['validScenes']==b['validScenes'] and a['dynamicBodies']==b['dynamicBodies']
for result in (old,new):
 assert result['aggregate']['evaluated']==63
 assert result['aggregate']['runtimeFailures']==0
 assert result['aggregate']['withOccludedContrast']==17
 assert result['aggregate']['stableSourceProse']==63
 assert result['aggregate']['repeatedAfterSave']==0
assert old['aggregate']['delayedPhysicsWitnessDelivered']==62
assert old['aggregate']['occludedCauseWronglyDelivered']==1
assert new['aggregate']['delayedPhysicsWitnessDelivered']==63
assert new['aggregate']['occludedCauseWronglyDelivered']==0
corrected=read(ROOT/'prse_event_emission_timing_fix_v2.json')
assert [x['id'] for x in corrected['results']]==[27,29]
assert all(x['atEmitterCapture']['visible']==1 and x['atEmitterCapture']['blocked']==0
           and x['persistedVisibleDelivered'] and x['persistedOccludedSuppressed']
           and x['subscriberErrors']==0 for x in corrected['results'])
late=read(ROOT/'prse_observer_delayed_witness_v2.json')
assert late['comparison']['withoutTickCaptureWitnessedEvents']==0
assert late['comparison']['savedAndDelayedDelivered']==1
assert late['comparison']['hiddenObserverNoRetroactiveCause']
remote=read(ROOT/'prse_observer_offscreen_remnant_reentry_v1.json')
assert remote['perception']['previouslyUnseenCausesRevealed']==0
assert remote['perception']['duplicateFactOnNextPoll']==0
for path in (oldfile,newfile,RAW/'prse_occlusion_raw_v1.json'):
 assert stat.S_IMODE(path.stat().st_mode)==0o600, 'Private artifact must not be world-readable'
out={
 'provenance':{
  'source':'SceneEval-500_v250610 source ZIP via author-provided GitHub release',
  'externalSourceSHA256':digest(source),
  'rawOwnerPrivateFiles':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in
    (oldfile,newfile,RAW/'prse_occlusion_raw_v1.json')},
  'caveat':'Physically observed with sampled shape rays, not human visual judgments, original room geometry remains approximate'},
 'geometry':{
   'sourceScenes':200,'validatedPhysicalScenes':196,'viewpointsPerScene':5,
   'distanceEligibleObjectObservations':2917,'blockedByActualRapierCollider':142,
   'oldDistanceOnlyOccludedFraction':142/2917,
   'humanSampleOccluded':parts['human']['blockedAsOccluded'],
   'assistedSampleOccluded':parts['assisted']['blockedAsOccluded']},
 'eventTime':{
   'physicalScenesWithSelectedDynamicBody':63,
   'withOccludedContrast':17,
   'priorPostStepCapture':{
    'witnessedAndDelivered':62,'wronglyDeliveringOccludedCause':1,'repeatAfterReload':0},
   'correctedEmissionTimeCapture':{
    'witnessedAndDelivered':63,'wronglyDeliveringOccludedCause':0,'repeatAfterReload':0},
   'previousFailureSceneIDsCorrected':[27,29],
   'observerDeliveryAndWorldSnapshotsTested':True},
 'offscreen':{
  'realAshColliderOnReturn':remote['simulation']['ashColliderCount']==1,
  'unseenOffscreenIgnitionNotRevealed':True,
  'destroyedOriginalIDPreserved':remote['simulation']['stableNoteId'],
  'sourceLiteraryDescriptionPreserved':remote['simulation']['originalSourceIntact']}
}
dest=ROOT/'prse_physical_perception_evidence_aggregate_v1.json'
if dest.exists():
    assert read(dest)==out, 'Existing aggregate differs from independently verified sources; refusing overwrite'
else:
    with dest.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED',out['geometry'],out['eventTime'],out['offscreen'])
