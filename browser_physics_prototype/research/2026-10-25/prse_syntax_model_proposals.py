#!/usr/bin/env python3
"""Fixed text-only comparison input: deterministic lexical parser versus a genuine
pretrained CPU dependency parser plus conservative typed-relation mapping.

The frozen deterministic inputs and source text are reused; official SceneEval
annotation labels are NOT opened or used anywhere in this program. The model is
spaCy's public en_core_web_sm 3.8.0 syntax model; do not mislabel it a generative LLM.
Complete source-derived outputs stay in owner-private Nitro research storage.
"""
from pathlib import Path
from hashlib import sha256
import json,time,os
from prse_spacy_relation_interpreter import load_model,dependency_relations,combine
ROOT=Path(__file__).parent
ORIGINAL=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
OUT=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model')
WHEEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl')
OUT.mkdir(parents=True,exist_ok=True,mode=0o700);OUT.chmod(0o700)
assert ORIGINAL.is_file() and WHEEL.is_file()
def hash(p):return sha256(p.read_bytes()).hexdigest()
frozen=json.loads(ORIGINAL.read_text())
bases=frozen['proposalsAll500']
assert len(bases)==500
assert [int(p['sourceId']) for p in bases]==list(range(500))
nlp=load_model()
assert nlp.meta['name']=='core_web_sm' and nlp.meta['version']=='3.8.0'
start=time.monotonic()
deps=[]
for doc,b in zip(nlp.pipe((x['text'] for x in bases),batch_size=32,n_process=1),bases):
 deps.append(dependency_relations(doc,b))
elapsed=time.monotonic()-start
assert len(deps)==500
obj={}
for method in ('dependency','union'):
 out=OUT/f'prse_spacy_sceneeval_500_{method}_v1.json'
 proposals=[combine(b,d,method=method) for b,d in zip(bases,deps)]
 assert all(a['quantities']==b['quantities'] and a['mentions']==b['mentions']
   and a['text']==b['text'] for a,b in zip(proposals,bases))
 source={'metadata':{'method':method,'baselineInputSHA256':hash(ORIGINAL),
  'modelWheelSHA256':hash(WHEEL),'model':'en_core_web_sm 3.8.0 pretrained CPU',
  'modelSource':'https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0',
  'goldAnnotationsNotLoaded':True,'modelIsNotGenerativeLLM':True,
  'rawIsThirdPartySourceDerived':True,
  'limitations':'Not a trained SceneEval relation classifier, fails coreference/implicit supports; manual mapping rules written on some development examples'},
  'proposalsAll500':proposals}
 with out.open('x') as fp:json.dump(source,fp,indent=2);fp.write('\n')
 out.chmod(0o600)
 counts={group:{
  'descriptions':len(part),
  'objectsReported':sum(sum(max(0,n['count']) for n in x['quantities'].values()) for x in part),
  'predictedObjectRelations':sum(sum(r['kind']=='object' for r in x['relations']) for x in part),
  'predictedRoomRelations':sum(sum(r['kind']=='room' for r in x['relations']) for x in part)}
  for group,part in [('human_100',proposals[:100]),('assisted_400',proposals[100:]),('all_500',proposals)]}
 obj[method]={'sha256':hash(out),'privatePath':str(out),
  'bytes':out.stat().st_size,'counts':counts}
safe={'metadata':{'frozenInputSHA256':hash(ORIGINAL),
 'spaCyWheelSHA256':hash(WHEEL),'spaCyVersion':nlp.meta['version'],
 'method':'same source object mentions/counts; dependency-only vs union with frozen lexical parser',
 'sourceScenes':500,'noGoldLabelsRead':True,'gpuUsed':False,
 'modelSource':'https://spacy.io/models/en',
 'modelLicense':'MIT', 'parseWallTimeSeconds':round(elapsed,3)},
 'variants':obj}
path=ROOT/'prse_syntax_model_proposal_manifest_v1.json'
with path.open('x') as fp:json.dump(safe,fp,indent=2);fp.write('\n')
print('PRETRAINED_CPU_MODEL_PROPOSALS',json.dumps({'time_s':round(elapsed,3),
 'counts':{k:v['counts'] for k,v in obj.items()}},sort_keys=True))
