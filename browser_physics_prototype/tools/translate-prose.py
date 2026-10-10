#!/usr/bin/env python3
"""LLM -> data doability. Never evaluate generated code, always validate physical geometry.
Live inference runs only as an explicit offline build step; the browser loads validated JSON.
"""
import argparse, hashlib, json, pathlib, time, urllib.request, datetime

ROOT=pathlib.Path(__file__).resolve().parents[1]
SCENE={
 'id':'riverside-shelter','anchor_x':37.0,
 'prose':('On the far bank, a rain-worn wooden shelter stands against the forest. '
          'Inside there is a long oak bench resting on the floor. '
          'A small beeswax candle stands on the bench in a metal holder. '
          'A clay water jug rests on the ground beside the bench. '
          'A handwritten note lies on the bench. It warns that the old woods are vulnerable to fire. '
          'The scene should feel like an abandoned but believable place.'),
}
KIND=['bench','candle','jug','note']
SCHEMA={'type':'object','properties':{'scene_description':{'type':'string'},'objects':{'type':'array','minItems':4,'maxItems':4,'items':{'type':'object','properties':{
 'id':{'type':'string','enum':KIND},'kind':{'type':'string','enum':KIND},'name':{'type':'string'},'description':{'type':'string'},
 'x':{'type':'number'},'y':{'type':'number'},'z':{'type':'number'},'width':{'type':'number'},'height':{'type':'number'},'depth':{'type':'number'},'mass':{'type':'number'},'support':{'type':'string','enum':['floor','bench']},
 },'required':['id','kind','name','description','x','y','z','width','height','depth','mass','support'],'additionalProperties':False}}},'required':['scene_description','objects'],'additionalProperties':False}

def validate(o):
 if not isinstance(o,dict) or set(o)!={'scene_description','objects'}:return (False,'top-level schema')
 if not isinstance(o['scene_description'],str) or len(o['scene_description'])>2000:return(False,'scene prose')
 a=o['objects'];
 if not isinstance(a,list) or len(a)!=4 or set(v.get('id')for v in a)!={*KIND}:return(False,'missing or duplicate objects')
 for v in a:
  if v['id']!=v['kind']:return(False,'kind identity mismatch')
  if v['support'] not in ('bench','floor'):return(False,'unsupported support')
  if v['support']=='bench' and v['kind'] not in ('candle','note'):return(False,'impossible support type')
  if v['kind']=='bench' and v['support']!='floor':return(False,'bench cannot float')
  if v['kind']=='jug' and v['support']!='floor':return(False,'jug should be floor object')
  if not isinstance(v['name'],str) or len(v['name'])>90 or not isinstance(v['description'],str) or len(v['description'])>700:return(False,'bad prose')
  import math
  for key in ['x','y','z','width','height','depth','mass']:
   if not isinstance(v[key],(float,int)) or not math.isfinite(v[key]):return(False,'nonfinite dimensions')
  if not (-3<v['x']<3 and -.8<v['z']<.8 and 0<v['y']<4):return(False,'out of bounds')
  if not all(.008<=v[k]<4 for k in ['width','height','depth']):return(False,'invalid size')
  if not .0001<v['mass']<400:return(False,'invalid mass')
 bench=next(v for v in a if v['kind']=='bench')
 if not (1.0<=bench['width']<=3.0 and .35<=bench['height']<=1.3):return(False,'bench implausible')
 return(True,'valid; support reconstruction still required')

parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=['direct','relations'],default='relations');parser.add_argument('--out',default=str(ROOT/'generated'/'llm-scene-study.json'));parser.add_argument('--endpoint',default='http://jetson.lan:14829/completion');args=parser.parse_args()

intro='Translate prose into a physically plausible small 3D game scene. All dimensions in METRES, mass in kilograms. x east-west, y upward, z depth. Positions are object CENTRES relative to shelter origin. Output exactly one instance each id bench, candle, jug, note. Names/descriptions must respect the given story. Do not add objects.'
if args.profile=='relations':intro+=' Crucially: the candle and note REST ON the bench (support=bench). The bench and jug REST ON the floor (support=floor). Use physically plausible masses/dimensions and positions. Do not place supported objects below their support surface; relative positions may be validated and corrected during physical materialization.'
else:intro+=' Use support=bench for small objects placed on the bench, and floor for things on the floor.'
prompt=intro+'\nSTORY:\n'+SCENE['prose']+'\nReturn ONLY JSON.'
payload={'prompt':prompt,'n_predict':700,'temperature':0.1,'top_k':10,'json_schema':SCHEMA,'stream':False}
start=time.monotonic();body=json.dumps(payload).encode();request=urllib.request.Request(args.endpoint,data=body,headers={'Content-Type':'application/json'},method='POST');
try:
 with urllib.request.urlopen(request,timeout=75) as response:
  raw=json.loads(response.read(1500000).decode())
 result=json.loads(raw['content']);ok,reason=validate(result)
except Exception as e:
 result=None;ok=False;reason=type(e).__name__+': '+str(e)[:300];raw={}
meta={'schema_version':1,'scene_id':SCENE['id'],'source_prose':SCENE['prose'],'anchor_x':SCENE['anchor_x'],'model':'Qwen3.8-27B-Q3_K_XL','endpoint':'Jetson llama.cpp /completion','profile':args.profile,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-start,2),'valid':ok,'validation':reason,'objects':result['objects'] if result else [],'scene_description':result['scene_description'] if result else '', 'tokens_predicted':raw.get('tokens_predicted')}
p=pathlib.Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'valid':ok,'reason':reason,'duration':meta['elapsed_seconds'],'model_tokens':meta['tokens_predicted'],'objects':[(v['kind'],v['x'],v['y'],v['width'],v['height'],v['support'])for v in meta['objects']],'file':str(p)},ensure_ascii=False));
if not ok:raise SystemExit(1)
