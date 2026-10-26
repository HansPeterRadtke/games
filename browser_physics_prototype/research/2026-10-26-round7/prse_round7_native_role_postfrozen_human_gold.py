#!/usr/bin/env python3
"""Independent postfrozen source-role audit of 31 real paired PRSE Rapier worlds.
Reads Nr3D human phrase-to-3D object annotations only AFTER source-only
proposals and true native contact outcomes are frozen and hashed. A human
description's annotated target ID/class is distinct from a true vertical
support label, which Nr3D does not provide exhaustively.
"""
import json,re,hashlib,csv,ast,statistics,math
from pathlib import Path
from collections import Counter
from stat import S_IMODE
ROOT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-nr3d-independent-r7')
HERE=Path(__file__).resolve().parent
ORIGINAL=ROOT/'ScanEnts3D_Nr3D_official_raw.csv'
SOURCE=ROOT/'nr3d_physical_feasibility_goldblind_input_v1.json'
PHYSICS=ROOT/'nr3d_matched_true_native_rapier_31cases_raw_v1.json'
SCORE=ROOT/'nr3d_postfrozen_independent_human_3d_gold_percase_v1.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def cn(s):return re.sub('[^a-z0-9]+','_',s.lower()).strip('_')
assert all(S_IMODE(x.stat().st_mode)==0o600 for x in (ORIGINAL,SOURCE,PHYSICS,SCORE))
p=read(PHYSICS);s=read(SOURCE);ref=read(SCORE)
assert p['metadata']['sourceOnlyPhysicalSpecSHA256']==sha(SOURCE)
assert p['metadata']['originalHumanGoldNotReadByNativeExperiment']
assert len(p['records'])==len(s['cases'])==31
refmap={i['sourceId']:i for i in ref['rows']}
assert len(refmap)==480
annotations={}
with ORIGINAL.open(newline='',encoding='utf-8') as file:
 for record in csv.DictReader(file):
  i=int(record['index'])
  if i not in {c['datasetIndex'] for c in s['cases']}:continue
  annotations[i]=record
assert len(annotations)==31
C=Counter();cases=[]
for raw,experiment in zip(s['cases'],p['records']):
 assert raw['scanId']==experiment['scanId'] and raw['datasetIndex']==experiment['datasetIndex']
 i=raw['datasetIndex'];a=annotations[i];r=refmap[i]
 assert raw['originalSourceText']==a['utterance'] and raw['sourceHash']==r['sourceSHA256']
 assert experiment['status']=='paired_real_rapier_38ticks_each'
 assert experiment['nativeControl']['savedContactsExact'] and experiment['nativeCandidate']['savedContactsExact']
 assert experiment['nativeControl']['realNativeBodyCount']==experiment['nativeCandidate']['realNativeBodyCount']==2
 target=cn(a['instance_type']);child=cn(raw['sourceOnlyChildType']);parent=cn(raw['sourceOnlyParentType'])
 try:
  gold_entities=ast.literal_eval(a['entities'])
 except Exception:gold_entities=[]
 anchors=[]
 for item in gold_entities:
  if not isinstance(item,(tuple,list)) or len(item)!=2:continue
  for v in item[1] if isinstance(item[1],list) else []:
   if not isinstance(v,str) or '_' not in v:continue
   ID,kind=v.split('_',1)
   if ID!=a['target_id']:
    anchors.append({'instanceID':ID,'annotatedKind':cn(kind)})
 valid_source_target=(child==target)
 valid_source_anchor=any(x['annotatedKind']==parent for x in anchors)
 includes_native_top=experiment['nativeCandidate']['contactPairs'] and raw['category']=='source_explicit_pretrained_on_proposal'
 row={'datasetIndex':i,'scanId':a['scan_id'],'humanTargetKind':target,
  'humanTargetID':a['target_id'],'sourceOnlyProposedChild':child,'sourceOnlyProposedParent':parent,
  'independentTargetKindMatchesProposedChild':valid_source_target,
  'independentDifferentInstanceAnchorOfParentKind':valid_source_anchor,
  'originalCorrectGuess':a['correct_guess']=='True',
  'frozenSourceOnlyCategory':raw['category'],
  'actualNativeContactCreated':bool(includes_native_top),
  'numberOfGoldDifferentInstances':len(anchors),
  'originalNamedSourcePhraseSHA256':raw['sourceHash'],
  'trueMeasuredScanNetColliderContact':'UNKNOWN: original scan point cloud and mesh are unavailable'}
 cases.append(row)
 C['sourceCases']+=1
 C['sourceOnCandidates']+=row['frozenSourceOnlyCategory']=='source_explicit_pretrained_on_proposal'
 C['sourceOnTargetKindCorrect']+=int(valid_source_target and row['frozenSourceOnlyCategory']=='source_explicit_pretrained_on_proposal')
 C['sourceOnIndependentParentKindAnnotated']+=int(valid_source_anchor and row['frozenSourceOnlyCategory']=='source_explicit_pretrained_on_proposal')
 C['sourceOnBothChildTargetAndAnchorKindCorrect']+=int(valid_source_anchor and valid_source_target and row['frozenSourceOnlyCategory']=='source_explicit_pretrained_on_proposal')
 C['sourceOnRealNativeContact']+=int(bool(includes_native_top))
 C['nontopSourceNaturalNegative']+=row['frozenSourceOnlyCategory']=='original_nontop_source_negative_control'
 C['nontopSourcePhysicalContactIncorrectlyGenerated']+=int(row['frozenSourceOnlyCategory']=='original_nontop_source_negative_control' and bool(experiment['nativeCandidate']['contactPairs']))
assert C['sourceOnCandidates']==15 and C['nontopSourceNaturalNegative']==16
assert C['sourceOnRealNativeContact']==15 and C['nontopSourcePhysicalContactIncorrectlyGenerated']==0
out=ROOT/'nr3d_31_actual_native_rapier_independent_human_phrase_labels_raw_v1.json'
with out.open('x') as f:json.dump({'metadata':{'originalCSV_SHA256':sha(ORIGINAL),
 'frozenSourceOnlyPhysicalSpecSHA256':sha(SOURCE),
 'frozenActualGameCoreRapier_SHA256':sha(PHYSICS),
 'selectedPostFrozenHumanGoldOnly':True},'cases':cases},f,indent=2);f.write('\n')
out.chmod(0o600)
safe={'metadata':{
 'frozenOriginalNr3dHumanSourceAndLabelsSHA256':sha(ORIGINAL),
 'preregisteredSourceOnlyProposalsSHA256':sha(SOURCE),
 'frozenActualRapierNativeWorldsSHA256':sha(PHYSICS),
 'originalHuman3DReferenceRoleAuditSHA256':sha(out),
 'humanClassAndAnchorLabelsNotHumanVerticalSupportGeometry':True,
 'validNativeSupportContactsNotClaimedAsTrueSourceWorldMeshes':True,
 'explicitPreviouslyDeniedRandomParentPlaceboNotAttempted':True,
 },'summary':dict(C)}
file=HERE/'prse_round7_independent_physical_roles_actual_gold_aggregate_v1.json'
with file.open('x') as f:json.dump(safe,f,indent=2);f.write('\n')
print('PRSE_INDEPENDENT_NR3D_HUMAN_GOLD_ON_REAL_RAPIER',dict(C))
