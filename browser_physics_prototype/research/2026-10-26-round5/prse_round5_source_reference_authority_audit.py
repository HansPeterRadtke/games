#!/usr/bin/env python3
"""Source-authority adjudication over frozen real Rapier LEGO worlds.

Independent external human-authored original instructions + typed constraints
are the top authority for what the literary input INTENDS. Separate reference
scene ID fields are fallible example 3D scenes. Native Rapier contacts are
authority only for what PRSE physically SIMULATED. Narration is not a gold label.

This is a READ-ONLY source/reference/model audit, not the previously denied
random-support feasibility test. All posthoc categories are marked accordingly.
"""
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
from stat import S_IMODE
from math import acos,hypot
from itertools import groupby
import json,re,statistics
HERE=Path(__file__).resolve().parent
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
V=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1')
R3=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-hard-negatives-r3')
R5=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-round5-source-authority')
S=BASE/'lego_source_only_matched_native_130_raw_v1.json'
EX=V/'lego_extended_actual_native_matched_130_raw_v2.json'
GOLD=BASE/'lego_full_data_public_human_gold.json'
AUDIT=R3/'round3_human_source_claims_and_native_gold_audit_v1.json'
def load(p):return json.loads(p.read_text())
def sha(p):return sha256(p.read_bytes()).hexdigest()
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (S,EX,GOLD,AUDIT))
src=load(GOLD);old=load(S)['rows'];ext=load(EX)['rows'];human=load(AUDIT)['perCase']
assert len(src)==len(old)==len(ext)==130
assert len(human)==22
assert load(EX)['summary']['accepted']==130
def norm(s):
 return re.sub(r'[^a-z0-9_]+','_',s.strip().lower().replace(' ','_').replace('-','_')).strip('_')
def category_from_id(raw):
 # Reference ID rather than object_name has underlying physical component.
 # Pipe separates receptacle parent. Parentheses suffix preserves room.
 root=raw.split(' (',1)[0].split('|',1)[0]
 root=re.sub(r'[-_]\d+$','',root)
 return norm(root)
def category_from_objname(raw):
 if not isinstance(raw,str) or not raw:return None
 root=re.sub(r'[-_]\d+$','',raw)
 return norm(root)
def kind_from_body(e):return norm(e['kind'])
def pair_match(ref,bodies,kind_field):
 reference=Counter(k for e in ref['objects'] if (k:=kind_field(e)))
 made=Counter(kind_from_body(e) for e in bodies)
 covered=sum(min(reference[k],made[k]) for k in reference)
 missing=sum(max(0,reference[k]-made[k]) for k in reference)
 unmatched=sum(max(0,made[k]-reference[k]) for k in made)
 assert covered+missing==sum(reference.values())
 assert covered+unmatched==sum(made.values())
 return covered,missing,unmatched,reference,made
def tilt(q):
 n=hypot(q['x'],q['y'],q['z'],q['w'])
 if n<.5:return 3.14159
 return acos(max(-1,min(1,1-2*(q['x']**2+q['z']**2)/(n*n))))
def upright_top(state,childID,supportID):
 v={e['id']:e for e in state['bodyStates']}
 if childID not in v or supportID not in v:return False
 a,b=v[childID],v[supportID]
 if a['shape']!='box' or b['shape']!='box' or tilt(a['rotation'])>.1 or tilt(b['rotation'])>.1:return False
 if any(abs(a['position'][ax]-b['position'][ax])+a['size'][ax]/2>b['size'][ax]/2+.03 for ax in ('x','z')):return False
 dy=(a['position']['y']-a['size']['y']/2)-(b['position']['y']+b['size']['y']/2)
 if abs(dy)>.08:return False
 return any({p['a'],p['b']}=={childID,supportID} and p['contactPointCount']>0
            for p in state['contactPairs'])
counts=Counter();private=[];hard=[]
exact_old=exact_ext=0;totalID=totalNamed=0;totalRooms=0;ambiguous_ref=0
human_by_scene=defaultdict(list)
for row in human:human_by_scene[row['scene']].append(row)
for i,(story,prev,native) in enumerate(zip(src,old,ext)):
 ref_file=BASE/f'reference-snapshots/data_{i}.json'
 assert S_IMODE(ref_file.stat().st_mode)==0o600
 ref=load(ref_file)
 assert ref['index']==i and ref['query']==story['instruction']
 bodiesOld=prev['lexical']['bodyStates']
 bodiesNew=native['candidate']['bodyStates']
 bodiesControl=native['baseline']['bodyStates']
 assert {e['id'] for e in bodiesNew}=={e['id'] for e in bodiesControl}
 original_count=len(bodiesOld);new_count=len(bodiesNew)
 idKinds=lambda x:category_from_id(x['id'])
 nameKinds=lambda x:category_from_objname(x.get('object_name'))
 oldByID=pair_match(ref,bodiesOld,idKinds)
 newByID=pair_match(ref,bodiesNew,idKinds)
 oldByName=pair_match(ref,bodiesOld,nameKinds)
 newByName=pair_match(ref,bodiesNew,nameKinds)
 assert oldByID[0]<=original_count and newByID[0]<=new_count
 assert newByID[0]>=oldByID[0]
 counts['humanScenes']+=1
 counts['singleRoomScenes']+=len(ref['rooms'])==1
 counts['multipleRoomScenes']+=len(ref['rooms'])>1
 counts['sourceNamedReferenceRoomInstances']+=len(ref['rooms'])
 counts['referenceIdCategorizedAssets']+=len(ref['objects'])
 counts['referenceNamedAssets']+=sum(bool(e.get('object_name')) for e in ref['objects'])
 counts['namedReferenceOldMatch']+=oldByName[0]
 counts['namedReferenceExtendedMatch']+=newByName[0]
 counts['rawIdReferenceOldMatch']+=oldByID[0]
 counts['rawIdReferenceExtendedMatch']+=newByID[0]
 counts['physicalBodiesPrevious']+=len(bodiesOld)
 counts['physicalBodiesExtended']+=len(bodiesNew)
 counts['extendedMatchedExtraByIdKinds']+=newByID[0]-oldByID[0]
 counts['extendedMatchedExtraByObjectName']+=newByName[0]-oldByName[0]
 if len(ref['rooms'])>1:
  counts['multiRoomNeverAssignedByGlobalSingleRoomCompiler']+=1
  counts['multiRoomActualBodiesInStudy']+=len(bodiesNew)
 for e in ref['objects']:
  if not e.get('object_name') and '|' in e['id']:
   counts['referenceAnonymousNameHasExplicitChildParentId']+=1
  if e.get('object_name') and idKinds(e)!=nameKinds(e):
   counts['referenceObjectNameDiffersFromUnderlyingIdKind']+=1
 cats=[(e['id'],category_from_id(e['id']),e.get('roomId')) for e in ref['objects']]
 raw_ids=Counter(e['id'] for e in ref['objects'])
 counts['sameIdRepeatedInReferenceAssets']+=sum(n-1 for n in raw_ids.values() if n>1)
 private.append({'scene':i,'referenceIDCategories':dict(oldByID[3]),
                 'referenceObjectNameCategories':dict(oldByName[3]),
                 'oldGeneratedCategories':dict(oldByID[4]),
                 'extendedGeneratedCategories':dict(newByID[4]),
                 'referenceTypeMatchOld':oldByID[0],
                 'referenceTypeMatchExtended':newByID[0],
                 'sourceIsMultiRoom':len(ref['rooms'])>1,
                 'rawReferenceIDs':cats})

# Author ON entailment versus actual physical contacts. Human source labels are
# independent; semantic classifications were assigned POSTHOC in round 3.
# A positive set chosen after seeing model contacts is NOT an unbiased recall.
selected=[]
for i,row in enumerate(ext):
 state=row['candidate']
 contacts=state['contactPairs']
 candidateKinds={e['id']:kind_from_body(e) for e in state['bodyStates']}
 supportlist=[]
 for contact in contacts:
  a=contact['a'];b=contact['b']
  top= (a,b) if upright_top(state,a,b) else ((b,a) if upright_top(state,b,a) else None)
  category='unknown_in_original_author'
  proof=None
  if top:
   child,support=top
   for case in human_by_scene[i]:
    if case['relation']!=[candidateKinds[child],candidateKinds[support]]:continue
    category=case['posthocHumanPhraseAdjudication']
    proof=case.get('sourceClaimHash')
    break
  # Original source says a composite 'computer including a mouse' sits on
  # the desk; it does not independently assert that the mouse's own collider
  # rests directly on the desk. Distinguish composite/uncertain from false.
  if i==54 and top and [candidateKinds[top[0]],candidateKinds[top[1]]]==['mouse','desk'] and category=='unknown_in_original_author':
   category='composite_unknown'
   proof=next((c.get('sourceClaimHash') for c in human_by_scene[i]
       if c['posthocHumanPhraseAdjudication']=='composite_unknown'),None)
  if i==54 and not top:
   # A mouse is part of the described computer, not an independently
   # authored 'mouse resting on desk' clause, and this contact has no
   # independently validated top-face support geometry after Rapier settles.
   category='composite_unknown_not_top_support'
   counts['physicalContactCompositeButNotActualTopSupport']+=1
  if top and category=='nonvertical':counts['physicalContactWronglyCalledHumanOnByLegacyMachineGold']+=1
  if top and category=='direct_vertical':counts['physicalContactEntailedBySelectedHumanClause']+=1
  if top and category=='vertical':counts['physicalContactEntailedByPreviouslySelectedHumanClause']+=1
  if top and category=='composite_unknown':counts['physicalContactCompositeDirectRelationUnresolved']+=1
  if not top:counts['physicalContactNotUprightTopSupport']+=1
  if top and category.startswith('unknown'):counts['physicalContactSourceLinkNotResolved']+=1
  counts['realNativeContactPairsExtended']+=1
  supportlist.append({'childID':top[0] if top else None,'supportID':top[1] if top else None,
    'sourceTypeRoles':[candidateKinds[top[0]],candidateKinds[top[1]]] if top else None,
    'sourceEntailmentPosthoc':category,'humanLabelHash':proof,
    'realColliderContactPointCount':contact.get('contactPointCount',0)})
 if supportlist:hard.append({'scene':i,'contacts':supportlist})
assert counts['humanScenes']==130
assert counts['sourceNamedReferenceRoomInstances']==295
assert counts['multipleRoomScenes']==95
assert counts['physicalBodiesPrevious']==575
assert counts['physicalBodiesExtended']==678
assert counts['realNativeContactPairsExtended']==11
assert counts['physicalContactWronglyCalledHumanOnByLegacyMachineGold']==1
assert counts['physicalContactNotUprightTopSupport']==1
assert counts['physicalContactCompositeButNotActualTopSupport']==1
assert counts['physicalContactEntailedBySelectedHumanClause']+counts['physicalContactEntailedByPreviouslySelectedHumanClause']==9

# Additional source/reference authority conflict in the six added model
# physically supported pairs. Freeze human label provenance from the earlier
# posthoc audit; compare to actual reference object INSTANCE IDs.
six=[r for r in human if r['posthocHumanPhraseAdjudication']=='direct_vertical']
assert len(six)==6
known=[]
for row in six:
 i=row['scene'];child,support=row['relation']
 ref=load(BASE/f'reference-snapshots/data_{i}.json')
 directLinks=[]
 for e in ref['objects']:
  id=e['id']
  if '|' not in id:continue
  childID,parentID=id.split(' (',1)[0].split('|',1)
  directLinks.append((category_from_id(childID),category_from_id(parentID),id))
 strict=[id for a,b,id in directLinks if a==child and b==support]
 # Ignore semi-automatic category synonyms in exact score.
 childAny=sum(category_from_id(e['id'])==child for e in ref['objects'])
 parentAny=sum(category_from_id(e['id'])==support for e in ref['objects'])
 category='exact_linked_reference_child_parent_ids' if strict else (
   'reference_contains_child_and_parent_but_no_exact_link' if childAny and parentAny else
   'reference_missing_exact_child_or_parent_category')
 counts['sixAuthorSourceDirectOnHumanClauses']+=1
 counts['sixAuthorExactLinkedReferencePairs']+=bool(strict)
 counts['sixAuthorBothReferenceObjectKindsPresent']+=bool(childAny and parentAny)
 known.append({'scene':i,'sourceRoles':[child,support],
  'independentHumanLabelSHA256':row['sourceClaimHash'],
  'physicalCandidateActualTopSupported':any(x['sourceEntailmentPosthoc']=='direct_vertical' and x['sourceTypeRoles']==[child,support] for x in next(v['contacts'] for v in hard if v['scene']==i)),
  'referenceExactChildCategoryCount':childAny,'referenceExactParentCategoryCount':parentAny,
  'referenceExactDirectChildParentIDLinks':strict,
  'sourceVsReferenceAuthorityStatus':category})
assert all(x['physicalCandidateActualTopSupported'] for x in known)
# Correctness lower bounds cannot be based on reference absence; correct
# original human author statement still wins over mismatching 3D example.
protected=R5/'prse_round5_source_vs_reference_vs_native_percase_v1.json'
with protected.open('x') as f:
 json.dump({'records':private,'humanSourceContactAudit':hard,'sixNewHumanSourcesReferenceAdjudication':known},f,indent=2)
 f.write('\n')
protected.chmod(0o600)
out={'metadata':{'independentOriginalHumanSourceSHA256':sha(GOLD),
 'referenceDataAuthoredByBenchmarkTeamButNotGuaranteedSemanticGroundTruth':True,
 'sourceWorldClaimAuthority':'Original independently human-annotated literary constraints',
 'referenceInstanceIDAuthority':'Use actual id field for reference physical instance type; object_name can be group/alias',
 'physicalAuthority':'Actual GameCore/Rapier top-face collider contacts in frozen physical world only',
 'observerAuthority':'Only physically observed facts and witnessed events; not shown here',
 'sourceSelectionsPosthocAndNotOutOfSample':True,
 'noExhaustiveHumanNegativeGold':True,'unknownAndAmbiguousRemainUnknown':True,
 'noIndependentMetricScaleOr3DMeshGroundTruth':True,
 'percaseRawSHA256':sha(protected),
 'priorSourceStudyCommittedSHA256':sha(S),
 'newExtendedNativeFrozenSHA256':sha(EX),
 'originalHumanAnnotatedSourceConflictRule':'Reference example mismatches cannot override exact original human description'},
 'counts':dict(counts),
 'sixPosthocNewSupportSourceReferenceCases':[{
  'scene':e['scene'],'roles':e['sourceRoles'],
  'referenceStatus':e['sourceVsReferenceAuthorityStatus'],
  'exactReferenceDirectChildParentLinkCount':len(e['referenceExactDirectChildParentIDLinks'])}
  for e in known]}
safe=HERE/'prse_round5_source_authority_reference_native_aggregate_v1.json'
with safe.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('ROUND5_SOURCE_REFERENCE_PHYSICAL_AUTHORITY',json.dumps(dict(counts),sort_keys=True))
print('ROUND5_SIX_SOURCE_REF_CONFLICTS',json.dumps(out['sixPosthocNewSupportSourceReferenceCases']))
