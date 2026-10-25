#!/usr/bin/env python3
"""Independent scorer for three already frozen SceneEval text interpreters.

Gold annotations are opened HERE ONLY, after both pretrained syntactic-parser
proposals and deterministic baseline have already been written as raw JSON.
Count type-pair matches twice: optimistic unordered as in prior research and
strict ordered annotated fields (still not true instance-level grounding).
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import csv,io,zipfile,json
ROOT=Path(__file__).parent
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
MODEL_DIR=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model')
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
assert CORPUS.is_file()
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as fp:
  rows=list(csv.DictReader(io.TextIOWrapper(fp,encoding='utf-8-sig')))
assert len(rows)==500
def h(p):return sha256(p.read_bytes()).hexdigest()
assert h(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
variants={'deterministic':BASE,
 'dependency':MODEL_DIR/'prse_spacy_sceneeval_500_dependency_v1.json',
 'union':MODEL_DIR/'prse_spacy_sceneeval_500_union_v1.json'}
relations_alias={'next_to':'next','adjacent':'next','beside':'next','facing':'face',
 'opposite':'across','beneath':'under','side_by_side':'next','around':'surround'}
alias={'television':'tv','refrigerator':'fridge','bunk_bed':'bed'}
def canonical(n):
 n=n.split(':')[0].lower().strip().replace(' ','_')
 return alias.get(n,n)
def canonrel(x):return relations_alias.get(x.lower(),x.lower())
def expect(row,kind='unordered',domain='combined'):
 entries=Counter()
 for field in ('OORel','OARel'):
  if domain=='object' and field!='OORel':continue
  if domain=='room' and field!='OARel':continue
  for part in row[field].split(';'):
   vals=[x.strip() for x in part.split(',')]
   if len(vals)<(6 if field=='OORel' else 5):continue
   try:n=int(vals[1])
   except ValueError:continue
   if vals[0]=='gt':n+=1
   if vals[0] not in ('eq','ge','gt'):continue
   relation=canonrel(vals[2])
   if field=='OORel':
    names=[canonical(vals[4]),canonical(vals[5])]
    key=('pair',relation,*(tuple(sorted(names)) if kind=='unordered' else names))
   else:key=('room',relation,canonical(vals[3]),canonical(vals[4]))
   entries[key]=max(entries[key],n)
 return entries
def predicted(proposal,kind='unordered',domain='combined'):
 result=Counter()
 for r in proposal['relations']:
  if domain=='object' and r['kind']!='object':continue
  if domain=='room' and r['kind']!='room':continue
  relation=canonrel(r['type'])
  if r['kind']=='object':
   names=[canonical(r['a']),canonical(r['b'])]
   key=('pair',relation,*(tuple(sorted(names)) if kind=='unordered' else names))
  elif r['kind']=='room':
   key=('room',relation,canonical(r['a']),canonical(r['b']))
  else:continue
  result[key]=max(result[key],1)
 return result
def compare(gold,pred):
 correct=sum(min(v,pred.get(k,0)) for k,v in gold.items())
 return (sum(gold.values()),sum(pred.values()),correct)
subset={
 'development35':list(range(35)),
 'later65':list(range(35,100)),
 'human100':list(range(100)),
 'assisted400':list(range(100,500)),
 'assistedSample100':list(range(100,500,4)),
 'all500':list(range(500))
}
out={}
private={}
for method,location in variants.items():
 data=json.loads(location.read_text())
 props=data['proposalsAll500']
 assert len(props)==500
 assert all(p['text']==rows[i]['Description'] and p['sourceId']==str(i) for i,p in enumerate(props))
 out[method]={'provenanceSHA256':h(location),'splits':{}}
 private[method]={}
 for key,ids in subset.items():
  for k in ('unordered','ordered'):
   for domain in ('object','room','combined'):
    expected=actual=correct=0
    per=[]
    for i in ids:
     t=expect(rows[i],k,domain)
     p=predicted(props[i],k,domain)
     x,y,z=compare(t,p)
     expected+=x;actual+=y;correct+=z
     per.append({'id':i,'gold':x,'predicted':y,'matched':z})
    precision=correct/actual if actual else 0
    recall=correct/expected if expected else 0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0
    out[method]['splits'].setdefault(key,{}).setdefault(k,{})[domain]={
     'scenes':len(ids),'expectedAnnotations':expected,'predictedClaims':actual,
     'matched':correct,'precision':precision,'recall':recall,'f1':f1,
     'falsePositiveClaims':actual-correct,'missingClaims':expected-correct}
    private[method].setdefault(key,{}).setdefault(k,{})[domain]=per
# Same source quantities/counts should never change between arms.
base=json.loads(BASE.read_text())['proposalsAll500']
for method,source in variants.items():
 props=json.loads(source.read_text())['proposalsAll500']
 assert all(props[i]['quantities']==base[i]['quantities'] and
            props[i]['mentions']==base[i]['mentions'] for i in range(500))
result={
 'metadata':{'source':'Official SceneEval-500_v250610 external annotations evaluated only after proposals frozen',
  'sourceZIPsha256':h(CORPUS),
  'model':'CPU pretrained spaCy en_core_web_sm 3.8.0 syntax model + authored dependency relation mapping',
  'goldDataNeverInModel':'Input source descriptions only. No fine tuning or model-selection based on these gold annotations.',
  'strictDirectionLimit':'Strict uses source annotation type order; still not instance-specific physical truth',
  'unorderedLimit':'Optimistic relation-type and unordered class pair, matches prior studies, not exact scene meaning',
  'developmentContamination':'First 35 manually inspected; all500 previously evaluated on deterministic baseline; remaining subsets not untouched outer holdouts'},
 'variants':out}
with (ROOT/'prse_syntax_model_relation_scores_v2.json').open('x') as fp:
 json.dump(result,fp,indent=2);fp.write('\n')
raw=MODEL_DIR/'prse_syntax_model_per_case_gold_audit_v2.json'
with raw.open('x') as fp:json.dump(private,fp,indent=2);fp.write('\n')
raw.chmod(0o600)
for method in variants:
 for split in ('human100','assisted400','assistedSample100'):
  a=out[method]['splits'][split]
  print(method,split,
   'obj_unordered',(a['unordered']['object']['matched'],a['unordered']['object']['expectedAnnotations'],round(a['unordered']['object']['f1'],4)),
   'obj_ordered',(a['ordered']['object']['matched'],a['ordered']['object']['expectedAnnotations'],round(a['ordered']['object']['f1'],4)))
