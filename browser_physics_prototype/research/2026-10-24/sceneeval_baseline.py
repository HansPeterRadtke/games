#!/usr/bin/env python3
"""Exploratory, corpus-level PRSE scene parsing comparison on independently annotated SceneEval-500.
External annotations are EVALUATION ONLY, never used to parse a description.
Manual first 100 vs VLM-assisted last 400 reported separately. No model calls.
"""
import csv,io,hashlib,json,re,zipfile,collections
from pathlib import Path

DATA=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
if not DATA.exists():raise RuntimeError('Official external benchmark is missing')
SRC='https://github.com/3dlg-hcvc/SceneEval/releases/tag/SceneEval-500_v250610'
# Fixed small curated vocabulary from ordinary furniture/game objects, not mined from gold labels.
names={
'bed':['bed','beds'],'nightstand':['nightstand','nightstands','bedside table','bedside tables'],
'wardrobe':['wardrobe','wardrobes'],'armchair':['armchair','armchairs'],'floor_lamp':['floor lamp','floor lamps'],
'sofa':['sofa','sofas','couch','couches'],'bookshelf':['bookshelf','bookshelves','bookcase','bookcases'],
'dining_table':['dining table','dining tables'],'coffee_table':['coffee table','coffee tables'],
'table':['table','tables'],'chair':['chair','chairs'],'desk':['desk','desks'],'dresser':['dresser','dressers'],
'cabinet':['cabinet','cabinets'],'lamp':['lamp','lamps'],'rug':['rug','rugs'],'plant':['plant','plants'],
'painting':['painting','paintings'],'mirror':['mirror','mirrors'],'window':['window','windows'],
'television':['television','televisions','tv','tvs'],'shelf':['shelf','shelves'],
'toilet':['toilet','toilets'],'sink':['sink','sinks'],'bathtub':['bathtub','bathtubs'],
'refrigerator':['refrigerator','refrigerators','fridge','fridges'],
'oven':['oven','ovens'],'stool':['stool','stools'],'bedside_lamp':['bedside lamp','bedside lamps'],
'vase':['vase','vases'],'box':['box','boxes'],'ball':['ball','balls'],'book':['book','books']
}
number={'a':1,'an':1,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
def extract(sentence,legacy=False):
 if legacy:return {} # Preexisting PRSE scene-translation rejects any non-exact shelter role set.
 # longest matched noun phrase wins, avoid matching "lamp" within "floor lamp"
 candidates=[]
 for cls,terms in names.items():
  for noun in terms:
   for m in re.finditer(r'\b'+re.escape(noun)+r'\b',sentence,re.I):
    candidates.append((m.start(),m.end(),cls,noun))
 candidates.sort(key=lambda v:(-(v[1]-v[0]),v[0]))
 selected=[]
 for c in candidates:
  if not any(c[0]<v[1] and c[1]>v[0] for v in selected):selected.append(c)
 ans=collections.Counter()
 for start,end,cls,noun in selected:
  phrase=sentence[max(0,start-48):start].lower()
  count=re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+|a|an)\s+(?:(?:big|small|old|new|large|little|blue|red|green|white|black|wooden|round|square|king-size|king size|modern|antique|long|tiny|single|double)\s+){0,4}$',phrase)
  qty=number.get(count.group(1),None) if count else None
  if qty is None and count:qty=int(count.group(1))
  if qty is None:qty=1
  ans[cls]+=min(qty,40)
 return dict(ans)

def truth_counts(raw):
 gold={}
 for spec in filter(None,(part.strip() for part in raw.split(';'))):
  bits=[x.strip() for x in spec.split(',')]
  if len(bits)<3:continue
  if bits[0]!='eq':continue
  try:n=int(bits[1])
  except ValueError:continue
  kind=bits[2]
  gold[kind]=max(gold.get(kind,0),n)
 return gold

def report(rows,mode):
 all_tp=all_pred=all_gold=0; exact=0; scene_recall=[];scene_precision=[];structural=0
 by=[]
 for row in rows:
  gold=truth_counts(row['ObjCount']);pred=extract(row['Description'],legacy=mode=='legacy')
  tp=sum(min(gold.get(k,0),v) for k,v in pred.items())
  total=sum(gold.values());count=sum(pred.values())
  all_tp+=tp;all_gold+=total;all_pred+=count
  exact+=int(gold==pred)
  scene_recall.append(tp/total if total else 1.)
  scene_precision.append(tp/count if count else int(total==0))
  by.append({'id':row['ID'],'description':row['Description'],'expected':gold,'predicted':pred,
             'recall':tp/total if total else 1.,'precision':tp/count if count else float(total==0),
             'exact':gold==pred,'difficulty':row['Difficulty']})
 precision=all_tp/all_pred if all_pred else 0.
 recall=all_tp/all_gold if all_gold else 0.
 return {'prompts':len(rows),'gold_objects':all_gold,'predicted_objects':all_pred,
        'true_positive_count':all_tp,'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0.,
        'exact_scene_counts':exact,'exact_scene_rate':exact/len(rows),
        'mean_scene_recall':sum(scene_recall)/len(rows),'mean_scene_precision':sum(scene_precision)/len(rows),
        'examples':by[:12],'low_recall_examples':[r for r in by if r['recall']<.5][:8]}
with zipfile.ZipFile(DATA) as z:
 with z.open('annotations.csv') as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(rows)==500
assert [int(r['ID']) for r in rows]==list(range(500))
out={'metadata':{'dataset':'SceneEval-500_v250610','source':SRC,'sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),
  'human_annotations':100,'vlm_assisted_annotations':400,'transformer':'regex + finite vocabulary; no learned model calls',
  'limitations':'Exploratory curated lexicon, support/spatial relations and attributes not evaluated; annotations not used as parser input. Counts are not physics.',
  'model_comparison':'existing old shelter translator has fixed four roles; no same-prompt model comparison was performed'},
     'results':{}}
for name,part in [('human_curated_first_100',rows[:100]),('vlm_assisted_remaining_400',rows[100:]),('all_500',rows)]:
 out['results'][name]={mode:report(part,mode) for mode in ('legacy','lexicon')}
out['preparsed_human_100']=[{'id':r['ID'],'description':r['Description'],'predicted':extract(r['Description'])} for r in rows[:100]]
print(json.dumps({key:{m:{k:round(v,4) for k,v in r.items() if k in ('f1','exact_scene_rate','recall','precision','prompts')}
 for m,r in data.items()} for key,data in out['results'].items()},indent=2))
import sys
output_arg=next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith('--output=')), 'sceneeval_counts_exploratory.json')
if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_.-]*\.json', output_arg):raise ValueError('Unsafe filename')
p=Path(__file__).with_name(output_arg)
with p.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
