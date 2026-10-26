#!/usr/bin/env python3
"""POSTHOC targeted known compound truncation fix for frozen Nr3D outputs.
Rule is intentionally explicit and developed AFTER earlier independent gold
inspection: NEVER represent as heldout or preregistered. No physics, GPU, or
service effects. Only modify source-derived first noun phrase if it contains
one of three already diagnosed compound objects. Original frozen predictions
and Nr3D human labels remain unchanged. New scoring shows BOTH wins/losses.
"""
import json,re,hashlib,collections,statistics,time
from pathlib import Path
ROOT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-nr3d-independent-r7')
HERE=Path(__file__).resolve().parent
frozen=ROOT/'nr3d_source_only_predictions_480_frozen_v1.json'
human=ROOT/'nr3d_postfrozen_independent_human_3d_gold_percase_v1.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
A=json.loads(frozen.read_text())['records'];G=json.loads(human.read_text())['rows']
assert len(A)==len(G)==480
lookup={x['sourceId']:x for x in G}
# Scope is deliberately narrow and SOURCE-ONLY. Match the head whose frozen
# first nominal prediction truncated the multi-word noun. Avoid incidental
# unrelated later mentions: a match must begin near selected prediction.
RULES={
 'trash_can':(r'\b(?:trash\s*can|trashcan|garbage\s*can|garbage\s*bin|waste\s*bin)\b',
              {'trash','can','trashcan','garbage','bin'}),
 'toilet_paper':(r'\btoilet\s+paper\b',{'toilet','paper'}),
 'computer_tower':(r'\bcomputer\s+tower\b',{'computer','tower'})
}
out=[];stats=collections.Counter()
for row in A:
 gold=lookup[row['datasetIndex']]
 assert row['scanId']==gold['scanId'] and row['sourceHash']==gold['sourceSHA256']
 pred=row['sourceOnlyPretrainedTargetType']
 prior=pred['kind'] if pred else None
 now=prior;rule=None
 for kind,(pattern,heads) in RULES.items():
  if prior not in heads:continue
  m=re.search(pattern,row['text'],re.I)
  if not m:continue
  # Preserve original grammatical target-selection position. No remote
  # phrases or unrelated later subclauses may override its source head.
  if abs(m.start()-pred['start'])>24 and abs(m.end()-pred['end'])>24:continue
  now=kind;rule=kind;break
 before=prior==gold['officialTargetClass']
 after=now==gold['officialTargetClass']
 stats['all']+=1
 stats['priorCorrect']+=before
 stats['newCorrect']+=after
 stats['changes']+=rule is not None
 stats['wins']+=after and not before
 stats['losses']+=before and not after
 if rule:stats['rule_'+rule]+=1
 out.append({'sceneId':row['scanId'],'sourceHash':row['sourceHash'],
  'sourceIndex':row['datasetIndex'],'old':prior,'new':now,
  'sourceOnlyCompoundRule':rule,
  'preexistingFrozenCorrect':before,'posthocCorrect':after})
assert stats['all']==480 and stats['priorCorrect']==309
raw=ROOT/'nr3d_posthoc_compound_semantic_repair_percase_v1.json'
with raw.open('x') as f:json.dump({'metadata':{
 'frozenSourceSHA256':sha(frozen),'independentHumanLabelsSHA256':sha(human),
 'posthocRulesSeenEarlierGoldAndNotNewHeldout':True,
 'notMetric3DAssetOrObjectIdentityEvaluation':True},
 'counts':dict(stats),'rows':out},f,indent=2);f.write('\n')
raw.chmod(0o600)
result={'metadata':{'privateEvidenceSHA256':sha(raw),'originalPredictionSHA256':sha(frozen),
 'originalHumanAnnotationSHA256':sha(human),
 'posthocDiagnosticOnly':True,'preregisteredOutcomeStillFailed':True,
 'newModelNotTestedOnUnseenData':True,'noPhysicallyVerifiedSourceObjectIDs':True},
 'summary':dict(stats),'oldAllInputAccuracy':round(stats['priorCorrect']/480,6),
 'posthocAllInputAccuracy':round(stats['newCorrect']/480,6),
 'posthocDifferencePercentagePoints':round(100*(stats['newCorrect']-stats['priorCorrect'])/480,3)}
safe=HERE/'prse_round8_compound_source_posthoc_diagnostic_aggregate_v1.json'
with safe.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('ROUND8_POSTHOC_COMPOUND_FIX',json.dumps(result,sort_keys=True))
