#!/usr/bin/env python3
"""Independent SceneEval scorer: frozen greedy vs frozen local optimized
PHYSICAL relation states against original author annotations.

No gold labels enter scene compilation, local search, or physics simulation.
The scorer treats ordered objects as an unordered TYPE pair, an optimistic
metric, and explicitly reports any formerly true gold fact lost to repair.
Complete per-case external traces remain under owner-private Nitro storage.
"""
import csv,io,zipfile,json,hashlib
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).parent
PUBLIC_SOURCE=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
PREV_DIR=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints')
NEW_DIR=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-relation-solver')
assert PUBLIC_SOURCE.is_file()
with zipfile.ZipFile(PUBLIC_SOURCE) as z:
 with z.open('annotations.csv') as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
REL={'next_to':'next','adjacent':'next','beside':'next','facing':'face',
 'opposite':'across','beneath':'under','side_by_side':'next','around':'surround'}
NOUN={'television':'tv','refrigerator':'fridge','bunk_bed':'bed'}
def obj(x):
 x=x.split(':')[0].strip().lower().replace(' ','_')
 return NOUN.get(x,x)
def rel(x):return REL.get(x.lower(),x.lower())
def key(t,a,b,kind):
 if kind=='object':return (rel(t),tuple(sorted([obj(a),obj(b)])))
 return (rel(t),obj(a),obj(b))
def truth(row,kind):
 gold=Counter()
 field='OORel' if kind=='object' else 'OARel'
 for part in row[field].split(';'):
  fields=[s.strip() for s in part.split(',')]
  if len(fields)<(6 if kind=='object' else 5):continue
  op=fields[0]
  try:n=int(fields[1])
  except ValueError:continue
  if op=='gt':n+=1
  if op not in ('eq','ge','gt'):continue
  k=key(fields[2],fields[4],fields[5],kind) if kind=='object' else key(fields[2],fields[3],fields[4],kind)
  gold[k]=max(gold[k],n)
 return gold
def before_relations(row):
 return row.get('physicalRelationOutcomes',[])
def after_relations(row):
 return row.get('relations',[]) if row.get('status')=='materialized_and_reloaded' else []
def credited(rels,kind):
 counter=Counter()
 for r in rels:
  if r.get('kind')!=kind:continue
  present=r.get('result') is True
  if not present:continue
  k=key(r['type'],r['a'],r['b'],kind)
  counter[k]=max(counter[k],1)
 return counter
def calculate(ids,baseline,modified,kind):
 matched_old=matched_new=gold_total=predold=prednew=0
 gained=lost=unchanged=0
 per_case=[]
 for identifier in ids:
  gold=truth(rows[identifier],kind)
  old=credited(before_relations(baseline[identifier]),kind)
  new=credited(after_relations(modified[identifier]),kind)
  cnt_gold=sum(gold.values())
  cnt_old=sum(min(n,old.get(k,0)) for k,n in gold.items())
  cnt_new=sum(min(n,new.get(k,0)) for k,n in gold.items())
  gold_total+=cnt_gold;matched_old+=cnt_old;matched_new+=cnt_new
  predold+=sum(old.values());prednew+=sum(new.values())
  if cnt_new>cnt_old:gained+=1
  elif cnt_new<cnt_old:lost+=1
  else:unchanged+=1
  per_case.append({'id':identifier,'gold':cnt_gold,'matchedBefore':cnt_old,
   'matchedAfter':cnt_new,'resultDelta':cnt_new-cnt_old,'physicallyPredictedBefore':sum(old.values()),
   'physicallyPredictedAfter':sum(new.values())})
 def metrics(correct,pred):
  precision=correct/pred if pred else 0
  recall=correct/gold_total if gold_total else 0
  return {'matched':correct,'predicted':pred,'precision':precision,'recall':recall,
   'f1':2*precision*recall/(precision+recall) if precision+recall else 0}
 return {'goldClaims':gold_total,'baseline':metrics(matched_old,predold),
  'optimized':metrics(matched_new,prednew),'improvementAbsolute':matched_new-matched_old,
  'improvedScenes':gained,'regressedScenes':lost,'unchangedScenes':unchanged,
  'perCase':per_case}
def score(kind):
 path=NEW_DIR/f'prse_solver_{kind}_100_raw_v1.json'
 raw=json.loads(path.read_text())
 assert raw['summary']['sourceDescriptions']==100 and raw['metadata']['noGoldUsed']
 names=[int(r['id']) for r in raw['results']]
 if kind=='human':assert names==list(range(100))
 else:assert names==list(range(100,500,4))
 previous='prse_sceneeval_constraint_physics_v2_after_support.json' if kind=='human' else 'prse_sceneeval_assisted_100_physics_v1.json'
 past=json.loads((PREV_DIR/previous).read_text())
 baseline={int(x['id']):x for x in past['results']}
 updated={int(x['id']):x for x in raw['results']}
 assert set(names)==set(baseline)==set(updated)
 return {'sample':kind,'inputRows':names,'physics':raw['summary'],
  'objectRelations':calculate(names,baseline,updated,'object'),
  'roomRelations':calculate(names,baseline,updated,'room'),
  'rawSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
  'originalGreedyFile':previous}
out={k:score(k) for k in ('human','assisted')}
summary={
 'provenance':{'source':'SceneEval-500 v250610 original ZIP',
  'sourceSHA256':hashlib.sha256(PUBLIC_SOURCE.read_bytes()).hexdigest(),
  'goldUsage':'Read by this scorer after both physics proposal files already written; never fed to optimizer',
  'reference':'Old separately recorded greedy physical scenes on same source IDs',
  'metricLimit':'Directional arguments ignored and duplicate instance relations coalesced; this score is optimistic, not exact semantic equivalence',
  'externalEvidence':'Full source and individual raw cases kept private on Nitro'},
 'samples':{k:{x:y for x,y in s.items() if x not in ('inputRows',)}
  for k,s in out.items()}}
for s in summary['samples'].values():
 for typ in ('objectRelations','roomRelations'):
  s[typ].pop('perCase')
output=ROOT/'prse_solver_external_gold_comparison_v1.json'
with output.open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
for k,s in out.items():
 print(k,'overall optimized',s['physics']['afterActualPhysicsSatisfied'],
  'greedy',s['physics']['beforeGreedySatisfied'],
  'object gold',s['objectRelations']['baseline']['matched'],'=>',s['objectRelations']['optimized']['matched'],
  'room gold',s['roomRelations']['baseline']['matched'],'=>',s['roomRelations']['optimized']['matched'],
  'gained/lost',s['objectRelations']['improvedScenes'],s['objectRelations']['regressedScenes'])
