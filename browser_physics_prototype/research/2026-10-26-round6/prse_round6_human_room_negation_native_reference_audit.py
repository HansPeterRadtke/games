#!/usr/bin/env python3
"""ROUND SIX independent HUMAN SOURCE negative-room constraints vs REAL frozen
native Rapier bodies and released 3D reference ID links.

This is an entirely separate post-frozen semantic authority/false-negative
test, NOT the denied new observer/physics experiment and NOT the previously
denied feasible-random-parent placebo. Source original, human constraint
labels, earlier independent actual Rapier worlds and 130 release reference
files are immutable. No geometry or runtime services are changed.

Two unavoidable scope rules:
1. "There is no bed IN THE BEDROOM" does NOT forbid a bed in the KITCHEN.
2. A reference id like "pillow|bed (bedroom)" with no corresponding bed
   is an inconsistent/dangling reference link, NOT proof a real collider
   or original author-approved bed exists in that room.
"""
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
from stat import S_IMODE
import json,re,time
HERE=Path(__file__).resolve().parent
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
EXT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1')
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-round6-explicit-negatives')
PRIVATE.mkdir(parents=True,exist_ok=True,mode=0o700)
PRIVATE.chmod(0o700)
GOLD=BASE/'lego_full_data_public_human_gold.json'
OLD=BASE/'lego_source_only_matched_native_130_raw_v1.json'
NEW=EXT/'lego_extended_actual_native_matched_130_raw_v2.json'
SOURCES=BASE/'lego_source_only_frozen_130_raw_v1.json'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (GOLD,OLD,NEW,SOURCES))
start=time.perf_counter()
gold=load(GOLD);old=load(OLD);new=load(NEW);sources=load(SOURCES)
assert len(gold)==len(old['rows'])==len(new['rows'])==len(sources['scenes'])==130
assert new['summary']['accepted']==130 and old['summary']['acceptedNativeSameBudget']==130
assert sources['metadata']['rawFullDataSHA256']==sha(GOLD)
assert new['metadata']['referenceGoldNeverOpened'] and old['summary']['sourceOnlyNoAuthorGoldAndTrueRapier']
assert new['summary']['samePhysicalBodiesInEachArm']==678
# Actual independent human-gold NEGATIVE OBJECT ABSENCE clauses (exact text
# structure), not synthetic negatives and not absence-from-reference proxies.
REGEX=re.compile(r'^There is no (refrigerator|bed|door) in the (kitchen|bedroom|cell)\.$',re.I)
def norm(x):return re.sub(r'[^a-z0-9_]+','_',x.lower().replace(' ','_').replace('-','_')).strip('_')
def ref_prefix(token):
 return norm(re.sub(r'[-_]\d+$','',token))
def scene_bodies(i,arm):
 prev=old['rows'][i]['lexical']['bodyStates']
 next_=new['rows'][i]['candidate' if arm=='candidate' else 'baseline']['bodyStates']
 return prev if arm=='old' else next_
# Frozen explicit original authored positive clauses in the SAME scene as
# the forbidden-room tests. Their room scope is different and must survive.
# No new interpretation is added from the reference scene: the original human
# author wrote these exact Object Placement statements.
REQUIRED_OPPOSITE_ROOM={
 (20,'bed','kitchen'):'There are a treadmill and a bed in the kitchen.',
 (20,'refrigerator','bedroom'):'In the bedroom, there is a refrigerator and a kitchen island.'
}
for (i,kind,room),clause in REQUIRED_OPPOSITE_ROOM.items():
 assert any(' '.join(l['instructions'])==clause and l['condition_type']=='Object Placement'
            for l in gold[i]['labels']),('Original human source instruction unavailable',i,kind,room)
assert len(REQUIRED_OPPOSITE_ROOM)==2
model=Counter();records=[];negatives=[];ref_count=Counter()
for i,story in enumerate(gold):
 assert sources['scenes'][i]['sourceText']==story['instruction']
 assert new['rows'][i]['sourceHash']==sources['scenes'][i]['sourceHash']
 assert old['rows'][i]['sourceId']==sources['scenes'][i]['sourceId']
 originalReference=BASE/f'reference-snapshots/data_{i}.json'
 assert S_IMODE(originalReference.stat().st_mode)==0o600
 ref=load(originalReference)
 assert ref['index']==i and ref['query']==story['instruction']
 rawids=[e['id'] for e in ref['objects']]
 standalones=set(rawids)
 for e in ref['objects']:
  token=e['id'].split(' (',1)[0]
  if '|' not in token:continue
  child,parent=token.split('|',1)
  target=parent+' ('+e['roomId']+')'
  ref_count['allParentReferenceLinks']+=1
  if target in standalones:
   ref_count['parentIdExistsInExactlySameRoom']+=1
  else:
   ref_count['strictParentIdUnresolved']+=1
   if e['id'].count('|')>1:ref_count['nestedReferenceMultiParentUnsupported']+=1
  records.append({'scene':i,'linkedChildID':e['id'],
     'exactParentInSameRoomID':target,
     'sameRoomParentExactIDExists':target in standalones})
 for lab in story['labels']:
  clause=' '.join(lab['instructions'])
  match=REGEX.fullmatch(clause.strip())
  if not match:continue
  assert lab['condition_type'] in ('Object Placement','Floor Layout')
  kind,room=(v.lower() for v in match.groups())
  conflicting=[]
  for x in ref['objects']:
   if x.get('roomId','').casefold()!=room:continue
   identifiers=x['id'].split(' (',1)[0].split('|')
   if any(ref_prefix(token)==kind for token in identifiers):
    conflicting.append(x['id'])
  candidate={
   'scene':i,'humanLabelIndex':lab['condition_idx'],
   'humanSourceAbsenceSHA256':sha256(clause.encode()).hexdigest(),
   'forbiddenObjectKind':kind,'forbiddenRoom':room,
   'independentReferenceIDsConflictingWithHumanAbsence':conflicting,
   'frozenNativeModels':{}
  }
  for arm in ('old','baseline','candidate'):
   bodies=scene_bodies(i,arm)
   categories=[norm(e['kind']) for e in bodies]
   # A globally absent kind proves no positive object of this type is present,
   # but without room-ID provenance this does NOT prove full room semantics.
   exactGenerated=sum(k==kind for k in categories)
   # refrigerator / fridge synonym is only applied to the explicitly named
   # natural source word and previously recognized lexical object kind.
   synonyms={'refrigerator':{'refrigerator','fridge'}}.get(kind,{kind})
   generated=sum(k in synonyms for k in categories)
   candidate['frozenNativeModels'][arm]={
     'globalForbiddenKindBodies':generated,
     'nativeBodysourceRoomIDsAvailable':all('roomId' in body for body in bodies),
     'proofOfForbiddenRoomPhysicalObject':False,
     'forbiddenRoomStatus':'source_negative_not_violated_by_global_absence'
          if not generated else 'unknown_room_provenance'
   }
   model['negativeClauses_'+arm]+=1
   model['forbiddenKindAbsentGlobally_'+arm]+=generated==0
   model['forbiddenKindPresentRoomUnknown_'+arm]+=generated>0
  ref_count['explicitIndependentHumanForbiddenRoomObjectCases']+=1
  ref_count['humanAbsencesContradictedByReferenceIDComponent']+=bool(conflicting)
  ref_count['referenceIDComponentRowsContradictSourceAbsence']+=len(conflicting)
  negatives.append(candidate)
model['frozenHumanScenesCompared']=130
model['actualOldNativeBodyInstances']=sum(len(old['rows'][i]['lexical']['bodyStates']) for i in range(130))
model['actualExtendedNativeBodyInstances']=sum(len(new['rows'][i]['candidate']['bodyStates']) for i in range(130))
model['humanWorldWithRoomCountGreaterThanOne']=sum(len(
   load(BASE/f'reference-snapshots/data_{i}.json')['rooms'])>1 for i in range(130))
# Positive source room requirements elsewhere in same world are still
# mandatory, even if the globally absent body trivially avoids a negative.
positives=[]
for (i,kind,room),clause in REQUIRED_OPPOSITE_ROOM.items():
 other={'scene':i,'requiredKind':kind,'requiredRoom':room,
  'sourcePositiveConstraintSHA256':sha256(clause.encode()).hexdigest(),
  'baselineGlobalPresence':{},'referenceExactRoomQualifiedStandaloneKindPresent':False}
 ref=load(BASE/f'reference-snapshots/data_{i}.json')
 for e in ref['objects']:
  if e.get('roomId')!=room:continue
  val=e['id'].split(' (')[0].split('|')[0]
  if ref_prefix(val)==kind and '|' not in e['id']:other['referenceExactRoomQualifiedStandaloneKindPresent']=True
 for arm in ('old','baseline','candidate'):
  bodies=scene_bodies(i,arm)
  present=sum(norm(e['kind']) in ({'refrigerator','fridge'} if kind=='refrigerator' else {kind}) for e in bodies)
  other['baselineGlobalPresence'][arm]=present
  model['humanOtherRoomPositiveObligations_'+arm]+=1
  model['physicallyMissingRequiredPositiveKindAnywhere_'+arm]+=present==0
 positives.append(other)
assert len(negatives)==4,('Explicit independent author room negatives count differs',len(negatives))
assert len(positives)==2
assert ref_count['allParentReferenceLinks']==2938
assert ref_count['strictParentIdUnresolved']==89
assert ref_count['parentIdExistsInExactlySameRoom']==2849
assert ref_count['humanAbsencesContradictedByReferenceIDComponent']==2
assert ref_count['referenceIDComponentRowsContradictSourceAbsence']==7
assert all(v==2 for key,v in model.items() if key.startswith('physicallyMissingRequiredPositiveKindAnywhere_'))
assert model['actualOldNativeBodyInstances']==575
assert model['actualExtendedNativeBodyInstances']==678
assert model['humanWorldWithRoomCountGreaterThanOne']==95
# The reference is human-constructed, not exhaustive gold. An unresolved
# parent link is NOT evidence the parent body physically exists.
assert all(not any(x['frozenNativeModels'][arm]['proofOfForbiddenRoomPhysicalObject']
                for arm in ('old','baseline','candidate')) for x in negatives)
private=PRIVATE/'prse_round6_original_human_negative_room_native_reference_percase_v1.json'
with private.open('x') as f:
 json.dump({'humanRoomAbsenceClauses':negatives,
            'humanSourceOppositeRoomPositiveClauses':positives,
            'originalReferenceChildParentIDLinks':records},
           f,indent=2);f.write('\n')
private.chmod(0o600)
summary={
 'metadata':{
  'humanAuthorOriginalSourceSHA256':sha(GOLD),
  'humanSourceParserOriginalBaselineSHA256':sha(SOURCES),
  'priorFrozenActualNativeLexicalWorldSHA256':sha(OLD),
  'priorFrozenActualNativeExpandedWorldSHA256':sha(NEW),
  'independentAuthorHumanConstraintTypesUntouched':True,
  'reference3DInstanceIDsCanContradictOriginalAuthorRoomAbsences':True,
  'humanSourceRoomSpecificNegationOverrulesInconsistentExampleReferenceLinks':True,
  'unresolvedReferenceParentIDNotProofOfRealPhysicalObject':True,
  'unscopedRapierObjectKindNotProofOfItsRoomID':True,
  'noAuthorAnnotatedExhaustiveContactNegativeRate':True,
  'preselectedHighPrecisionRoomNegationSyntaxOnly':True,
  'noNewPhysicsOrDeniedObserverCycleExperimentPerformed':True,
  'noRandomFeasibleParentPlacebo':True,
  'fullPrivateAuditSHA256':sha(private)
 },'referenceSourceIDLinkAudit':dict(ref_count),
  'nativeFrozenWorldAndPositiveNegativeSourceAudit':dict(model),
  'explicitHumanNegativeScenes':sorted({r['scene'] for r in negatives}),
  'pairedRequiredOppositeRoomPositivesMissingGlobally':sum(x['baselineGlobalPresence']['candidate']==0 for x in positives),
  'wallSeconds':round(time.perf_counter()-start,4)}
out=HERE/'prse_round6_human_explicit_negative_room_reference_native_aggregate_v1.json'
with out.open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print('ROUND6 NEW INDEPENDENT HUMAN ROOM-NEGATIVE NATIVE TEST',json.dumps(summary,sort_keys=True))
