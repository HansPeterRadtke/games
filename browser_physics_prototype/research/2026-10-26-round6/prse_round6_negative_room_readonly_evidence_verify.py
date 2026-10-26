#!/usr/bin/env python3
"""Read-only verifier for the NEW round-six independent author room-negation
versus previously frozen actual Rapier source-only baselines and 3D references.
Makes NO physics changes, no model calls, no original source mutations.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
from stat import S_IMODE
import json,re
HERE=Path(__file__).resolve().parent
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
EXT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1')
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-round6-explicit-negatives')
def read(p):return json.loads(p.read_text())
def sha(p):return sha256(p.read_bytes()).hexdigest()
goldpath=BASE/'lego_full_data_public_human_gold.json'
sources=BASE/'lego_source_only_frozen_130_raw_v1.json'
old=BASE/'lego_source_only_matched_native_130_raw_v1.json'
new=EXT/'lego_extended_actual_native_matched_130_raw_v2.json'
raw=PRIVATE/'prse_round6_original_human_negative_room_native_reference_percase_v1.json'
safe=HERE/'prse_round6_human_explicit_negative_room_reference_native_aggregate_v1.json'
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (goldpath,sources,old,new,raw))
assert S_IMODE(PRIVATE.stat().st_mode)==0o700
data=read(raw);agg=read(safe);G=read(goldpath)
assert len(G)==130
assert agg['metadata']['humanAuthorOriginalSourceSHA256']==sha(goldpath)
assert agg['metadata']['humanSourceParserOriginalBaselineSHA256']==sha(sources)
assert agg['metadata']['priorFrozenActualNativeLexicalWorldSHA256']==sha(old)
assert agg['metadata']['priorFrozenActualNativeExpandedWorldSHA256']==sha(new)
assert agg['metadata']['fullPrivateAuditSHA256']==sha(raw)
assert agg['metadata']['preselectedHighPrecisionRoomNegationSyntaxOnly']
assert agg['metadata']['noNewPhysicsOrDeniedObserverCycleExperimentPerformed']
assert agg['metadata']['noAuthorAnnotatedExhaustiveContactNegativeRate']
assert agg['metadata']['noRandomFeasibleParentPlacebo']
N=data['humanRoomAbsenceClauses']
P=data['humanSourceOppositeRoomPositiveClauses']
R=data['originalReferenceChildParentIDLinks']
assert len(N)==4 and len(P)==2 and len(R)==2938
REGEX=re.compile(r'^There is no (refrigerator|bed|door) in the (kitchen|bedroom|cell)\.$',re.I)
for case in N:
 i=case['scene']
 labels=G[i]['labels']
 human=next(l for l in labels if l['condition_idx']==case['humanLabelIndex'])
 clause=' '.join(human['instructions'])
 assert sha256(clause.encode()).hexdigest()==case['humanSourceAbsenceSHA256']
 match=REGEX.fullmatch(clause.strip())
 assert match and list(v.lower() for v in match.groups())==[case['forbiddenObjectKind'],case['forbiddenRoom']]
 assert human['condition_type'] in ('Object Placement','Floor Layout')
 ref=read(BASE/f'reference-snapshots/data_{i}.json')
 original=case['independentReferenceIDsConflictingWithHumanAbsence']
 assert all(s in {x['id'] for x in ref['objects']} for s in original)
 for forbidden in original:
  room=case['forbiddenRoom']
  assert room in forbidden and case['forbiddenObjectKind'] in forbidden
 for arm in ('old','baseline','candidate'):
  assert case['frozenNativeModels'][arm]['globalForbiddenKindBodies']==0
  assert case['frozenNativeModels'][arm]['forbiddenRoomStatus']=='source_negative_not_violated_by_global_absence'
  assert not case['frozenNativeModels'][arm]['proofOfForbiddenRoomPhysicalObject']
assert sum(len(x['independentReferenceIDsConflictingWithHumanAbsence']) for x in N)==7
assert sum(bool(x['independentReferenceIDsConflictingWithHumanAbsence']) for x in N)==2
# The TWO positive descriptions are independent ORIGINAL human source clauses
# from the same scene, but their required KIND is absent in BOTH frozen actual
# native inventories; a room-specific negative cannot be 'solved' by deleting
# all occurrences globally.
assert {(x['scene'],x['requiredKind'],x['requiredRoom']) for x in P}=={
 (20,'bed','kitchen'),(20,'refrigerator','bedroom')}
for x in P:
 i=x['scene']
 assert any(sha256(' '.join(l['instructions']).encode()).hexdigest()==x['sourcePositiveConstraintSHA256']
            and l['condition_type']=='Object Placement'
            for l in G[i]['labels'])
 assert x['referenceExactRoomQualifiedStandaloneKindPresent'] is True
 assert all(x['baselineGlobalPresence'][arm]==0 for arm in ('old','baseline','candidate'))
assert sum(not x['sameRoomParentExactIDExists'] for x in R)==89
assert sum(x['sameRoomParentExactIDExists'] for x in R)==2849
for x in R:
 file=BASE/f'reference-snapshots/data_{x['scene']}.json'
 assert file.is_file() and S_IMODE(file.stat().st_mode)==0o600
 # Within each original scene, full ID of linked child must remain original.
 assert x['linkedChildID'] in {r['id'] for r in read(file)['objects']}
assert agg['referenceSourceIDLinkAudit']['allParentReferenceLinks']==2938
assert agg['referenceSourceIDLinkAudit']['strictParentIdUnresolved']==89
assert agg['referenceSourceIDLinkAudit']['humanAbsencesContradictedByReferenceIDComponent']==2
assert agg['referenceSourceIDLinkAudit']['referenceIDComponentRowsContradictSourceAbsence']==7
assert agg['nativeFrozenWorldAndPositiveNegativeSourceAudit']['actualOldNativeBodyInstances']==575
assert agg['nativeFrozenWorldAndPositiveNegativeSourceAudit']['actualExtendedNativeBodyInstances']==678
assert agg['nativeFrozenWorldAndPositiveNegativeSourceAudit']['humanWorldWithRoomCountGreaterThanOne']==95
for arm in ('old','baseline','candidate'):
 assert agg['nativeFrozenWorldAndPositiveNegativeSourceAudit']['negativeClauses_'+arm]==4
 assert agg['nativeFrozenWorldAndPositiveNegativeSourceAudit']['physicallyMissingRequiredPositiveKindAnywhere_'+arm]==2
assert agg['pairedRequiredOppositeRoomPositivesMissingGlobally']==2
print('VERIFIED PRSE ROUND SIX independent authored source-room negatives and actual frozen Rapier:')
print('4 explicit human forbiddances from 3 scenes; 2 opposite-room positive source requirements missed globally')
print('in both same-object-baseline and expanded source-conditioned actual native scene inventories.')
print('2 of 4 forbidden room cases contradicted by 7 exact released reference child-parent ID strings,')
print('with 89 of 2938 reference parent links lacking an exact standalone same-room parent ID.')
print('Reference link inconsistency is NOT a physical false positive; global absence is NOT full room fidelity.')
print('Original sources, all 130 references, original frozen Rapier states, privacy permissions and raw hashes verified.')
