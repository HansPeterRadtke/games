#!/usr/bin/env python3
"""Independent, READ-ONLY evidence verification for the actual PRSE native
GameCore/Rapier scene spatial relationships after open-vocabulary noun
augmentation versus strict existing 3D geometry catalog.

Source/gold separation: 197 native physical scenes, 3 method arms and contacts
frozen before official SceneEval OORel labels were opened by a separate scorer.
A first research-only replay failed due wrong assisted-source index mapping;
preserve its v1 negative results, never reclassify as a physics failure.

This verifier requires the complete original source/raw evidence under owner-
private Nitro paths. Git contains source code, safe aggregates and source SHA.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
from collections import Counter
import csv,io,json,zipfile,subprocess
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
QUANTITY=R/'prse_spacy_open_vocab_native_gold_200_aggregate_v1.json'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def data(p):return json.loads(p.read_text())
assert digest(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(P.stat().st_mode)==0o700
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
ids=list(range(100))+list(range(100,500,4))
assert len(ids)==200 and [int(gold[i]['ID']) for i in ids]==ids
assert data(QUANTITY)['total']['augmentedGoldClausesMatched']==972
frozenSource=data(BASE)['proposalsAll500']
manifest={}
expectedV1={
 'baseline':{'accepted':197,'failed':0,'bodies':938,'contacts':11},
 'generic':{'accepted':126,'failed':71,'bodies':1004,'contacts':3},
 'catalog':{'accepted':193,'failed':4,'bodies':926,'contacts':9}}
expectedV2={
 'baseline':{'accepted':197,'failed':0,'bodies':938,'contacts':11,'new':0},
 'generic':{'accepted':197,'failed':0,'bodies':2048,'contacts':11,'new':1110},
 'catalog':{'accepted':197,'failed':0,'bodies':955,'contacts':11,'new':17}}
for version in ('v1','v2'):
 for method in ('baseline','generic','catalog'):
  file=P/f'prse_post_asset_native_{method}_200_raw_{version}.json'
  assert file.exists() and S_IMODE(file.stat().st_mode)==0o600
  raw=data(file)
  assert raw['metadata']['sourceIds']==ids
  assert [x['id'] for x in raw['rows']]==ids
  metrics=raw['summary']
  expected=expectedV1[method] if version=='v1' else expectedV2[method]
  assert metrics['acceptedNativeBodyScenes']==expected['accepted']
  assert metrics['failedRebuilds']==expected['failed']
  assert metrics['nativePhysicalBodies']==expected['bodies']
  assert metrics['actualNativeContactPairs']==expected['contacts']
  if version=='v2':
   assert metrics['provisionalAddedBodies']==expected['new']
   assert metrics['sourceTextStillHasSameHash']
   for row in raw['rows']:
    if row['status']!='native_simulated':continue
    assert row['originalLiterarySourceHash']==sha256(
      frozenSource[row['id']]['text'].encode('utf-8')).hexdigest()
    assert row['realBodies']==len(row['bodyStates'])
    assert row['nativeContactPairs'] is not None
    for contact in row['nativeContactPairs']:
     idsNow={x['id'] for x in row['bodyStates']}
     assert contact['a'] in idsNow and contact['b'] in idsNow and contact['contactPointCount']>0
  manifest[file.name]={'sha256':digest(file),'bytes':file.stat().st_size,
    'ownerPrivate':True}
# Verify both frozen public method-summary manifests.
for version in ('v1','v2'):
 pub=data(R/f'prse_post_asset_relation_input_200_aggregate_{version}.json')
 assert len(pub['methods'])==3
 for x in pub['methods']:
  k=x['summary']['method']
  assert x['privateRawSHA256']==manifest[f'prse_post_asset_native_{k}_200_raw_{version}.json']['sha256']
  assert x['summary']==(data(P/f'prse_post_asset_native_{k}_200_raw_{version}.json'))['summary']
# The v1 failure is an ORIGINAL RESEARCH REPRODUCER source-index bug,
# NOT evidence that external assisted source physics failed.
old=data(P/'prse_post_asset_native_generic_200_raw_v1.json')
assert sum(x['status']=='failed' for x in old['rows'])==71
assert all('Invalid original source mention evidence' in x['error'] for x in old['rows'] if x['status']=='failed')
new=data(P/'prse_post_asset_native_generic_200_raw_v2.json')
assert all(x['status']!='failed' for x in new['rows'])
# Independent gold opens ONLY here and separate scorer, NEVER native scene generator.
official=R/'prse_post_asset_spatial_relation_gold_200_aggregate_v1.json'
assert official.exists()
scored=data(official)
assert scored['metadata']['officialSceneEvalZIPSHA256']==digest(GOLD)
assert scored['metadata']['physicallyFrozenSourceIDs']==ids
assert scored['metadata']['labelsOnlyOpenedAfterNativePhysicsReconstruction'] is True
audit=P/'prse_post_asset_spatial_relation_gold_200_raw_v1.json'
assert S_IMODE(audit.stat().st_mode)==0o600
assert scored['metadata']['privateFullAuthorGoldAuditSHA256']==digest(audit)
for method in ('baseline','generic','catalog'):
 assert scored['metadata']['privateMethodNativeRawHashes'][method]==manifest[f'prse_post_asset_native_{method}_200_raw_v2.json']['sha256']
expected={
 'baseline':{'all':911,'testable':512,'pair':95,'satisfied':18,'nativeOn':3,'near':15},
 'generic':{'all':911,'testable':512,'pair':335,'satisfied':33,'nativeOn':3,'near':30},
 'catalog':{'all':911,'testable':512,'pair':99,'satisfied':18,'nativeOn':3,'near':15}}
for method,splits in scored['methods'].items():
 total=Counter()
 for name,group in splits.items():
  total.update(group)
  assert group['acceptedSourceScenes']==(98 if name=='human' else 99)
  assert group['unsupportedAnnotationRelationKinds']+group['authorRelationsWithVerifiablePredicateKind']==group['allOfficialAuthorObjectRelations']
 metrics=expected[method]
 assert total['allOfficialAuthorObjectRelations']==metrics['all']
 assert total['authorRelationsWithVerifiablePredicateKind']==metrics['testable']
 assert total['typePairsMaterializedInReal3D']==metrics['pair']
 assert total['physicallySatisfiedAuthorRelationsAtLeastRequiredInstances']==metrics['satisfied']
 assert total['nativeContactSupportedOnAuthorClauses']==metrics['nativeOn']
 assert total['geometricProximityAuthorClauses']==metrics['near']
 assert total['unsupportedAnnotationRelationKinds']==399
 # Critically DO NOT mistake a 3D AABB proximity match for source-driven
 # intended spatial layout when placeholders are distributed on a grid.
 assert metrics['satisfied']==metrics['nativeOn']+metrics['near']
bootstrap=data(R/'prse_post_asset_spatial_paired_uncertainty_v1.json')
for group,baseline,augmented,strict,on in [('human',11,14,11,2),('assisted',7,19,7,1)]:
 r=bootstrap['byGroup'][group]
 assert (r['baselineNativeSatisfied'],r['genericNativeSatisfied'],r['catalogNativeSatisfied'],
   r['baselineOnWithActualContact'],r['genericOnWithActualContact'])==(baseline,augmented,strict,on,on)
 assert r['sceneBootstrap95Difference'][0] <= r['pairedConditionalRecallDifference'] <= r['sceneBootstrap95Difference'][1]
 assert r['zeroSupportContactGain']
# Existing Games asset index is explicitly CC0 sprite artwork, not a
# 3D interactive mesh library.
asset=R.parent.parent/'generated/semantic-asset-manifest.json'
if not asset.exists():asset=R.parents[2]/'generated/semantic-asset-manifest.json'
m=data(asset)
assert m.get('license')=='CC0'
selection=m['selection']
assert selection and all(
  r['artifact']['path'].lower().endswith(('.png','.webp','.jpg','.jpeg'))
  for r in selection.values() if isinstance(r,dict) and 'artifact' in r)
# Verify this RESEARCH checkout has no tracked glTF/GLB/OBJ meshes; cannot
# extrapolate to all personal 3D projects outside the Games repo.
tracked=subprocess.run(['git','ls-files'],text=True,capture_output=True,check=True).stdout.splitlines()
meshTypes={'.glb','.gltf','.fbx','.obj','.stl','.blend','.dae','.usd','.usdz'}
trackedMeshes=[f for f in tracked if Path(f).suffix.lower() in meshTypes]
assert not trackedMeshes

out={'metadata':{
 'sceneEvalSHA256':digest(GOLD),
 'frozenSourceProposalsSHA256':digest(BASE),
 'inputOfficialAnnotationOnlyAfterPhysicalOutput':True,
 'artifactScope':'Only existing Games repository tracked asset manifest; not all other machines/pipelines',
 'schemaCaveats':'Gold annotation relation type-pair existence; three-dimensional AABB current poses and actual native Rapier contacts; instance identity/direction/asset realism not independently proven',
 'confidenceCaveats':'Near may match source author type-pairs by coincidence; most directional/containment/orientation types explicitly abstained',
 'researchOriginalFailure':'First v1 assisted index mismatch retained as test/reproducer error, not physics failure',
 'noSharedModelGPUorProductionEffects':True},
 'authorGoldSupportedPredicates':expected,
 'genuinelyPhysicsContactingGoldOnClausesUnchanged':3,
 'strictCatalogSupportedGoldRelationsUnchanged':18,
 'accidentalNearMatchRisk':True,
 'trackedGames3DMeshFiles':len(trackedMeshes),
 'GamesManifestSelectionKinds':len(selection),
 'nativeRawAndIndependentGoldManifest':manifest,
 'privateGoldAuditRaw':{'sha256':digest(audit),'bytes':audit.stat().st_size},
 'pairedSceneBootstrap':bootstrap['byGroup']}
dest=R/'prse_post_asset_spatial_relation_evidence_manifest_v1.json'
if dest.exists():assert data(dest)==out,'Refusing to overwrite differently grounded research result'
else:
 with dest.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('Verified original v1 assisted-source index reproducer error preserved and corrected v2 frozen.')
print('Verified three 197-source actual native GameCore physics worlds and collider contacts.')
print('Verified official SceneEval 911 object relations, 512 testable predicate kinds, baseline/generic/catalog source-type satisfied 18/33/18.')
print('Verified exactly 3 source ON constraints with actual native Rapier collider contacts in ALL THREE arms.')
print('Verified extra 15 spatial matches are proximity only; 399 source relation kinds require separate geometry/orientation/containment semantics.')
print('Verified Games tracked asset selection is 2D sprite images, no tracked interactive 3D mesh files.')
