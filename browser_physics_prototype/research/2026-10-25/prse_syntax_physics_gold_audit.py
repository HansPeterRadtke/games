#!/usr/bin/env python3
"""Independent official SceneEval gold audit of frozen, physics-validated
deterministic vs pretrained syntactic-parser PRSE scene proposals.

Gold labels are read only by THIS scorer after original and new physical
scene outputs are already written. Reports both optimistic unordered class-pair
matching and strict annotation-field-order matching. Neither equals instance-
specific semantic truth; no learned fine-tuning or gold-guided scene selection.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import io,csv,zipfile,json

HERE=Path(__file__).parent
BASE_DIR=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-relation-solver')
MODEL_DIR=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model-physics')
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as fp:rows=list(csv.DictReader(io.TextIOWrapper(fp,encoding='utf-8-sig')))
assert len(rows)==500
def sha(p):return sha256(p.read_bytes()).hexdigest()
assert sha(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
REL={'next_to':'next','adjacent':'next','beside':'next','facing':'face','opposite':'across','beneath':'under','side_by_side':'next','around':'surround'}
NOUN={'television':'tv','refrigerator':'fridge','bunk_bed':'bed'}
def noun(x):
 x=x.split(':')[0].strip().lower().replace(' ','_')
 return NOUN.get(x,x)
def rel(x):return REL.get(x.lower(),x.lower())
def key(k,r,a,b,ordered=False):
 if k=='object':
  names=[noun(a),noun(b)]
  return ('object',rel(r),*(names if ordered else sorted(names)))
 return ('room',rel(r),noun(a),noun(b))
def gold(row,kind,ordered):
 out=Counter()
 for part in row['OORel' if kind=='object' else 'OARel'].split(';'):
  v=[x.strip() for x in part.split(',')]
  if len(v)<(6 if kind=='object' else 5):continue
  try:n=int(v[1])
  except ValueError:continue
  if v[0]=='gt':n+=1
  if v[0] not in ('eq','ge','gt'):continue
  k=key(kind,v[2],v[4],v[5],ordered) if kind=='object' else key(kind,v[2],v[3],v[4],ordered)
  out[k]=max(out[k],n)
 return out
def grounded(row,kind,ordered):
 out=Counter()
 if row['status']!='materialized_and_reloaded':return out
 for r in row.get('relations',[]):
  if r['kind']!=kind or r['result'] is not True:continue
  k=key(kind,r['type'],r['a'],r['b'],ordered)
  out[k]=max(out[k],1)
 return out
def eval_method(method,sample,kind,ordered,baseline_ids):
 scores=[]
 path=BASE_DIR/f'prse_solver_{sample}_100_raw_v1.json' if method=='deterministic' else MODEL_DIR/f'prse_syntax_{method}_{sample}_100_raw_v1.json'
 dat=json.loads(path.read_text())
 recs=dat['results']
 assert [int(e['id']) for e in recs]==baseline_ids
 correct=allgold=allpred=0;better=worse=same=0
 for id,item in zip(baseline_ids,recs):
  g=gold(rows[id],kind,ordered)
  p=grounded(item,kind,ordered)
  c=sum(min(n,p.get(k,0)) for k,n in g.items())
  correct+=c;allgold+=sum(g.values());allpred+=sum(p.values())
  scores.append({'sourceId':id,'correct':c,'gold':sum(g.values()),'predicted':sum(p.values())})
 prec=correct/allpred if allpred else 0
 recall=correct/allgold if allgold else 0
 return {'correct':correct,'gold':allgold,'physicallyPredicted':allpred,'precision':prec,
   'recall':recall,'f1':2*prec*recall/(prec+recall) if prec+recall else 0,
   'physicalScenesAccepted':dat['summary']['physicallyMaterialized'],
   'parsedSourceConstraints':dat['summary']['parsedConstraints'],
   'physicallySatisfiedParsedConstraints':dat['summary']['afterActualPhysicsSatisfied'],
   'physicallyViolatedParsedConstraints':dat['summary']['afterActualPhysicsViolated'],
   'physicallyUnsupportedParsedConstraints':dat['summary']['afterActualPhysicsUnsupported'],
   'searchCandidateChecks':dat['summary']['totalCandidateChecks'],
   'wallTimeMs':dat['summary']['wallTimeMs'],'privateRawSHA256':sha(path),
   'perCase':scores}
samples={'human':list(range(100)),'assisted':list(range(100,500,4))}
comparison={}
for subset,ids in samples.items():
 comparison[subset]={}
 for kind in ('object','room'):
  comparison[subset][kind]={}
  for direction in ('unordered','ordered'):
   methods={m:eval_method(m,subset,kind,direction=='ordered',ids)
       for m in ('deterministic','dependency','union')}
   # Directional exactness means official annotation argument order, not
   # real human perceived relations or per-instance grounding.
   for m in methods:
    methods[m].pop('perCase')
   comparison[subset][kind][direction]=methods
safe={
 'metadata':{
  'source':'SceneEval-500 v250610 official annotated human and assisted data',
  'sourceSha256':sha(CORPUS),
  'model':'Pretrained spaCy en_core_web_sm 3.8.0 CPU syntactic dependencies + authored mapping',
  'frozenParserInput':'Same basic object vocabulary/quantities from previous deterministic baseline, only relations differ',
  'noGoldDuringInference':True,'noLLMOrGPU':True,
  'goldMetricWarnings':'Type-level relation, order-insensitive or as-encoded direction, no true per-instance visual grounding, exploratory source corpus',
  'notBlind':'Prior source rows and baseline scores had been seen, no pristine independent holdout'},
 'results':comparison}
with (HERE/'prse_syntax_physics_external_gold_v1.json').open('x') as fp:json.dump(safe,fp,indent=2);fp.write('\n')
for part in samples:
 for k in ('object','room'):
  for d in ('unordered','ordered'):
   m=comparison[part][k][d]
   print(part,k,d,'gold',m['deterministic']['gold'],
         'correct',[(x,m[x]['correct']) for x in m],
         'physics scenes',m['union']['physicalScenesAccepted'])
