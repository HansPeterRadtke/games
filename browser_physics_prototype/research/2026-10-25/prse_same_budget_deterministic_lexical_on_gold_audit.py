#!/usr/bin/env python3
"""Independent source-author OORel scorer for ALREADY FROZEN deterministic lexical 3D
placement candidates in the SAME physical-body budget.

The frozen deterministic source ON relations and alternative native Rapier
scenes were completed WITHOUT SceneEval author gold. This scorer alone reads
the original external author OORel annotations and tests actual native
contact+upright+footprint. Gold never controls positions or selection.

Baseline: exact earlier frozen generic scene, same 197 accepted source IDs,
same 2,048 real native bodies as alternative. A hit is supported only by an
ACTUAL solver contact manifold, not nominal supportId or a source string.

This is an exposed benchmark and generic rigid-box model, NOT guaranteed
semantic entailment, correct asset shape/scale or independent future-domain
population accuracy. Report all lost and gained real gold contacts and
unannotated new contact pairs.
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter,defaultdict
from stat import S_IMODE
import json,zipfile,csv,io,math,random
ROOT=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-only-placement')
OLD=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_generic_200_raw_v2.json')
MODEL=PRIVATE/'prse_source_only_on_nounchunk_200_raw_v1.json'
NEW=PRIVATE/'prse_source_only_nounchunk_same_budget_native_200_raw_v3.json'
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert digest(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (OLD,MODEL,NEW))
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
ids=list(range(100))+list(range(100,500,4))
prior=load(OLD)['rows'];alt=load(NEW)['rows'];grammar=load(MODEL)['cases']
assert [x['id'] for x in prior]==[x['sourceId'] for x in alt]==[x['sourceId'] for x in grammar]==ids
def norm(s):
 k=s.lower().strip().replace(' ','_')
 return {'television':'tv','refrigerator':'fridge','bunk_bed':'bed','bedside_lamp':'lamp'}.get(k,k)
def sourceON(row):
 result=[]
 for part in row['OORel'].split(';'):
  v=[x.strip() for x in part.split(',')]
  if len(v)<6 or v[2]!='on' or v[0] not in ('eq','ge','gt'):continue
  n=int(v[1])+(1 if v[0]=='gt' else 0)
  result.append({'support':norm(v[4]),'child':norm(v[5]),
   'minChildren':max(1,n),'operator':v[0]})
 return result
def tilt(q):
 n=math.hypot(q['x'],q['y'],q['z'],q['w'])
 if n<.5:return math.pi
 return math.acos(max(-1,min(1,1-2*(q['x']*q['x']+q['z']*q['z'])/(n*n))))
def realON(bodies,pairs,parent,child):
 by=defaultdict(list)
 for e in bodies:by[norm(e['kind'])].append(e)
 touching={frozenset((e['a'],e['b'])) for e in pairs if e.get('contactPointCount',e.get('contactCount',0))>0}
 matched=set()
 for support in by[parent]:
  for item in by[child]:
   if item['id']==support['id'] or support['shape']!='box':continue
   if tilt(support['rotation'])>.10 or tilt(item['rotation'])>.10:continue
   if any(abs(item['position'][axis]-support['position'][axis])+item['size'][axis]/2>
          support['size'][axis]/2+.03 for axis in ('x','z')):continue
   if abs((item['position']['y']-item['size']['y']/2)-
          (support['position']['y']+support['size']['y']/2))>.08:continue
   if frozenset((support['id'],item['id'])) not in touching:continue
   matched.add(item['id'])
 return len(matched)
splits={'human':Counter(),'assisted':Counter()};rows=[]
for index,id in enumerate(ids):
 older,newer=prior[index],alt[index]
 group='human' if id<100 else 'assisted'
 s=splits[group];s['sourceDescriptions']+=1
 goldClaims=sourceON(gold[id])
 if older['status']!='native_simulated':
  assert newer['status']=='original_scene_not_physically_accepted'
  s['goldOnUnverifiedOriginalRejectedSource']+=len(goldClaims);continue
 assert newer['status']=='source_only_native_gamecore_verified',(id,newer.get('error'),newer['status'])
 oldIDs={x['id'] for x in older['bodyStates']}
 newIDs={x['id'] for x in newer['bodyStates']}
 assert oldIDs==newIDs
 assert older['realBodies']==newer['nativeBodyCount']
 assert newer.get('status')=='source_only_native_gamecore_verified'
 assert newer['nativeSaveContactIDsPreserved'] and newer['nativeSaveBodyCountPreserved']
 s['acceptedSameBudgetNativeWorlds']+=1
 s['actualOriginalNativeBodyCount']+=older['realBodies']
 s['actualAlternativeNativeBodyCount']+=newer['nativeBodyCount']
 s['actualOldContactPairs']+=len(older['nativeContactPairs'])
 s['actualNewContactPairs']+=len(newer['nativeContactPairs'])
 s['sourceOnlyProposedOnRelations']+=len(newer['attempts'])
 s['sourceOnlyActuallyPositionedRelations']+=newer['movedExistingBodyCount']
 s['newSourceOnlyPairActuallyContacted']+=newer['actualNewSourceAttachmentContactPairs']
 labels={ (v['support'],v['child']) for v in goldClaims}
 for attempt in newer['attempts']:
  if attempt['status']!='nominally_valid_prephysics_source_on':continue
  annotated=(norm(attempt['b']),norm(attempt['a'])) in labels
  s['positionsBackedByAuthorONTypePair']+=int(annotated)
  s['positionsNotNamedInAuthorONAnnotations']+=int(not annotated)
 for i,g in enumerate(goldClaims):
  old=realON(older['bodyStates'],older['nativeContactPairs'],g['support'],g['child'])
  new=realON(newer['bodyStates'],newer['nativeContactPairs'],g['support'],g['child'])
  goodOld=old>=g['minChildren'];goodNew=new>=g['minChildren']
  s['goldAuthorONClauses']+=1
  s['goldPhysicallySupportedOriginal']+=int(goodOld)
  s['goldPhysicallySupportedAlternative']+=int(goodNew)
  s['authorSupportedOnGained']+=int(not goodOld and goodNew)
  s['authorSupportedOnLost']+=int(goodOld and not goodNew)
  rows.append({'sourceId':id,'goldIndex':i,'gold':g,
   'oldNativeSupportCount':old,'newNativeSupportCount':new,
   'oldGoldSatisfied':goodOld,'newGoldSatisfied':goodNew})
combined=Counter()
for s in splits.values():combined.update(s)
assert combined['goldAuthorONClauses']==354
assert combined['goldPhysicallySupportedOriginal']==3
assert combined['acceptedSameBudgetNativeWorlds']==197
assert combined['actualOriginalNativeBodyCount']==combined['actualAlternativeNativeBodyCount']==2048
assert combined['actualOldContactPairs']==11
# Paired scene bootstrap: 110 source scenes contain independently author ON.
ci={}
for group in ('human','assisted'):
 r=[x for x in rows if (x['sourceId']<100)==(group=='human')]
 scenes=sorted(set(x['sourceId'] for x in r));by=defaultdict(list)
 for x in r:by[x['sourceId']].append(x)
 rng=random.Random(20261025+(17 if group=='human' else 31));samples=[]
 for _ in range(4000):
  draw=[by[scenes[rng.randrange(len(scenes))]] for _ in scenes]
  flat=[i for row in draw for i in row]
  d=len(flat)
  samples.append(sum(x['newGoldSatisfied']-x['oldGoldSatisfied'] for x in flat)/d if d else 0)
 samples.sort()
 ci[group]={'sourceScenesWithOn':len(scenes),'paired95Difference':[samples[100],samples[3899]],
  'sceneNotClausesIndependent':True}
result={'metadata':{
 'independentAuthorSceneEvalZipSHA256':digest(CORPUS),
 'sourceOnlyProposalsSHA256':digest(MODEL),'nativeAlternativeSHA256':digest(NEW),
 'frozenOriginalNativeGenericControlSHA256':digest(OLD),
 'goldNeverReadDuringParserOrGameCorePhysicalSimulation':True,
 'physicalSourcePolicy':'frozen_deterministic_lexical_on',
 'originalSameBudgetAll2070Exception':'The true matched physical native source scenes have 2048 nonwall bodies in BOTH conditions',
 'originalParserFrozenSHA256':digest(Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')),
 'sourceAnnotationCaveat':'Class-level author ON type pairs may omit legal additional relationships; exact referent identity unproven',
 'realismCaveat':'All added generic physical objects uncalibrated in shape, size and interactive affordance. A native collider contact is necessary but not sufficient for realistic support.',
 'dataCaveat':'Same previously researched external corpus, not pristine future source-generalization data'},
 'byGroup':{k:dict(v) for k,v in splits.items()},
 'total':dict(combined),
 'pairedSceneBootstrap':ci}
private=PRIVATE/'prse_source_only_on_native_postgold_lexical_per_case_v1.json'
with private.open('x') as f:json.dump({'metadata':result['metadata'],'rows':rows},f,indent=2);f.write('\n')
private.chmod(0o600)
result['metadata']['privatePerCaseGoldSHA256']=digest(private)
dest=ROOT/'prse_same_budget_deterministic_lexical_on_author_gold_200_aggregate_v1.json'
with dest.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for name,data in splits.items():
 print(name,'originalGoldON',data['goldPhysicallySupportedOriginal'],'newGoldON',
 data['goldPhysicallySupportedAlternative'],'goldConditions',data['goldAuthorONClauses'],
 'newRealContactPairs',data['actualNewContactPairs']-data['actualOldContactPairs'],
 'actualSourceOnlyContactPairs',data['newSourceOnlyPairActuallyContacted'],
 'placementsNotNamedByAnnotations',data['positionsNotNamedInAuthorONAnnotations'])
print('TOTAL',dict(combined))
