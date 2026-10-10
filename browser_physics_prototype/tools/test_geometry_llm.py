import json,time,urllib.request,pathlib,datetime
base=pathlib.Path(__file__).resolve().parents[1]/'research'/'2026-10-10'
scenes=[]
for title,candle_y in [('A',.525),('B',1.525),('C',.225)]:
 scenes.append({'case':title,'objects':[{'id':'bench','center_m':[0,.225,0],'half_extents_m':[.9,.225,.2]},{'id':'candle','center_m':[.3,candle_y,0],'half_extents_m':[.04,.075,.04]}]})
prompt=('3D game geometry task. Coordinates are x,y,z in metres, Y is vertical up. Each cuboid has a CENTER and HALF-EXTENTS. Classify whether the candle in each case has its BOTTOM exactly on the bench TOP, is FLOATING above it, or is INTERSECTING the bench volume. Assume no other supports or forces. No story, no imagination. Reply JSON.\n'+json.dumps(scenes,separators=(',',':'))+'\n')
schema={'type':'object','properties':{q:{'type':'string','enum':['supported','floating','intersecting']}for q in ['A','B','C']},'required':['A','B','C'],'additionalProperties':False}
payload={'prompt':prompt,'n_predict':90,'temperature':0,'top_k':8,'json_schema':schema,'stream':False}
t=time.monotonic();err=None;raw={};parsed=None
try:
 req=urllib.request.Request('http://jetson.lan:14829/completion',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=75)as resp:raw=json.loads(resp.read(100000).decode());parsed=json.loads(raw['content'])
except Exception as e:err=f'{type(e).__name__}: {e}'
answer={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duration':round(time.monotonic()-t,2),'model':'Qwen3.8-27B','cases':scenes,'predicted':parsed,'expected':{'A':'supported','B':'floating','C':'intersecting'},'error':err,'tokens':raw.get('tokens_predicted')};answer['correct']=sum(parsed.get(k)==v for k,v in answer['expected'].items())if parsed else 0
(base/'geometry-result.json').write_text(json.dumps(answer,indent=2));print(json.dumps({k:answer[k]for k in ['duration','predicted','expected','correct','error','tokens']}))
