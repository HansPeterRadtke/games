import json,time,urllib.request,pathlib,datetime
base=pathlib.Path(__file__).resolve().parents[1]/'research'/'2026-10-10'
data=json.loads((base/'scene-progression-20261010.json').read_text())
def compact(k):
 return [{'id':x['id'],'kind':x['kind'],'condition':x['condition'], 'lit':x.get('lit'),'wet':x.get('wet'),'position_m':x.get('position'), 'size_m':x.get('size'),'support_id':x.get('support')}for x in data[k]['objects']]
input_obj={'phase_1':compact('lit'),'phase_2':compact('burned')}
prompt=('You are an observer of a small simulated game world. Describe these TWO moments using ONLY the supplied structured object state and geometry. No invented events, no unobserved past, no extra objects. '
        'The two phases may differ. '
        'Output short factual descriptions in English and answer two yes/no state questions: is paper burning in phase 1, and is the note readable in phase 2?\nJSON STATE:\n'+json.dumps(input_obj,separators=(',',':'))+'\nONLY JSON.')
schema={'type':'object','properties':{'phase1':{'type':'string'},'phase2':{'type':'string'},'paper_burning_phase1':{'type':'boolean'},'note_readable_phase2':{'type':'boolean'}},'required':['phase1','phase2','paper_burning_phase1','note_readable_phase2'],'additionalProperties':False}
payload={'prompt':prompt,'n_predict':200,'temperature':0,'top_k':6,'json_schema':schema,'stream':False}
t=time.monotonic();err=None;raw={};parsed=None
try:
 req=urllib.request.Request('http://jetson.lan:14829/completion',data=json.dumps(payload).encode(),method='POST',headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=85)as resp:raw=json.loads(resp.read(200000).decode())
 parsed=json.loads(raw['content'])
except Exception as e:err=f'{type(e).__name__}: {e}'
answer={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':'Qwen3.8-27B','duration':round(time.monotonic()-t,2),'input':input_obj,'result':parsed,'error':err,'token_count':raw.get('tokens_predicted'),'stopped':raw.get('stopped_eos')}
(base/'inverse-result.json').write_text(json.dumps(answer,indent=2))
print(json.dumps({k:answer[k]for k in ['duration','result','error','token_count','stopped']},ensure_ascii=False))
