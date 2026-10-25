#!/usr/bin/env python3
"""INDEPENDENT official SceneEval author OORel annotation check of PREVIOUSLY
FROZEN source-only spaCy role gate and independent native Rapier physical
contact audit. No author labels entered the syntax model, source extractor,
scene compiler or real native physical simulation.

Category-pair annotation concordance is at most a proxy for intended
semantic support: gold may omit relations, and exact object-instance identity
and visible geometry remain unresolved.
"""
import json,csv,io,zipfile
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
from stat import S_IMODE

R=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
SOURCE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert sha(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
rolePath=PRIVATE/'prse_source_role_on_200_raw_v1.json'
physPath=PRIVATE/'prse_source_blind_support_eligibility_v1.json'
assert rolePath.exists() and physPath.exists()
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (rolePath,physPath))
roles=read(rolePath)['records']
physics=read(physPath)['records']
by={(r['id'],r['relA'],r['relB']):r for r in physics if 'relA' in r}
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:labels=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(labels)==500
def normalize(x):
 s=x.strip().lower().replace(' ','_')
 return {'television':'tv','bunk_bed':'bed','bedside_lamp':'lamp','refrigerator':'fridge'}.get(s,s)
goldBySource={}
for id in set(r['sourceId'] for r in roles):
 pairs=set()
 for txt in labels[id]['OORel'].split(';'):
  p=[x.strip() for x in txt.split(',')]
  if len(p)<6 or p[2]!='on':continue
  # Author annotation encodes substrate first, supported object second.
  pairs.add((normalize(p[5]),normalize(p[4])))
 goldBySource[id]=pairs
metrics=Counter()
per=[]
for r in roles:
 id=r['sourceId']
 isGold=(normalize(r['parsedChild']),normalize(r['parsedSupport'])) in goldBySource[id]
 isRole=r['status']=='source_syntax_role_candidate'
 rr=by.get((id,r['parsedChild'],r['parsedSupport']))
 isNative=bool(rr and rr['status']=='true')
 if not rr:metrics['proposedInUnacceptedOrMissingNativeScene']+=1
 metrics['originalParsedOnClaims']+=1
 metrics['originalParsedOnAnnotationConcordant']+=int(isGold)
 metrics['originalParsedOnPhysicallyTrue']+=int(isNative)
 metrics['originalParsedOnPhysicallyTrueAndGoldConcordant']+=int(isNative and isGold)
 metrics['syntaxRoleAccept']+=int(isRole)
 metrics['syntaxRoleAnnotationConcordant']+=int(isRole and isGold)
 metrics['syntaxRolePhysicallyTrue']+=int(isRole and isNative)
 metrics['syntaxRolePhysicalAndGoldConcordant']+=int(isRole and isNative and isGold)
 metrics['syntaxAbstainedButAnnotationConcordant']+=int(not isRole and isGold)
 metrics['sourceRolePhysicallyTrueButNotInAuthorAnnotations']+=int(isRole and isNative and not isGold)
 per.append({'sourceId':id,'child':r['parsedChild'],'support':r['parsedSupport'],
  'passSourceSyntax':isRole,'physicalStatus':rr.get('status') if rr else 'not_measured',
  'annotationOnCategoryConcordant':isGold,'reason':r['reason']})
output=PRIVATE/'prse_source_role_independent_on_gold_v1.json'
with output.open('x') as f:json.dump({'metadata':{
 'source':'Author SceneEval-500 OORel labels opened AFTER source-only grammar and Rapier physical evidence frozen',
 'warning':'Unannotated proposed relation not necessarily false; category-pair annotation agreement does not certify exact reference or physical support'},
 'metrics':dict(metrics),'rows':per},f,indent=2);f.write('\n')
output.chmod(0o600)
with (R/'prse_source_role_gold_200_aggregate_v1.json').open('x') as f:
 json.dump({'metadata':{'sceneEvalZIPsha256':sha(GOLD),
  'frozenParserSHA256':sha(SOURCE),
  'sourceOnlyRoleSHA256':sha(rolePath),'frozenNativeSupportSHA256':sha(physPath),
  'privatePostGoldSHA256':sha(output),
  'notAFullCoreferenceEntailmentJudge':True},
  'summary':dict(metrics)},f,indent=2);f.write('\n')
print('INDEPENDENT_SOURCE_ROLE_GOLD',json.dumps(metrics))
