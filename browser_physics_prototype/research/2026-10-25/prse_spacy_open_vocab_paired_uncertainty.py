#!/usr/bin/env python3
"""Uncertainty of improvement for the already frozen PRSE GameCore/Rapier
open-vocabulary noun-candidate source count comparison.

Bootstrap SCENES as paired clusters, not individual annotated counts. This
preserves within-scene correlation and correctly counts zero-delta scenes.
Original SceneEval has been examined in previous experiments; intervals are
conditional exploratory benchmark variability, NOT new unseen generality.
"""
import json,random
from pathlib import Path
from statistics import median
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery/prse_spacy_open_vocab_native_independent_gold_cases_v1.json')
rows=json.loads(P.read_text())['cases']
assert len(rows)==200
out={'metadata':{
 'method':'Paired nonparametric 4000 bootstrap resamples of original SceneEval descriptions (not object claims), fixed RNG seed',
 'important':'Previously evaluated curated scene corpus and no human source-meaning/3D scale ratings; confidence intervals are CONDITIONAL not true universal PRSE accuracy',
 'exposure':'Old type-count benchmark and some author annotations were reviewed in previous work; no claim of independent pristine holdout',
 'goldNeverEnteredParserOrPhysics':True},
 'byGroup':{}}
for group,lo,hi in [('human',0,100),('assisted',100,500)]:
 sample=[v for v in rows if v['id'] in (range(lo,hi) if group=='human' else range(100,500,4))
  and v.get('officialSourceCount') is not None]
 expected=98 if group=='human' else 99
 assert len(sample)==expected
 # Paired sample includes only both physically materialized branches.
 records=[(x['goldMatchedBefore'],x['goldMatchedAfter'],len(x['officialSourceCount']),
   len(x['addedCandidate3DPlaceholders']),len(x['unannotatedExtraKindProposals'])) for x in sample]
 before=sum(x[0] for x in records);after=sum(x[1] for x in records);claims=sum(x[2] for x in records)
 assert claims>0
 rnd=random.Random(20261025+(0 if group=='human' else 111))
 differences=[];extras=[]
 for _ in range(4000):
  sampled=[records[rnd.randrange(len(records))] for i in range(len(records))]
  denom=sum(x[2] for x in sampled)
  differences.append(sum(x[1]-x[0] for x in sampled)/denom if denom else 0)
  extras.append(sum(x[4] for x in sampled)/len(sample))
 differences.sort();extras.sort()
 out['byGroup'][group]={
  'physicallyAcceptedScenes':len(sample),'annotatedCountClauses':claims,
  'baselinePhysicallySatisfied':before,'augmentedPhysicallySatisfied':after,
  'incrementalGoldClausesSatisfied':after-before,
  'baselineConditionalRecall':before/claims,
  'augmentedConditionalRecall':after/claims,
  'recallDifference':(after-before)/claims,
  'sceneBootstrap95Difference':[differences[100],differences[3899]],
  'additionalGenericNativeBodies':sum(x[3] for x in records),
  'extraPhysicalTypesNotInAuthorAnnotations':sum(x[4] for x in records),
  'conditionalUnknownTypeCountPerSceneBootstrap95':[extras[100],extras[3899]],
  'sourceDiscourseAndPhysicalDimensionalityStillNotValidated':True}
f=R/'prse_spacy_open_vocab_paired_uncertainty_v1.json'
with f.open('x') as fp:json.dump(out,fp,indent=2);fp.write('\n')
for k,v in out['byGroup'].items():
 print(k,'baseline',round(v['baselineConditionalRecall'],4),'augmented',
 round(v['augmentedConditionalRecall'],4),'gain percentage points',
 round(100*v['recallDifference'],1),'scene95',
 [round(100*x,1) for x in v['sceneBootstrap95Difference']])
