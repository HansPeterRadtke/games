#!/usr/bin/env python3
"""Post-frozen independent author-label audit of open-vocabulary nouns allowed
ONLY when the existing PRSE geometry catalog already has a physical size class.

The complete 197-source native GameCore/Rapier worlds and source provenance
were generated/saved WITHOUT SceneEval author annotations. This scorer is a
separate post hoc audit and does not mutate that physical production.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import csv,io,zipfile,json,stat
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance/prse_source_quantity_physics_200_raw_v1.json')
NATIVE=P/'prse_spacy_open_vocab_catalog_native_200_raw_v1.json'
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert NATIVE.is_file() and stat.S_IMODE(NATIVE.stat().st_mode)==0o600
assert sha(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
b=read(BASE)['results'];n=read(NATIVE)['results']
ids=list(range(100))+list(range(100,500,4))
assert [r['sourceId'] for r in n]==[r['sourceID'] for r in b]==ids
def label(t):
 x=t.lower().strip().replace(' ','_')
 return {'television':'tv','refrigerator':'fridge','bunk_bed':'bed','bedside_lamp':'lamp'}.get(x,x)
def parses(s):
 for text in s.split(';'):
  parts=[x.strip() for x in text.split(',')]
  if len(parts)<3:continue
  try:amount=int(parts[1])
  except ValueError:continue
  if parts[0] in ('eq','ge','gt'):yield label(parts[2]),parts[0],amount
def matches(x,op,y):
 return x==y if op=='eq' else x>=y if op=='ge' else x>y
splits={'human':Counter(),'assisted':Counter()}
detailed=[]
for sourceID,old,new in zip(ids,b,n):
 group='human' if sourceID<100 else 'assisted';r=splits[group]
 r['originalScenes']+=1
 if new['status']!='accepted_native_3d_reentered':
  r['unaccepted']+=1
  r['unverifiedSourceCounts']+=len(list(parses(gold[sourceID]['ObjCount'])))
  continue
 assert old['status']=='native_3d_verified'
 base={label(x['type']):x['materialized'] for x in old['physicalTypeCounts']}
 alt={label(k):v for k,v in new['afterNativePhysicalCount'].items()}
 assert all(alt.get(k,0)>=v for k,v in base.items())
 r['accepted']+=1;r['actualNewCatalogBodies']+=new['addedActualNativeBodies']
 r['newCategories']+=len(set(c['kind'] for c in new['retainedCategories']))
 goldClaims=list(parses(gold[sourceID]['ObjCount']))
 changed=0
 for typ,op,amt in goldClaims:
  before=matches(base.get(typ,0),op,amt)
  after=matches(alt.get(typ,0),op,amt)
  r['independentlyAuthorAnnotatedCountClauses']+=1
  r['baselineMatches']+=before
  r['catalogMatches']+=after
  r['newlyMatchedAuthorCountClauses']+=(not before and after)
  r['previouslyCorrectNowWrong']+=(before and not after)
  changed+=(not before and after)
 detailed.append({'id':sourceID,'sourceLabels':goldClaims,'baselineCounts':base,
  'catalogCounts':alt,'sourceGenericCandidateAdds':new['retainedCategories'],
  'newMatches':changed})
tot=Counter()
for x in splits.values():tot.update(x)
raw=P/'prse_spacy_open_vocab_catalog_postgold_cases_v1.json'
with raw.open('x') as f:json.dump({'context':'Independent author annotation audit after source+native geometry catalog arm frozen',
 'cases':detailed},f,indent=2);f.write('\n')
raw.chmod(0o600)
out={'metadata':{
 'officialSceneEvalSha256':sha(GOLD),
 'frozenCatalogNativeResultSha256':sha(NATIVE),
 'frozenOriginalNativeResultSha256':sha(BASE),
 'privatePostGoldCaseSha256':sha(raw),
 'onlyExistingPRSECategoryGeometry':True,
 'noSourceAnnotationInParserOrPhysicalSceneConstruction':True,
 'stillNotValidated3DRenderableAssetsOrAllObjectShapes':True},
 'splits':{k:dict(v) for k,v in splits.items()},'total':dict(tot)}
with (R/'prse_spacy_open_vocab_catalog_gold_200_aggregate_v1.json').open('x') as f:
 json.dump(out,f,indent=2);f.write('\n')
for k,v in splits.items():
 print(k,'baseGold',v['baselineMatches'],'catalogGold',v['catalogMatches'],
 'newCorrect',v['newlyMatchedAuthorCountClauses'],'bodies',v['actualNewCatalogBodies'])
print('TOTAL',dict(tot))
