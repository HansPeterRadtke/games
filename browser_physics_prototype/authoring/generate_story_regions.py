#!/usr/bin/env python3
"""Local authoring study: literary world -> constrained 3D landmark proposals.

Not a public inference API. The expensive work runs before browser deployment;
validated results load without any connection to a model at runtime.
"""
import argparse, datetime, hashlib, json, math, os, pathlib, re, sys, time
import requests

ROOT=pathlib.Path(__file__).resolve().parents[1]
ARTIFACT=ROOT/'generated/story-region-bank.json'
AUDIT=pathlib.Path('/data/var/llm_game/studies/story-region-llm-audit.jsonl')
MODEL_URL=os.environ.get('PRSE_LLM_URL','http://jetson.lan:14829/completion')
SCENARIOS=(
 {'region':1,'branch':'bridge_repaired','anchor':43.0,'context':'The player repaired a damaged footbridge using two real timber planks. A traveler noticed the help. Ahead there is an old riverside forest hamlet.'},
 {'region':1,'branch':'bridge_unrepaired','anchor':43.0,'context':'The bridge is still broken. The traveler remains unable to cross. A forest path ahead curves towards an abandoned hamlet and its river.'},
 {'region':2,'branch':'mechanism_open','anchor':55.0,'context':'The player experimented with timings and activated an old resonating mechanism that raised a metal fence. A peculiar vibration now sometimes travels through the landscape.'},
 {'region':2,'branch':'mechanism_closed','anchor':55.0,'context':'The old mechanism remains unsolved and its lifting fence stayed shut; the player might have jumped over the fence. The world is still a grounded rural landscape with strange old machinery.'},
)
KIND={'tree','rock','spring','destination','shelter'}
# Restricted to known visual adapters and passive physics. Model prose remains free-form.
SCHEMA={'type':'object','properties':{'title':{'type':'string'},'description':{'type':'string'},'objects':{'type':'array','items':{'type':'object','properties':{'name':{'type':'string'},'kind':{'type':'string','enum':sorted(KIND)},'description':{'type':'string'},'offset_x_m':{'type':'number'},'center_height_m':{'type':'number'},'width_m':{'type':'number'},'height_m':{'type':'number'},'depth_m':{'type':'number'},'mass_kg':{'type':'number'},'interaction_clue':{'type':'string'}},'required':['name','kind','description','offset_x_m','center_height_m','width_m','height_m','depth_m','mass_kg','interaction_clue'],'additionalProperties':False}}},'required':['title','description','objects'],'additionalProperties':False}

def is_finite(value,low,high):
    return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value) and low<=value<=high

def validate(raw,scenario):
    if not isinstance(raw,dict) or not isinstance(raw.get('title'),str) or not 5<=len(raw['title'])<=95 or not isinstance(raw.get('description'),str) or not 50<=len(raw['description'])<=950:return 'Invalid title or scene prose'
    objects=raw.get('objects');
    if not isinstance(objects,list) or not 2<=len(objects)<=4:return 'Object count out of bounds'
    seen=[]
    for i,obj in enumerate(objects):
        if not isinstance(obj,dict) or obj.get('kind') not in KIND:return f'Unknown object kind {i}'
        for f in ('name','description','interaction_clue'):
            if not isinstance(obj.get(f),str) or not 1<=len(obj[f])<=300:return f'Invalid object prose {i}:{f}'
        for f,lo,hi in [('offset_x_m',-4.2,4.2),('center_height_m',.08,5),('width_m',.15,5.5),('height_m',.15,8),('depth_m',.15,5.5),('mass_kg',.05,20000)]:
            if not is_finite(obj.get(f),lo,hi):return f'Invalid coordinate/dimension {i}:{f}={obj.get(f)}'
        # A rigid 3D object may not initially penetrate the ground, even if the model says so.
        if obj['center_height_m']+0.02<obj['height_m']/2:return f'Ground penetration {i}'
        for prev in seen:
            if abs(obj['offset_x_m']-prev['offset_x_m'])<(obj['width_m']+prev['width_m'])/2-0.09:
                if abs(obj['center_height_m']-prev['center_height_m'])<(obj['height_m']+prev['height_m'])/2-0.06:return f'Overlapping physical object footprints {i}'
        seen.append(obj)
    return None

def make_prompt(scenario):
    return ('You are the world author for a persistent game, not its physics engine. Write atmospheric fiction describing a small new part of one coherent forest world in exactly one or two short sentences. The scene must be a causal consequence of player action and the existing world history; do not contradict earlier events. Then describe exactly 2 distinct visible landmark objects which physically occupy real XYZ space near the center of this scene. Describe surprising but plausible discoveries and observational clues, not simple treasure rewards. All distances are measured in METERS, mass in kilograms. Placement requirements: local center offsets x -4 to +4 m, y is the HEIGHT OF AN OBJECT CENTER ABOVE GROUND (height/2 for objects resting on ground), depth is along invisible z axis. Do not overlap solid objects in x and y. Objects should be on solid ground and believable. Use only visual object kinds tree, rock, spring, destination, shelter. No characters or weapons. Include interaction_clue meaningful when explored. No unsafe executable code, scripts, or actions in the returned data. If the scene consequence is only a semantic observation, keep physical props simple. Required JSON only.\nExisting world: A beech grove leads to a resonance gate, a traveler, a spring, an old bridge, a river, and the beginning of a valley. Active gameplay events: '+scenario['context']+'\nNew region at global x '+str(scenario['anchor'])+' m.')

def inference(prompt,timeout=50):
    args={'prompt':prompt,'temperature':.42,'top_p':.86,'n_predict':245,'stream':False,'json_schema':SCHEMA}
    start=time.monotonic();resp=requests.post(MODEL_URL,json=args,timeout=(5,timeout));resp.raise_for_status();raw=resp.json();text=raw.get('content');
    if not isinstance(text,str) or len(text)>45000:raise ValueError('Empty or oversized response')
    return json.loads(text),round(time.monotonic()-start,2),raw.get('tokens_predicted')

def generate(scenario,attempts=1):
    prompt=make_prompt(scenario);promptHash=hashlib.sha256(prompt.encode()).hexdigest();errors=[]
    for attempt in range(1,attempts+1):
        try:
            result,latency,tokens=inference(prompt)
            reason=validate(result,scenario)
            audit={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'region':scenario['region'],'branch':scenario['branch'],'attempt':attempt,'latency_s':latency,'tokens':tokens,'valid':reason is None,'rejection':reason,'model_url':MODEL_URL,'prompt_sha256':promptHash,'output':result}
            with AUDIT.open('a') as fd:fd.write(json.dumps(audit,ensure_ascii=False)+'\n')
            if reason:errors.append(reason);continue
            return {'region':scenario['region'],'branch':scenario['branch'],'anchor':scenario['anchor'],'source':'local-llm:Qwen3.8-27B:'+promptHash[:14],'title':result['title'],'description':result['description'],'objects':result['objects'],'latency_s':latency,'tokens':tokens,'prompt_sha256':promptHash}
        except (requests.RequestException,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:errors.append(f'{type(e).__name__}: {str(e)[:180]}')
    raise ValueError(f'All candidates invalid for region {scenario["region"]} branch {scenario["branch"]}: {errors}')

def main():
    p=argparse.ArgumentParser();p.add_argument('--scenarios',nargs='*',default=['bridge_repaired','bridge_unrepaired','mechanism_open','mechanism_closed']);args=p.parse_args()
    selected=[s for s in SCENARIOS if s['branch'] in args.scenarios];assert selected,'No scenarios selected'
    ARTIFACT.parent.mkdir(exist_ok=True,parents=True);AUDIT.parent.mkdir(exist_ok=True,parents=True)
    previous=json.loads(ARTIFACT.read_text()) if ARTIFACT.is_file() else {'version':1,'model':'Qwen3.8-27B','scenes':[]}
    scenes={(s['region'],s['branch']):s for s in previous.get('scenes',[])}
    failures=[]
    for scenario in selected:
        key=scenario['region'],scenario['branch']
        if key in scenes:print('CACHED',scenario['branch'],flush=True);continue
        try:
            result=generate(scenario);scenes[key]=result;print('ACCEPT',scenario['branch'],'latency',result['latency_s'],'tokens',result['tokens'],'objects',len(result['objects']),flush=True)
        except Exception as exc:failures.append(str(exc));print('REJECT',str(exc),flush=True)
    content={'version':1,'model':'Qwen3.8-27B','scenes':list(scenes.values())};temporary=ARTIFACT.with_suffix('.json.tmp');temporary.write_text(json.dumps(content,ensure_ascii=False,indent=2));os.replace(temporary,ARTIFACT)
    print('PACK',ARTIFACT,'SCENES',len(content['scenes']),'FAILURES',len(failures),flush=True)
    if failures:sys.exit(1)

if __name__=='__main__':main()
