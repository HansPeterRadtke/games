#!/usr/bin/env python3
"""Paired SCENE-level bootstrap uncertainty on already frozen physical relation
match counts. Resamples original SceneEval scene IDs (not individual frames or
annotations) to avoid inflating effective sample size by correlated relations.
This is conditional on this curated benchmark, NOT population generalization.
"""
import csv,io,json,zipfile,random
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).parent
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-relation-solver')
MODEL=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model-physics')
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as fp:rows=list(csv.DictReader(io.TextIOWrapper(fp,encoding='utf-8-sig')))
REL={'next_to':'next','adjacent':'next','beside':'next','facing':'face','opposite':'across',
     'beneath':'under','side_by_side':'next','around':'surround'}
NOUN={'television':'tv','refrigerator':'fridge','bunk_bed':'bed'}
def norm(x):
 x=x.split(':')[0].strip().lower().replace(' ','_')
 return NOUN.get(x,x)
def label(t):return REL.get(t.lower(),t.lower())
def key(r,a,b):
 return (label(r),tuple(sorted((norm(a),norm(b)))))
def gold(row):
 out=Counter()
 for s in row['OORel'].split(';'):
  f=[v.strip() for v in s.split(',')]
  if len(f)<6:continue
  try:n=int(f[1])
  except ValueError:continue
  if f[0]=='gt':n+=1
  if f[0] not in ('eq','ge','gt'):continue
  out[key(f[2],f[4],f[5])]=max(out[key(f[2],f[4],f[5])],n)
 return out
def matches(row,truth):
 proposals=Counter()
 if row['status']!='materialized_and_reloaded':return 0
 for r in row.get('relations',[]):
  if r['kind']=='object' and r['result'] is True:
   k=key(r['type'],r['a'],r['b'])
   proposals[k]=max(proposals[k],1)
 return sum(min(n,proposals.get(k,0)) for k,n in truth.items())
indices={'human':list(range(100)),'assisted':list(range(100,500,4))}
output={'metadata':{
 'method':'paired scene-level nonparametric bootstrap, 4000 resamples with deterministic seed 20261025',
 'metric':'difference in physically grounded SceneEval unordered type-pair recall, matched gold count over gold annotations',
 'limitation':'SceneEval is curated and not iid across all possible literary games. Intervals measure benchmark resampling variability, not prospective human-world accuracy.',
 'input':'frozen independently annotated physical scene outputs; no parser or physics output is modified by this scorer'},
 'comparisons':{}}
for group,ids in indices.items():
 frozen={}
 for method in ('deterministic','dependency','union'):
  name=f'prse_solver_{group}_100_raw_v1.json' if method=='deterministic' else f'prse_syntax_{method}_{group}_100_raw_v1.json'
  path=(BASE if method=='deterministic' else MODEL)/name
  f=json.loads(path.read_text())['results']
  assert [int(r['id']) for r in f]==ids
  frozen[method]=f
 goldcounts=[sum(gold(rows[i]).values()) for i in ids]
 truth=[gold(rows[i]) for i in ids]
 counted={method:[matches(r,t) for r,t in zip(frozen[method],truth)] for method in frozen}
 assert len(goldcounts)==100
 comps={}
 for method in ('dependency','union'):
  original=sum(counted['deterministic'])
  new=sum(counted[method])
  denominator=sum(goldcounts)
  delta=(new-original)/denominator
  randomgen=random.Random(20261025 + (0 if group=='human' else 200)+ (0 if method=='dependency' else 700))
  changes=[]
  for _ in range(4000):
   sampled=[randomgen.randrange(100) for _ in range(100)]
   denom=sum(goldcounts[i] for i in sampled)
   difference=sum(counted[method][i]-counted['deterministic'][i] for i in sampled)
   changes.append(difference/denom if denom else 0)
  changes.sort()
  comps[method]={
    'benchmarkGoldClaims':denominator,
    'baselineMatched':original,
    'modelMatched':new,
    'recallDifference':delta,
    'bootstrapPercentile95':[changes[100],changes[3899]],
    'bootstrapFractionImproved':sum(x>0 for x in changes)/len(changes),
    'perSceneGains':sum(a>b for a,b in zip(counted[method],counted['deterministic'])),
    'perSceneLosses':sum(a<b for a,b in zip(counted[method],counted['deterministic'])),
    'perSceneUnchanged':sum(a==b for a,b in zip(counted[method],counted['deterministic']))
   }
 output['comparisons'][group]=comps
path=ROOT/'prse_syntax_model_paired_uncertainty_v1.json'
with path.open('x') as fp:json.dump(output,fp,indent=2);fp.write('\n')
for group,cs in output['comparisons'].items():
 for m,x in cs.items():print(group,m,'delta',round(x['recallDifference'],5),
  'interval',list(round(y,5) for y in x['bootstrapPercentile95']),
  'gain/loss/unchanged',[x['perSceneGains'],x['perSceneLosses'],x['perSceneUnchanged']])
