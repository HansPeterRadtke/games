#!/usr/bin/env python3
"""READ-ONLY actual native GameCore/Rapier source-room-fact roundtrip verifier.

Never reruns the previously blocked general observer/offscreen study or denied
random-parent placebo. Does not create more physical worlds. Tests saved
input -> frozen source-only manifest -> NEW actual GameCore/Rapier physical
materialization -> native save/restored actual bodies -> bounded factual text
and independent official human-authored constraints.

Negative controls are deterministic *read-only clones* of frozen physical
records: wrong room tags/poses must be rejected as unsupported source truth.
No physics scene is mutated and no original generated evidence overwritten.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
from stat import S_IMODE
import json,math,re,copy
HERE=Path(__file__).resolve().parent
PRIV=Path('/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round9-room-contract')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
SOURCE=BASE/'lego_full_data_public_human_gold.json'
FROZEN=PRIV/'source_original_strict_room_proposal_frozen_v3.json'
PHYS=PRIV/'room_source_to_native_to_factual_text_v3_raw_v2.json'
HUMAN=PRIV/'actual_saved_native_source_vs_independent_human_constraints_v1.json'
SAFE1=HERE/'prse_round9_actual_native_author_room_source_roundtrip_aggregate_v2.json'
SAFE2=HERE/'prse_round9_native_human_source_room_semantic_score_aggregate_v1.json'
OLD=BASE/'lego_source_only_matched_native_130_raw_v1.json'
assert S_IMODE(PRIV.stat().st_mode)==0o700
assert all(p.exists() and S_IMODE(p.stat().st_mode)==0o600
 for p in (SOURCE,FROZEN,PHYS,HUMAN,OLD))
source=load(SOURCE)
manifest=load(FROZEN);physical=load(PHYS);human=load(HUMAN)
safe1=load(SAFE1);safe2=load(SAFE2)
assert manifest['metadata']['humanOfficialLabelsAndReferenceRoomsNeverReadBySourceProposals']
assert physical['metadata']['goldLabelsNeverReadInGeneration']
assert physical['metadata']['sourceOnlyManifestSHA256']==digest(FROZEN)
assert human['metadata']['actualNewNativeRapierSaveToFactualWorldReportSHA256']==digest(PHYS)
assert human['metadata']['frozenSourceOnlyManifestSHA256']==digest(FROZEN)
assert human['metadata']['humanGoldOfficialSHA256']==digest(SOURCE)
assert safe1['metadata']['privateRawSHA256']==digest(PHYS)
assert safe2['metadata']['privateHumanGoldScorerSHA256']==digest(HUMAN)
assert safe2['metadata']['frozenActualGameCoreRapierNativeSaveSHA256']==digest(PHYS)
assert len(manifest['cases'])==len(physical['cases'])==len(human['rows'])==3
assert [x['sceneIndex'] for x in manifest['cases']]==[20,26,40]
assert [x['sceneIndex'] for x in physical['cases']]==[20,26,40]
assert physical['summary']['inputHumanAuthoredSourceScenes']==3
assert physical['summary']['sourcePositiveObjectInstances']==17
assert physical['summary']['sourceNegativeRoomFacts']==4
assert physical['summary']['sourcePositiveKindGroups']==15
assert physical['summary']['originalRooms']==8
assert physical['summary']['casesNativeSuccessful']==3
assert physical['summary']['nativeActualSourceInstances']==17
assert physical['summary']['sourceFactsCorrectAfterNativeSnapshot']==3
assert physical['summary']['casesWithAnyFailures']==0
assert physical['summary']['validFullSourceScenes']==0
assert physical['summary']['independentHumanTargetNarrationValidated']==0
assert physical['summary']['originalBroadObserverCycleNeverRun']
assert physical['summary']['noDeniedRandomParentPlaceboAttempted']
assert human['metrics']['humanLabelMatchedPhysicalInstances']==17
assert human['metrics']['humanLabelMatchedRoomSpecificAbsences']==4
assert human['metrics']['officialHumanConstraintsInTheseScenes']==37
assert human['metrics']['sourceGoldComputerSupportClausesUnfulfilled']==1
assert human['metrics']['sourceGoldRoomAdjacencyClausesViolated']==1
assert human['metrics']['measuredActualPlatformGapCm']==800
assert human['metrics']['observerLiteraryTruthVerified']==0
failures=[]
def check_room_source(entities,proposal):
 kinds=Counter((x['roomId'],x['kind']) for x in entities if x['kind']!='room_floor')
 counts={(p['roomId'],p['kind']):p['count'] for p in proposal['positiveRoomKinds']}
 positives=[(x,kinds[x],n) for x,n in counts.items() if kinds[x]!=n]
 negatives=[(x['roomId'],x['kind']) for x in proposal['explicitNegativeRoomKinds']
            if kinds[(x['roomId'],x['kind'])]>0]
 unexpected=[(kind,n) for kind,n in kinds.items() if kind not in counts]
 # Independently validate actual 3D spatial body positions within claimed
 # source-qualified physical room floor bounds rather than just trusting a
 # string attribute. Room representation itself is provisional.
 floors={room:[x for x in entities if x['roomId']==room and x['kind']=='room_floor']
         for room in proposal['roomNames']}
 spatial=[]
 for x in entities:
  reg=floors[x['roomId']]
  if not reg:spatial.append((x['id'],'unrealized room floor'));continue
  loX=min(y['position']['x']-y['dimensions']['x']/2 for y in reg)
  hiX=max(y['position']['x']+y['dimensions']['x']/2 for y in reg)
  loZ=min(y['position']['z']-y['dimensions']['z']/2 for y in reg)
  hiZ=max(y['position']['z']+y['dimensions']['z']/2 for y in reg)
  if not(loX-.01<=x['position']['x']<=hiX+.01 and
         loZ-.01<=x['position']['z']<=hiZ+.01):
   spatial.append((x['id'],'physically outside declared room'))
 return {'positives':positives,'negatives':negatives,
         'unexpected':unexpected,'spatial':spatial}
samples=Counter()
for plan,state,score in zip(manifest['cases'],physical['cases'],human['rows']):
 i=plan['sceneIndex']
 assert state['sceneIndex']==score['sceneIndex']==i
 assert state['status']=='native_room_positive_negative_subset_saved_and_restored'
 assert state['savedSameRoomQualifiedIDsAndGeometryExact']
 assert state['savedOriginalHumanSourceStillExact']
 assert state['fullLiteraryAuthorSourceAccepted'] is False
 assert not state['originalTextLeakedAsCurrentNarration'] if 'originalTextLeakedAsCurrentNarration' in state else True
 assert source[i]['instruction']==plan['sourceText']
 assert sha256(plan['sourceText'].encode()).hexdigest()==plan['sourceTextSHA256']
 assert state['originalSourceHash']==plan['sourceTextSHA256']
 assert len(plan['roomNames'])==state['restoredActualNativeScene']['physicalPartitionFloorCount']//6
 actual=state['restoredActualNativeScene']
 before=state['beforeSnapshot']
 assert actual['nativeMaterializedAll']==before['nativeMaterializedAll']
 assert len(actual['realNativeBodies'])==len(before['realNativeBodies'])
 assert len(actual['actualNativeInterobjectContacts'])==len(before['actualNativeInterobjectContacts'])
 byId={x['id']:x for x in before['realNativeBodies']}
 assert len(byId)==len(before['realNativeBodies'])
 for e in actual['realNativeBodies']:
  b=byId.get(e['id'])
  assert b and (e['roomId'],e['kind'],e['shape'],e['dimensions'])==(
    b['roomId'],b['kind'],b['shape'],b['dimensions'])
  assert all(abs(e['position'][dim]-b['position'][dim])<.0001 for dim in ('x','y','z'))
  assert not e['geometrySourceCertified'] and e['isRealGameCoreRapierBody']
 assert len(actual['realNativeBodies'])==6*len(plan['roomNames'])+sum(x['count'] for x in plan['positiveRoomKinds'])
 assert len([x for x in actual['realNativeBodies'] if x['kind']=='room_floor'])==6*len(plan['roomNames'])
 assert len([x for x in actual['realNativeBodies'] if x['kind']!='room_floor'])==sum(x['count'] for x in plan['positiveRoomKinds'])
 assert all(x['shape']=='box' for x in actual['realNativeBodies'])
 assert all(max(x['dimensions'].values())<=8 for x in actual['realNativeBodies'])
 assert not any(check_room_source(actual['realNativeBodies'],plan).values())
 for room in plan['roomNames']:
  assert 'In the provisional spatial region called '+room.replace('_',' ')+',' in state['factualRoomTextFromRestoredActualBodies']
 assert state['sourceUnresolvedCount']>0 and not score['fullSourceCorrect']
 for req in plan['positiveRoomKinds']:
  # Author's typed human label, independently supplied, authenticates this
  # narrow sourced clause, not ALL its other physical/material attributes.
  typed=[l for l in source[i]['labels'] if
     sha256(' '.join(l['instructions']).encode()).hexdigest()==req['sourceClauseSHA256']]
  assert typed and any(x['condition_type'] in ('Object Placement','Floor Layout') for x in typed)
 # Actual existing (not simulated) native inter-body contacts are tuples of
 # the SAME saved source-qualified rigid bodies; no fabricated contacts.
 actual_ids=set(byId)
 for contact in actual['actualNativeInterobjectContacts']:
  a,b,num=contact
  assert a in actual_ids and b in actual_ids and a!=b and num>0
 # Read-only exact “wrong room” and “wrong spatial pose” negative controls.
 # NOT the denied random support-parent placebo and NOT a new physics run.
 if i==20:
  bed=next(x for x in actual['realNativeBodies'] if x['roomId']=='kitchen' and x['kind']=='bed')
  fridge=next(x for x in actual['realNativeBodies'] if x['roomId']=='bedroom' and x['kind']=='fridge')
  for original,destination in ((bed,'bedroom'),(fridge,'kitchen')):
   tampered=copy.deepcopy(actual['realNativeBodies'])
   next(x for x in tampered if x['id']==original['id'])['roomId']=destination
   errors=check_room_source(tampered,plan)
   assert errors['negatives'] and (errors['positives'] or errors['spatial'])
   samples['deterministic_wrong_room_tag_refused']+=1
  moved=copy.deepcopy(actual['realNativeBodies'])
  next(x for x in moved if x['id']==bed['id'])['position']['x']+=33
  err=check_room_source(moved,plan)
  assert err['spatial'] and not err['negatives']
  samples['wrong_native_spatial_location_refused']+=1
 if i==40:
  ids={x['id']:x for x in actual['realNativeBodies']}
  desk=[x['id'] for x in actual['realNativeBodies'] if x['roomId']=='guard_control_room' and x['kind']=='desk']
  comps=[x['id'] for x in actual['realNativeBodies'] if x['roomId']=='guard_control_room' and x['kind']=='computer']
  assert len(desk)==1 and len(comps)==2
  contacts={frozenset((a,b)) for a,b,n in actual['actualNativeInterobjectContacts'] if n>0}
  assert all(frozenset((comp,desk[0])) not in contacts for comp in comps)
  samples['source_computers_supported_by_desk_not_actual_native']=2
 samples['originalHumanRooms']+=len(plan['roomNames'])
 samples['allRoomPositiveGroups']+=len(plan['positiveRoomKinds'])
 samples['allRealNativeAuthorSourceBodies']+=actual['sourcedPhysicalInstanceCount']
 samples['allRoomNegations']+=len(plan['explicitNegativeRoomKinds'])
 samples['actualNativeRestoredWorldsFactualSubsetCorrect']+=1
 samples['fullSourceAccepted']+=int(state['fullLiteraryAuthorSourceAccepted'])
assert samples['allRealNativeAuthorSourceBodies']==17
assert samples['allRoomPositiveGroups']==15
assert samples['allRoomNegations']==4
assert samples['wrong_native_spatial_location_refused']==1
assert samples['deterministic_wrong_room_tag_refused']==2
assert samples['source_computers_supported_by_desk_not_actual_native']==2
assert samples['fullSourceAccepted']==0
print('ROUND9 VERIFIED independent human text > source-only scoped room predictions > 3 REAL GameCore/Rapier scenes')
print('17 source-qualified rigid bodies, 8 separate floor regions represented by 48 REAL fixed 3D tile colliders,')
print('4 forbidden room-object kinds absent, and all source body IDs/3D positions/categories exact after native binary save.')
print('Actual restored native-world room inventory produced bounded FACTUAL TEXT, NOT literary or observer prose.')
print('Two wrongly room-tagged and one physically displaced source object correctly FAIL read-only source/geometry checks.')
print('Independent authored constraints: both source computer-on-desk supports missing, and adjacent rooms 8m apart.')
print('Full human scene success 0/3 due unmodeled materials, source relations, shapes, topology and observer truth.')
