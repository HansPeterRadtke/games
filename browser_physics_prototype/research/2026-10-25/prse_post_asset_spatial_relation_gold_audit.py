#!/usr/bin/env python3
"""Independent SceneEval SOURCE-RELATION audit of already frozen real PRSE
GameCore/Rapier native body poses and ACTUAL COLLIDER contact manifolds.

The scene parser and THREE physical worlds (baseline / generic-box / strict
dimensional catalog) were previously materialized and saved WITHOUT official
SceneEval relationship labels. This scorer alone opens author OORel labels.

Supported predicates for limited transparent physics checks:
  ON: gold convention "substrate,object", second rests above first, AABB
      containment in both horizontal dimensions AND actual native contact.
      Unknown rotated/nonplanar surface is not incorrectly asserted.
  NEXT/NEAR: two real surface AABBs within 1.1/1.5 metres in full 3D.
      Proximity can be ACCIDENTAL due to arbitrary placements, so even matches
      are NOT evidence of deliberate source-entailed arrangement.

Directional, inside, orientation, containment, multi-party and architectural
relations are ABSTENTIONS, NOT negative successes, pending actual frame and
asset/container definitions. A source gold relation can have repeated types;
the most lenient existential pair count is a SOURCE-TYPE UPPER BOUND, not
instance-level proof or real observed narrative entailment.

All per-case author relationships remain owner-private Nitro, with aggregates
and raw source SHA only in the Games Git repository.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
from collections import Counter,defaultdict
import json,zipfile,io,csv,math

R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset')
DATA=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
SOURCE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert sha(DATA)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(DATA) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
ids=list(range(100))+list(range(100,500,4))
PREDS={
 'on':'on',
 'near':'near','nearby':'near','close_to':'near',
 'next':'next','next_to':'next','beside':'next','adjacent':'next','side_by_side':'next'
}
def norm(t):
 k=t.strip().lower().replace(' ','_')
 return {'television':'tv','bunk_bed':'bed','refrigerator':'fridge',
  'bedside_lamp':'lamp'}.get(k,k)
def gold_rels(row):
 for chunk in row['OORel'].split(';'):
  bits=[x.strip() for x in chunk.split(',')]
  if len(bits)<6:continue
  try:num=int(bits[1])
  except ValueError:continue
  if bits[0] not in ('eq','ge','gt'):continue
  count=max(1,num+(bits[0]=='gt'))
  yield {'relation':bits[2].lower(),'mapped':PREDS.get(bits[2].lower()),
   'kindA':norm(bits[4]),'kindB':norm(bits[5]),'minCount':count,
   'op':bits[0],'sourceCount':num}
def centered(box,key):
 return box['position'][key]
def surface_gap(a,b):
 d=[]
 for k in ('x','y','z'):
  gap=max(0.,abs(a['position'][k]-b['position'][k])-
   (a['size'][k]+b['size'][k])/2)
  d.append(gap)
 return math.sqrt(sum(x*x for x in d))
def upright(x):
 q=x['rotation']
 # An axis-aligned cuboid bounding box and "up" support are not justified
 # when the actual native rigid body is tilted.
 angle=2*math.acos(min(1,max(-1,abs(q['w']))))
 return angle<.10
def predicate(name,a,b,contacts):
 if name=='on':
  if not upright(a) or not upright(b):return None
  top=a['position']['y']+a['size']['y']/2
  bottom=b['position']['y']-b['size']['y']/2
  inFootprint=all(
   abs(b['position'][k]-a['position'][k])+b['size'][k]/2<=a['size'][k]/2+.03
   for k in ('x','z'))
  if not inFootprint or abs(bottom-top)>.08:return False
  if frozenset([a['id'],b['id']]) not in contacts:return False
  return True
 if name in ('next','near'):
  return surface_gap(a,b)<=(1.1 if name=='next' else 1.5)
 return None

methods={}
for method in ('baseline','generic','catalog'):
 filename=P/f'prse_post_asset_native_{method}_200_raw_v2.json'
 assert filename.exists() and S_IMODE(filename.stat().st_mode)==0o600
 data=load(filename)
 assert data['metadata']['sourceIds']==ids
 assert [x['id'] for x in data['rows']]==ids
 assert data['summary']['acceptedNativeBodyScenes']==197
 assert data['summary']['failedRebuilds']==0
 assert data['summary']['sourceTextStillHasSameHash']
 methods[method]=data
assert [(x['status']) for x in methods['baseline']['rows']]==[
 x['status'] for x in methods['generic']['rows']]==[
 x['status'] for x in methods['catalog']['rows']]
metrics={k:{s:Counter() for s in ('human','assisted')} for k in methods}
allPrivate=[]
for index,id in enumerate(ids):
 entries={method:methods[method]['rows'][index] for method in methods}
 if entries['baseline']['status']!='native_simulated':
  allPrivate.append({'id':id,'status':'not_physically_accepted'})
  continue
 goals=list(gold_rels(gold[id]))
 row={'id':id,'subset':'human' if id<100 else 'assisted',
  'goals':[]}
 for method,one in entries.items():
  group=metrics[method][row['subset']]
  group['acceptedSourceScenes']+=1
  # Counters below updated once per scene via separate method loop later,
  # not per annotation relation.
 for relation in goals:
  result={**relation,'independentPhysics':{}}
  for method,one in entries.items():
   group=metrics[method][row['subset']]
   group['allOfficialAuthorObjectRelations']+=1
   mapping=relation['mapped']
   if mapping is None:
    group['unsupportedAnnotationRelationKinds']+=1
    result['independentPhysics'][method]='abstain_unsupported_relation_semantics'
    continue
   group['authorRelationsWithVerifiablePredicateKind']+=1
   byKind=defaultdict(list)
   for b in one['bodyStates']:byKind[norm(b['kind'])].append(b)
   aa=byKind.get(relation['kindA'],[])
   bb=byKind.get(relation['kindB'],[])
   if not aa or not bb:
    group['typePairPhysicallyMissing']+=1
    result['independentPhysics'][method]='type_missing'
    continue
   group['typePairsMaterializedInReal3D']+=1
   contacts={frozenset([e['a'],e['b']]) for e in one['nativeContactPairs']}
   yes=set();unknown=0;candidatePairs=0
   for a in aa:
    for b in bb:
     if a['id']==b['id']:continue
     candidatePairs+=1
     answer=predicate(mapping,a,b,contacts)
     if answer is True:yes.add((a['id'],b['id']))
     if answer is None:unknown+=1
   # Intentionally optimistic. Count distinct supported B source entities;
   # a "one monitor on desk" source relation should not be satisfied by
   # reusing the same monitor on several indistinguishable desk instances.
   witnesses=len(set(b for a,b in yes))
   if witnesses>=relation['minCount']:
    group['physicallySatisfiedAuthorRelationsAtLeastRequiredInstances']+=1
    if mapping=='on':
     group['nativeContactSupportedOnAuthorClauses']+=1
    else:
     group['geometricProximityAuthorClauses']+=1
    result['independentPhysics'][method]='actual_native_supported'
   elif candidatePairs>0 and unknown==candidatePairs:
    group['unverifiedBecauseAllPhysicalPairsUnsupportedOrRotated']+=1
    result['independentPhysics'][method]='unknown_rotation_or_unsupported'
   else:
    group['authorRelationTypesPresentButUnfulfilled']+=1
    result['independentPhysics'][method]='not_physically_supported'
   if relation['mapped']=='on':
    group['authorOnRelationsWithBothTypesPhysicallyPresent']+=1
    group['nativePhysicallyContactingOnWitnessPairs']+=len(yes)
   else:
    group['authorProximityRelationsWithBothTypesPhysicallyPresent']+=1
   group['candidateTypePairWitnessesTested']+=candidatePairs
  row['goals'].append(result)
 allPrivate.append(row)

# Corpus total counts including rejected authored source relation requirements.
for index,id in enumerate(ids):
 if methods['baseline']['rows'][index]['status']=='native_simulated':continue
 group='human' if id<100 else 'assisted'
 unverified=len(list(gold_rels(gold[id])))
 for m in methods:
  metrics[m][group]['geometricallyRejectedScenes']+=1
  metrics[m][group]['authorRelationsNotPhysicallyCheckedRejectedScene']+=unverified

public={'metadata':{
 'officialSceneEvalZIPSHA256':sha(DATA),
 'physicallyFrozenSourceIDs':ids,
 'labelsOnlyOpenedAfterNativePhysicsReconstruction':True,
 'metric':'Optimistic source-type pair existence; on requires real Rapier contact/3D planar footprint; near/next use full 3D AABB surface separation',
 'relationDirectionCaution':'On label interpreted as annotation substrate in first argument and object in second; not a guarantee of every complex natural-language relation',
 'abstentions':'Camera-dependent directional, containment, facing, multi-party and architectural label relations are deliberately unknown, not declared false',
 'proximityCaution':'Arbitrary floor-grid proximity can satisfy an author type-pair label by coincidence; not source-driven intended arrangement',
 'sourceFidelityCaution':'Categories can have ambiguous repeated instances; no instance-specific annotator correspondence proved',
 'physicalAssetCaution':'Generic added bodies have uncalibrated toy collision-box shapes and no visual asset fidelity'},
 'methods':{m:{g:dict(c) for g,c in groups.items()} for m,groups in metrics.items()}}
pub=R/'prse_post_asset_spatial_relation_gold_200_aggregate_v1.json'
full=P/'prse_post_asset_spatial_relation_gold_200_raw_v1.json'
with full.open('x') as f:
 json.dump({'metadata':public['metadata'],'perScene':allPrivate},f,indent=2);f.write('\n')
full.chmod(0o600)
public['metadata']['privateFullAuthorGoldAuditSHA256']=sha(full)
public['metadata']['privateMethodNativeRawHashes']={
 m:sha(P/f'prse_post_asset_native_{m}_200_raw_v2.json') for m in methods}
with pub.open('x') as f:json.dump(public,f,indent=2);f.write('\n')
for method in methods:
 print('METHOD',method)
 for group,c in metrics[method].items():
  print(' ',group,
   'gold',c['allOfficialAuthorObjectRelations'],
   'testableKind',c['authorRelationsWithVerifiablePredicateKind'],
   'pairAvailable',c['typePairsMaterializedInReal3D'],
   'nativeSatisfied',c['physicallySatisfiedAuthorRelationsAtLeastRequiredInstances'],
   'contactVerifiedOn',c['nativeContactSupportedOnAuthorClauses'],
   'proximityMatches',c['geometricProximityAuthorClauses'],
   'unverifiedSemanticRelations',c['unsupportedAnnotationRelationKinds'])
