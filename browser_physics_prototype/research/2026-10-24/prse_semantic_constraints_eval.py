#!/usr/bin/env python3
"""Corpus-separated quantitative evaluation of a bounded semantic interpreter.

Gold SceneEval labels NEVER enter the interpreter; only its saved predictions
are compared. This is an exploratory fixed-parser study, not pre-registered.
"""
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter,defaultdict
from pathlib import Path
from prse_semantic_constraints import interpret,canon

HERE=Path(__file__).parent
FILE=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
REL={'next_to':'next','beside':'next','adjacent':'next','facing':'face','opposite':'across',
     'beneath':'under','around':'surround','in':'inside','side_by_side':'next'}
PROPS={'wood':'wooden','king_size':'king_size','grey':'grey','big':'large'}
def predlabel(name):
 return canon(name).lower().replace(' ','_')
def reltype(name):return REL.get(name,name)
def truth(raw,typ):
 output=Counter()
 for part in raw.split(';'):
  f=[x.strip() for x in part.strip().split(',')]
  if len(f)<3:continue
  op=f[0]
  try:n=int(f[1])
  except ValueError:continue
  if typ=='quant' and len(f)>=3:
   key=predlabel(f[2])
  elif typ=='relation' and len(f)>=6:
   # Pair-wise relation *type*, no unwarranted directional correctness claim.
   key=(reltype(f[2]),tuple(sorted([predlabel(f[4]),predlabel(f[5].split(':')[0])])))
  elif typ=='room' and len(f)>=5:
   key=(reltype(f[2]),predlabel(f[3]),predlabel(f[4]))
  elif typ=='attribute' and len(f)>=4:
   key=(predlabel(f[2]),PROPS.get(f[3],f[3]))
  else:continue
  # Repeated identical annotations are not treated as independent different claims.
  if op=='ge':output[key]=max(output[key],n)
  elif op=='gt':output[key]=max(output[key],n+1)
  elif op=='eq':output[key]=max(output[key],n)
 return output

def predicted(scene,typ):
 output=Counter()
 if typ=='quant':
  for k,d in scene['quantities'].items():
   val=d['count']+(1 if d['op']=='gt' else 0)
   output[predlabel(k)]=val
 elif typ=='relation':
  for r in scene['relations']:
   if r['kind']!='object':continue
   pair=tuple(sorted([predlabel(r['a']),predlabel(r['b'])]))
   key=(reltype(r['type']),pair)
   count=scene['quantities'].get(r['a'],{}).get('count',1)
   output[key]=max(output[key],max(1,count))
 elif typ=='room':
  for r in scene['relations']:
   if r['kind']!='room':continue
   output[(reltype(r['type']),predlabel(r['a']),predlabel(r['b']))]+=1
 elif typ=='attribute':
  for m in scene['mentions']:
   for attr in m['attributes']:
    key=(predlabel(m['type']),PROPS.get(attr,attr))
    output[key]=max(output[key],max(1,m['quantity']))
 return output

def mscore(rows,typ):
 gold=Counter();pred=Counter();true=Counter()
 zeroCases=zeroCorrect=0
 per=[];fails=[]
 for row,parsed in rows:
  field={'quant':'ObjCount','relation':'OORel','room':'OARel','attribute':'ObjAttr'}[typ]
  actual=truth(row[field],typ)
  stated=predicted(parsed,typ)
  nz={k:n for k,n in actual.items() if n>0}
  z={k:n for k,n in actual.items() if n==0}
  tp=sum(min(n,stated.get(k,0)) for k,n in nz.items())
  a=sum(nz.values());b=sum(n for n in stated.values() if n>0)
  zeroCases+=len(z)
  zeroCorrect+=sum(1 for k in z if stated.get(k)!=None and (k in stated and stated[k]==0))
  gold.update(nz);pred.update({k:n for k,n in stated.items() if n>0})
  true.update({k:min(n,stated.get(k,0)) for k,n in nz.items()})
  per.append({'id':row['ID'],'goldFacts':a,'predictedFacts':b,'correctFacts':tp,
   'precision':tp/b if b else 0.,'recall':tp/a if a else 1.,
   'unknownAbstain':b==0 and a>0})
  if tp<a and len(fails)<15:fails.append({'id':row['ID'],'text':row['Description'][:280],
    'missing':[str(k) for k,n in nz.items() if stated.get(k,0)<n][:6],
    'proposed':[str(k) for k in stated][:6]})
 sum_gold=sum(gold.values());sum_pred=sum(pred.values());sum_true=sum(true.values())
 precision=sum_true/sum_pred if sum_pred else 0.
 recall=sum_true/sum_gold if sum_gold else 0.
 return {'sceneCount':len(rows),'goldFacts':sum_gold,'predictedFacts':sum_pred,
  'matchedFacts':sum_true,'precision':precision,'recall':recall,
  'f1':2*precision*recall/(precision+recall) if precision+recall else 0,
  'goldZeroClaims':zeroCases,'explicitlyNegatedCorrect':zeroCorrect,
  'scenesAbstained':sum(z['unknownAbstain'] for z in per),
  'fullyMatchedSceneFraction':sum(z['correctFacts']==z['goldFacts'] and z['predictedFacts']==z['goldFacts'] for z in per)/len(per),
  'failuresFirst15':fails}
with zipfile.ZipFile(FILE) as z:
 with z.open('annotations.csv') as f:
  rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(rows)==500
# The parser is invoked with no gold or learned weights from the benchmark.
proposals=[interpret(r['Description'],source_id=r['ID']) for r in rows]
segments={'first35_development':list(zip(rows[:35],proposals[:35])),
 'remaining65_original_human':list(zip(rows[35:100],proposals[35:100])),
 'original_human_100':list(zip(rows[:100],proposals[:100])),
 'machine_assisted_400':list(zip(rows[100:],proposals[100:])),
 'all_500':list(zip(rows,proposals))}
scores={name:{typ:mscore(sample,typ) for typ in ('quant','relation','room','attribute')}
 for name,sample in segments.items()}
negationCases=[{'id':r['ID'],'text':r['Description'],'gold':truth(r['ObjCount'],'quant'),
  'predicted':predicted(p,'quant')} for r,p in zip(rows,proposals) if
  any(n==0 for n in truth(r['ObjCount'],'quant').values())]
output={'provenance':{'corpus':'SceneEval-500 release v250610, original 100 human annotations + 400 assisted',
 'sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),
 'parser':'bounded deterministic regex constraint graph with explicit abstentions, not model',
 'claims':'Pair-relation score ignores direction and physical satisfaction; room attrs are NOT grounded.',
 'dataReview':'35 development descriptions examined; remaining 65 manual records separate but previous baseline examined whole corpus metrics. Not a pristine blind holdout.',
 'goldUsedOnlyInScorer':True},
 'scores':scores,
 'negativeCountCases':negationCases[:30],
 'proposalsFirst100':proposals[:100],
 'proposalsAll500':proposals}
import sys
name=next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith('--output=')),'prse_semantic_constraints_eval_v1.json')
if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_.-]*\.json',name):raise ValueError('Unsafe output name')
out=HERE/name
with out.open('x') as f:json.dump(output,f,indent=2,default=lambda x:dict(x));f.write('\n')
for split in ('first35_development','remaining65_original_human','machine_assisted_400'):
 print(split,{name:{k:round(val[k],4) if isinstance(val[k],float) else val[k]
       for k in ('f1','precision','recall','matchedFacts','goldFacts','predictedFacts','goldZeroClaims','explicitlyNegatedCorrect')}
       for name,val in scores[split].items()})
print('sample_references',[(i,proposals[i]['quantities'],proposals[i]['relations'][:3]) for i in (7,22)])
