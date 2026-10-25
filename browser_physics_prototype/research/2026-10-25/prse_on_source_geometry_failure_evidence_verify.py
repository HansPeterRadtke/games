#!/usr/bin/env python3
"""Independent, READ-ONLY verification of PRSE real-source ON support bottlenecks.

Baseline/strict existing category/catalog/generic geometry are the EXACT
earlier frozen native GameCore/Rapier scenes, generated WITHOUT seeing
official SceneEval source annotations. This new scorer only checks WHY their
existing physical ON relations fail, using independently supplied gold.

No new gold-informed scene proposal/placement is created. Hypothetical AABB
fit/free-on-top probes are optimistic geometric bounds, NOT actual physically
simulated support, and NOT an equal-body-budget method comparison.

All detailed source-derived per-case data remain owner-private.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
from collections import Counter
import zipfile,csv,io,json,math

HERE=Path(__file__).parent
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
NATIVE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset')
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-on-feasibility')
RAW=PRIVATE/'prse_on_author_source_instance_geometry_200_raw_v1.json'
PUBLIC=HERE/'prse_on_source_geometry_failure_decomposition_v1.json'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert sha(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(PRIVATE.stat().st_mode)==0o700 and S_IMODE(RAW.stat().st_mode)==0o600
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:authors=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(authors)==500
raw=read(RAW);pub=read(PUBLIC)
assert pub['metadata']['privateRawSHA256']==sha(RAW)
assert raw['metadata']['officialSceneEvalSha256']==sha(GOLD)
assert raw['metadata']['sourceAnnotationsOnlyOpenedPosthoc']
assert raw['metadata']['existingPhysicalStateNeverChanged']
assert raw['metadata']['originalGoldOnClausesOn197AcceptedNativeScenes']==354
assert raw['metadata']['totalOriginalGoldOnClauses']==363
assert pub['summary']==raw['summary']
assert pub['metadata']['sameSourceIDs']==list(range(100))+list(range(100,500,4))
ids=pub['metadata']['sameSourceIDs']
initialGold=read(HERE/'prse_post_asset_spatial_relation_gold_200_aggregate_v1.json')
frozen={}
for name,n in [('baseline',938),('generic',2048),('catalog',955)]:
 file=NATIVE/f'prse_post_asset_native_{name}_200_raw_v2.json'
 assert S_IMODE(file.stat().st_mode)==0o600
 assert pub['metadata']['frozenPhysicalInputSHA256'][name]==sha(file)
 frozen[name]=read(file)
 assert frozen[name]['summary']['nativePhysicalBodies']==n
 assert frozen[name]['summary']['acceptedNativeBodyScenes']==197
 assert [v['id'] for v in frozen[name]['rows']]==ids

expected={
 'baseline':{'both_types_missing':126,'child_type_missing':160,
 'support_type_missing':21,'insufficient_child_instances':8,
 'no_sufficient_supported_footprint':2,
 'nominal_fit_but_no_collision_free_top_position':2,
 'nominal_reposition_possible_but_no_real_support':32,
 'real_native_supported':3,
 'bothTypesPresent':47,'sufficientSizeCompatibleExistingChildInstances':37,
 'sufficientHypotheticalUnoccupiedAABBTopPositions':35},
 'generic':{'both_types_missing':12,'child_type_missing':83,
 'support_type_missing':33,'insufficient_child_instances':12,
 'no_sufficient_supported_footprint':72,
 'nominal_fit_but_no_collision_free_top_position':8,
 'nominal_reposition_possible_but_no_real_support':131,
 'real_native_supported':3,
 'bothTypesPresent':226,'sufficientSizeCompatibleExistingChildInstances':142,
 'sufficientHypotheticalUnoccupiedAABBTopPositions':134},
 'catalog':{'both_types_missing':126,'child_type_missing':160,
 'support_type_missing':21,'insufficient_child_instances':8,
 'no_sufficient_supported_footprint':2,
 'nominal_fit_but_no_collision_free_top_position':2,
 'nominal_reposition_possible_but_no_real_support':32,
 'real_native_supported':3,
 'bothTypesPresent':47,'sufficientSizeCompatibleExistingChildInstances':37,
 'sufficientHypotheticalUnoccupiedAABBTopPositions':35}}
names=(
 'both_types_missing','child_type_missing','support_type_missing',
 'insufficient_child_instances','no_sufficient_supported_footprint',
 'nominal_fit_but_no_collision_free_top_position',
 'nominal_reposition_possible_but_no_real_support','real_native_supported')
alias={'television':'tv','bunk_bed':'bed','refrigerator':'fridge','bedside_lamp':'lamp'}
def norm(s):
 s=s.strip().lower().replace(' ','_')
 return alias.get(s,s)
def annotatedSourceON(row):
 result=[]
 for chunk in row['OORel'].split(';'):
  v=[x.strip() for x in chunk.split(',')]
  if len(v)<6 or v[2]!='on':continue
  if v[0] not in ('eq','ge','gt'):continue
  count=int(v[1])+(v[0]=='gt')
  result.append((norm(v[4]),norm(v[5]),max(1,count)))
 return result
countAll=0;countAccepted=0
for slot,id in enumerate(ids):
 gold=annotatedSourceON(authors[id])
 countAll+=len(gold)
 accepted=frozen['baseline']['rows'][slot]['status']=='native_simulated'
 if accepted:countAccepted+=len(gold)
 for name in ('baseline','catalog','generic'):
  rawCases=[r for r in raw['fullPerCase'][name] if r['sourceId']==id]
  if not accepted:
   assert not rawCases,'Rejected physical scene cannot be silently scored as a correct live world'
   continue
  assert len(rawCases)==len(gold)
  for i,(sourceSupport,sourceChild,minCount) in enumerate(gold):
   r=rawCases[i]
   assert r['clauseIndex']==i
   assert (r['sourceSupportKind'],r['sourceChildKind'],r['authorMinContactedChildCount'])==(
    sourceSupport,sourceChild,minCount)
   assert r['status'] in names
   assert r['sourceOnSupportedByActualNativeContacts']==(
    r['actualRapierNativeSupportDistinctChildBodies']>=minCount)
   assert not r['sourceOnSupportedByActualNativeContacts'] or r['typeClassesPresent']
assert countAll==363 and countAccepted==354

for name in ('baseline','generic','catalog'):
 d=pub['summary'][name]['goldFailureCategories']
 assert d['goldAuthorOnClausesChecked']==354
 assert d['acceptedSources']==197
 assert d['geometryRejectedSources']==3
 assert d['goldOnUnverifiedRejectedScenes']==9
 assert d['confirmedNativeContactAndSupportRequirements']==3
 assert sum(d[x] for x in names)==354
 for label,value in expected[name].items():
  assert d[label]==value,(name,label,d.get(label),value)
 assert d['sufficientHypotheticalUnoccupiedAABBTopPositions']>=d['confirmedNativeContactAndSupportRequirements']
 assert d['sufficientSizeCompatibleExistingChildInstances']>=d['sufficientHypotheticalUnoccupiedAABBTopPositions']
 assert d['bothTypesPresent']>=d['sufficientSizeCompatibleExistingChildInstances']
 assert sum(initialGold['methods'][name][group]['nativeContactSupportedOnAuthorClauses']
  for group in ('human','assisted'))==3
 ci=pub['summary'][name]['conditionalSceneBootstrap95']
 assert ci['sceneClustersWithOnClauses']==110
 for key in ('conditionalBootstrap95ForTypePresent',
  'conditionalBootstrap95ForActualContact',
  'conditionalBootstrap95ForOptimisticUnoccupiedTop'):
  lo,hi=ci[key]
  assert 0<=lo<=hi<=1

goldQuantities=read(HERE/'prse_source_quantity_official_gold_200_aggregate_v1.json')['combined']
assert goldQuantities['goldCountClauses']==1237
assert goldQuantities['goldCountSatisfiedByPhysicalWorld']==565
assert goldQuantities['goldCountContradictedByPhysicalWorld']==672

out={'source':{
 'officialSceneEvalSourceSHA256':sha(GOLD),
 'threeAlreadyFrozenNativeGameCoreRapierSceneSHA256':pub['metadata']['frozenPhysicalInputSHA256'],
 'posthocSourceONAuthorAnnotationsOnly':True,
 'sourceIDs':ids,
 'samePhysicalSceneSamplesButNotSameObjectBudget':True,
 'allAuthorSourceONClauses':363,
 'acceptedPhysicalSceneGoldONClauses':354,
 'unverifiedSourceGoldONOnThreeOriginalRejectedScenes':9},
 'verifiedMetrics':pub['summary'],
 'nativeSupportedONAcrossEveryMethod':3,
 'baselineToGenericBothKindsPresentChange':226-47,
 'genericSupportSizeMismatchCount':72,
 'genericNominalUnoccupiedTopButNeverRealizedCount':131,
 'sourceCountIndependentNegativeStill565of1237':True,
 'caveat':'Do not reinterpret hypothetical AABB-fitting unoccupied top positions as actual physics successes. Counts are source-type pair optimistic and uncalibrated generic boxes do not provide realistic furniture, container geometry, or human source entailment.',
 'exactOwnerPrivateRawSHA256':sha(RAW)}
manifest=HERE/'prse_on_source_geometry_failure_evidence_manifest_v1.json'
if manifest.exists():assert read(manifest)==out,'Refusing to overwrite different original evidence'
else:
 with manifest.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED 354 independent original authored source ON clauses across 197 actual Rapier scenes, 9 unverified on 3 rejected scenes.')
print('VERIFIED baseline failure categories: 307 missing at least one type, 35 unoccupied top hypothetically possible, only 3 truly supported.')
print('VERIFIED 1110 extra generic real bodies: 226 category pairs present, 72 size mismatch, 131 nominally unoccupied yet not really supported, actual contact stays 3.')
print('VERIFIED strict catalog extra17 bodies leaves original source ON results unchanged; provenance SHA and old negative-controls preserved.')
