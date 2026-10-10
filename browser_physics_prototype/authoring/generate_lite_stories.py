#!/usr/bin/env python3
"""Bounded local LLM prose authoring; separately derived safe physical templates.

The LLM owns descriptions, names and interactions. Existing tested scene geometry
owns collisions. This is explicitly not the LLM generating physics values.
"""
import pathlib,json,sys,requests,datetime,hashlib,time,os,math,importlib.util
MOD_PATH=pathlib.Path(__file__).parent/'generate_story_regions.py'
spec=importlib.util.spec_from_file_location('fullstory',MOD_PATH)
full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
SCHEMA={'type':'object','properties':{'title':{'type':'string'},'description':{'type':'string'},'kind':{'type':'string','enum':['rock','tree','spring','shelter']},'clue':{'type':'string'}},'required':['title','description','kind','clue'],'additionalProperties':False}
TEMPLATES={
 'rock':(.83,.42,.68,.83,.72,850),
 'tree':(1.7,2.3,1.5,4.6,1.5,220),
 'spring':(1.1,.16,1.12,.32,.8,60),
 'shelter':(2,1.32,2.1,2.64,1.9,1300),
}
def geometric(scenario,data,latency,tokens):
    kind=data['kind'];width,center,width2,height,depth,mass=TEMPLATES[kind]
    # Use constant, tested arrangement, distinct spatial identities and source lineage.
    return {'region':scenario['region'],'branch':scenario['branch'],'anchor':scenario['anchor'],'title':data['title'],'description':data['description'],
     'source':'local-llm:Qwen3.8-27B:shortprose:'+hashlib.sha256((scenario['context']+data['title']).encode()).hexdigest()[:16],
     'geometrySource':'validated-layout-template-v1','latency_s':latency,'tokens':tokens,'objects':[
      {'name':data['title'],'kind':kind,'description':data['description'],'interaction_clue':data['clue'],'offset_x_m':-2.45,'center_height_m':center,'width_m':width2,'height_m':height,'depth_m':depth,'mass_kg':mass},
      {'name':'Weather-worn trail marker','kind':'destination','description':'A small hand-carved trail marker indicates an old route through the valley.','interaction_clue':'The carving may be easier to interpret from another angle.','offset_x_m':2.9,'center_height_m':.65,'width_m':.24,'height_m':1.3,'depth_m':.24,'mass_kg':9.5}
     ]}

def main():
    selected=sys.argv[1:] or ['bridge_repaired','bridge_unrepaired']
    art=full.ARTIFACT;art.parent.mkdir(exist_ok=True,parents=True)
    pack=json.loads(art.read_text()) if art.is_file() else {'version':1,'model':'Qwen3.8-27B','scenes':[]}
    scenes={(r['region'],r['branch']):r for r in pack['scenes']}
    for scenario in full.SCENARIOS:
        if scenario['branch'] not in selected:continue
        key=(scenario['region'],scenario['branch'])
        if key in scenes:print('CACHED',scenario['branch'],flush=True);continue
        prompt='You write an evolving persistent game world. Context: '+scenario['context']+' A new valley region is ahead. Describe one memorable, physically plausible landmark and hint of its relationship to what the player did. Use 12-27 words of atmospheric description and one short clue. No grand revelations, no contradictions, no repetition. The response is JSON with exactly keys title, description, kind and clue. The kind is rock, tree, spring or shelter.'
        start=time.monotonic();status=''
        try:
            raw=requests.post(full.MODEL_URL,json={'prompt':prompt,'temperature':.3,'n_predict':160,'stream':False,'json_schema':SCHEMA},timeout=(5,65));raw.raise_for_status();out=raw.json();data=json.loads(out['content']);latency=round(time.monotonic()-start,2)
            if data.get('kind') not in TEMPLATES or not all(isinstance(data.get(k),str) and 4<len(data[k])<=400 for k in ['title','description','clue']):raise ValueError('Invalid short narrative')
            scene=geometric(scenario,data,latency,out.get('tokens_predicted'))
            reason=full.validate(scene,scenario)
            if reason:raise ValueError(reason)
            scenes[key]=scene;status=f'ACCEPT {scenario["branch"]} {scene["title"]!r} latency={latency} seconds tokens={scene["tokens"]}'
        except (requests.RequestException,ValueError,KeyError,TypeError) as e:status=f'REJECT {scenario["branch"]} {type(e).__name__}: {e}'
        print(status,flush=True)
    pack={'version':1,'model':'Qwen3.8-27B','scenes':list(scenes.values())};tmp=art.with_suffix('.json.tmp');tmp.write_text(json.dumps(pack,ensure_ascii=False,indent=2));os.replace(tmp,art)
    print('PACK',len(scenes),'SCENES',flush=True)
if __name__=='__main__':main()
