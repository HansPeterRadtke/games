#!/usr/bin/env python3
"""Small reverse-language feasibility check; does not affect live gameplay without review."""
import datetime,hashlib,json,pathlib,time,urllib.request
base=pathlib.Path(__file__).resolve().parents[1]
prompt=('Rewrite this observed aftermath as one concise descriptive English paragraph for a game world: '
        'The shelter roof is smoke-stained. The wooden bench is scorched but still standing. '
        'The note is unreadable ash. The candle remains lit. The water jug remains full. '
        'The paragraph must not resurrect burned objects or invent new physical events. Return JSON.')
schema={'type':'object','properties':{'scene_prose':{'type':'string'}},'required':['scene_prose'],'additionalProperties':False}
payload={'prompt':prompt,'n_predict':125,'temperature':.05,'top_k':6,'json_schema':schema,'stream':False}
start=time.monotonic();error=None;content=None;raw={}
try:
 req=urllib.request.Request('http://jetson.lan:14829/completion',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=50) as response:raw=json.loads(response.read(1000000).decode())
 content=json.loads(raw['content'])['scene_prose']
 if not (20<len(content)<950):raise ValueError('length')
 lower=content.lower()
 if not all(any(w in lower for w in group)for group in [('ash','burned','burnt'),('scorch','blacken'),('smoke','soot')]):raise ValueError('missing required observed outcomes')
except Exception as exc:error=f'{type(exc).__name__}: {str(exc)[:200]}'
record={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'elapsed_seconds':round(time.monotonic()-start,2),'text':content,'error':error,'model':'Qwen3.8-27B','tokens_predicted':raw.get('tokens_predicted')}
path=base/'generated/llm-aftermath-compact.json';path.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'valid':error is None,'seconds':record['elapsed_seconds'],'text':content,'error':error},ensure_ascii=False))
if error:raise SystemExit(1)
