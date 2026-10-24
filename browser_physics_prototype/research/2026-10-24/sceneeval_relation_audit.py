#!/usr/bin/env python3
"""Source-separated relation/attribute audit for the six manually mapped
external SceneEval prompts. Unverifiable claims are NOT counted as passes.
Original SceneEval annotations are stored unchanged in the separate source file.
"""
import json,math,re,sys
from pathlib import Path
ROOT=Path(__file__).parent
res=json.loads((ROOT/'prse_semantic_physics_results_v4.json').read_text())
source=json.loads((ROOT/'sceneeval_six_source_annotations.json').read_text())['selected']
alias={'television':'TV','dining-table':'dining_table','floor-lamp':'floor_lamp',
       'office-desk':'office_desk','sofa-chair':'sofa_chair'}
def cat(e,scene):
 k=alias.get(e['kind'],e['kind'])
 if scene=='sceneeval-dining-15' and k=='chair':return 'dining_chair'
 return k
def distance(a,b):
 pa=a['position'];pb=b['position'];return math.hypot(pa['x']-pb['x'],pa['z']-pb['z'])
def evaluate(rule,parent,children):
 if not parent or not children:return 'fail','Named scene entities are missing'
 if rule=='on':
  ok=any(b.get('supportId')==a['id'] for a in parent for b in children)
  return ('pass' if ok else 'fail'),'Verified authored physical support ID, not visual contact proof'
 if rule=='near':
  ok=min(distance(a,b) for a in parent for b in children)<2.5
  return ('pass' if ok else 'fail'),'Threshold-near is a provisional spatial heuristic'
 if rule=='next_to':
  ok=any(abs(a['position']['z']-b['position']['z'])<1.0
   and abs(a['position']['x']-b['position']['x'])-(a['size']['x']+b['size']['x'])/2<.6
   for a in parent for b in children)
  return ('pass' if ok else 'fail'),'Approximate side-adjacency; no room geometry'
 if rule=='front':
  ok=any(b['position']['z']<a['position']['z']-.3 for a in parent for b in children)
  return ('pass' if ok else 'fail'),'Conventional camera axis assumed; no viewer orientation'
 if rule=='surround':
  if len(children)<3:return 'fail','Insufficient objects around landmark'
  near=[b for b in children if min(distance(a,b) for a in parent)<3.5]
  sides={('L' if b['position']['x']<parent[0]['position']['x']-.3 else
          'R' if b['position']['x']>parent[0]['position']['x']+.3 else
          'F' if b['position']['z']>parent[0]['position']['z']+.3 else 'B')
          for b in near}
  return ('pass' if len(sides)>=3 else 'fail'),'At least three distinct surrounding sectors'
 return 'unverifiable','Requires wall/door geometry, orientation or interaction semantics absent from plan'
logs=[];count={'pass':0,'fail':0,'unverifiable':0}
for plan in res['roomPlans']:
 sid=str(next(x['sourceId'] for x in res['sourceCountResults'] if x['id']==plan['id']))
 annotated=source[sid];entities=plan['entities'];records=[]
 for spec in filter(None,[x.strip() for x in annotated['relations'].split(';')]):
  fields=[v.strip() for v in spec.split(',')];op=fields[0]
  if len(fields)<6:continue
  try:weight=int(fields[1])
  except ValueError:weight=1
  rule=fields[2];parent=fields[4];child=fields[5].split(':')[0]
  a=[e for e in entities if cat(e,plan['id'])==parent]
  b=[e for e in entities if cat(e,plan['id'])==child]
  state,reason=evaluate(rule,a,b)
  if op not in ['eq','ge']:state='unverifiable'
  count[state]+=weight
  records.append({'annotation':spec,'state':state,'reason':reason,'multiplicity':weight})
 for spec in filter(None,[x.strip() for x in annotated['roomRelations'].split(';')]):
  try:weight=int(spec.split(',')[1])
  except (IndexError,ValueError):weight=1
  count['unverifiable']+=weight
  records.append({'annotation':spec,'state':'unverifiable',
                  'reason':'No wall/room/door boundary geometry in these manually mapped scenes','multiplicity':weight})
 for spec in filter(None,[x.strip() for x in annotated['attributes'].split(';')]):
  fields=[v.strip() for v in spec.split(',')]
  try:weight=int(fields[1])
  except (ValueError,IndexError):weight=1
  count['unverifiable']+=weight
  records.append({'annotation':spec,'state':'unverifiable',
                  'reason':'No independently measured style, color or exact object-attribute grounding','multiplicity':weight})
 logs.append({'sceneId':plan['id'],'sourceId':sid,'claims':records})
result={'provenance':'SceneEval-500 externally annotated test descriptions; manually authored 3D plans evaluated',
 'method':'No learned scene generation; relation heuristics deliberately limited, unsupported claims are not passed',
 'count':count,'cases':logs}
name=next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith('--output=')), 'sceneeval_relation_audit_results.json')
if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_.-]*\.json',name):raise ValueError('Unsafe filename')
with (ROOT/name).open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps({'number_claims':sum(len(r['facts']) for r in res['sourceCountResults']),
 'relation_and_attribute_claims':sum(count.values()),'relation_and_attribute_status':count,
 'room_count':len(logs)},indent=2))
