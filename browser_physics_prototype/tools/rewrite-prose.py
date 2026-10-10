#!/usr/bin/env python3
"""Physical consequences back into coherent LLM prose: explicit offline doability."""
import json, pathlib, urllib.request,time,datetime,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
source=json.loads((root/'generated/llm-scene-study.json').read_text())
statuses={'shelter-setting':'smoky','shelter-bench':'scorched','shelter-candle':'lit','shelter-note':'ashes','shelter-jug':'intact_water'}
labels=['shelter-setting','shelter-bench','shelter-candle','shelter-note','shelter-jug']
schema={'type':'object','properties':{'scene_prose':{'type':'string'},'updates':{'type':'array','minItems':5,'maxItems':5,'items':{'type':'object','properties':{'id':{'type':'string','enum':labels},'condition':{'type':'string','enum':['smoky','scorched','lit','ashes','intact_water']},'description':{'type':'string'}},'required':['id','condition','description'],'additionalProperties':False}}},'required':['scene_prose','updates'],'additionalProperties':False}
prompt=('Rewrite this small game scene in ordinary literary prose AFTER an offscreen accident. Keep exactly the five objects and their identity; do not invent new physical objects. '
 'The note is UNREADABLE ASH, NOT a readable warning. The wooden bench is still present but SCORCHED, not destroyed. The candle remains lit. The shelter roof is smoke-stained; no complete building collapse. The clay jug still has water. '
 'Reflect all these durable facts accurately and keep descriptions concise, plausible and coherent. Return only JSON. '
 'Original scene: '+source['scene_description']+'\nConfirmed physical and semantic outcomes: '+json.dumps(statuses))
payload={'prompt':prompt,'n_predict':300,'temperature':.15,'json_schema':schema,'top_k':12,'stream':False}
start=time.monotonic();error=None;result=None;raw={}
try:
 req=urllib.request.Request('http://jetson.lan:14829/completion',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=90) as resp:raw=json.loads(resp.read(1000000).decode())
 result=json.loads(raw['content'])
 if set(item['id'] for item in result['updates'])!=set(labels):raise ValueError('mismatched scene identities')
 if any(item['condition']!=statuses[item['id']] for item in result['updates']):raise ValueError('contradictory structural outcomes')
 if not 30<len(result['scene_prose'])<1400 or any(not 3<len(item['description'])<350 for item in result['updates']):raise ValueError('out-of-range language')
except Exception as ex:error=f'{type(ex).__name__}: {str(ex)[:250]}'
doc={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'model':'Qwen3.8-27B','elapsed_seconds':round(time.monotonic()-start,2),'source_scene_id':source['scene_id'],'physical_outcomes':statuses,'output':result,'error':error,'tokens_predicted':raw.get('tokens_predicted')}
path=root/'generated'/'llm-aftermath-study.json';path.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'elapsed_seconds':doc['elapsed_seconds'],'valid':error is None,'error':error,'result':result},ensure_ascii=False));
if error:raise SystemExit(1)
