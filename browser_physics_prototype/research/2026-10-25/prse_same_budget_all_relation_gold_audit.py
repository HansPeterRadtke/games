#!/usr/bin/env python3
"""Independent SceneEval author gold OORel scorer for unchanged source/ID/body
budget: baseline generic vs deterministic lexical ON placement vs pretrained
grammar ON placement on SAME 197 externally sourced native Rapier worlds.

Frozen native GameCore/Rapier bodies/poses/contacts are loaded read-only.
Official author gold only opened AFTER all physical runs frozen. Test every
ON / NEAR / NEXT source clause whose spatial meaning is supported by the
existing limited native bounding-box/contact evaluator. Other semantic kinds
must ABSTAIN; never call them correct or false.

This catches possible sacrifice of nearby author relations when an object
is moved to satisfy an ON constraint. Type-only optimistic existential source
matching remains insufficient for exact persistent instance coreference.
"""
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
from stat import S_IMODE
import csv,io,json,zipfile,math,random

R=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-only-placement')
PREV=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_generic_200_raw_v2.json')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert sha(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
for p in [PREV,PRIVATE/'prse_source_only_nounchunk_same_budget_native_200_raw_v2.json',
 PRIVATE/'prse_source_only_nounchunk_same_budget_native_200_raw_v3.json']:
 assert p.exists() and S_IMODE(p.stat().st_mode)==0o600
data={
 'baseline':read(PREV)['rows'],
 'pretrained':read(PRIVATE/'prse_source_only_nounchunk_same_budget_native_200_raw_v2.json')['rows'],
 'lexical':read(PRIVATE/'prse_source_only_nounchunk_same_budget_native_200_raw_v3.json')['rows']}
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
ids=list(range(100))+list(range(100,500,4))
alias={'television':'tv','bunk_bed':'bed','bedside_lamp':'lamp','refrigerator':'fridge'}
def norm(s):
 k=s.strip().lower().replace(' ','_')
 return alias.get(k,k)
relations={
 'on':'on',
 'near':'near','nearby':'near','close_to':'near',
 'next_to':'next','next':'next','beside':'next','adjacent':'next','side_by_side':'next'
}
def official(row):
 for clause in row['OORel'].split(';'):
  p=[x.strip() for x in clause.split(',')]
  if len(p)<6 or p[0] not in ('eq','ge','gt'):continue
  try:num=int(p[1])
  except ValueError:continue
  yield {'type':relations.get(p[2]),'rawType':p[2], 'a':norm(p[4]),'b':norm(p[5]),
   'min':max(1,num+(1 if p[0]=='gt' else 0))}
def angle(b):
 q=b['rotation'];n=math.hypot(q['x'],q['y'],q['z'],q['w'])
 return math.acos(max(-1,min(1,1-2*(q['x']**2+q['z']**2)/(n*n))))
def gap(a,b):
 return math.sqrt(sum(max(0,abs(a['position'][k]-b['position'][k])-
  (a['size'][k]+b['size'][k])/2)**2 for k in ('x','y','z')))
def support(parent,child,pairs):
 if parent['id']==child['id'] or parent['shape']!='box' or angle(parent)>.1 or angle(child)>.1:return False
 if abs(child['position']['y']-child['size']['y']/2-
  (parent['position']['y']+parent['size']['y']/2))>.08:return False
 if any(abs(child['position'][k]-parent['position'][k])+child['size'][k]/2>
         parent['size'][k]/2+.03 for k in ('x','z')):return False
 return frozenset([parent['id'],child['id']]) in pairs
def witnesses(ty,aa,bb,bodies,pairs):
 grouped=defaultdict(list)
 for body in bodies:grouped[norm(body['kind'])].append(body)
 witnesses=set()
 for a in grouped[aa]:
  for b in grouped[bb]:
   if a['id']==b['id']:continue
   if ty=='on' and support(a,b,pairs):witnesses.add(b['id'])
   elif ty in ('near','next') and gap(a,b)<=(1.5 if ty=='near' else 1.1):
    witnesses.add(b['id'])
 return len(witnesses)
def bodyAndContacts(row,method):
 if method=='baseline':return row['bodyStates'],row['nativeContactPairs']
 return row['bodyStates'],row['nativeContactPairs']
metrics={name:{name2:Counter() for name2 in ('human','assisted')} for name in data}
cases=[]
for k,id in enumerate(ids):
 current={method:entries[k] for method,entries in data.items()}
 if current['baseline']['status']!='native_simulated':
  assert all(current[p]['status']=='original_scene_not_physically_accepted' for p in ['lexical','pretrained'])
  continue
 assert all(current[m]['status']=='source_only_native_gamecore_verified' for m in ('lexical','pretrained'))
 oldIDs={x['id'] for x in current['baseline']['bodyStates']}
 assert all({x['id'] for x in current[m]['bodyStates']}==oldIDs for m in ('lexical','pretrained'))
 for constraint in official(gold[id]):
  one={'sourceId':id,'group':'human' if id<100 else 'assisted',
    'relation':constraint,'physicallySupportedByMethod':{}}
  for method in data:
   tally=metrics[method][one['group']]
   tally['allAuthorObjectObjectClauses']+=1
   ty=constraint['type']
   if ty is None:
    tally['unsupportedKindsHeldUnknown']+=1
    one['physicallySupportedByMethod'][method]=None
    continue
   tally['testableAuthorClauses']+=1
   body,pair=bodyAndContacts(current[method],method)
   contactSet={frozenset((r['a'],r['b'])) for r in pair if r.get('contactPointCount',0)>0}
   n=witnesses(ty,constraint['a'],constraint['b'],body,contactSet)
   success=n>=constraint['min']
   one['physicallySupportedByMethod'][method]=success
   tally['physicallyConfirmed']+=int(success)
   tally['physicallyNotConfirmed']+=int(not success)
   tally[ty+'_sourceClauses']+=1
   tally[ty+'_confirmed']+=int(success)
  cases.append(one)
by={}
for method in data:
 total=Counter()
 for subset in ('human','assisted'):total.update(metrics[method][subset])
 by[method]=dict(total)
 assert total['testableAuthorClauses']==512
 assert total['unsupportedKindsHeldUnknown']==399
 assert total['on_sourceClauses']==354
 assert total['allAuthorObjectObjectClauses']==911
assert by['baseline']['on_confirmed']==by['lexical']['on_confirmed']==3
assert by['pretrained']['on_confirmed']==11
assert by['baseline']['physicallyConfirmed']==33

# New source relationship matches and losses on SAME 512 testable author clauses.
matched=Counter()
for row in cases:
 s=row['physicallySupportedByMethod']
 if s['baseline'] is None:continue
 if s['pretrained'] and not s['baseline']:matched['pretrainedGained']+=1
 if s['baseline'] and not s['pretrained']:matched['pretrainedLost']+=1
 if s['lexical'] and not s['baseline']:matched['lexicalGained']+=1
 if s['baseline'] and not s['lexical']:matched['lexicalLost']+=1
 for p in ('baseline','lexical','pretrained'):matched[p+'Supported']+=int(s[p])
# Source-level paired-cluster resampling, not independent annotation claims.
bootstrap={}
for subset in ('human','assisted'):
 sourceRows=defaultdict(list)
 for r in cases:
  if r['group']==subset and r['physicallySupportedByMethod']['baseline'] is not None:
   sourceRows[r['sourceId']].append(r)
 names=sorted(sourceRows)
 assert len(names)>20
 rng=random.Random(20261025+(10 if subset=='human' else 39))
 deltas=[]
 for _ in range(4000):
  draw=[sourceRows[names[rng.randrange(len(names))]] for x in names]
  entries=[v for item in draw for v in item]
  n=len(entries)
  delta=sum(int(v['physicallySupportedByMethod']['pretrained'])-
            int(v['physicallySupportedByMethod']['baseline']) for v in entries)
  deltas.append(delta/n if n else 0)
 deltas.sort()
 bootstrap[subset]={'physicalSourceSceneClustersWithTestableRelations':len(names),
 'observedImprovementOnTestableRelations':(
  by['pretrained'] if False else
  (metrics['pretrained'][subset]['physicallyConfirmed']-
   metrics['baseline'][subset]['physicallyConfirmed'])/
  metrics['pretrained'][subset]['testableAuthorClauses']),
 'conditionalScenePairedBootstrap95':[deltas[100],deltas[3899]],
 'previouslyExaminedSceneCorpusNotFreshHoldout':True}
out={'metadata':{
 'officialSceneEvalSHA256':sha(GOLD),
 'priorSourceNativeControlSHA256':sha(PREV),
 'lexicalFrozenNativeSHA256':sha(PRIVATE/'prse_source_only_nounchunk_same_budget_native_200_raw_v3.json'),
 'pretrainedFrozenNativeSHA256':sha(PRIVATE/'prse_source_only_nounchunk_same_budget_native_200_raw_v2.json'),
 'allModelAndPhysicalHypothesesAlreadyFrozenBeforeGoldScoring':True,
 'sameNativePhysicalBodyCountsAcrossMethods':2048,
 'sourceDirectionCaveat':'ON first annotated object is support substrate, second is child. Type-pair only optimistic.',
 'proximityCaveat':'NEAR/NEXT matches can occur by coincidence from the grid; physical support requires real Rapier contacts',
 'unhandledLabels':'Other 399 author relation kinds withheld as unknown, not negatives',
 'sourceAssetCaveat':'Pretrained noun-expanded bodies are generic 3D physics boxes with unverified real object shapes and sizes; this score is not general literary fidelity'},
 'methods':{m:{s:dict(c) for s,c in splits.items()} for m,splits in metrics.items()},
 'combined':by,'matchedDifferences':dict(matched),
 'sourceClusteredPairedUncertainty':bootstrap}
priv=PRIVATE/'prse_all_rapier_real_author_relations_postgold_200_raw_v1.json'
with priv.open('x') as f:json.dump({'metadata':out['metadata'],'cases':cases},f,indent=2);f.write('\n')
priv.chmod(0o600)
out['metadata']['privatePerCaseGoldSHA256']=sha(priv)
pub=R/'prse_same_budget_on_all_source_relations_gold_200_aggregate_v1.json'
with pub.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for method in data:print('METHOD',method,by[method])
print('PAIRED_GAIN_LOSS',dict(matched))
print('PAIRED_SCENE_BOOTSTRAP',bootstrap)
