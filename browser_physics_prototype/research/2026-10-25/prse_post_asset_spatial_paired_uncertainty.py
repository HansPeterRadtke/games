#!/usr/bin/env python3
"""Paired SCENE bootstrap, source gold spatial type-pair predicate fidelity,
using only already frozen independently collected native GameCore/Rapier
positions/contact manifolds and SceneEval author-label test results.

No model/physics re-run, no gold-driven tuning or claims of general population
accuracy. For the user's primary PRSE objective, this quantifies how the
potentially accidental NEAR relation matches affect supported scene fidelity,
separate from counts and from truly contacting ON source requirements.
"""
from pathlib import Path
import json,random
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_spatial_relation_gold_200_raw_v1.json')
raw=json.loads(P.read_text())['perScene']
assert len(raw)==200
out={'metadata':{
 'method':'Paired 4000-bootstrap, resample independently authored source SCENES not individual related clauses',
 'scope':'Only supported native Rapier ON + coordinate-based NEXT/NEAR source predicate families; other relation types explicitly abstained',
 'limitation':'Source type-pair existential score is optimistic, layout floor-grid proximity can match by chance; this is an exposed curated dataset, not blind future fiction',
 'noSharedGPUorModelCalls':True},
 'byGroup':{}}
for subset in ('human','assisted'):
 scenes=[r for r in raw if r.get('subset')==subset]
 assert len(scenes)==(98 if subset=='human' else 99)
 a=[]
 for row in scenes:
  goals=[g for g in row['goals'] if g['mapped'] is not None]
  a.append((
   len(goals),
   sum(g['independentPhysics']['baseline']=='actual_native_supported' for g in goals),
   sum(g['independentPhysics']['generic']=='actual_native_supported' for g in goals),
   sum(g['independentPhysics']['catalog']=='actual_native_supported' for g in goals),
   sum(g['relation']=='on' and g['independentPhysics']['baseline']=='actual_native_supported' for g in goals),
   sum(g['relation']=='on' and g['independentPhysics']['generic']=='actual_native_supported' for g in goals)
  ))
 denominator=sum(q[0] for q in a);base=sum(q[1] for q in a)
 gen=sum(q[2] for q in a);cat=sum(q[3] for q in a)
 rng=random.Random(20261025+(17 if subset=='assisted' else 0))
 deltas=[]
 for _ in range(4000):
  take=[a[rng.randrange(len(a))] for i in range(len(a))]
  d=sum(x[0] for x in take)
  deltas.append(sum(x[2]-x[1] for x in take)/d if d else 0)
 deltas.sort()
 out['byGroup'][subset]={
  'physicallyAcceptedScenes':len(scenes),
  'authorRelationClausesWithSupportedPhysicalPredicate':denominator,
  'baselineNativeSatisfied':base,
  'genericNativeSatisfied':gen,
  'catalogNativeSatisfied':cat,
  'baselineOnWithActualContact':sum(q[4] for q in a),
  'genericOnWithActualContact':sum(q[5] for q in a),
  'additionalGenericProximityMatchesNotNewOnSupport':gen-base,
  'pairedConditionalRecallDifference':(gen-base)/denominator if denominator else 0,
  'sceneBootstrap95Difference':[deltas[100],deltas[3899]],
  'zeroSupportContactGain':sum(q[5] for q in a)==sum(q[4] for q in a)}
with (R/'prse_post_asset_spatial_paired_uncertainty_v1.json').open('x') as f:
 json.dump(out,f,indent=2);f.write('\n')
for k,v in out['byGroup'].items():
 print(k,'source gold testable',v['authorRelationClausesWithSupportedPhysicalPredicate'],
 'baseline',v['baselineNativeSatisfied'],'generic',v['genericNativeSatisfied'],
 'catalog',v['catalogNativeSatisfied'],'native on',v['baselineOnWithActualContact'],
 'gain points',round(100*v['pairedConditionalRecallDifference'],2),
 'scene95',list(round(100*x,2) for x in v['sceneBootstrap95Difference']))
