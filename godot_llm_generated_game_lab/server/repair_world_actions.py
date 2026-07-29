from __future__ import annotations
import argparse,copy,json,time,urllib.request
from pathlib import Path
from typing import Any,Callable
from jsonschema import Draft202012Validator
import world_generation as world
MODEL_URL='http://10.8.0.7:14831/completion'; MODEL_ID='qwen2.5-14b-world-author'; TIMEOUT=300

def post(prompt:str,schema:dict[str,Any],seed:int,max_tokens:int,semantic:Callable[[dict[str,Any]],list[str]])->tuple[dict[str,Any],dict[str,Any]]:
 feedback=''; attempts=[]
 for attempt in range(2):
  text=prompt if not feedback else prompt+'\n\nRewrite the complete JSON and fix every validation problem: '+feedback
  payload={'prompt':text,'n_predict':max_tokens,'temperature':0.42 if attempt==0 else 0.2,'top_p':0.88,'seed':seed+attempt,'json_schema':schema}
  req=urllib.request.Request(MODEL_URL,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
  started=time.monotonic()
  try:
   with urllib.request.urlopen(req,timeout=TIMEOUT) as r: body=json.load(r)
   value=json.loads(body['content']); errors=[e.message for e in Draft202012Validator(schema).iter_errors(value)]; errors.extend(semantic(value))
   if errors: raise ValueError('; '.join(errors[:30]))
   attempts.append({'attempt':attempt+1,'ok':True,'seconds':round(time.monotonic()-started,3)})
   return value,{'model':body.get('model',MODEL_ID),'tokens_predicted':body.get('tokens_predicted'),'attempts':attempts,'fallback_used':False}
  except Exception as exc:
   feedback=f'{type(exc).__name__}: {exc}'[:2800]; attempts.append({'attempt':attempt+1,'ok':False,'seconds':round(time.monotonic()-started,3),'error':feedback})
 raise RuntimeError(json.dumps(attempts,ensure_ascii=False))

def effect_type(branch:dict[str,Any])->set[str]:
 prop=branch['properties']['type'];
 if 'const' in prop:return {prop['const']}
 return set(prop.get('enum',[]))

def bound_effects(allowed:set[str],object_ids:list[str],exit_ids:list[str],stat_ids:list[str])->dict[str,Any]:
 schema=copy.deepcopy(world.EFFECT_SCHEMA); branches=[]
 for branch in schema['oneOf']:
  if not effect_type(branch)&allowed: continue
  props=branch['properties']
  if 'target_id' in props: props['target_id']={'type':'string','enum':object_ids}
  if 'exit_id' in props: props['exit_id']={'type':'string','enum':exit_ids}
  if 'stat' in props: props['stat']={'type':'string','enum':stat_ids}
  branches.append(branch)
 schema['oneOf']=branches; return schema

def bound_conditions(object_ids:list[str],stat_ids:list[str])->dict[str,Any]:
 schema=copy.deepcopy(world.CONDITION_SCHEMA)
 for branch in schema['oneOf']:
  props=branch['properties']
  if 'target_id' in props: props['target_id']={'type':'string','enum':object_ids}
  if 'stat' in props: props['stat']={'type':'string','enum':stat_ids}
 return schema

def action_schema(trigger:str,allowed:set[str],object_ids:list[str],exit_ids:list[str],stat_ids:list[str])->dict[str,Any]:
 schema=copy.deepcopy(world.ACTION_SCHEMA); schema['properties']['input']={'const':trigger}; schema['properties']['conditions']['items']=bound_conditions(object_ids,stat_ids); schema['properties']['effects']['items']=bound_effects(allowed,object_ids,exit_ids,stat_ids); return schema

def action_semantic(action:dict[str,Any],trigger:str)->list[str]:
 errors=[]; effects=[e for e in action.get('effects',[]) if isinstance(e,dict)]; types=[str(e.get('type','')) for e in effects]
 if not any(t!='show_message' for t in types): errors.append('action must change executable state')
 if len([json.dumps(e,sort_keys=True) for e in effects])!=len(set(json.dumps(e,sort_keys=True) for e in effects)): errors.append('duplicate effects are forbidden')
 if trigger=='touch' and any(t in {'remove_object','set_visibility','scene_transition','end_game'} for t in types): errors.append('touch action is too destructive')
 if trigger=='touch' and float(action.get('range_meters',0))>1.0: errors.append('touch range must be at most one meter')
 if trigger in {'interact','hit'} and not 0.5<=float(action.get('range_meters',0))<=3.5: errors.append('action range must be practical')
 if len(str(action.get('actor_animation_prompt','')).split())<8 or len(str(action.get('target_animation_prompt','')).split())<8: errors.append('animation prompts are underspecified')
 return errors

def stats_schema()->dict[str,Any]:
 return {
  'type':'array','minItems':4,'maxItems':4,
  'items':{
   'type':'object','additionalProperties':False,
   'required':['id','label','initial','minimum','maximum'],
   'properties':{
    'id':{'type':'string','enum':['health','stamina','autonomy','mom_patience']},
    'label':{'type':'string','minLength':2,'maxLength':40},
    'initial':{'type':'number','minimum':0,'maximum':100},
    'minimum':{'const':0},
    'maximum':{'const':100},
   },
  },
 }


def repair(path:Path)->None:
 bundle=json.loads(path.read_text()); plan=bundle['scene_plan']; object_ids=[plan['player']['id']]+[o['id'] for o in plan['objects']]; exit_ids=[e['id'] for e in plan.get('exits',[])]; stat_ids=['health','stamina','autonomy','mom_patience']
 gameplay_schema={'type':'object','additionalProperties':False,'required':['objective','win_conditions','lose_conditions','available_inputs','stats','starting_inventory'],'properties':{'objective':{'type':'string','minLength':30,'maxLength':300},'win_conditions':{'type':'array','minItems':1,'maxItems':4,'items':{'type':'string','minLength':10,'maxLength':180}},'lose_conditions':{'type':'array','minItems':1,'maxItems':4,'items':{'type':'string','minLength':10,'maxLength':180}},'available_inputs':{'type':'array','minItems':5,'maxItems':7,'uniqueItems':True,'items':{'type':'string','enum':['move','touch','interact','attack','use','dash','jump']}},'stats':stats_schema(),'starting_inventory':{'type':'array','minItems':0,'maxItems':4,'uniqueItems':True,'items':{'type':'string','pattern':'^[a-z][a-z0-9_-]{1,56}$'}}}}
 def gameplay_sem(v):
  errors=[]
  if not {'move','touch','interact','attack','use'}.issubset(set(v.get('available_inputs',[]))): errors.append('missing core inputs')
  stats=v.get('stats',[]); ids=[str(x.get('id','')) for x in stats if isinstance(x,dict)]
  if set(ids)!=set(stat_ids) or len(ids)!=4: errors.append('stats must contain health, stamina, autonomy, and mom_patience exactly once')
  for stat in stats:
   if isinstance(stat,dict) and not float(stat.get('minimum',0))<=float(stat.get('initial',0))<=float(stat.get('maximum',100)): errors.append(f"stat {stat.get('id')} initial is outside bounds")
  return errors
 prompt='Design the executable game rules for Your Mom. The objective must be fun and playable in this dining room. Health, stamina, autonomy, and mom patience have fixed definitions supplied by the schema. Win and lose conditions must be achievable through object actions. Starting inventory contains only real portable items, or is empty. Return JSON only.\n'+json.dumps({'game_description':bundle.get('game_description'),'opening_scene':bundle.get('opening_scene'),'objects':object_ids,'exits':exit_ids},ensure_ascii=False)
 gameplay,meta=post(prompt,gameplay_schema,281000,700,gameplay_sem); plan['gameplay']=gameplay; bundle.setdefault('generation',{})['repaired_gameplay']=meta; path.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'event':'gameplay_repaired','objective':gameplay['objective']}),flush=True)
 player_schema={'type':'object','additionalProperties':False,'required':['interact','hit','use'],'properties':{}}
 player_allowed={'show_message','change_stat','set_state','inventory_add','inventory_remove','move','scene_transition','end_game'}
 for trigger in ['interact','hit','use']: player_schema['properties'][trigger]=action_schema(trigger,player_allowed,object_ids,exit_ids,stat_ids)
 def player_sem(v):
  errors=[]
  for t in ['interact','hit','use']: errors.extend(action_semantic(v[t],t))
  if len({v[t]['id'] for t in v})!=3: errors.append('player action ids must be unique')
  return errors
 prompt='Generate exactly three default player actions for the generated game: interact, hit, and use. They provide useful behavior when no object-specific action is chosen. Use only valid IDs and stats. Use player_interact, player_attack, and player_use as actor clips. The target clip may equal the actor clip for default self-actions. Effects must be coherent and must never contain code strings or arithmetic expressions. Return JSON only.\n'+json.dumps({'gameplay':gameplay,'player':plan['player'],'objects':object_ids,'exits':exit_ids},ensure_ascii=False)
 player_actions,meta=post(prompt,player_schema,281010,1100,player_sem); plan['player']['actions']=[player_actions[t] for t in ['interact','hit','use']]; bundle['generation']['repaired_player_actions']=meta; path.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'event':'player_actions_repaired','actions':[a['id'] for a in plan['player']['actions']]}),flush=True)
 schemas={
  'touch':action_schema('touch',{'show_message','change_stat','set_state','inventory_add','inventory_remove','move','set_collision'},object_ids,exit_ids,stat_ids),
  'interact':action_schema('interact',{'show_message','change_stat','set_state','inventory_add','inventory_remove','move','set_visibility','set_collision','scene_transition','end_game'},object_ids,exit_ids,stat_ids),
  'hit':action_schema('hit',{'show_message','change_stat','set_state','move','set_visibility','set_collision','remove_object','end_game'},object_ids,exit_ids,stat_ids),
 }
 object_schema={'type':'object','additionalProperties':False,'required':['touch','interact','hit'],'properties':schemas}
 for index,obj in enumerate(plan['objects']):
  def semantic(v):
   errors=[]
   for t in ['touch','interact','hit']: errors.extend(action_semantic(v[t],t))
   if len({v[t]['id'] for t in v})!=3: errors.append('action ids must be unique')
   return errors
  prompt=f'''Design three distinct executable actions for {obj['name']}: touch, interact, and hit. Touch is mild and immediate and cannot delete or hide anything. Interact is useful, funny, or narratively meaningful. Hit causes a visible physical reaction and a reasonable consequence, but ordinary durable objects should not vanish on the first strike. Every action must change actual state or stats, use only the supplied IDs and stats, and contain no code strings or duplicate effects. Actor clips are player_touch, player_interact, and player_attack. Target clips are {obj['id']}_touch, {obj['id']}_interact, and {obj['id']}_hit. Animation prompts must describe clear physical motion for a real image-to-video model while preserving identity. Return JSON only.\n'''+json.dumps({'gameplay':gameplay,'object':obj,'valid_objects':object_ids,'valid_exits':exit_ids,'valid_stats':stat_ids},ensure_ascii=False)
  value,meta=post(prompt,object_schema,281100+index*10,1500,semantic); obj['actions']=[value[t] for t in ['touch','interact','hit']]; bundle['generation'].setdefault('repaired_object_actions',{})[obj['id']]=meta; path.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'event':'object_repaired','index':index+1,'total':len(plan['objects']),'id':obj['id'],'actions':[a['id'] for a in obj['actions']]}),flush=True)
 errors=world.validate_scene_plan(plan,bundle['user_prompt']); schema_errors=[e.message for e in Draft202012Validator(world.scene_plan_schema(bundle['user_prompt'])).iter_errors(plan)]
 if schema_errors or errors: raise RuntimeError(json.dumps({'schema':schema_errors,'semantic':errors},ensure_ascii=False))
 bundle['generation']['repaired_action_graph_complete']={'model':MODEL_ID,'actions':len(plan['player']['actions'])+sum(len(o['actions']) for o in plan['objects']),'fallback_used':False}; path.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'event':'complete','actions':30,'fallback':False}),flush=True)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('bundle',type=Path); args=ap.parse_args(); repair(args.bundle)
if __name__=='__main__': main()
