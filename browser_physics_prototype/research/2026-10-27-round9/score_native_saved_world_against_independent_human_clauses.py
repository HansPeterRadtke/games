#!/usr/bin/env python3
"""AFTER NEW NATIVE OUTPUT FROZEN: independent authored-human LEGO constraints
versus ACTUAL GameCore/Rapier room-qualified source body, real contacts,
native save/identity and bounded factual text. This is a POSTHOC small sample,
not a new heldout generalization estimate, and source body shapes are NOT
author-correct metric meshes. The full observer-cycle operation remains
blocked and is not retried.
"""
from pathlib import Path
from collections import defaultdict,Counter
from hashlib import sha256
from stat import S_IMODE
import json,math,re,time
HERE=Path(__file__).resolve().parent
PRIV=Path('/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round9-room-contract')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
manifest=PRIV/'source_original_strict_room_proposal_frozen_v3.json'
NATIVE_RAW=PRIV/'room_source_to_native_to_factual_text_v3_raw_v2.json'
goldpath=BASE/'lego_full_data_public_human_gold.json'
old=BASE/'lego_source_only_matched_native_130_raw_v1.json'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (manifest,NATIVE_RAW,goldpath,old))
gold=read(goldpath);src=read(manifest);record=read(NATIVE_RAW)
assert src['metadata']['humanOfficialLabelsAndReferenceRoomsNeverReadBySourceProposals']
assert record['metadata']['goldLabelsNeverReadInGeneration']
assert record['metadata']['sourceOnlyManifestSHA256']==sha(manifest)
assert len(src['cases'])==len(record['cases'])==3
assert [x['sceneIndex'] for x in src['cases']]==[20,26,40]
assert record['summary']['casesNativeSuccessful']==3
assert record['summary']['nativeActualSourceInstances']==17
assert record['summary']['completeOriginalHumanSceneValidated']==0
before=time.perf_counter();counts=Counter();rows=[]
for plan,case in zip(src['cases'],record['cases']):
 i=plan['sceneIndex'];human=gold[i]
 assert case['sceneIndex']==i and case['status']=='native_room_positive_negative_subset_saved_and_restored'
 assert human['instruction']==plan['sourceText']
 assert sha256(human['instruction'].encode()).hexdigest()==plan['sourceTextSHA256']
 assert case['savedOriginalHumanSourceStillExact'] and case['savedSameRoomQualifiedIDsAndGeometryExact']
 assert not case['fullLiteraryAuthorSourceAccepted'] and case['noIndependentObserverNarrationWasGenerated']
 native=case['restoredActualNativeScene'];bodies=native['realNativeBodies']
 assert native['sourcedPhysicalInstanceCount']==sum(x['count'] for x in plan['positiveRoomKinds'])
 assert native['physicalPartitionFloorCount']==6*len(plan['roomNames'])
 assert native['allExplicitAuthorPositivesSatisfiedInNativeSpatialRegions']
 assert native['allExplicitAuthorRoomNegativesSatisfied']
 assert len({x['id'] for x in bodies})==len(bodies)
 assert len(bodies)==native['nativeMaterializedAll']
 assert all(x['isRealGameCoreRapierBody'] for x in bodies)
 assert all(x['geometrySourceCertified'] is False for x in bodies)
 labels=human['labels'];gold_clauses={}
 for l in labels:
  h=sha256(' '.join(l['instructions']).encode()).hexdigest()
  gold_clauses.setdefault(h,[]).append(l)
 uniquePositive=set()
 for pos in plan['positiveRoomKinds']:
  match=gold_clauses.get(pos['sourceClauseSHA256'],[])
  assert match,('Original independent human author labeled positive NOT FOUND',i,pos)
  assert any(l['condition_type'] in ('Object Placement','Floor Layout') for l in match)
  real=sum(x['kind']==pos['kind'] and x['roomId']==pos['roomId'] for x in bodies)
  assert real==pos['count']
  # exact source-positive fidelity is currently lexical only, not metric geometry.
  counts['humanLabelMatchedRoomKindGroups']+=1
  counts['humanLabelMatchedPhysicalInstances']+=real
  uniquePositive.add(pos['sourceClauseSHA256'])
 for neg in plan['explicitNegativeRoomKinds']:
  match=gold_clauses.get(neg['sourceClauseSHA256'],[])
  assert match,('Original independently human-labeled negative absent',i,neg)
  assert any(l['condition_type'] in ('Object Placement','Floor Layout') for l in match)
  assert not any(x['kind']==neg['kind'] and x['roomId']==neg['roomId'] for x in bodies)
  counts['humanLabelMatchedRoomSpecificAbsences']+=1
 counts['completeHumanScenes']+=1
 counts['authorPhysicalRoomSourceKindsRecognized']+=len(plan['positiveRoomKinds'])
 counts['independentHumanPositiveClausesPartiallyOrFullyRecognized']+=len(uniquePositive)
 counts['officialHumanConstraintsInTheseScenes']+=len(labels)
 counts['unverifiedRoomOrAttributeClauses']+=len(plan['recognizedButUnmaterializableClauses'])
 counts['originalAuthorRoomNamesRecognized']+=len(plan['roomNames'])
 # From restored native GameCore bodies only, check factual current-world text
 # mirrors exactly named room/object categories, without claiming a literary
 # observer. No interpolated material, motives, histories or secret events.
 report=case['factualRoomTextFromRestoredActualBodies']
 assert report.count('In the provisional spatial region called ')==len(plan['roomNames'])
 assert 'author says' not in report and 'was destroyed' not in report
 for room in plan['roomNames']:
  prefix='In the provisional spatial region called '+room.replace('_',' ')+','
  assert prefix in report
 counts['restoredActualRoomTextDerivedWithoutHallucinatedSourceAttributes']+=1
 # Test previous ACTUAL frozen lexical same scene (not a same-body comparison)
 # specifically missing two author-required categories globally in case 20.
 if i==20:
  previous=read(old)['rows'][i]['lexical']['bodyStates']
  kindSet={x['kind'] for x in previous}
  assert 'bed' not in kindSet and 'fridge' not in kindSet
  actualKinds={(x['roomId'],x['kind']) for x in bodies}
  assert ('kitchen','bed') in actualKinds and ('bedroom','fridge') in actualKinds
  assert ('bedroom','bed') not in actualKinds and ('kitchen','fridge') not in actualKinds
  assert case['localRoomNegativeTamperGuard']['recognizedContradiction']
  counts['previouslyMissingIndependentAuthorRequiredKindsActuallyInstantiated']+=2
 # Independent original source requires TWO computers "on" desk, not merely
 # in same room. New source-only parser never extracted that relation; actual
 # Rapier contact pairs show both computers touching only the ROOM FLOOR.
 # This proves new actual physical state still fails that original clause.
 if i==40:
  humanSupport='Two computers in the guard control room are on the desk.'
  assert any(' '.join(l['instructions'])==humanSupport
             and l['condition_type']=='Object Placement' for l in labels)
  desk={x['id'] for x in bodies if x['kind']=='desk' and x['roomId']=='guard_control_room'}
  computers={x['id'] for x in bodies if x['kind']=='computer' and x['roomId']=='guard_control_room'}
  assert len(desk)==1 and len(computers)==2
  contacts=native['actualNativeInterobjectContacts']
  assert not any(set((a,b))==set((x,y)) for a,b,n in contacts
      for x in computers for y in desk)
  assert all(any(set((a,b))=={comp,f['id']} and n>0 for a,b,n in contacts
       for f in bodies if f['kind']=='room_floor')
       for comp in computers)
  counts['authorExplicitComputerOnDeskSupportsUnfulfilled']+=2
  counts['sourceGoldComputerSupportClausesUnfulfilled']+=1
 # Author explicitly says kitchen ADJACENT to living room; these physical
 # source-room floor regions have no shared boundary, separated by a gap.
 if i==20:
  stmt='The kitchen is adjacent to the living room.'
  assert any(' '.join(l['instructions'])==stmt
           and l['condition_type']=='Floor Layout' for l in labels)
  living=[x for x in bodies if x['roomId']=='living_room' and x['kind']=='room_floor']
  kitchen=[x for x in bodies if x['roomId']=='kitchen' and x['kind']=='room_floor']
  assert living and kitchen
  right=max(x['position']['x']+x['dimensions']['x']/2 for x in living)
  left=min(x['position']['x']-x['dimensions']['x']/2 for x in kitchen)
  gap=left-right
  assert gap>3,('Room platforms unexpectedly abut; change prior relation conclusion',gap)
  counts['sourceGoldRoomAdjacencyClausesViolated']+=1
  counts['measuredActualPlatformGapCm']=round(gap*100)
 # Architecture/attributes/room surfaces were never reconstructed.
 assert case['sourceUnresolvedCount']>0
 assert case['fullLiteraryAuthorSourceAccepted'] is False
 rows.append({'sceneIndex':i,
  'humanOfficialConstraintCount':len(labels),
  'sourceRecognizedRoomGroups':len(plan['positiveRoomKinds']),
  'nativeSavedSourceObjectInstances':native['sourcedPhysicalInstanceCount'],
  'nativeActualPlatformTileCount':native['physicalPartitionFloorCount'],
  'officialHumanNegativeConstraintsMatched':len(plan['explicitNegativeRoomKinds']),
  'unresolvedKnownSourceClauses':case['sourceUnresolvedCount'],
  'fullSourceCorrect':False,
  'originalSourceRestoredExactly':case['savedOriginalHumanSourceStillExact'],
  'roomQualifiedBodyIDsRestoredExactly':case['savedSameRoomQualifiedIDsAndGeometryExact'],
  'factualWorldInventoryTextSourceFaithfulForAcceptedSubset':True,
  'sourceAndTruthfulObserverLiteraryProseNotEvaluated':True})
assert counts['completeHumanScenes']==3
assert counts['humanLabelMatchedPhysicalInstances']==17
assert counts['humanLabelMatchedRoomSpecificAbsences']==4
assert counts['authorExplicitComputerOnDeskSupportsUnfulfilled']==2
assert counts['sourceGoldRoomAdjacencyClausesViolated']==1
assert counts['previouslyMissingIndependentAuthorRequiredKindsActuallyInstantiated']==2
assert all(r['fullSourceCorrect'] is False for r in rows)
counts['realGameCoreNativeSaveToBodyAndRoomTextSucceededInBoundedSubset']=3
counts['completeLiteraryScenesAccepted']=0
counts['knownSourceRelationClausesViolated']=2
counts['observerLiteraryTruthVerified']=0
counts['originalHumanSceneSourceType']='posthoc studied benchmark, no pristine heldout'
out=PRIV/'actual_saved_native_source_vs_independent_human_constraints_v1.json'
with out.open('x') as f:
 json.dump({'metadata':{'humanGoldOfficialSHA256':sha(goldpath),
 'frozenSourceOnlyManifestSHA256':sha(manifest),
 'actualNewNativeRapierSaveToFactualWorldReportSHA256':sha(NATIVE_RAW),
 'posthocNotHeldout':True,'assetGeometryAndTopologyNotValidated':True,
 'notTheDeniedBroadObserverCycle':True},
 'metrics':dict(counts),'rows':rows},f,indent=2);f.write('\n')
out.chmod(0o600)
safe=HERE/'prse_round9_native_human_source_room_semantic_score_aggregate_v1.json'
with safe.open('x') as f:
 json.dump({'metadata':{'privateHumanGoldScorerSHA256':sha(out),
 'frozenSourceOriginalTextManifestSHA256':sha(manifest),
 'frozenActualGameCoreRapierNativeSaveSHA256':sha(NATIVE_RAW),
 'independentHumanSourceOriginalSHA256':sha(goldpath),
 'onlyPreviouslyStudiedHumanScenes':True,
 'sourceRoomSubsetNotCompleteAuthorScene':True,
 'fullNarrativeObserverRoundTripNotAttempted':True},
 'summary':dict(counts),'perScene':rows,
 'wallSeconds':round(time.perf_counter()-before,4)},f,indent=2);f.write('\n')
print('PRSE_ROUND9_NATIVE_SAVED_3D_VS_INDEPENDENT_HUMAN_SOURCE_GOLD',json.dumps(dict(counts),sort_keys=True))
