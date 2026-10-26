#!/usr/bin/env python3
"""POST-FROZEN independent SceneEval official author ON evaluator for the NEW
300 previously physically unevaluated assisted-source descriptions.
Native GameCore comparison was frozen without any author annotations; this
source-audit script may open independent OORel gold only AFTER physics.
The corpus overall was previously studied and all shapes are generic boxes.
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter,defaultdict
from stat import S_IMODE
import json,zipfile,csv,io,math,random
HERE=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-new-physical-300')
RAW=PRIVATE/'prse_source_only_same_budget_native_300_raw_v1.json'
MODEL=PRIVATE/'prse_source_only_on_nounchunk_300_raw_v1.json'
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert S_IMODE(PRIVATE.stat().st_mode)==0o700
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (RAW,MODEL))
assert digest(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
ids=[i for i in range(100,500) if (i-100)%4!=0]
run=load(RAW);candidate=load(MODEL)
scenes=run['rows'];proposals=candidate['cases']
assert [r['sourceId'] for r in scenes]==[r['sourceId'] for r in proposals]==ids
assert set(ids).isdisjoint(set(range(100))|set(range(100,500,4)))
assert all(r['status'] in ('same_body_real_native_matched','original_scene_not_physically_accepted') for r in scenes)
assert not any(r.get('sourceGroup')!='assisted' for r in scenes)
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

rows=[];sceneScores={};total=Counter();unmatchedNewNative=[]
for idx,id in enumerate(ids):
 row=scenes[idx];src=proposals[idx];golds=sourceON(gold[id])
 s={'sceneId':id,'goldOnRequirements':len(golds),'physicallyEvaluated':False}
 total['descriptions']+=1
 total['goldONAll300']+=len(golds)
 if row['status']!='same_body_real_native_matched':
  total['goldONInRejectedScenes']+=len(golds)
  sceneScores[id]=s
  continue
 s['physicallyEvaluated']=True
 total['acceptedScenes']+=1
 oldB=row['oldBodyStates'];newB=row['newBodyStates'];oldC=row['oldNativeContactPairs'];newC=row['newNativeContactPairs']
 assert {x['id'] for x in oldB}=={x['id'] for x in newB}
 assert row['identicalSourceAndNativeEntityBudget'] and row['savedNativeSourceAndContacts']
 total['bodiesEachArm']+=len(newB)
 total['controlContacts']+=len(oldC)
 total['sourceContactPairs']+=len(newC)
 total['oldQualifiedNativeContacts']+=len(oldC)
 total['newQualifiedNativeContacts']+=len(newC)
 total['sourceModelCandidates']+=len(src['proposedOn'])
 total['admittedNativeSourceSupportPairs']+=row['actualNewSourcePairs']
 total['nativeSceneContactsGained']+=len(newC)-len(oldC)
 total['zeroMovesNegativeScenes']+=not bool(row['placed'])
 labeled={(x['support'],x['child']) for x in golds}
 for attempt in row['attempts']:
  if attempt['status']!='nominally_valid_prephysics_source_on':continue
  total['sourceMoves']+=1
  if (norm(attempt['b']),norm(attempt['a'])) in labeled:
   total['newRelationsAnnotatedAtTypePairLevel']+=1
  else:
   total['newRelationsUnannotatedAtTypePairLevel']+=1
 for j,g in enumerate(golds):
  oldCount=realON(oldB,oldC,g['support'],g['child'])
  newCount=realON(newB,newC,g['support'],g['child'])
  oldOK=oldCount>=g['minChildren'];newOK=newCount>=g['minChildren']
  typeCounts=Counter(norm(x['kind']) for x in oldB)
  kindsPresent=typeCounts[g['support']]>=1 and typeCounts[g['child']]>=g['minChildren']
  total['goldONPhysicallyEvaluable']+=1
  total['goldONSufficientObjectTypesAndCounts']+=int(kindsPresent)
  total['goldONPhysicallySupportedBaseline']+=int(oldOK)
  total['goldONPhysicallySupportedSourceOnly']+=int(newOK)
  total['goldONTrueGained']+=int(not oldOK and newOK)
  total['goldONTrueLost']+=int(oldOK and not newOK)
  rows.append({'sourceId':id,'goldIndex':j,'oldCount':oldCount,'newCount':newCount,
   'oldTrue':oldOK,'newTrue':newOK,'typesSufficient':kindsPresent,'gold':g})
 sceneScores[id]=s
assert total['descriptions']==300 and total['acceptedScenes']==run['summary']['matchedNativeScenarios']
assert total['sourceContactPairs']==run['summary']['sourceOnlyNativeContactPairs']
assert total['controlContacts']==run['summary']['baselineNativeContactPairs']
assert total['admittedNativeSourceSupportPairs']==run['summary']['sourceOnlyProposedContactsReal']
assert total['bodiesEachArm']==run['summary']['totalSamePhysicalBodiesPerArm']
assert total['sourceMoves']==run['summary']['placed']
assert total['newRelationsAnnotatedAtTypePairLevel']+total['newRelationsUnannotatedAtTypePairLevel']==total['sourceMoves']
# Bootstrap source rooms (not their correlated gold clauses), accepted only.
by=defaultdict(list)
for r in rows:by[r['sourceId']].append(r)
keys=sorted(by);rng=random.Random(20261026);scores=[]
for _ in range(4000):
 drawn=[by[keys[rng.randrange(len(keys))]] for _ in range(len(keys))]
 flat=[r for group in drawn for r in group]
 scores.append(sum(int(r['newTrue'])-int(r['oldTrue']) for r in flat)/len(flat) if flat else 0)
scores.sort()
meta={'goldSHA256':digest(CORPUS),'frozenPhysicsSHA256':digest(RAW),
 'frozenSourceOnlyParserSHA256':digest(MODEL),'goldOpenedOnlyAfterNativeFrozen':True,
 'newPhysicalSubsetOutsidePrior200':True,'generalSourceCorpusPreviouslyExamined':True,
 'limitedToPartlyAssistedDescriptions':True,
 'goldONTypePairsMayBeIncomplete':True,
 'pretrainedNewContactsWithoutGoldONLabelNotAutomaticFalsePositives':True,
 'genericCollidersDoNotEstablishActualFurnitureScaleShapeOrAffordance':True}
private=PRIVATE/'prse_new300_independent_author_gold_percase_v1.json'
with private.open('x') as f:json.dump({'metadata':meta,'perCase':rows,'sceneScores':sceneScores},f,indent=2);f.write('\n')
private.chmod(0o600)
summary={'metadata':{**meta,'privateGoldPerCaseSHA256':digest(private)},'total':dict(total),
 'pairedSourceSceneBootstrap':{'seed':20261026,'resamples':4000,
  'sourceScenesWithON':len(keys),'differencePoint':(total['goldONPhysicallySupportedSourceOnly']-total['goldONPhysicallySupportedBaseline'])/total['goldONPhysicallyEvaluable'] if total['goldONPhysicallyEvaluable'] else 0,
  'conditional95': [scores[100],scores[3899]],
  'warning':'Previously studied corpus; not independent future-domain estimate.'}}
out=HERE/'prse_new300_matched_native_independent_gold_aggregate_v1.json'
with out.open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print('POST_FROZEN_AUTHOR_SCORE',json.dumps(summary['total'],sort_keys=True))
print('SCENE_BOOTSTRAP',json.dumps(summary['pairedSourceSceneBootstrap']))
