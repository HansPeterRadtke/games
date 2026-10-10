#!/usr/bin/env python3
"""Feasibility: demand revisions for place/observation contradictions in model prose."""
import json,pathlib,requests,time,hashlib,datetime,os
ROOT=pathlib.Path(__file__).resolve().parents[1];path=ROOT/'generated/story-region-bank.json'
bank=json.loads(path.read_text());
SCHEMA={'type':'object','properties':{'description':{'type':'string'},'clue':{'type':'string'}},'required':['description','clue'],'additionalProperties':False}
for scene in bank['scenes']:
 if scene['branch'] not in {'bridge_repaired','bridge_unrepaired'}:continue
 known={'bridge_repaired':'At x=23m the player repaired the footbridge and carried planks across it. At x=43m, twenty metres east, the reopened route may now show new activity. The original bridge must NOT be touching the new landmark.','bridge_unrepaired':'At x=23m the footbridge remains broken; the traveler is stranded on the WEST bank x=17m. At x=43m, twenty metres EAST, there cannot be any new footprints by that traveler. The split tree cannot touch the original bridge abutment.'}[scene['branch']]
 prompt=('Revision task for persistent physics game. You already wrote a new LANDMARK at x=43m named '+scene['title']+'. Current description: '+scene['description']+'. Landmark kind '+scene['objects'][0]['kind']+'. Factual geography: '+known+' Rewrite only the one-sentence description (14-27 words) and one short inspection clue. Keep the landmark, keep narrative continuity, avoid physical proximity contradictions. Return exactly JSON keys description, clue.')
 start=time.monotonic()
 try:
  r=requests.post('http://jetson.lan:14829/completion',json={'prompt':prompt,'json_schema':SCHEMA,'n_predict':105,'temperature':.2,'stream':False},timeout=(5,40));r.raise_for_status();out=json.loads(r.json()['content']);latency=round(time.monotonic()-start,2)
  desc=out.get('description','');clue=out.get('clue','');
  if not isinstance(desc,str) or not 40<=len(desc)<=300 or not isinstance(clue,str) or not 10<=len(clue)<=150:raise ValueError('Narrative output invalid')
  if scene['branch']=='bridge_unrepaired' and any(term in desc.lower() for term in ['abutment','footprints of the traveler','traveler\'s footprints']):raise ValueError('Geographical contradiction persists')
  if scene['branch']=='bridge_repaired' and any(term in desc.lower() for term in ['planks you used','planks you carried']):raise ValueError('Geometry contradicts tracked material')
  old=scene['description'];scene['original_description']=old;scene['description']=desc;scene['objects'][0]['description']=desc;scene['objects'][0]['interaction_clue']=clue;scene['revision_model']='Qwen3.8-27B';scene['revision_latency_s']=latency
  scene['source']=scene['source']+':coherence-edit';print('REVISED',scene['branch'],repr(desc),'latency',latency,'seconds',flush=True)
 except (requests.RequestException,KeyError,ValueError) as e:print('REJECT',scene['branch'],type(e).__name__,str(e)[:240],flush=True)

tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(bank,indent=2,ensure_ascii=False));os.replace(tmp,path)
