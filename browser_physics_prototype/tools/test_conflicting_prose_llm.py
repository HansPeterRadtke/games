import json,time,urllib.request,pathlib,datetime
base=pathlib.Path(__file__).resolve().parents[1]/'research'/'2026-10-10'
data=json.loads((base/'scene-progression-20261010.json').read_text())
state={x['kind']:{'condition':x.get('condition'),'lit':x.get('lit'),'water':x.get('water')}for x in data['burned']['objects']}
conflict={'old_description':'An undamaged wooden bench supports a legible handwritten warning. The shelter is clean. A small lit candle stands on the bench.', 'current_structured_state':state,'completed_world_events':[e['type'] for e in data['events']]}
prompt=('You are the scene narrator in a simulated game world. The old description may be obsolete. The structured CURRENT STATE is authoritative, and completed events explain how it changed. Write a concise current description without inventing new events or resurrecting destroyed items. Can the note still be read? Is the bench still physically present? Reply ONLY JSON.\n'+json.dumps(conflict,separators=(',',':')))
schema={'type':'object','properties':{'now':{'type':'string'},'note_readable':{'type':'boolean'},'bench_still_present':{'type':'boolean'}},'required':['now','note_readable','bench_still_present'],'additionalProperties':False}
payload={'prompt':prompt,'n_predict':145,'temperature':0,'top_k':8,'json_schema':schema,'stream':False}
t=time.monotonic();parsed=None;err=None;raw={}
try:
 req=urllib.request.Request('http://jetson.lan:14829/completion',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=75)as resp:raw=json.loads(resp.read(100000).decode());parsed=json.loads(raw['content'])
except Exception as e:err=f'{type(e).__name__}: {e}'
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':'Qwen3.8-27B','duration':round(time.monotonic()-t,2),'input':conflict,'output':parsed,'error':err,'tokens':raw.get('tokens_predicted')}
(base/'conflicting-prose-result.json').write_text(json.dumps(record,indent=2));print(json.dumps({k:record[k]for k in ['duration','output','error','tokens']}))
