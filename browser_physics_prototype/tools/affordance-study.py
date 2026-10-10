#!/usr/bin/env python3
"""Bounded local LLM proposal of object interactions, not executable game logic."""
import json,urllib.request,time,hashlib,pathlib,datetime
root=pathlib.Path(__file__).resolve().parents[1]
verbs=['light','extinguish','tip','read','ignite','pour','inspect']
ids=['bench','candle','jug','note']
scene=json.loads((root/'generated'/'llm-scene-study.json').read_text())
schema={'type':'object','properties':{'actions':{'type':'array','minItems':3,'maxItems':7,'items':{'type':'object','properties':{'object_id':{'type':'string','enum':ids},'verb':{'type':'string','enum':verbs},'label':{'type':'string'}},'required':['object_id','verb','label'],'additionalProperties':False}}},'required':['actions'],'additionalProperties':False}
allowed={'bench':{'inspect'},'candle':{'light','extinguish','tip','inspect'},'jug':{'pour','inspect'},'note':{'read','ignite'}}
prompt=('Analyze object descriptions from a game scene and list seven physically sensible interactions the player might try. '
        'Choose allowed verbs and objects only. Do not invent physical outcomes or executable code. '
        'Favor lighting a candle, reading the paper, and using water. Return one concise JSON object. '
        +json.dumps([{k:o[k]for k in ['id','description']}for o in scene['objects']],ensure_ascii=False))
payload={'prompt':prompt,'n_predict':290,'temperature':.15,'top_k':12,'json_schema':schema,'stream':False}
start=time.monotonic();raw={};problem=None
try:
 request=urllib.request.Request('http://jetson.lan:14829/completion',headers={'Content-Type':'application/json'},data=json.dumps(payload).encode(),method='POST')
 with urllib.request.urlopen(request,timeout=85)as response:raw=json.loads(response.read(1000000).decode())
 response=json.loads(raw['content']);proposal=response['actions'];
 if not isinstance(proposal,list) or not 3<=len(proposal)<=7:raise ValueError('unexpected count')
 seen=set();valid=[];rejected=[]
 for a in proposal:
  if isinstance(a,dict) and a.get('verb')in allowed.get(a.get('object_id'),set()) and isinstance(a.get('label'),str) and 0<len(a['label'])<=70 and (a['object_id'],a['verb'])not in seen:
   valid.append(a);seen.add((a['object_id'],a['verb']))
  else:rejected.append(a)
except Exception as error:problem=f'{type(error).__name__}: {str(error)[:240]}';valid=[];rejected=[];proposal=[]
record={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'model':'Qwen3.8-27B','duration_seconds':round(time.monotonic()-start,2),'proposed':proposal,'accepted':valid,'rejected':rejected,'problem':problem,'total_tokens':raw.get('tokens_predicted')}
p=root/'generated'/'llm-affordances.json';p.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:record[k]for k in ['duration_seconds','total_tokens','accepted','rejected','problem']},ensure_ascii=False));
if problem:raise SystemExit(1)
