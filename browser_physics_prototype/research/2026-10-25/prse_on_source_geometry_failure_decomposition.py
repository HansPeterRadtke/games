#!/usr/bin/env python3
"""PRSE decisive real-source 'ON' failure-decomposition study.

All three native Rapier source worlds (baseline, +pretrained generic objects,
+existing class-size catalog objects) were FROZEN in prior, gold-blind
GameCore/Rapier runs. This diagnostic opens official SceneEval OORel author
annotations ONLY AFTER those actual physical worlds were saved.

It separates:
  missing supporting-object type,
  missing supported-object type,
  insufficient instance quantity,
  available pair but no box footprint fit,
  nominal box-size-compatible pair (hypothetical, NOT proof of actual contact),
  genuine native Rapier upright top/footprint CONTACT.

The categories 'size-compatible' and 'possible reposition' are NOT physical
success. They are an optimistic geometric upper bound, NOT a gold-driven
placement algorithm and do not mutate any original 3D scene. Actual physical
support is determined exclusively from frozen Rapier contact data.

The SAME source IDs / three frozen methods provide matched source controls,
but these three methods have DIFFERENT object count budgets (938/2048/955);
therefore never claim this is an equal-compute model comparison.

Complete original source/user annotation and per-case results stay private
owner-only on Nitro. Safe aggregates, code, and SHA-256 pointers go to Games.
"""
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
from stat import S_IMODE
import csv,io,json,zipfile,math,random

HERE=Path(__file__).parent
RAW=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-on-feasibility')
OLD=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset')
ZIP=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
RAW.mkdir(parents=True,exist_ok=True,mode=0o700);RAW.chmod(0o700)
def read(p):return json.loads(p.read_text())
def sha(p):return sha256(p.read_bytes()).hexdigest()
assert sha(ZIP)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(ZIP) as z:
 with z.open('annotations.csv') as f:
  authors=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(authors)==500
ids=list(range(100))+list(range(100,500,4))
method={}
for name,expectedN in [('baseline',938),('generic',2048),('catalog',955)]:
 f=OLD/f'prse_post_asset_native_{name}_200_raw_v2.json'
 assert f.is_file() and S_IMODE(f.stat().st_mode)==0o600
 d=read(f)
 assert d['metadata']['sourceIds']==ids
 assert [x['id'] for x in d['rows']]==ids
 assert d['summary']['acceptedNativeBodyScenes']==197
 assert d['summary']['nativePhysicalBodies']==expectedN
 assert d['summary']['failedRebuilds']==0
 method[name]=d
def norm(s):
 k=s.strip().lower().replace(' ','_')
 return {'television':'tv','bunk_bed':'bed','refrigerator':'fridge',
  'bedside_lamp':'lamp'}.get(k,k)
def clauses(row):
 for text in row['OORel'].split(';'):
  values=[v.strip() for v in text.split(',')]
  if len(values)<6 or values[2]!='on':continue
  try:count=int(values[1])
  except ValueError:continue
  op=values[0]
  if op not in ('eq','ge','gt'):continue
  yield {'support':norm(values[4]),'child':norm(values[5]),
   'minCount':count+(op=='gt'), 'op':op,'sourceQuantity':count}
def up_angle(q):
 n=math.sqrt(sum(q[k]**2 for k in ('x','y','z','w')))
 if n<.5:return float('nan')
 return math.acos(max(-1,min(1,1-2*(q['x']**2+q['z']**2)/(n*n))))
def size_ok(support,child):
 if support['id']==child['id']:return False
 return support['shape']=='box' and \
  support['size']['x'] >= child['size']['x']+.02 and \
  support['size']['z'] >= child['size']['z']+.02
def proper_real_contact(support,child,contactPairs):
 if not size_ok(support,child):return False
 if up_angle(support['rotation'])>.10 or up_angle(child['rotation'])>.10:
  return False
 if abs(child['position']['y']-child['size']['y']/2-
        (support['position']['y']+support['size']['y']/2))>.08:return False
 if any(abs(support['position'][ax]-child['position'][ax])+
        child['size'][ax]/2 > support['size'][ax]/2+.03 for ax in ('x','z')):return False
 return frozenset((support['id'],child['id'])) in contactPairs
def fit_without_other_objects(scene,support,child):
 """AABB-only optimistic hypothetical; DOES NOT alter actual GameCore physics."""
 if not size_ok(support,child):return False
 center=support['position']
 wx=(support['size']['x']-child['size']['x'])/2
 wz=(support['size']['z']-child['size']['z'])/2
 others=[e for e in scene if e['id'] not in (support['id'],child['id'])]
 for fx in (0,-.65,.65):
  for fz in (0,-.65,.65):
   proposed={k:center[k] for k in ('x','y','z')}
   proposed['x']+=fx*wx
   proposed['z']+=fz*wz
   proposed['y']+=support['size']['y']/2+child['size']['y']/2+.001
   clear=True
   for other in others:
    if all(abs(proposed[k]-other['position'][k]) <
         (child['size'][k]+other['size'][k])/2-.012 for k in ('x','y','z')):
     clear=False;break
   if clear:return True
 return False

outcomes={m:[] for m in method}
countByMethod={m:Counter() for m in method}
failureTypes={m:{'missingSupport':Counter(),'missingChild':Counter(),
 'sizeMismatch':Counter(),'noRealContact':Counter()} for m in method}
allGoldClauseCount=0;acceptedGoldClauseCount=0
for slot,id in enumerate(ids):
 gold=list(clauses(authors[id]))
 allGoldClauseCount+=len(gold)
 accepted=method['baseline']['rows'][slot]['status']=='native_simulated'
 for name,data in method.items():
  world=data['rows'][slot]
  if not accepted:
   assert world['status']!='native_simulated'
   countByMethod[name]['geometryRejectedSources']+=1
   countByMethod[name]['goldOnUnverifiedRejectedScenes']+=len(gold)
   continue
  assert world['status']=='native_simulated'
  countByMethod[name]['acceptedSources']+=1
  byKind=defaultdict(list)
  for body in world['bodyStates']:byKind[norm(body['kind'])].append(body)
  contacts={frozenset((x['a'],x['b'])) for x in world['nativeContactPairs']}
  for sourceIndex,g in enumerate(gold):
   s,c=g['support'],g['child']
   supports=byKind.get(s,[]);children=byKind.get(c,[])
   necessary=max(1,g['minCount'])
   status='unknown'
   if not supports and not children:status='both_types_missing'
   elif not supports:status='support_type_missing'
   elif not children:status='child_type_missing'
   elif len(children)<necessary:status='insufficient_child_instances'
   else:
    compatible={e['id'] for e in children if
      any(size_ok(parent,e) for parent in supports)}
    available={e['id'] for e in children if
      any(fit_without_other_objects(world['bodyStates'],parent,e)
       for parent in supports)}
    real={e['id'] for e in children if
      any(proper_real_contact(parent,e,contacts) for parent in supports)}
    if len(compatible)<necessary:status='no_sufficient_supported_footprint'
    elif len(available)<necessary:status='nominal_fit_but_no_collision_free_top_position'
    elif len(real)<necessary:status='nominal_reposition_possible_but_no_real_support'
    else:status='real_native_supported'
   # Score important bounds irrespective of primary hierarchical failure.
   compatibility={e['id'] for e in children if any(size_ok(parent,e)
     for parent in supports)}
   topPotential={e['id'] for e in children if any(
     fit_without_other_objects(world['bodyStates'],parent,e)
     for parent in supports)}
   realSupported={e['id'] for e in children if any(
     proper_real_contact(parent,e,contacts) for parent in supports)}
   row={'sourceId':id,'subset':'human' if id<100 else 'assisted',
    'clauseIndex':sourceIndex,'sourceSupportKind':s,'sourceChildKind':c,
    'authorMinContactedChildCount':necessary,
    'actualSupportTypeBodies':len(supports),
    'actualChildTypeBodies':len(children),
    'sizeCompatibleDistinctChildBodies':len(compatibility),
    'optimisticNonOverlappingTopCandidateChildren':len(topPotential),
    'actualRapierNativeSupportDistinctChildBodies':len(realSupported),
    'sourceOnSupportedByActualNativeContacts':len(realSupported)>=necessary,
    'typeClassesPresent':bool(supports) and bool(children),
    'sameSourceTypeClauseWithEnoughAvailableInstances':
       bool(supports) and len(children)>=necessary,
    'status':status}
   outcomes[name].append(row)
   tally=countByMethod[name]
   tally['goldAuthorOnClausesChecked']+=1
   tally[status]+=1
   tally['bothTypesPresent']+=int(row['typeClassesPresent'])
   tally['sufficientQuantityForRequiredChildInstances']+=int(
     row['sameSourceTypeClauseWithEnoughAvailableInstances'])
   tally['sufficientSizeCompatibleExistingChildInstances']+=int(
     len(compatibility)>=necessary)
   tally['sufficientHypotheticalUnoccupiedAABBTopPositions']+=int(
     len(topPotential)>=necessary)
   tally['confirmedNativeContactAndSupportRequirements']+=int(
     row['sourceOnSupportedByActualNativeContacts'])
   tally['childInstancesInGoldClauses']+=necessary
   if not supports:failureTypes[name]['missingSupport'][s]+=1
   if not children:failureTypes[name]['missingChild'][c]+=1
   if supports and children and len(compatibility)<necessary:
    failureTypes[name]['sizeMismatch'][(s,c)]+=1
   if len(topPotential)>=necessary and len(realSupported)<necessary:
    failureTypes[name]['noRealContact'][(s,c)]+=1
 if accepted:acceptedGoldClauseCount+=len(gold)
assert acceptedGoldClauseCount==354,(acceptedGoldClauseCount,'Expected previous independently annotated source on cohort')
assert all(v['goldAuthorOnClausesChecked']==354 for v in countByMethod.values())
assert all(v['confirmedNativeContactAndSupportRequirements']==3 for v in countByMethod.values()),{
 k:v['confirmedNativeContactAndSupportRequirements'] for k,v in countByMethod.items()}

# Previously confirmed optimistic native physical scorer must match EXACT
# count. The semantics here are more conservative on quaternion yaw than old
# full rotation, yet all official supported "on" results should agree.
prior=read(HERE/'prse_post_asset_spatial_relation_gold_200_aggregate_v1.json')
for name in method:
 count=sum(v.get('nativeContactSupportedOnAuthorClauses',0)
    for v in prior['methods'][name].values())
 assert count==countByMethod[name]['confirmedNativeContactAndSupportRequirements']

# Cluster-resample SCENES, not dependent source clauses: confidence intervals
# conditional on old curated SceneEval sample, NOT the full literary domain.
boots={}
for name,rows in outcomes.items():
 sceneIDs=sorted(set(x['sourceId'] for x in rows))
 grouped={id:[x for x in rows if x['sourceId']==id] for id in sceneIDs}
 assert len(sceneIDs)<197 and len(sceneIDs)>30
 rng=random.Random(20261025+{'baseline':1,'generic':2,'catalog':3}[name])
 numbers=[]
 for _ in range(4000):
  sample=[grouped[sceneIDs[rng.randrange(len(sceneIDs))]] for _ in sceneIDs]
  flat=[x for group in sample for x in group]
  n=len(flat)
  if n==0:continue
  numbers.append([
    sum(x['typeClassesPresent'] for x in flat)/n,
    sum(x['actualRapierNativeSupportDistinctChildBodies']>=
        x['authorMinContactedChildCount'] for x in flat)/n,
    sum(x['optimisticNonOverlappingTopCandidateChildren']>=
        x['authorMinContactedChildCount'] for x in flat)/n])
 boots[name]={'sceneClustersWithOnClauses':len(sceneIDs),
    'conditionalBootstrap95ForTypePresent':[sorted(x[0] for x in numbers)[100],sorted(x[0] for x in numbers)[3899]],
    'conditionalBootstrap95ForActualContact':[sorted(x[1] for x in numbers)[100],sorted(x[1] for x in numbers)[3899]],
    'conditionalBootstrap95ForOptimisticUnoccupiedTop':[sorted(x[2] for x in numbers)[100],sorted(x[2] for x in numbers)[3899]]}

summary={name:{
 'physicallyInstantiatedRapierBodies':method[name]['summary']['nativePhysicalBodies'],
 'actualGameCoreNativeObjectContactPairs':method[name]['summary']['actualNativeContactPairs'],
 'goldFailureCategories':dict(countByMethod[name]),
 'mostMissingSupportTypes':failureTypes[name]['missingSupport'].most_common(15),
 'mostMissingChildTypes':failureTypes[name]['missingChild'].most_common(15),
 'conditionalSceneBootstrap95':boots[name]}
 for name in ('baseline','generic','catalog')}
metadata={'source':'Same fixed SceneEval-500 first100 human plus every fourth assisted100 actual frozen physically simulated GameCore/Rapier source descriptions',
 'officialSceneEvalSha256':sha(ZIP),
 'sameSourceIDs':ids,
 'sourceAnnotationsOnlyOpenedPosthoc':True,
 'existingPhysicalStateNeverChanged':True,
 'totalOriginalGoldOnClauses':allGoldClauseCount,
 'originalGoldOnClausesOn197AcceptedNativeScenes':acceptedGoldClauseCount,
 'physicalReality':'Actual native Rapier collider contacts and source-linked body xyz/quaternions read from already frozen physical world runs',
 'criticalLimitation':'AABB dimension fit and hypothetical unoccupied placement are posthoc optimistic physical potential, NEVER contact proof. The three arms have different object budgets. Instance-level author reference identity and real visual asset fidelity are not established.'}
sourceManifest={name:sha(OLD/f'prse_post_asset_native_{name}_200_raw_v2.json')
 for name in ('baseline','generic','catalog')}
payload={'metadata':{**metadata,'frozenPhysicalInputSHA256':sourceManifest},
 'summary':summary,'fullPerCase':outcomes}
raw=RAW/'prse_on_author_source_instance_geometry_200_raw_v1.json'
with raw.open('x') as f:json.dump(payload,f,indent=2);f.write('\n')
raw.chmod(0o600)
public={'metadata':{**metadata,'frozenPhysicalInputSHA256':sourceManifest,
 'privateRawSHA256':sha(raw)},'summary':summary}
pub=HERE/'prse_on_source_geometry_failure_decomposition_v1.json'
with pub.open('x') as f:json.dump(public,f,indent=2);f.write('\n')
for name,one in summary.items():
 print('METHOD',name,'BODIES',one['physicallyInstantiatedRapierBodies'])
 print(' CATEGORIES',one['goldFailureCategories'])
 print(' MISSING_SUPPORT',one['mostMissingSupportTypes'][:8])
 print(' MISSING_CHILD',one['mostMissingChildTypes'][:8])
print('SAVED_CORRECT',pub.name,'PRIVATE_RAW_SHA',sha(raw))
