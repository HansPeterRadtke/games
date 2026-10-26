#!/usr/bin/env python3
"""Source-only selection of Nr3D TRUE-native Rapier feasibility probes.
NO human reference IDs, instance_type, 3D mesh or original Nr3D CSV gold
is opened; these are frozen earlier source-only statements and negative
idioms. NOT previously denied random-parent placebo. Parent is explicitly
named by source relation; controls have exactly no source relation.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import json,sys
ROOT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-nr3d-independent-r7')
SRC=ROOT/'nr3d_source_only_predictions_480_frozen_v1.json'
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'2026-10-24'))
import prse_semantic_constraints as old
def sha(p):return sha256(p.read_bytes()).hexdigest()
raw=json.loads(SRC.read_text())
assert raw['metadata']['noHumanGroundTruthFieldsOpened']
case=[];counts=Counter()
for r in raw['records']:
 proposes=r['sourceOnlyOnTopProposal']
 if proposes:
  rel=proposes[0]
  child,parent=rel['child'],rel['parent']
  if child==parent:continue
  category='source_explicit_pretrained_on_proposal'
  sourceOffsets=rel
 elif r['explicitNaturalNontopCases']:
  kinds=[]
  for m in old.mentions(r['text']):
   if old.quantify(r['text'],m)[0]<=0:continue
   k=old.canon(m['type'])
   if k not in kinds and k not in {'room','wall','floor','door','window','ceiling'}:kinds.append(k)
  if len(kinds)<2:continue
  child,parent=kinds[:2]
  category='original_nontop_source_negative_control'
  sourceOffsets=None
 else:continue
 case.append({'scanId':r['scanId'],'datasetIndex':r['datasetIndex'],'sourceHash':r['sourceHash'],
   'originalSourceText':r['text'],
   'category':category,'sourceOnlyChildType':child,
   'sourceOnlyParentType':parent,'sourcePreposition':sourceOffsets,
   'oldBody1':'sem-r7-'+sha256(r['scanId'].encode()).hexdigest()[:18]+'-child',
   'oldBody2':'sem-r7-'+sha256(r['scanId'].encode()).hexdigest()[:18]+'-parent',
   'geometryOrigin':'generic fixed-size 3D boxes, intentionally NOT ScanNet reference shapes',
   'assetGroundTruthPresent':False})
 counts[category]+=1
assert counts['source_explicit_pretrained_on_proposal']==15
assert 10<=counts['original_nontop_source_negative_control']<=40
assert len({x['scanId'] for x in case})==len(case)
dst=ROOT/'nr3d_physical_feasibility_goldblind_input_v1.json'
with dst.open('x') as f:json.dump({
 'metadata':{'sourceOnlyPredictionsSHA256':sha(SRC),'goldNotConsulted':True,
   'matchedBodyInventoryAnd38RapierTicks':True,
   'noRandomFeasibleParentPlacebo':True,
   'notIndependentSourceGeometryTruth':True},
 'summary':dict(counts),'cases':case},f,indent=2);f.write('\n')
dst.chmod(0o600)
print('FROZEN_NR3D_PHYSICAL_SOURCE_ONLY',dict(counts),'sha',sha(dst))
