#!/usr/bin/env python3
"""Read-only independent provenance and quantitative audit of the matched
neural-syntax versus deterministic PRSE scene-translation experiment.
No model inference, no physics rerun, and no mutation of raw source evidence.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
import json,zipfile,io,csv

R=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research')
WHEEL=PRIVATE/'models/spacy-english-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl'
BASE=PRIVATE/'runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json'
TEXT=PRIVATE/'runs/2026-10-25-syntax-model'
PHYS=PRIVATE/'runs/2026-10-25-syntax-model-physics'
DATA=PRIVATE/'SceneEval-500_v250610.zip'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert digest(WHEEL)=='1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85'
assert digest(DATA)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
meta=read(R/'prse_syntax_model_proposal_manifest_v1.json')
assert meta['metadata']['spaCyVersion']=='3.8.0'
assert meta['metadata']['gpuUsed']==False
assert meta['metadata']['frozenInputSHA256']==digest(BASE)
assert meta['metadata']['spaCyWheelSHA256']==digest(WHEEL)
b=read(BASE)['proposalsAll500']
assert len(b)==500
with zipfile.ZipFile(DATA) as z:
 with z.open('annotations.csv') as fp:rows=list(csv.DictReader(io.TextIOWrapper(fp,encoding='utf-8-sig')))
assert len(rows)==500
manifest={}
for method in ('dependency','union'):
 path=TEXT/f'prse_spacy_sceneeval_500_{method}_v1.json'
 assert S_IMODE(path.stat().st_mode)==0o600
 assert digest(path)==meta['variants'][method]['sha256']
 p=read(path)
 assert p['metadata']['goldAnnotationsNotLoaded'] and p['metadata']['modelIsNotGenerativeLLM']
 assert p['metadata']['baselineInputSHA256']==digest(BASE)
 assert p['metadata']['modelWheelSHA256']==digest(WHEEL)
 rows500=p['proposalsAll500']
 assert len(rows500)==500
 assert all(x['sourceId']==str(i) and x['text']==rows[i]['Description']
  and x['quantities']==b[i]['quantities'] and x['mentions']==b[i]['mentions']
  for i,x in enumerate(rows500))
 manifest[method]={'proposalSHA256':digest(path),'privateRawBytes':path.stat().st_size}
scores=read(R/'prse_syntax_model_relation_scores_v2.json')
physGold=read(R/'prse_syntax_physics_external_gold_v1.json')
stats=read(R/'prse_syntax_model_paired_uncertainty_v1.json')
assert scores['metadata']['sourceZIPsha256']==digest(DATA)
assert physGold['metadata']['sourceSha256']==digest(DATA)
expected={
 'human':{'gold':478,'matched':[30,33,35],'physics':[97,98,97],
          'room':[39,45,49]},
 'assisted':{'gold':743,'matched':[22,21,23],'physics':[99,99,97],
             'room':[21,22,25]}
}
for sample,expected_values in expected.items():
 ids=list(range(100)) if sample=='human' else list(range(100,500,4))
 for idx,method in enumerate(('deterministic','dependency','union')):
  object_metric=physGold['results'][sample]['object']['unordered'][method]
  room_metric=physGold['results'][sample]['room']['unordered'][method]
  assert object_metric['gold']==expected_values['gold']
  assert object_metric['correct']==expected_values['matched'][idx]
  assert object_metric['physicalScenesAccepted']==expected_values['physics'][idx]
  assert room_metric['correct']==expected_values['room'][idx]
  if method!='deterministic':
   file=PHYS/f'prse_syntax_{method}_{sample}_100_raw_v1.json'
   assert S_IMODE(file.stat().st_mode)==0o600
   assert digest(file)==read(R/f'prse_syntax_{method}_{sample}_100_aggregate_v1.json')['metadata']['rawSHA256']
   raw=read(file)
   assert [int(x['id']) for x in raw['results']]==ids
   assert raw['metadata']['noGoldUsed'] and raw['metadata']['maxCandidateAttemptsPerScene']==150
   assert raw['summary']['stableOriginalIdentitiesAndProse']==raw['summary']['physicallyMaterialized']
   assert all(x['maxReloadPositionError']<.001 for x in raw['results']
       if x['status']=='materialized_and_reloaded')
   assert physGold['results'][sample]['object']['unordered'][method]['privateRawSHA256']==digest(file)
   manifest[f'{method}_{sample}']={'physicsSHA256':digest(file),
     'privateRawBytes':file.stat().st_size}
 orig=stats['comparisons'][sample]
 for method in ('dependency','union'):
  st=orig[method]
  assert st['baselineMatched']==expected_values['matched'][0]
  assert st['modelMatched']==expected_values['matched'][1 if method=='dependency' else 2]
  assert sum(st[k] for k in ('perSceneGains','perSceneLosses','perSceneUnchanged'))==100
  assert st['bootstrapPercentile95'][0]<=st['recallDifference']<=st['bootstrapPercentile95'][1]
for f in (TEXT/'prse_syntax_model_per_case_gold_audit_v1.json',
 TEXT/'prse_syntax_model_per_case_gold_audit_v2.json'):
 assert f.is_file() and S_IMODE(f.stat().st_mode)==0o600
assert stats['metadata']['method'].startswith('paired scene-level nonparametric bootstrap')
print('VERIFIED: official SceneEval source ZIP and compatible model wheel checksums,')
print('500 source texts and lexical quantities unchanged, model proposals frozen prior to gold scoring,')
print('four scene-level physics evaluation batches with exact source IDs, actual GameCore re-entry,')
print('human object grounded matches 30→33/35 of 478 and assisted 22→21/23 of 743,')
print('room changes 39→45/49 and 21→22/25, and scene-bootstrap uncertainty retained.')
