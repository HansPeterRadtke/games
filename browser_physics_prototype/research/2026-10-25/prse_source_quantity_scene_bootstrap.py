#!/usr/bin/env python3
"""Exploratory scene-level bootstrap uncertainty for the independent SceneEval
quantity/attribute comparison, not inference about all future literary worlds.

Scene claims from a single text are dependent; resample SCENES instead of
pretending 1,237 annotated quantities are 1,237 independent experiments.
The previous official gold audit is already frozen; this script does not alter
the model/parser, physical world, annotations or prior output.
"""
from pathlib import Path
import json,random
R=Path(__file__).parent
RAW=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance/prse_source_quantity_official_gold_per_case_v1.json')
data=json.loads(RAW.read_text())['cases']
out={'metadata':{
 'method':'Scene-level nonparametric bootstrap, 4000 independent resamples per source category with fixed seed',
 'source':'Frozen official SceneEval source/physics count audit, manually authored human and partly assisted disjoint source groups',
 'sampleLimit':'Curated previous-benchmark-exposed prompts, not pristine withheld or random general PRSE fiction; CI conditional on this dataset',
 'metric':'Fraction of independently annotated exact/inequality object-type count claims satisfied by PRSE actual native 3D population',
 'unit':'source descriptions, not individual dependent annotated claims'},'splits':{}}
for idx,group in enumerate(('human100','assisted100')):
 scenes=[r for r in data if r['subset']==group and r['status']=='native_3d_verified']
 assert len(scenes)==(98 if group=='human100' else 99)
 original=[]
 for row in scenes:
  total=len(row['countClaims'])
  correct=sum(c['physicalSatisfied'] for c in row['countClaims'])
  origattr=len(row['attributes'])
  attr=sum(c['parsedSourceAttributeMatches'] for c in row['attributes'])
  original.append((correct,total,attr,origattr))
 a=sum(x[0] for x in original);b=sum(x[1] for x in original)
 ca=sum(x[2] for x in original);cb=sum(x[3] for x in original)
 samples=[];attributeSamples=[]
 rng=random.Random(20261025+idx*79)
 for _ in range(4000):
  seq=[original[rng.randrange(len(original))] for _ in range(len(original))]
  den=sum(x[1] for x in seq)
  aden=sum(x[3] for x in seq)
  samples.append(sum(x[0] for x in seq)/den if den else 0.)
  attributeSamples.append(sum(x[2] for x in seq)/aden if aden else 0.)
 samples.sort();attributeSamples.sort()
 out['splits'][group]={
  'acceptedPhysicalScenes':len(scenes),
  'authorAnnotatedQuantityClauses':b,
  'physicallySatisfiedGoldQuantityClauses':a,
  'observedClauseFraction':a/b,
  'conditionalBootstrap95':[samples[100],samples[3899]],
  'authorAnnotatedAttributes':cb,
  'lexicallyMatchingAttributes':ca,
  'attributeTextOnlyFraction':ca/cb if cb else 0,
  'attributeBootstrap95':[attributeSamples[100],attributeSamples[3899]],
  'sourceVsPhysicsQualifier':'Actual materialized count, but no independent source-reference entailment or appearance verification'}
with (R/'prse_source_quantity_scene_bootstrap_v1.json').open('x') as f:
 json.dump(out,f,indent=2);f.write('\n')
for name,s in out['splits'].items():
 print(name,'count source alignment',round(s['observedClauseFraction'],4),
  '95% scene-bootstrap',list(round(t,4) for t in s['conditionalBootstrap95']),
  'text-only attribute matches',round(s['attributeTextOnlyFraction'],4))
