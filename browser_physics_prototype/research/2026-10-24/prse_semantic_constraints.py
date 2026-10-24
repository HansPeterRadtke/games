#!/usr/bin/env python3
"""Explicit small deterministic scene interpreter, *not* an LLM or complete NLP.

Inputs are ONLY external SceneEval text, never gold labels. Emits a provenance-
bearing constraint proposal; unknown relations and attributes are abstentions.
The official annotations are read separately only by the benchmark script.
"""
import ast
import re
import json
from pathlib import Path
from collections import defaultdict

HERE=Path(__file__).parent
baseline=ast.parse((HERE/'sceneeval_baseline.py').read_text())
LEXICON=next(ast.literal_eval(node.value) for node in baseline.body
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in node.targets))
LEXICON={
 **LEXICON,
 'bunk_bed':['bunk bed','bunk beds'],
 'fridge':['fridge','fridges','mini fridge','mini fridges'],
 'light':['light','lights'],
 'ceiling_light':['ceiling light','ceiling lights'],
 'pendant_light':['pendant light','pendant lights'],
 'wall_light':['wall light','wall lights'],
 'wall_cabinet':['wall cabinet','wall cabinets'],
 'wine_cabinet':['wine cabinet','wine cabinets'],
 'bar_stool':['bar stool','bar stools'],
 'bar_table':['bar table','bar tables'],
 'dining_chair':['dining chair','dining chairs'],
 'office_chair':['office chair','office chairs'],
 'office_desk':['office desk','office desks'],
 'sofa_chair':['sofa chair','sofa chairs'],
 'floor_cushion':['floor cushion','floor cushions'],
 'bean_bag':['bean bag','bean bags'],
 'tv_stand':['tv stand','tv stands'],
 'toy_box':['toy box','toy boxes'],
 'doll':['doll','dolls'],
 'monitor':['monitor','monitors'],
 'cup':['cup','cups'],
 'jug':['jug','jugs'],
 'potted_plant':['potted plant','potted plants'],
 'clock':['clock','clocks'],
 'tray':['tray','trays'],
 'electronic_peripheral':['electronic peripheral','electronic peripherals'],
 'wall_shelf':['wall shelf','wall shelves'],
 'display_shelf':['display shelf','display shelves'],
 'bookcase':['bookcase','bookcases'],
 'bar_chair':['bar chair','bar chairs'],
 'teapot':['teapot','teapots'],
 'floor_lamp':['floor lamp','floor lamps']
}
# Map semantically exact variants for official labels. Broader taxonomy mergers
# are explicitly not assumed (e.g. bookcase != bookshelf in the benchmark).
NAME_MAP={
 'television':'TV',
 'refrigerator':'fridge',
 'bunk_bed':'bed',
 'fridge':'fridge',
 'bedside_lamp':'lamp'
}
def canon(x):
 return NAME_MAP.get(x.lower().replace(' ','_'),x.replace(' ','_'))
COUNTS={'a':1,'an':1,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,
        'seven':7,'eight':8,'nine':9,'ten':10}
QUANT=r'(at\s+least\s+|more\s+than\s+)?(zero|no|one|two|three|four|five|six|seven|eight|nine|ten|\d+|a|an)'
ADJ=(r'(?:old|large|small|big|little|modern|blue|black|white|red|green|wooden|marble|'
    r'round|square|metal|king-size|king size|double|single|twin|queen|two-seater|four-seater|'
    r'wall-mounted|tiny|mini|large-sized|adjacent|long|short|brown|grey|gray|antique|'
    r'minimal|display|hanging|floor|narrow|rectangular|wide|beautiful|well-lit|soft|'
    r'wood|office|dining|simple|standard|low|high)')
PROPS=['blue','red','green','black','white','brown','gray','grey','wooden',
       'marble','metal','large','small','king-size','double','queen','twin','square','round','long','short']
PROP_MAP={'wooden':'wooden','king-size':'king_size','gray':'grey'}
PREDICATES={
 'next to':'next', 'beside':'next', 'adjacent to':'adjacent', 'near':'near',
 'on top of':'on','on':'on', 'in front of':'front','behind':'behind','above':'above',
 'under':'under','beneath':'under','across from':'across','opposite':'opposite',
 'to the left of':'left','to the right of':'right','left of':'left','right of':'right',
 'around':'surround','surrounding':'surround','against':'against','in the corner of':'corner',
 'in the corners of':'corner','in the middle of':'middle', 'in the center of':'center',
 'on each side of':'side_of','on the long side of':'long_side',
 'on the short side of':'short_side'
}
PREDICATE_RE=re.compile(r'\b(?:'+ '|'.join(re.escape(k) for k in sorted(PREDICATES,key=len,reverse=True))+r')\b',re.I)
ROOM_ANCHORS={'wall','walls','room','door','ceiling','floor','window','windows','corner'}
def mentions(text):
 candidates=[]
 for cls,terms in LEXICON.items():
  for term in terms:
   for m in re.finditer(r'\b'+re.escape(term)+r'\b',text,re.I):
    candidates.append({'start':m.start(),'end':m.end(),'type':canon(cls),
        'matched':text[m.start():m.end()], 'term':term})
 candidates.sort(key=lambda x:(-(x['end']-x['start']),x['start']))
 selected=[]
 for m in candidates:
  if not any(m['start']<a['end'] and m['end']>a['start'] for a in selected):
   selected.append(m)
 return sorted(selected,key=lambda x:x['start'])

def quantify(text,m):
 prefix=text[max(0,m['start']-92):m['start']].lower()
 # A noun may follow a quantity and several adjectives. Bound to the nearest
 # phrase ending at the noun, rather than grabbing a number from previous item.
 match=re.search(r'\b'+QUANT+r'\s+(?:'+ADJ+r'\s+){0,5}$',prefix)
 if match:
  n=match.group(2)
  num=0 if n in ('no','zero') else COUNTS.get(n,int(n) if n.isdigit() else 1)
  op='ge' if match.group(1) and match.group(1).strip().startswith('at least') else 'gt' if match.group(1) else 'eq'
  return num,op,'quantified',prefix[match.start():].strip()
 # Short exact negation window, not whole preceding sentence.
 if re.search(r'\b(?:no|without(?:\s+any)?|lacks?|not\s+(?:a|an|any))\s+(?:'+ADJ+r'\s+){0,3}$',
              text[max(0,m['start']-40):m['start']].lower()):
  return 0,'eq','negative','negated mention'
 return 1,'eq','unquantified','implicit singular; may be uncertain'
def interpret(text,source_id='unknown'):
 if not isinstance(text,str) or len(text)>6000:raise ValueError('Invalid text')
 names=mentions(text)
 interpreted=[]
 for m in names:
  n,op,confidence,evidence=quantify(text,m)
  pre=text[max(0,m['start']-65):m['start']].lower()
  # Modifiers are only trusted in a narrow pre-noun span; do not let an
  # attribute from the previous enumerated object contaminate this object.
  phrase=re.search(r'((?:(?:'+ADJ+r')\s+){1,5})$',pre)
  properties=[]
  if phrase:
   properties=[PROP_MAP.get(w,w) for w in PROPS if re.search(r'\b'+re.escape(w)+r'\b',phrase.group(1))]
  interpreted.append({**m,'quantity':n,'op':op,'certainty':confidence,
                      'quantityEvidence':evidence,'attributes':sorted(set(properties))})
 quantities={}
 for m in interpreted:
  k=m['type']
  if k not in quantities:quantities[k]={'count':m['quantity'],'op':m['op']}
  else:
   prior=quantities[k]
   if m['quantity']>prior['count']:prior.update(count=m['quantity'],op=m['op'])
   # A repeated reference does not silently create a duplicate entity.
   # Presence and absence in two clauses is a conflict, left unresolved.
 conflicting=[k for k in quantities if any(m['type']==k and m['quantity']==0 for m in interpreted)
           and any(m['type']==k and m['quantity']>0 for m in interpreted)]
 for k in conflicting:quantities[k]['ambiguous']=True
 relations=[]
 for match in PREDICATE_RE.finditer(text):
  key=PREDICATES[match.group(0).lower()]
  left=[m for m in interpreted if m['end']<=match.start() and match.start()-m['end']<75 and m['quantity']>0]
  # Within the current clause only; never let 'against the wall, and a lamp'
  # hallucinate that the wall relation targets the later lamp.
  following=text[match.end():min(len(text),match.end()+60)]
  sep=re.search(r'[,.;]|\band\s+(?:a|an|at least|two|three)\b',following,re.I)
  local=following[:sep.start()] if sep else following
  right=[m for m in interpreted if m['start']>=match.end()
         and m['start']<match.end()+len(local) and m['quantity']>0]
  anchors=[(v.start(),v.group(0).lower()) for v in
   re.finditer(r'\b(?:wall|walls|room|door|ceiling|floor|window|windows|corner)\b',local,re.I)]
  l=left[-1] if left else None
  r=right[0] if right else None
  # If an explicit room boundary noun precedes an entity mention, treat the
  # relation as a room constraint, NOT a future object-to-object relation.
  if anchors and (r is None or anchors[0][0]<r['start']-match.end()):r=None
  segment=text[max(0,match.start()-45):min(len(text),match.end()+65)]
  if not l:continue
  if key in {'corner','middle','center'}:
   relation={'kind':'room','type':key,'a':l['type'],'b':'room',
         'sourceText':segment,'confidence':'phrase_match'}
  elif r:
   # X on Y => child X / support Y; retain ordered roles in addition to
   # benchmark's symmetric type-pair evaluation.
   relation={'kind':'object','type':key,'a':l['type'],'b':r['type'],
      'sourceText':segment,'confidence':'phrase_match'}
  elif anchors:
   relation={'kind':'room','type':key,'a':l['type'],'b':anchors[0][1],
      'sourceText':segment,'confidence':'phrase_match'}
  else:continue
  if relation not in relations and not any(
   z['type']==relation['type'] and z['a']==relation['a'] and z['b']==relation['b']
     for z in relations):relations.append(relation)
 return {'sourceId':str(source_id),'text':text,'quantities':quantities,
   'mentions':interpreted,'relations':relations,
   'unresolved':{'conflictingQuantityTypes':conflicting,
    'unsupportedConditions':'Coreference, implicit supports, rotation and full room topology are NOT solved'}}
if __name__=='__main__':
 for s in [
  'There is no coffee table, but a sofa and a TV on a TV stand.',
  'A room contains a wooden table with two red books on top of the table.',
  'There is at least one nightstand next to the bed.',
  'A blue lamp near a sofa in front of a bed.'
 ]:print(json.dumps(interpret(s),indent=2))
