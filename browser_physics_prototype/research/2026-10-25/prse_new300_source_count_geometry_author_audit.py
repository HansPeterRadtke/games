#!/usr/bin/env python3
"""Post-frozen author source ObjCount versus actual new 300 native GameCore
bodies. Author labels NEVER enter materialization. No author scale/mesh 3D gold
exists here; unverified shapes remain unknown, not physically correct.
"""
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
from stat import S_IMODE
import csv,io,zipfile,json
HERE=Path(__file__).parent
PRIV=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-new-physical-300')
SOURCE=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
RAW=PRIV/'prse_source_only_same_budget_native_300_raw_v1.json'
def digest(p):return sha256(p.read_bytes()).hexdigest()
assert digest(SOURCE)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(RAW.stat().st_mode)==0o600
with zipfile.ZipFile(SOURCE) as z:
 with z.open('annotations.csv') as f: gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
world=json.loads(RAW.read_text())
ids=[i for i in range(100,500) if (i-100)%4!=0]
assert [r['sourceId'] for r in world['rows']]==ids
def canonical(k):
 v=k.lower().replace(' ','_')
 return {'television':'tv','bunk_bed':'bed','refrigerator':'fridge',
   'bedside_lamp':'lamp'}.get(v,v)
def gold_rows(field):
 claims=[]
 for part in field.split(';'):
  f=[x.strip() for x in part.strip().split(',')]
  if len(f)<3:continue
  try:n=int(f[1])
  except ValueError:continue
  if f[0] not in ('eq','ge','gt'):continue
  claims.append({'type':canonical(f[2]),'op':f[0],'num':n,
   'attribute':f[3] if len(f)>3 else None})
 return claims
def correct(op,n,current):
 if op=='eq':return current==n
 if op=='ge':return current>=n
 if op=='gt':return current>n
 return None
def attrEquivalent(a,b):
 x=a.lower().replace(' ','_');y=b.lower().replace(' ','_')
 lookup={'wood':'wooden','gray':'grey','king_size':'king_size','big':'large'}
 return lookup.get(x,x)==lookup.get(y,y)

stat=Counter();cases=[]
for row in world['rows']:
 id=row['sourceId'];claims=gold_rows(gold[id]['ObjCount']);attrs=gold_rows(gold[id]['ObjAttr'])
 stat['descriptions']+=1
 if row['status']!='same_body_real_native_matched':
  stat['objectCountClaimsNotPhysicallyVerified']+=len(claims)
  stat['objectAttributeClaimsNotPhysicallyVerified']+=len(attrs)
  continue
 original=Counter(canonical(x['kind']) for x in row['oldBodyStates'])
 alt=Counter(canonical(x['kind']) for x in row['newBodyStates'])
 assert original==alt,'Source placement must keep all object classes and multiplicities unchanged'
 stat['acceptedScenes']+=1
 stat['physicalBodyInstances']+=len(row['oldBodyStates'])
 for b in row['oldBodyStates']:
  if str(b['source']).startswith('syntax-proposed:'):
   stat['genericFallbackPhysicalBodies']+=1
   if all(abs(b['size'][a]-v)<1e-8 for a,v in (('x',.24),('y',.28),('z',.24))):
    stat['genericFallbackSmallPlaceholderBoxes']+=1
 for claim in claims:
  actual=original[claim['type']];met=correct(claim['op'],claim['num'],actual)
  stat['independentAuthorObjectCountClauses']+=1
  stat['authorObjectCountSatisfied']+=int(met)
  stat['authorObjectCountFailed']+=int(not met)
  stat['missingObjectType']+=int(actual==0 and claim['num']>0)
  stat['underCountWithTypePresent']+=int(actual>0 and claim['num']>actual and claim['op'] in ('eq','ge'))
  stat['overCountWhenExact']+=int(claim['op']=='eq' and actual>claim['num'])
  cases.append({'sourceId':id,'gold':claim,'physicalCount':actual,'satisfied':met})
 stat['authorAttributeClausesOnlyTextOrAppearanceNotPhysicalGold']+=len(attrs)
assert stat['acceptedScenes']==world['summary']['matchedNativeScenarios']
assert stat['physicalBodyInstances']==world['summary']['totalSamePhysicalBodiesPerArm']
assert stat['authorObjectCountSatisfied']+stat['authorObjectCountFailed']==stat['independentAuthorObjectCountClauses']
report={'metadata':{'sourceSHA256':digest(SOURCE),'newNativeRawSHA256':digest(RAW),
 'authorLabelsScoredPostNativeOnly':True,'sourceCorpusPreviouslyStudied':True,
 'bodyCountsSameForBothPhysicalPlacements':True,
 'noPhysicalMeshScalePoseGroundTruth':True,
 'allProvisionalGenericCollidersLackApprovedPhysicalDimensions':True},'total':dict(stat)}
private=PRIV/'prse_new300_author_quantity_percase_v1.json'
with private.open('x') as f:json.dump({'cases':cases},f,indent=2);f.write('\n')
private.chmod(0o600)
report['metadata']['privateGoldPerCaseSHA256']=digest(private)
out=HERE/'prse_new300_source_count_geometry_author_aggregate_v1.json'
with out.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print('NEW300_GOLD_COUNTS',json.dumps(report['total'],sort_keys=True))
